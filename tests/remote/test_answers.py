import copy
from typing import Any

import pytest

from beamtime.ops.answers import ANSWERS, flagged, merged, placed


def test_placed_leaves_what_users_wrote_alone() -> None:
    """Paths get the source; configs, proposals, logged tables and conditions keep their values."""
    card = {
        "kind": "card",
        "run": {"id": "r", "path": "g/r"},
        "config": {"group": "norm", "path": "data/cifar"},
        "proposals": [{"group": "g", "version": "v"}],
        "meta": {"source": "local", "from": "g"},
    }
    out = placed(card, "box")
    assert out["run"]["path"] == "@box/g/r" and out["proposals"][0]["group"] == "@box/g"
    assert out["config"] == {"group": "norm", "path": "data/cifar"}
    assert out["meta"] == {"source": "@box", "from": "@box/g"}
    data = {"entries": [{"run": "r", "step": 1, "path": "_data/x.png",
                         "columns": {"group": ["a"], "path": ["b"]}}]}  # fmt: skip
    entry = placed(data, "box")["entries"][0]
    assert entry["path"] == "_data/x.png" and entry["columns"] == {"group": ["a"], "path": ["b"]}
    shown = placed({"group": "g", "proposal": {"predictions": [{"where": {"group": "x"}}]}}, "box")
    assert shown["proposal"]["predictions"][0]["where"] == {"group": "x"}
    table = placed({"columns": ["path", "runs"], "rows": [[".", 1], ["g", 2]]}, "box")
    assert table["rows"] == [["@box", 1], ["@box/g", 2]]


def test_a_blocks_proposal_call_gets_the_source() -> None:
    """The proposal block's call is a place under a key of user content; its answer is not."""
    call = {"method": "proposal_show", "params": {"group": "exp/a"}, "scope": "exp/a"}
    data = {"proposal": call, "check": call | {"method": "check"}}
    out = placed({"blocks": [{"data": data}]}, "au")["blocks"][0]["data"]
    for found in out.values():
        assert found["params"]["group"] == "@au/exp/a" and found["scope"] == "@au/exp/a"
    shown = {"group": "exp/a", "proposal": {"yaml": "group: x\n", "group": "x"}}
    assert placed(shown, "au")["proposal"] == {"yaml": "group: x\n", "group": "x"}


def test_merged_sums_matches_and_refuses_what_does_not_federate() -> None:
    """A listing merges with local first; a kind that is not a listing raises."""
    one = {"kind": "groups", "rows": [["@a"]], "meta": {"matched": 1}}
    two = {"kind": "groups", "rows": [["@b"]], "meta": {"matched": 2}}
    out = merged("groups", [("local", one), ("b", two)], {}, "cli")
    assert out["rows"] == [["@a"], ["@b"]] and out["meta"] == {"matched": 3, "source": "."}
    with pytest.raises(ValueError, match="no merge for 'card'"):
        merged("card", [("local", one)], {}, "cli")


def test_wait_keeps_statuses() -> None:
    """A wait answer has no places in `changed`: `from` is a status and `run` a run id."""
    wait = {
        "kind": "wait",
        "met": True,
        "changed": [{"run": "20260101-aaaa", "name": "n", "from": "running", "to": "finished"}],
        "runs": {"finished": 1},
        "matching": ["20260101-aaaa"],
        "meta": {},
    }
    out = placed(wait, "box")
    assert out["changed"] == wait["changed"] and out["matching"] == wait["matching"]
    assert out["runs"] == {"finished": 1}


def test_compare_places_only_its_targets() -> None:
    """A compare answer's targets are places; its statuses, metrics and differences are not."""
    compare = {
        "kind": "compare",
        "targets": [
            {"target": "scaling", "runs": 2, "status": {"finished": 2}, "code": ["abc"]},
            {"target": "20260101-aaaa", "runs": 1, "status": {"running": 1}, "code": []},
        ],
        "same_code": False,
        "differences": [{"key": "config.group", "values": ["a", "b"], "same_split_as": None}],
        "rows": [{"metric": "loss", "values": [1.0, 2.0], "delta": 1.0}],
        "meta": {"matched": 1},
    }
    out = placed(compare, "box")
    assert [t["target"] for t in out["targets"]] == ["@box/scaling", "@box/20260101-aaaa"]
    assert {k: v for k, v in out.items() if k != "targets"} == {
        k: v for k, v in compare.items() if k != "targets"
    }
    assert [{k: v for k, v in t.items() if k != "target"} for t in out["targets"]] == [
        {k: v for k, v in t.items() if k != "target"} for t in compare["targets"]
    ]


def test_compare_target_idempotent() -> None:
    """A target that names a source stays; placing twice gives the same answer."""
    compare = {"kind": "compare", "targets": [{"target": "@other/g"}, {"target": "g"}]}
    once = placed(compare, "box")
    assert [t["target"] for t in once["targets"]] == ["@other/g", "@box/g"]
    assert placed(once, "box") == once


