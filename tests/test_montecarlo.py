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


# --- Mutation-score triage additions (cosmic-ray, 2026-08-01) -----------------
#
# The existing tests check the "uniform" branch's exact mean/std (diagnostic
# for the formula) but only check the "normal" branch's clipped min/max
# range -- which every mid/sigma formula satisfies trivially post-clip. And
# nothing exercises a zero-width tolerance band, an unknown `distribution`
# value, or clearance_yield's own zero-clearance boundary.


def test_normal_distribution_matches_the_documented_mid_and_sigma():
    """The normal branch places +/-3 sigma at the tolerance limits:
    mid=(lo+hi)/2, sigma=(hi-lo)/6. A min/max-only check (everything clips
    into range regardless of mid/sigma) cannot distinguish the correct
    formula from a folded/multiplied/divided/off-by-one-denominator mutant;
    mean and std can.
    """
    hole = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)
    rng = np.random.default_rng(42)
    samples = sample_size(hole, rng, n=20_000, distribution="normal")
    assert samples.mean() == pytest.approx(20.0105, abs=1e-3)
    assert samples.std() == pytest.approx(0.00351, abs=2e-4)


def test_zero_width_tolerance_returns_the_constant_nominal():
    """hi == lo (a basic, untoleranced dimension) is a legitimate case --
    see the analogous finding in test_types.py. sample_size must return the
    constant value, not divide by a zero-width sigma.
    """
    basic = FeatureOfSize(10.0, 0.0, 0.0, FeatureType.INTERNAL)
    rng = np.random.default_rng(0)
    samples = sample_size(basic, rng, n=100, distribution="normal")
    assert np.all(samples == 10.0)


def test_zero_width_tolerance_does_not_consume_rng_state():
    """The `sigma == 0.0` shortcut returns np.full(n, mid) without drawing
    from rng. numpy's Generator.normal(scale=0) is ALSO deterministic and
    returns the same constant values, so a mutant that fails to take the
    shortcut is invisible to a values-only check -- it only shows up as
    unwanted rng-state consumption, observed here via a later draw that
    would otherwise be reproducible.
    """
    basic = FeatureOfSize(10.0, 0.0, 0.0, FeatureType.INTERNAL)
    toleranced = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)

    rng_a = np.random.default_rng(123)
    sample_size(basic, rng_a, n=50, distribution="normal")  # must not draw
    result_a = sample_size(toleranced, rng_a, n=50, distribution="normal")

    rng_b = np.random.default_rng(123)
    result_b = sample_size(toleranced, rng_b, n=50, distribution="normal")

    assert np.array_equal(result_a, result_b)


def test_unknown_distribution_before_both_names_lexically_is_rejected():
    """'bogus' sorts before both 'normal' and 'uniform' lexically, so a `<=`
    substitute for either `==` comparison would incorrectly dispatch it
    instead of raising.
    """
    hole = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError, match="distribution must be"):
        sample_size(hole, rng, n=10, distribution="bogus")


def test_unknown_distribution_after_both_names_lexically_is_rejected():
    """'zzz' sorts after both 'normal' and 'uniform' lexically, so a `>=`
    substitute for either `==` comparison would incorrectly dispatch it
    instead of raising.
    """
    hole = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError, match="distribution must be"):
        sample_size(hole, rng, n=10, distribution="zzz")


def test_uniform_matched_by_equality_not_identity():
    """Guards against `==` degrading to `is`; CPython interns identifier-
    shaped literals, so a literal "uniform" here could coincidentally share
    identity with the literal in montecarlo.py. Build the string at runtime
    so identity cannot coincide by accident.
    """
    hole = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)
    rng = np.random.default_rng(0)
    distribution = "".join(["uniform"])
    samples = sample_size(hole, rng, n=1_000, distribution=distribution)
    assert samples.min() >= hole.min_size
    assert samples.max() <= hole.max_size


def test_normal_matched_by_equality_not_identity():
    """Same reasoning as above, for the "normal" branch."""
    hole = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)
    rng = np.random.default_rng(0)
    distribution = "".join(["normal"])
    samples = sample_size(hole, rng, n=1_000, distribution=distribution)
    assert samples.min() >= hole.min_size
    assert samples.max() <= hole.max_size


def test_zero_clearance_does_not_count_as_yielding():
    """Exactly touching (clearance == 0, e.g. two identical zero-tolerance
    features) must not count as a successful clearance fit: the criterion
    is a strict `> 0`. Also gives clearance_yield its own zero-width-band
    exercise, analogous to the one in test_types.py / this file above.
    """
    hole = FeatureOfSize(20.0, 0.0, 0.0, FeatureType.INTERNAL)
    shaft = FeatureOfSize(20.0, 0.0, 0.0, FeatureType.EXTERNAL)
    verdict = clearance_yield(hole, shaft, n=100, seed=0)
    assert verdict.margin == pytest.approx(0.0)
    assert verdict.assembles is False


def test_clearance_is_subtraction_not_ratio_floor_division():
    """detail["mean_clearance"]/["min_clearance"] must be holes-shafts (a
    small mm-scale gap), not floor(holes/shafts). At this nominal size,
    holes/shafts is always close to 1, so floor division degenerates to 0
    or 1 -- which coincidentally has the same SIGN as the correct
    subtraction for the existing all-clearance and all-interference tests,
    hiding the mutant from a `>0`/`==0` yield check alone. The exact
    magnitude of mean/min clearance exposes it.
    """
    hole, shaft = fit_from_designation(20.0, "H7/g6")
    verdict = clearance_yield(hole, shaft, n=1_000, seed=0)
    assert 0.0 < verdict.detail["mean_clearance"] < 0.1
    assert 0.0 < verdict.detail["min_clearance"] < 0.1


# --- Equivalent mutants (documented, not killed) ------------------------------
#
# 1. `if sigma <= 0.0:` in place of `if sigma == 0.0:`. sigma = (hi-lo)/6.0,
#    and FeatureOfSize.__post_init__ already guarantees upper_dev >=
#    lower_dev, so hi >= lo always and sigma can never be negative. Given
#    that invariant, `sigma <= 0.0` and `sigma == 0.0` are exactly the same
#    predicate -- there is no reachable sigma for which they disagree.
#
# 2. `assembles=yield_frac == 1.0` in place of `yield_frac >= 1.0`.
#    yield_frac = float(np.mean(boolean array)), which is mathematically
#    bounded to [0, 1] -- a mean of 0/1 values can never exceed 1.0. Given
#    that bound, `>= 1.0` and `== 1.0` are the same predicate; `>= 1.0`
#    could only diverge from `== 1.0` for a value strictly greater than 1.0,
#    which yield_frac cannot produce.
