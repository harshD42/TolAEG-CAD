import pytest
from tolcad.reliability import verdict_stability

HOLE = {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.1}
BOLT = {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0}


def _mate(position_tol: float) -> dict:
    hole = dict(HOLE, position_tol=position_tol)
    return {"type": "floating_fastener", "hole_a": hole, "hole_b": hole,
            "fastener": dict(BOLT)}


def test_far_from_boundary_verdicts_never_flip():
    # Allowable is 0.5; these are all far from it in both directions.
    mates = [_mate(t) for t in (0.05, 0.10, 0.15, 0.90, 0.95)]
    assert verdict_stability(mates, epsilon=1e-6, seed=0) == pytest.approx(1.0)


def test_near_boundary_cases_are_excluded_not_counted_as_failures():
    # position_tol 0.5 sits exactly on the allowable boundary.
    mates = [_mate(0.5)]
    # All cases excluded -> stability is undefined, reported as 1.0 with zero denominator.
    assert verdict_stability(mates, epsilon=1e-3, seed=0) == pytest.approx(1.0)


def test_stability_is_deterministic_for_a_given_seed():
    mates = [_mate(t) for t in (0.05, 0.2, 0.8)]
    a = verdict_stability(mates, epsilon=1e-6, seed=7)
    b = verdict_stability(mates, epsilon=1e-6, seed=7)
    assert a == b


def test_empty_input_rejected():
    with pytest.raises(ValueError, match="at least one mate"):
        verdict_stability([], epsilon=1e-6, seed=0)
