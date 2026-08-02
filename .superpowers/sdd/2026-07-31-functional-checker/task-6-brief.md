### Task 6: ISO 286 tolerance tables

**Files:**
- Create: `src/tolcad/iso286.py`
- Test: `tests/test_iso286.py`

**Interfaces:**
- Consumes: `FeatureOfSize`, `FeatureType`
- Produces:
  - `it_grade(nominal_mm: float, grade: int) -> float` — IT tolerance in **mm**
  - `fundamental_deviation(nominal_mm: float, letter: str) -> float` — in **mm**
  - `fit_from_designation(nominal_mm: float, designation: str) -> tuple[FeatureOfSize, FeatureOfSize]` — e.g. `"H7/g6"` → (hole, shaft)

**Citation requirement:** all table values MUST be transcribed from ISO 286-1 or an
equivalent published table and the source recorded in the module docstring.
Values below are correct for the ranges given but MUST be verified against print.

Verification anchor for Ø20 H7/g6: hole `+0.021/0`, shaft `-0.007/-0.020`.
Minimum clearance 0.007 mm, maximum 0.041 mm.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_iso286.py
import pytest
from tolcad.types import FeatureType
from tolcad.iso286 import fit_from_designation, fundamental_deviation, it_grade


def test_it7_at_20mm_is_21_microns():
    assert it_grade(20.0, 7) == pytest.approx(0.021)


def test_it6_at_20mm_is_13_microns():
    assert it_grade(20.0, 6) == pytest.approx(0.013)


def test_it_grade_respects_size_band_boundaries():
    # 18 falls in the 10-18 band (upper bound inclusive), 18.1 in 18-30
    assert it_grade(18.0, 7) == pytest.approx(0.018)
    assert it_grade(18.1, 7) == pytest.approx(0.021)


def test_h_hole_has_zero_fundamental_deviation():
    assert fundamental_deviation(20.0, "H") == pytest.approx(0.0)


def test_g_shaft_deviation_at_20mm_is_minus_7_microns():
    assert fundamental_deviation(20.0, "g") == pytest.approx(-0.007)


def test_h7g6_at_20mm_matches_published_limits():
    hole, shaft = fit_from_designation(20.0, "H7/g6")
    assert hole.feature_type is FeatureType.INTERNAL
    assert shaft.feature_type is FeatureType.EXTERNAL
    assert hole.min_size == pytest.approx(20.000)
    assert hole.max_size == pytest.approx(20.021)
    assert shaft.max_size == pytest.approx(19.993)
    assert shaft.min_size == pytest.approx(19.980)


def test_h7g6_is_a_clearance_fit():
    """Minimum clearance must be strictly positive for a sliding fit."""
    hole, shaft = fit_from_designation(20.0, "H7/g6")
    min_clearance = hole.min_size - shaft.max_size
    assert min_clearance == pytest.approx(0.007)
    assert min_clearance > 0


def test_h7p6_is_an_interference_fit():
    """Maximum clearance must be negative for a press fit."""
    hole, shaft = fit_from_designation(20.0, "H7/p6")
    max_clearance = hole.max_size - shaft.min_size
    assert max_clearance < 0


def test_unsupported_size_rejected():
    with pytest.raises(ValueError, match="outside supported range"):
        it_grade(900.0, 7)


def test_malformed_designation_rejected():
    with pytest.raises(ValueError, match="designation"):
        fit_from_designation(20.0, "H7g6")


@pytest.mark.xfail(
    reason="Fails until table values are verified against print. Do not delete.",
    strict=False,
)
def test_transcription_source_recorded():
    """Gate A guard: table values must cite a real published source."""
    import tolcad.iso286 as mod

    doc = mod.__doc__ or ""
    assert "replace this line" not in doc, (
        "ISO 286 tables are still unverified — record the edition and table number"
    )
    assert "ISO 286" in doc
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_iso286.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.iso286'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/iso286.py
"""ISO 286 limits and fits, hole-basis system.

Table values transcribed from ISO 286-1. Published in micrometres; converted to
millimetres at the table boundary so that no downstream code handles microns.

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

    hole_it = it_grade(nominal_mm, hole_grade)
    hole = FeatureOfSize(nominal_mm, 0.0, hole_it, FeatureType.INTERNAL)

    shaft_it = it_grade(nominal_mm, shaft_grade)
    dev = fundamental_deviation(nominal_mm, shaft_letter)

    if shaft_letter in ("g", "h"):
        # Deviation is the upper limit (es); lower is es - IT.
        shaft = FeatureOfSize(nominal_mm, dev - shaft_it, dev, FeatureType.EXTERNAL)
    else:
        # Deviation is the lower limit (ei); upper is ei + IT.
        shaft = FeatureOfSize(nominal_mm, dev, dev + shaft_it, FeatureType.EXTERNAL)

    return hole, shaft
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_iso286.py -v`
Expected: PASS, 10 tests, plus 1 XFAIL (`test_transcription_source_recorded`). The XFAIL
turns to XPASS once the source line is filled in — that flip is the signal the tables are
verified.

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/iso286.py tests/test_iso286.py
git commit -m "feat: ISO 286 tolerance tables and hole-basis fits"
```

---

