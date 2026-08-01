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


def test_transcription_source_recorded():
    """Gate A guard: table values must cite a real published source.

    Was an xfail while the placeholder stood. The tables were verified against
    the primary ISO 286-1 Tables 1, 4 and 5 on 2026-08-01 (all 117 values, zero
    discrepancies), so this is now a plain regression test: it fails if anyone
    reintroduces the placeholder or strips the citation.
    """
    import tolcad.iso286 as mod

    doc = mod.__doc__ or ""
    assert "replace this line" not in doc, (
        "ISO 286 tables are unverified again — record the edition and table number"
    )
    assert "ISO 286-1" in doc
    for table in ("Table 1", "Table 4", "Table 5"):
        assert table in doc, f"citation lost its reference to {table}"


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


def test_it12_to_it14_are_tabulated():
    """ISO 273 assigns H12/H13/H14 to its three clearance-hole series, so the
    generator cannot cite the standard without these grades."""
    for grade in (12, 13, 14):
        assert it_grade(20.0, grade) > 0.0


@pytest.mark.parametrize("nominal, grade, expected_mm", [
    # ISO 286-1:2010 Table 1. These are published in MILLIMETRES, not
    # micrometres -- the table has a separate span label for IT12-IT18.
    (4.0, 12, 0.12), (4.0, 13, 0.18), (4.0, 14, 0.30),
    (8.0, 12, 0.15), (8.0, 13, 0.22), (8.0, 14, 0.36),
    (14.0, 12, 0.18), (14.0, 13, 0.27), (14.0, 14, 0.43),
])
def test_it12_to_it14_match_iso286_table_1(nominal, grade, expected_mm):
    assert it_grade(nominal, grade) == pytest.approx(expected_mm)


def test_the_new_rows_did_not_land_a_thousand_times_too_small():
    """ISO 286-1 publishes IT12-IT18 in mm while _IT_MICRONS stores um.

    Pasting 0.43 straight into a micrometre table yields 0.00043 mm, which is
    smaller than IT5 and would sail through every other test in this file.
    IT14 must exceed IT8 at the same size, always.
    """
    for nominal in (4.0, 8.0, 14.0, 100.0, 400.0):
        assert it_grade(nominal, 12) > it_grade(nominal, 8)
        assert it_grade(nominal, 13) > it_grade(nominal, 12)
        assert it_grade(nominal, 14) > it_grade(nominal, 13)


def test_new_rows_span_every_size_band():
    """A short row would silently misalign against _SIZE_BANDS."""
    from tolcad.iso286 import _IT_MICRONS, _SIZE_BANDS
    for grade in (12, 13, 14):
        assert len(_IT_MICRONS[grade]) == len(_SIZE_BANDS)


def test_existing_grades_are_untouched():
    """117 values were verified against primary tables; this plan only appends."""
    assert it_grade(4.0, 5) == pytest.approx(0.005)
    assert it_grade(4.0, 8) == pytest.approx(0.018)
    assert it_grade(14.0, 7) == pytest.approx(0.018)


# --- All 39 IT12-IT14 cells, pinned individually (F-2 fix round) --------------
#
# The controller hand-verified all 39 cells (3 grades x 13 bands) against the
# primary-source scan once, as a one-off shell run. That verification was never
# encoded in the suite: only 3 of 13 bands had a per-value check, ordering
# covered 5 of 13, and the length check catches truncation but not a
# same-length transposition of two adjacent bands within a row. Eight of
# thirteen bands had zero correctness coverage for grades 12-14. This pins all
# 39 values directly, indexed parallel to _SIZE_BANDS, so a future edit that
# corrupts any single cell -- including a transposition -- fails here.

_SIZE_BAND_PROBES_MM = [2, 4, 8, 14, 25, 40, 65, 100, 150, 200, 300, 350, 450]

# ISO 286-1:2010 Table 1, published in MILLIMETRES for IT12-IT18. Indexed
# parallel to _SIZE_BANDS / _SIZE_BAND_PROBES_MM.
_IT12_TABLE_MM = [0.10, 0.12, 0.15, 0.18, 0.21, 0.25, 0.30, 0.35, 0.40, 0.46, 0.52, 0.57, 0.63]
_IT13_TABLE_MM = [0.14, 0.18, 0.22, 0.27, 0.33, 0.39, 0.46, 0.54, 0.63, 0.72, 0.81, 0.89, 0.97]
_IT14_TABLE_MM = [0.25, 0.30, 0.36, 0.43, 0.52, 0.62, 0.74, 0.87, 1.00, 1.15, 1.30, 1.40, 1.55]


@pytest.mark.parametrize("band_index, probe_mm", list(enumerate(_SIZE_BAND_PROBES_MM)))
def test_all_39_it12_to_it14_cells_match_iso286_table_1(band_index, probe_mm):
    for grade, table in ((12, _IT12_TABLE_MM), (13, _IT13_TABLE_MM), (14, _IT14_TABLE_MM)):
        expected_mm = table[band_index]
        assert it_grade(probe_mm, grade) == pytest.approx(expected_mm), (
            f"IT{grade} at size band index {band_index} "
            f"(_SIZE_BANDS upper bound, probe {probe_mm} mm): "
            f"expected {expected_mm} mm, got {it_grade(probe_mm, grade)} mm"
        )


# --- The accepted designation set, pinned in both directions (I-2 fix round) ---
#
# Adding IT12-IT14 for ISO 273 also widened fit_from_designation's accepted
# inputs: 'g', 'h' and 'p' carry no grade restriction, so they are valid for any
# grade present in _IT_MICRONS, and H12/g12, H13/h13 and H14/p14 went from
# raising ValueError to returning a fit. Nothing pinned that either way, so the
# public surface of a checker-core function moved as an unannounced side effect.
#
# The widening is CORRECT per ISO 286-1 -- Tables 4 and 5 give g, h and p for all
# standard tolerance grades -- so acceptance is what gets pinned here, alongside
# the two rejections that must survive it.


@pytest.mark.parametrize("designation", ["H12/g12", "H13/h13", "H14/p14"])
def test_iso273_grades_are_accepted_for_unrestricted_shaft_letters(designation):
    """g, h and p are valid at every standard grade, hence at IT12-IT14 too."""
    hole, shaft = fit_from_designation(20.0, designation)
    assert hole.min_size < hole.max_size
    assert shaft.min_size < shaft.max_size
    assert hole.nominal == pytest.approx(20.0)


def test_an_untabulated_grade_is_still_rejected():
    """Widening to 12-14 must not become 'accept anything'.

    IT9 is a real ISO 286 grade this module does not tabulate. Returning a value
    for it would mean guessing, so it must raise -- naming the grades we do have.
    """
    with pytest.raises(ValueError, match="IT grade 9 not tabulated"):
        fit_from_designation(20.0, "H9/g9")


def test_k_is_still_restricted_to_it4_through_it7_after_the_widening():
    """'k' has a grade range in ISO 286 Table 5 and IT12-IT14 do not enter it.

    Table 5 splits 'k' into an "IT4 to IT7" column and an "up to IT3 and above
    IT7" column (ei = 0), and only the first is transcribed here. So unlike g/h/p,
    'k' must NOT have picked up the new grades.
    """
    for designation in ("H12/k12", "H13/k13", "H14/k14"):
        with pytest.raises(ValueError, match="only tabulated for"):
            fit_from_designation(20.0, designation)
