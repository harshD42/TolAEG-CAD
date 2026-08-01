import pytest

cq = pytest.importorskip("cadquery", reason="requires the [gen] extra")

from tolcad.gen.build import build_assembly
from tolcad.gen.sampler import sample_assembly


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
    """A hole that removed nothing would silently make every part identical."""
    one = build_assembly(sample_assembly(2, 1))
    four = build_assembly(sample_assembly(2, 4))
    vol_one = sum(c.obj.val().Volume() for c in one.children)
    vol_four = sum(c.obj.val().Volume() for c in four.children)
    assert vol_four < vol_one, "more mates did not remove more material"


def test_same_seed_gives_identical_volume():
    a = sum(c.obj.val().Volume() for c in build_assembly(sample_assembly(5, 3)).children)
    b = sum(c.obj.val().Volume() for c in build_assembly(sample_assembly(5, 3)).children)
    assert a == pytest.approx(b)
