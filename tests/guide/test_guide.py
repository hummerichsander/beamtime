import json
import re
import typing
from importlib.resources import files
from pathlib import Path

import pytest
import yaml

from beamtime.format.authored import NOTE_TYPES
from beamtime.guide import EXAMPLES, TOPICS, example, read, values_of
from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.ops.registry import BY_NAME, BY_TOOL, GuideParams
from beamtime.record.proposals import parse as parse_proposal
from beamtime.views import code
from beamtime.views import model as m

PARTS = files("beamtime.guide") / "parts"
NAMES = ["index", *TOPICS]
TEXTS = {name: (PARTS / f"{name}.md").read_text(encoding="utf-8") for name in NAMES}
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
    """Port of ``labelOf`` in ``web/src/bt/labels.ts``: the section label of a top-level node.

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


def test_every_topic_is_a_short_file() -> None:
    """Each topic and the index exist and stay short."""
    for name in NAMES:
        assert len(TEXTS[name].splitlines()) <= LONGEST, name


def test_every_topic_is_listed_in_the_index() -> None:
    """The index names every topic, plus the examples and the blocks."""
    for name in (*TOPICS, "examples", "blocks"):
        assert re.search(rf"`{name}[`, \[]", TEXTS["index"]), name


def test_registry_lists_the_topics(ctx: Context) -> None:
    """The ``guide`` parameter accepts every topic, and each answers."""
    annotated = typing.get_type_hints(GuideParams, include_extras=True)["part"]
    (literal,) = (a for a in typing.get_args(typing.get_args(annotated)[0]) if a is not type(None))
    allowed = set(typing.get_args(literal))
    assert allowed == {"examples", "blocks", *TOPICS}
    for topic in TOPICS:
        assert call("guide", {"part": topic}, ctx)["text"] == read(
            f"{topic}.md", ctx.settings.agent
        )


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
    source = "".join(f.read_text(encoding="utf-8") for f in WEB.rglob("*.ts"))
    for name in ("kit", "kit-api", "charts", "type"):
        for path in re.findall(r"\bbt\.((?:[a-zA-Z]+\.)*[a-zA-Z]+)", TEXTS[name]):
            assert path.split(".")[-1] in source, f"{name}: bt.{path}"


def test_type_topic_names_real_classes_with_their_families() -> None:
    """The type part is short, opens with the family rule, is linked, and its table follows the tokens."""
    from beamtime.guide.skills import SKILLS

    design = Path(__file__).parents[2] / "design"
    if not design.is_dir():
        pytest.skip("no design sources")
    text = TEXTS["type"]
    assert len(text.split()) < 900 and "family says who wrote the text" in text.split("\n\n")[1]
    assert "type" in SKILLS["beamtime-views"][1]
    for name in ("index", "kit", "kit-api", "anti-patterns", "checklist"):
        assert "guide type" in TEXTS[name] or "`type`" in TEXTS[name], name

    groups = json.loads((design / "tokens.json").read_text(encoding="utf-8"))["type"]["groups"]
    family = {s["name"]: g["name"].lower() for g in groups for s in g["styles"]}
    css = (design / "tokens.css").read_text(encoding="utf-8") + (design / "components.css").read_text(encoding="utf-8")
    rows = re.findall(r"^\| `(\w+)` \| ([a-z ]+?)\b", text, re.M)
    assert {"body", "heading", "small", "num", "number", "prose", "caption", "code"} <= {n for n, _ in rows}
    for name, font in rows:
        assert re.search(rf"\.{name}\b[^{{]*[{{,]", css), f"no selector .{name}"
        if name in family:
            assert font.split()[0] == family[name], f"{name} is {family[name]}, the part says {font}"
    for name in re.findall(r'class="([^"]+)"', text):
        for cls in name.split():
            assert re.search(rf"\.{cls}\b", css), cls
    for snippet in re.findall(r"```js\n(.*?)```", text, re.S):
        assert code.problems("export default function render(root) {}\n" + snippet) == []


def test_note_types_and_verdict_words_are_all_there() -> None:
    """The notes part covers every note type; the verdicts part the three judgements."""
    for type_ in NOTE_TYPES:
        assert f"`{type_}`" in TEXTS["notes"], type_
    for word in ("confirmed", "refuted", "inconclusive"):
        assert word in TEXTS["verdicts"]


def test_vocabulary_table_and_title_rule_are_in_the_parts() -> None:
    """The kit part has the vocabulary table; views, kit and checklist say titles become section labels."""
    assert "bt.theme.tone" in TEXTS["kit"] and "bt.ui.Predictions" in TEXTS["kit"]
    assert "bt.ui.Sym" in TEXTS["checklist"]
    for name in ("views", "kit", "checklist"):
        assert "section label" in TEXTS[name], name


@pytest.mark.parametrize("name", EXAMPLES)
def test_examples_validate_and_label_their_sections(ctx: Context, name: str) -> None:
    """An example has no errors, no wording lint, and a section label on every top-level block."""
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


def with_agent(project: Path, agent: str) -> Context:
    """Write the project's ``agent`` setting and make a context that reads it.

    :param project: The project root.
    :param agent: The YAML value of ``agent``.
    :return: The context."""
    (project / "beamtime.yaml").write_text(f"agent: {agent}\n", encoding="utf-8")
    return Context.make(caller="cli")


def defaults_of(ctx: Context) -> list[str]:
    """Take the lines of the index's Defaults section.

    :param ctx: The operation context.
    :return: Its bullet lines."""
    text = call("guide", {}, ctx)["text"]
    section = text.split("## Defaults")[1]
    return [line for line in section.splitlines() if line.startswith("- ")]


def test_defaults_without_agent_are_all_marked_default(ctx: Context) -> None:
    """A project without ``agent`` gets today's rules, every configurable line marked (default)."""
    lines = defaults_of(ctx)
    assert "- Ask before you launch a run. (default)" in lines
    assert any("3 seeds per point; significance 0.95. (default)" in line for line in lines)
    assert any("at most 2 render rounds. (default)" in line for line in lines)
    assert any("near 1500 tokens" in line for line in lines)
    assert lines[-1] == "- Never run user commands; hand the user the exact command. (fixed)"
    assert all(line.endswith(("(default)", "(fixed)")) for line in lines)


