# Task 4: Floating and Fixed Fastener Conditions (Tier 1) — Report

## Status
**DONE**

## Commit SHAs
- **50a833b**: feat: floating and fixed fastener conditions (Tier 1)
- **99c6a99**: fix: validate hole_b feature_type and improve asymmetric hole tests

## Test Summary
All 15 tests pass (6 existing + 9 new: 7 from brief + 2 corrected asymmetric tests + 1 hole_b validation test).

---

## What Was Done

### Step 1: Write the Failing Tests
Appended 7 test functions to `tests/test_y14_5.py`:
- Imported the three new functions: `floating_fastener_tolerance`, `fixed_fastener_tolerance`, `fastener_assembles`
- Defined canonical test constants:
  - `M8_BOLT = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL)` — M8 bolt at Ø8.0 max
  - `CLEARANCE_HOLE = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)` — Ø8.5 min clearance hole

Tests cover:
1. `test_floating_fastener_tolerance_is_hole_mmc_minus_fastener_mmc` — T = H - F = 0.5
2. `test_fixed_fastener_tolerance_is_half_the_floating_value` — T = (H - F) / 2 = 0.25
3. `test_floating_fastener_assembles_at_allowable_tolerance` — pass at 0.5 tolerance
4. `test_floating_fastener_fails_above_allowable_tolerance` — fail at 0.6 tolerance, margin = -0.1
5. `test_fixed_fastener_is_stricter_than_floating` — 0.5 tolerance passes floating but fails fixed
6. `test_asymmetric_holes_use_the_worse_one` — max() of two position tolerances
7. `test_unknown_condition_rejected` — ValueError on invalid condition string

### Step 2: Run Test to Verify It Fails
**Command:**
```bash
pytest tests/test_y14_5.py -v
```

**Output (first 50 lines, showing the ImportError):**
```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0 -- C:\...
...
tests\test_y14_5.py:3: in <module>
    from tolcad.y14_5 import (
E   ImportError: cannot import name 'fastener_assembles' from 'tolcad.y14_5'
=========================== short test summary info ===========================
ERROR tests/test_y14_5.py
Interrupted: 1 error during collection
```

✓ **Confirmed:** Tests fail with expected ImportError before implementation exists.

### Step 3: Write Minimal Implementation
Appended to `src/tolcad/y14_5.py`:

#### `_check_fastener_pair(hole, fastener) -> None`
Internal validator ensuring hole is INTERNAL and fastener is EXTERNAL. Raises ValueError if types are swapped.

#### `floating_fastener_tolerance(hole, fastener) -> float`
```python
def floating_fastener_tolerance(
    hole: FeatureOfSize, fastener: FeatureOfSize
) -> float:
    """Position tolerance available to each part, floating fastener condition.

    T = H - F, where H is hole MMC and F is fastener MMC.
    Source: ASME Y14.5 floating fastener formula. CITATION PENDING HUMAN VERIFICATION.
    """
    _check_fastener_pair(hole, fastener)
    return hole.mmc - fastener.mmc
```

#### `fixed_fastener_tolerance(hole, fastener) -> float`
```python
def fixed_fastener_tolerance(hole: FeatureOfSize, fastener: FeatureOfSize) -> float:
    """Position tolerance available to each part, fixed fastener condition.

    T = (H - F) / 2. The available clearance is split between the two parts
    because the fastener cannot shift in the part that constrains it.
    Assumes a projected tolerance zone.
    Source: ASME Y14.5 fixed fastener formula. CITATION PENDING HUMAN VERIFICATION.
    """
    _check_fastener_pair(hole, fastener)
    return (hole.mmc - fastener.mmc) / 2.0
```

