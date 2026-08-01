"""Gate A: verdict stability under input perturbation.

An unreliable oracle attenuates every downstream correlation by sqrt(reliability),
which can move Gate B's result across a pre-registered threshold. This measures it.

SENSITIVITY AND INTERPRETATION:
A verdict flips only if a perturbation shifts the margin far enough to cross the boundary
(margin from positive to negative, or vice versa). The perturbation magnitude Δmargin is a
sum of several signed uniform(-epsilon, +epsilon) draws, so it concentrates near zero with
standard deviation roughly epsilon * sqrt(n_fields / 3). Moving margin by more than ~2*epsilon
is a tail event.

Practical consequence: This metric detects instability only for mates whose margin is within
roughly 2-3*epsilon of zero. For a deterministic checker with comfortably larger margins,
the metric reports 1.0 — which is the correct answer (no instability within the tested band),
but NOT a proof that the checker is reliable in general. A 1.0 result means:
- "No instability detected in mates with |margin| >= 2*epsilon" (the tested band)
- NOT "the checker is proven reliable under all perturbations"

If a design has all margins well outside the tested band, this metric cannot detect its
instability — it will report 1.0. This is correct for the measurement definition but must
not be mistaken for a strong guarantee.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np

from tolcad.checker import check

# Cases whose margin is within this multiple of epsilon are genuinely ambiguous;
# a flip there is correct behaviour, so they are excluded from the denominator.
# A case is genuinely ambiguous only when its margin is smaller than a couple of
# perturbation steps; beyond that, a flip indicates real instability.
BOUNDARY_BAND = 2.0

_PERTURBABLE = ("nominal", "lower_dev", "upper_dev", "position_tol")


@dataclass(frozen=True)
class StabilityResult:
    """Result of verdict stability measurement.

    value: fraction of tested (non-boundary) mates whose verdict survived perturbation.
    tested: number of mates outside the boundary band (actually tested).
    excluded: number of mates inside the boundary band (excluded from denominator).
    """

    value: float
    tested: int
    excluded: int

    def __float__(self) -> float:
        """Allow StabilityResult to be used as a float in comparisons and arithmetic."""
        return self.value


def _perturb(mate: dict, epsilon: float, rng: np.random.Generator) -> dict:
    """Perturb mate parameters by uniform random ±epsilon.

    Each parameter in _PERTURBABLE that exists in a dict is perturbed by adding a value
    from uniform(-epsilon, +epsilon). Handles aliasing correctly: each distinct dict object
    is perturbed exactly once, even if the mate structure contains the same dict object
    multiple times (e.g., when hole_a and hole_b reference the same dict).
    """
    out = copy.deepcopy(mate)
    seen_ids = set()
    for value in out.values():
        if isinstance(value, dict) and id(value) not in seen_ids:
            seen_ids.add(id(value))
            for key in _PERTURBABLE:
                if key in value:
                    value[key] += float(rng.uniform(-epsilon, epsilon))
    return out


def verdict_stability(mates: list[dict], epsilon: float, seed: int) -> StabilityResult:
    """Fraction of non-boundary mates whose verdict survives an epsilon perturbation.

    Returns a StabilityResult with value=1.0 when every case falls inside the boundary
    band (nothing to test). The tested and excluded counts allow the caller to distinguish
    this case from a verified 1.0 stability.

    Args:
        mates: List of mate specifications to test.
        epsilon: Perturbation magnitude.
        seed: Random seed for reproducibility.

    Returns:
        StabilityResult with stability value and test counts.
    """
    if not mates:
        raise ValueError("need at least one mate to measure stability")

    rng = np.random.default_rng(seed)
    tested = stable = excluded = 0

    for mate in mates:
        base = check(mate)
        if abs(base.margin) < BOUNDARY_BAND * epsilon:
            excluded += 1
            continue  # genuinely ambiguous; a flip here is correct
        tested += 1
        if check(_perturb(mate, epsilon, rng)).assembles == base.assembles:
            stable += 1

    stability_value = 1.0 if tested == 0 else stable / tested
    return StabilityResult(value=stability_value, tested=tested, excluded=excluded)
