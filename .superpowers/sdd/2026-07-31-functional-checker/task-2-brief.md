### Task 2: Core domain types

**Files:**
- Create: `src/tolcad/types.py`
- Test: `tests/test_types.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `FeatureType` enum: `INTERNAL`, `EXTERNAL`
  - `FeatureOfSize(nominal: float, lower_dev: float, upper_dev: float, feature_type: FeatureType, position_tol: float = 0.0)` with properties `mmc -> float`, `lmc -> float`
  - `Verdict(assembles: bool, margin: float, method: str, detail: dict)`

`mmc` is the maximum-material condition: the **largest** size for an external feature, the **smallest** for an internal one. `margin` is positive when assembly is guaranteed, in mm.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_types.py
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

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_types.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.types'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/types.py
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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_types.py -v`
Expected: PASS, 3 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/types.py tests/test_types.py
git commit -m "feat: core domain types for toleranced features"
```

---

