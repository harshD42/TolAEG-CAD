import pytest
from tolcad.types import FeatureOfSize, FeatureType
from tolcad.y14_5 import virtual_condition, vc_assembles

INTERNAL = FeatureType.INTERNAL
EXTERNAL = FeatureType.EXTERNAL


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
