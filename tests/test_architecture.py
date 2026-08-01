"""Gate A: core must never depend on the optional SolidWorks path."""

import ast
import pathlib

CORE = pathlib.Path(__file__).parent.parent / "src" / "tolcad"


def _imports_from_code(code: str) -> set[str]:
    """Extract imported module names from code string via AST.

    Catches:
    - Direct imports: import X, import X.Y
    - Named imports: from X import Y
    - Bare relative imports: from . import X, from .. import Y (Finding 1)
    - Dynamic imports: importlib.import_module("X"), __import__("X") (Finding 2)
    """
    tree = ast.parse(code)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # from X import Y — capture the module X
                names.add(node.module)
            else:
                # Bare relative import: from . import X or from .. import X
                # node.module is None, so check alias.name for what's being imported
                names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            # Dynamic imports: importlib.import_module("X") or __import__("X")
            is_import_call = False
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "import_module":
                    is_import_call = True
            elif isinstance(node.func, ast.Name):
                if node.func.id == "__import__":
                    is_import_call = True

            if is_import_call and node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                    names.add(first_arg.value)
    return names


def _imported_modules(path: pathlib.Path) -> set[str]:
    """Extract all imported module names from a Python file."""
    return _imports_from_code(path.read_text(encoding="utf-8"))


def test_bare_relative_import_of_validation_is_caught():
    """Finding 1: bare relative imports like 'from . import validation' are caught.

    Previously, 'from . import validation' would not be detected because
    node.module is None for bare relative imports, and only node.module was checked.
    """
    code = "from . import validation"
    names = _imports_from_code(code)
    assert "validation" in names, (
        f"Bare relative import of validation must be caught; found: {names}"
    )


def test_dynamic_import_of_validation_is_caught():
    """Finding 2: dynamic imports like importlib.import_module("validation") are caught.

    Previously, calls to importlib.import_module() or __import__() were invisible
    to the AST scan because they are ast.Call nodes, not Import nodes.
    """
    cases = [
        ('importlib.import_module("validation")', "validation"),
        ('__import__("validation")', "validation"),
        ('importlib.import_module("validation.submodule")', "validation.submodule"),
    ]
    for code, expected in cases:
        names = _imports_from_code(code)
        assert expected in names, (
            f"Dynamic import '{code}' should be caught; found: {names}"
        )


def test_no_core_module_imports_validation():
    """Finding 3 + original: core must never depend on validation/.

    The lint now guards against vacuous passes by verifying:
    1. CORE is a directory
    2. Python files exist to scan
    3. Expected core modules are found by name
    """
    # Finding 3: Assert the scan path exists and is accessible
    assert CORE.is_dir(), (
        f"CORE path must be a directory; got {CORE}. "
        "If this fails, the path is wrong and the lint would pass vacuously."
    )

    # Finding 3: Assert we actually found Python files to scan
    module_files = list(CORE.rglob("*.py"))
    assert module_files, (
        f"Found no Python files in CORE={CORE}. "
        "The lint would pass vacuously if CORE is renamed or moved."
    )

    # Finding 3: Verify expected core modules are present to prevent vacuous pass
    expected_modules = {"__init__", "types", "y14_5", "iso286", "montecarlo"}
    found_modules = {f.stem for f in module_files}
    missing = expected_modules - found_modules
    assert not missing, (
        f"Expected core modules {missing} not found in CORE={CORE}. "
        f"Found: {found_modules}. "
        "Lint would pass vacuously if core modules are moved or renamed."
    )

    # Main check: scan for validation imports
    offenders = []
    for path in module_files:
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
