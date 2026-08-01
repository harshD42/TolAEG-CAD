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
)
from tolcad.gen.spec import AssemblySpec, MateSpec

MAX_DIFFICULTY = 4

# Fraction of the allowable position tolerance actually applied, by difficulty.
# At difficulty 4 the range straddles 1.0, so some joints fail.
_TOL_FRACTION_RANGE = {
    1: (0.20, 0.50),
    2: (0.40, 0.80),
    3: (0.60, 1.00),
    4: (0.80, 1.30),
}

_TIER1_KINDS = ("floating_fastener", "fixed_fastener")


def _tier1_mate(rng: np.random.Generator, difficulty: int) -> MateSpec:
    fastener_mm = float(rng.choice(FASTENER_SIZES))
    grade = str(rng.choice(("close", "normal", "loose")))
    kind = str(rng.choice(_TIER1_KINDS))

    hole = clearance_hole_for(fastener_mm, grade)
    fastener = {"nominal": fastener_mm, "lower_dev": -0.1, "upper_dev": 0.0}

    # Allowable per Y14.5: floating T = H - F; fixed splits H - F across both parts.
    hole_mmc = hole["nominal"] + hole["lower_dev"]
    allowable = hole_mmc - fastener_mm
    if kind == "fixed_fastener":
        allowable /= 2.0

    lo, hi = _TOL_FRACTION_RANGE[difficulty]
    tol_a = round(allowable * float(rng.uniform(lo, hi)), 4)
    tol_b = round(allowable * float(rng.uniform(lo, hi)), 4)

    return MateSpec(
        kind=kind,
        nominal_mm=fastener_mm,
        hole_a=dict(hole, position_tol=tol_a),
        hole_b=dict(hole, position_tol=tol_b),
        fastener=fastener,
        designation=None,
        position_tol_a=tol_a,
        position_tol_b=tol_b,
    )


def _iso_fit_mate(rng: np.random.Generator) -> MateSpec:
    nominal = float(rng.choice((10.0, 12.0, 16.0, 20.0, 25.0)))
    designation = str(rng.choice(SUPPORTED_FITS))
    iso_fit_mate_features(nominal, designation)  # validates the pair
    return MateSpec(
        kind="iso_fit", nominal_mm=nominal, hole_a=None, hole_b=None,
        fastener=None, designation=designation,
        position_tol_a=0.0, position_tol_b=0.0,
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
        _iso_fit_mate(rng) if rng.random() < 0.25 else _tier1_mate(rng, difficulty)
        for _ in range(difficulty)
    ]
    return AssemblySpec(seed=seed, difficulty=difficulty, mates=mates)
