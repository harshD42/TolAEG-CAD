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


def _run_gate_a_stdout() -> str:
    """One Gate A run, stdout only. Gate A exits 1 by design (SKIPs remain)."""
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    return result.stdout


def _row(prefix: str, out: str) -> str:
    """The single report line beginning with `prefix`, stripped.

    `out` is REQUIRED rather than defaulted to a fresh run: each Gate A run
    costs ~2s and re-running per row would silently multiply that, and worse,
    would let two assertions in one test read two different runs.
    """
    matches = [ln.strip() for ln in out.splitlines() if ln.strip().startswith(prefix)]
    assert len(matches) == 1, f"expected exactly one {prefix!r} row, got {matches}"
    return matches[0]


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

    y14_expected = "SKIP" if "CITATION PENDING" in y14_src else "PASS"
    iso_expected = "SKIP" if "replace this line" in iso_src else "PASS"
    assert y14_expected in _row("Y14.5 citation verified", result.stdout)
    assert iso_expected in _row("ISO 286 transcription verified", result.stdout)

    # I6: the fresh-clone criterion cannot be checked in-process and must stay SKIP.
    assert "SKIP" in _row("Fresh clone pipeline", result.stdout)


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

    HEADROOM, RE-MEASURED after the 2026-08-01f mate-set repair (200
    pre-registered seeds, 12 tested mates). Scaling the perturbation inside
    `reliability._perturb` by k while leaving the exclusion band at epsilon:

        k=1  mean 0.9975   PASS   (the shipped measurement)
        k=2  mean 0.9392   FAIL   (caught)
        k=3  mean 0.8950   FAIL   (caught)

    So this criterion now notices a 2x degradation. The previous ledger
    measured k=1 0.9982 / k=2 0.9518 PASS / k=3 0.9068 FAIL over 11 tested
    mates -- 2x slipped through by 0.0018. Restoring the twelfth mate (the one
    that had been silently swallowed by the exclusion band) both lowered the
    k=1 mean and tightened the sensitivity to roughly 2x. That is the honest
    bound: not the 1000x of the instance it replaces, and not infinite either.
    If the mate set or epsilon changes, re-measure these numbers -- do not
    carry them forward.

    The exact composition is pinned two-sided by
    `test_reliability_tested_and_excluded_are_pinned_exactly`. The `tested > 0`
    asserted here is the weaker vacuity guard it supersedes, kept because a
    vacuous 1.0 over an empty denominator is worth naming at the point of use.
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
        tested=12,
        excluded=0,
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


# --- construction rule for the sensitive-band mates (2026-08-01f) ------------
#
# The band a "binding" part is measured against is the TOP of the regime-2
# sensitive band (5*epsilon), not `BOUNDARY_BAND * epsilon` (2e-4), which is the
# band's BOTTOM -- the exclusion threshold. A part parked at exactly 0.0 and a
# part at the intended +3.5e-4 are both inside the sensitive band; only the
# 5*epsilon form sees them both, and seeing both is the whole point.
_SENSITIVE_BAND = 5.0 * _RELIABILITY_EPSILON


def test_every_sensitive_mate_has_exactly_one_binding_part():
    """The construction rule, asserted rather than trusted.

    mate[8] was documented as +3.5e-4 using a SUM, but y14_5 implements B-3's
    per-part min(). Its per-part margins were (0.0, +3.5e-4), so min() gave
    exactly 0.0, the exclusion band swallowed it, and tested silently became 11
    while the frozen spec claimed 12. mate[9] had the same zero part and
    survived only because min() picked its negative branch.

    CONSTRUCTION RULE: each sensitive-band mate has exactly ONE binding part at
    +-3.5e-4; every other part in that mate is slack at >=10x the band. A mate
    with no part in the band at all is a regime-1 (far-from-boundary) mate and
    is not governed by the rule.
    """
    import scripts.gate_a as mod
    from tolcad.checker import check

    band = _SENSITIVE_BAND
    for i, mate in enumerate(mod._RELIABILITY_MATES):
        detail = check(mate).detail
        parts = [detail.get("margin_a"), detail.get("margin_b")]
        parts = [p for p in parts if p is not None]
        if not parts:
            continue  # single-expression mate; nothing to balance
        binding = [p for p in parts if abs(p) <= band]
        if not binding:
            continue  # regime 1: far from the boundary, rule does not apply
        assert len(binding) == 1, (
            f"mate[{i}] has {len(binding)} parts inside the sensitive band "
            f"{band:.2e} (margins {parts}); the construction rule requires "
            f"exactly one binding part, every other slack at >=10x"
        )
        # ...and the other half of the rule: every non-binding part slack at
        # >=10x. The mates are constructed at EXACTLY 10x (3.5e-4 -> 3.5e-3),
        # which in binary floating point lands a few ulp under the exact ratio,
        # so the comparison carries a relative tolerance rather than being
        # written as a bare `>=` that the construction itself would fail.
        slack = [p for p in parts if abs(p) > band]
        assert all(abs(p) >= 10.0 * abs(binding[0]) * (1.0 - 1e-9) for p in slack), (
            f"mate[{i}] has a non-binding part closer than 10x the binding "
            f"part {binding[0]:.2e} (margins {parts})"
        )


