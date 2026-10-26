from pathlib import Path

import pytest

from beamtime.format.authored import read_markdown_doc
from beamtime.format.io import write_replaced
from beamtime.format.run import read_card, read_config
from beamtime.format.schema import SchemaError, schema_of


@pytest.mark.parametrize("obj", [{}, {"schema": "1"}, {"schema": 0}, {"schema": True}])
def test_missing_or_invalid_schema(obj: dict) -> None:
    """Files without a positive integer schema are refused with a reason."""
    with pytest.raises(SchemaError, match="missing or invalid 'schema'"):
        schema_of(obj, kind="run", path="x/_run.json")


def test_not_a_mapping() -> None:
    """A file that is not a mapping is refused."""
    with pytest.raises(SchemaError, match="expected a mapping"):
        schema_of([1], kind="run", path="x/_run.json")


def test_newer_schema_says_how_to_upgrade(tmp_path: Path) -> None:
    """A newer schema names the file and the upgrade command."""
    write_replaced(tmp_path / "_config.json", {"schema": 99, "lr": 1})
    with pytest.raises(SchemaError, match="pip install -U beamtime") as e:
        read_config(tmp_path)
    assert "_config.json" in str(e.value)


def test_card_without_schema(tmp_path: Path) -> None:
    """Machine-written files without a schema are refused."""
    write_replaced(tmp_path / "_run_card.json", {"status": "running"})
    with pytest.raises(SchemaError):
        read_card(tmp_path)


def test_markdown_without_frontmatter(tmp_path: Path) -> None:
    """Notes need frontmatter."""
    p = tmp_path / "20261025-170200-m4p7.md"
    p.write_text("# just markdown\n")
    with pytest.raises(SchemaError, match="frontmatter"):
        read_markdown_doc(p, kind="note")
