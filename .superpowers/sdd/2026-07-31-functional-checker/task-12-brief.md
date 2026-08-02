### Task 12: NIST conformance oracle harness

**Files:**
- Create: `validation/nist_pmi.py`
- Test: `tests/test_nist_harness.py`

**Interfaces:**
- Consumes: nothing from core
- Produces: `validation.nist_pmi.load_expected(path) -> dict[str, bool]`, `validation.nist_pmi.agreement(ours, expected) -> float`, `validation.nist_pmi.disagreements(ours, expected) -> list[str]`

Spec v2 §7 adds the **NIST MBE PMI Validation and Conformance Test Suite** as a licence-free
Gate A oracle. Reading its STEP AP242 semantic PMI requires OCCT XCAF (`XCAFDoc_DimTolTool`),
which is a Phase 3 dependency — so this task builds the *comparison harness* only, exactly
mirroring the TolAnalyst pattern. The actual comparison runs in Phase 3.

CSV format: `part_id,assembles`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_nist_harness.py
import pytest
from validation.nist_pmi import agreement, disagreements, load_expected


def test_loads_expected_verdicts(tmp_path):
    csv = tmp_path / "nist.csv"
    csv.write_text("part_id,assembles\nFTC-06,true\nFTC-07,false\n", encoding="utf-8")
    got = load_expected(csv)
    assert got == {"FTC-06": True, "FTC-07": False}


def test_agreement_is_fraction_of_matching_verdicts():
    ours = {"FTC-06": True, "FTC-07": True}
    expected = {"FTC-06": True, "FTC-07": False}
    assert agreement(ours, expected) == pytest.approx(0.5)


def test_disagreements_are_listed_for_root_causing():
    ours = {"FTC-06": True, "FTC-07": True}
    expected = {"FTC-06": True, "FTC-07": False}
    assert disagreements(ours, expected) == ["FTC-07"]


def test_no_overlap_is_an_error_not_a_silent_pass():
    with pytest.raises(ValueError, match="no overlapping"):
        agreement({"A": True}, {"B": True})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_nist_harness.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'validation.nist_pmi'`

- [ ] **Step 3: Write minimal implementation**

```python
# validation/nist_pmi.py
"""Cross-check tolcad verdicts against the NIST MBE PMI Conformance Test Suite.

Public, authoritative, licence-free — this is the oracle that lets Gate A be cleared
without any commercial CAD licence.

Parsing the suite's STEP AP242 semantic PMI requires OCCT XCAF and happens in Phase 3.
This module only compares verdicts already extracted to CSV: part_id,assembles
"""

from __future__ import annotations

import csv
import pathlib


def load_expected(path: str | pathlib.Path) -> dict[str, bool]:
    """Read expected assembly verdicts keyed by NIST part id (e.g. FTC-06)."""
    out: dict[str, bool] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[row["part_id"]] = row["assembles"].strip().lower() == "true"
    return out


def agreement(ours: dict[str, bool], expected: dict[str, bool]) -> float:
    """Fraction of shared part ids where our verdict matches the expected one."""
    shared = set(ours) & set(expected)
    if not shared:
        raise ValueError("no overlapping part ids between the two verdict sets")
    return sum(1 for k in shared if ours[k] == expected[k]) / len(shared)


def disagreements(ours: dict[str, bool], expected: dict[str, bool]) -> list[str]:
    """Part ids where verdicts differ. Gate A requires each to be root-caused."""
    shared = set(ours) & set(expected)
    return sorted(k for k in shared if ours[k] != expected[k])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_nist_harness.py -v`
Expected: PASS, 4 tests

- [ ] **Step 5: Commit**

```bash
git add validation/nist_pmi.py tests/test_nist_harness.py
git commit -m "feat: NIST PMI conformance oracle harness"
```

---

