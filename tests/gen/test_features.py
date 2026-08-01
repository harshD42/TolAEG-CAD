import pytest
from tolcad.gen.features import (
    FASTENER_SIZES, SUPPORTED_FITS, clearance_hole_for, iso_fit_mate_features,
)


def test_fastener_sizes_are_the_common_metric_series():
    assert FASTENER_SIZES == (3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0)


@pytest.mark.parametrize("grade, expected_nominal", [
    ("close", 8.4), ("normal", 9.0), ("loose", 10.0),
])
def test_clearance_hole_for_m8(grade, expected_nominal):
    hole = clearance_hole_for(8.0, grade)
    assert hole["nominal"] == pytest.approx(expected_nominal)


def test_clearance_hole_is_always_at_least_the_fastener():
    for f in FASTENER_SIZES:
        for grade in ("close", "normal", "loose"):
            hole = clearance_hole_for(f, grade)
            mmc = hole["nominal"] + hole["lower_dev"]
            assert mmc >= f, f"M{f} {grade}: hole MMC {mmc} below fastener {f}"


def test_unknown_grade_rejected():
    with pytest.raises(ValueError, match="grade"):
        clearance_hole_for(8.0, "snug")


def test_unknown_fastener_size_rejected():
    with pytest.raises(ValueError, match="fastener"):
        clearance_hole_for(7.0, "normal")


def test_supported_fits_are_all_accepted_by_the_checker():
    from tolcad.iso286 import fit_from_designation
    for d in SUPPORTED_FITS:
        hole, shaft = fit_from_designation(20.0, d)
        assert hole.min_size < hole.max_size
        assert shaft.min_size < shaft.max_size


def test_iso_fit_mate_features_returns_hole_then_shaft():
    hole, shaft = iso_fit_mate_features(20.0, "H7/g6")
    assert hole["nominal"] == pytest.approx(20.0)
    # g6 shaft at 20 mm is es -7 um, ei -20 um
    assert shaft["upper_dev"] == pytest.approx(-0.007)
    assert shaft["lower_dev"] == pytest.approx(-0.020)
