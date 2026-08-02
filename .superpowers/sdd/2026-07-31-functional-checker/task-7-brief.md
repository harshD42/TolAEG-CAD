### Task 7: Monte Carlo stack-up (Tier 2)

**Files:**
- Create: `src/tolcad/montecarlo.py`
- Test: `tests/test_montecarlo.py`

**Interfaces:**
- Consumes: `FeatureOfSize`, `Verdict`
- Produces:
  - `sample_size(feature: FeatureOfSize, rng, n: int, distribution: str = "normal") -> np.ndarray`
  - `clearance_yield(hole, shaft, n: int, seed: int, distribution: str = "normal") -> Verdict`

`clearance_yield` returns a `Verdict` whose `margin` is the estimated yield in
[0, 1] — the fraction of sampled part pairs achieving positive clearance.
`assembles` is True iff yield is 1.0 within sampling resolution.

The `"normal"` distribution places ±3σ at the tolerance limits and truncates;
`"uniform"` samples the limits uniformly. Both are reported; the choice is an
ablation axis, not a hidden assumption.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_montecarlo.py
import numpy as np
import pytest
from tolcad.iso286 import fit_from_designation
from tolcad.montecarlo import clearance_yield, sample_size
from tolcad.types import FeatureOfSize, FeatureType


def test_samples_stay_within_tolerance_limits():
    hole = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)
    rng = np.random.default_rng(42)
    samples = sample_size(hole, rng, n=10_000)
    assert samples.min() >= hole.min_size
    assert samples.max() <= hole.max_size


def test_uniform_distribution_spans_the_range():
    hole = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)
    rng = np.random.default_rng(42)
    samples = sample_size(hole, rng, n=10_000, distribution="uniform")
    assert samples.mean() == pytest.approx(20.0105, abs=1e-3)


def test_clearance_fit_yields_fully():
    """H7/g6 has positive minimum clearance, so yield must be exactly 1.0."""
    hole, shaft = fit_from_designation(20.0, "H7/g6")
    verdict = clearance_yield(hole, shaft, n=10_000, seed=0)
    assert verdict.margin == pytest.approx(1.0)
    assert verdict.assembles is True


def test_interference_fit_never_clears():
    """H7/p6 is a press fit; clearance yield must be exactly 0.0."""
    hole, shaft = fit_from_designation(20.0, "H7/p6")
    verdict = clearance_yield(hole, shaft, n=10_000, seed=0)
    assert verdict.margin == pytest.approx(0.0)
    assert verdict.assembles is False


def test_transition_fit_yields_partially():
    """H7/k6 sometimes clears and sometimes interferes."""
    hole, shaft = fit_from_designation(20.0, "H7/k6")
    verdict = clearance_yield(hole, shaft, n=50_000, seed=0, distribution="uniform")
    assert 0.0 < verdict.margin < 1.0


def test_identical_seeds_give_identical_results():
    hole, shaft = fit_from_designation(20.0, "H7/k6")
    a = clearance_yield(hole, shaft, n=10_000, seed=7)
    b = clearance_yield(hole, shaft, n=10_000, seed=7)
    assert a.margin == b.margin


def test_seed_is_recorded_in_detail():
    hole, shaft = fit_from_designation(20.0, "H7/g6")
    verdict = clearance_yield(hole, shaft, n=1_000, seed=99)
    assert verdict.detail["seed"] == 99
    assert verdict.detail["n"] == 1_000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_montecarlo.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.montecarlo'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/montecarlo.py
"""Tier 2: Monte Carlo tolerance stack-up.

Statistical, unlike Tier 1. Every result carries its seed and sample count so
that any reported number is reproducible.
"""

from __future__ import annotations

import numpy as np

from tolcad.types import FeatureOfSize, Verdict


def sample_size(
    feature: FeatureOfSize,
    rng: np.random.Generator,
    n: int,
    distribution: str = "normal",
) -> np.ndarray:
    """Draw n actual sizes for a toleranced feature, clipped to its limits.

    'normal' places +/-3 sigma at the tolerance limits, then truncates.
    'uniform' samples the limits uniformly.
    """
    lo, hi = feature.min_size, feature.max_size

    if distribution == "uniform":
        return rng.uniform(lo, hi, size=n)

    if distribution == "normal":
        mid = (lo + hi) / 2.0
        sigma = (hi - lo) / 6.0
        if sigma == 0.0:
            return np.full(n, mid)
        return np.clip(rng.normal(mid, sigma, size=n), lo, hi)

    raise ValueError(
        f"distribution must be 'normal' or 'uniform', got {distribution!r}"
    )


def clearance_yield(
    hole: FeatureOfSize,
    shaft: FeatureOfSize,
    n: int,
    seed: int,
    distribution: str = "normal",
) -> Verdict:
    """Estimate the fraction of part pairs achieving positive clearance.

    margin is the yield in [0, 1]. assembles is True only at full yield.
    """
    rng = np.random.default_rng(seed)
    holes = sample_size(hole, rng, n, distribution)
    shafts = sample_size(shaft, rng, n, distribution)

    clearances = holes - shafts
    yield_frac = float(np.mean(clearances > 0.0))

    return Verdict(
        assembles=yield_frac >= 1.0,
        margin=yield_frac,
        method="monte_carlo_clearance",
        detail={
            "seed": seed,
            "n": n,
            "distribution": distribution,
            "min_clearance": float(clearances.min()),
            "mean_clearance": float(clearances.mean()),
        },
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_montecarlo.py -v`
Expected: PASS, 7 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/montecarlo.py tests/test_montecarlo.py
git commit -m "feat: Monte Carlo clearance stack-up (Tier 2)"
```

---