def test_no_conventions(ctx: Context) -> None:
    """Without detected conventions the metric and seed line is left out."""
    assert not [line for line in defaults_of(ctx) if "Main metric" in line or "seeds in" in line]


def test_agent_settings_reach_the_guide(project: Path) -> None:
    """Style and keys change the Defaults, the parts and the memory budget."""
    ctx = with_agent(
        project,
        "{style: hands-on, seeds: 5, main_metric: val/loss, direction: min, seed_key: config.seed,"
        " memory_tokens: 500}",
    )
    text = call("guide", {}, ctx)["text"]
    lines = defaults_of(ctx)
    assert "- You may launch runs. (hands-on)" in lines
    assert any("5 seeds per point" in line and line.endswith("(beamtime.yaml)") for line in lines)
    metric = "- Main metric val/loss, lower is better; seeds in config.seed."
    assert f"{metric} (beamtime.yaml)" in lines
    assert "From this project's beamtime.yaml (agent: hands-on)" in text
    assert "plan 5 seeds per point" in call("guide", {"part": "proposals"}, ctx)["text"]
    assert "(5 in this project)" in call("guide", {"part": "predictions"}, ctx)["text"]
    assert "about 500 tokens" in call("guide", {"part": "memory"}, ctx)["text"]


def test_no_placeholder_survives(project: Path) -> None:
    """No part's output keeps a ``{{agent.*}}`` placeholder."""
    ctx = with_agent(project, "{style: analysis}")
    for part in (None, *TOPICS):
        assert "{{agent." not in call("guide", {"part": part}, ctx)["text"], part


