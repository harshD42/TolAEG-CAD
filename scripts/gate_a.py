#!/usr/bin/env python
"""Gate A report. Thresholds are pre-registered in the design spec, section 7.

Exits 0 only when every criterion passes. A skipped criterion is not a pass.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).parent.parent
NIST_EXPECTED = REPO / "data" / "nist_pmi_expected.csv"
TOLANALYST_EXPORT = REPO / "data" / "tolanalyst_verdicts.csv"
AGREEMENT_THRESHOLD = 0.95  # pre-registered, DO NOT LOOSEN


def _pytest_passes(target: str) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q"],
        cwd=REPO, capture_output=True, text=True,
    )
    return result.returncode == 0


def main() -> int:
    rows: list[tuple[str, str, str]] = []
    passes: list[bool] = []

    def record(name: str, ok: bool | None, note: str) -> None:
        rows.append((name, {True: "PASS", False: "FAIL", None: "SKIP"}[ok], note))
        passes.append(ok is True)

    record("Y14.5 worked examples", _pytest_passes("tests/test_y14_5.py"),
           "100% required")
    record("Monte Carlo convergence", _pytest_passes("tests/test_convergence.py"),
           "+/-0.5% at N=100k")
    record("Checker reliability", _pytest_passes("tests/test_reliability.py"),
           ">=0.95 verdict stability")
    record("Validation isolation", _pytest_passes("tests/test_architecture.py"),
           "no core imports")

    # Oracles: populated in Phase 3, when generated geometry can feed both engines.
    for name, path, threshold in (
        ("NIST PMI conformance", NIST_EXPECTED, 1.00),
        ("TolAnalyst agreement", TOLANALYST_EXPORT, AGREEMENT_THRESHOLD),
    ):
        if not path.exists():
            record(name, None, f"no export at {path.name}")
            continue
        record(name, False, "harness ready; comparison runs in Phase 3")

    width = max(len(r[0]) for r in rows)
    print("\nGate A - checker correctness (blocking)\n")
    for name, status, note in rows:
        print(f"  {name:<{width}}  {status:<5}  {note}")

    cleared = all(passes)
    print(f"\nGate A: {'CLEARED' if cleared else 'NOT CLEARED'}\n")
    return 0 if cleared else 1


if __name__ == "__main__":
    raise SystemExit(main())
