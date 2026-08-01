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

SCOPE: TIER 1 MATES ONLY.
`margin` is not a single comparable unit across tiers: for Tier 1 mates (virtual_condition,
floating_fastener, fixed_fastener) it is millimetres of geometric slack, but for Tier 2
(iso_fit) it is a Monte Carlo clearance YIELD in [0, 1]. Comparing a yield to
`BOUNDARY_BAND * epsilon` (an mm-scale quantity) is meaningless, and Tier 2 mates have no
sub-dict fields for `_perturb` to find (their fields are top-level scalars), so they would
silently score a vacuous 1.0 even if never actually perturbed. For both reasons,
`verdict_stability` REJECTS any mate whose `type` is not one of the three Tier 1 types.
There is no partial support for Tier 2 mates in this module.
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

# The only mate types whose margin is millimetres of geometric slack and whose
# parameters live in perturbable sub-dicts. iso_fit (Tier 2) is deliberately
# excluded; see the module docstring.
_TIER1_TYPES = frozenset({"virtual_condition", "floating_fastener", "fixed_fastener"})


@dataclass(frozen=True)
class StabilityResult:
    """Result of verdict stability measurement.

    value: fraction of tested (non-boundary) mates whose verdict survived perturbation.
    tested: number of mates outside the boundary band (actually tested).
    excluded: number of mates inside the boundary band (excluded from denominator).
    min_abs_margin: smallest |margin| among tested mates (None if tested == 0).
    max_abs_margin: largest |margin| among tested mates (None if tested == 0).
        Reporting this range alongside `value` lets a reader see what band was
        actually probed: a 1.0 result over mates with min_abs_margin >> epsilon
        means "no instability detected far from the boundary," which is a much
        weaker claim than a 1.0 result that includes mates close to the
        exclusion threshold.
    """

    value: float
    tested: int
    excluded: int
    min_abs_margin: float | None = None
    max_abs_margin: float | None = None

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
        mates: List of mate specifications to test. Every mate must be a Tier 1
            type (virtual_condition, floating_fastener, fixed_fastener). Tier 2
            (iso_fit) mates are rejected; see the module docstring for why.
        epsilon: Perturbation magnitude.
        seed: Random seed for reproducibility.

    Returns:
        StabilityResult with stability value and test counts.

    Raises:
        ValueError: if `mates` is empty, or if any mate's `type` is not a
            Tier 1 type.
    """
    if not mates:
        raise ValueError("need at least one mate to measure stability")

    for mate in mates:
        mate_type = mate.get("type")
        if mate_type not in _TIER1_TYPES:
            raise ValueError(
                f"verdict_stability only supports Tier 1 mate types "
                f"{sorted(_TIER1_TYPES)}; got {mate_type!r}. Tier 2 margins "
                "(e.g. iso_fit's Monte Carlo yield) are not commensurable "
                "with Tier 1 mm-of-slack margins — see the module docstring."
            )

    rng = np.random.default_rng(seed)
    tested = stable = excluded = 0
    tested_abs_margins: list[float] = []

    for mate in mates:
        base = check(mate)
        if abs(base.margin) < BOUNDARY_BAND * epsilon:
            excluded += 1
            continue  # genuinely ambiguous; a flip here is correct
        tested += 1
        tested_abs_margins.append(abs(base.margin))
        if check(_perturb(mate, epsilon, rng)).assembles == base.assembles:
            stable += 1

    stability_value = 1.0 if tested == 0 else stable / tested
    return StabilityResult(
        value=stability_value,
        tested=tested,
        excluded=excluded,
        min_abs_margin=min(tested_abs_margins) if tested_abs_margins else None,
        max_abs_margin=max(tested_abs_margins) if tested_abs_margins else None,
    )
