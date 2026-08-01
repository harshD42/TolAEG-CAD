import pytest
from tolcad.types import EPS, FeatureOfSize, FeatureType
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
    # Per-part (B-3): margin = min(H_a-F-T_a, H_b-F-T_b).
    # H_a=H_b=8.5, F=8.0, T_a=T_b=0.6:
    # margin_a = margin_b = 8.5-8.0-0.6 = -0.1
    # margin = min(-0.1, -0.1) = -0.1
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
    """Per-part (B-3): margin = min(H_a-F-T_a, H_b-F-T_b) -- the joint is
    only as good as its worst individual part, never an average or sum.
    H_a=H_b=8.5, F=8.0, T_a=0.6, T_b=0.1:
      margin_a = 8.5-8.0-0.6 = -0.1
      margin_b = 8.5-8.0-0.1 = +0.4
      margin = min(-0.1, +0.4) = -0.1
    hole_a is the worse part (large T_a) and its own -0.1 governs, so this
    does NOT assemble -- unlike the old pooled model, which averaged the two
    parts' slack together and let hole_b's surplus paper over hole_a's
    deficit.
    """
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    hole_b = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    verdict = fastener_assembles(hole_a, hole_b, M8_BOLT, condition="floating")
    assert verdict.assembles is False
    assert verdict.margin == pytest.approx(-0.1)
    # hole_a has the smaller (worse) individual margin, so it governs.
    assert verdict.detail["governing_part"] == "hole_a"


def test_asymmetric_holes_worse_on_hole_b():
    """Same as above with hole_a/hole_b's tolerances swapped. min() is
    commutative, so the verdict and margin are identical to the
    hole_a-governs case above.
    H_a=H_b=8.5, F=8.0, T_a=0.1, T_b=0.6:
      margin_a = 8.5-8.0-0.1 = +0.4
      margin_b = 8.5-8.0-0.6 = -0.1
      margin = min(+0.4, -0.1) = -0.1
    """
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    hole_b = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    verdict = fastener_assembles(hole_a, hole_b, M8_BOLT, condition="floating")
    assert verdict.assembles is False
    assert verdict.margin == pytest.approx(-0.1)
    # Now hole_b has the smaller (worse) individual margin, so it governs.
    assert verdict.detail["governing_part"] == "hole_b"


