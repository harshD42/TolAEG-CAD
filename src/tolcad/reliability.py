"""Gate A: verdict stability under input perturbation.

An unreliable oracle attenuates every downstream correlation by sqrt(reliability),
which can move Gate B's result across a pre-registered threshold. This measures it.
"""

from __future__ import annotations

import copy

import numpy as np

from tolcad.checker import check

# Cases whose margin is within this multiple of epsilon are genuinely ambiguous;
# a flip there is correct behaviour, so they are excluded from the denominator.
BOUNDARY_BAND = 10.0

_PERTURBABLE = ("nominal", "lower_dev", "upper_dev", "position_tol")


def _perturb(mate: dict, epsilon: float, rng: np.random.Generator) -> dict:
    out = copy.deepcopy(mate)
    for value in out.values():
        if isinstance(value, dict):
            for key in _PERTURBABLE:
                if key in value:
                    value[key] += float(rng.uniform(-epsilon, epsilon))
    return out


def verdict_stability(mates: list[dict], epsilon: float, seed: int) -> float:
    """Fraction of non-boundary mates whose verdict survives an epsilon perturbation.

    Returns 1.0 when every case falls inside the boundary band (nothing to test).
    """
    if not mates:
        raise ValueError("need at least one mate to measure stability")

    rng = np.random.default_rng(seed)
    tested = stable = 0

    for mate in mates:
        base = check(mate)
        if abs(base.margin) < BOUNDARY_BAND * epsilon:
            continue  # genuinely ambiguous; a flip here is correct
        tested += 1
        if check(_perturb(mate, epsilon, rng)).assembles == base.assembles:
            stable += 1

    return 1.0 if tested == 0 else stable / tested