#### `fastener_assembles(hole_a, hole_b, fastener, condition) -> Verdict`
```python
def fastener_assembles(
    hole_a: FeatureOfSize,
    hole_b: FeatureOfSize,
    fastener: FeatureOfSize,
    condition: str,
) -> Verdict:
    """Check a two-part fastened joint against the Y14.5 allowable tolerance."""
    if condition == "floating":
        allowable = floating_fastener_tolerance(hole_a, fastener)
    elif condition == "fixed":
        allowable = fixed_fastener_tolerance(hole_a, fastener)
    else:
        raise ValueError(f"condition must be 'floating' or 'fixed', got {condition!r}")

    worst = max(hole_a.position_tol, hole_b.position_tol)
    margin = allowable - worst

    return Verdict(
        assembles=margin >= -EPS,
        margin=margin,
        method=f"{condition}_fastener",
        detail={
            "allowable_tol": allowable,
            "worst_applied_tol": worst,
            "hole_mmc": hole_a.mmc,
            "fastener_mmc": fastener.mmc,
        },
    )
```

Key design decisions:
- Both functions use the same hole's MMC for tolerance calculation (standard practice: one reference hole defines the fastener).
- `fastener_assembles` uses `max()` of the two position tolerances to be conservative (worse-case across both parts).
- Margin is `assembles >= -EPS` (boundary is pass, following Tier 1 exact arithmetic).
- Detail dict includes allowable, worst applied, and both MMC values for diagnostics.

### Step 4: Run Test to Verify It Passes
**Command:**
```bash
pytest tests/test_y14_5.py -v
```

**Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0 -- C:\...
...
tests/test_y14_5.py::test_virtual_condition_external_adds_position_tolerance PASSED [  7%]
tests/test_y14_5.py::test_virtual_condition_internal_subtracts_position_tolerance PASSED [ 15%]
tests/test_y14_5.py::test_assembly_guaranteed_when_pin_vc_fits_hole_vc PASSED [ 23%]
tests/test_y14_5.py::test_assembly_fails_when_pin_vc_exceeds_hole_vc PASSED [ 30%]
tests/test_y14_5.py::test_exact_boundary_case_assembles PASSED           [ 38%]
tests/test_y14_5.py::test_rejects_swapped_feature_types PASSED           [ 46%]
tests/test_y14_5.py::test_floating_fastener_tolerance_is_hole_mmc_minus_fastener_mmc PASSED [ 53%]
tests/test_y14_5.py::test_fixed_fastener_tolerance_is_half_the_floating_value PASSED [ 61%]
tests/test_y14_5.py::test_floating_fastener_assembles_at_allowable_tolerance PASSED [ 69%]
tests/test_y14_5.py::test_floating_fastener_fails_above_allowable_tolerance PASSED [ 76%]
tests/test_y14_5.py::test_fixed_fastener_is_stricter_than_floating PASSED [ 84%]
tests/test_y14_5.py::test_asymmetric_holes_use_the_worse_one PASSED      [ 92%]
tests/test_y14_5.py::test_unknown_condition_rejected PASSED              [100%]

