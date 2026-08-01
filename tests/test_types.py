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


def test_verdict_is_immutable():
    v = Verdict(assembles=True, margin=0.5, method="floating_fastener", detail={})
    with pytest.raises(AttributeError):
        v.assembles = False
