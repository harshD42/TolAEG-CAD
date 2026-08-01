"""Seed -> AssemblySpec. Deterministic, no CAD dependency.

Difficulty 1-4 sets the number of mates (the tolerance loop length, capped at 4
by spec section 4.1) and how tightly position tolerances crowd the allowable.
Higher difficulty produces more marginal joints, so the corpus contains both
assemblable and non-assemblable cases by construction.
"""

from __future__ import annotations

import numpy as np

from tolcad.gen.features import (
    FASTENER_SIZES, SUPPORTED_FITS, clearance_hole_for, iso_fit_mate_features,
    tapped_hole_for,
)
from tolcad.gen.layout import plate_size_for_mates
from tolcad.gen.spec import AssemblySpec, MateSpec

MAX_DIFFICULTY = 4

# Fraction of the allowable position tolerance actually applied, by difficulty.
#
# EVERY RANGE MUST STRADDLE 1.0. The applied tolerance is allowable * f, and the
# Y14.5 margin reduces to allowable * (1 - f) for a floating fastener and
# allowable * (1 - mean(f_a, f_b)) for a fixed one. So f <= 1 everywhere makes
# the margin non-negative *identically*: an earlier ladder capped d1-d3 at 1.0
# and produced zero Tier 1 failures at three of the four levels, which meant a
# model that always answered "assembles" scored 100% on Tier 1 below d4. Those
# levels measured nothing.
#
# The ranges below were tuned by measuring the Tier 1 failure rate over seeds
# 0-199 at each difficulty; see the table in the module tests. The shape is
# monotonically increasing, roughly 20% at d1 to 70% at d4.
_TOL_FRACTION_RANGE = {
    1: (0.60, 1.09),
    2: (0.65, 1.16),
    3: (0.70, 1.25),
    4: (0.72, 1.34),
}

_TIER1_KINDS = ("floating_fastener", "fixed_fastener")

# Monte Carlo seeds for iso_fit mates are derived from (assembly seed, mate
# index) so they are reproducible from the spec alone. The offset keeps every
# generated seed clear of 0, which is tolcad.checker's fallback: a spec that
# lost its seed on the way through JSON is then visibly different from one that
# legitimately drew seed 0.
_MC_SEED_BASE = 10_000
_MC_SAMPLES = 100_000

# Nominal diameters an iso_fit mate is drawn from. Named rather than inline so
# tests/gen/test_features.py can exercise the disclosure at the sizes the
# corpus ACTUALLY contains -- 12 and 16 both sit in the ISO band 10 < d <= 18,
# which an arbitrary test nominal set can miss entirely.
_ISO_FIT_NOMINALS_MM: tuple[float, ...] = (10.0, 12.0, 16.0, 20.0, 25.0)

# The plate thickness the sampler builds to. Also the projection distance for a
# fixed fastener: the fastener crosses part_a's full thickness before it reaches
# the tapped feature in part_b. Kept as one constant so the recorded projected
# zone and the built geometry cannot drift apart.
_PLATE_THICKNESS_MM = 8.0

# Fastener size tolerance. NO STANDARD BEHIND THESE TWO NUMBERS, deliberately.
# A real citation would be ISO 4759-1 (tolerances for fasteners) or ISO 965
# (ISO general purpose metric screw threads -- tolerances), neither of which has
# been obtained and checked against the primary text, and inventing a citation
# is worse than declaring the gap. So this is a flat, standard-free
# simplification, stated as such -- the same treatment features.py gives the
# tapped hole's band.
#
# PROVABLY INERT, for the same structural reason. A fastener is an EXTERNAL
# feature, so its MMC is max_size = nominal + upper_dev. _FASTENER_UPPER_DEV_MM
# is 0.0, so MMC is exactly the nominal diameter, and y14_5.fastener_assembles
# reads fastener.mmc and nothing else -- never LMC, never the band width. The
# lower deviation therefore cannot move any verdict in the corpus at any value,
# and the upper deviation could only move one by ceasing to be zero.
# tests/gen/test_sampler.py pins MMC == nominal over every sampled Tier 1 mate.
_FASTENER_LOWER_DEV_MM = -0.1
_FASTENER_UPPER_DEV_MM = 0.0


