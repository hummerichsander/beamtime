"""Compact text answers, alike in terminals and pipes: agents see what people see."""

import math
from typing import Any

SPARKS = "▁▂▃▄▅▆▇█"
SPARK_WIDTH = 24


def num(value: Any) -> str:
    """Format a cell compactly.

    :param value: Any answer value.
    :return: E.g. ``3e-4``, ``0.931``, ``12k``, ``-``."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        if value == 0:
            return "0"
        if abs(value) >= 1e5 or abs(value) < 1e-3:
            mantissa, exp = f"{value:.2e}".split("e")
            mantissa = mantissa.rstrip("0").rstrip(".")
            return f"{mantissa}e{int(exp)}"
        return f"{value:.3g}"
    if isinstance(value, dict) and "mean" in value:
        return f"{num(value['mean'])}±{num(value['std'])} ({value['n']})"
    if isinstance(value, list):
        text = ",".join(num(v) for v in value[:5])
        return text + (f",… ({len(value)})" if len(value) > 5 else "")
    if isinstance(value, dict):
        return ", ".join(f"{k}={num(v)}" for k, v in value.items())
    return str(value)


def header(column: str) -> str:
    """Shorten a column name for display.

    :param column: A field name.
    :return: ``run`` for the name, ``id`` for the id, metrics without ``metric.``."""
    match column:
        case "run.name":
            return "run"
        case "run.id":
            return "id"
    return column.removeprefix("metric.").removeprefix("run.")


def table(columns: list[str], rows: list[list[Any]]) -> list[str]:
    """Align columns without box drawing.

    :param columns: The column names.
    :param rows: The rows.
    :return: The lines."""
    order = [i for i, col in enumerate(columns) if col != "run.id"]
    order += [i for i, col in enumerate(columns) if col == "run.id"]
    cells = [[header(columns[i]) for i in order]]
    # seed means list their run ids; in text, how many is enough.
    cells += [[count_or_num(columns[i], row[i]) for i in order] for row in rows]
    widths = [max(len(r[k]) for r in cells) for k in range(len(order))]
    return ["  ".join(c.ljust(w) for c, w in zip(r, widths, strict=True)).rstrip() for r in cells]


def count_or_num(column: str, value: Any) -> str:
    """Format a cell; the run ids of a seed group show as their count.

    :param column: The column name.
    :param value: The cell.
    :return: The text."""
    if column == "runs" and isinstance(value, list):
        return str(len(value))
    return num(value)


def spark(values: list[Any]) -> str:
    """Draw a sparkline of up to 24 characters.

    :param values: The values; ``None`` draws a gap.
    :return: The sparkline."""
    if not values:
        return ""
    if len(values) > SPARK_WIDTH:
        step = len(values) / SPARK_WIDTH
        values = [values[int(i * step)] for i in range(SPARK_WIDTH)]
    finite = [v for v in values if v is not None and math.isfinite(v)]
    if not finite:
        return " " * len(values)
    lo, hi = min(finite), max(finite)
    span = hi - lo or 1.0
    return "".join(
        " "
        if v is None or not math.isfinite(v)
        else SPARKS[min(len(SPARKS) - 1, int((v - lo) / span * len(SPARKS)))]
        for v in values
    )


def trend(values: list[Any]) -> str:
    """Tell whether a curve still moves at its end.

    :param values: The values.
    :return: ``↑``, ``↓`` or ``→``."""
    finite = [v for v in values if v is not None and math.isfinite(v)]
    if len(finite) < 4:
        return "→"
    tail = finite[-max(2, len(finite) // 10) :]
    span = (max(finite) - min(finite)) or 1.0
    change = (tail[-1] - tail[0]) / span
    return "↑" if change > 0.02 else "↓" if change < -0.02 else "→"


def curve_line(curve: dict[str, Any]) -> str:
    """Summarize one curve on one line.

    :param curve: A curve of a ``series`` answer.
    :return: Label, first, min, max, last, trend and a sparkline."""
    if "by" in curve:
        label = num(curve["by"]) or "all"
        ys = curve.get("mean", [])
        extra = f"  runs {len(curve['runs'])}"
    else:
        label = curve.get("name") or curve["run"]
        ys = curve["y"] if curve.get("raw") else curve.get("last", [])
        extra = ""
    if "by" in curve:
        mins = maxs = ys
    elif curve.get("raw"):
        mins = maxs = ys
    else:
        mins, maxs = curve.get("min", []), curve.get("max", [])
    finite = [v for v in ys if v is not None]
    if not finite:
        return f"{label}  {curve['metric']}: no data"
    lo = min(v for v in mins if v is not None)
    hi = max(v for v in maxs if v is not None)
    key = curve["metric"]
    return (
        f"{label}  {key}  first {num(finite[0])}  min {num(lo)}  max {num(hi)}  "
        f"last {num(finite[-1])}  {trend(ys)} {spark(ys)}{extra}"
    )


def meta_line(answer: dict[str, Any], noun: str, shown: int) -> str:
    """Write the closing line: how much was shown, freshness, how to get more.

    :param answer: The answer.
    :param noun: What the items are, e.g. ``runs``.
    :param shown: How many items were shown.
    :return: The line."""
    meta = answer.get("meta", {})
    parts = []
    matched = meta.get("matched")
    if noun in ("seed means", "curves"):
        parts.append(f"{shown} {noun} from {matched} runs")
    elif matched is not None and matched != shown:
        parts.append(f"{shown} of {matched} {noun}")
    else:
        parts.append(f"{shown} {noun}")
    if fresh := meta.get("freshness"):
        parts.append(fresh["text"])
    if meta.get("next"):
        parts.append(f"--cursor {meta['next']} for more")
    elif meta.get("cut"):
        parts.append("--limit to see more")
    return " · ".join(parts)


def render(answer: dict[str, Any]) -> str:
    """Render an answer as compact text.

    :param answer: Any operation's answer.
    :return: The text."""
    kind = answer.get("kind")
    match kind:
        case "runs" | "groups" | "file" | "settings" | "doctor":
            lines = table(answer["columns"], answer["rows"])
            noun = {"runs": "runs", "groups": "groups"}.get(kind, "rows")
            if kind == "runs" and answer["meta"].get("means") is not None:
                noun = "seed means"
            if kind in ("runs", "groups", "file"):
                lines.append(meta_line(answer, noun, len(answer["rows"])))
            for problem in answer.get("problems", []):
                lines.append(f"problem: {problem}")
            return "\n".join(lines)
        case "series":
            lines = [curve_line(c) for c in answer["curves"]]
            lines.append(meta_line(answer, "curves", len(answer["curves"])))
            return "\n".join(lines)
        case "keys":
            return render_keys(answer)
        case "card":
            return render_card(answer)
        case "data":
            lines = [render_entry(e) for e in answer["entries"]]
            answer["meta"]["matched"] = answer["meta"].get("entries")
            lines.append(meta_line(answer, "entries", len(answer["entries"])))
            return "\n".join(lines)
        case "timeline":
            lines = [timeline_line(e) for e in answer["entries"]]
            lines.append(meta_line(answer, "entries", len(answer["entries"])))
            return "\n".join(lines)
        case "output":
            lines = list(answer["lines"])
            meta = answer["meta"]
            tail = f"{meta['shown']} of {meta['total_lines']} lines"
            if meta.get("hint"):
                tail += f" · {meta['hint']}"
            return "\n".join([*lines, tail])
        case "status":
            return render_status(answer)
        case "check":
            return render_check(answer)
        case "notes":
            lines = [note_line(e) for e in answer["entries"]]
            lines.append(meta_line(answer, "notes", len(answer["entries"])))
            return "\n".join(lines)
        case "proposal":
            return render_proposal(answer)
        case "memory":
            return render_memory(answer)
        case _:
            return "\n".join(answer.get("lines", [])) or str(answer)


def timeline_line(entry: dict[str, Any]) -> str:
    """Render one timeline entry, with the note body if it was asked for.

    :param entry: An entry of a ``timeline`` answer.
    :return: The text."""
    when = entry["t"][:16].replace("T", " ")
    where = entry.get("run") or entry.get("group") or ""
    line = f"{when}  {entry['kind']} {entry['type'] or ''}  {where}  "
    description = entry.get("description") or ""
    if description != (entry["type"] or "").replace("_", " "):
        line += description
    line = line.rstrip()
    return line + (f"\n{entry['body'].strip()}" if entry.get("body") else "")


def render_keys(answer: dict[str, Any]) -> str:
    """Render a ``keys`` answer in sections.

    :param answer: The answer.
    :return: The text."""
    status = ", ".join(f"{k} {v}" for k, v in answer["status"].items())
    lines = [f"{answer['runs']} runs: {status}", "", "metrics"]
    lines += ["  " + line for line in table(**answer["metrics"])]
    lines += ["", "config"] + ["  " + line for line in table(**answer["config"])]
    if answer["data"]["rows"]:
        lines += ["", "data"] + ["  " + line for line in table(**answer["data"])]
    if answer["tags"]:
        lines += [
            "",
            "tags  " + ", ".join(f"{t} ({n})" for t, n in answer["tags"].items()),
        ]
    lines.append(meta_line(answer, "runs", answer["runs"]))
    return "\n".join(lines)


def render_card(answer: dict[str, Any]) -> str:
    """Render a run card.

    :param answer: The answer.
    :return: The text."""
    run = answer["run"]
    lines = [
        f"{run['name']}  {run['id']}  {run['status']}",
        f"path        {run['path']}",
    ]
    for key in (
        "created_at",
        "ended_at",
        "duration_s",
        "steps",
        "host",
        "attempts",
        "error",
    ):
        if run.get(key) not in (None, "", 0) or key == "steps":
            lines.append(f"{key.replace('_', ' '):<12}{num(run.get(key))}")
    if run.get("tags"):
        lines.append(f"tags        {', '.join(run['tags'])}")
    if run.get("warnings"):
        lines.append(f"warnings    {run['warnings']} (see `beamtime output` and the events)")
    if answer["config"]:
        lines += ["", "config"] + [f"  {k} = {num(v)}" for k, v in flat(answer["config"])]
    if answer["metrics"]:
        cols = ["metric", "first", "last", "min", "max", "mean", "count", "last_step"]
        rows = [[k, *[m.get(c) for c in cols[1:]]] for k, m in answer["metrics"].items()]
        lines += ["", *table(cols, rows)]
    if answer["values"]:
        lines += ["", "values"] + [f"  {k} = {num(v)}" for k, v in answer["values"].items()]
    if answer.get("proposals"):
        lines += ["", "proposals"]
        for prop in answer["proposals"]:
            line = f"  {prop['group']} {prop['version']}  check "
            line += result_text(prop["check"], prop.get("provisional"))
            if prop.get("verdict"):
                line += f"  verdict {prop['verdict']}"
            if prop.get("current") is False:
                line += "  (superseded)"
            lines.append(line)
    if answer.get("cited_by"):
        lines += ["", "cited by"] + [
            f"  {n['id']}  {n['type']}  {n['description']}" for n in answer["cited_by"]
        ]
    if answer["events"]:
        lines += ["", "recent events"] + [
            f"  {e['t'][:16].replace('T', ' ')}  {e['description']}" for e in answer["events"]
        ]
    return "\n".join(lines)


def flat(config: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
    """Flatten a nested config for display.

    :param config: The config.
    :param prefix: The path so far.
    :return: Dotted keys and values."""
    out = []
    for k, v in config.items():
        if isinstance(v, dict) and v:
            out += flat(v, f"{prefix}{k}.")
        else:
            out.append((f"{prefix}{k}", v))
    return out


def render_entry(entry: dict[str, Any]) -> str:
    """Render one logged data entry.

    :param entry: An entry of a ``data`` answer.
    :return: The text."""
    head = f"{entry['run']}  step {entry['step']}  {entry['kind']}"
    if "columns" in entry:
        cols = list(entry["columns"])
        rows = [list(r) for r in zip(*entry["columns"].values(), strict=False)][:20]
        return "\n".join([head, *["  " + line for line in table(cols, rows)]])
    if "text" in entry:
        return f"{head}\n  {entry['text']}"
    return f"{head}  {entry.get('file', entry.get('path'))}"


def render_status(answer: dict[str, Any]) -> str:
    """Render ``status``.

    :param answer: The answer.
    :return: The text."""
    daemon = answer["daemon"]
    lines = [
        f"root      {answer['root']} (from {answer['root_from']})",
        f"log dir   {answer['logdir']}" + ("" if answer["logdir_exists"] else " (not created yet)"),
        f"cache     {answer['cache']}",
        "runs      " + (", ".join(f"{k} {v}" for k, v in answer["runs"].items()) or "none"),
        "daemon    "
        + (
            f"running since pid {daemon.get('pid')}"
            if daemon
            else "not running (each call catches up itself; serve comes with M5)"
        ),
    ]
    if memory := answer.get("memory"):
        since = memory["notes_since"]
        lines.append(
            f"memory    {memory['version']}"
            + (f"; {since} note(s) since, `beamtime memory update .`" if since else "; current")
        )
    if answer["web_ui"]:
        lines.append(f"web UI    {answer['web_ui']}")
    if answer["remotes"]:
        lines.append(f"remotes   {', '.join(answer['remotes'])} (connected from milestone M8)")
    if fresh := answer["meta"].get("freshness"):
        lines.append(fresh["text"])
    return "\n".join(lines)


def result_text(result: str | None, provisional: bool | None = None) -> str:
    """Write a check result, marked when the plan is not complete.

    :param result: The result.
    :param provisional: Whether it is provisional.
    :return: E.g. ``pass (provisional)``."""
    return f"{result or 'no predictions'}{' (provisional)' if provisional else ''}"


def render_check(answer: dict[str, Any]) -> str:
    """Render a check: the combined result, the plan and one line per prediction.

    :param answer: The answer.
    :return: The text."""
    lines = [
        f"{answer['group']}  proposal {answer['version']}  "
        f"{result_text(answer['result'], answer.get('provisional'))}"
    ]
    if answer.get("problem"):
        lines.append(f"problem: {answer['problem']}")
    if plan := answer.get("progress"):
        lines.append(f"plan        {plan['text']}")
    if answer.get("level") is not None:
        lines.append(f"level       {answer['level']:.0%} t-intervals")
    for p in answer.get("predictions", []):
        line = f"  {p['name']:<20} {p['result']:<13}"
        if p.get("effect") is not None:
            line += f" effect {num(p['effect'])}"
            if p.get("ci"):
                line += f" [{num(p['ci'][0])}, {num(p['ci'][1])}]"
            line += f" vs {p.get('op', '')} {num(p.get('threshold'))}  points {p.get('points')}"
        elif p.get("kind") == "manual":
            line += f" manual: {p.get('description')}"
        lines.append(line.rstrip())
        if p.get("detail"):
            lines.append(f"  {'':<20} {p['detail']}")
        for point in p.get("by_point", []) if len(p.get("by_point", [])) > 1 else []:
            ci = f" [{num(point['ci'][0])}, {num(point['ci'][1])}]" if point.get("ci") else ""
            lines.append(
                f"  {'':<20}   {num(point['point']) or 'all'}: {num(point['mean'])}{ci} "
                f"{point['result']}"
            )
        for note in p.get("cited_by", []):
            lines.append(
                f"  {'':<20} cited by {note['id']} ({note['type']}): {note['description']}"
            )
    return "\n".join(lines)


def note_line(entry: dict[str, Any]) -> str:
    """Render one note of a ``notes`` answer.

    :param entry: The entry.
    :return: The text, with the body if it was asked for."""
    state = f" [{entry['state']}]" if entry.get("state") else ""
    verdict = f" {entry['overall']} on {entry['proposal']}" if entry.get("overall") else ""
    line = f"{entry['id']}  {entry['type']}{state}{verdict}  {entry['group']}  "
    line += entry.get("description") or ""
    return line + (f"\n{entry['body'].strip()}\n" if entry.get("body") else "")


def render_proposal(answer: dict[str, Any]) -> str:
    """Render a proposal with its versions.

    :param answer: The answer.
    :return: The text."""
    import yaml

    lines = [
        f"{answer['group']}  {answer['status']}  version {answer['version']}"
        + (f"  ({answer['progress']})" if answer.get("progress") else ""),
        "",
        yaml.safe_dump(answer["proposal"], sort_keys=False, allow_unicode=True).rstrip(),
        "",
        "versions",
    ]
    for v in answer["versions"]:
        frozen = "frozen" if v["frozen"] else "not frozen"
        line = f"  {v['version']}  {v['runs']} runs, {frozen}, check {v['check']}"
        if v.get("supersedes"):
            line += f"; supersedes {v['supersedes']}: {v['reason']}"
        lines.append(line)
    return "\n".join(lines)


def render_memory(answer: dict[str, Any]) -> str:
    """Render the memory chain, root first.

    :param answer: The answer.
    :return: The text."""
    lines = []
    for m in answer["chain"]:
        head = f"# memory of {m['group']}  ({m['version']}, notes until {m.get('covers_until')})"
        lines += [head, "", (m.get("body") or m.get("problem") or "").strip(), ""]
    lines += answer["meta"].get("hints", [])
    return "\n".join(lines).strip()
