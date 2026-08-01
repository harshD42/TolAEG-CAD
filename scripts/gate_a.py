#!/usr/bin/env python
"""Gate A report. Thresholds are pre-registered in the design spec, section 7.

Exits 0 only when every criterion passes. A skipped criterion is not a pass.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

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
        # margin = (8.5-8.0)+(8.5-8.0) - (0.5+0.49965) = 1.0 - 0.99965 = +3.5e-4
        "type": "floating_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.5},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.49965},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    },
    {
        # margin = (8.5-8.0)+(8.5-8.0) - (0.5+0.50035) = 1.0 - 1.00035 = -3.5e-4
        "type": "floating_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.5},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.50035},
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
_RELIABILITY_SEED = 20260731


def _pytest_passes(target: str) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q"],
        cwd=REPO, capture_output=True, text=True,
    )
    return result.returncode == 0


def _marker_present(path: pathlib.Path, marker: str) -> bool:
    return marker in path.read_text(encoding="utf-8")


def _format_margin_band(stability: StabilityResult) -> str:
    """Render the tested |margin| range for the reliability report row.

    This is what makes the reliability measurement auditable: it tells a
    reader which band of margins the stability metric actually probed. When
    every mate was excluded (tested == 0) there is no range to report, so a
    distinct, non-numeric fallback string is used instead of e.g. formatting
    None as a number.
    """
    if stability.tested:
        return f"|margin| in [{stability.min_abs_margin:.2e}, {stability.max_abs_margin:.2e}]"
    return "no mates outside the exclusion band"


def main() -> int:
    rows: list[tuple[str, str, str]] = []
    passes: list[bool] = []

    def record(name: str, ok: bool | None, note: str) -> None:
        rows.append((name, {True: "PASS", False: "FAIL", None: "SKIP"}[ok], note))
        passes.append(ok is True)

    # Renamed from "Y14.5 worked examples": these tests are arithmetic derived
    # from the same two unverified formulas the implementation uses, so a PASS
    # here cannot falsify the underlying premise. It is self-consistency, not
    # standard verification. See "Y14.5 citation verified" below for the
    # actual standard-verification status.
    record("Y14.5 self-consistency", _pytest_passes("tests/test_y14_5.py"),
           "100% required; NOT standard-verified (see Y14.5 citation verified)")

    # Monte Carlo convergence depends on the ISO 286 tables (fit_from_designation),
    # so its PASS is only meaningful if the ISO 286 module (including its
    # transcription guard) is also exercised.
    record(
        "Monte Carlo convergence",
        _pytest_passes("tests/test_convergence.py") and _pytest_passes("tests/test_iso286.py"),
        "+/-0.5% at N=100k",
    )

    reliability_tests_pass = _pytest_passes("tests/test_reliability.py")
    stability = verdict_stability(
        _RELIABILITY_MATES, epsilon=_RELIABILITY_EPSILON, seed=_RELIABILITY_SEED
    )
    reliability_ok = reliability_tests_pass and stability.value >= RELIABILITY_THRESHOLD
    band = _format_margin_band(stability)
    record(
        "Checker reliability",
        reliability_ok,
        f"measured {stability.value:.4f} (tested={stability.tested}, "
        f"excluded={stability.excluded}, tested {band}); "
        f"threshold {RELIABILITY_THRESHOLD}",
    )

    record("Validation isolation", _pytest_passes("tests/test_architecture.py"),
           "no core imports")

    # These two rows are unfalsifiable pass conditions until a human checks the
    # transcribed values against the actual published standards. They must
    # read SKIP for as long as the pending-citation markers remain in source.
    citation_pending = _marker_present(Y14_5_SRC, CITATION_PENDING_MARKER)
    record(
        "Y14.5 citation verified",
        None if citation_pending else True,
        "CITATION PENDING HUMAN VERIFICATION marker present in y14_5.py"
        if citation_pending else "citation verified against standard",
    )

    iso286_pending = _marker_present(ISO286_SRC, ISO286_PLACEHOLDER_MARKER)
    record(
        "ISO 286 transcription verified",
        None if iso286_pending else True,
        "placeholder 'replace this line' present in iso286.py docstring"
        if iso286_pending else "transcription verified against standard",
    )

    # Oracles: populated in Phase 3, when generated geometry can feed both engines.
    for name, path, load_fn, agreement_fn, threshold in (
        ("NIST PMI conformance", NIST_EXPECTED, nist_pmi.load_expected, nist_pmi.agreement, 1.00),
        ("TolAnalyst agreement", TOLANALYST_EXPORT, tolanalyst.load_verdicts, tolanalyst.agreement, AGREEMENT_THRESHOLD),
    ):
        if not path.exists():
            record(name, None, f"no export at {path.name}")
            continue
        expected = load_fn(path)
        ours: dict[str, bool] = {}  # Phase 3: populate once generated geometry feeds both engines
        try:
            value = agreement_fn(ours, expected)
        except ValueError as exc:
            record(name, False, f"our verdict set is empty (Phase 3 not wired up): {exc}")
            continue
        record(name, value >= threshold, f"agreement {value:.4f} (>= {threshold})")

    # Spec section 7, criterion 7: "Fresh clone, no SW license, full pipeline runs
    # end-to-end". This requires an actual clean-clone CI run to verify honestly;
    # a pass claimed from inside the current (already-configured) checkout would
    # not establish it.
    record(
        "Fresh clone pipeline",
        None,
        "requires a clean-clone CI run to verify honestly; not checked in-process",
    )

    width = max(len(r[0]) for r in rows)
    print("\nGate A - checker correctness (blocking)\n")
    for name, status, note in rows:
        print(f"  {name:<{width}}  {status:<5}  {note}")

    cleared = all(passes)
    print(f"\nGate A: {'CLEARED' if cleared else 'NOT CLEARED'}\n")
    return 0 if cleared else 1


if __name__ == "__main__":
    raise SystemExit(main())