def test_reliability_tested_and_excluded_are_pinned_exactly():
    """O-C: an instrument-composition quantity, pinned two-sided.

    `tested > 0` catches TOTAL degeneracy and missed the PARTIAL degeneracy that
    lived underneath it for four ledgers. Pin the exact composition.
    """
    import scripts.gate_a as mod

    aggregate = mod._aggregate_reliability(
        mod._RELIABILITY_MATES,
        epsilon=mod._RELIABILITY_EPSILON,
        seeds=mod.RELIABILITY_SEEDS,
        threshold=mod.RELIABILITY_THRESHOLD,
    )
    assert aggregate.tested == 12, (
        f"tested={aggregate.tested}, expected 12. A mate has fallen into the "
        f"exclusion band -- check the per-part margins against the construction rule."
    )
    assert aggregate.excluded == 0


# --- 2026-08-01g: measured vs. attested, and criterion 1 restored ------------


def test_gate_a_distinguishes_measured_rows_from_attested_ones():
    """Two rows PASS because a marker string is absent from source. That is a
    human attestation, not a measurement, and 6 PASS must not read as six."""
    out = _run_gate_a_stdout()
    assert "PASS(attested)" in out, (
        "attested rows must be labelled; otherwise a reader counts them as "
        "measurements"
    )
    for attested in ("Y14.5 citation verified", "ISO 286 transcription verified"):
        line = _row(attested, out)
        assert "attested" in line, f"{attested} is an attestation and must say so"


def test_criterion_one_is_restored_as_its_own_measured_row():
    """Spec section 7 criterion 1 is agreement with PUBLISHED worked examples.

    gate_a renamed it to "self-consistency" and noted that is arithmetic derived
    from the same unverified formulas -- so the published-examples criterion was
    reported by nothing. The three examples ARE encoded; point the row at them.
    """
    line = _row("Y14.5 published worked examples", _run_gate_a_stdout())
    assert "PASS" in line and "measured" in line


def test_the_criterion_one_node_ids_exist_and_pass():
    """ANTI-VACUITY for the row above.

    The criterion-1 row is only worth its label if the selectors it names
    actually resolve to the three published worked examples. Collect them by
    exact node ID and require all three to run and pass: a renamed or deleted
    test would make pytest exit 4 or 5 here, naming which selector went stale,
    instead of leaving the Gate A row to report a bare FAIL with no diagnosis.
    """
    from scripts.gate_a import _Y14_5_WORKED_EXAMPLE_TESTS

    assert len(_Y14_5_WORKED_EXAMPLE_TESTS) == 3, (
        "ASME Y14.5-2018 Appendix B prints three worked examples (B-3; B-4; "
        "B-4 unequal split); criterion 1 must name all three"
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *_Y14_5_WORKED_EXAMPLE_TESTS, "-q", "--no-header"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"criterion 1's node IDs did not all collect and pass "
        f"(pytest exit {result.returncode}):\n{result.stdout}\n{result.stderr}"
    )
    assert "3 passed" in result.stdout, (
        f"expected exactly 3 tests to run, got:\n{result.stdout}"
    )


def test_the_attested_rows_print_their_evidence():
    """An attestation with no provenance is just a green word.

    A reader must be able to check WHO attested, WHEN, and against WHICH
    edition and table, without leaving the report.
    """
    out = _run_gate_a_stdout()
    y14 = _row("Y14.5 citation verified", out)
    iso = _row("ISO 286 transcription verified", out)
    for fragment in ("Harsh Dwivedi", "2026-08-01", "ASME Y14.5-2018", "Appendix B"):
        assert fragment in y14, f"Y14.5 attestation omits {fragment!r}: {y14}"
    for fragment in ("Harsh Dwivedi", "2026-08-01", "ISO 286-1:2010", "Table 1"):
        assert fragment in iso, f"ISO 286 attestation omits {fragment!r}: {iso}"


def test_the_tally_states_the_measured_attested_split():
    """The headline count is where the misreading happened, so fix it there.

    "6 PASS / 3 SKIP" invited the reader to count six measurements. The tally
    line must state the split, and it must agree with the rows above it.
    """
    out = _run_gate_a_stdout()
    tally = [ln.strip() for ln in out.splitlines() if " PASS (" in ln and "attested)" in ln]
    assert len(tally) == 1, f"expected exactly one tally line, got {tally}"

    row_lines = [
        ln for ln in out.splitlines()
        if ln.startswith("  ") and ("PASS(" in ln or "FAIL(" in ln or "SKIP(" in ln)
    ]
    measured = sum(1 for ln in row_lines if "PASS(measured)" in ln)
    attested = sum(1 for ln in row_lines if "PASS(attested)" in ln)
    skipped = sum(1 for ln in row_lines if "SKIP(" in ln)
    assert f"{measured + attested} PASS ({measured} measured, {attested} attested)" in tally[0]
    assert f"{skipped} SKIP" in tally[0]

    # And the split must be non-degenerate in both directions -- a tally that
    # said "7 measured, 0 attested" would have re-created the original defect.
    assert measured > 0 and attested > 0


def test_every_gate_a_row_declares_a_kind():
    """No row may print a bare PASS/FAIL/SKIP. `record` asserts this, but the
    assertion is only reached if `record` is actually called -- this checks the
    rendered output, which is what a reader sees.
    """
    out = _run_gate_a_stdout()
    body = out.split("Gate A - checker correctness (blocking)", 1)[1]
    body = body.split("Gate A:", 1)[0]
    for ln in body.splitlines():
        if not ln.startswith("  ") or not ln.strip():
            continue
        if " PASS (" in ln:  # the tally line, checked separately
            continue
        assert any(f"{word}({kind})" in ln for word in ("PASS", "FAIL", "SKIP")
                   for kind in ("measured", "attested")), (
            f"report line declares no evidence kind: {ln!r}"
        )
