import math

import pytest

cq = pytest.importorskip("cadquery", reason="requires the [gen] extra")

from tolcad.gen.build import build_assembly
from tolcad.gen.layout import (
    feature_positions_mm, feature_radii_mm, minimum_plate_size_mm,
)
from tolcad.gen.sampler import sample_assembly
from tolcad.gen.spec import AssemblySpec

# Positions are compared to ~1 nm. The build rounds layout coordinates to 4 dp
# and OCCT reproduces them to floating-point noise, so 6 dp is tight enough to
# catch a real placement error and loose enough not to chase representation.
_POSITION_DP = 6


def _parts(spec) -> dict:
    return {child.name: child.obj.val() for child in build_assembly(spec).children}


def _cylinder_centre_xs(solid) -> list[float]:
    """x coordinate of every cylindrical face, i.e. of every drilled feature.

    A full through hole or flat-bottomed bore contributes exactly one
    cylindrical face whose Center() sits on its axis. A feature that ran off
    the plate edge becomes a partial cylinder whose centroid is displaced, so
    this also catches overhang.
    """
    return sorted(
        round(f.Center().x, _POSITION_DP)
        for f in solid.Faces()
        if f.geomType() == "CYLINDER"
    )


def _expected_positions(spec) -> tuple[list[float], list[float]]:
    """(part_a xs, part_b xs) the spec says features should occupy."""
    xs = feature_positions_mm(feature_radii_mm(spec.mates))
    a = [round(x, _POSITION_DP)
         for x, m in zip(xs, spec.mates) if m.kind != "iso_fit"]
    b = [round(x, _POSITION_DP) for x in xs]
    return sorted(a), sorted(b)


def _expected_removed_volume(spec) -> tuple[float, float]:
    """(part_a, part_b) material an unclipped, non-overlapping drill would remove."""
    t = spec.plate_thickness_mm
    removed_a = removed_b = 0.0
    for mate in spec.mates:
        if mate.kind == "iso_fit":
            removed_b += math.pi * (mate.nominal_mm / 2.0) ** 2 * (t / 2.0)
            continue
        removed_a += math.pi * (mate.hole_a["nominal"] / 2.0) ** 2 * t
        removed_b += math.pi * (mate.hole_b["nominal"] / 2.0) ** 2 * t
    return removed_a, removed_b


def test_builds_a_two_part_assembly():
    asm = build_assembly(sample_assembly(1, 2))
    names = {child.name for child in asm.children}
    assert names == {"part_a", "part_b"}


def test_geometry_is_a_valid_solid_with_positive_volume():
    asm = build_assembly(sample_assembly(1, 2))
    for child in asm.children:
        solid = child.obj.val()
        assert solid.isValid(), f"{child.name} produced an invalid solid"
        assert solid.Volume() > 0.0


def test_drilling_holes_removes_material():
    """A hole that removed nothing would silently make every part identical.

    The plate is now sized per assembly, so a four-mate plate is physically
    BIGGER than a one-mate plate and total volume no longer decreases with mate
    count. Compare the volume removed from each assembly's own undrilled
    plates, which is what the original total-volume assertion was reaching for.
    """
    def removed(spec) -> float:
        blank = spec.plate_size_mm ** 2 * spec.plate_thickness_mm
        return 2.0 * blank - sum(s.Volume() for s in _parts(spec).values())

    one = removed(sample_assembly(2, 1))
    four = removed(sample_assembly(2, 4))
    assert one > 0.0, "drilling one mate removed no material at all"
    assert four > one, "more mates did not remove more material"


def test_same_seed_gives_identical_volume():
    a = sum(s.Volume() for s in _parts(sample_assembly(5, 3)).values())
    b = sum(s.Volume() for s in _parts(sample_assembly(5, 3)).values())
    assert a == pytest.approx(b)


@pytest.mark.parametrize("seed, difficulty", [(0, 4), (1, 3), (2, 4), (7, 2), (13, 4)])
def test_features_land_at_the_absolute_positions_the_layout_specifies(seed, difficulty):
    """Guards C1: chained relative workplanes put holes at CUMULATIVE positions.

    `.faces(">Z").workplane()` inherits the parent origin, so a per-feature
    `.center(x, 0)` chain drilled x = -12, 0, +12 as -12, then -12, then 0 --
    two holes where three were asked for, the third off the plate.
    """
    spec = sample_assembly(seed, difficulty)
    expected_a, expected_b = _expected_positions(spec)
    parts = _parts(spec)
    assert _cylinder_centre_xs(parts["part_a"]) == expected_a
    assert _cylinder_centre_xs(parts["part_b"]) == expected_b


@pytest.mark.parametrize("seed, difficulty", [(0, 4), (1, 3), (2, 4), (7, 2), (13, 4)])
def test_every_feature_that_should_be_drilled_exists(seed, difficulty):
    """Feature COUNT, which no earlier test asserted.

    part_a carries one hole per Tier 1 mate; iso_fit is a blind bore in part_b
    only, so part_b carries one feature per mate.
    """
    spec = sample_assembly(seed, difficulty)
    tier1 = sum(1 for m in spec.mates if m.kind != "iso_fit")
    parts = _parts(spec)
    assert len(_cylinder_centre_xs(parts["part_a"])) == tier1
    assert len(_cylinder_centre_xs(parts["part_b"])) == len(spec.mates)


@pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
def test_features_are_contained_and_disjoint_across_the_seed_sweep(difficulty):
    """Guards C1 and I3 together, over seeds 0-49 at every difficulty.

    A drill that clears the plate edge and misses its neighbours removes
    exactly pi*r^2*depth. Any overhang clips the cylinder, any overlap
    double-counts shared material, and a dropped feature removes nothing -- all
    three make the measured removal STRICTLY LESS than the sum of the ideal
    feature volumes. Equality is therefore containment and disjointness at
    once, and it is a one-sided check that cannot be satisfied by accident.
    """
    for seed in range(50):
        spec = sample_assembly(seed, difficulty)
        blank = spec.plate_size_mm ** 2 * spec.plate_thickness_mm
        parts = _parts(spec)
        expected_a, expected_b = _expected_removed_volume(spec)
        where = f"seed {seed} d{difficulty}"
        assert blank - parts["part_a"].Volume() == pytest.approx(
            expected_a, rel=1e-9, abs=1e-9
        ), f"{where}: part_a features clipped, merged or missing"
        assert blank - parts["part_b"].Volume() == pytest.approx(
            expected_b, rel=1e-9, abs=1e-9
        ), f"{where}: part_b features clipped, merged or missing"


def test_a_plate_too_small_for_its_features_is_rejected():
    """AssemblySpec.plate_size_mm has a 40.0 default; features can outgrow it.

    Failing loudly beats exporting reference geometry with a hole hanging off
    the edge, which is exactly what shipped before.
    """
    spec = sample_assembly(0, 4)
    radii = feature_radii_mm(spec.mates)
    assert minimum_plate_size_mm(radii) > 40.0, "pick a seed whose plate must grow"
    cramped = AssemblySpec(
        seed=spec.seed, difficulty=spec.difficulty, mates=spec.mates,
        plate_size_mm=40.0, plate_thickness_mm=spec.plate_thickness_mm,
    )
    with pytest.raises(ValueError, match="too small"):
        build_assembly(cramped)
