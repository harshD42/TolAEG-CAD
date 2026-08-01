import pytest
from tolcad.types import FeatureOfSize, FeatureType
from tolcad.y14_5 import (
    bonus_tolerance,
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


def test_asymmetric_holes_worse_on_hole_a():
    """Worse tolerance on hole_a (0.6 > allowable 0.5) must fail."""
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    hole_b = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    verdict = fastener_assembles(hole_a, hole_b, M8_BOLT, condition="floating")
    assert verdict.assembles is False


def test_asymmetric_holes_worse_on_hole_b():
    """Worse tolerance on hole_b (0.6 > allowable 0.5) must fail.
    This test proves hole_b is actually considered, not ignored.
    """
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    hole_b = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    verdict = fastener_assembles(hole_a, hole_b, M8_BOLT, condition="floating")
    assert verdict.assembles is False


def test_unknown_condition_rejected():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    with pytest.raises(ValueError, match="condition"):
        fastener_assembles(hole, hole, M8_BOLT, condition="press")


def test_argument_order_does_not_change_verdict_for_asymmetric_hole_sizes():
    """C1 regression: swapping hole_a/hole_b must not change the verdict when the
    holes differ in SIZE (not just position_tol). The allowable tolerance must
    always be computed from the smaller (governing) hole, regardless of which
    argument position it is passed in.

    Ø8.5 and Ø8.05 holes, both position_tol 0.3, through an M8 bolt (mmc 8.0):
    the smaller (Ø8.05) hole governs, allowable = 8.05 - 8.0 = 0.05, so margin
    = 0.05 - 0.3 = -0.25 and the joint does not assemble, regardless of order.
    """
    big = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.3)
    tight = FeatureOfSize(8.05, 0.0, 0.2, INTERNAL, position_tol=0.3)

    v_big_first = fastener_assembles(big, tight, M8_BOLT, condition="floating")
    v_tight_first = fastener_assembles(tight, big, M8_BOLT, condition="floating")

    assert v_big_first.assembles == v_tight_first.assembles
    assert v_big_first.assembles is False
    assert v_big_first.margin == pytest.approx(v_tight_first.margin)
    assert v_big_first.margin == pytest.approx(-0.25)

    # The governing (smaller) hole must be recorded regardless of argument order.
    assert v_big_first.detail["governing_hole_mmc"] == pytest.approx(8.05)
    assert v_tight_first.detail["governing_hole_mmc"] == pytest.approx(8.05)


def test_rejects_external_hole_b():
    """hole_b must be validated as INTERNAL, not silently ignored."""
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    external_hole = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.1)
    with pytest.raises(ValueError, match="hole_b"):
        fastener_assembles(hole_a, external_hole, M8_BOLT, condition="floating")


def test_no_bonus_at_mmc():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    assert bonus_tolerance(hole, 8.5) == pytest.approx(0.0)


def test_full_bonus_at_lmc_for_internal_feature():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    assert bonus_tolerance(hole, 8.7) == pytest.approx(0.2)


def test_full_bonus_at_lmc_for_external_feature():
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL)
    assert bonus_tolerance(pin, 7.9) == pytest.approx(0.1)


def test_partial_bonus_mid_range():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    assert bonus_tolerance(hole, 8.6) == pytest.approx(0.1)


def test_actual_size_outside_limits_rejected():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    with pytest.raises(ValueError, match="outside"):
        bonus_tolerance(hole, 8.9)
