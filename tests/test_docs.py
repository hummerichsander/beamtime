import json
import runpy
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_the_command_reference_is_current() -> None:
    """docs/reference/cli.md is what the registry generates; run docs/site/reference.py after
    changing an operation."""
    reference = runpy.run_path(str(ROOT / "docs" / "site" / "reference.py"))["reference"]
    assert (ROOT / "docs" / "reference" / "cli.md").read_text(encoding="utf-8") == reference()


def test_the_mcp_reference_is_current() -> None:
    """docs/reference/mcp.md is what the registry and the MCP server generate; run
    docs/site/reference.py after changing an operation or a family."""
    reference = runpy.run_path(str(ROOT / "docs" / "site" / "reference.py"))["mcp_reference"]
    assert (ROOT / "docs" / "reference" / "mcp.md").read_text(encoding="utf-8") == reference()


def test_every_page_in_the_nav_exists() -> None:
    """The site's navigation lists only pages that exist, each with a title."""
    nav = json.loads((ROOT / "docs" / "nav.json").read_text(encoding="utf-8"))
    for page in (p for s in nav["sections"] for p in s["pages"]):
        assert (ROOT / "docs" / page).read_text(encoding="utf-8").startswith("# "), page
