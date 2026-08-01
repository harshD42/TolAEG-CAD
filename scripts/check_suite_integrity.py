#!/usr/bin/env python
"""Suite integrity: detect tests that cannot fail.

NOT a research gate. CLAUDE.md freezes Gate A/B/C/D; this is separate and
scripts/gate_a.py is untouched. See
docs/superpowers/specs/2026-08-01-suite-integrity-design.md

Layer 1 (here): branch coverage over the checker core -- a branch no test
enters cannot fail. Layer 2 (added in the next task): mutation score.
Layer 3 lives in tests/ and runs in every pytest invocation.

Usage: python scripts/check_suite_integrity.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CORE_MODULES = ("types", "y14_5", "iso286", "montecarlo", "checker", "reliability")

CORE_TEST_SUBSET = [f"tests/test_{name}.py" for name in CORE_MODULES]

# MEASURED, not chosen. A floor pinned at a round number is not a measurement,
# and this project's drift class is precisely a threshold that stops tracking
# what it bounds.
#
# Measured 91.64% TOTAL branch coverage on 2026-08-01 via the exact
# run_coverage() invocation below (233 stmts / 15 miss / 90 branch / 12 partial;
# checker 100.00%, reliability 98.53%, types 91.84%, iso286 88.89%,
# y14_5 87.34%, montecarlo 85.19%).
#
# *** SCOPE, AND WHY IT MATTERS. *** The measurement omits src/tolcad/gen/ via
# [tool.coverage.run] omit in pyproject.toml -- see the comment there, which is
# the canonical explanation. In short: gen/ is deliberately outside Layer 1 and
# Layer 2 (design spec non-goals), so its ~222 never-exercised statements were
# pure denominator. With them in scope the TOTAL measured 48%, which meant core
# coverage could HALVE and still clear the floor: a floor that cannot fail,
# shipped inside the layer built to catch metrics that cannot fail. If someone
# removes the omit, this constant becomes meaningless again -- though not
# silently: the measurement would drop to ~48%, far below this floor, and the
# gate would fail loudly rather than quietly stop measuring anything.
#
# Raising this pin is routine. LOWERING it requires a recorded reason here,
# because a silently lowered floor is itself an instance of the drift class.
COVERAGE_FLOOR = 91.64  # measured 2026-08-01, gen/ omitted; see note above


def run_coverage() -> tuple[float, bool]:
    """Branch coverage over the six core modules. Returns (measured, ok)."""
    proc = subprocess.run(
        [
            sys.executable, "-m", "pytest", *CORE_TEST_SUBSET,
            "-q", "--no-header", "-p", "no:cacheprovider", "-m", "not slow",
            "--cov=src/tolcad", "--cov-branch", "--cov-report=term",
        ],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    match = re.search(r"^TOTAL\s+.*?(\d+(?:\.\d+)?)%", proc.stdout, re.MULTILINE)
    if match is None:
        raise RuntimeError(
            "could not parse coverage output; refusing to report a number "
            f"that was not measured.\n{proc.stdout[-2000:]}"
        )
    measured = float(match.group(1))
    return measured, measured >= COVERAGE_FLOOR


def _print_report(rows: list[tuple[str, str, str, bool]]) -> None:
    print("Suite integrity - tests that cannot fail (non-blocking for Gate A)")
    print()
    for name, measured, threshold, ok in rows:
        status = "PASS" if ok else "FAIL"
        print(f"  {name:<34} {status:<6} {measured} (floor {threshold})")
    print()


def main(argv: list[str]) -> int:
    rows: list[tuple[str, str, str, bool]] = []

    if "--self-test-failure" in argv:
        # Covers this script's own nonzero-exit path. Without it that branch
        # would be untested -- the exact defect Layer 1 exists to catch.
        rows.append(("Self-test (synthetic failure)", "n/a", "n/a", False))
    else:
        measured, ok = run_coverage()
        rows.append(
            ("Core branch coverage", f"{measured:.2f}%", f"{COVERAGE_FLOOR:.2f}%", ok)
        )

    _print_report(rows)
    failed = [name for name, _, _, ok in rows if not ok]
    if failed:
        print(f"Suite integrity: FAILED ({', '.join(failed)})")
        return 1
    print("Suite integrity: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
