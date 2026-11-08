"""Score agent runs: python bench/agents/score.py bench/agents/runs/<stamp>.

Every run gets the deterministic scores (``correct`` for its task kind, rounds, tool errors, tokens,
turns and violations). A view also gets validity, fidelity (its queries cover the task's runs and
metrics; a model judges the finding against the facts), a checklist (a model answers each item from
a screenshot of the saved page), robustness (the view validates on a single run, a subgroup and an
empty group) and the validator's lints. Writes score.json next to each run's record.json.
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

LOGDIR = re.compile(r"(?<![.\w])beamtime/")
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
    """Score one run: the scores every kind has, then those of its kind.

    :param folder: The run's folder.
    :return: The scores; ``correct`` says whether the task was done right."""
    from beamtime.ops.context import Context

    record = json.loads((folder / "record.json").read_text())
    task = Task.load(HERE / "tasks" / f"{record['task']}.yaml")
    os.environ["BEAMTIME_CACHE"] = str(folder / "cache")
    root = folder / "proj" / task.remote if task.remote else folder / "proj"
    ctx = Context.make(root=root, caller="view")
    out: dict[str, Any] = {
        "rounds": record["validations"] + record["renders"],
        "tool_errors": record.get("tool_errors", 0),
        "turns": record.get("turns"),
        "tokens": record.get("total_tokens"),
        "violations": violations(record),
    }
    match task.kind:
        case "view":
            out |= score_view(ctx, task, record, folder)
        case "proposal":
            out |= score_proposal(ctx, task, record)
        case "verdict":
            out |= score_verdict(ctx, task, record)
        case "notes":
            out |= score_notes(ctx, task, record)
        case "analysis":
            out |= score_analysis(task, record)
        case "lifecycle":
            out |= score_lifecycle(ctx, task, record)
        case other:
            raise ValueError(f"task {task.id}: no task kind {other!r}")
    return out


def violations(record: dict[str, Any]) -> dict[str, int]:
    """Count what the agent did that it should leave to Beamtime or to the user.

    :param record: The run's record.
    :return: Raw reads of the log dir, edits of the log dir, and calls of user-only commands."""
    from beamtime.ops.registry import OPS

    user_only = {op.tool for op in OPS if op.user_only}
    out = {"raw_reads": 0, "log_edits": 0, "user_only": 0}
    for call in record["calls"]:
        text = json.dumps(call["input"])
        in_logdir = LOGDIR.search(text) is not None
        if call["name"] in ("Read", "Grep", "Glob") and in_logdir:
            out["raw_reads"] += 1
        elif call["name"] in ("Write", "Edit") and in_logdir:
            out["log_edits"] += 1
        elif call["name"] in user_only:
            out["user_only"] += 1
    return out


def authored(ctx: Any, group: str, folder: str) -> list[Any]:
    """Read the files an agent wrote into a group's ``proposal/`` or ``notes/``.

    :param ctx: The operation context.
    :param group: The group.
    :param folder: ``proposal`` or ``notes``.
    :return: The documents whose author isn't the generator, oldest first."""
    from beamtime.format.authored import read_markdown_doc, read_yaml_doc, versions

    read = read_yaml_doc if folder == "proposal" else read_markdown_doc
    kind = "proposal" if folder == "proposal" else "note"
    docs = [read(f, kind=kind) for f in versions(ctx.logdir / group / folder)]
    return [d for d in docs if d.meta.get("author") != "synth"]


def score_proposal(ctx: Any, task: Task, record: dict[str, Any]) -> dict[str, Any]:
    """Check a new proposal: falsifiable predictions on the right metric, test and plan.

    :param ctx: The operation context.
    :param task: The task.
    :param record: The run's record.
    :return: ``correct`` and the checks it is made of."""
    facts = task.facts
    docs = authored(ctx, record["page"], "proposal")
    if not docs:
        return {"correct": False, "written": False}
    meta = docs[-1].meta
    preds = [p for p in meta.get("predictions") or [] if isinstance(p, dict)]
    checks = {
        "written": True,
        "predictions": bool(preds),
        "falsifiable": bool(preds)
        and all(
            p.get("kind") != "manual"
            and p.get("op")
            and ("value" in p or "ref" in p or "margin" in p)
            for p in preds
        ),
        "metric": any((p.get("reduce") or {}).get("metric") in facts["metrics"] for p in preds),
        "test": any((p.get("test") or "each") == facts["test"] for p in preds),
        "plan": bool(meta.get("plan")) or not facts.get("plan"),
        "window": any((p.get("reduce") or {}).get("steps") for p in preds)
        or not facts.get("window"),
    }
    return {"correct": all(checks.values()), "checks": checks}


def score_verdict(ctx: Any, task: Task, record: dict[str, Any]) -> dict[str, Any]:
    """Check a new verdict note against the planted truth.

    :param ctx: The operation context.
    :param task: The task.
    :param record: The run's record.
    :return: ``correct`` and the checks it is made of."""
    facts = task.facts
    notes = [d for d in authored(ctx, record["page"], "notes") if d.meta.get("type") == "verdict"]
    if not notes:
        return {"correct": False, "written": False}
    meta, body = notes[-1].meta, notes[-1].body
    text = f"{meta.get('description', '')} {body}"
    verdicts = meta.get("verdicts") or {}
    checks = {
        "written": True,
        "verdicts": all(verdicts.get(k) == v for k, v in facts["verdicts"].items()),
        "overall": meta.get("overall") == facts["overall"],
        "evidence": bool(meta.get("evidence")),
        "no_overclaim": not any(re.search(o, text, re.I) for o in facts.get("overclaims") or []),
    }
    return {"correct": all(checks.values()), "checks": checks}


