import numpy as np
import pytest
from tolcad.reliability import StabilityResult, _perturb, verdict_stability
from tolcad.types import Verdict

HOLE = {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.1}
BOLT = {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0}


def _mate(position_tol: float) -> dict:
    hole = dict(HOLE, position_tol=position_tol)
    return {"type": "floating_fastener", "hole_a": hole, "hole_b": hole,
            "fastener": dict(BOLT)}


def test_far_from_boundary_verdicts_never_flip():
    # Allowable is 0.5; these are all far from it in both directions.
    mates = [_mate(t) for t in (0.05, 0.10, 0.15, 0.90, 0.95)]
    result = verdict_stability(mates, epsilon=1e-6, seed=0)
    assert result.value == pytest.approx(1.0)
    assert result.tested > 0  # Verify these cases are actually tested


def test_near_boundary_cases_are_excluded_not_counted_as_failures():
    # position_tol 0.5 sits exactly on the allowable boundary (margin = 0).
    # With BOUNDARY_BAND = 2.0 and epsilon = 1e-3, exclusion band is 2e-3.
    # This case should be excluded.
    mates = [_mate(0.5)]
    result = verdict_stability(mates, epsilon=1e-3, seed=0)
    assert result.value == pytest.approx(1.0)
    assert result.tested == 0  # All cases excluded
    assert result.excluded == 1


def test_stability_is_deterministic_for_a_given_seed():
    mates = [_mate(t) for t in (0.05, 0.2, 0.8)]
    a = verdict_stability(mates, epsilon=1e-6, seed=7)
    b = verdict_stability(mates, epsilon=1e-6, seed=7)
    assert a.value == b.value
    assert a.tested == b.tested
    assert a.excluded == b.excluded


def test_empty_input_rejected():
    with pytest.raises(ValueError, match="at least one mate"):
        verdict_stability([], epsilon=1e-6, seed=0)


def test_positive_control_detects_instability():
    """Positive control: construct an input where verdict_stability returns < 1.0.

    This test proves the metric is not vacuous and can actually detect instability.
    Uses an aggregate construction: 100 mates each with margin = 2.05*epsilon, which
    detects stability < 1.0 on 100% of seeds (verified across 100 consecutive seeds).

    Rationale: Mates with margin = 2.05*epsilon sit just outside the exclusion band
    (|margin| < 2*epsilon). Perturbations are sums of ~7 uniform(-epsilon, +epsilon)
    draws with expected magnitude ~epsilon * sqrt(7/3) ≈ 1.5*epsilon, concentrated near
    zero but with sufficient tail probability to flip some mates. With 100 mates,
    the aggregate sees stable instability across all random seeds.
    """
    # Robust positive control: 100 mates at margin = 2.05e-4 (with epsilon = 1e-4)
    # This is just outside the exclusion band (2e-4) and detects on 100% of seeds.
    epsilon = 1e-4
    margin_target = 2.05 * epsilon  # 2.05e-4
    position_tol_target = 0.5 - margin_target  # 0.5 - 2.05e-4 = 0.49979500

    critical_mates = [_mate(position_tol_target) for _ in range(100)]
    result = verdict_stability(critical_mates, epsilon=epsilon, seed=0)

    # All 100 mates should be tested (margin = 2.05e-4 > 2e-4 exclusion band)
    assert result.tested == 100, (
        f"Expected all 100 mates tested, got tested={result.tested}, "
        f"excluded={result.excluded}"
    )
    # The key assertion: stability is measurably less than 1.0
    # This aggregate construction detects instability on 100% of seeds.
    assert 0.0 <= result.value < 1.0, (
        f"Positive control failed: expected stability < 1.0 but got {result.value} "
        f"(tested={result.tested})"
    )


