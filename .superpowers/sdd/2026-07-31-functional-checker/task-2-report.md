# Task 2: Core Domain Types — Implementation Report

## Summary
Successfully implemented core domain types for the tolcad functional checker, defining the fundamental abstractions for toleranced features and verdict results.

## Step-by-Step Execution

### Step 1: Write the Failing Test
**File created:** `tests/test_types.py`

Wrote three test cases:
1. `test_internal_feature_mmc_is_smallest_size()` — verifies MMC for holes is the smallest size
2. `test_external_feature_mmc_is_largest_size()` — verifies MMC for pins is the largest size
3. `test_verdict_is_immutable()` — verifies Verdict dataclass is frozen and raises AttributeError on mutation

### Step 2: Run Test to Verify Failure
**Command:**
```bash
cd "C:\Users\harsh\Downloads\Projects\Paper1" && python -m pytest tests/test_types.py -v
```

**Output (expected failure):**
```
ERROR collecting tests/test_types.py
ImportError while importing test module...
E   ModuleNotFoundError: No module named 'tolcad.types'
```

✓ Test failed as expected with `ModuleNotFoundError`.

### Step 3: Write Minimal Implementation
**File created:** `src/tolcad/types.py`

Implemented:
- **Module-level constant:** `EPS = 1e-9` (for Tier 1 exact comparisons)
- **FeatureType enum:** `INTERNAL` and `EXTERNAL` members for identifying whether a feature removes or adds material
- **FeatureOfSize dataclass:** Frozen, with constructor parameters:
  - `nominal: float` — nominal dimension in mm
  - `lower_dev: float` — lower deviation from nominal
  - `upper_dev: float` — upper deviation from nominal
  - `feature_type: FeatureType` — whether it's a hole or pin
  - `position_tol: float = 0.0` — positional tolerance (optional)

  Properties implemented:
  - `max_size` → `nominal + upper_dev`
  - `min_size` → `nominal + lower_dev`
  - `mmc` (maximum material condition): For INTERNAL features (holes), returns `min_size` (smallest size means most material present). For EXTERNAL features (pins), returns `max_size` (largest size means most material present).
  - `lmc` (least material condition): Opposite of MMC.

  Validation in `__post_init__`:
  - Ensures `upper_dev >= lower_dev`
  - Ensures `position_tol >= 0.0`

- **Verdict dataclass:** Frozen, representing the result of a functional check:
  - `assembles: bool` — whether assembly is possible
  - `margin: float` — positive when assembly is guaranteed, in mm
  - `method: str` — identification of the checking method used
  - `detail: dict` — additional metadata (defaults to empty dict)

### Step 4: Run Test to Verify Success
**Command:**
```bash
cd "C:\Users\harsh\Downloads\Projects\Paper1" && python -m pytest tests/test_types.py -v
```

**Output (all passing):**
```
tests/test_types.py::test_internal_feature_mmc_is_smallest_size PASSED   [ 33%]
tests/test_types.py::test_external_feature_mmc_is_largest_size PASSED    [ 66%]
tests/test_types.py::test_verdict_is_immutable PASSED                    [100%]

============================== 3 passed in 0.02s ==============================
```

✓ All three tests passed.

### Step 5: Commit
**Command:**
```bash
cd "C:\Users\harsh\Downloads\Projects\Paper1" && git add src/tolcad/types.py tests/test_types.py && git commit -m "feat: core domain types for toleranced features"
```

**Output:**
```
[feat/functional-checker e4e735a] feat: core domain types for toleranced features
 2 files changed, 95 insertions(+)
 create mode 100644 src/tolcad/types.py
 create mode 100644 tests/test_types.py
```

**Commit SHA:** `e4e735a`

## Verification
Ran full test suite to ensure no regressions:
```bash
python -m pytest -v
```

**Result:**
```
tests/test_smoke.py::test_package_imports PASSED                         [ 25%]
tests/test_types.py::test_internal_feature_mmc_is_smallest_size PASSED   [ 50%]
tests/test_types.py::test_external_feature_mmc_is_largest_size PASSED    [ 75%]
tests/test_types.py::test_verdict_is_immutable PASSED                    [100%]

============================== 4 passed in 0.02s ==============================
```

