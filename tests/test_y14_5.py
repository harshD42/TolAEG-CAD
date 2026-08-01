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
    # H_a=H_b=8.5, F=8.0, T_a=T_b=0.6:
    # margin = (8.5-8.0) + (8.5-8.0) - (0.6+0.6) = 1.0 - 1.2 = -0.2
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="floating")
    assert verdict.assembles is False
    assert verdict.margin == pytest.approx(-0.2)


def test_fixed_fastener_is_stricter_than_floating():
    """Same geometry: a tolerance that passes floating must fail fixed at 0.5."""
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    assert fastener_assembles(hole, hole, M8_BOLT, condition="floating").assembles
    assert not fastener_assembles(hole, hole, M8_BOLT, condition="fixed").assembles


def test_asymmetric_holes_worse_on_hole_a():
    """H_a=H_b=8.5, F=8.0, T_a=0.6, T_b=0.1: worst-case axis separation is
    T_a/2 + T_b/2 = 0.35, comfortably within the combined permitted radius
    r_a + r_b = 0.25 + 0.25 = 0.50, so this ASSEMBLES.
    margin = (8.5-8.0) + (8.5-8.0) - (0.6+0.1) = 1.0 - 0.7 = +0.3
    """
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    hole_b = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    verdict = fastener_assembles(hole_a, hole_b, M8_BOLT, condition="floating")
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.3)


def test_asymmetric_holes_worse_on_hole_b():
    """Same as above with hole_a/hole_b's tolerances swapped. Floating pools
    T_a and T_b symmetrically, so the verdict and margin are identical.
    margin = (8.5-8.0) + (8.5-8.0) - (0.1+0.6) = 1.0 - 0.7 = +0.3
    """
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    hole_b = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    verdict = fastener_assembles(hole_a, hole_b, M8_BOLT, condition="floating")
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.3)


def test_floating_fully_swap_invariant():
    """Floating is symmetric under (H_a,T_a) <-> (H_b,T_b): swapping which
    part is 'a' and which is 'b' must not change margin or verdict, even
    when the holes differ in both size and position_tol.

    This also pins an absolute expected margin: asserting only that the two
    swapped verdicts equal EACH OTHER passes under the old buggy min()
    model too (and under any wrong-but-symmetric formula), since anything
    symmetric in (H_a,T_a) <-> (H_b,T_b) agrees with itself under a swap.
    Pinning the value against the documented formula is what actually
    discriminates the correct model from a symmetric-but-wrong one.

    H_a=8.5, F=8.0, T_a=0.3; H_b=8.6, T_b=0.4:
    margin = (H_a-F) + (H_b-F) - (T_a+T_b)
           = (8.5-8.0) + (8.6-8.0) - (0.3+0.4)
           = 0.5 + 0.6 - 0.7 = 0.4
    """
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.3)
    hole_b = FeatureOfSize(8.6, 0.0, 0.2, INTERNAL, position_tol=0.4)
    v1 = fastener_assembles(hole_a, hole_b, M8_BOLT, condition="floating")
    v2 = fastener_assembles(hole_b, hole_a, M8_BOLT, condition="floating")
    assert v1.assembles == v2.assembles
    assert v1.margin == pytest.approx(v2.margin)
    assert v1.margin == pytest.approx(0.4)
    assert v2.margin == pytest.approx(0.4)


def test_fixed_symmetric_in_position_tol_swap_only():
    """Fixed pools T_a and T_b as a sum, so swapping ONLY the tolerances
    (while keeping H_a on hole_a and H_b on hole_b) leaves margin unchanged.

    hole_a=8.5 (T=0.3), hole_b=8.6 (T=0.4):
      margin = (8.5-8.0) - (0.3+0.4) = 0.5 - 0.7 = -0.2
    hole_a=8.5 (T=0.4), hole_b=8.6 (T=0.3):
      margin = (8.5-8.0) - (0.4+0.3) = 0.5 - 0.7 = -0.2  (same)
    """
    hole_a_1 = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.3)
    hole_b_1 = FeatureOfSize(8.6, 0.0, 0.2, INTERNAL, position_tol=0.4)
    hole_a_2 = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.4)
    hole_b_2 = FeatureOfSize(8.6, 0.0, 0.2, INTERNAL, position_tol=0.3)

    v1 = fastener_assembles(hole_a_1, hole_b_1, M8_BOLT, condition="fixed")
    v2 = fastener_assembles(hole_a_2, hole_b_2, M8_BOLT, condition="fixed")
    assert v1.margin == pytest.approx(v2.margin)
    assert v1.margin == pytest.approx(-0.2)
    assert v1.assembles == v2.assembles is False


