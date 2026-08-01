import subprocess
import sys
import pathlib

import pytest

REPO = pathlib.Path(__file__).parent.parent

sys.path.insert(0, str(REPO))
from scripts.gate_a import (  # noqa: E402
    RELIABILITY_SEEDS,
    RELIABILITY_THRESHOLD,
    _aggregate_reliability,
    _format_margin_band,
    _RELIABILITY_EPSILON,
    _RELIABILITY_MATES,
)
from tolcad.reliability import StabilityResult, verdict_stability  # noqa: E402


def test_gate_a_script_runs_without_solidworks_export():
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert "TolAnalyst agreement" in result.stdout
    assert "SKIP" in result.stdout
    # Missing oracle means Gate A is not cleared.
    assert result.returncode != 0


def test_gate_a_reports_every_criterion():
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    for criterion in [
        "Y14.5 self-consistency",
        "TolAnalyst agreement",
        "Monte Carlo convergence",
        "Validation isolation",
    ]:
        assert criterion in result.stdout


def test_gate_a_reports_v2_criteria():
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    for criterion in [
        "Y14.5 self-consistency",
        "NIST PMI conformance",
        "TolAnalyst agreement",
        "Monte Carlo convergence",
        "Checker reliability",
        "Validation isolation",
    ]:
        assert criterion in result.stdout, f"missing criterion: {criterion}"


def test_gate_a_not_cleared_without_oracles():
    """Missing oracles must never count as passes."""
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert "NOT CLEARED" in result.stdout
    assert result.returncode != 0


def test_gate_a_reports_final_wave_criteria():
    """C3/C4/I5/I6: the final fix wave added new rows that must not be lost:
    a measured reliability value, the pending-citation guard rows, and the
    fresh-clone criterion from spec section 7.
    """
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    for criterion in [
        "Y14.5 citation verified",
        "ISO 286 transcription verified",
        "Fresh clone pipeline",
    ]:
        assert criterion in result.stdout, f"missing criterion: {criterion}"

    # C3, revised by 2026-08-01e: the reliability row must show the multi-seed
    # aggregate (mean over the pre-registered seed set), not just PASS/FAIL
    # and not a single pinned-seed value.
    assert "mean" in result.stdout

    # C4: these two rows must TRACK their source markers rather than being
    # hardcoded either way. Both citations were verified against the primary
    # standards on 2026-08-01, so both markers are gone and both rows now read
    # PASS. If a marker is ever reintroduced the row must revert to SKIP.
    y14_src = (REPO / "src" / "tolcad" / "y14_5.py").read_text(encoding="utf-8")
    iso_src = (REPO / "src" / "tolcad" / "iso286.py").read_text(encoding="utf-8")
    lines = {ln.strip() for ln in result.stdout.splitlines()}

    def _row(prefix: str) -> str:
        matches = [ln for ln in lines if ln.startswith(prefix)]
        assert len(matches) == 1, f"expected exactly one {prefix!r} row, got {matches}"
        return matches[0]

    y14_expected = "SKIP" if "CITATION PENDING" in y14_src else "PASS"
    iso_expected = "SKIP" if "replace this line" in iso_src else "PASS"
    assert y14_expected in _row("Y14.5 citation verified")
    assert iso_expected in _row("ISO 286 transcription verified")

    # I6: the fresh-clone criterion cannot be checked in-process and must stay SKIP.
    assert "SKIP" in _row("Fresh clone pipeline")


# --- 2026-08-01e: multi-seed reliability aggregate --------------------------
#
# These tests guard against the exact failure mode the amendment describes:
# a reliability row backed by one lucky (or unlucky) seed rather than a
# stable, auditable, pre-registered aggregate.


def test_reliability_seed_set_is_the_full_pre_registered_range():
    """The seed set is 0-199 inclusive, fixed before any seed was run."""
    assert RELIABILITY_SEEDS == tuple(range(200))
    assert len(RELIABILITY_SEEDS) == 200


def test_aggregate_reliability_uses_every_seed_not_one():
    """The aggregate's mean must actually reflect all 200 seeds, not a single one.

    Constructed so the check is falsifiable: computing the aggregate mean by
    hand from the individual per-seed verdict_stability(...).value calls must
    match `_aggregate_reliability`'s reported mean. A single-seed
    implementation (or one that silently only uses seed 0) would fail this
    for any mate set whose per-seed value actually varies.
    """
    aggregate = _aggregate_reliability(
        _RELIABILITY_MATES,
        epsilon=_RELIABILITY_EPSILON,
        seeds=RELIABILITY_SEEDS,
        threshold=RELIABILITY_THRESHOLD,
    )
    assert aggregate.n_seeds == 200

    per_seed_values = [
        verdict_stability(_RELIABILITY_MATES, epsilon=_RELIABILITY_EPSILON, seed=s).value
        for s in RELIABILITY_SEEDS
    ]
    # The per-seed values must not all be identical -- otherwise this test
    # could not distinguish a real aggregate from a single-seed stand-in.
    assert len(set(per_seed_values)) > 1, (
        "per-seed reliability values are all identical; this test cannot "
        "falsify a single-seed implementation with this mate set"
    )
    expected_mean = sum(per_seed_values) / len(per_seed_values)
    assert aggregate.mean == pytest.approx(expected_mean)