✓ All tests pass, including the pre-existing smoke test.

## Files Created

### `src/tolcad/types.py` (71 lines)
```python
"""Core domain types. All dimensions in millimetres."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

EPS = 1e-9


class FeatureType(Enum):
    """Whether a feature of size removes or adds material."""

    INTERNAL = "internal"  # hole, slot, bore
    EXTERNAL = "external"  # pin, shaft, boss


@dataclass(frozen=True)
class FeatureOfSize:
    """A toleranced feature of size, per ASME Y14.5.

    Deviations are signed offsets from nominal, in mm.
    A Ø8.5 +0.2/-0.0 hole is FeatureOfSize(8.5, 0.0, 0.2, INTERNAL).
    """

    nominal: float
    lower_dev: float
    upper_dev: float
    feature_type: FeatureType
    position_tol: float = 0.0

    def __post_init__(self) -> None:
        if self.upper_dev < self.lower_dev:
            raise ValueError(
                f"upper_dev {self.upper_dev} below lower_dev {self.lower_dev}"
            )
        if self.position_tol < 0.0:
            raise ValueError(f"position_tol must be non-negative, got {self.position_tol}")

    @property
    def max_size(self) -> float:
        return self.nominal + self.upper_dev

    @property
    def min_size(self) -> float:
        return self.nominal + self.lower_dev

    @property
    def mmc(self) -> float:
        """Maximum material condition: most material present."""
        if self.feature_type is FeatureType.INTERNAL:
            return self.min_size
        return self.max_size

    @property
    def lmc(self) -> float:
        """Least material condition: least material present."""
        if self.feature_type is FeatureType.INTERNAL:
            return self.max_size
        return self.min_size


@dataclass(frozen=True)
class Verdict:
    """Result of a functional check.

    margin > 0 means assembly is guaranteed, in mm of slack.
    """

    assembles: bool
    margin: float
    method: str
    detail: dict = field(default_factory=dict)
```

### `tests/test_types.py` (24 lines)
```python
import pytest
from tolcad.types import FeatureOfSize, FeatureType, Verdict


def test_internal_feature_mmc_is_smallest_size():
    # Ø8.5 +0.2/-0.0 hole
    hole = FeatureOfSize(8.5, 0.0, 0.2, FeatureType.INTERNAL)
    assert hole.mmc == pytest.approx(8.5)
    assert hole.lmc == pytest.approx(8.7)


def test_external_feature_mmc_is_largest_size():
    # Ø8.0 +0.0/-0.1 pin
    pin = FeatureOfSize(8.0, -0.1, 0.0, FeatureType.EXTERNAL)
    assert pin.mmc == pytest.approx(8.0)
    assert pin.lmc == pytest.approx(7.9)


def test_verdict_is_immutable():
    v = Verdict(assembles=True, margin=0.5, method="floating_fastener", detail={})
    with pytest.raises(AttributeError):
        v.assembles = False
```

## Key Design Points

1. **MMC Semantics:** Correctly implements ASME Y14.5 semantics:
   - For INTERNAL features (holes): MMC is the smallest size
   - For EXTERNAL features (pins): MMC is the largest size

2. **Frozen Dataclasses:** Both `FeatureOfSize` and `Verdict` use `@dataclass(frozen=True)` to ensure immutability as required by the interface.

3. **Validation:** `FeatureOfSize.__post_init__` enforces invariants:
   - Upper deviation must not be less than lower deviation
   - Position tolerance must be non-negative

4. **EPS Constant:** Module-level `EPS = 1e-9` is available for Tier 1 exact comparisons per CLAUDE.md conventions.

5. **Default Factory:** `Verdict.detail` uses `field(default_factory=dict)` to avoid mutable default arguments.

## Notes for Next Implementer

- These types are the foundation for all downstream tasks (Tasks 3-14). The interfaces must remain stable.
- The MMC/LMC logic is counterintuitive but correct per ASME Y14.5 — do not "simplify" it based on intuition.
- `FrozenInstanceError` from frozen dataclasses subclasses `AttributeError`, so `pytest.raises(AttributeError)` correctly catches immutability violations.
- `EPS = 1e-9` is available module-wide for all subsequent tolerance comparisons.
