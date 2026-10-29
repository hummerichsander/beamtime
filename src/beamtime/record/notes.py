"""Notes: validating new notes, and the derived states of existing ones."""

import json
from typing import Any

from beamtime.format.authored import EVIDENCE_KINDS, link_kind
from beamtime.format.ids import is_version_id
from beamtime.index.store import in_scope
from beamtime.query.models import closest
from beamtime.record.check import evaluate, snapshot
from beamtime.record.proposals import RecordError, Target, all_versions, load

TYPES = ("observation", "decision", "idea", "question", "verdict")
VERDICTS = ("confirmed", "refuted", "inconclusive")


def evidence_entry(item: str | dict[str, Any]) -> dict[str, Any]:
    """Turn an evidence item into a typed entry.

    :param item: A typed entry, or a run id, note id, ``group#prediction`` or
        ``group@view-version``.
    :return: The typed entry, e.g. ``{run: <id>}``."""
    if isinstance(item, dict):
        if not item or not any(k in item for k in (*EVIDENCE_KINDS, "metric")):
            raise RecordError(
                f"evidence {item!r}: give run, metric (with stat, run, value), view, "
                "prediction or note"
            )
        return item
    kind = link_kind(item)
    if kind == "folder":
        raise RecordError(
            f"evidence {item!r}: give a run id, a note id, group#prediction or group@view-version"
        )
    return {kind: item}


def build(
    target: Target,
    *,
    type: str,
    description: str,
    resolves: list[str],
    supersedes: str | None,
    completes: list[str],
    evidence: list[str | dict[str, Any]],
    proposal: str | None,
    verdicts: dict[str, str],
    overall: str | None,
) -> dict[str, Any]:
    """Validate a new note's fields and add the check snapshot to verdicts.

    :param target: The group or run the note goes into.
    :param type: The note type.
    :param description: The one-line description.
    :param resolves: Ids of notes it answers.
    :param supersedes: The id of a note it corrects.
    :param completes: Groups it declares complete (decisions).
    :param evidence: What it rests on.
    :param proposal: The judged proposal version (verdicts).
    :param verdicts: Prediction name to verdict (verdicts).
    :param overall: The overall verdict (verdicts).
    :return: The frontmatter fields after ``schema``, without author and user."""
    problems = []
    if type not in TYPES:
        raise RecordError(f"type {type!r} is not a note type.{closest(type, list(TYPES))} "
                          f"Types: {', '.join(TYPES)}.")  # fmt: skip
    description = (description or "").strip()
    if not description or "\n" in description:
        problems.append("description is one line, required: what listings show first")
    known = note_ids(target)
    for note in [*resolves, *([supersedes] if supersedes else [])]:
        if not is_version_id(note) or note not in known:
            problems.append(f"no note {note!r}; `beamtime notes` lists them with their ids")
    if completes and type != "decision":
        problems.append("completes belongs to decision notes")
    for folder in completes:
        if not target.index.folder_path(folder.strip("/")).is_dir():
            problems.append(f"completes: no group {folder!r} below the log dir")
    meta: dict[str, Any] = {"description": description, "type": type}
    if type == "verdict":
        problems += judge(target, proposal, verdicts, overall)
        if not problems:
            check = evaluate(target, proposal, load(target.dir, proposal))
            meta |= {
                "proposal": proposal,
                "verdicts": verdicts,
                "overall": overall,
                "check": snapshot(check),
            }
    elif proposal or verdicts or overall:
        problems.append("proposal, verdict and overall belong to verdict notes (--type verdict)")
    try:
        entries = [evidence_entry(e) for e in evidence]
    except RecordError as e:
        problems.append(str(e))
        entries = []
    for entry in entries:
        if (run := entry.get("run")) is not None and target.index.store.run(str(run)) is None:
            problems.append(f"evidence: no run {run!r}")
        if (note := entry.get("note")) is not None and note not in known:
            problems.append(f"evidence: no note {note!r}")
    if problems:
        raise RecordError("; ".join(problems))
    if entries:
        meta["evidence"] = entries
    if resolves:
        meta["resolves"] = resolves
    if supersedes:
        meta["supersedes"] = supersedes
    if completes:
        meta["completes"] = [f.strip("/") for f in completes]
    return meta


