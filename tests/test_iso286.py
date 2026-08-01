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