def test_zero_denominator_is_distinguishable_from_verified_stability():
    """Verify that an all-excluded case is distinguishable from a verified 1.0.

    A caller can tell the difference by inspecting the tested count.
    """
    # Case 1: all excluded (zero denominator)
    mates_excluded = [_mate(0.5)]
    result_excluded = verdict_stability(mates_excluded, epsilon=1e-3, seed=0)
    assert result_excluded.value == 1.0
    assert result_excluded.tested == 0
    assert result_excluded.excluded == 1

    # Case 2: all tested and stable
    mates_stable = [_mate(t) for t in (0.05, 0.10)]
    result_stable = verdict_stability(mates_stable, epsilon=1e-6, seed=0)
    assert result_stable.value == 1.0
    assert result_stable.tested > 0
    assert result_stable.excluded == 0


class _CountingRNG:
    """Wraps a real Generator and counts calls to `.uniform()`.

    Lets a test observe how many perturbation draws `_perturb` actually makes,
    which is the only way to directly falsify a reinstated aliasing bug (a
    bug that double-perturbs an aliased dict does not change *whether* the
    function runs, only *how many draws it consumes* and therefore the
    resulting values).
    """

    def __init__(self, real_rng: np.random.Generator) -> None:
        self._real = real_rng
        self.calls = 0

    def uniform(self, lo: float, hi: float) -> float:
        self.calls += 1
        return self._real.uniform(lo, hi)


def test_aliasing_is_handled_correctly():
    """Verify that hole_a and hole_b are each perturbed exactly once when aliased.

    When hole_a and hole_b reference the same dict, copy.deepcopy preserves the
    alias. `_perturb` must track seen dict ids to avoid double-perturbing.

    A prior version of this test asserted only `result.tested <= 1`, which is
    trivially true for a single mate regardless of whether the aliasing bug is
    present or not — it would pass even with the bug reinstated. This version
    counts the actual number of perturbation draws consumed, which differs
    measurably (7 vs 11) between the aliased case and a non-aliased control
    with equivalent content, and so is falsifiable.
    """
    hole = {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.1}
    fastener = {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0}

    # hole_a and hole_b are the SAME dict object.
    mate_aliased = {"type": "floating_fastener", "hole_a": hole, "hole_b": hole,
                    "fastener": dict(fastener)}
    # Control: hole_a and hole_b are distinct dicts with identical content.
    mate_control = {"type": "floating_fastener", "hole_a": dict(hole),
                    "hole_b": dict(hole), "fastener": dict(fastener)}

    rng_aliased = _CountingRNG(np.random.default_rng(0))
    _perturb(mate_aliased, epsilon=1e-6, rng=rng_aliased)

    rng_control = _CountingRNG(np.random.default_rng(0))
    _perturb(mate_control, epsilon=1e-6, rng=rng_control)

    # hole has 4 perturbable fields (nominal, lower_dev, upper_dev, position_tol);
    # fastener has 3 (no position_tol).
    assert rng_aliased.calls == 4 + 3, (
        "aliased hole_a/hole_b must be perturbed exactly once (shared object), "
        f"got {rng_aliased.calls} draws"
    )
    assert rng_control.calls == 4 + 4 + 3, (
        "distinct hole_a/hole_b must each be perturbed independently, "
        f"got {rng_control.calls} draws"
    )


def test_min_max_abs_margin_report_actual_extremes_of_tested_set():
    """StabilityResult.min_abs_margin/max_abs_margin must report the actual
    smallest/largest |margin| among the TESTED (non-excluded) mates, not
    some other value (e.g. across all mates including excluded ones, or a
    placeholder). Uses distinct, hand-computable margins so the extremes
    are unambiguous.

    `_mate` uses the SAME hole dict for hole_a and hole_b, so per-part
    (B-3) floating reduces to margin = min(H-F-T, H-F-T) = H-F-T, with
    H - F = 8.5 - 8.0 = 0.5:
      position_tol=0.05 -> margin = 0.5-0.05 = 0.45
      position_tol=0.10 -> margin = 0.5-0.10 = 0.40
      position_tol=0.20 -> margin = 0.5-0.20 = 0.30
    With epsilon=1e-6, the exclusion band is 2e-6, so none of these
    (margins 0.3-0.45) are anywhere near excluded.
    """
    mates = [_mate(t) for t in (0.05, 0.10, 0.20)]
    result = verdict_stability(mates, epsilon=1e-6, seed=0)
    assert result.tested == 3
    assert result.excluded == 0
    assert result.min_abs_margin == pytest.approx(0.3)
    assert result.max_abs_margin == pytest.approx(0.45)


