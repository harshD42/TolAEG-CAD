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


def test_h7h6_at_20mm_matches_expected_limits():
    """Regression: 'h' is es-based (tabulated deviation is always 0)."""
    hole, shaft = fit_from_designation(20.0, "H7/h6")
    assert hole.min_size == pytest.approx(20.000)
    assert hole.max_size == pytest.approx(20.021)
    assert shaft.max_size == pytest.approx(20.000)
    assert shaft.min_size == pytest.approx(19.987)


def test_h7k6_at_20mm_matches_expected_limits():
    """Regression: 'k' is ei-based and grade 6 is within the supported 4-7 range."""
    hole, shaft = fit_from_designation(20.0, "H7/k6")
    assert hole.min_size == pytest.approx(20.000)
    assert hole.max_size == pytest.approx(20.021)
    assert shaft.min_size == pytest.approx(20.002)
    assert shaft.max_size == pytest.approx(20.015)


def test_unclassified_shaft_letter_rejected(monkeypatch):
    """FINDING 1: a shaft letter tabulated in _DEVIATION_MICRONS but not
    classified as es-based or ei-based must raise, not silently fall into
    either interpretation via a catch-all else branch."""
    import tolcad.iso286 as mod

    monkeypatch.setitem(mod._DEVIATION_MICRONS, "z", [0] * 13)
    with pytest.raises(ValueError, match="not classified"):
        fit_from_designation(20.0, "H7/z6")


def test_h7k8_rejects_unsupported_k_grade():
    """FINDING 2: 'k' fundamental deviation is only tabulated for IT grades
    4-7; grade 8 (though present in _IT_MICRONS) must be rejected rather than
    silently combined with the grade-6/7-only 'k' deviation value."""
    with pytest.raises(ValueError, match="k"):
        fit_from_designation(20.0, "H7/k8")


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


# --- Cross-verification against published secondary sources (2026-08-01) -------
#
# These pin the exact values confirmed against independent published reproductions
# of ISO 286. They do NOT discharge test_transcription_source_recorded, which still
# demands a primary-source citation. Their job is to make the cross-verification
# executable, so a future edit that silently changes a table value fails here.
#
# Note the 10-18 band: nothing else in this suite covered it, and a scraped source
# initially reported it wrongly (row-misaligned onto the 6-10 band). It is pinned
# precisely because it was the one place a transcription slip could have hidden.


@pytest.mark.parametrize(
    "nominal_mm, grade, expected_microns",
    [
        (12.0, 6, 11),  # 10-18 band, IT6
        (20.0, 6, 13),  # 18-30 band, IT6
        (20.0, 7, 21),  # 18-30 band, IT7
    ],
)
def test_it_grade_matches_published_value(nominal_mm, grade, expected_microns):
    assert it_grade(nominal_mm, grade) == pytest.approx(expected_microns / 1000.0)


@pytest.mark.parametrize(
    "designation, es_microns, ei_microns",
    [
        ("H7/g6", -7, -20),
        ("H7/h6", 0, -13),
        ("H7/k6", 15, 2),
        ("H7/p6", 35, 22),
    ],
)
def test_shaft_deviations_at_20mm_match_published_table(
    designation, es_microns, ei_microns
):
    """RoyMech's ISO 286-2 shaft table, 18-30 mm row. es = upper, ei = lower."""
    _, shaft = fit_from_designation(20.0, designation)
    assert (shaft.max_size - 20.0) == pytest.approx(es_microns / 1000.0, abs=1e-9)
    assert (shaft.min_size - 20.0) == pytest.approx(ei_microns / 1000.0, abs=1e-9)


def test_it6_band_boundary_is_not_off_by_one():
    """Guards the misalignment that a scraped source actually exhibited.

    IT6 differs across the 6-10 / 10-18 / 18-30 boundaries, so an off-by-one in
    _SIZE_BANDS or _IT_MICRONS would show up here even though a 20 mm-only test
    would still pass.
    """
    assert it_grade(10.0, 6) == pytest.approx(0.009)  # 6-10 band, upper bound
    assert it_grade(10.1, 6) == pytest.approx(0.011)  # 10-18 band
    assert it_grade(18.0, 6) == pytest.approx(0.011)  # 10-18 band, upper bound
    assert it_grade(18.1, 6) == pytest.approx(0.013)  # 18-30 band
