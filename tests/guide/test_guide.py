import re
import typing
from importlib.resources import files
from pathlib import Path

import pytest
import yaml

from beamtime.format.authored import NOTE_TYPES
from beamtime.guide import EXAMPLES, TOPICS, example
from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.ops.registry import BY_NAME, BY_TOOL, GuideParams
from beamtime.record.proposals import parse as parse_proposal
from beamtime.views import model as m

PARTS = files("beamtime.guide") / "parts"
NAMES = ["overview", *TOPICS]
TEXTS = {name: (PARTS / f"{name}.md").read_text() for name in NAMES}
LONGEST = 125
SWEEP = "scaling/lr-sweep"
WEB = Path(__file__).parents[2] / "web" / "src"
KINDS = {  # the block kinds the shell labels, as in web/src/bt/labels.ts
    "stat": "readings", "line": "charts", "scatter": "charts", "bar": "charts",
    "histogram": "charts", "table": "runs", "data_table": "table", "images": "images",
    "text": "text", "markdown": "text", "note": "note", "notes": "notes", "memory": "memory",
    "groups": "groups", "output": "output", "config": "config", "timeline": "timeline",
    "proposal": "predictions",
}  # fmt: skip


def fences(text: str) -> list[str]:
    """Take the fenced YAML snippets of a guide part.

    :param text: The Markdown.
    :return: The snippets."""
    return re.findall(r"```yaml\n(.*?)```", text, re.S)


def label_of(node: m.Node) -> str:
    """Port of ``labelOf`` in ``web/src/bt/labels.ts``: the margin label of a top-level node.

    :param node: The node.
    :return: The label; empty for none."""
    block = m.block_of(node)
    if block in KINDS:
        return KINDS[block]
    if block in ("row", "grid"):
        kinds = {KINDS.get(m.block_of(c)) for c in node.children}
        if len(kinds) == 1 and (only := next(iter(kinds))):
            return only
    title = (node.title or "").strip()
    return title.lower() if title and len(title.split()) <= 2 else ""


def test_every_topic_is_a_short_file_and_listed_in_the_overview() -> None:
    """Each topic exists, stays short, and the overview names it."""
    for name in NAMES:
        assert len(TEXTS[name].splitlines()) <= LONGEST, name
    for name in TOPICS:
        assert f"`{name}`" in TEXTS["overview"] or f"`{name}," in TEXTS["overview"] or (
            f" {name}`" in TEXTS["overview"]
        ), name


def test_registry_lists_the_topics(ctx: Context) -> None:
    """The ``guide`` parameter accepts every topic, and each answers."""
    annotated = typing.get_type_hints(GuideParams, include_extras=True)["part"]
    (literal,) = (a for a in typing.get_args(typing.get_args(annotated)[0]) if a is not type(None))
    allowed = set(typing.get_args(literal))
    assert allowed == {"examples", "blocks", *TOPICS}
    for topic in TOPICS:
        assert call("guide", {"part": topic}, ctx)["text"] == TEXTS[topic]


def test_named_operations_exist() -> None:
    """Every ``snake_case`` tool and every ``beamtime <command>`` a part names is an operation."""
    for name, text in TEXTS.items():
        for tool in re.findall(r"`((?:view|block|note|memory|proposal|source)_[a-z_]+)", text):
            assert tool in BY_TOOL, f"{name}: {tool}"
        for words in re.findall(r"`beamtime ((?:[a-z]+ ?){1,2})", text):
            first, *rest = words.split()
            assert first in BY_NAME or " ".join([first, *rest[:1]]) in BY_NAME, f"{name}: {words}"


def test_named_topics_exist() -> None:
    """Every ``guide <topic>`` a part names is a topic, an example, or a block."""
    known = {"examples", "blocks", *TOPICS}
    for name, text in TEXTS.items():
        for word in re.findall(r"`guide ([a-z][a-z-]*)", text):
            assert word in known, f"{name}: guide {word}"


def test_yaml_snippets_parse() -> None:
    """Snippets are views, lists of blocks or proposals, and each is accepted by its reader."""
    seen = 0
    for name, text in TEXTS.items():
        for snippet in fences(text):
            data = yaml.safe_load(snippet)
            seen += 1
            if isinstance(data, dict) and "body" in data:
                m.parse(data, source=name)
            elif isinstance(data, list):
                m.parse({"body": data}, source=name)
            elif isinstance(data, dict) and "predictions" in data:
                parse_proposal(data, source=name)
            else:
                assert {"params", "code", "where"} & set(data), f"{name}: unknown snippet"
    assert seen


def test_kit_names_exist_in_the_frontend() -> None:
    """Every ``bt.<group>.<Name>`` the kit parts name is in the kit's source."""
    if not WEB.is_dir():
        pytest.skip("no web sources")
    source = "".join(f.read_text() for f in WEB.rglob("*.ts"))
    for name in ("kit", "kit-api", "charts"):
        for path in re.findall(r"\bbt\.((?:[a-zA-Z]+\.)*[a-zA-Z]+)", TEXTS[name]):
            assert path.split(".")[-1] in source, f"{name}: bt.{path}"


def test_note_types_and_verdict_words_are_all_there() -> None:
    """The notes part covers every note type; the verdicts part the three judgements."""
    for type_ in NOTE_TYPES:
        assert f"`{type_}`" in TEXTS["notes"], type_
    for word in ("confirmed", "refuted", "inconclusive"):
        assert word in TEXTS["verdicts"]


def test_vocabulary_table_and_title_rule_are_in_the_parts() -> None:
    """The kit part has the vocabulary table; overview, kit and checklist say titles go left."""
    assert "bt.theme.tone" in TEXTS["kit"] and "bt.ui.Predictions" in TEXTS["kit"]
    assert "bt.ui.Sym" in TEXTS["checklist"]
    for name in ("overview", "kit", "checklist"):
        assert "left column" in TEXTS[name], name


@pytest.mark.parametrize("name", EXAMPLES)
def test_examples_validate_and_label_their_sections(ctx: Context, name: str) -> None:
    """An example has no errors, no wording lint, and a margin label on every top-level block."""
    group = {"direction": "scaling", "run": None}.get(name, SWEEP)
    if group is None:
        group = call("runs", {"from": SWEEP, "limit": 1}, ctx)["rows"][0][0]
    call("view new", {"group": group, "from": name, "name": f"ex-{name}"}, ctx)
    result = call("view validate", {"draft": f"ex-{name}", "render": False}, ctx)
    assert result["ok"], result["findings"]
    lints = ("words", "caption", "heading")
    assert not [f for f in result["findings"] if any(w in f["message"] for w in lints)]
    view = m.parse(yaml.safe_load(example(name, ctx, group)), source=name)
    assert all(label_of(n) for n in view.body), [m.block_of(n) for n in view.body]
