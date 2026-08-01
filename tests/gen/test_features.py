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


def test_no_supported_fit_is_line_to_line():
    """A fit whose worst-case clearance is exactly zero has a coin-toss label.

    H7/h6 was in this set and came out 85 True / 23 False across the corpus,
    decided by whether any of 100k Monte Carlo draws landed on the boundary.
    Its margin was only ever 1.0 or 0.99999 -- one clearance failure in 100k.
    """
    from tolcad.iso286 import fit_from_designation

    for designation in SUPPORTED_FITS:
        hole, shaft = fit_from_designation(20.0, designation)
        assert hole.min_size != shaft.max_size, (
            f"{designation} is line-to-line at 20 mm (hole min == shaft max == "
            f"{hole.min_size}); its verdict is decided by sampling noise"
        )


def test_supported_fits_still_contain_both_verdict_classes():
    """Dropping a fit must not leave the ISO set all-passing or all-failing."""
    from tolcad.checker import check

    verdicts = {
        d: check({"type": "iso_fit", "nominal": 20.0, "designation": d,
                  "seed": 12345, "n": 100_000}).assembles
        for d in SUPPORTED_FITS
    }
    assert any(verdicts.values()), f"no clearance fit left: {verdicts}"
    assert not all(verdicts.values()), f"no interference fit left: {verdicts}"


def test_iso_fit_verdict_is_fixed_by_the_shaft_letter_at_every_size():
    """DOCUMENTS a structural property; this is a disclosure, not a bug.

    assembles is `yield >= 1.0`, i.e. zero interference anywhere in the
    tolerance range, which for a hole-basis fit means hole_min > shaft_max.
    Since hole_min == nominal and shaft_max == nominal + es, the verdict is
    True exactly when es <= 0 -- the definition of a clearance-class shaft
    letter. It therefore CANNOT vary with diameter, and no amount of nominal
    variation will make these labels harder to guess from the designation.
    Tier 2's contribution to the benchmark is the YIELD, not this boolean.
    """
    from tolcad.checker import check

    nominals = (6.0, 10.0, 20.0, 50.0, 120.0)
    for designation in SUPPORTED_FITS:
        seen = {
            check({"type": "iso_fit", "nominal": n, "designation": designation,
                   "seed": 999, "n": 100_000}).assembles
            for n in nominals
        }
        assert len(seen) == 1, (
            f"{designation} changed verdict across {nominals}: {seen}. If this "
            f"ever fails the structural argument above is wrong -- re-derive it "
            f"before relying on the disclosure."
        )


def test_iso_fit_yield_does_vary_with_size():
    """The continuous signal Tier 2 actually contributes, unlike the boolean.

    Guards against the yield collapsing to a constant, which would leave
    Tier 2 contributing nothing at all once the boolean is set aside.
    """
    from tolcad.checker import check

    yields = {
        n: check({"type": "iso_fit", "nominal": n, "designation": "H7/k6",
                  "seed": 999, "n": 100_000}).margin
        for n in (6.0, 20.0, 120.0)
    }
    assert len(set(yields.values())) > 1, (
        f"H7/k6 yield is constant across diameters: {yields}"
    )


def test_tapping_drill_is_tabulated_for_every_fastener_size():
    from tolcad.gen.features import TAPPING_DRILL_MM
    assert set(TAPPING_DRILL_MM) == set(FASTENER_SIZES)


@pytest.mark.parametrize("fastener_mm, expected", [
    (3.0, 2.5), (4.0, 3.3), (5.0, 4.2), (6.0, 5.0),
    (8.0, 6.8), (10.0, 8.5), (12.0, 10.2),
])
def test_tapped_hole_matches_the_coarse_pitch_series(fastener_mm, expected):
    from tolcad.gen.features import tapped_hole_for
    assert tapped_hole_for(fastener_mm)["nominal"] == pytest.approx(expected)


def test_tapped_hole_is_always_smaller_than_its_fastener():
    """This is what makes a fixed joint geometrically distinguishable.

    A tapped hole the fastener could pass through would be a clearance hole,
    and the two fastener kinds would look identical again.
    """
    from tolcad.gen.features import tapped_hole_for
    for f in FASTENER_SIZES:
        hole = tapped_hole_for(f)
        assert hole["nominal"] + hole["upper_dev"] < f, (
            f"M{f} tapped hole is not smaller than the fastener at LMC"
        )


def test_unknown_fastener_size_rejected_by_tapped_hole():
    from tolcad.gen.features import tapped_hole_for
    with pytest.raises(ValueError, match="fastener"):
        tapped_hole_for(7.0)
