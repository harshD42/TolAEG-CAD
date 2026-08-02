### Task 8: Monte Carlo convergence (Gate A criterion)

**Files:**
- Create: `tests/test_convergence.py`
- Modify: `pyproject.toml` (register the `slow` marker)

**Interfaces:**
- Consumes: `clearance_yield`, `fit_from_designation`
- Produces: nothing importable; establishes the Gate A stability criterion

Gate A requires the yield estimate to be stable to **±0.5% range across 5 seeds at N=100,000**.
A transition fit is the right probe: clearance and interference fits are degenerate at
0.0 and 1.0 and would pass trivially.

**Why N=100k and not 10k.** For a transition fit with yield p≈0.6, the binomial standard
error is √(p(1−p)/N). At N=10k that is ≈0.0049, so the expected range across 5 seeds is
≈2.33σ ≈ 0.011 — twice the threshold, and unachievable by correct code. At N=100k,
SE ≈ 0.0016 and expected range ≈ 0.0036. Spec §7 was corrected accordingly, pre-data.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_convergence.py
"""Gate A: Monte Carlo stability. Threshold is pre-registered in spec section 7."""

import pytest
from tolcad.iso286 import fit_from_designation
from tolcad.montecarlo import clearance_yield

GATE_A_TOLERANCE = 0.005  # +/- 0.5%, pre-registered. DO NOT LOOSEN.


@pytest.mark.slow
def test_yield_stable_across_seeds_at_100k_samples():
    hole, shaft = fit_from_designation(20.0, "H7/k6")
    yields = [
        clearance_yield(hole, shaft, n=100_000, seed=s, distribution="uniform").margin
        for s in range(5)
    ]
    spread = max(yields) - min(yields)
    assert spread <= GATE_A_TOLERANCE, (
        f"yield spread {spread:.4f} exceeds Gate A tolerance {GATE_A_TOLERANCE}; "
        f"yields={yields}"
    )


@pytest.mark.slow
def test_convergence_improves_with_sample_count():
    """Spread at 100k must not exceed spread at 1k. Guards against a broken RNG path."""
    hole, shaft = fit_from_designation(20.0, "H7/k6")

    def spread(n: int) -> float:
        ys = [
            clearance_yield(hole, shaft, n=n, seed=s, distribution="uniform").margin
            for s in range(5)
        ]
        return max(ys) - min(ys)

    assert spread(100_000) <= spread(1_000)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_convergence.py -v`
Expected: FAIL with `'slow' not found in markers configuration option` (strict markers not yet registered)

- [ ] **Step 3: Register the marker**

```toml
# pyproject.toml  — replace the [tool.pytest.ini_options] block
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "--strict-markers"
markers = [
    "slow: Monte Carlo convergence checks (deselect with -m 'not slow')",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_convergence.py -v`
Expected: PASS, 2 tests

If `test_yield_stable_across_seeds_at_100k_samples` fails, **do not raise
`GATE_A_TOLERANCE`.** The threshold is pre-registered. Investigate the RNG path or
record the failure as a Gate A deviation in the spec.

- [ ] **Step 5: Commit**

```bash
git add tests/test_convergence.py pyproject.toml
git commit -m "test: Monte Carlo convergence criterion for Gate A"
```

---

