"""Canonical mating features for generated assemblies. No CAD dependency.

Clearance-hole diameters follow the common metric close/normal/loose series.
Every value below matches the ISO 273 fine/medium/coarse table as reproduced in
general engineering references, but it has NOT been checked against the primary
standard text the way the Y14.5 formulas and ISO 286 deviations were, so no
edition is cited. They are ordinary table values rather than a
standard-restricted formula, and they affect realism, not correctness: the
checker's verdict is exact for whatever diameters it is handed. They are pinned
by tests so a silent edit cannot drift them.
"""

from __future__ import annotations

from tolcad.iso286 import fit_from_designation

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

# Hole tolerance applied to a generated clearance hole: H13-ish, +0.2/-0.0 mm.
_HOLE_UPPER_DEV_MM = 0.2

SUPPORTED_FITS: tuple[str, ...] = ("H7/g6", "H7/h6", "H7/k6", "H7/p6")


def clearance_hole_for(fastener_mm: float, grade: str) -> dict:
    """Return a checker-ready hole dict for a fastener at a clearance grade."""
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
        "upper_dev": _HOLE_UPPER_DEV_MM,
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
