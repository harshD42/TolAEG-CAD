### Task 10: Top-level checker dispatch

**Files:**
- Create: `src/tolcad/checker.py`
- Test: `tests/test_checker.py`

**Interfaces:**
- Consumes: everything above
- Produces: `check(mate: dict) -> Verdict`

`mate` is a plain dict so the Phase 3 generator can emit JSON without importing tolcad.
Required key `type`, one of `"virtual_condition"`, `"floating_fastener"`,
`"fixed_fastener"`, `"iso_fit"`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_checker.py
import pytest
from tolcad.checker import check


def test_dispatches_virtual_condition():
    verdict = check({
        "type": "virtual_condition",
        "pin": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0, "position_tol": 0.0},
        "hole": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.2},
    })
    assert verdict.assembles is True
    assert verdict.method == "virtual_condition"


def test_dispatches_floating_fastener():
    hole = {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.6}
    verdict = check({
        "type": "floating_fastener",
        "hole_a": hole,
        "hole_b": hole,
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    })
    assert verdict.assembles is False


def test_dispatches_iso_fit():
    verdict = check({
        "type": "iso_fit",
        "nominal": 20.0,
        "designation": "H7/g6",
        "n": 10_000,
        "seed": 0,
    })
    assert verdict.margin == pytest.approx(1.0)


def test_unknown_mate_type_rejected():
    with pytest.raises(ValueError, match="unknown mate type"):
        check({"type": "weld"})


def test_missing_type_key_rejected():
    with pytest.raises(ValueError, match="'type'"):
        check({})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_checker.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.checker'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/checker.py
"""Top-level dispatch over mate types.

Mates arrive as plain dicts so the generator can emit JSON without importing tolcad.
"""

from __future__ import annotations

from tolcad.iso286 import fit_from_designation
from tolcad.montecarlo import clearance_yield
from tolcad.types import FeatureOfSize, FeatureType, Verdict
from tolcad.y14_5 import fastener_assembles, vc_assembles


def _feature(spec: dict, feature_type: FeatureType) -> FeatureOfSize:
    return FeatureOfSize(
        nominal=spec["nominal"],
        lower_dev=spec["lower_dev"],
        upper_dev=spec["upper_dev"],
        feature_type=feature_type,
        position_tol=spec.get("position_tol", 0.0),
    )


def check(mate: dict) -> Verdict:
    """Evaluate a single mate specification."""
    if "type" not in mate:
        raise ValueError("mate specification requires a 'type' key")

    kind = mate["type"]

    if kind == "virtual_condition":
        return vc_assembles(
            _feature(mate["pin"], FeatureType.EXTERNAL),
            _feature(mate["hole"], FeatureType.INTERNAL),
        )

    if kind in ("floating_fastener", "fixed_fastener"):
        return fastener_assembles(
            _feature(mate["hole_a"], FeatureType.INTERNAL),
            _feature(mate["hole_b"], FeatureType.INTERNAL),
            _feature(mate["fastener"], FeatureType.EXTERNAL),
            condition=kind.replace("_fastener", ""),
        )

    if kind == "iso_fit":
        hole, shaft = fit_from_designation(mate["nominal"], mate["designation"])
        return clearance_yield(
            hole,
            shaft,
            n=mate.get("n", 10_000),
            seed=mate.get("seed", 0),
            distribution=mate.get("distribution", "normal"),
        )

    raise ValueError(f"unknown mate type {kind!r}")
```

- [ ] **Step 4: Run all tests**

Run: `pytest -v`
Expected: PASS, all tests including both in `test_architecture.py`

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/checker.py tests/test_checker.py
git commit -m "feat: top-level mate dispatch"
```

---