def test_fixed_not_swap_invariant_on_full_hole_swap():
    """Fixed is NOT symmetric under a full (H_a,T_a) <-> (H_b,T_b) swap: the
    size term only ever comes from hole_a, so fully swapping which part is
    'a' and which is 'b' changes the margin. Never assert full
    swap-invariance for fixed.

    hole_a=8.5 (T=0.3), hole_b=8.6 (T=0.4): margin = 0.5 - 0.7 = -0.2
    hole_a=8.6 (T=0.4), hole_b=8.5 (T=0.3): margin = 0.6 - 0.7 = -0.1
    """
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.3)
    hole_b = FeatureOfSize(8.6, 0.0, 0.2, INTERNAL, position_tol=0.4)

    v_original = fastener_assembles(hole_a, hole_b, M8_BOLT, condition="fixed")
    v_fully_swapped = fastener_assembles(hole_b, hole_a, M8_BOLT, condition="fixed")

    assert v_original.margin == pytest.approx(-0.2)
    assert v_fully_swapped.margin == pytest.approx(-0.1)
    assert v_original.margin != pytest.approx(v_fully_swapped.margin)


def test_unknown_condition_rejected():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    with pytest.raises(ValueError, match="condition"):
        fastener_assembles(hole, hole, M8_BOLT, condition="press")


def test_argument_order_does_not_change_verdict_for_asymmetric_hole_sizes():
    """Floating pools both holes' clearance and both position tolerances, so
    swapping hole_a/hole_b must not change the verdict when the holes differ
    in SIZE (not just position_tol) either.

    Ø8.5 and Ø8.05 holes, both position_tol 0.3, through an M8 bolt (mmc 8.0):
    margin = (8.5-8.0) + (8.05-8.0) - (0.3+0.3) = 0.5 + 0.05 - 0.6 = -0.05
    and the joint does not assemble, regardless of order.
    """
    big = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.3)
    tight = FeatureOfSize(8.05, 0.0, 0.2, INTERNAL, position_tol=0.3)

    v_big_first = fastener_assembles(big, tight, M8_BOLT, condition="floating")
    v_tight_first = fastener_assembles(tight, big, M8_BOLT, condition="floating")

    assert v_big_first.assembles == v_tight_first.assembles
    assert v_big_first.assembles is False
    assert v_big_first.margin == pytest.approx(v_tight_first.margin)
    assert v_big_first.margin == pytest.approx(-0.05)

    # hole_a_mmc/hole_b_mmc must be recorded consistently regardless of
    # argument order (governing_hole/governing_hole_mmc no longer exist --
    # the pooled model has no single "governing" hole).
    assert v_big_first.detail["hole_a_mmc"] == pytest.approx(8.5)
    assert v_big_first.detail["hole_b_mmc"] == pytest.approx(8.05)
    assert v_tight_first.detail["hole_a_mmc"] == pytest.approx(8.05)
    assert v_tight_first.detail["hole_b_mmc"] == pytest.approx(8.5)


def test_rejects_external_hole_b_when_floating():
    """For 'floating', hole_b must be validated as INTERNAL: a floating
    fastener needs a clearance hole in both parts, not silently ignored.
    """
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    external_hole = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.1)
    with pytest.raises(ValueError, match="hole_b"):
        fastener_assembles(hole_a, external_hole, M8_BOLT, condition="floating")


