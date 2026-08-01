"""Layout arithmetic. No CAD needed -- layout.py is part of the CAD-free half."""

import pytest

from tolcad.gen.features import FASTENER_SIZES, clearance_hole_for
from tolcad.gen.layout import (
    _EDGE_MARGIN_MM, _MIN_WALL_MM, feature_pitch_mm, feature_positions_mm,
    feature_radii_mm, minimum_plate_size_mm,
)
from tolcad.gen.sampler import _TOL_FRACTION_RANGE, MAX_DIFFICULTY, sample_assembly

_LARGEST_RADIUS_MM = max(
    clearance_hole_for(f, "loose")["nominal"] for f in FASTENER_SIZES
) / 2.0

# Cruder second floors, spelled as numbers so zeroing a production constant is
# caught even if the derivation above is edited. Recompute these whenever the
# clearance-hole table, its tolerance grades, or the difficulty ladder changes.
#
# ROUNDED UP, DELIBERATELY. The derived requirements are 3.78 and 1.89; these
# literals are 3.8 and 1.9 so they sit strictly ABOVE them. That is the whole
# point of a second floor -- it must hold even if the derivation is mis-derived,
# which it cannot do if it merely equals the derivation. An earlier pass set them
# to exactly 3.78 / 1.89 and the edge literal then landed a ulp BELOW its derived
# requirement (1.89 < 1.8900000000000001), passing only on the 1e-9 epsilon.
_LITERAL_WALL_FLOOR_MM = 3.8
_LITERAL_EDGE_FLOOR_MM = 1.9


def test_largest_clearance_hole_needs_more_than_the_old_hardcoded_pitch():
    """The premise of I3: 12 mm pitch cannot hold two Ø14.5 features."""
    assert 2.0 * _LARGEST_RADIUS_MM > 12.0


def test_pitch_leaves_a_wall_between_the_widest_neighbours():
    radii = [_LARGEST_RADIUS_MM, _LARGEST_RADIUS_MM, 1.6]
    pitch = feature_pitch_mm(radii)
    for a, b in zip(radii, radii[1:]):
        assert pitch - (a + b) >= _MIN_WALL_MM - 1e-9


def test_plate_leaves_an_edge_margin_around_the_outermost_feature():
    radii = [_LARGEST_RADIUS_MM] * MAX_DIFFICULTY
    size = minimum_plate_size_mm(radii)
    positions = feature_positions_mm(radii)
    for x, r in zip(positions, radii):
        assert size / 2.0 - (abs(x) + r) >= _EDGE_MARGIN_MM - 1e-9


def test_positions_are_symmetric_about_the_plate_centre():
    positions = feature_positions_mm([3.0, 4.0, 5.0])
    assert positions[0] == pytest.approx(-positions[-1])
    assert sum(positions) == pytest.approx(0.0)


def test_radii_track_the_larger_of_the_two_mating_holes():
    class _Mate:
        kind = "floating_fastener"
        hole_a = {"nominal": 6.6}
        hole_b = {"nominal": 10.0}

    assert feature_radii_mm([_Mate()]) == [5.0]


def test_sampler_records_a_plate_big_enough_for_its_own_features():
    """The sidecar's plate_size_mm must never contradict the geometry."""
    for seed in range(50):
        for difficulty in range(1, MAX_DIFFICULTY + 1):
            spec = sample_assembly(seed, difficulty)
            needed = minimum_plate_size_mm(feature_radii_mm(spec.mates))
            assert spec.plate_size_mm >= needed - 1e-9, (
                f"seed {seed} d{difficulty}: plate {spec.plate_size_mm} < {needed}"
            )


def test_plate_size_is_serialised_in_the_sidecar():
    spec = sample_assembly(0, 4)
    assert '"plate_size_mm"' in spec.to_json()
    assert '"plate_thickness_mm"' in spec.to_json()


def _worst_case_radial_excursion_mm() -> float:
    """How far one feature's edge can reach past nominal, from the tables.

    Re-derived at test time from the two tables the number actually depends on:

      * the clearance-hole table (via the public clearance_hole_for), which
        fixes the largest allowable position tolerance -- hole MMC minus
        fastener, exactly as sampler._tier1_mate computes it -- and the largest
        hole growth, upper_dev on the diameter;
      * sampler._TOL_FRACTION_RANGE, whose largest hi is the most of that
        allowable the difficulty ladder ever applies.

    The allowable is halved for a fixed fastener, so the floating case above is
    the worst one. Position tolerance is diametral, hence the /2 to get a
    radial axis offset.
    """
    largest_allowable = 0.0
    largest_radius_growth = 0.0
    for fastener_mm in FASTENER_SIZES:
        for grade in ("close", "normal", "loose"):
            hole = clearance_hole_for(fastener_mm, grade)
            mmc = hole["nominal"] + hole["lower_dev"]
            largest_allowable = max(largest_allowable, mmc - fastener_mm)
            largest_radius_growth = max(largest_radius_growth, hole["upper_dev"] / 2.0)
    largest_fraction = max(hi for _lo, hi in _TOL_FRACTION_RANGE.values())
    return largest_allowable * largest_fraction / 2.0 + largest_radius_growth


