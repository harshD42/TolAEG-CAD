### Task 5: Bonus tolerance under the MMC modifier

**Files:**
- Modify: `src/tolcad/y14_5.py` (append)
- Modify: `tests/test_y14_5.py` (append)

**Interfaces:**
- Consumes: `FeatureOfSize`, `FeatureType`
- Produces: `bonus_tolerance(feature: FeatureOfSize, actual_size: float) -> float`

Under the MMC modifier, a feature departing from MMC toward LMC earns extra
position tolerance equal to that departure. This matters because it is exactly the
mechanism that makes "nominally correct" parts assemble in practice — omitting it
would make the checker pessimistic and overstate the paper's finding.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_y14_5.py  (append)
from tolcad.y14_5 import bonus_tolerance


def test_no_bonus_at_mmc():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    assert bonus_tolerance(hole, 8.5) == pytest.approx(0.0)


def test_full_bonus_at_lmc_for_internal_feature():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    assert bonus_tolerance(hole, 8.7) == pytest.approx(0.2)


def test_full_bonus_at_lmc_for_external_feature():
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL)
    assert bonus_tolerance(pin, 7.9) == pytest.approx(0.1)


def test_partial_bonus_mid_range():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    assert bonus_tolerance(hole, 8.6) == pytest.approx(0.1)


def test_actual_size_outside_limits_rejected():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    with pytest.raises(ValueError, match="outside"):
        bonus_tolerance(hole, 8.9)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_y14_5.py -v`
Expected: FAIL with `ImportError: cannot import name 'bonus_tolerance'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/y14_5.py  (append)

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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_y14_5.py -v`
Expected: PASS, 18 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/y14_5.py tests/test_y14_5.py
git commit -m "feat: bonus tolerance under MMC modifier"
```

---