def test_memory_update_warns_at_the_configured_budget(project: Path) -> None:
    """``memory update`` warns beyond ``memory_tokens * 4`` characters, and ``memory show`` says it."""
    ctx = with_agent(project, "{memory_tokens: 100}")
    body = "x" * 401
    out = call("memory update", {"group": "tokenizer", "body": body}, ctx)
    assert "beyond the budget of about 400 (100 tokens)" in out["lines"][-1]
    assert call("memory show", {"group": "tokenizer"}, ctx)["budget"] == 400


def test_proposal_words_reach_the_guide(project: Path) -> None:
    """The Defaults and the proposals part name the limit; ``analysis`` leaves the line out."""
    line = "- Keep a proposal near 150 words: statement, rationale and prediction descriptions."
    assert f"{line} (default)" in defaults_of(Context.make(caller="cli"))
    ctx = with_agent(project, "{style: careful}")
    assert f"{line} (careful)" in defaults_of(ctx)
    assert "near 150 words" in call("guide", {"part": "proposals"}, ctx)["text"]
    ctx = with_agent(project, "{proposal_words: 80}")
    assert "near 80 words" in call("guide", {"part": "proposals"}, ctx)["text"]
    assert any("near 80 words" in x and x.endswith("(beamtime.yaml)") for x in defaults_of(ctx))
    ctx = with_agent(project, "{style: analysis}")
    assert not [x for x in defaults_of(ctx) if "Keep a proposal" in x]


def test_topics_naming_family_tools_carry_the_line(project: Path) -> None:
    """Topics that tell the agent to call a family tool say so under ``core`` and not under ``all``."""
    pytest.importorskip("mcp")
    from beamtime.guide import TOOLS_MORE
    from beamtime.mcp.server import FAMILIES

    members = {name for names in FAMILIES.values() for name in names}
    only_the_checker = {"charts", "anti-patterns", "kit-api", "type"}
    core, every = with_agent(project, "{mcp_tools: core}"), with_agent(project, "{mcp_tools: all}")
    for topic in TOPICS:
        named = members & set(re.findall(r"`(\w+)", TEXTS[topic]))
        text = call("guide", {"part": topic}, core)["text"]
        assert (TOOLS_MORE in text) == (bool(named) and topic not in only_the_checker), topic
        if TOOLS_MORE in text:
            all_text = call("guide", {"part": topic}, every)["text"]
            assert text.replace(f"{TOOLS_MORE}\n\n", "") == all_text, topic
            assert "\n\n\n" not in all_text and "tools_more" not in all_text, topic


def test_mcp_tools_is_not_listed_in_the_defaults(project: Path) -> None:
    """The knob is for the user: the default answer does not mention it, under either value."""
    for value in ("core", "all"):
        text = call("guide", {}, with_agent(project, f"{{mcp_tools: {value}}}"))["text"]
        assert "mcp_tools" not in text and "tools_more" not in text


def test_data_files_topic_is_short_and_linked() -> None:
    """The topic stays under 100 lines; the index, the analysis part and the views skill name it."""
    from beamtime.guide.skills import SKILLS

    assert len(TEXTS["data-files"].splitlines()) <= 100
    assert "data-files" in SKILLS["beamtime-views"][1]
    for name in ("index", "analysis", "kit", "kit-api"):
        assert "data-files" in TEXTS[name], name


def test_defaults_point_to_data_files(ctx: Context) -> None:
    """The defaults line on data files names `view_data` and the topic."""
    (line,) = [s for s in defaults_of(ctx) if "data_table" in s]
    assert "view_data" in line and "(`guide data-files`)" in line