def test_min_max_abs_margin_none_when_all_excluded():
    """When every mate falls inside the boundary band (tested == 0), there
    is no tested margin to report, so both fields must be None rather than
    some misleading numeric placeholder (e.g. 0.0, which would look like a
    real, vanishingly small margin).
    """
    mates = [_mate(0.5)]  # margin = 0, excluded under epsilon=1e-3
    result = verdict_stability(mates, epsilon=1e-3, seed=0)
    assert result.tested == 0
    assert result.min_abs_margin is None
    assert result.max_abs_margin is None


def test_iso_fit_mate_is_rejected():
    """C2: iso_fit (Tier 2) mates must be rejected, not silently scored stable.

    Tier 2 margin is a Monte Carlo clearance yield in [0, 1], not millimetres,
    and iso_fit mates have no perturbable sub-dicts (nominal/designation/n/seed
    are top-level scalars), so _perturb would be a provable no-op on them.
    verdict_stability must raise rather than half-support this case.
    """
    mate = {"type": "iso_fit", "nominal": 20.0, "designation": "H7/p6",
            "n": 1_000, "seed": 0}
    with pytest.raises(ValueError, match="Tier 1"):
        verdict_stability([mate], epsilon=1e-6, seed=0)


# --- Mutation-score triage additions (cosmic-ray, 2026-08-01) -----------------
#
# These target arithmetic/boundary/structural mutants that the behavioural
# tests above never exercised: the exact BOUNDARY_BAND multiplier (as opposed
# to some other combining operator), the strict "<" boundary edge, the exact
# ratio (as opposed to a floor division that happens to still land in [0,1)
# for the existing positive-control test), a verdict flipping fail->pass
# specifically, StabilityResult's immutability, and continue-vs-break in the
# exclusion loop.


def test_boundary_band_multiplies_not_mods_epsilon():
    """BOUNDARY_BAND * epsilon must scale the exclusion threshold; a `%`
    substitute gives an unrelated (usually much smaller) value. epsilon=0.7
    -> correct band=1.4, mod-mutant band=2.0%0.7=0.6. margin=-1.0 (|margin|=
    1.0) sits inside the correct band but outside the mutant's.
    """
    mate = _mate(1.5)  # margin = 0.5 - 1.5 = -1.0
    result = verdict_stability([mate], epsilon=0.7, seed=0)
    assert result.tested == 0
    assert result.excluded == 1


def test_boundary_band_constant_is_two_not_one():
    """Pins BOUNDARY_BAND's actual value (2.0), not just the multiplication
    operator. epsilon=0.1 -> band=0.2 if BOUNDARY_BAND=2.0, 0.1 if it were
    1.0. margin=0.15 falls inside the first, outside the second.
    """
    mate = _mate(0.35)  # margin = 0.5 - 0.35 = 0.15
    result = verdict_stability([mate], epsilon=0.1, seed=0)
    assert result.tested == 0
    assert result.excluded == 1


def test_boundary_band_edge_is_tested_not_excluded():
    """|margin| exactly equal to the exclusion threshold must be TESTED
    (strict `<`), not excluded; a `<=` mutant would wrongly exclude it.
    epsilon=0.1 -> band=0.2; margin=0.2 exactly.
    """
    mate = _mate(0.3)  # margin = 0.5 - 0.3 = 0.2
    result = verdict_stability([mate], epsilon=0.1, seed=0)
    assert result.tested == 1
    assert result.excluded == 0