def _mc_seed_for(seed: int, mate_index: int) -> int:
    """Deterministic, collision-free Monte Carlo seed for one mate."""
    return _MC_SEED_BASE + seed * MAX_DIFFICULTY + mate_index


def _tier1_mate(rng: np.random.Generator, difficulty: int) -> MateSpec:
    fastener_mm = float(rng.choice(FASTENER_SIZES))
    grade = str(rng.choice(("close", "normal", "loose")))
    kind = str(rng.choice(_TIER1_KINDS))

    hole = clearance_hole_for(fastener_mm, grade)
    fastener = {
        "nominal": fastener_mm,
        "lower_dev": _FASTENER_LOWER_DEV_MM,
        "upper_dev": _FASTENER_UPPER_DEV_MM,
    }

    # Allowable per Y14.5: floating T = H - F; fixed splits H - F across both parts.
    hole_mmc = hole["nominal"] + hole["lower_dev"]
    allowable = hole_mmc - fastener_mm
    if kind == "fixed_fastener":
        allowable /= 2.0

    lo, hi = _TOL_FRACTION_RANGE[difficulty]
    tol_a = round(allowable * float(rng.uniform(lo, hi)), 4)
    tol_b = round(allowable * float(rng.uniform(lo, hi)), 4)

    # hole_a is always the clearance hole the fastener passes through. hole_b is
    # a second clearance hole for a floating joint, but a TAPPED hole for a fixed
    # one -- that difference is what lets the exported STEP express which Y14.5
    # formula applies. Without it the two kinds were byte-identical geometry
    # carrying different ground truth, which is unlearnable by construction.
    hole_b = hole if kind == "floating_fastener" else tapped_hole_for(fastener_mm)

    return MateSpec(
        kind=kind,
        nominal_mm=fastener_mm,
        hole_a=dict(hole, position_tol=tol_a),
        hole_b=dict(hole_b, position_tol=tol_b),
        fastener=fastener,
        designation=None,
        position_tol_a=tol_a,
        position_tol_b=tol_b,
        projected_zone_mm=(
            _PLATE_THICKNESS_MM if kind == "fixed_fastener" else None
        ),
    )


def _iso_fit_mate(rng: np.random.Generator, mc_seed: int) -> MateSpec:
    nominal = float(rng.choice(_ISO_FIT_NOMINALS_MM))
    designation = str(rng.choice(SUPPORTED_FITS))
    iso_fit_mate_features(nominal, designation)  # validates the pair
    return MateSpec(
        kind="iso_fit", nominal_mm=nominal, hole_a=None, hole_b=None,
        fastener=None, designation=designation,
        position_tol_a=0.0, position_tol_b=0.0,
        mc_seed=mc_seed, mc_n=_MC_SAMPLES,
    )


def sample_assembly(seed: int, difficulty: int) -> AssemblySpec:
    """Deterministically sample one assembly."""
    if not 1 <= difficulty <= MAX_DIFFICULTY:
        raise ValueError(
            f"difficulty must be 1-{MAX_DIFFICULTY} (spec section 4.1 caps the "
            f"tolerance loop at {MAX_DIFFICULTY} contributors), got {difficulty}"
        )
    rng = np.random.default_rng(seed)
    mates = [
        _iso_fit_mate(rng, _mc_seed_for(seed, i))
        if rng.random() < 0.25
        else _tier1_mate(rng, difficulty)
        for i in range(difficulty)
    ]
    # The plate is sized from the features it has to hold, not hardcoded, so a
    # change to the feature tables can never quietly outgrow it.
    return AssemblySpec(
        seed=seed,
        difficulty=difficulty,
        mates=mates,
        plate_size_mm=plate_size_for_mates(mates),
        plate_thickness_mm=_PLATE_THICKNESS_MM,
    )
