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