def test_excluded_mate_does_not_short_circuit_remaining_mates():
    """The exclusion loop uses `continue`, not `break`: an excluded mate
    must only be skipped, not abandon every mate after it in the list.
    """
    mates = [_mate(0.5), _mate(0.05)]  # first excluded (margin=0), second tested
    result = verdict_stability(mates, epsilon=1e-3, seed=0)
    assert result.excluded == 1
    assert result.tested == 1


def test_stability_result_is_immutable():
    mates = [_mate(0.05)]
    result = verdict_stability(mates, epsilon=1e-6, seed=0)
    assert isinstance(result, StabilityResult)
    with pytest.raises(AttributeError):
        result.value = 0.0


def test_stability_value_is_a_true_ratio_not_a_floor_division(monkeypatch):
    """stable/tested must be an exact ratio. A `//` substitute rounds every
    non-full-stability case down to 0 for these small integer counts, which
    the existing positive-control test cannot catch (it only asserts
    0.0 <= value < 1.0, and floor-division's 0 satisfies that too). Forces
    exactly stable=1, tested=2 (ratio 0.5) via a fake `check`, independent
    of the perturbation's randomness.
    """
    import tolcad.reliability as mod

    calls = {"n": 0}

    def fake_check(mate):
        calls["n"] += 1
        # Call order: mate1-base, mate1-perturbed, mate2-base, mate2-perturbed.
        # mate1 is stable (True both times); mate2 flips (True then False).
        idx = calls["n"]
        if idx in (1, 2):
            return Verdict(assembles=True, margin=10.0, method="x", detail={})
        return Verdict(assembles=(idx == 3), margin=10.0, method="x", detail={})

    monkeypatch.setattr(mod, "check", fake_check)
    mates = [
        {"type": "virtual_condition", "pin": {}, "hole": {}},
        {"type": "virtual_condition", "pin": {}, "hole": {}},
    ]
    result = mod.verdict_stability(mates, epsilon=1e-6, seed=0)
    assert result.tested == 2
    assert result.value == pytest.approx(0.5)


def test_stability_counts_a_fail_to_pass_flip_as_unstable(monkeypatch):
    """A verdict flipping from fail(base) to pass(perturbed) must count as
    UNSTABLE. `perturbed.assembles == base.assembles` correctly reports
    False (unstable) for False->True; a `>=` substitute (treating bool as
    0/1) wrongly reports True>=False as True (stable) -- the one direction
    of flip a `>=` mutant gets backwards.
    """
    import tolcad.reliability as mod

    calls = {"n": 0}

    def fake_check(mate):
        calls["n"] += 1
        # base (call 1) = False (fails); perturbed (call 2) = True (passes).
        return Verdict(assembles=(calls["n"] == 2), margin=10.0, method="x", detail={})

    monkeypatch.setattr(mod, "check", fake_check)
    mate = {"type": "virtual_condition", "pin": {}, "hole": {}}
    result = mod.verdict_stability([mate], epsilon=1e-6, seed=0)
    assert result.tested == 1
    assert result.value == pytest.approx(0.0)


# --- Equivalent mutants (documented, not killed) ------------------------------
#
# 1. `stability_value = 1.0 if tested <= 0 else ...` in place of
#    `if tested == 0 else ...`. `tested` is a counter initialised to 0 and
#    only ever incremented, so it can never go negative; given that
#    invariant, `tested <= 0` and `tested == 0` are the same predicate.
#
# 2. `check(_perturb(...)).assembles is base.assembles` in place of
#    `== base.assembles`. Both sides are Python `bool`, and CPython
#    guarantees `True`/`False` are process-wide singletons -- there are only
#    ever two bool objects in existence, so `is`/`is not` and `==`/`!=`
#    agree on every bool comparison. There is no pair of bools for which
#    they could disagree.
