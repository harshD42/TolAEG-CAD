"""Gate A: core must never depend on the optional SolidWorks path."""

import ast
import pathlib

CORE = pathlib.Path(__file__).parent.parent / "src" / "tolcad"


def _imported_modules(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_no_core_module_imports_validation():
    offenders = []
    for path in CORE.rglob("*.py"):
        bad = {m for m in _imported_modules(path) if m.split(".")[0] == "validation"}
        if bad:
            offenders.append(f"{path.name} imports {sorted(bad)}")
    assert not offenders, (
        "core modules must not import validation/: " + "; ".join(offenders)
    )


def test_core_imports_without_numpy_optional_deps_beyond_declared():
    """Core must import cleanly with no SolidWorks tooling present."""
    import tolcad.checker  # noqa: F401
    import tolcad.iso286  # noqa: F401
    import tolcad.montecarlo  # noqa: F401
    import tolcad.y14_5  # noqa: F401
