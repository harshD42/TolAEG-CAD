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
    - Dynamic imports: importlib.import_module("X"), __import__("X"), including
      the bare-name form after `from importlib import import_module`, and the
      attribute form `builtins.__import__("X")` (Finding 2)
    - exec/eval with string literals: exec("import X"), eval("...") (Finding 4)
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
            # Dynamic imports: import_module(...) or __import__(...), whether
            # called as a bare name (from importlib import import_module;
            # import_module(...)) or as an attribute (importlib.import_module(...),
            # builtins.__import__(...)). Both forms are things a developer could
            # write without intending to evade the lint.
            is_import_call = False
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in ("import_module", "__import__"):
                is_import_call = True
            elif isinstance(func, ast.Name):
                if func.id in ("import_module", "__import__"):
                    is_import_call = True
                # exec() and eval() with string literals: check for import statements
                elif func.id in ("exec", "eval"):
                    if node.args:
                        first_arg = node.args[0]
                        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                            # Extract any import statements from the string literal
                            try:
                                inner_names = _imports_from_code(first_arg.value)
                                names.update(inner_names)
                            except SyntaxError:
                                # If the string is not valid Python, skip it
                                pass
                    continue

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


def test_bare_name_import_module_call_is_caught():
    """Finding 2 (escalated): `from importlib import import_module` followed by a
    bare `import_module("validation")` call must be caught.

    Previously only the attribute form (importlib.import_module(...)) was
    checked; a developer who imports the name directly would slip past the lint.
    """
    code = 'from importlib import import_module\nimport_module("validation")'
    names = _imports_from_code(code)
    assert "validation" in names, (
        f"bare-name import_module() call must be caught; found: {names}"
    )


def test_dunder_import_as_attribute_is_caught():
    """Finding 2 (escalated): `builtins.__import__("validation")` must be caught.

    Previously only the bare-name form (__import__(...)) was checked; accessing
    it as an attribute of a module (e.g. builtins.__import__) would slip past.
    """
    code = 'import builtins\nbuiltins.__import__("validation")'
    names = _imports_from_code(code)
    assert "validation" in names, (
        f"__import__ accessed as an attribute must be caught; found: {names}"
    )


def test_exec_with_validation_import_is_caught():
    """Finding 4: exec("import validation") must be caught.

    The pythonpath change to include "." in the repo root means core modules
    can no longer rely on ModuleNotFoundError at runtime. The AST lint is now
    the sole enforcement. This test proves exec() calls with import statements
    are still caught.
    """
    code = 'exec("import validation")'
    names = _imports_from_code(code)
    assert "validation" in names, (
        f"exec() with validation import must be caught; found: {names}"
    )


def test_eval_with_validation_import_is_caught():
    """Finding 4: eval() calls with import statements must be caught."""
    code = 'eval("__import__(\'validation\')")'
    names = _imports_from_code(code)
    assert "validation" in names, (
        f"eval() with validation import must be caught; found: {names}"
    )


def test_innocent_exec_call_is_not_flagged():
    """Finding 4: innocent exec("x = 1") must NOT be flagged as importing validation."""
    code = 'exec("x = 1")'
    names = _imports_from_code(code)
    assert "validation" not in names, (
        f"Innocent exec() should not flag validation; found: {names}"
    )
    # The set should be empty for non-import code
    assert len(names) == 0, (
        f"Innocent exec() should not extract any names; found: {names}"
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


CORE_LIGHT_MODULES = (
    "types", "y14_5", "iso286", "montecarlo", "checker", "reliability",
)
HEAVY_PACKAGES = {"cadquery", "OCP"}


def test_checker_core_does_not_import_cad_libraries():
    """The checker must stay installable and runnable without CadQuery.

    Gate A's "runs with no commercial licence" guarantee depends on the core
    being light. tolcad.gen may import CadQuery; the six modules below may not,
    and may not import tolcad.gen either.
    """
    offenders = []
    for stem in CORE_LIGHT_MODULES:
        path = CORE / f"{stem}.py"
        assert path.is_file(), f"expected core module missing: {path}"
        imported = _imported_modules(path)
        bad = {m for m in imported if m.split(".")[0] in HEAVY_PACKAGES}
        bad |= {m for m in imported if m.startswith("tolcad.gen")}
        if bad:
            offenders.append(f"{stem}.py imports {sorted(bad)}")
    assert not offenders, (
        "checker core must not depend on CAD libraries: " + "; ".join(offenders)
    )