============================== 13 passed in 0.03s ==============================
```

✓ **Confirmed:** All 13 tests pass (6 existing + 7 new).

### Step 5: Commit
**Command:**
```bash
git add src/tolcad/y14_5.py tests/test_y14_5.py
git commit -m "feat: floating and fixed fastener conditions (Tier 1)"
```

**Result:** 2 files changed, 115 insertions (+)

---

## Concerns

### ⚠️ CITATION PENDING (Expected — Intentional)
Both tolerance formulas (`floating_fastener_tolerance` and `fixed_fastener_tolerance`) contain docstring citations marked as **CITATION PENDING HUMAN VERIFICATION**:

```
Source: ASME Y14.5 floating fastener formula. CITATION PENDING HUMAN VERIFICATION.
Source: ASME Y14.5 fixed fastener formula. CITATION PENDING HUMAN VERIFICATION.
```

**Reason:** This implementation cannot verify the formulas or numeric examples against a printed copy of ASME Y14.5-2018. The canonical worked example (M8 bolt through Ø8.5 clearance holes yielding T = 0.5 for floating, T = 0.25 for fixed) and the formulas themselves (T = H - F, T = (H - F) / 2) are transcribed from the brief, not verified against the standard.

**Action required (not urgent — expected in code review):** A domain expert with access to ASME Y14.5-2018 (or equivalent authoritative source such as Meadows / Krulikowski) must verify:
1. The formula T = H - F for floating fastener condition.
2. The formula T = (H - F) / 2 for fixed fastener condition.
3. The canonical worked example (M8 at 8.0 MMC, clearance hole at 8.5 MMC, yielding tolerances 0.5 and 0.25 respectively).
4. The definition of "available to each part" (floating) vs. "per part" (fixed split).

Once verified, replace the "CITATION PENDING" lines with the appropriate source and page number from the standard.

This is not a code defect — it is a placeholder for human verification and is intentionally left as-is per task constraints.

---

## Notes for Task 5

Task 5 (bonus_tolerance) will append to the same module (`src/tolcad/y14_5.py`). Key integration points:

1. **Imports are stable:** No new imports were added to y14_5.py; it continues to use only `EPS, FeatureOfSize, FeatureType, Verdict`.

2. **No module-level state:** All new functions are pure (no side effects, no global mutation).

3. **Tier 1 discipline maintained:** All arithmetic uses EPS = 1e-9 for boundary checks (margin >= -EPS pattern).

4. **Test structure ready:** The test file (`tests/test_y14_5.py`) can accept additional tests for Task 5; the INTERNAL, EXTERNAL, M8_BOLT, and CLEARANCE_HOLE constants are module-level and reusable.

5. **Next appended function:** Task 5 will add `bonus_tolerance(feature) -> float`, which computes additional tolerance available under MMC modifier. It should be appended before any changes to the existing four functions.

---

## File Changes Summary

**src/tolcad/y14_5.py:**
- Added 4 functions (1 private helper + 3 public)
- 52 lines added
- No changes to existing 2 functions or docstring

**tests/test_y14_5.py:**
- Added 7 test functions
- Appended imports and constants (M8_BOLT, CLEARANCE_HOLE)
- 63 lines added
- No changes to existing 6 tests

**Git:**
- Commit SHA: 50a833b
- Branch: feat/functional-checker (unchanged)

---

## Verification Checklist

✓ No imports duplicated  
✓ No existing functions modified  
✓ No validation module imports  
✓ All tests pass (15/15)  
✓ Tier 1 exact arithmetic (EPS = 1e-9)  
✓ No SolidWorks dependency  
✓ Citation properly marked as pending  
✓ Code matches brief specification  
✓ Dimensions in millimetres (float)  
✓ Commit message follows convention  

---

## Post-Review Fixes (Commit 99c6a99)

### Finding 1: `hole_b` Feature Type Validation Missing

**Issue:** `fastener_assembles()` validated `hole_a` via `_check_fastener_pair(hole_a, fastener)` but never validated `hole_b`. The function used `hole_b.position_tol` directly in `max(hole_a.position_tol, hole_b.position_tol)` without ensuring `hole_b` was an INTERNAL feature. An EXTERNAL feature passed as `hole_b` would silently produce incorrect results.

**Fix:** Added explicit validation at the start of `fastener_assembles()`:
```python
if hole_b.feature_type is not FeatureType.INTERNAL:
    raise ValueError("hole_b must be an internal feature")