def test_local_paths_map_onto_the_remote() -> None:
    """A path that names no source, `@local/...` included, is placed on the remote, once."""
    table = {"columns": ["path"], "rows": [["@local/g"], ["@local"], ["g"], ["@other/g"]]}
    out = placed(table, "box")
    assert out["rows"] == [["@box/g"], ["@box"], ["@box/g"], ["@other/g"]]
    assert placed(out, "box") == out


def table(source: str, lr: list[float]) -> dict:
    """An aggregated run table as one source answers it.

    :param source: The source's name.
    :param lr: One learning rate per group row.
    :return: The answer, with a runs column and one aggregate column."""
    rows = [[[f"{source}-{i}"], v, v * 2] for i, v in enumerate(lr)]
    return {"kind": "runs", "columns": ["runs", "config.lr", "val/acc"], "rows": rows, "meta": {}}


def test_by_labels_each_row_with_its_source() -> None:
    """Aggregated rows get a source column after runs and keep each source's order, local first."""
    answers = [("local", table("l", [0.3, 0.1])), ("box", table("b", [0.2, 0.05]))]
    out = merged("runs", answers, {"by": ["config.lr"]}, "cli")
    assert out["columns"] == ["runs", "source", "config.lr", "val/acc"]
    assert [r[1] for r in out["rows"]] == [".", ".", "@box", "@box"]
    assert [r[2] for r in out["rows"]] == [0.3, 0.1, 0.2, 0.05]


def test_single_source_no_label() -> None:
    """With one source there is nothing to tell apart."""
    out = merged("runs", [("box", table("b", [0.2, 0.1]))], {"by": ["config.lr"]}, "cli")
    assert out["columns"] == ["runs", "config.lr", "val/acc"]
    assert [r[1] for r in out["rows"]] == [0.2, 0.1]


def test_by_with_sort() -> None:
    """A user sort applies to the aggregated columns, across sources."""
    answers = [("local", table("l", [0.3, 0.1])), ("box", table("b", [0.2, 0.05]))]
    params = {"by": ["config.lr"], "sort": ["config.lr"]}
    out = merged("runs", answers, params, "cli")
    assert [r[2] for r in out["rows"]] == [0.05, 0.1, 0.2, 0.3]
    assert [r[1] for r in out["rows"]] == ["@box", ".", "@box", "."]


def test_seeds_federated() -> None:
    """seeds labels and keeps order like by."""
    answers = [("local", table("l", [0.3])), ("box", table("b", [0.2]))]
    out = merged("runs", answers, {"seeds": ["config.seed"]}, "cli")
    assert [r[1] for r in out["rows"]] == [".", "@box"]


def test_limit_cut_is_flagged() -> None:
    """Rows dropped at the merged limit, here every remote group, mark the answer cut."""
    answers = [("local", table("l", [0.3, 0.1])), ("box", table("b", [0.2, 0.05]))]
    out = merged("runs", answers, {"by": ["config.lr"], "limit": 2}, "cli")
    assert [r[1] for r in out["rows"]] == [".", "."]
    assert out["meta"]["cut"] is True and out["meta"]["shown"] == 2


def test_merged_sums_groups_and_means_like_matched() -> None:
    """Every source's group and seed-mean counts add up next to its matched runs."""
    one = table("l", [0.3, 0.1]) | {"meta": {"matched": 4, "groups": 2}}
    two = table("b", [0.2]) | {"meta": {"matched": 3, "groups": 1}}
    out = merged("runs", [("local", one), ("box", two)], {"by": ["config.lr"]}, "cli")
    assert out["meta"]["matched"] == 7 and out["meta"]["groups"] == 3
    assert "means" not in out["meta"]
    one["meta"] = {"matched": 4, "means": 2}
    two["meta"] = {"matched": 3, "means": 1}
    out = merged("runs", [("local", one), ("box", two)], {"seeds": ["config.seed"]}, "cli")
    assert out["meta"]["means"] == 3 and "groups" not in out["meta"]


RUN = "20260101-aaaa"
SRC = {"source": ".", "from": "g"}

