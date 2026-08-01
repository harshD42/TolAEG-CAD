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
