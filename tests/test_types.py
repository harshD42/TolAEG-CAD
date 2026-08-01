import pytest
from tolcad.types import FeatureOfSize, FeatureType, Verdict


def test_internal_feature_mmc_is_smallest_size():
    # Ø8.5 +0.2/-0.0 hole
    hole = FeatureOfSize(8.5, 0.0, 0.2, FeatureType.INTERNAL)
    assert hole.mmc == pytest.approx(8.5)
    assert hole.lmc == pytest.approx(8.7)


def test_external_feature_mmc_is_largest_size():
    # Ø8.0 +0.0/-0.1 pin
    pin = FeatureOfSize(8.0, -0.1, 0.0, FeatureType.EXTERNAL)
    assert pin.mmc == pytest.approx(8.0)
    assert pin.lmc == pytest.approx(7.9)


def test_zero_width_tolerance_band_is_a_valid_basic_dimension():
    """upper_dev == lower_dev is a legitimate basic (untoleranced) dimension.

    Guards ``if upper_dev < lower_dev: raise`` staying strict less-than; a
    mutant that widens it to <= would wrongly reject this valid zero-width
    case, which every Tier 1 verdict ultimately rests on being constructible.
    """
    basic = FeatureOfSize(10.0, 0.0, 0.0, FeatureType.INTERNAL)
    assert basic.min_size == pytest.approx(10.0)
    assert basic.max_size == pytest.approx(10.0)
    assert basic.mmc == pytest.approx(10.0)
    assert basic.lmc == pytest.approx(10.0)


def test_verdict_is_immutable():
    v = Verdict(assembles=True, margin=0.5, method="floating_fastener", detail={})
    with pytest.raises(AttributeError):
        v.assembles = False


# --- Mutation-score triage additions (cosmic-ray, 2026-08-01) -----------------


def test_feature_of_size_is_immutable():
    """FeatureOfSize is @dataclass(frozen=True); nothing previously asserted
    that. A mutant flipping it to frozen=False would silently allow a
    toleranced feature to be mutated after construction.
    """
    hole = FeatureOfSize(8.5, 0.0, 0.2, FeatureType.INTERNAL)
    with pytest.raises(AttributeError):
        hole.nominal = 9.0


def test_position_tol_defaults_to_zero_when_omitted():
    """position_tol's default must be 0.0. Existing tests always pass all
    four positional args and never assert the default's VALUE, only that
    mmc/lmc come out right when position_tol happens not to matter for
    those two properties (it doesn't -- mmc/lmc never read position_tol).
    """
    hole = FeatureOfSize(8.5, 0.0, 0.2, FeatureType.INTERNAL)
    assert hole.position_tol == 0.0


def test_negative_position_tol_rejected():
    """position_tol must be non-negative. No existing test ever passes a
    negative value, so the guard `if position_tol < 0.0: raise` was never
    exercised on its true side.
    """
    with pytest.raises(ValueError, match="non-negative"):
        FeatureOfSize(8.5, 0.0, 0.2, FeatureType.INTERNAL, position_tol=-0.1)


# --- Equivalent mutants (documented, not killed) ------------------------------
#
# TWO mutants replace `is` with `==` on `self.feature_type is FeatureType.
# INTERNAL` (in both `mmc` and `lmc`). FeatureType is a plain Enum with no
# custom __eq__, and CPython enum members are singletons, so `is` and `==`
# produce identical results for every FeatureType value -- there is no input
# that could make them disagree. (Same reasoning documented in
# test_y14_5.py for the analogous FeatureType comparisons there.)