def test_fraction_passing_is_consistent_with_per_seed_values():
    """fraction_passing must equal the fraction of INDIVIDUAL seeds whose own
    stability value meets RELIABILITY_THRESHOLD -- computed independently
    here directly from verdict_stability, not by re-reading the aggregate's
    internals.
    """
    aggregate = _aggregate_reliability(
        _RELIABILITY_MATES,
        epsilon=_RELIABILITY_EPSILON,
        seeds=RELIABILITY_SEEDS,
        threshold=RELIABILITY_THRESHOLD,
    )
    per_seed_values = [
        verdict_stability(_RELIABILITY_MATES, epsilon=_RELIABILITY_EPSILON, seed=s).value
        for s in RELIABILITY_SEEDS
    ]
    expected_fraction = sum(v >= RELIABILITY_THRESHOLD for v in per_seed_values) / len(per_seed_values)
    assert aggregate.fraction_passing == pytest.approx(expected_fraction)


def test_aggregate_reliability_reports_mean_ci_and_tested_band():
    """The aggregate's CI must actually bracket the mean, and tested/excluded
    counts (the auditability the amendment requires be kept) must still be
    present and non-negative.
    """
    aggregate = _aggregate_reliability(
        _RELIABILITY_MATES,
        epsilon=_RELIABILITY_EPSILON,
        seeds=RELIABILITY_SEEDS,
        threshold=RELIABILITY_THRESHOLD,
    )
    assert aggregate.ci_low <= aggregate.mean <= aggregate.ci_high
    assert aggregate.tested >= 0
    assert aggregate.excluded >= 0
    assert 0.0 <= aggregate.fraction_passing <= 1.0


def test_gate_a_reliability_row_reports_mean_ci_and_fraction():
    """The printed gate row -- not just the underlying dataclass -- must show
    the mean, its bootstrap CI, and the fraction of seeds individually
    passing, so a reader sees the distribution rather than a point value.
    """
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    lines = [ln for ln in result.stdout.splitlines() if ln.strip().startswith("Checker reliability")]
    assert len(lines) == 1, f"expected exactly one reliability row, got {lines}"
    row = lines[0]

    assert "mean" in row
    assert "pre-registered seeds" in row
    assert "CI" in row
    assert "fraction of seeds" in row
    # The tested/excluded auditability from before this amendment must survive.
    assert "tested=" in row
    assert "excluded=" in row
    assert "|margin|" in row or "no mates outside the exclusion band" in row


def test_gate_a_reliability_criterion_holds_for_the_real_measurement():
    """The reliability row must read PASS because the MEASUREMENT says so.

    Every other reliability test here either monkeypatches the aggregate or
    checks the row's formatting, so none of them is sensitive to the real
    measured value drifting. This one is, and it is the guard the declared
    mutation `reliability-perturbation-tripled` exists to exercise: it closes
    historical instance 4, a Gate A measurement whose headroom was so large
    that no plausible degradation could move it.

    HEADROOM, MEASURED RATHER THAN ASSUMED (2026-08-01, 200 pre-registered
    seeds, 11 tested mates). Scaling the perturbation inside
    `reliability._perturb` by k while leaving the exclusion band at epsilon:

        k=1  mean 0.9982   PASS   (the shipped measurement)
        k=2  mean 0.9518   PASS   (NOT caught -- 0.0018 above the threshold)
        k=3  mean 0.9068   FAIL   (caught)

    So this criterion notices a 3x degradation and does not notice a 2x one.
    That is the honest bound on its sensitivity: roughly 2-3x, not the 1000x
    of the instance it replaces, and not infinite either. If the mate set or
    epsilon changes, re-measure these numbers -- do not carry them forward.

    `tested > 0` is asserted separately: a mean of 1.0 obtained by excluding
    every mate is a vacuous 1.0, not a passing measurement.
    """
    aggregate = _aggregate_reliability(
        _RELIABILITY_MATES,
        epsilon=_RELIABILITY_EPSILON,
        seeds=RELIABILITY_SEEDS,
        threshold=RELIABILITY_THRESHOLD,
    )
    assert aggregate.tested > 0, (
        "every mate fell inside the exclusion band, so the reported value is a "
        "vacuous 1.0 over an empty denominator, not a measurement of anything"
    )
    assert aggregate.mean >= RELIABILITY_THRESHOLD, (
        f"Gate A's reliability criterion is no longer met by the real "
        f"measurement: mean {aggregate.mean:.4f} over {aggregate.n_seeds} "
        f"pre-registered seeds, threshold {RELIABILITY_THRESHOLD}. The "
        f"threshold is pre-registered and must not be loosened to fit."
    )


def test_gate_a_reliability_row_is_fail_when_mean_below_threshold(monkeypatch, capsys):
    """If the mean genuinely falls below RELIABILITY_THRESHOLD, the row must
    read FAIL -- this must not be silently coerced to PASS by the reporting
    layer. Uses a monkeypatched aggregate (not a tuned seed range) so the
    test doesn't depend on ever actually observing a real FAIL run. Calls
    main() in-process (rather than via subprocess) so the monkeypatch, which
    only affects this process, actually takes effect.
    """
    import scripts.gate_a as gate_a_module

    fake_aggregate = gate_a_module.ReliabilityAggregate(
        mean=0.90,
        ci_low=0.85,
        ci_high=0.95,
        fraction_passing=0.80,
        tested=11,
        excluded=1,
        min_abs_margin=3.5e-4,
        max_abs_margin=0.45,
        n_seeds=200,
    )
    monkeypatch.setattr(gate_a_module, "_aggregate_reliability", lambda *a, **k: fake_aggregate)

    gate_a_module.main()
    out = capsys.readouterr().out
    lines = [ln for ln in out.splitlines() if ln.strip().startswith("Checker reliability")]
    assert len(lines) == 1
    assert "FAIL" in lines[0]