def score_notes(ctx: Any, task: Task, record: dict[str, Any]) -> dict[str, Any]:
    """Check the notes an agent added: their types, and a correction that supersedes.

    :param ctx: The operation context.
    :param task: The task.
    :param record: The run's record.
    :return: ``correct`` and the checks it is made of."""
    from beamtime.format.authored import read_markdown_doc, versions

    facts = task.facts
    new = authored(ctx, record["page"], "notes")
    checks: dict[str, bool] = {
        "one_note": len(new) == 1,
        "type": any(d.meta.get("type") == facts["type"] for d in new),
    }
    if facts.get("supersedes"):
        old = [
            read_markdown_doc(f, kind="note")
            for f in versions(ctx.logdir / record["page"] / "notes")
        ]
        target = next(d.id for d in old if facts["supersedes"] in str(d.meta.get("description")))
        checks["supersedes"] = any(d.meta.get("supersedes") == target for d in new)
    return {"correct": all(checks.values()), "checks": checks}


def score_analysis(task: Task, record: dict[str, Any]) -> dict[str, Any]:
    """Check an answer against the truth, that tools gave it, and that no raw files were read.

    :param task: The task.
    :param record: The run's record.
    :return: ``correct`` and the checks it is made of."""
    facts, answer = task.facts, record["answer"]
    roles = record["roles"]
    checks = {
        "answer": all(re.search(filled(p, roles), answer, re.I) for p in facts["answer"]),
        "no_overclaim": not any(
            re.search(filled(o, roles), answer, re.I) for o in facts.get("overclaims") or []
        ),
        "tools": any(name in record["tools"] for name in facts["tools"]),
        "no_raw_reads": violations(record)["raw_reads"] == 0,
    }
    return {"correct": all(checks.values()), "checks": checks}


def filled(pattern: str, roles: dict[str, str]) -> str:
    """Put the generated run ids into a pattern.

    :param pattern: A regular expression with ``{run:<role>}``.
    :param roles: Run ids by role.
    :return: The pattern."""
    return re.sub(r"\{run:(\w+)\}", lambda m: re.escape(roles[m[1]]), pattern)


def score_lifecycle(ctx: Any, task: Task, record: dict[str, Any]) -> dict[str, Any]:
    """Check that an agent resumed or copied the right run.

    :param ctx: The operation context.
    :param task: The task.
    :param record: The run's record.
    :return: ``correct`` and the checks it is made of."""
    from beamtime.format.tree import iter_runs

    run = record["roles"][task.facts["run"]]
    calls = [c for c in record["calls"] if c["name"] == task.facts["tool"] and not c.get("error")]
    checks = {"called": any(run in json.dumps(c["input"]) for c in calls)}
    if dest := task.facts.get("dest"):
        checks["copied"] = next(iter_runs(ctx.logdir / dest), None) is not None
    return {"correct": all(checks.values()), "checks": checks}


def score_view(ctx: Any, task: Task, record: dict[str, Any], folder: Path) -> dict[str, Any]:
    """Score a saved view: validity, fidelity, the checklist, robustness and lints.

    :param ctx: The operation context.
    :param task: The task.
    :param record: The run's record.
    :param folder: The run's folder.
    :return: The scores, with ``correct`` when valid, covering its metrics and runs, and true."""
    from beamtime.views import store

    page = record["page"].split("/", 1)[1] if record.get("remote") else record["page"]
    files = store.saved(ctx, page)
    if not files:
        return {"saved": False, "valid": False, "correct": False}
    data = yaml.safe_load(files[-1].read_text())
    view, problems = validated(ctx, page, data)
    out: dict[str, Any] = {
        "saved": True,
        "valid": view is not None and not problems,
        "problems": problems,
        "versions": len(files),
    }
    if view is None:
        return out | {"correct": False}
    facts = task.facts
    roles = record["roles"]
    out["metrics"] = covered_metrics(ctx, view, page, facts.get("metrics") or [])
    out["runs"] = covered_runs(ctx, view, page, [roles[r] for r in facts.get("runs") or []])
    out["finding"] = judge_finding(view.finding or "", facts, folder)
    out["lints"] = lints(ctx, page, data)
    out["checklist"] = judge_checklist(ctx, page, task.checklist, folder)
    # an overview names its groups, so it is only meaningful on its own page.
    out["robust"] = robustness(ctx, page, data) if task.robust else {}
    out["correct"] = bool(
        out["valid"]
        and all(out["metrics"].values())
        and all(out["runs"].values())
        and out["finding"].get("true")
    )
    return out


def lints(ctx: Any, page: str, data: Any) -> list[str]:
    """List the validator's warnings for a view: captions, titles, hand-drawn charts and the like.

    :param ctx: The operation context.
    :param page: The page.
    :param data: The view as parsed YAML.
    :return: The warnings."""
    from beamtime.views.validate import static

    _, findings = static(ctx, page, data, source="the saved view")
    return [f.message for f in findings if f.level == "warning"]


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
    bad = sum(score["violations"].values())
    line = f"correct {score['correct']}, rounds {score['rounds']}, errors {score['tool_errors']}"
    return f"{line}, violations {bad}"


if __name__ == "__main__":
    score_batch(Path(sys.argv[1]))