def test_allows_external_hole_b_when_fixed():
    """For 'fixed', hole_b is the fixed feature and may legitimately be a
    press-fit pin (EXTERNAL), not just a tapped hole (INTERNAL): its MMC
    never enters the fixed formula, so its feature_type is not restricted.
    """
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    press_fit_pin = FeatureOfSize(9.0, -0.1, 0.0, EXTERNAL, position_tol=0.1)
    verdict = fastener_assembles(hole_a, press_fit_pin, M8_BOLT, condition="fixed")
    # margin = (8.5-8.0) - (0.1+0.1) = 0.3
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.3)


def test_floating_raises_when_hole_a_below_fastener_mmc():
    """A hole the fastener must pass through cannot be smaller than the
    fastener at MMC -- the permitted-axis disc would have negative radius.
    H_a=7.9 < F=8.0 must raise, not silently produce a positive margin.
    """
    hole_a = FeatureOfSize(7.9, 0.0, 0.0, INTERNAL, position_tol=0.0)
    hole_b = FeatureOfSize(9.0, 0.0, 0.0, INTERNAL, position_tol=0.0)
    with pytest.raises(ValueError, match="hole_a"):
        fastener_assembles(hole_a, hole_b, M8_BOLT, condition="floating")


def test_floating_raises_when_hole_b_below_fastener_mmc():
    """Same guard, mirrored: floating requires BOTH holes to admit the
    fastener, so an undersized hole_b must also raise.
    """
    hole_a = FeatureOfSize(9.0, 0.0, 0.0, INTERNAL, position_tol=0.0)
    hole_b = FeatureOfSize(7.9, 0.0, 0.0, INTERNAL, position_tol=0.0)
    with pytest.raises(ValueError, match="hole_b"):
        fastener_assembles(hole_a, hole_b, M8_BOLT, condition="floating")


def test_fixed_raises_when_hole_a_below_fastener_mmc():
    """Fixed still requires hole_a (the clearance hole) to admit the
    fastener at MMC.
    """
    hole_a = FeatureOfSize(7.9, 0.0, 0.0, INTERNAL, position_tol=0.0)
    hole_b = FeatureOfSize(9.0, 0.0, 0.0, INTERNAL, position_tol=0.0)
    with pytest.raises(ValueError, match="hole_a"):
        fastener_assembles(hole_a, hole_b, M8_BOLT, condition="fixed")


def test_fixed_does_not_raise_when_hole_b_below_fastener_mmc():
    """hole_b's MMC is irrelevant in the fixed case -- it is the fixed
    feature (e.g. a tapped hole sized for the fastener's threads, not for
    clearance), so an undersized hole_b must NOT raise. This is the exact
    scenario from the spec: H_a=9.0, H_b=7.9, T=0, F=8.0 -> margin = 1.0.
    """
    hole_a = FeatureOfSize(9.0, 0.0, 0.0, INTERNAL, position_tol=0.0)
    hole_b = FeatureOfSize(7.9, 0.0, 0.0, INTERNAL, position_tol=0.0)
    verdict = fastener_assembles(hole_a, hole_b, M8_BOLT, condition="fixed")
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(1.0)


def test_detail_radial_slack_is_half_the_diametral_margin():
    """detail["radial_slack"] must equal margin / 2: margin is diametral
    (see the module docstring's UNITS note), so the physical radial slack
    between the two axes is half of it.

    hole_a=hole_b=8.5, T_a=T_b=0.1, F=8.0 (M8_BOLT):
    margin = (8.5-8.0) + (8.5-8.0) - (0.1+0.1) = 1.0 - 0.2 = 0.8
    radial_slack = 0.8 / 2 = 0.4
    """
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="floating")
    assert verdict.margin == pytest.approx(0.8)
    assert verdict.detail["radial_slack"] == pytest.approx(verdict.margin / 2.0)
    assert verdict.detail["radial_slack"] == pytest.approx(0.4)


def test_detail_margin_unit_states_diametral():
    """detail["margin_unit"] must document that margin is a diametral
    quantity, not a radial one -- misreading this is the exact failure
    class the UNITS note in the module docstring warns against.
    """
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="fixed")
    assert verdict.detail["margin_unit"] == "diametral_mm"
    assert "diametral" in verdict.detail["margin_unit"]


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