def test_the_margin_constants_still_cover_the_tables_they_came_from():
    """Ties the floors to the ladder and the clearance table they derive from.

    The literal floors below are a second, cruder line: they are fixed numbers
    a human checked once, so they go stale silently. Raise
    _TOL_FRACTION_RANGE[4] hi from 1.34 to 1.7 and two neighbours consume
    2 * (2.5 * 1.7 / 2) + 0.2 = 4.45 mm against a 4.0 mm wall -- a degenerate
    ligament that every literal-only test in the repo waves through. This one
    fires.

    STILL NOT SELF-REFERENTIAL: the requirement is computed from features.py
    and sampler.py and compared against layout.py's constants. It is a
    cross-module comparison, which is exactly what the self-referential
    pitch/edge assertions above are not.
    """
    required_wall = 2.0 * _worst_case_radial_excursion_mm()
    required_edge = _worst_case_radial_excursion_mm()

    assert _MIN_WALL_MM >= required_wall - 1e-9, (
        f"_MIN_WALL_MM {_MIN_WALL_MM} is below the {required_wall} mm the "
        f"clearance table and the difficulty ladder now demand between two "
        f"features leaning toward each other"
    )
    assert _EDGE_MARGIN_MM >= required_edge - 1e-9, (
        f"_EDGE_MARGIN_MM {_EDGE_MARGIN_MM} is below the {required_edge} mm "
        f"the clearance table and the difficulty ladder now demand at an edge"
    )


def test_the_margin_constants_are_actually_large_enough():
    """The other margin tests compare against these constants, so they cannot
    fail if the constants go to zero. This one spells the numbers out.

    A zero wall makes adjacent holes exactly tangent. The containment test in
    test_build.py cannot catch that either, because tangency has zero
    intersection volume -- it would sail through as a degenerate B-rep with no
    ligament between neighbouring features.

    THE ARITHMETIC, reconciled with layout.py. The widest feature that carries
    a position tolerance is Ø14.5 (M12 loose); its allowable is 14.5 - 12.0 =
    2.5 mm diametral, the ladder applies at most 1.34x of it, so the applied
    tolerance is 3.35 mm diametral and an axis sits at most 3.35 / 2 = 1.675 mm
    off nominal. Since clearance holes moved to their ISO 273 series grades,
    that same hole carries IT14 (>10-18 mm band, 0.43 mm diametral), so a
    radius can grow another 0.215 mm. Two neighbours leaning together
    therefore consume 3.78 mm; one leaning at an edge consumes 1.890 mm.

    _LITERAL_WALL_FLOOR_MM / _LITERAL_EDGE_FLOOR_MM (3.8 / 1.9) are that same
    arithmetic rounded UP to fixed numbers, so they are a conservative floor
    that holds even if the derivation is mis-derived -- unlike the 3.7 / 1.85
    figures they replace, which were rounded up from the pre-ISO-273 axis
    offset and had quietly drifted below the current requirement without either
    layout test noticing. See test_the_literal_floors_are_not_below_the_derived_ones
    for why that gap matters.

    Ø25 iso_fit bores are wider than Ø14.5 and do not change any of this: they
    carry position_tol 0.0 and an IT7-class band (~0.01 mm on the radius), so
    they are never the binding case for a margin sized against position error.
    """
    assert _MIN_WALL_MM >= _LITERAL_WALL_FLOOR_MM, (
        f"_MIN_WALL_MM {_MIN_WALL_MM} leaves no ligament between two features "
        f"leaning toward each other"
    )
    assert _EDGE_MARGIN_MM >= _LITERAL_EDGE_FLOOR_MM, (
        f"_EDGE_MARGIN_MM {_EDGE_MARGIN_MM} lets a feature leaning at the edge "
        f"break out of the plate"
    )


def test_the_literal_floors_are_not_below_the_derived_ones():
    """The literals are a second, cruder floor -- they must not undercut the real one.

    When clearance holes moved from a flat +0.2 to their ISO 273 series grades,
    the worst-case growth at M12 coarse went from 0.100 to 0.215 mm and the
    required wall rose from 3.55 to 3.78. The literal still said 3.7. NEITHER
    layout test failed: the derived floor recomputed correctly and passed, and
    the literal passed too -- it had simply stopped being a floor, and would
    have accepted a _MIN_WALL_MM of 3.75 that is genuinely too small.

    BOTH literals are checked here, not just the wall one. An earlier version of
    this test guarded the wall literal alone and left the edge literal compared
    only against the production constant -- the identical pattern that let the
    wall literal go stale. The edge literal was in fact already a ulp below its
    derived requirement (1.89 vs 1.8900000000000001) when that gap was found.

    This test is what notices next time, for either floor.
    """
    required_wall = 2.0 * _worst_case_radial_excursion_mm()
    required_edge = _worst_case_radial_excursion_mm()

    assert _LITERAL_WALL_FLOOR_MM >= required_wall - 1e-9, (
        f"the literal wall floor {_LITERAL_WALL_FLOOR_MM} is below the derived "
        f"requirement {required_wall:.4f}; recompute it from the tables"
    )
    assert _LITERAL_EDGE_FLOOR_MM >= required_edge - 1e-9, (
        f"the literal edge floor {_LITERAL_EDGE_FLOOR_MM} is below the derived "
        f"requirement {required_edge:.4f}; recompute it from the tables"
    )
