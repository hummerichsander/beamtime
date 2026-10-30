from pathlib import Path

import pytest
import yaml

from beamtime.format.authored import newest, read_markdown_doc, versions
from beamtime.ops import call
from beamtime.ops.context import Context, OpError

PROPOSAL = {
    "statement": "Warmup removes the loss spike.",
    "plan": {"runs": 6},
    "predictions": [
        {
            "name": "no-spike",
            "reduce": {"metric": "train/loss", "stat": "max", "steps": [100, 300]},
            "op": "<",
            "value": 2.5,
        },
        {"name": "sharper", "kind": "manual", "description": "Samples look sharper."},
    ],
}


def fails(code: int, match: str, op: str, params: dict, ctx: Context) -> None:
    """Assert that an operation fails with an exit code and a message.

    :param code: The exit code.
    :param match: A regular expression the message must match.
    :param op: The operation.
    :param params: Its parameters.
    :param ctx: The operation context."""
    with pytest.raises(OpError, match=match) as e:
        call(op, params, ctx)
    assert e.value.code == code


def test_proposal_set_new_folder(ctx: Context) -> None:
    """A proposal can be written before the first run, into a folder that is created."""
    out = call("proposal set", {"group": "warmup/sweep", "proposal": PROPOSAL, "author": "a"}, ctx)
    path = ctx.logdir / out["path"]
    saved = yaml.safe_load(path.read_text())
    assert saved["schema"] == 1 and saved["author"] == "a" and saved["user"]
    assert saved["predictions"][0]["name"] == "no-spike"
    shown = call("proposal show", {"group": "warmup/sweep"}, ctx)
    assert shown["status"] == "proposed" and shown["versions"][0]["frozen"] is False
    status = call("groups", {"from": "warmup"}, ctx)
    assert ["warmup/sweep", PROPOSAL["statement"], "proposed"] == status["rows"][-1][:3]
    again = call("proposal set", {"group": "warmup/sweep", "proposal": PROPOSAL}, ctx)
    assert "which no run had recorded" in again["lines"][1]
    fails(2, "reserved", "proposal set", {"group": "x/notes", "proposal": PROPOSAL}, ctx)


def test_proposal_validation(ctx: Context) -> None:
    """Invalid proposals are refused with exit code 3 and say how to fix them."""
    bad = [
        ({"statment": "x"}, "Did you mean 'statement'"),
        ({"statement": "x", "plan": {"runs": 0}}, "plan is"),
        ({"statement": "x", "predictions": [{"name": "a", "reduce": {"metric": "m"}}]}, "op is"),
        ({"statement": "x", "predictions": [{"name": "a", "test": "trend"}]}, "v1.1"),
        (
            {"statement": "x", "predictions": [{"name": "a", "kind": "manual"}] * 2},
            "unique",
        ),
        ({"rationale": "no statement"}, "statement is required"),
        ("statement: [unclosed", "not valid YAML"),
        (pred({"metric": "metric.val/acc.max"}), "a metric key like 'val/acc', not a field"),
        (pred({"metric": " val/acc"}), "without spaces"),
        (pred({"metric": "val/acc", "steps": [300, 100]}), "the first step comes first"),
        (pred({"metric": "val/acc", "steps": [1]}), r"reduce.steps is \[first, last\]"),
    ]
    for proposal, match in bad:
        fails(3, match, "proposal set", {"group": "new", "proposal": proposal}, ctx)


def pred(reduce: dict) -> dict:
    """A proposal with one prediction using a reduction.

    :param reduce: The prediction's reduce.
    :return: The proposal."""
    return {"statement": "x", "predictions": [{"name": "a", "reduce": reduce, "op": ">", "value": 0.5}]}


def test_numbers_written_as_text_are_read(ctx: Context) -> None:
    """YAML reads 1e-3 as text; values and margins written so are numbers all the same."""
    from beamtime.record.proposals import parse

    text = "statement: x\npredictions:\n- {name: a, reduce: {metric: val/loss}, op: <, value: 1e-3}\n"
    import yaml

    proposal = parse(yaml.safe_load(text), source="test")
    assert proposal.predictions[0].value == 1e-3
    compare = {"name": "b", "reduce": {"metric": "val/loss"}, "op": "<", "test": "compare",
               "a": {"config.lr": 0.1}, "b": {"config.lr": 0.01}, "margin": "5e-2"}  # fmt: skip
    assert parse({"statement": "x", "predictions": [compare]}, source="t").predictions[0].margin == 0.05


