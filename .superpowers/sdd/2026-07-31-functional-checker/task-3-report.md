# Task 3: Virtual Condition (Tier 1) — Report

## Summary
Successfully implemented Tier 1 ASME Y14.5 assembly conditions: `virtual_condition()` and `vc_assembles()` functions. All 6 new tests pass; all 10 total tests (including pre-existing smoke and types tests) pass.

## Execution Steps

### Step 1: Write the Failing Test
Created `tests/test_y14_5.py` with 6 test cases covering:
- Virtual condition for external features (adds position tolerance)
- Virtual condition for internal features (subtracts position tolerance)
- Assembly passing when pin VC fits hole VC
- Assembly failing when pin VC exceeds hole VC
- Exact boundary case (VC_pin == VC_hole) must assemble
- Rejection of swapped feature types

**Command**: File created at `C:\Users\harsh\Downloads\Projects\Paper1\tests\test_y14_5.py`

### Step 2: Run Test to Verify Failure
**Command**: `pytest tests/test_y14_5.py -v`

**Output**:
```
ERROR collecting tests/test_y14_5.py
...
E   ModuleNotFoundError: No module named 'tolcad.y14_5'
=========================== short test summary info ===========================
ERROR tests/test_y14_5.py
============================= Interrupted: 1 error during collection ===========================
```

**Result**: Expected failure confirmed — module does not exist yet.

### Step 3: Write Minimal Implementation
Created `src/tolcad/y14_5.py` with two functions:

1. **`virtual_condition(feature: FeatureOfSize) -> float`**
   - External: `MMC + position_tol` (worst-case boundary is larger)
   - Internal: `MMC - position_tol` (worst-case boundary is smaller)

2. **`vc_assembles(pin: FeatureOfSize, hole: FeatureOfSize) -> Verdict`**
   - Validates pin is EXTERNAL, hole is INTERNAL
   - Computes margin = `VC_hole - VC_pin`
   - Assembles if `margin >= -EPS` (uses `EPS = 1e-9` from `types.py`)
   - Returns `Verdict` with assembles flag, margin, method, and detail dict

**File**: `C:\Users\harsh\Downloads\Projects\Paper1\src\tolcad\y14_5.py`

### Step 4: Run Test to Verify Success
**Command**: `pytest tests/test_y14_5.py -v`

**Output**:
```
collected 6 items

tests/test_y14_5.py::test_virtual_condition_external_adds_position_tolerance PASSED [ 16%]
tests/test_y14_5.py::test_virtual_condition_internal_subtracts_position_tolerance PASSED [ 33%]
tests/test_y14_5.py::test_assembly_guaranteed_when_pin_vc_fits_hole_vc PASSED [ 50%]
tests/test_y14_5.py::test_assembly_fails_when_pin_vc_exceeds_hole_vc PASSED [ 66%]
tests/test_y14_5.py::test_exact_boundary_case_assembles PASSED           [ 83%]
tests/test_y14_5.py::test_rejects_swapped_feature_types PASSED           [100%]

============================== 6 passed in 0.03s ==============================
```

**Result**: All 6 tests PASS.

### Step 5: Commit
**Command**: 
```bash
git add src/tolcad/y14_5.py tests/test_y14_5.py
git commit -m "feat: virtual condition check (Tier 1)"
```

**Output**:
```
[feat/functional-checker d292eef] feat: virtual condition check (Tier 1)
 2 files changed, 91 insertions(+)
 create mode 100644 src/tolcad/y14_5.py
 create mode 100644 tests/test_y14_5.py
```

**Commit SHA**: `d292eef`

## Full Test Run (Verification)
**Command**: `pytest -v` (from repo root)

**Output**:
```
collected 10 items

tests/test_smoke.py::test_package_imports PASSED                         [ 10%]
tests/test_types.py::test_internal_feature_mmc_is_smallest_size PASSED   [ 20%]
tests/test_types.py::test_external_feature_mmc_is_largest_size PASSED    [ 30%]
tests/test_types.py::test_verdict_is_immutable PASSED                    [ 40%]
tests/test_y14_5.py::test_virtual_condition_external_adds_position_tolerance PASSED [ 50%]
tests/test_y14_5.py::test_virtual_condition_internal_subtracts_position_tolerance PASSED [ 60%]
tests/test_y14_5.py::test_assembly_guaranteed_when_pin_vc_fits_hole_vc PASSED [ 70%]
tests/test_y14_5.py::test_assembly_fails_when_pin_vc_exceeds_hole_vc PASSED [ 80%]
tests/test_y14_5.py::test_exact_boundary_case_assembles PASSED           [ 90%]
tests/test_y14_5.py::test_rejects_swapped_feature_types PASSED           [100%]

============================== 10 passed in 0.03s ==============================
```

