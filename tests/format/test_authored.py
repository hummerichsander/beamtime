from pathlib import Path

from beamtime.format.authored import newest, read_markdown_doc, read_yaml_doc, versions


def test_proposal_versions(golden: Path) -> None:
    """Versions sort by id; the newest is current."""
    folder = golden / "scaling" / "proposal"
    assert [p.stem for p in versions(folder)] == [
        "20261020-140000-q7w3",
        "20261021-090000-q8w4",
    ]
    doc = read_yaml_doc(newest(folder), kind="proposal")
    assert doc.id == "20261021-090000-q8w4"
    assert doc.meta["supersedes"]["version"] == "20261020-140000-q7w3"


def test_proposal_fields(golden: Path) -> None:
    """A proposal reads with its plan and predictions."""
    doc = read_yaml_doc(golden / "scaling/proposal/20261020-140000-q7w3.yaml", kind="proposal")
    assert doc.schema == 1 and doc.body == ""
    assert [p["name"] for p in doc.meta["predictions"]] == ["no-spike", "sharper-samples"]


def test_note_frontmatter_and_body(golden: Path) -> None:
    """A note splits into frontmatter fields and a Markdown body."""
    doc = read_markdown_doc(golden / "scaling/notes/20261025-170200-m4p7.md", kind="note")
    assert doc.meta["type"] == "verdict"
    assert doc.meta["verdicts"] == {"no-spike": "confirmed", "sharper-samples": "refuted"}
    assert doc.body == "\nNo spike in any seed; see [[20261024-101532-k3m9xq2a]].\n"


def test_view_block_memory(golden: Path) -> None:
    """Views, blocks and memory read generically."""
    view = read_yaml_doc(newest(golden / "scaling/view"), kind="view")
    assert view.meta["title"] == "Warmup sweep"
    block = read_yaml_doc(newest(golden / "scaling/blocks/loss-panel"), kind="block")
    assert block.meta["name"] == "loss-panel"
    memory = read_markdown_doc(newest(golden / "memory"), kind="memory")
    assert memory.body.startswith("\n## Current understanding")


def test_missing_folder_has_no_versions(tmp_path: Path) -> None:
    """A folder without versions has no current one."""
    assert versions(tmp_path / "view") == [] and newest(tmp_path / "view") is None
    (tmp_path / "view").mkdir()
    (tmp_path / "view" / "draft.yaml").write_text("schema: 1\n")
    assert newest(tmp_path / "view") is None