def judge(
    target: Target, proposal: str | None, verdicts: dict[str, str], overall: str | None
) -> list[str]:
    """Check a verdict: the version exists and every prediction is judged.

    :param target: The group or run.
    :param proposal: The judged version.
    :param verdicts: Prediction name to verdict.
    :param overall: The overall verdict.
    :return: One message per problem."""
    problems = []
    versions = all_versions(target.dir)
    if not proposal:
        latest = f" (current: {versions[-1]})" if versions else ""
        return [f"a verdict names the judged proposal version with --proposal{latest}"]
    if proposal not in versions:
        return [f"no proposal version {proposal!r} in {target.rel}; versions: {versions}"]
    names = [p.name for p in load(target.dir, proposal).predictions]
    if unknown := sorted(set(verdicts) - set(names)):
        problems.append(f"no prediction {', '.join(unknown)}; predictions: {', '.join(names)}")
    if missing := [n for n in names if n not in verdicts]:
        problems.append(f"judge every prediction; missing: {', '.join(missing)}")
    for name, value in verdicts.items():
        if value not in VERDICTS:
            problems.append(f"verdict {name}={value!r}: use {', '.join(VERDICTS)}")
    if overall not in VERDICTS:
        problems.append(f"overall is one of {', '.join(VERDICTS)}")
    return problems


def note_ids(target: Target) -> set[str]:
    """List every indexed note id.

    :param target: Any target, for its index.
    :return: The ids."""
    return {r[0] for r in target.index.store.db.execute("SELECT id FROM notes")}


def listing(
    target: Target,
    *,
    types: list[str] | None,
    only_open: bool,
    full: bool,
    only_current: bool = False,
) -> list[dict[str, Any]]:
    """List the notes at or below a group with their derived states, newest first.

    :param target: The group or run.
    :param types: Note types to keep, or ``None`` for all.
    :param only_open: Keep only open questions.
    :param full: Include the bodies.
    :param only_current: Leave out notes that a newer version supersedes.
    :return: One entry per note."""
    from beamtime.format.authored import read_markdown_doc

    db = target.index.store.db
    resolved = {
        r[0] for r in db.execute("SELECT j.value FROM notes, json_each(notes.meta, '$.resolves') j")
    }
    superseded = {
        r[0]: r[1]
        for r in db.execute(
            "SELECT json_extract(meta, '$.supersedes'), id FROM notes "
            "WHERE json_extract(meta, '$.supersedes') IS NOT NULL"
        )
    }
    cond, params = (
        ("run_id = ?", [target.run_id])
        if target.run_id is not None
        else in_scope("folder", target.rel)
    )
    out = []
    for path, folder, note_id, type_, description, meta in db.execute(
        f"SELECT path, folder, id, type, description, meta FROM notes WHERE {cond} "
        "ORDER BY id DESC",
        params,
    ):
        # removed since the index last looked; it is gone, not broken.
        if not (target.index.logdir / path).is_file():
            continue
        state = None
        if type_ == "question":
            state = "resolved" if note_id in resolved else "open"
        if note_id in superseded:
            state = f"superseded by {superseded[note_id]}"
        if (types and type_ not in types) or (only_open and state != "open"):
            continue
        if only_current and note_id in superseded:
            continue
        entry = {
            "id": note_id,
            "group": folder,
            "type": type_,
            "description": description,
            "state": state,
        }
        fields = json.loads(meta or "{}")
        if type_ == "verdict":
            entry["proposal"] = fields.get("proposal")
            entry["overall"] = fields.get("overall")
        if full:
            entry["meta"] = {k: v for k, v in fields.items() if k != "schema"}
            entry["body"] = read_markdown_doc(target.index.logdir / path, kind="note").body
        out.append(entry)
    return out
