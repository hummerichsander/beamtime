import ast
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent / "src" / "beamtime"
ALLOWED = {
    "sdk": {"beamtime.sdk", "beamtime.format"},
    "format": {"beamtime.format"},
    "synth": {"beamtime.format", "beamtime.synth"},
}


def module_level(node: ast.AST):
    """Walk a tree without entering functions, whose imports are lazy and optional.

    :param node: The tree.
    :return: The nodes outside function bodies."""
    yield node
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield from module_level(child)


def imports(path: Path) -> set[str]:
    """Collect the absolute module names a file imports at module level.

    :param path: A Python file.
    :return: The imported module names."""
    tree = ast.parse(path.read_text(), feature_version=(3, 10))
    names = set()
    for node in module_level(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names.add(node.module)
    return names


@pytest.mark.parametrize("package", sorted(ALLOWED))
def test_sdk_side_imports_only_stdlib_yaml_and_itself(package: str) -> None:
    """The SDK side runs on Python 3.10 with the standard library and PyYAML only;
    optional libraries are imported inside the functions that need them."""
    for path in (SRC / package).rglob("*.py"):
        for name in imports(path):
            top = name.split(".")[0]
            if top == "beamtime":
                assert any(
                    name == a or name.startswith(f"{a}.") for a in ALLOWED[package]
                ), f"{path.name} imports {name}"
            else:
                assert top in sys.stdlib_module_names or top == "yaml", (
                    f"{path.name} imports {name}"
                )
