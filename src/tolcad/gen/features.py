"""Canonical mating features for generated assemblies. No CAD dependency.

CLEARANCE HOLES -- ISO 273-1979(E), Table 1. All 21 diameters below (M3-M12 x
fine/medium/coarse) were checked against the primary standard on 2026-08-01 and
match exactly. This module's internal names close/normal/loose correspond to the
standard's fine/medium/coarse.

The standard also states: "The following tolerance fields are given for
information only, for use where it is desirable to specify tolerances: fine
series : H12, medium series : H13, coarse series : H14." We take that option, so
a hole's upper deviation is the IT value at ITS OWN diameter for ITS series --
not a single constant. An earlier version applied a flat +0.2 mm described only
as "H13-ish", which was not any of the three grades and did not vary with size.

TAPPING DRILLS -- ISO 2306-1972, Table 1 (coarse pitch series). All 7 diameters
checked against the primary standard on 2026-08-01 and match exactly. Note M8 ->
6.8 and M12 -> 10.2 are NOT nominal-minus-pitch (that would give 6.75 and 10.25).
ISO 2306 clause 0 says the drill diameter is only APPROXIMATELY D - P, with the
actual sizes selected from the ISO/R 235 preferred drill series. Do not "correct"
them to the subtraction.

All values are pinned by tests so a silent edit cannot drift them.
"""

from __future__ import annotations

from tolcad.iso286 import fit_from_designation, it_grade

FASTENER_SIZES: tuple[float, ...] = (3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0)

# fastener nominal -> (close, normal, loose) clearance hole nominal diameter, mm
_CLEARANCE_HOLE_MM: dict[float, tuple[float, float, float]] = {
    3.0: (3.2, 3.4, 3.6),
    4.0: (4.3, 4.5, 4.8),
    5.0: (5.3, 5.5, 5.8),
    6.0: (6.4, 6.6, 7.0),
    8.0: (8.4, 9.0, 10.0),
    10.0: (10.5, 11.0, 12.0),
    12.0: (13.0, 13.5, 14.5),
}
_GRADE_INDEX = {"close": 0, "normal": 1, "loose": 2}

# ISO 273-1979 Table 1, tolerance-fields note. Grade per clearance-hole series.
SERIES_TOLERANCE_GRADE: dict[str, int] = {"close": 12, "normal": 13, "loose": 14}

# Tapped holes: ISO 2306 gives drill DIAMETERS, not tolerances, and ISO 273
# covers clearance holes only, so no standard here fixes a grade for the tapped
# feature. A flat band is used deliberately rather than inventing a citation.
# This is provably inert: y14_5's B-4 formula never reads hole_b's size in the
# fixed-fastener case (its docstring is explicit that hole_b is not a clearance
# hole there), so no verdict in the corpus depends on this number.
_TAPPED_HOLE_UPPER_DEV_MM = 0.2

# Hole-basis fits the generator samples. One clearance (g6), one transition
# (k6), one interference (p6).
#
# H7/h6 WAS HERE AND WAS DELIBERATELY REMOVED. It is line-to-line: an H hole's
# lower deviation is zero and an h shaft's upper deviation is zero, so hole
# minimum and shaft maximum are both exactly the nominal and the exact
# worst-case clearance is 0. tolcad.montecarlo scores `assembles` as
# `yield >= 1.0` against a strict `clearance > 0`, so the label came down to
# whether any of 100,000 samples landed exactly on the boundary: 85 True /
# 23 False across the corpus, margin only ever 1.0 or 0.99999. That is
# sampling noise wearing a ground-truth label, and it would have surfaced as
# irreducible, unexplainable model-vs-checker disagreement. Removed before
# pre-registration rather than after.
SUPPORTED_FITS: tuple[str, ...] = ("H7/g6", "H7/k6", "H7/p6")

# Tapping drill diameter for a coarse-pitch metric thread, mm. A screw threading
# into one of these does NOT pass through it -- that is exactly what makes a
# fixed-fastener joint geometrically distinct from a floating one, where the
# fastener clears both parts.
#
# ISO 2306-1972, Table 1 (coarse pitch series): all 7 diameters below were
# checked against the primary standard on 2026-08-01 and match exactly,
# including M8 -> 6.8 and M12 -> 10.2, which come from the ISO/R 235 preferred
# drill series rather than nominal-minus-pitch (which would give 6.75 / 10.25).
# They affect realism, not correctness: the checker's B-4 verdict never reads
# hole_b's size in the fixed case.
TAPPING_DRILL_MM: dict[float, float] = {
    3.0: 2.5,
    4.0: 3.3,
    5.0: 4.2,
    6.0: 5.0,
    8.0: 6.8,
    10.0: 8.5,
    12.0: 10.2,
}


def clearance_hole_for(fastener_mm: float, grade: str) -> dict:
    """Return a checker-ready hole dict for a fastener at a clearance grade.

    The upper deviation is the ISO 286 IT value for this series' grade AT THE
    HOLE'S OWN DIAMETER, per the ISO 273 tolerance-fields note. Lower deviation
    is zero: these are H holes, so MMC equals the nominal diameter.
    """
    if fastener_mm not in _CLEARANCE_HOLE_MM:
        raise ValueError(
            f"fastener size {fastener_mm} not tabulated; have {FASTENER_SIZES}"
        )
    if grade not in _GRADE_INDEX:
        raise ValueError(f"grade must be one of {sorted(_GRADE_INDEX)}, got {grade!r}")
    nominal = _CLEARANCE_HOLE_MM[fastener_mm][_GRADE_INDEX[grade]]
    return {
        "nominal": nominal,
        "lower_dev": 0.0,
        "upper_dev": it_grade(nominal, SERIES_TOLERANCE_GRADE[grade]),
        "position_tol": 0.0,
    }


def tapped_hole_for(fastener_mm: float) -> dict:
    """Return a checker-ready hole dict for the tapped feature of a fixed joint.

    The fastener threads into this hole rather than passing through it, so the
    diameter is deliberately BELOW the fastener's. y14_5.fastener_assembles does
    not check hole_b's size in the fixed case -- its docstring is explicit that
    hole_b is not a clearance hole there and its MMC never enters the B-4
    formula -- so a sub-fastener diameter here is correct, not a violation.
    """
    if fastener_mm not in TAPPING_DRILL_MM:
        raise ValueError(
            f"fastener size {fastener_mm} not tabulated; have {FASTENER_SIZES}"
        )
    return {
        "nominal": TAPPING_DRILL_MM[fastener_mm],
        "lower_dev": 0.0,
        "upper_dev": _TAPPED_HOLE_UPPER_DEV_MM,
        "position_tol": 0.0,
    }


def iso_fit_mate_features(nominal_mm: float, designation: str) -> tuple[dict, dict]:
    """Return (hole, shaft) dicts for an ISO 286 fit, in checker dict form."""
    if designation not in SUPPORTED_FITS:
        raise ValueError(
            f"fit {designation!r} not supported; have {SUPPORTED_FITS}"
        )
    hole, shaft = fit_from_designation(nominal_mm, designation)
    return (
        {"nominal": hole.nominal, "lower_dev": hole.lower_dev,
         "upper_dev": hole.upper_dev, "position_tol": 0.0},
        {"nominal": shaft.nominal, "lower_dev": shaft.lower_dev,
         "upper_dev": shaft.upper_dev},
    )