def test_floating_fully_swap_invariant():
    """Floating (per-part, B-3) is symmetric under (H_a,T_a) <-> (H_b,T_b):
    margin = min(H_a-F-T_a, H_b-F-T_b), and min() of an unordered pair does
    not care which element is labelled 'a' and which 'b'. Swapping which
    part is 'a' and which is 'b' must not change margin or verdict, even
    when the holes differ in both size and position_tol.

    This also pins an absolute expected margin: asserting only that the two
    swapped verdicts equal EACH OTHER passes under the old buggy pooled
    model too (and under any wrong-but-symmetric formula), since anything
    symmetric in (H_a,T_a) <-> (H_b,T_b) agrees with itself under a swap.
    Pinning the value against the documented formula is what actually
    discriminates the correct model from a symmetric-but-wrong one.

    H_a=8.5, F=8.0, T_a=0.3; H_b=8.6, T_b=0.4:
      margin_a = 8.5-8.0-0.3 = 0.2
      margin_b = 8.6-8.0-0.4 = 0.2
      margin = min(0.2, 0.2) = 0.2
    Swapped (H_a=8.6,T_a=0.4; H_b=8.5,T_b=0.3):
      margin_a = 8.6-8.0-0.4 = 0.2
      margin_b = 8.5-8.0-0.3 = 0.2
      margin = min(0.2, 0.2) = 0.2  (same)
    """
    hole_a = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.3)
    hole_b = FeatureOfSize(8.6, 0.0, 0.2, INTERNAL, position_tol=0.4)
    v1 = fastener_assembles(hole_a, hole_b, M8_BOLT, condition="floating")
    v2 = fastener_assembles(hole_b, hole_a, M8_BOLT, condition="floating")
    assert v1.assembles == v2.assembles
    assert v1.margin == pytest.approx(v2.margin)
    assert v1.margin == pytest.approx(0.2)
    assert v2.margin == pytest.approx(0.2)


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
    """Floating (per-part, B-3) takes min() over both parts' individual
    margins, so swapping hole_a/hole_b must not change the verdict when the
    holes differ in SIZE (not just position_tol) either.

    Ø8.5 and Ø8.05 holes, both position_tol 0.3, through an M8 bolt (mmc 8.0):
      margin_big  = 8.5 -8.0-0.3 = +0.2
      margin_tight= 8.05-8.0-0.3 = -0.25
      margin = min(+0.2, -0.25) = -0.25
    and the joint does not assemble, regardless of order (min is
    commutative, so which hole is labelled 'a' or 'b' does not matter).
    """
    big = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.3)
    tight = FeatureOfSize(8.05, 0.0, 0.2, INTERNAL, position_tol=0.3)

    v_big_first = fastener_assembles(big, tight, M8_BOLT, condition="floating")
    v_tight_first = fastener_assembles(tight, big, M8_BOLT, condition="floating")

    assert v_big_first.assembles == v_tight_first.assembles
    assert v_big_first.assembles is False
    assert v_big_first.margin == pytest.approx(v_tight_first.margin)
    assert v_big_first.margin == pytest.approx(-0.25)

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
      margin_a = margin_b = 8.5-8.0-0.1 = 0.4
      margin = min(0.4, 0.4) = 0.4
    radial_slack = 0.4 / 2 = 0.2
    """
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="floating")
    assert verdict.margin == pytest.approx(0.4)
    assert verdict.detail["radial_slack"] == pytest.approx(verdict.margin / 2.0)
    assert verdict.detail["radial_slack"] == pytest.approx(0.2)


def test_detail_margin_unit_states_diametral():
    """detail["margin_unit"] must document that margin is a diametral
    quantity, not a radial one -- misreading this is the exact failure
    class the UNITS note in the module docstring warns against.
    """
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="fixed")
    assert verdict.detail["margin_unit"] == "diametral_mm"
    assert "diametral" in verdict.detail["margin_unit"]


def test_b3_worked_example_boundary_case_assembles():
    """ASME Y14.5-2018 Nonmandatory Appendix B, section B-3, worked example:

    "Given that the fasteners in Figure B-1 are 6 diameter maximum and the
    clearance holes are 6.44 diameter minimum, find the required positional
    tolerance: T = 6.44 - 6 = 0.44 diameter for each part."

    So F (fastener MMC) = 6.0, H_a = H_b = 6.44, T_a = T_b = 0.44 (exactly
    the tolerance the standard says is "required", i.e. the boundary).
    Per-part (B-3): margin = min(H_a-F-T_a, H_b-F-T_b)
                            = min(6.44-6.0-0.44, 6.44-6.0-0.44)
                            = min(0.0, 0.0) = 0.0
    This is the exact boundary the standard's own arithmetic produces, so
    it must assemble (margin >= -EPS).
    """
    fastener = FeatureOfSize(6.0, 0.0, 0.0, EXTERNAL)
    hole = FeatureOfSize(6.44, 0.0, 0.0, INTERNAL, position_tol=0.44)
    verdict = fastener_assembles(hole, hole, fastener, condition="floating")
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.0, abs=1e-9)


def test_b4_worked_example_boundary_case_assembles():
    """ASME Y14.5-2018 Nonmandatory Appendix B, section B-4, worked example
    (same Figure B-1 geometry as the B-3 example, now fixed fastener):

    "T = (6.44-6)/2 = 0.22 diameter for each part."

    F = 6.0, H_a = H_b = 6.44, T_a = T_b = 0.22 (the "required" tolerance,
    i.e. the boundary).
    Fixed (B-4): margin = (H_a-F) - (T_a+T_b)
                        = (6.44-6.0) - (0.22+0.22)
                        = 0.44 - 0.44 = 0.0
    Must assemble at this exact boundary.
    """
    fastener = FeatureOfSize(6.0, 0.0, 0.0, EXTERNAL)
    hole = FeatureOfSize(6.44, 0.0, 0.0, INTERNAL, position_tol=0.22)
    verdict = fastener_assembles(hole, hole, fastener, condition="fixed")
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.0, abs=1e-9)


def test_b4_worked_example_unequal_split_boundary_case_assembles():
    """ASME Y14.5-2018 Nonmandatory Appendix B, section B-4, unequal-split
    worked example (same Figure B-1 geometry, 2T = 0.44 split unevenly):

    "When 2T is 0.44, if T1 = 0.18, then T2 = 0.26."

    F = 6.0, H_a = 6.44, T_a = 0.18, T_b = 0.26.
    Fixed (B-4): margin = (H_a-F) - (T_a+T_b)
                        = (6.44-6.0) - (0.18+0.26)
                        = 0.44 - 0.44 = 0.0
    Must assemble at this exact boundary, regardless of how the 0.44 total
    is split between the two parts.
    """
    fastener = FeatureOfSize(6.0, 0.0, 0.0, EXTERNAL)
    hole_a = FeatureOfSize(6.44, 0.0, 0.0, INTERNAL, position_tol=0.18)
    hole_b = FeatureOfSize(6.44, 0.0, 0.0, INTERNAL, position_tol=0.26)
    verdict = fastener_assembles(hole_a, hole_b, fastener, condition="fixed")
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.0, abs=1e-9)


def test_per_part_rule_discriminates_against_pooled_model():
    """ASME Y14.5-2018 Nonmandatory Appendix B, section B-3: the per-part
    rule ("the formula H = F + T or T = H - F is applied to each part
    individually") must reject a joint that the old, incorrect POOLED model
    would have accepted.

    H_a=8.6, T_a=0.65; H_b=8.2, T_b=0.0; F=8.0 (floating):
      margin_a = 8.6-8.0-0.65 = -0.05
      margin_b = 8.2-8.0-0.0  = +0.20
      per-part margin = min(-0.05, +0.20) = -0.05  -> does NOT assemble

    The old pooled model, margin = (H_a-F)+(H_b-F)-(T_a+T_b), would give
      (8.6-8.0)+(8.2-8.0)-(0.65+0.0) = 0.6+0.2-0.65 = +0.15  -> assembles

    This case exists specifically to fail if anyone reintroduces pooling:
    hole_a is individually out of tolerance (margin_a < 0) but hole_b's
    surplus slack is large enough to paper over the deficit under pooling.
    B-3 forbids exactly this kind of cross-part averaging.
    """
    fastener = FeatureOfSize(8.0, 0.0, 0.0, EXTERNAL)
    hole_a = FeatureOfSize(8.6, 0.0, 0.0, INTERNAL, position_tol=0.65)
    hole_b = FeatureOfSize(8.2, 0.0, 0.0, INTERNAL, position_tol=0.0)
    verdict = fastener_assembles(hole_a, hole_b, fastener, condition="floating")
    assert verdict.assembles is False
    assert verdict.margin == pytest.approx(-0.05)


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


# --- Mutation-score triage additions (cosmic-ray, 2026-08-01) -----------------
#
# The tests above only ever exercised bonus_tolerance/tolerance formulas at
# values where a wrong operator happens to coincide with the right one (e.g.
# 0.5/2.0 == 0.5**2.0, or where hole.mmc is always comfortably above
# fastener.mmc so `-` and `%` agree). These additions pick values that force
# genuine divergence, or exercise branches (equal-mmc boundary, EPS boundary,
# detail["governing_part"]) nothing above touched at all.


def test_bonus_tolerance_rejects_actual_size_below_min():
    """No existing test exercises the LOWER bound of the validity guard --
    test_actual_size_outside_limits_rejected only probes above max_size. A
    mutant that replaces `min_size - EPS` with `min_size * EPS` (or % / **)
    makes the lower bound collapse to ~0, so any small actual_size would
    wrongly be accepted; this catches it from below.
    """
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    with pytest.raises(ValueError, match="outside"):
        bonus_tolerance(hole, 8.3)


def test_bonus_tolerance_accepts_lower_bound_exactly_at_epsilon():
    """min_size - EPS is INCLUSIVE (`<=`); a mutant narrowing it to `<` would
    reject this exact boundary value instead of computing a (small) bonus.
    """
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    assert bonus_tolerance(hole, hole.min_size - EPS) == pytest.approx(EPS, abs=1e-12)


def test_bonus_tolerance_accepts_upper_bound_exactly_at_epsilon():
    """max_size + EPS is INCLUSIVE (`<=`); a mutant narrowing it to `<` would
    reject this exact boundary value instead of computing the bonus.
    """
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    assert bonus_tolerance(hole, hole.max_size + EPS) == pytest.approx(0.2 + EPS, abs=1e-12)


def test_floating_fastener_tolerance_beyond_double_the_fastener_mmc():
    """H=7, F=3: H - F = 4, but H % F = 1 (floor(7/3)=2, 7-2*3=1). The
    canonical worked example (H=8.5, F=8.0) never exceeds 2x, so subtraction
    and modulo happen to be indistinguishable there.
    """
    hole = FeatureOfSize(10.0, 0.0, 0.0, INTERNAL)
    fastener = FeatureOfSize(3.0, 0.0, 0.0, EXTERNAL)
    assert floating_fastener_tolerance(hole, fastener) == pytest.approx(7.0)


def test_fixed_fastener_tolerance_halves_not_squares_the_clearance():
    """0.5/2.0 == 0.5**2.0 == 0.25 by coincidence in the canonical worked
    example (CLEARANCE_HOLE/M8_BOLT), which is exactly why that mutant
    survived. 1.0/2.0=0.5 != 1.0**2.0=1.0 forces the two apart, and 9%8=1
    forces subtraction apart from modulo too.
    """
    hole = FeatureOfSize(9.0, 0.0, 0.0, INTERNAL)
    fastener = FeatureOfSize(8.0, 0.0, 0.0, EXTERNAL)
    assert fixed_fastener_tolerance(hole, fastener) == pytest.approx(0.5)


def test_fastener_assembles_clearance_values_beyond_double_fastener_mmc():
    """detail["clearance_a"]/["clearance_b"] must be hole.mmc - fastener.mmc,
    not hole.mmc % fastener.mmc. Chosen so hole_a.mmc/hole_b.mmc each exceed
    2x the fastener mmc, where modulo and subtraction diverge sharply.
    """
    fastener = FeatureOfSize(3.0, 0.0, 0.0, EXTERNAL)
    hole_a = FeatureOfSize(10.0, 0.0, 0.0, INTERNAL, position_tol=0.0)
    hole_b = FeatureOfSize(13.0, 0.0, 0.0, INTERNAL, position_tol=0.0)
    verdict = fastener_assembles(hole_a, hole_b, fastener, condition="floating")
    assert verdict.detail["clearance_a"] == pytest.approx(7.0)
    assert verdict.detail["clearance_b"] == pytest.approx(10.0)


def test_governing_part_tie_breaks_to_hole_a():
    """When both parts have bit-identical individual margins, the "<=" tie
    -break in `"hole_a" if margin_a <= margin_b else "hole_b"` must land on
    hole_a. Uses hole_a and hole_b built from the SAME feature so margin_a
    and margin_b are computed from identical inputs (bit-identical, not
    merely float-approx-equal from two different arithmetic paths).
    """
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.3)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="floating")
    assert verdict.detail["governing_part"] == "hole_a"


def test_floating_allows_hole_a_exactly_at_fastener_mmc():
    """hole_a.mmc == fastener.mmc is the zero-clearance boundary case (the
    fastener exactly fills the hole at MMC) -- legitimate, must NOT raise.
    The guard is `hole_a.mmc < fastener.mmc`; a `<=` mutant would wrongly
    reject this boundary. No existing test used an equal-mmc pair.
    """
    fastener = FeatureOfSize(6.0, 0.0, 0.0, EXTERNAL)
    hole = FeatureOfSize(6.0, 0.0, 0.0, INTERNAL, position_tol=0.0)
    verdict = fastener_assembles(hole, hole, fastener, condition="floating")
    assert verdict.detail["clearance_a"] == pytest.approx(0.0)
    assert verdict.detail["clearance_b"] == pytest.approx(0.0)


def test_vc_assembles_at_exact_epsilon_boundary():
    """margin == -EPS exactly is the assembles/fails boundary (`>= -EPS`); a
    mutant narrowing it to `>` would reject this exact boundary. Constructed
    from 0 and EPS directly so the arithmetic is bit-exact, not merely close.
    """
    pin = FeatureOfSize(EPS, 0.0, 0.0, EXTERNAL)
    hole = FeatureOfSize(0.0, 0.0, 0.0, INTERNAL)
    verdict = vc_assembles(pin, hole)
    assert verdict.margin == -EPS
    assert verdict.assembles is True


def test_fixed_fastener_assembles_at_exact_epsilon_boundary():
    """Same boundary as above, through fastener_assembles' `>= -EPS` (a
    separate call site from vc_assembles', so it needs its own mutant
    coverage). Constructed so margin = 0 - EPS = -EPS bit-exactly.
    """
    fastener = FeatureOfSize(0.0, 0.0, 0.0, EXTERNAL)
    hole_a = FeatureOfSize(0.0, 0.0, 0.0, INTERNAL, position_tol=EPS)
    hole_b = FeatureOfSize(0.0, 0.0, 0.0, INTERNAL, position_tol=0.0)
    verdict = fastener_assembles(hole_a, hole_b, fastener, condition="fixed")
    assert verdict.margin == -EPS
    assert verdict.assembles is True


# --- Equivalent mutants (documented, not killed) ------------------------------
#
# cosmic-ray's survivor list for y14_5.py also includes 16 mutants that are
# genuinely equivalent -- no test can distinguish them because the mutated
# expression cannot produce different observable behaviour, given invariants
# the rest of the module already enforces:
#
# 1. EIGHT mutants replace `is`/`is not` with `==`/`!=` (or vice versa) on
#    FeatureType comparisons, e.g. `feature.feature_type is FeatureType.EXTERNAL`
#    -> `== FeatureType.EXTERNAL` (and the `is not`/`!=` pairs in
#    vc_assembles, _check_fastener_pair, and fastener_assembles' hole_a/hole_b/
#    fastener guards). FeatureType is a plain Enum with no custom __eq__, so
#    its members compare equal only to themselves -- CPython enum members are
#    singletons, making `is`/`is not` and `==`/`!=` produce identical results
#    for every possible FeatureType value. There is no input that could make
#    these disagree.
#
# 2. EIGHT mutants replace `condition == "floating"` / `condition == "fixed"`
#    with `>=`, `<=`, or `is` against the same literal (in the governing_part
#    detail expression, the hole_b feature-type guard, and the hole_b MMC
#    guard). `fastener_assembles` validates `condition in ("floating",
#    "fixed")` before any of these comparisons run, so `condition` can only
#    ever be one of exactly those two strings at this point. For that
#    restricted two-value domain: "fixed" < "floating" lexically (comparing
#    "f-i-x" vs "f-l-o": 'i' < 'l'), so `>=`/`<=` against either literal agree
#    with `==`/`!=` for both possible values; and "floating"/"fixed" are
#    identifier-shaped literals that CPython interns identically between this
#    module and any caller using the same literal, so `is` agrees with `==`
#    too. A third value could break this, but the upstream guard forecloses
#    that -- there's no way to reach these lines with anything else.
