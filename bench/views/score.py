"""Score agent runs: python bench/views/score.py bench/views/runs/<stamp>.

Validity (the saved view validates; rounds it took), fidelity (its queries cover the task's runs and
metrics; a model judges the finding against the facts), checklist (a model answers each item from a
screenshot of the saved page) and robustness (the view validates on a single run, a subgroup and
an empty group). Writes score.json next to each run's record.json.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from run import HERE, Task

JUDGE = "sonnet"
JUDGE_LIMIT_S = 300


def score_batch(stamp: Path) -> None:
    """Score every run of a batch that has no score yet.

    :param stamp: The batch's folder."""
    for folder in sorted(p for p in stamp.iterdir() if (p / "record.json").is_file()):
        if not (folder / "score.json").is_file():
            score = score_run(folder)
            (folder / "score.json").write_text(json.dumps(score, indent=2))
            print(f"{folder.name}: {short(score)}", flush=True)


def score_run(folder: Path) -> dict[str, Any]:
    """Score one run.

    :param folder: The run's folder.
    :return: The scores."""
    from beamtime.ops.context import Context
    from beamtime.views import store

    record = json.loads((folder / "record.json").read_text())
    task = Task.load(HERE / "tasks" / f"{record['task']}.yaml")
    root, page = folder / "proj", record["page"]
    os.environ["BEAMTIME_CACHE"] = str(folder / "cache")
    ctx = Context.make(root=root, caller="view")
    files = store.saved(ctx, page)
    if not files:
        return {"saved": False, "valid": False, "rounds": record["validations"] + record["renders"]}
    data = yaml.safe_load(files[-1].read_text())
    view, problems = validated(ctx, page, data)
    out: dict[str, Any] = {
        "saved": True,
        "valid": view is not None and not problems,
        "problems": problems,
        "rounds": record["validations"] + record["renders"],
        "versions": len(files),
    }
    if view is None:
        return out
    facts = task.facts
    roles = record["roles"]
    out["metrics"] = covered_metrics(ctx, view, page, facts.get("metrics") or [])
    out["runs"] = covered_runs(ctx, view, page, [roles[r] for r in facts.get("runs") or []])
    out["finding"] = judge_finding(view.finding or "", facts, folder)
    out["checklist"] = judge_checklist(ctx, page, task.checklist, folder)
    # an overview names its groups, so it is only meaningful on its own page.
    out["robust"] = robustness(ctx, page, data) if task.robust else {}
    return out


def validated(ctx: Any, page: str, data: Any) -> tuple[Any, list[str]]:
    """Validate a view statically on a page.

    :param ctx: The operation context.
    :param page: The page.
    :param data: The view as parsed YAML.
    :return: The view (if it parses) and its error messages."""
    from beamtime.views.validate import static

    view, findings = static(ctx, page, data, source="the saved view")
    return view, [f.message for f in findings if f.level == "error"]


def calls(ctx: Any, view: Any, page: str) -> list[dict[str, Any]]:
    """Compile a view and list the API calls its blocks make.

    :param ctx: The operation context.
    :param view: The view.
    :param page: The page.
    :return: ``{method, params}`` per call, and the nodes' props as ``props``."""
    from beamtime.views.compile import compile_view, walk_tree
    from beamtime.views.library import Library

    tree = compile_view(view, path=page, library=Library(ctx=ctx, path=page))
    out = []
    for node in walk_tree(tree):
        for c in (node.get("data") or {}).values():
            out.append({"method": c["method"], "params": c["params"], "props": node.get("props")})
    return out


def covered_metrics(ctx: Any, view: Any, page: str, metrics: list[str]) -> dict[str, bool]:
    """Tell which required metrics the view's blocks ask for or show.

    :param ctx: The operation context.
    :param view: The view.
    :param page: The page.
    :param metrics: The required metric keys.
    :return: Covered, per metric."""
    text = json.dumps(calls(ctx, view, page))
    return {k: k in text for k in metrics}


def covered_runs(ctx: Any, view: Any, page: str, runs: list[str]) -> dict[str, bool]:
    """Tell which required runs the view's queries select.

    :param ctx: The operation context.
    :param view: The view.
    :param page: The page.
    :param runs: The required run ids.
    :return: Covered, per run."""
    from beamtime.ops import call
    from beamtime.ops.context import OpError
    from beamtime.views.code import placeholders

    selected: set[str] = set()
    for c in calls(ctx, view, page):
        if c["method"] not in ("runs", "series", "data", "timeline") or placeholders(c["params"]):
            continue
        sel = {k: c["params"][k] for k in ("from", "where", "depth") if k in c["params"]}
        try:
            answer = call("runs", sel | {"select": ["run.id"], "limit": 10000}, ctx)
        except OpError:
            continue
        selected |= {row[0] for row in answer["rows"]}
    return {r: r in selected for r in runs}


