"""Layout arithmetic. No CAD needed -- layout.py is part of the CAD-free half."""

import pytest

from tolcad.gen.features import FASTENER_SIZES, clearance_hole_for
from tolcad.gen.layout import (
    _EDGE_MARGIN_MM, _MIN_WALL_MM, feature_pitch_mm, feature_positions_mm,
    feature_radii_mm, minimum_plate_size_mm,
)
from tolcad.gen.sampler import MAX_DIFFICULTY, sample_assembly

_LARGEST_RADIUS_MM = max(
    clearance_hole_for(f, "loose")["nominal"] for f in FASTENER_SIZES
) / 2.0


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
