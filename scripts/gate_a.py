#!/usr/bin/env python
"""Gate A report. Thresholds are pre-registered in the design spec, section 7.

Exits 0 only when every criterion passes. A skipped criterion is not a pass.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
from dataclasses import dataclass

import numpy as np

REPO = pathlib.Path(__file__).parent.parent

# validation/ is not an installed package (deliberately, so core never depends
# on it). When this script is invoked directly (`python scripts/gate_a.py`),
# sys.path[0] is scripts/, not REPO, so validation would not otherwise import.
sys.path.insert(0, str(REPO))

from tolcad.reliability import StabilityResult, verdict_stability  # noqa: E402
from validation import nist_pmi, tolanalyst  # noqa: E402

NIST_EXPECTED = REPO / "data" / "nist_pmi_expected.csv"
TOLANALYST_EXPORT = REPO / "data" / "tolanalyst_verdicts.csv"
AGREEMENT_THRESHOLD = 0.95  # pre-registered, DO NOT LOOSEN

# Pre-registered in spec section 7: "Checker reliability ... >= 0.95, reported".
RELIABILITY_THRESHOLD = 0.95  # pre-registered, DO NOT LOOSEN

Y14_5_SRC = REPO / "src" / "tolcad" / "y14_5.py"
ISO286_SRC = REPO / "src" / "tolcad" / "iso286.py"
CITATION_PENDING_MARKER = "CITATION PENDING HUMAN VERIFICATION"
ISO286_PLACEHOLDER_MARKER = "replace this line"

# --- 2026-08-01g correction: measured vs. attested ---------------------------
#
# Every row declares which KIND of evidence stands behind it.
#
#   MEASURED  -- something was executed and its result decided the verdict.
#   ATTESTED  -- a human compared this code against a published standard and
#                recorded the outcome. The harness can only read that record
#                (here: the absence of a pending-verification marker in source).
#                It CANNOT re-derive the finding, so an attested PASS is an
#                unfalsifiable pass condition by construction.
#
# Reported inside an undifferentiated "6 PASS", the two attested rows read as
# measurements. They are not, and the tally at the foot of the report now says
# so. Attested rows must also print WHO attested, WHEN, and against WHICH
# edition and table, so the claim is checkable by a reader rather than merely
# asserted by a green word.
MEASURED = "measured"
ATTESTED = "attested"
_KINDS = (MEASURED, ATTESTED)

# Spec section 7's criterion 1 is "Agreement with published Y14.5 worked
# examples (Tier 1)". This harness had silently renamed it to "Y14.5
# self-consistency", whose own note records that it is arithmetic derived from
# the same two unverified formulas the implementation uses -- so criterion 1 was
# reported by nothing.
#
# These three tests encode the three worked examples PRINTED IN THE STANDARD,
# with the standard's own inputs quoted in their docstrings:
#   B-3            F = 6.0, H = 6.44  ->  T = 0.44 per part
#   B-4            F = 6.0, H = 6.44  ->  T = 0.22 per part
#   B-4 unequal    2T = 0.44          ->  T1 = 0.18, T2 = 0.26
# Those numbers come from ASME, not from us, so the self-consistency objection
# does not reach them: our formulas cannot make 6.44 - 6.0 = 0.44 true. Each is
# evaluated at the exact boundary the standard's own arithmetic produces, which
# is the only place a sign or factor error is visible.
#
# If a node ID here is renamed or deleted, pytest exits non-zero (4 for a
# collection error, 5 for nothing collected), so this row FAILs loudly rather
# than passing vacuously. `tests/test_gate_a.py::
# test_the_criterion_one_node_ids_exist_and_pass` pins that they resolve.
_Y14_5_WORKED_EXAMPLE_TESTS = (
    "tests/test_y14_5.py::test_b3_worked_example_boundary_case_assembles",
    "tests/test_y14_5.py::test_b4_worked_example_boundary_case_assembles",
    "tests/test_y14_5.py::test_b4_worked_example_unequal_split_boundary_case_assembles",
)

# The evidence the two attested rows print. Sourced from the commits that
# removed the pending markers, so the attribution is checkable in `git log`
# rather than being a claim this file makes about itself.
Y14_5_ATTESTATION = (
    "ATTESTED by Harsh Dwivedi, 2026-08-01, commit 2562bef: ASME Y14.5-2018 "
    "Nonmandatory Appendix B, sections B-3 and B-4, checked against the primary "
    "text; symbols per B-2.1. NOT a measurement -- this row reads a human record "
    "(the absence of the pending marker) and cannot re-derive the finding"
)
ISO286_ATTESTATION = (
    "ATTESTED by Harsh Dwivedi, 2026-08-01, commit 2562bef: ISO 286-1:2010 "
    "Table 1 (IT grades), Table 4 and Table 5 (shaft deviations), all 117 "
    "IT5-IT8 and H/g/h/k/p values across 13 size bands, checked against the "
    "primary tables; the IT12-IT14 rows were added later the same day from the "
    "same Table 1 in commit 13e3b97. NOT a measurement -- this row reads a "
    "human record (the absence of the placeholder) and cannot re-derive it"
)

# Fixed, seeded set of Tier 1 mates for the reliability measurement below.
#
# This set deliberately spans TWO regimes, per the module docstring in
# tolcad/reliability.py:
#   (1) Far-from-boundary mates (|margin| >> BOUNDARY_BAND * epsilon), where a
#       flip would indicate a genuine bug rather than boundary noise.
#   (2) SENSITIVE-BAND mates, with |margin| between BOUNDARY_BAND * epsilon
#       (the exclusion threshold, currently 2*epsilon) and roughly 5*epsilon.
#       These sit just outside exclusion but well within reach of a
#       perturbation of magnitude epsilon, so a flip here is a real,
#       detectable possibility rather than a tautology. Without band (2),
#       every mate's margin is orders of magnitude larger than the maximum
#       achievable perturbation, so "stability" would trivially measure
#       1.0000 on every seed -- a tautology, not a measurement. See NB-2.
#
# With _RELIABILITY_EPSILON = 1e-4, the exclusion boundary is 2e-4 and the
# targeted sensitive band is roughly [2e-4, 5e-4]. Sensitive-band mates below
# are constructed with margin ~= +-3.5e-4, comfortably inside that band.
#
# CONSTRUCTION RULE (frozen 2026-08-01, spec section 7 correction).
# Each sensitive-band mate has EXACTLY ONE binding part at +-3.5e-4; every other
# part in that mate is slack at >=10x the band. Without this rule the repair is
# under-determined -- two reviewers produced 0.9967 and 0.9971 from different
# constructions of the same stated intent. The rule determines the number.
#
# The rule exists because ASME B-3 (y14_5.py) is PER PART -- the floating-fastener
# margin is min(margin_a, margin_b), never their sum. Two mates below were once
# written as though it were a sum; one of them therefore sat at exactly 0.0, fell
# inside the exclusion band, and was silently dropped (tested=11, excluded=1). The
# rule is asserted, not trusted, by tests/test_gate_a.py::
# test_every_sensitive_mate_has_exactly_one_binding_part.
_RELIABILITY_MATES: list[dict] = [
    # --- far-from-boundary (regime 1) ---
    {
        "type": "virtual_condition",
        "pin": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0, "position_tol": 0.1},
        "hole": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.2},
    },
    {
        "type": "virtual_condition",
        "pin": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0, "position_tol": 0.4},
        "hole": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.2},
    },
    {
        "type": "floating_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.05},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.10},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    },
    {
        "type": "floating_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.90},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.95},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    },
    {
        "type": "fixed_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.05},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.05},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    },
    {
        "type": "fixed_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.40},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.40},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    },
    # --- sensitive band (regime 2): |margin| ~= 3.5e-4, inside [2e-4, 5e-4] ---
    {
        # VC_hole = 8.5 - 0.24965 = 8.25035; VC_pin = 8.0 + 0.25 = 8.25;
        # margin = +3.5e-4 (assembles, just outside the exclusion band).
        "type": "virtual_condition",
        "pin": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0, "position_tol": 0.25},
        "hole": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.24965},
    },
    {
        # VC_hole = 8.5 - 0.25035 = 8.24965; VC_pin = 8.0 + 0.25 = 8.25;
        # margin = -3.5e-4 (fails, just outside the exclusion band).
        "type": "virtual_condition",
        "pin": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0, "position_tol": 0.25},
        "hole": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.25035},
    },
    {
        # B-3 is PER PART: margin = min(H_a-F-T_a, H_b-F-T_b), NOT their sum.
        # Construction rule: exactly one binding part at +3.5e-4; the other slack
        # at >=10x the band. hole_a binds; hole_b is slack.
        #   margin_a = (8.5-8.0) - 0.49965 = +3.5e-4   <- binding
        #   margin_b = (8.5-8.0) - 0.49650 = +3.5e-3   <- slack, 10x
        "type": "floating_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.49965},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.49650},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    },
    {
        # B-3 is PER PART: margin = min(H_a-F-T_a, H_b-F-T_b), NOT their sum.
        #   margin_a = (8.5-8.0) - 0.50035 = -3.5e-4   <- binding
        #   margin_b = (8.5-8.0) - 0.49650 = +3.5e-3   <- slack
        "type": "floating_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.50035},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.49650},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    },
    {
        # margin = (8.5-8.0) - (0.25+0.24965) = 0.5 - 0.49965 = +3.5e-4
        "type": "fixed_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.25},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.24965},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    },
    {
        # margin = (8.5-8.0) - (0.25+0.25035) = 0.5 - 0.50035 = -3.5e-4
        "type": "fixed_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.25},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.25035},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    },
]
_RELIABILITY_EPSILON = 1e-4

# --- 2026-08-01e correction ---------------------------------------------
# A single pinned seed made the reliability PASS a one-shot Bernoulli draw:
# measured across 1000 seeds, verdict_stability on _RELIABILITY_MATES ranges
# 0.8333-1.0000 with mean 0.9896, and 12.2% of seeds land below the 0.95
# threshold. The fix is NOT a different single seed; it is to stop reporting
# a single draw at all. RELIABILITY_SEEDS below is the full pre-registered
# seed set (0-199 inclusive) over which the mean, its bootstrap CI, and the
# fraction of seeds individually clearing the threshold are computed. This
# set was fixed before being run and must not be tuned or narrowed to make
# the mean land on either side of 0.95.
RELIABILITY_SEEDS: tuple[int, ...] = tuple(range(200))  # pre-registered 0-199, DO NOT TUNE

# Percentile-bootstrap resample count for the CI on the mean reliability.
RELIABILITY_BOOTSTRAP_RESAMPLES = 10_000
_BOOTSTRAP_RNG_SEED = 0  # independent of RELIABILITY_SEEDS; only drives the CI


@dataclass(frozen=True)
class ReliabilityAggregate:
    """Aggregate of verdict_stability over the pre-registered seed set.

    mean: mean of the per-seed stability values -- this, not any single
        seed's value, is what is compared against RELIABILITY_THRESHOLD.
    ci_low, ci_high: 95% percentile-bootstrap CI on that mean.
    fraction_passing: fraction of INDIVIDUAL seeds whose own stability value
        meets RELIABILITY_THRESHOLD. Reported alongside the mean so a reader
        can see the distribution, not just a point value; it is diagnostic,
        not itself the pass/fail criterion.
    tested, excluded, min_abs_margin, max_abs_margin: identical across every
        seed by construction (they depend only on the unperturbed mates, not
        on the perturbation draw), carried through unchanged for the
        existing auditability of the tested |margin| band.
    n_seeds: number of seeds aggregated over (len(RELIABILITY_SEEDS)).
    """

    mean: float
    ci_low: float
    ci_high: float
    fraction_passing: float
    tested: int
    excluded: int
    min_abs_margin: float | None
    max_abs_margin: float | None
    n_seeds: int


def _aggregate_reliability(
    mates: list[dict],
    epsilon: float,
    seeds: tuple[int, ...],
    threshold: float,
) -> ReliabilityAggregate:
    """Run verdict_stability once per seed and aggregate the results.

    Reports the MEAN over `seeds` (the PASS/FAIL quantity), a percentile
    bootstrap CI on that mean, and the fraction of individual seeds that
    independently clear `threshold`.
    """
    results = [verdict_stability(mates, epsilon=epsilon, seed=s) for s in seeds]
    values = np.array([r.value for r in results], dtype=float)

    # tested/excluded/margins are a function of the base (unperturbed) mates
    # only, so every seed must agree on them; this is what lets a single
    # tested/excluded/margin-band be reported for the whole aggregate.
    tested = results[0].tested
    excluded = results[0].excluded
    min_abs_margin = results[0].min_abs_margin
    max_abs_margin = results[0].max_abs_margin
    assert all(
        r.tested == tested and r.excluded == excluded for r in results
    ), "tested/excluded must be seed-invariant (they depend only on base margins)"

    mean = float(values.mean())

    rng = np.random.default_rng(_BOOTSTRAP_RNG_SEED)
    resample_idx = rng.integers(0, values.size, size=(RELIABILITY_BOOTSTRAP_RESAMPLES, values.size))
    boot_means = values[resample_idx].mean(axis=1)
    ci_low, ci_high = (float(x) for x in np.percentile(boot_means, [2.5, 97.5]))

    fraction_passing = float((values >= threshold).mean())

    return ReliabilityAggregate(
        mean=mean,
        ci_low=ci_low,
        ci_high=ci_high,
        fraction_passing=fraction_passing,
        tested=tested,
        excluded=excluded,
        min_abs_margin=min_abs_margin,
        max_abs_margin=max_abs_margin,
        n_seeds=len(seeds),
    )


def _pytest_passes(*targets: str) -> bool:
    """True iff pytest exits 0 for every named target, run as one invocation.

    Variadic so a criterion can name individual node IDs rather than a whole
    file. A missing or renamed node ID makes pytest exit 4 (collection error)
    or 5 (nothing collected), both non-zero, so a stale selector reports FAIL
    rather than quietly measuring nothing.
    """
    assert targets, "a criterion that names no test measures nothing"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *targets, "-q"],
        cwd=REPO, capture_output=True, text=True,
    )
    return result.returncode == 0


def _marker_present(path: pathlib.Path, marker: str) -> bool:
    return marker in path.read_text(encoding="utf-8")


def _format_margin_band(stability: StabilityResult | ReliabilityAggregate) -> str:
    """Render the tested |margin| range for the reliability report row.

    This is what makes the reliability measurement auditable: it tells a
    reader which band of margins the stability metric actually probed. When
    every mate was excluded (tested == 0) there is no range to report, so a
    distinct, non-numeric fallback string is used instead of e.g. formatting
    None as a number.

    Accepts either a single-seed StabilityResult or a multi-seed
    ReliabilityAggregate: both expose tested/min_abs_margin/max_abs_margin,
    and for the aggregate those are seed-invariant (see _aggregate_reliability).
    """
    if stability.tested:
        return f"|margin| in [{stability.min_abs_margin:.2e}, {stability.max_abs_margin:.2e}]"
    return "no mates outside the exclusion band"


def main() -> int:
    # (name, ok, kind, note). `kind` is formatted into the status column, so a
    # reader cannot see PASS without also seeing what kind of evidence it rests
    # on. See the MEASURED/ATTESTED note at the top of this file.
    rows: list[tuple[str, bool | None, str, str]] = []
    passes: list[bool] = []

    def record(name: str, ok: bool | None, kind: str, note: str) -> None:
        # `kind` is positional and required: defaulting it to MEASURED would
        # let a future attested row inherit the stronger label by silence,
        # which is the exact defect this correction exists to remove.
        assert kind in _KINDS, f"{name}: kind must be one of {_KINDS}, got {kind!r}"
        rows.append((name, ok, kind, note))
        passes.append(ok is True)

    # Spec section 7, criterion 1: "Agreement with published Y14.5 worked
    # examples (Tier 1) -- 100%, closed-form, must be exact." Restored as its
    # own row by the 2026-08-01g correction; see _Y14_5_WORKED_EXAMPLE_TESTS.
    record(
        "Y14.5 published worked examples",
        _pytest_passes(*_Y14_5_WORKED_EXAMPLE_TESTS),
        MEASURED,
        f"100% required (spec section 7, criterion 1); "
        f"{len(_Y14_5_WORKED_EXAMPLE_TESTS)} worked examples printed in ASME "
        f"Y14.5-2018 Nonmandatory Appendix B, evaluated at the standard's own "
        f"inputs (B-3 F=6.0/H=6.44/T=0.44; B-4 T=0.22; B-4 unequal split "
        f"T1=0.18/T2=0.26)",
    )

    # Renamed from "Y14.5 worked examples": these tests are arithmetic derived
    # from the same two unverified formulas the implementation uses, so a PASS
    # here cannot falsify the underlying premise. It is self-consistency, not
    # standard verification. See "Y14.5 citation verified" below for the
    # actual standard-verification status.
    #
    # 2026-08-01g: KEPT, but demoted to informational. It is a real measurement
    # of a real thing -- the whole Tier 1 suite, which is broader than the three
    # published examples -- so it stays MEASURED; it is simply not one of spec
    # section 7's criteria, and it must not be mistaken for criterion 1 again.
    record("Y14.5 self-consistency", _pytest_passes("tests/test_y14_5.py"),
           MEASURED,
           "INFORMATIONAL, not a spec section 7 criterion: whole Tier 1 suite, "
           "100% required; NOT standard-verified (see Y14.5 citation verified)")

    # Monte Carlo convergence depends on the ISO 286 tables (fit_from_designation),
    # so its PASS is only meaningful if the ISO 286 module (including its
    # transcription guard) is also exercised.
    record(
        "Monte Carlo convergence",
        _pytest_passes("tests/test_convergence.py") and _pytest_passes("tests/test_iso286.py"),
        MEASURED,
        "+/-0.5% at N=100k",
    )

    reliability_tests_pass = _pytest_passes("tests/test_reliability.py")
    aggregate = _aggregate_reliability(
        _RELIABILITY_MATES,
        epsilon=_RELIABILITY_EPSILON,
        seeds=RELIABILITY_SEEDS,
        threshold=RELIABILITY_THRESHOLD,
    )
    # PASS/FAIL is decided on the MEAN over the pre-registered seed set, never
    # on any single seed's value (see the 2026-08-01e correction log entry).
    reliability_ok = reliability_tests_pass and aggregate.mean >= RELIABILITY_THRESHOLD
    band = _format_margin_band(aggregate)
    record(
        "Checker reliability",
        reliability_ok,
        MEASURED,
        f"mean {aggregate.mean:.4f} over {aggregate.n_seeds} pre-registered seeds "
        f"(95% bootstrap CI [{aggregate.ci_low:.4f}, {aggregate.ci_high:.4f}], "
        f"{RELIABILITY_BOOTSTRAP_RESAMPLES} resamples); "
        f"fraction of seeds >= {RELIABILITY_THRESHOLD}: {aggregate.fraction_passing:.4f} "
        f"(tested={aggregate.tested}, excluded={aggregate.excluded}, tested {band}); "
        f"threshold {RELIABILITY_THRESHOLD}",
    )

    record("Validation isolation", _pytest_passes("tests/test_architecture.py"),
           MEASURED,
           "no core imports")

    # These two rows are unfalsifiable pass conditions until a human checks the
    # transcribed values against the actual published standards. They must
    # read SKIP for as long as the pending-citation markers remain in source.
    # 2026-08-01g: they are therefore ATTESTED, not measured, and say so in the
    # status column; a PASS here prints the attestation's provenance.
    citation_pending = _marker_present(Y14_5_SRC, CITATION_PENDING_MARKER)
    record(
        "Y14.5 citation verified",
        None if citation_pending else True,
        ATTESTED,
        "PENDING: CITATION PENDING HUMAN VERIFICATION marker present in y14_5.py"
        if citation_pending else Y14_5_ATTESTATION,
    )

    iso286_pending = _marker_present(ISO286_SRC, ISO286_PLACEHOLDER_MARKER)
    record(
        "ISO 286 transcription verified",
        None if iso286_pending else True,
        ATTESTED,
        "PENDING: placeholder 'replace this line' present in iso286.py docstring"
        if iso286_pending else ISO286_ATTESTATION,
    )

    # Oracles: populated in Phase 3, when generated geometry can feed both engines.
    for name, path, load_fn, agreement_fn, threshold in (
        ("NIST PMI conformance", NIST_EXPECTED, nist_pmi.load_expected, nist_pmi.agreement, 1.00),
        ("TolAnalyst agreement", TOLANALYST_EXPORT, tolanalyst.load_verdicts, tolanalyst.agreement, AGREEMENT_THRESHOLD),
    ):
        if not path.exists():
            record(name, None, MEASURED, f"no export at {path.name}")
            continue
        expected = load_fn(path)
        ours: dict[str, bool] = {}  # Phase 3: populate once generated geometry feeds both engines
        try:
            value = agreement_fn(ours, expected)
        except ValueError as exc:
            record(name, False, MEASURED,
                   f"our verdict set is empty (Phase 3 not wired up): {exc}")
            continue
        record(name, value >= threshold, MEASURED,
               f"agreement {value:.4f} (>= {threshold})")

    # Spec section 7, criterion 7: "Fresh clone, no SW license, full pipeline runs
    # end-to-end". This requires an actual clean-clone CI run to verify honestly;
    # a pass claimed from inside the current (already-configured) checkout would
    # not establish it.
    record(
        "Fresh clone pipeline",
        None,
        MEASURED,
        "requires a clean-clone CI run to verify honestly; not checked in-process",
    )

    verdict_word = {True: "PASS", False: "FAIL", None: "SKIP"}
    statuses = [
        (name, f"{verdict_word[ok]}({kind})", note) for name, ok, kind, note in rows
    ]
    name_width = max(len(s[0]) for s in statuses)
    status_width = max(len(s[1]) for s in statuses)
    print("\nGate A - checker correctness (blocking)\n")
    for name, status, note in statuses:
        print(f"  {name:<{name_width}}  {status:<{status_width}}  {note}")

    # The tally, spelled out. "6 PASS / 3 SKIP" was read as six measurements
    # when two of the six were human attestations; the split is now printed
    # rather than left for a reader to reconstruct from the rows.
    def _count(ok: bool | None, kind: str | None = None) -> int:
        return sum(1 for _, o, k, _ in rows if o is ok and (kind is None or k == kind))

    n_pass, n_fail, n_skip = _count(True), _count(False), _count(None)
    print(
        f"\n  {n_pass} PASS ({_count(True, MEASURED)} measured, "
        f"{_count(True, ATTESTED)} attested), {n_fail} FAIL, {n_skip} SKIP. "
        f"An attested PASS is a human's record of checking this code against a "
        f"published standard; the harness reads that record and cannot re-derive it."
    )

    cleared = all(passes)
    print(f"\nGate A: {'CLEARED' if cleared else 'NOT CLEARED'}\n")
    return 0 if cleared else 1


if __name__ == "__main__":
    raise SystemExit(main())
