# Task 5: Bonus tolerance under the MMC modifier

## Summary
Successfully implemented `bonus_tolerance()` function in the Tier 1 module. This function calculates extra position tolerance earned when a feature departs from MMC toward LMC, which is critical for the checker to correctly evaluate whether nominally-marginal parts can assemble in practice.

---

## Step 1: Write the failing test

**File:** `tests/test_y14_5.py`

Added import for `bonus_tolerance`:
```python
from tolcad.y14_5 import (
    bonus_tolerance,
    fastener_assembles,
    fixed_fastener_tolerance,
    floating_fastener_tolerance,
    virtual_condition,
    vc_assembles,
)
```

Appended five test functions to verify the implementation:
- `test_no_bonus_at_mmc()`: Verifies zero bonus when actual_size equals MMC
- `test_full_bonus_at_lmc_for_internal_feature()`: Verifies maximum bonus at LMC for INTERNAL feature
- `test_full_bonus_at_lmc_for_external_feature()`: Verifies maximum bonus at LMC for EXTERNAL feature
- `test_partial_bonus_mid_range()`: Verifies proportional bonus at intermediate sizes
- `test_actual_size_outside_limits_rejected()`: Verifies validation error for out-of-range sizes

---

## Step 2: Run test to verify it fails

**Command:**
```bash
pytest tests/test_y14_5.py -v
```

**Output (expected failure):**
```
ImportError: cannot import name 'bonus_tolerance' from 'tolcad.y14_5'
```

✓ Test correctly fails with expected ImportError.

---

## Step 3: Write minimal implementation

**File:** `src/tolcad/y14_5.py`

Appended the following function after `fastener_assembles()`:

```python
def bonus_tolerance(feature: FeatureOfSize, actual_size: float) -> float:
    """Extra position tolerance earned by departing from MMC, under the MMC modifier.

    Bonus equals the departure from MMC toward LMC. Zero at MMC, maximal at LMC.
    """
    if not (feature.min_size - EPS <= actual_size <= feature.max_size + EPS):
        raise ValueError(
            f"actual_size {actual_size} outside limits "
            f"[{feature.min_size}, {feature.max_size}]"
        )
    return abs(actual_size - feature.mmc)
```

### Implementation notes:
- **EPS tolerance:** Used the imported `EPS = 1e-9` for floating-point error margin at limits, as required
- **Bonus calculation:** `abs(actual_size - feature.mmc)` correctly computes bonus for both INTERNAL and EXTERNAL features:
  - For INTERNAL: MMC is min_size (8.5), so departing upward (toward max_size/LMC) yields positive bonus
  - For EXTERNAL: MMC is max_size (8.0), so departing downward (toward min_size/LMC) yields positive bonus
  - The absolute value handles both cases correctly
- **Bounds checking:** Ensures actual_size falls within [min_size, max_size] with EPS tolerance to accommodate floating-point arithmetic

---

## Step 4: Run test to verify it passes

**Command:**
```bash
pytest tests/test_y14_5.py -v
```

**Output (all tests passing):**
```
collected 20 items

tests/test_y14_5.py::test_virtual_condition_external_adds_position_tolerance PASSED [  5%]
tests/test_y14_5.py::test_virtual_condition_internal_subtracts_position_tolerance PASSED [ 10%]
tests/test_y14_5.py::test_assembly_guaranteed_when_pin_vc_fits_hole_vc PASSED [ 15%]
tests/test_y14_5.py::test_assembly_fails_when_pin_vc_exceeds_hole_vc PASSED [ 20%]
tests/test_y14_5.py::test_exact_boundary_case_assembles PASSED           [ 25%]
tests/test_y14_5.py::test_rejects_swapped_feature_types PASSED           [ 30%]
tests/test_y14_5.py::test_floating_fastener_tolerance_is_hole_mmc_minus_fastener_mmc PASSED [ 35%]
tests/test_y14_5.py::test_fixed_fastener_tolerance_is_half_the_floating_value PASSED [ 40%]
tests/test_y14_5.py::test_floating_fastener_assembles_at_allowable_tolerance PASSED [ 45%]
tests/test_y14_5.py::test_floating_fastener_fails_above_allowable_tolerance PASSED [ 50%]
tests/test_y14_5.py::test_fixed_fastener_is_stricter_than_floating PASSED [ 55%]
tests/test_y14_5.py::test_asymmetric_holes_worse_on_hole_a PASSED        [ 60%]
tests/test_y14_5.py::test_asymmetric_holes_worse_on_hole_b PASSED        [ 65%]
tests/test_y14_5.py::test_unknown_condition_rejected PASSED              [ 70%]
tests/test_y14_5.py::test_rejects_external_hole_b PASSED                 [ 75%]
tests/test_y14_5.py::test_no_bonus_at_mmc PASSED                         [ 80%]
tests/test_y14_5.py::test_full_bonus_at_lmc_for_internal_feature PASSED  [ 85%]
tests/test_y14_5.py::test_full_bonus_at_lmc_for_external_feature PASSED  [ 90%]
tests/test_y14_5.py::test_partial_bonus_mid_range PASSED                 [ 95%]
tests/test_y14_5.py::test_actual_size_outside_limits_rejected PASSED     [100%]

============================== 20 passed in 0.04s ==============================
```

✓ All 20 tests pass (15 existing + 5 new).

---

## Step 5: Commit

**Command:**
```bash
git add src/tolcad/y14_5.py tests/test_y14_5.py
git commit -m "feat: bonus tolerance under MMC modifier"
```

**Output:**
```
[feat/functional-checker 786fff4] feat: bonus tolerance under MMC modifier
 2 files changed, 40 insertions(+)
```

**Commit SHA:** `786fff4`

---

## Verification of constraints

✓ **Module integrity:** No existing functions were modified. Verified that all original functions (`virtual_condition`, `vc_assembles`, `_check_fastener_pair`, `floating_fastener_tolerance`, `fixed_fastener_tolerance`, `fastener_assembles`) remain unchanged.

✓ **Import integrity:** The two `CITATION PENDING HUMAN VERIFICATION` docstring lines in floating_fastener_tolerance and fixed_fastener_tolerance were not touched.

✓ **Tier 1 precision:** Used `EPS = 1e-9` (from `tolcad.types`) for floating-point margin as required.

✓ **Test reuse:** Reused module-level constants `INTERNAL`, `EXTERNAL`, and `M8_BOLT` from existing test file rather than redefining them.

✓ **Architecture:** No module under `src/tolcad/` imports from `validation/`. New function adheres to all constraints.
