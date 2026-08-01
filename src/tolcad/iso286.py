"""ISO 286 limits and fits, hole-basis system.

Table values transcribed from ISO 286-1. Published in micrometres; converted to
millimetres at the table boundary so that no downstream code handles microns.

Supported shaft letters and grades (fit_from_designation, hole-basis 'H' only):
  - 'g', 'h': es-based (tabulated value is the upper deviation); valid for any
    grade present in _IT_MICRONS (5-8 as currently tabulated).
  - 'p': ei-based (tabulated value is the lower deviation); valid for any grade
    present in _IT_MICRONS (5-8 as currently tabulated).
  - 'k': ei-based, but ISO 286's tabulated 'k' fundamental deviation is only
    valid for IT grades 4-7. Grade 8 and above use a different rule this module
    does not implement, so 'k' is rejected outside grades 4-7 rather than
    silently returning a wrong number.
Any shaft letter present in _DEVIATION_MICRONS but not classified as es-based
or ei-based below is rejected with ValueError rather than silently guessed.

TRANSCRIPTION SOURCE: replace this line with the exact edition and table number the
values below were copied from (e.g. "ISO 286-1:2010, Table 1 and Table 6"). Leaving
this line unedited means the tables are unverified and no derived number may be
published. tests/test_iso286.py::test_transcription_source_recorded enforces this.
"""

from __future__ import annotations

from tolcad.types import FeatureOfSize, FeatureType

# Upper bound (inclusive) of each nominal size band, in mm.
_SIZE_BANDS = [3, 6, 10, 18, 30, 50, 80, 120, 180, 250, 315, 400, 500]

# IT grade tolerance, micrometres, indexed parallel to _SIZE_BANDS.
_IT_MICRONS: dict[int, list[int]] = {
    5: [4, 5, 6, 8, 9, 11, 13, 15, 18, 20, 23, 25, 27],
    6: [6, 8, 9, 11, 13, 16, 19, 22, 25, 29, 32, 36, 40],
    7: [10, 12, 15, 18, 21, 25, 30, 35, 40, 46, 52, 57, 63],
    8: [14, 18, 22, 27, 33, 39, 46, 54, 63, 72, 81, 89, 97],
}

# Fundamental deviation, micrometres. Uppercase = hole (EI), lowercase = shaft (es/ei).
_DEVIATION_MICRONS: dict[str, list[int]] = {
    "H": [0] * 13,
    "g": [-2, -4, -5, -6, -7, -9, -10, -12, -14, -15, -17, -18, -20],
    "h": [0] * 13,
    "k": [0, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4, 5],
    "p": [6, 12, 15, 18, 22, 26, 32, 37, 43, 50, 56, 62, 68],
}

# Explicit classification of how to interpret each tabulated shaft deviation.
# es-based: the tabulated value is the upper deviation (es); lower = es - IT.
# ei-based: the tabulated value is the lower deviation (ei); upper = ei + IT.
# A shaft letter present in _DEVIATION_MICRONS but absent from both sets below
# is a transcription/maintenance gap and must raise rather than fall through.
_ES_BASED_SHAFT_LETTERS: frozenset[str] = frozenset({"g", "h"})
_EI_BASED_SHAFT_LETTERS: frozenset[str] = frozenset({"k", "p"})

# Shaft letters whose tabulated deviation is only valid for a restricted range
# of IT grades. Letters not listed here are treated as valid for any grade
# present in _IT_MICRONS. 'k' deviation per ISO 286 is only tabulated for IT
# grades 4-7; using it with other grades would silently misapply the value.
_SHAFT_LETTER_GRADE_RANGE: dict[str, tuple[int, int]] = {
    "k": (4, 7),
}


def _band_index(nominal_mm: float) -> int:
    if nominal_mm <= 0 or nominal_mm > _SIZE_BANDS[-1]:
        raise ValueError(
            f"nominal size {nominal_mm} outside supported range (0, {_SIZE_BANDS[-1]}]"
        )
    for i, upper in enumerate(_SIZE_BANDS):
        if nominal_mm <= upper:
            return i
    raise AssertionError("unreachable")


def it_grade(nominal_mm: float, grade: int) -> float:
    """IT tolerance width in mm for a nominal size and grade."""
    if grade not in _IT_MICRONS:
        raise ValueError(f"IT grade {grade} not tabulated; have {sorted(_IT_MICRONS)}")
    return _IT_MICRONS[grade][_band_index(nominal_mm)] / 1000.0


def fundamental_deviation(nominal_mm: float, letter: str) -> float:
    """Fundamental deviation in mm. Uppercase for holes, lowercase for shafts."""
    if letter not in _DEVIATION_MICRONS:
        raise ValueError(
            f"deviation letter {letter!r} not tabulated; "
            f"have {sorted(_DEVIATION_MICRONS)}"
        )
    return _DEVIATION_MICRONS[letter][_band_index(nominal_mm)] / 1000.0


def _parse(designation: str) -> tuple[str, int, str, int]:
    if "/" not in designation:
        raise ValueError(
            f"designation {designation!r} must be of the form 'H7/g6'"
        )
    hole_part, shaft_part = designation.split("/", 1)
    try:
        return hole_part[0], int(hole_part[1:]), shaft_part[0], int(shaft_part[1:])
    except (ValueError, IndexError) as exc:
        raise ValueError(f"malformed designation {designation!r}") from exc


def fit_from_designation(
    nominal_mm: float, designation: str
) -> tuple[FeatureOfSize, FeatureOfSize]:
    """Build (hole, shaft) features from an ISO 286 fit like 'H7/g6'.

    Hole-basis only: the hole letter must be 'H', whose lower deviation is zero.
    """
    hole_letter, hole_grade, shaft_letter, shaft_grade = _parse(designation)

    if hole_letter != "H":
        raise ValueError(f"only hole-basis fits supported, got {hole_letter!r}")

    grade_range = _SHAFT_LETTER_GRADE_RANGE.get(shaft_letter)
    if grade_range is not None:
        lo, hi = grade_range
        if not (lo <= shaft_grade <= hi):
            raise ValueError(
                f"shaft letter {shaft_letter!r} deviation is only tabulated for "
                f"IT grades {lo}-{hi}; got grade {shaft_grade} (designation "
                f"{designation!r})"
            )

    hole_it = it_grade(nominal_mm, hole_grade)
    hole = FeatureOfSize(nominal_mm, 0.0, hole_it, FeatureType.INTERNAL)

    shaft_it = it_grade(nominal_mm, shaft_grade)
    dev = fundamental_deviation(nominal_mm, shaft_letter)

    if shaft_letter in _ES_BASED_SHAFT_LETTERS:
        # Deviation is the upper limit (es); lower is es - IT.
        shaft = FeatureOfSize(nominal_mm, dev - shaft_it, dev, FeatureType.EXTERNAL)
    elif shaft_letter in _EI_BASED_SHAFT_LETTERS:
        # Deviation is the lower limit (ei); upper is ei + IT.
        shaft = FeatureOfSize(nominal_mm, dev, dev + shaft_it, FeatureType.EXTERNAL)
    else:
        raise ValueError(
            f"shaft letter {shaft_letter!r} is tabulated in _DEVIATION_MICRONS but "
            "not classified as es-based or ei-based; add it to "
            "_ES_BASED_SHAFT_LETTERS or _EI_BASED_SHAFT_LETTERS before use"
        )

    return hole, shaft
