### Task 4: Floating and fixed fastener conditions (Tier 1)

**Files:**
- Modify: `src/tolcad/y14_5.py` (append)
- Modify: `tests/test_y14_5.py` (append)

**Interfaces:**
- Consumes: `FeatureOfSize`, `FeatureType`, `Verdict`, `EPS`
- Produces:
  - `floating_fastener_tolerance(hole: FeatureOfSize, fastener: FeatureOfSize) -> float`
  - `fixed_fastener_tolerance(hole: FeatureOfSize, fastener: FeatureOfSize) -> float`
  - `fastener_assembles(hole_a, hole_b, fastener, condition: str) -> Verdict`

Floating fastener (bolt through clearance holes in both parts, nut on the back):
`T = H - F`, available to **each** part.
Fixed fastener (one part threaded or with a pressed pin): `T = (H - F) / 2`.
`H` = hole MMC, `F` = fastener MMC.

**Citation requirement:** before implementing, confirm both formulas and at least
two worked numeric examples against a citable source — ASME Y14.5-2018, or
Meadows / Krulikowski. Record the source and page in a docstring. The examples
below are canonical but MUST be verified against print, not accepted from this plan.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_y14_5.py  (append)
from tolcad.y14_5 import (
    fastener_assembles,
    fixed_fastener_tolerance,
    floating_fastener_tolerance,
)

# Canonical worked example: M8 bolt (Ø8.0 max) through Ø8.5 min clearance holes.
M8_BOLT = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL)
CLEARANCE_HOLE = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)


def test_floating_fastener_tolerance_is_hole_mmc_minus_fastener_mmc():
    # T = H - F = 8.5 - 8.0 = 0.5 per part
    assert floating_fastener_tolerance(CLEARANCE_HOLE, M8_BOLT) == pytest.approx(0.5)


def test_fixed_fastener_tolerance_is_half_the_floating_value():
    # T = (H - F) / 2 = 0.25 per part
    assert fixed_fastener_tolerance(CLEARANCE_HOLE, M8_BOLT) == pytest.approx(0.25)


def test_floating_fastener_assembles_at_allowable_tolerance():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="floating")
    assert verdict.assembles is True


def test_floating_fastener_fails_above_allowable_tolerance():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="floating")
    assert verdict.assembles is False
    assert verdict.margin == pytest.approx(-0.1)


def test_fixed_fastener_is_stricter_than_floating():
    """Same geometry: a tolerance that passes floating must fail fixed at 0.5."""
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    assert fastener_assembles(hole, hole, M8_BOLT, condition="floating").assembles
    assert not fastener_assembles(hole, hole, M8_BOLT, condition="fixed").assembles


def test_asymmetric_holes_use_the_worse_one():
    tight = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    loose = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    verdict = fastener_assembles(tight, loose, M8_BOLT, condition="floating")
    assert verdict.assembles is False


def test_unknown_condition_rejected():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    with pytest.raises(ValueError, match="condition"):
        fastener_assembles(hole, hole, M8_BOLT, condition="press")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_y14_5.py -v`
Expected: FAIL with `ImportError: cannot import name 'floating_fastener_tolerance'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/y14_5.py  (append)

def _check_fastener_pair(hole: FeatureOfSize, fastener: FeatureOfSize) -> None:
    if hole.feature_type is not FeatureType.INTERNAL:
        raise ValueError("hole must be an internal feature")
    if fastener.feature_type is not FeatureType.EXTERNAL:
        raise ValueError("fastener must be an external feature")


def floating_fastener_tolerance(
    hole: FeatureOfSize, fastener: FeatureOfSize
) -> float:
    """Position tolerance available to each part, floating fastener condition.

    T = H - F, where H is hole MMC and F is fastener MMC.
    Source: ASME Y14.5 floating fastener formula. Verify citation before use.
    """
    _check_fastener_pair(hole, fastener)
    return hole.mmc - fastener.mmc


def fixed_fastener_tolerance(hole: FeatureOfSize, fastener: FeatureOfSize) -> float:
    """Position tolerance available to each part, fixed fastener condition.

    T = (H - F) / 2. The available clearance is split between the two parts
    because the fastener cannot shift in the part that constrains it.
    Assumes a projected tolerance zone.
    """
    _check_fastener_pair(hole, fastener)
    return (hole.mmc - fastener.mmc) / 2.0


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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_y14_5.py -v`
Expected: PASS, 13 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/y14_5.py tests/test_y14_5.py
git commit -m "feat: floating and fixed fastener conditions (Tier 1)"
```

---