def robustness(ctx: Any, page: str, data: Any) -> dict[str, bool | None]:
    """Validate the view on other pages: a single run, a subgroup and an empty group.

    :param ctx: The operation context.
    :param page: The page it was built for.
    :param data: The view as parsed YAML.
    :return: Whether it validates without errors, per kind; ``None`` where there is no such page."""
    from beamtime.format.tree import iter_runs

    folder = ctx.logdir / page
    run = next(iter_runs(folder), None)
    subgroups = [
        p
        for p in sorted(folder.iterdir())
        if p.is_dir()
        and not p.name.startswith("_")
        and not (p / "_run.json").exists()
        and any(iter_runs(p))
    ]
    empty = ctx.logdir / "bench-empty"
    empty.mkdir(exist_ok=True)
    pages = {
        "run": run.relative_to(ctx.logdir).as_posix() if run is not None else None,
        "subgroup": subgroups[0].relative_to(ctx.logdir).as_posix() if subgroups else None,
        "empty": "bench-empty",
    }
    try:
        return {k: None if p is None else not validated(ctx, p, data)[1] for k, p in pages.items()}
    finally:
        shutil.rmtree(empty)


def judge_finding(finding: str, facts: dict[str, Any], folder: Path) -> dict[str, Any]:
    """Ask a model whether the view's finding states the truth without overclaiming.

    :param finding: The view's finding.
    :param facts: The task's facts.
    :param folder: The run's folder, the judge's working directory.
    :return: ``{true, overclaims, why}``."""
    if not finding.strip():
        return {"true": False, "overclaims": [], "why": "no finding"}
    prompt = (
        "You judge a one-sentence finding written about an ML experiment against the known truth.\n"
        f"Truth: {facts.get('finding')}\n"
        f"Known overclaims to watch for: {json.dumps(facts.get('overclaims') or [])}\n"
        f"Finding: {finding}\n"
        "Is the finding consistent with the truth? It may say less, and it may add details the "
        "truth doesn't mention, as long as nothing contradicts the truth. Does it overclaim "
        "(state more certainty, generality or significance than the truth supports)? "
        'Answer with JSON only: {"true": bool, "overclaims": [str], "why": str}'
    )
    return ask(prompt, folder, tools="")


def judge_checklist(ctx: Any, page: str, items: list[str], folder: Path) -> dict[str, Any]:
    """Render the saved page and ask a model about each checklist item from the screenshot.

    :param ctx: The operation context.
    :param page: The page.
    :param items: The checklist.
    :param folder: The run's folder; the screenshot goes there.
    :return: ``{items: [{item, yes, why}], shot}``, or why it wasn't judged."""
    from beamtime.views.render import render_page

    shot = folder / "page.png"
    rendered = render_page(ctx, page, shot)
    if not rendered.get("rendered"):
        return {"items": [], "error": rendered.get("reason", "not rendered")}
    listed = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))
    prompt = (
        f"Read the screenshot {shot} with the Read tool. It shows a page of an experiment "
        "tracker. Answer each checklist item about what the page shows, strictly: yes only if the "
        f"screenshot clearly shows it.\n{listed}\n"
        'Answer with JSON only: {"items": [{"item": int, "yes": bool, "why": str}]}'
    )
    answer = ask(prompt, folder, tools="Read")
    marks = {a.get("item"): a for a in answer.get("items", []) if isinstance(a, dict)}
    return {
        "items": [
            {
                "item": item,
                "yes": bool(marks.get(i + 1, {}).get("yes")),
                "why": marks.get(i + 1, {}).get("why"),
            }
            for i, item in enumerate(items)
        ],
        "shot": str(shot),
        "render_findings": [f["message"] for f in rendered["findings"] if f["level"] == "error"],
    }


def ask(prompt: str, folder: Path, *, tools: str) -> dict[str, Any]:
    """Ask the judge model and read the JSON in its answer.

    :param prompt: The question.
    :param folder: The working directory.
    :param tools: Built-in tools it may use, e.g. ``Read``; empty for none.
    :return: The parsed JSON, or ``{error}``."""
    command = [
        "claude",
        "-p",
        prompt,
        "--model",
        JUDGE,
        "--tools",
        tools,
        "--allowedTools",
        tools,
        "--setting-sources",
        "project",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--output-format",
        "json",
    ]
    try:
        done = subprocess.run(
            command, cwd=folder, capture_output=True, text=True, timeout=JUDGE_LIMIT_S
        )
        text = json.loads(done.stdout).get("result", "")
    except (subprocess.TimeoutExpired, ValueError) as e:
        return {"error": str(e)}
    if (m := re.search(r"\{.*\}", text, re.S)) is None:
        return {"error": f"no JSON in {text[:200]!r}"}
    try:
        return json.loads(m.group(0))
    except ValueError as e:
        return {"error": str(e)}


def short(score: dict[str, Any]) -> str:
    """Summarize a score in one line.

    :param score: The score.
    :return: The line."""
    if not score.get("saved"):
        return "no view saved"
    items = score.get("checklist", {}).get("items", [])
    yes = sum(i["yes"] for i in items)
    return (
        f"valid {score['valid']}, rounds {score['rounds']}, finding "
        f"{score.get('finding', {}).get('true')}, checklist {yes}/{len(items)}"
    )


if __name__ == "__main__":
    score_batch(Path(sys.argv[1]))