**Result**: All tests pass (4 pre-existing + 6 new).

## Files Created/Modified

### 1. `src/tolcad/y14_5.py` (Created)
```python
"""Tier 1: closed-form ASME Y14.5 assembly conditions.

These are exact arithmetic identities from the standard, not simulations.
A failure here is unambiguously a failure of the input geometry.
"""

from __future__ import annotations

from tolcad.types import EPS, FeatureOfSize, FeatureType, Verdict


def virtual_condition(feature: FeatureOfSize) -> float:
    """Worst-case boundary of a feature, per ASME Y14.5.

    External: MMC + position tolerance (effectively the largest it can be).
    Internal: MMC - position tolerance (effectively the smallest it can be).
    """
    if feature.feature_type is FeatureType.EXTERNAL:
        return feature.mmc + feature.position_tol
    return feature.mmc - feature.position_tol


def vc_assembles(pin: FeatureOfSize, hole: FeatureOfSize) -> Verdict:
    """Check a single pin-in-hole pair by virtual condition.

    Assembly is guaranteed iff VC_pin <= VC_hole.
    """
    if pin.feature_type is not FeatureType.EXTERNAL:
        raise ValueError("pin must be an external feature")
    if hole.feature_type is not FeatureType.INTERNAL:
        raise ValueError("hole must be an internal feature")

    vc_pin = virtual_condition(pin)
    vc_hole = virtual_condition(hole)
    margin = vc_hole - vc_pin

    return Verdict(
        assembles=margin >= -EPS,
        margin=margin,
        method="virtual_condition",
        detail={"vc_pin": vc_pin, "vc_hole": vc_hole},
    )
```

### 2. `tests/test_y14_5.py` (Created)
```python
import pytest
from tolcad.types import FeatureOfSize, FeatureType
from tolcad.y14_5 import virtual_condition, vc_assembles

INTERNAL = FeatureType.INTERNAL
EXTERNAL = FeatureType.EXTERNAL


def test_virtual_condition_external_adds_position_tolerance():
    # Ø8.0 pin at MMC with 0.1 position tolerance -> VC 8.1
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.1)
    assert virtual_condition(pin) == pytest.approx(8.1)


def test_virtual_condition_internal_subtracts_position_tolerance():
    # Ø8.5 hole at MMC with 0.5 position tolerance -> VC 8.0
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    assert virtual_condition(hole) == pytest.approx(8.0)


def test_assembly_guaranteed_when_pin_vc_fits_hole_vc():
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.0)
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.2)
    verdict = vc_assembles(pin, hole)
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.3)  # 8.3 - 8.0


def test_assembly_fails_when_pin_vc_exceeds_hole_vc():
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.4)
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    verdict = vc_assembles(pin, hole)
    assert verdict.assembles is False
    assert verdict.margin == pytest.approx(-0.4)  # 8.0 - 8.4


def test_exact_boundary_case_assembles():
    """VC_pin == VC_hole is the guaranteed-fit boundary and must pass."""
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.0)
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    verdict = vc_assembles(pin, hole)
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.0, abs=1e-9)


def test_rejects_swapped_feature_types():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    with pytest.raises(ValueError, match="external"):
        vc_assembles(hole, hole)
```

## Notes for Tasks 4 and 5

1. **Import path**: Both functions are exported from `tolcad.y14_5` and can be imported as shown in the test file.

2. **Verdict structure**: The functions return `Verdict` objects with:
   - `assembles`: boolean flag
   - `margin`: float, the clearance (positive = passing, negative = failing)
   - `method`: string identifier (`"virtual_condition"`)
   - `detail`: dict containing computed `vc_pin` and `vc_hole` values for debugging

3. **Precision boundary**: Uses `EPS = 1e-9` from `types.py` for the assembly decision at `margin >= -EPS`. This is crucial for Tier 1 exactness and handles the equality case correctly.

4. **Feature type validation**: `vc_assembles()` enforces that the first argument (pin) is EXTERNAL and the second (hole) is INTERNAL. Swapped calls raise `ValueError` with a descriptive message matching "external".

5. **Extensibility**: The module structure allows Tasks 4 and 5 to add new functions (`fastener_conditions`, bonus tolerance, etc.) without breaking existing tests.

## Concerns
None. All requirements met exactly as specified in the brief.