def test_frozen_versions_are_superseded(ctx: Context) -> None:
    """A version runs recorded is frozen: a new one needs a reason."""
    new = PROPOSAL | {"plan": {"runs": 15}}
    fails(3, "frozen", "proposal set", {"group": "scaling/lr-sweep", "proposal": new}, ctx)
    before = newest(ctx.logdir / "scaling/lr-sweep/proposal").stem
    out = call(
        "proposal set",
        {"group": "scaling/lr-sweep", "proposal": new, "reason": "metric renamed"},
        ctx,
    )
    saved = yaml.safe_load((ctx.logdir / out["path"]).read_text())
    assert saved["supersedes"] == {"version": before, "reason": "metric renamed"}
    assert not any("has logged" in line for line in out["lines"])
    shown = call("proposal show", {"group": "scaling/lr-sweep"}, ctx)
    assert shown["status"] == "proposed"
    assert [v["frozen"] for v in shown["versions"]] == [False, True]
    old = call("check", {"group": "scaling/lr-sweep", "version": before}, ctx)
    assert old["result"] == "pass"


def test_metric_warning(ctx: Context) -> None:
    """Predictions on metrics nobody logged are saved, with a warning."""
    typo = {"statement": "x", "predictions": [
        {"name": "a", "reduce": {"metric": "val/accc"}, "op": ">", "value": 0.5}
    ]}  # fmt: skip
    out = call("proposal set", {"group": "scaling/lr-sweep", "proposal": typo, "reason": "r"}, ctx)
    assert any("'val/accc'" in line for line in out["lines"])


def test_verdict_notes(ctx: Context) -> None:
    """A verdict judges every prediction of an existing version and carries the check."""
    sweep = "tokenizer/bpe-vs-unigram"
    version = newest(ctx.logdir / sweep / "proposal").stem
    base = {"group": sweep, "type": "verdict", "description": "Unigram wins."}
    fails(3, "--proposal", "note add", base, ctx)
    fails(3, "missing: unigram-wins", "note add", base | {"proposal": version}, ctx)
    fails(3, "no prediction nope", "note add", base | {
        "proposal": version, "verdict": {"unigram-wins": "confirmed", "nope": "refuted"},
        "overall": "confirmed"}, ctx)  # fmt: skip
    out = call(
        "note add",
        base
        | {
            "proposal": version,
            "verdict": {"unigram-wins": "confirmed"},
            "overall": "confirmed",
            "evidence": [f"{sweep}#unigram-wins"],
            "body": "Clear gain; see [[tokenizer/bpe-vs-unigram#unigram-wins]].",
            "author": "claude-test",
        },
        ctx,
    )
    doc = read_markdown_doc(ctx.logdir / out["path"], kind="note")
    assert doc.meta["check"]["unigram-wins"]["result"] == "pass"
    assert doc.meta["evidence"] == [{"prediction": f"{sweep}#unigram-wins"}]
    assert doc.meta["author"] == "claude-test" and "Clear gain" in doc.body
    folder = call("groups", {"from": sweep}, ctx)["rows"][0]
    assert folder[2:6] == ["concluded", "pass", "6 of 6 grid points", "confirmed"]
    check = call("check", {"group": sweep}, ctx)
    assert check["predictions"][0]["cited_by"][0]["id"] == doc.id


