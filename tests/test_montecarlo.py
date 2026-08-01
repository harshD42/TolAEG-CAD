import numpy as np
import pytest
from tolcad.iso286 import fit_from_designation
from tolcad.montecarlo import clearance_yield, sample_size
from tolcad.types import FeatureOfSize, FeatureType


def test_samples_stay_within_tolerance_limits():
    hole = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)
    rng = np.random.default_rng(42)
    samples = sample_size(hole, rng, n=10_000)
    assert samples.min() >= hole.min_size
    assert samples.max() <= hole.max_size


def test_uniform_distribution_spans_the_range():
    """Regression: the mean alone cannot distinguish uniform from normal sampling
    (both are centred on the same midpoint), so an implementation that silently
    ignores the `distribution` argument would still pass a mean-only check.
    The standard deviation is diagnostic: for this feature (range 0.021 mm),
    a true uniform draw has std ~= range/sqrt(12) ~= 0.00605, while the
    (truncated) normal draw used elsewhere has std ~= range/6 ~= 0.00351.
    """
    hole = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)
    rng = np.random.default_rng(42)
    samples = sample_size(hole, rng, n=10_000, distribution="uniform")
    assert samples.mean() == pytest.approx(20.0105, abs=1e-3)
    assert samples.std() == pytest.approx(0.00605, abs=1e-3)


def test_clearance_fit_yields_fully():
    """H7/g6 has positive minimum clearance, so yield must be exactly 1.0."""
    hole, shaft = fit_from_designation(20.0, "H7/g6")
    verdict = clearance_yield(hole, shaft, n=10_000, seed=0)
    assert verdict.margin == pytest.approx(1.0)
    assert verdict.assembles is True


def test_interference_fit_never_clears():
    """H7/p6 is a press fit; clearance yield must be exactly 0.0."""
    hole, shaft = fit_from_designation(20.0, "H7/p6")
    verdict = clearance_yield(hole, shaft, n=10_000, seed=0)
    assert verdict.margin == pytest.approx(0.0)
    assert verdict.assembles is False


def test_transition_fit_yields_partially():
    """H7/k6 sometimes clears and sometimes interferes."""
    hole, shaft = fit_from_designation(20.0, "H7/k6")
    verdict = clearance_yield(hole, shaft, n=50_000, seed=0, distribution="uniform")
    assert 0.0 < verdict.margin < 1.0


def test_identical_seeds_give_identical_results():
    hole, shaft = fit_from_designation(20.0, "H7/k6")
    a = clearance_yield(hole, shaft, n=10_000, seed=7)
    b = clearance_yield(hole, shaft, n=10_000, seed=7)
    assert a.margin == b.margin


def test_seed_is_recorded_in_detail():
    hole, shaft = fit_from_designation(20.0, "H7/g6")
    verdict = clearance_yield(hole, shaft, n=1_000, seed=99)
    assert verdict.detail["seed"] == 99
    assert verdict.detail["n"] == 1_000
