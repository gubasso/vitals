"""Each system library enters through its one adapter module."""

import ast
from pathlib import Path

import pytest

SOURCE = Path(__file__).parents[2] / "src" / "vitals"
OWNERS = {"psutil": "adapters/psutil_source.py", "pynvml": "adapters/nvml_source.py"}


def _imported_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.parametrize("library", sorted(OWNERS))
def test_one_module_imports_the_library(library: str) -> None:
    """Only the owner adapter imports the library."""
    importers = sorted(
        str(path.relative_to(SOURCE))
        for path in SOURCE.rglob("*.py")
        if library in _imported_roots(path)
    )
    assert importers == [OWNERS[library]]