def test_notes_states_and_links(ctx: Context, roles: dict[str, str]) -> None:
    """Questions are open until resolved; superseded notes say so; runs show backlinks."""
    open_ = call("notes", {"open": True}, ctx)["entries"]
    assert [e["description"] for e in open_] == ["Is the gain the same for code?"]
    question = open_[0]["id"]
    fails(3, "no note", "note add", {"group": ".", "type": "idea", "description": "x",
                                     "resolves": ["20200101-000000-zzzz"]}, ctx)  # fmt: skip
    fails(3, "one line", "note add", {"group": ".", "type": "idea", "description": "a\nb"}, ctx)
    fails(3, "decision", "note add", {"group": ".", "type": "idea", "description": "x",
                                      "completes": ["scaling"]}, ctx)  # fmt: skip
    answer = call("note add", {"group": "tokenizer", "type": "observation",
                               "description": "Same gain on code.", "resolves": [question],
                               "evidence": [roles["killed"]]}, ctx)  # fmt: skip
    assert call("notes", {"open": True}, ctx)["entries"] == []
    fix = call("note add", {"group": "tokenizer", "type": "observation",
                            "description": "Gain is smaller on code.",
                            "supersedes": answer["version"]}, ctx)  # fmt: skip
    listed = {e["id"]: e for e in call("notes", {"from": "tokenizer", "full": True}, ctx)["entries"]}
    assert listed[answer["version"]]["state"] == f"superseded by {fix['version']}"
    current = call("notes", {"from": "tokenizer", "current": True}, ctx)["entries"]
    assert fix["version"] in {e["id"] for e in current}
    assert answer["version"] not in {e["id"] for e in current}
    assert listed[question]["state"] == "resolved" and "body" in listed[question]
    card = call("card", {"run": roles["killed"]}, ctx)
    assert {n["id"] for n in card["cited_by"]} >= {answer["version"]}
    assert card["proposals"][0]["check"] == "pass" and card["proposals"][0]["verdict"] == "confirmed"


def test_memory(ctx: Context) -> None:
    """Memory versions chain from the root down; new notes make them stale."""
    chain = call("memory show", {"group": "tokenizer/bpe-vs-unigram"}, ctx)["chain"]
    assert [m["group"] for m in chain] == ["."] and chain[0]["notes_since"] == 0
    call("note add", {"group": "tokenizer", "type": "idea", "description": "Try 128k."}, ctx)
    shown = call("memory show", {"group": "tokenizer"}, ctx)
    assert shown["chain"][0]["notes_since"] == 1 and "1 note(s)" in shown["meta"]["hints"][0]
    assert call("status", {}, ctx)["memory"]["notes_since"] == 1
    body = "---\nauthor: claude-test\n---\n## Current understanding\n- Unigram wins [[x]]\n"
    out = call("memory update", {"group": ".", "body": body}, ctx)
    assert out["lines"][1].startswith("covers notes until")
    assert call("memory show", {"group": "tokenizer"}, ctx)["chain"][0]["notes_since"] == 0
    call("memory update", {"group": "tokenizer", "body": "- big\n" * 2000}, ctx)
    chain = call("memory show", {"group": "tokenizer"}, ctx)["chain"]
    assert [m["group"] for m in chain] == [".", "tokenizer"]
    assert read_markdown_doc(newest(ctx.logdir / "memory"), kind="memory").meta["author"] == (
        "claude-test"
    )
    big = call("memory update", {"group": "tokenizer", "body": "x" * 7000}, ctx)
    assert "budget" in big["lines"][-1]
    assert len(versions(ctx.logdir / "tokenizer" / "memory")) == 2
    fails(3, "covers_until", "memory update", {"body": "x", "covers_until": "yesterday"}, ctx)


def test_notes_page_by_before(ctx: Context) -> None:
    """Notes come a page at a time: newest first, then the ones before the last shown."""
    for i in range(5):
        call("note add", {"group": "paging", "type": "idea", "description": f"Idea {i}."}, ctx)
    first = call("notes", {"from": "paging", "limit": 2}, ctx)
    assert [e["description"] for e in first["entries"]] == ["Idea 4.", "Idea 3."]
    assert first["more"] and first["meta"]["matched"] == 5
    second = call("notes", {"from": "paging", "limit": 2, "before": first["entries"][-1]["id"]}, ctx)
    assert [e["description"] for e in second["entries"]] == ["Idea 2.", "Idea 1."]
    last = call("notes", {"from": "paging", "limit": 2, "before": second["entries"][-1]["id"]}, ctx)
    assert [e["description"] for e in last["entries"]] == ["Idea 0."] and not last["more"]
