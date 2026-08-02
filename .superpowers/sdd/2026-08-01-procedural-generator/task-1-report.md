# Task 1 Report: Optional `gen` extra and core-stays-light lint

## Summary
Task 1 successfully implemented an optional `gen` dependency extra and added an AST-based lint to prevent the checker core from importing CadQuery or the new generator package. All 111 tests pass, including the new lint test that validates the isolation.

---

## Implementation Steps and Results

### Step 1: Wrote the failing test (appended to `tests/test_architecture.py`)

Appended to the end of the file:
- `CORE_LIGHT_MODULES`: tuple of the six core checker module stems: `"types"`, `"y14_5"`, `"iso286"`, `"montecarlo"`, `"checker"`, `"reliability"`
- `HEAVY_PACKAGES`: set containing `"cadquery"` and `"OCP"`
- `test_checker_core_does_not_import_cad_libraries()`: function that verifies none of the six core modules import heavy CAD libraries or the new `tolcad.gen` package

**Final code (lines 218-242 of test_architecture.py):**
```python
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
```

### Step 2: Verified the test ran

Command:
```bash
pytest tests/test_architecture.py::test_checker_core_does_not_import_cad_libraries -v
```

Result: **PASSED** (after appending both constants and test together)

The test passed immediately because the core modules genuinely do not import the forbidden libraries. This is the correct behavior.

### Step 3: Added the optional extra and created the generator package

#### Modified `pyproject.toml` (line 9):
```toml
[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov>=5.0"]
gen = ["cadquery>=2.8"]
```

#### Created `src/tolcad/gen/__init__.py`:
```python
"""Procedural toleranced-assembly generation.

Imports CadQuery, which the checker core deliberately does not. Install with
`pip install -e ".[gen]"`. tests/test_architecture.py enforces that the six
core checker modules never import this package or CadQuery.
"""
```

### Step 4: Installed and ran the full test suite

Command:
```bash
pip install -e ".[dev,gen]" && pytest -q
```

Result: **111 passed in 14.70s**

All tests pass, including the new CAD import lint. This is 1 more than the baseline (110 → 111).

### Step 5: Committed the changes

Command:
```bash
git add pyproject.toml src/tolcad/gen/__init__.py tests/test_architecture.py
git commit -m "feat: optional gen extra, lint keeping checker core CAD-free"
```

Result: Commit SHA **71afffb**

---

## Verification: Test Passes for the Right Reason

To confirm the lint passes because the core is genuinely clean (not because CadQuery is missing):

```bash
python -c "import cadquery; print(f'CadQuery version: {cadquery.__version__}')"
```

Result: **CadQuery version: 2.8.0**

CadQuery 2.8.0 is installed and available in the global environment. The test passes not because the library is absent, but because none of the six core modules actually import it.

---

## Gate A Verification

Command:
```bash
python scripts/gate_a.py
```

Result: 
- 6 PASS / 3 SKIP / NOT CLEARED (as expected)
- Exit code: **1** (correct: the pipeline is not fully cleared)

---

## Summary of Changes

| File | Change |
|------|--------|
| `pyproject.toml` | Added `gen = ["cadquery>=2.8"]` to `[project.optional-dependencies]` |
| `src/tolcad/gen/__init__.py` | Created new package (docstring only) |
| `tests/test_architecture.py` | Added 2 constants and 1 test function (15 new lines) |

**Total impact**: 3 files modified, 1 new file, 34 insertions

---

## Constraints Verification

- ✅ All dimensions in millimetres (no change)
- ✅ No module under `src/tolcad/` imports from `validation/` (no change)
- ✅ Six core modules do NOT import `tolcad.gen` or CadQuery (verified by passing lint)
- ✅ All headline paths run with no SolidWorks licence (no change to core; `gen` is optional)
- ✅ `EPS = 1e-9` unchanged (no change)
- ✅ Pre-registered thresholds frozen (no change): `GATE_A_TOLERANCE = 0.005`, `AGREEMENT_THRESHOLD = 0.95`, `RELIABILITY_THRESHOLD = 0.95`
- ✅ `python scripts/gate_a.py` exits 1 with 6 PASS / 3 SKIP / NOT CLEARED (correct)

---

## Reused Codebase Elements

As specified in the requirements:
- **Reused** `CORE = pathlib.Path(__file__).parent.parent / "src" / "tolcad"` from the existing test file
- **Reused** `_imported_modules(path)` helper (defined at line 68 of test_architecture.py) for AST-based import detection
- Did NOT redefine either; appended new constants and test at the end of the file