```

This matches the validation pattern used in `vc_assembles()` (Task 3) and is consistent with the module's error-handling style.

**New Test:** `test_rejects_external_hole_b()` — verifies that passing an EXTERNAL feature as `hole_b` raises `ValueError` with the correct message.

---

### Finding 2: Asymmetric Hole Test Was Tautological

**Issue:** `test_asymmetric_holes_use_the_worse_one()` had:
- `tight = FeatureOfSize(..., position_tol=0.6)` as `hole_a`
- `loose = FeatureOfSize(..., position_tol=0.1)` as `hole_b`

Since `hole_a` is the source of the allowable tolerance (via `floating_fastener_tolerance(hole_a, fastener)`), it was already the worse of the two. A buggy implementation that ignored `hole_b` entirely would still compute the correct margin and verdict, making the test unable to catch the bug.

**Fix:** Replaced with two separate tests covering both orderings:

1. **`test_asymmetric_holes_worse_on_hole_a()`** — worse tolerance (0.6) on `hole_a`:
   ```python
   hole_a = FeatureOfSize(..., position_tol=0.6)
   hole_b = FeatureOfSize(..., position_tol=0.1)
   ```
   Expected: Fail (0.6 > allowable 0.5). Tests the original case.

2. **`test_asymmetric_holes_worse_on_hole_b()`** — worse tolerance (0.6) on `hole_b`:
   ```python
   hole_a = FeatureOfSize(..., position_tol=0.1)
   hole_b = FeatureOfSize(..., position_tol=0.6)
   ```
   Expected: Fail (0.6 > allowable 0.5). This test would **pass incorrectly** if `hole_b` were ignored, proving the fix works.

These two tests together verify that the `max()` operation genuinely considers both holes, regardless of order.

---

### Test Run Output (Post-Fix)

**Command:**
```bash
pytest tests/test_y14_5.py -v
```

**Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0 -- C:\...
...
tests/test_y14_5.py::test_virtual_condition_external_adds_position_tolerance PASSED [  6%]
tests/test_y14_5.py::test_virtual_condition_internal_subtracts_position_tolerance PASSED [ 13%]
tests/test_y14_5.py::test_assembly_guaranteed_when_pin_vc_fits_hole_vc PASSED [ 20%]
tests/test_y14_5.py::test_assembly_fails_when_pin_vc_exceeds_hole_vc PASSED [ 26%]
tests/test_y14_5.py::test_exact_boundary_case_assembles PASSED           [ 33%]
tests/test_y14_5.py::test_rejects_swapped_feature_types PASSED           [ 40%]
tests/test_y14_5.py::test_floating_fastener_tolerance_is_hole_mmc_minus_fastener_mmc PASSED [ 46%]
tests/test_y14_5.py::test_fixed_fastener_tolerance_is_half_the_floating_value PASSED [ 53%]
tests/test_y14_5.py::test_floating_fastener_assembles_at_allowable_tolerance PASSED [ 60%]
tests/test_y14_5.py::test_floating_fastener_fails_above_allowable_tolerance PASSED [ 66%]
tests/test_y14_5.py::test_fixed_fastener_is_stricter_than_floating PASSED [ 73%]
tests/test_y14_5.py::test_asymmetric_holes_worse_on_hole_a PASSED        [ 80%]
tests/test_y14_5.py::test_asymmetric_holes_worse_on_hole_b PASSED        [ 86%]
tests/test_y14_5.py::test_unknown_condition_rejected PASSED              [ 93%]
tests/test_y14_5.py::test_rejects_external_hole_b PASSED                 [100%]

============================== 15 passed in 0.04s ==============================
```

✓ **Confirmed:** All 15 tests pass. Both findings fixed and validated.

---

### Code Changes Summary (Post-Fix)

**src/tolcad/y14_5.py:**
- Added 1 line of validation to `fastener_assembles()` (checking `hole_b.feature_type`)
- No other changes to function logic or structure

**tests/test_y14_5.py:**
- Replaced 1 test (`test_asymmetric_holes_use_the_worse_one()`) with 2 better tests
- Added 1 new test for `hole_b` type validation
- Net: +2 tests (15 total vs. original 13)

**Git:**
- Commit SHA: 99c6a99
- Message: "fix: validate hole_b feature_type and improve asymmetric hole tests"

---

## Final Status

- ✓ Finding 1 fixed: `hole_b` now validated for INTERNAL feature_type
- ✓ Finding 2 fixed: Asymmetric hole tests now properly detect whether `hole_b` is considered
- ✓ All 15 tests pass
- ✓ No regressions in existing tests
- ✓ Code style and Tier 1 discipline maintained
- ✓ Ready for Task 5 (no further changes needed to this module)
