import json
import subprocess
import sys
from pathlib import Path

import pytest

from beamtime import bt, remote
from beamtime.ops.context import OpError
from beamtime.ops.registry import OPS

GROUP = "scaling/lr-sweep"


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record the operations that reach the routing layer.

    :param monkeypatch: Pytest's monkeypatch.
    :return: The names of the operations called, in order."""
    seen: list[str] = []
    real = remote.answer

    def answer(name, params, ctx):
        seen.append(name)
        return real(name, params, ctx)

    monkeypatch.setattr(remote, "answer", answer)
    return seen


def test_bt_answers_a_query(project: Path) -> None:
    """A read answers whole, as a plain dict."""
    found = bt.runs({"from": GROUP, "limit": 5})
    assert found["kind"] == "runs"
    assert found["rows"]


def test_bt_ops_name_what_agents_may_call(project: Path) -> None:
    """``ops()`` lists every non-user-only operation and neither a user-only one nor ``script``."""
    names = set(bt.ops())
    assert {"runs", "status", "importance"} <= names
    assert not {op.tool for op in OPS if op.user_only} & names
    assert "script" not in names


def test_bt_hides_user_only(project: Path) -> None:
    """A user-only operation is no attribute and no call."""
    user_only = next(op.tool for op in OPS if op.user_only)
    with pytest.raises(AttributeError):
        getattr(bt, user_only)
    with pytest.raises(KeyError):
        bt.call(user_only)


def test_bt_has_no_script() -> None:
    """No code runs code: ``bt.script`` does not exist."""
    with pytest.raises(AttributeError):
        bt.script
    with pytest.raises(KeyError):
        bt.call("script")


def test_bt_serves_a_second_read_from_the_cache(project: Path, calls: list[str]) -> None:
    """The second identical read is answered from ``.beamtime/bt-cache/`` without the operation."""
    first = bt.runs({"from": GROUP, "limit": 3})
    second = bt.runs({"from": GROUP, "limit": 3})
    assert first == second
    assert calls == ["runs"]
    assert list((project / ".beamtime" / "bt-cache").glob("runs-*.json"))
    assert (project / ".beamtime" / ".gitignore").is_file()
    bt.runs({"from": GROUP, "limit": 4})
    assert calls == ["runs", "runs"]


def test_bt_never_caches_the_moment(project: Path, calls: list[str]) -> None:
    """``status`` is asked again every time."""
    bt.status()
    bt.status()
    assert calls == ["status", "status"]
    assert not list((project / ".beamtime" / "bt-cache").glob("status-*"))


def test_bt_never_caches_a_write(project: Path, calls: list[str]) -> None:
    """A write runs every time and leaves nothing in the cache."""
    for _ in range(2):
        bt.note_add(group=GROUP, type="observation", description="seen", body="a note")
    assert calls == ["note add", "note add"]
    assert not (project / ".beamtime" / "bt-cache").exists()


def test_bt_write_drops_the_cache(project: Path, calls: list[str]) -> None:
    """A read after a write sees the write, not the answer kept before it."""
    before = bt.notes({"from": GROUP})
    bt.note_add(group=GROUP, type="observation", description="seen", body="a note")
    after = bt.notes({"from": GROUP})
    assert after != before
    assert calls == ["notes", "note add", "notes"]


def test_bt_skips_unserializable(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An answer that is not JSON is returned and not saved."""
    answer = {"kind": "runs", "odd": object()}
    monkeypatch.setattr(remote, "answer", lambda *a: answer)
    assert bt.runs({"from": GROUP}) is answer
    assert not list((project / ".beamtime" / "bt-cache").glob("runs-*"))


def test_bt_names_the_parameters(project: Path) -> None:
    """A wrong parameter name is answered with the names the operation takes."""
    with pytest.raises(OpError, match="runs takes: .*from"):
        bt.runs(frm=GROUP)


def test_bt_underscore_is_dropped(project: Path) -> None:
    """``from_`` is the parameter ``from``."""
    assert bt.runs(from_=GROUP, limit=1)["kind"] == "runs"


def test_bt_routes_like_mcp(project: Path, calls: list[str]) -> None:
    """An ``@source`` target reaches the routing layer, not a ``KeyError``."""
    with pytest.raises(OpError):
        bt.runs({"from": "@nowhere/x"})
    assert calls == ["runs"]


def test_bt_writes_as_the_author_of_the_environment(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A write without an author takes ``BEAMTIME_AUTHOR``, else ``agent``."""
    sent: list[dict] = []
    monkeypatch.setattr(remote, "answer", lambda name, given, ctx: sent.append(given) or {})
    monkeypatch.delenv("BEAMTIME_AUTHOR", raising=False)
    bt.note_add(group=GROUP, type="observation", description="a", body="b")
    monkeypatch.setenv("BEAMTIME_AUTHOR", "claude-x")
    bt.note_add(group=GROUP, type="observation", description="a", body="b")
    assert [s["author"] for s in sent] == ["agent", "claude-x"]


def test_bt_describes_parameters(project: Path) -> None:
    """``params(name)`` gives the summary and a JSON schema."""
    described = bt.params("runs")
    assert described["summary"]
    assert "from" in described["params"]["properties"]


def test_bt_works_in_an_isolated_child(project: Path) -> None:
    """``python -I`` run in the root imports ``bt`` and calls an operation."""
    code = "from beamtime import bt; import json; print(json.dumps([len(bt.ops()), bt.status()['kind']]))"
    out = subprocess.run(
        [sys.executable, "-I", "-c", code], cwd=project, capture_output=True, text=True, check=True
    )
    count, kind = json.loads(out.stdout)
    assert kind == "status"
    assert count == len(bt.ops())
