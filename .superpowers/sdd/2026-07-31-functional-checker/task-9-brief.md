### Task 9: Architecture guard — validation isolation

**Files:**
- Create: `validation/__init__.py`
- Create: `validation/tolanalyst.py`
- Create: `tests/test_architecture.py`

**Interfaces:**
- Consumes: `Verdict` (inside `validation/` only)
- Produces: `validation.tolanalyst.load_verdicts(path) -> dict[str, bool]`; `validation.tolanalyst.agreement(ours, theirs) -> float`

Gate A requires that no core module imports `validation/`. This test enforces it
mechanically so the reproducibility guarantee cannot rot.

TolAnalyst is a **black box**. This module reads a CSV of verdicts exported by a
separate manual step. It does not automate, wrap, or describe SolidWorks internals.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_architecture.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_architecture.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.checker'` (Task 10 creates it)

- [ ] **Step 3: Write the validation package**

```python
# validation/__init__.py
"""Optional SolidWorks cross-validation. Never imported by core tolcad modules."""
```

```python
# validation/tolanalyst.py
"""Cross-check tolcad verdicts against SolidWorks TolAnalyst.

TolAnalyst is treated strictly as a black-box oracle: this module ingests a CSV of
verdicts produced by a separate manual export and compares them to ours. It does not
wrap, automate, or document any SolidWorks internals.

CSV format: assembly_id,assembles
"""

from __future__ import annotations

import csv
import pathlib


def load_verdicts(path: str | pathlib.Path) -> dict[str, bool]:
    """Read exported TolAnalyst verdicts keyed by assembly id."""
    out: dict[str, bool] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[row["assembly_id"]] = row["assembles"].strip().lower() == "true"
    return out


def agreement(ours: dict[str, bool], theirs: dict[str, bool]) -> float:
    """Fraction of shared assembly ids where the two verdicts match."""
    shared = set(ours) & set(theirs)
    if not shared:
        raise ValueError("no overlapping assembly ids between the two verdict sets")
    matches = sum(1 for k in shared if ours[k] == theirs[k])
    return matches / len(shared)


def disagreements(ours: dict[str, bool], theirs: dict[str, bool]) -> list[str]:
    """Assembly ids where verdicts differ. Gate A requires each to be root-caused."""
    shared = set(ours) & set(theirs)
    return sorted(k for k in shared if ours[k] != theirs[k])
```

- [ ] **Step 4: Run test — one will still fail**

Run: `pytest tests/test_architecture.py::test_no_core_module_imports_validation -v`
Expected: PASS

The second test stays red until Task 10 creates `tolcad.checker`. That is expected.

- [ ] **Step 5: Commit**

```bash
git add validation tests/test_architecture.py
git commit -m "feat: TolAnalyst verdict comparison and architecture guard"
```

---