KINDS = {
    "card": (
        {
            "run": {"id": RUN, "path": "g/r", "name": "group", "proposals": {".": "v1"}},
            "config": {"group": "norm", "path": "data/cifar"},
            "metrics": {"group": {"last": 1.0}},
            "proposals": [{"group": ".", "version": "v1", "statement": "path"}],
            "checkpoints": [{"name": "path", "location": "/scratch/ckpt"}],
            "events": [{"type": "created", "description": "from g"}],
        },
        [("run", "path"), ("proposals", 0, "group")],
    ),
    "output": ({"run": RUN, "rank": 0, "lines": ["group g"]}, []),
    "resume": (
        {"run": RUN, "status": "failed", "cwd": "/home/u/g", "command": ["python", "g"]},
        [],
    ),
    "status": (
        {"root": "/home/u/g", "logdir": "/home/u/g/beamtime", "runs": {"failed": 1}},
        [],
    ),
    "data": (
        {"key": "group", "entries": [{"run": RUN, "step": 1, "path": "_data/x.png"}]},
        [],
    ),
    "series": (
        {"curves": [{"run": RUN, "metric": "group", "by": {"group": "a"}, "source": "preview"}]},
        [],
    ),
    "keys": (
        {"metrics": {"columns": ["key"], "rows": [["path"]]}, "status": {"running": 1}},
        [],
    ),
    "groups": (
        {"columns": ["path", "status"], "rows": [[".", "ok"], ["g", "from"]]},
        [("rows", 0, 0), ("rows", 1, 0)],
    ),
    "runs": (
        {"columns": ["run.id", "run.path", "config.path"], "rows": [[RUN, "g/r", "data"]]},
        [("rows", 0, 1)],
    ),
    "timeline": (
        {
            "entries": [
                {"kind": "event", "run": RUN, "type": "created", "description": "g"},
                {"kind": "note", "id": "n1", "group": "g", "run": None, "description": "g"},
            ]
        },
        [("entries", 1, "group")],
    ),
    "notes": (
        {
            "group": "g",
            "entries": [{"id": "n1", "group": "g/s", "type": "question", "body": "see g"}],
            "more": False,
        },
        [("group",), ("entries", 0, "group")],
    ),
    "note": ({"id": "n1", "group": "g", "body": "g"}, [("group",)]),
    "memory": (
        {"group": "g/s", "chain": [{"group": ".", "version": "v", "body": "g"}], "budget": 9},
        [("group",), ("chain", 0, "group")],
    ),
    "proposal": (
        {"group": "g", "proposal": {"group": "x", "statement": "g"}, "versions": []},
        [("group",)],
    ),
    "check": (
        {"group": "g", "version": "v1", "predictions": [{"name": "group", "result": "pass"}]},
        [("group",)],
    ),
    "file": (
        {"group": "g", "path": "data/fit.csv", "columns": ["path"], "rows": [["data/x"]]},
        [("group",)],
    ),
    "digest": (
        {"group": "g", "runs": {"failed": 1}, "failures": [{"status": "failed", "runs": [RUN]}]},
        [("group",)],
    ),
    "logs": (
        {"entries": [{"run": RUN, "name": "n", "lines": ["path g"]}], "tracebacks": []},
        [],
    ),
    "diagnose": (
        {"entries": [{"run": RUN, "status": "failed", "flags": {"missing": ["group"]}}]},
        [],
    ),
    "plan missing": (
        {"group": "g", "form": "grid", "entries": [{"config": {"group": "a"}, "runs": {}}]},
        [("group",)],
    ),
}


def at_box(v: str) -> str:
    """Place a path on the remote ``box``, as ``placed`` does.

    :param v: A path without a source.
    :return: The path on ``box``."""
    return "@box" if v == "." else f"@box/{v}"


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_every_kind_places_its_own_fields(kind: str) -> None:
    """Places get the source; run ids, statuses, keys and what users wrote stay as they are."""
    answer, places = KINDS[kind]
    answer = {"kind": kind, **answer, "meta": answer.get("meta", {}) | SRC}
    expected = copy.deepcopy(answer)
    expected["meta"] |= {"source": "@box", "from": "@box/g"}
    for path in places:
        holder: Any = expected
        for step in path[:-1]:
            holder = holder[step]
        holder[path[-1]] = at_box(holder[path[-1]])
    assert kind in ANSWERS
    assert placed(answer, "box") == expected
    assert placed(placed(answer, "box"), "box") == expected


def test_old_remotes_say_local() -> None:
    """A remote of version 0.2 names itself ``local``; it is placed like ``.``."""
    out = placed({"kind": "card", "run": {"path": "g"}, "meta": {"source": "local"}}, "box")
    assert out["meta"]["source"] == "@box"


def test_a_view_file_keeps_its_relative_path() -> None:
    """A file's path is inside the group's view; a table column called path is the user's."""
    out = placed({"kind": "file", "group": "g", "path": "fit.csv", "columns": ["path"],
                  "rows": [["x"]]}, "box")  # fmt: skip
    assert out["path"] == "fit.csv" and out["rows"] == [["x"]]


def test_series_curves_name_their_source_like_everything_else() -> None:
    """With several sources' curves, ``by.source`` is ``.`` for this machine and ``@name``."""
    curves = {"kind": "series", "curves": [{"by": {"config.lr": 0.1}}], "meta": {}}
    out = merged("series", [("local", curves), ("box", curves)], {}, "cli")
    assert [c["by"]["source"] for c in out["curves"]] == [".", "@box"]


def test_a_source_that_cut_shows_at_the_top() -> None:
    """The merged answer says who cut, unless a cursor already leads on."""
    states = [{"name": ".", "state": "connected"}, {"name": "@a", "state": "connected", "cut": True},
              {"name": "@b", "state": "connected", "cut": True}]  # fmt: skip
    out = flagged({"meta": {"sources": states}})
    assert out["meta"]["cut"] is True
    assert out["meta"]["hint"] == "narrow from or where to see all of @a, @b"
    paged = {"meta": {"sources": states, "next": "5", "hint": "pass cursor"}}
    assert flagged(paged)["meta"] == {"sources": states, "next": "5", "hint": "pass cursor"}
    assert "cut" not in flagged({"meta": {"sources": states[:1]}})["meta"]
