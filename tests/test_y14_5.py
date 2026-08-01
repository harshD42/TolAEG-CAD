import pytest
from tolcad.types import FeatureOfSize, FeatureType
from tolcad.y14_5 import (
    fastener_assembles,
    fixed_fastener_tolerance,
    floating_fastener_tolerance,
    virtual_condition,
    vc_assembles,
)

INTERNAL = FeatureType.INTERNAL
EXTERNAL = FeatureType.EXTERNAL

# Canonical worked example: M8 bolt (Ø8.0 max) through Ø8.5 min clearance holes.
M8_BOLT = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL)
CLEARANCE_HOLE = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)


def test_virtual_condition_external_adds_position_tolerance():
    # Ø8.0 pin at MMC with 0.1 position tolerance -> VC 8.1
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.1)
    assert virtual_condition(pin) == pytest.approx(8.1)


def test_virtual_condition_internal_subtracts_position_tolerance():
    # Ø8.5 hole at MMC with 0.5 position tolerance -> VC 8.0
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    assert virtual_condition(hole) == pytest.approx(8.0)


def test_assembly_guaranteed_when_pin_vc_fits_hole_vc():
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.0)
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.2)
    verdict = vc_assembles(pin, hole)
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.3)  # 8.3 - 8.0


def test_assembly_fails_when_pin_vc_exceeds_hole_vc():
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.4)
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    verdict = vc_assembles(pin, hole)
    assert verdict.assembles is False
    assert verdict.margin == pytest.approx(-0.4)  # 8.0 - 8.4


def test_exact_boundary_case_assembles():
    """VC_pin == VC_hole is the guaranteed-fit boundary and must pass."""
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.0)
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    verdict = vc_assembles(pin, hole)
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.0, abs=1e-9)


def test_rejects_swapped_feature_types():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    with pytest.raises(ValueError, match="external"):
        vc_assembles(hole, hole)


def test_floating_fastener_tolerance_is_hole_mmc_minus_fastener_mmc():
    # T = H - F = 8.5 - 8.0 = 0.5 per part
    assert floating_fastener_tolerance(CLEARANCE_HOLE, M8_BOLT) == pytest.approx(0.5)


def test_fixed_fastener_tolerance_is_half_the_floating_value():
    # T = (H - F) / 2 = 0.25 per part
    assert fixed_fastener_tolerance(CLEARANCE_HOLE, M8_BOLT) == pytest.approx(0.25)


def test_floating_fastener_assembles_at_allowable_tolerance():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="floating")
    assert verdict.assembles is True


def test_floating_fastener_fails_above_allowable_tolerance():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="floating")
    assert verdict.assembles is False
    assert verdict.margin == pytest.approx(-0.1)


def test_fixed_fastener_is_stricter_than_floating():
    """Same geometry: a tolerance that passes floating must fail fixed at 0.5."""
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    assert fastener_assembles(hole, hole, M8_BOLT, condition="floating").assembles
    assert not fastener_assembles(hole, hole, M8_BOLT, condition="fixed").assembles


def test_asymmetric_holes_use_the_worse_one():
    tight = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    loose = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    verdict = fastener_assembles(tight, loose, M8_BOLT, condition="floating")
    assert verdict.assembles is False


def test_unknown_condition_rejected():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    with pytest.raises(ValueError, match="condition"):
        fastener_assembles(hole, hole, M8_BOLT, condition="press")