def test_data_files_recipe(ctx: Context, project: Path) -> None:
    """The recipe's commands run in order with the topic's own snippets and save a valid view."""
    text = TEXTS["data-files"]
    blocks = [b for s in fences(text) for b in yaml.safe_load(s)]
    script = re.search(r"```js\n(.*?)```", text, re.S).group(1)
    table, chart = blocks
    assert "data/fit.csv" in str(table) and "data/fit.csv" in str(chart)

    source = project / "results" / "fit.csv"
    source.parent.mkdir()
    source.write_text("lr,pred_acc\n0.0001,0.52\n0.001,0.71\n0.01,0.64\n", encoding="utf-8")
    call("view new", {"group": SWEEP, "name": "fit"}, ctx)
    answer = call("view data", {"draft": "fit", "file": "results/fit.csv", "name": "fit.csv"}, ctx)
    assert answer["ref"] == "data/fit.csv" and answer["columns"] == ["lr", "pred_acc"]

    draft = project / ".beamtime" / "drafts" / "fit"
    view = yaml.safe_load((draft / "view.yaml").read_text(encoding="utf-8"))
    view["finding"] = "lr 1e-3 is predicted best"
    view["body"].append({"section": {"id": "fit", "title": "fit", "children": blocks}})
    (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False), encoding="utf-8")
    (draft / "code").mkdir(exist_ok=True)
    (draft / "code" / "fit-chart.js").write_text(script, encoding="utf-8")

    result = call("view validate", {"draft": "fit", "render": False}, ctx)
    assert result["ok"], result["findings"]
    assert not [f for f in result["findings"] if "data" in f["message"]], result["findings"]
    saved = call("view save", {"draft": "fit", "message": "predicted accuracy"}, ctx)
    assert saved["version"]
    note = call(
        "note add",
        {"group": SWEEP, "type": "observation", "description": "fit.csv from results/fit.csv"},
        ctx,
    )
    assert note["kind"] == "note add"
    (stored,) = (project / "beamtime" / SWEEP / "view" / "data").glob("*-fit.csv")
    assert stored.read_bytes() == source.read_bytes()
    query = {"file": {"path": f"data/{stored.name}", "view": SWEEP, "columns": ["lr"]}}
    shown = call("query", {"query": query}, ctx)
    assert [r[0] for r in shown["rows"]] == [0.0001, 0.001, 0.01]


def seeded_keys(fields: list[str], seed: str | None) -> dict[str, typing.Any]:
    """Make a ``keys`` answer whose config varies over ``fields``, with the group's seed key.

    :param fields: The varying config keys.
    :param seed: The group's seed key, or ``None``.
    :return: The answer, as far as the guide reads it."""
    rows = [[k, 3, [0, 1, 2]] for k in fields]
    return {
        "metrics": {"rows": [["val/loss", 3, 10, False, 3]]},
        "config": {"rows": rows, "varying": fields, "seed": seed},
        "data": {"rows": []},
    }


@pytest.mark.parametrize(
    ("seed", "fields", "seeds", "swept"),
    [
        (
            "config.trainer.seed",
            ["config.trainer.seed", "config.lr"],
            "config.trainer.seed",
            "config.lr",
        ),
        ("config.seed", ["config.seed", "config.lr"], "config.seed", "config.lr"),
    ],
)
def test_example_values_use_the_groups_seed_key(
    ctx: Context,
    monkeypatch: pytest.MonkeyPatch,
    seed: str,
    fields: list[str],
    seeds: str,
    swept: str,
) -> None:
    """A group seeded by ``trainer.seed`` fills ``seeds`` with it and never sweeps it."""

    def answer(op: str, params: dict[str, typing.Any], ctx: Context) -> dict[str, typing.Any]:
        return seeded_keys(fields, seed) if op == "keys" else {"proposal": {}}

    monkeypatch.setattr("beamtime.guide.remote_answer", answer)
    values = values_of(ctx, "g")
    assert values["seeds"] == seeds
    assert values["swept"] == swept
    assert values["swept2"] == seeds


def test_example_values_fall_back_to_config_seed_on_older_remotes(
    ctx: Context, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An answer without a ``seed`` entry is read as the literal ``config.seed``."""

    def answer(op: str, params: dict[str, typing.Any], ctx: Context) -> dict[str, typing.Any]:
        if op != "keys":
            return {"proposal": {}}
        keys = seeded_keys(["config.seed", "config.lr"], None)
        del keys["config"]["seed"]
        return keys

    monkeypatch.setattr("beamtime.guide.remote_answer", answer)
    values = values_of(ctx, "g")
    assert values["seeds"] == "config.seed"
    assert values["swept"] == "config.lr"
