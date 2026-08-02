### Task 3: Virtual condition (Tier 1)

**Files:**
- Create: `src/tolcad/y14_5.py`
- Test: `tests/test_y14_5.py`

**Interfaces:**
- Consumes: `FeatureOfSize`, `FeatureType`, `Verdict`, `EPS` from `tolcad.types`
- Produces:
  - `virtual_condition(feature: FeatureOfSize) -> float`
  - `vc_assembles(pin: FeatureOfSize, hole: FeatureOfSize) -> Verdict`

Virtual condition is the worst-case boundary a feature can occupy:
external `VC = MMC + position_tol`, internal `VC = MMC - position_tol`.
Assembly is guaranteed iff `VC_pin <= VC_hole`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_y14_5.py
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

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_y14_5.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.y14_5'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/y14_5.py
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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_y14_5.py -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/y14_5.py tests/test_y14_5.py
git commit -m "feat: virtual condition check (Tier 1)"
```

---

