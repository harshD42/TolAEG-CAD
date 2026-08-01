#!/usr/bin/env python
"""Gate A report. Thresholds are pre-registered in the design spec, section 7.

Exits 0 only when every criterion passes. A skipped criterion is not a pass.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).parent.parent
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

    ok = _pytest_passes("tests/test_y14_5.py")
    rows.append(("Y14.5 worked examples", "PASS" if ok else "FAIL", "100% required"))

    ok_conv = _pytest_passes("tests/test_convergence.py")
    rows.append(
        ("Monte Carlo convergence", "PASS" if ok_conv else "FAIL", "+/-0.5% at N=100k")
    )

    ok_iso = _pytest_passes("tests/test_architecture.py")
    rows.append(("Validation isolation", "PASS" if ok_iso else "FAIL", "no core imports"))

    if TOLANALYST_EXPORT.exists():
        from validation.tolanalyst import agreement, load_verdicts

        theirs = load_verdicts(TOLANALYST_EXPORT)
        # Populated in Phase 3 once the generator can produce matching assemblies.
        ours: dict[str, bool] = {}
        try:
            score = agreement(ours, theirs)
            ok_tol = score >= AGREEMENT_THRESHOLD
            rows.append(
                ("TolAnalyst agreement", "PASS" if ok_tol else "FAIL", f"{score:.1%}")
            )
        except ValueError as exc:
            ok_tol = False
            rows.append(("TolAnalyst agreement", "FAIL", str(exc)))
    else:
        ok_tol = False
        rows.append(
            ("TolAnalyst agreement", "SKIP", f"no export at {TOLANALYST_EXPORT.name}")
        )

    width = max(len(r[0]) for r in rows)
    print("\nGate A — checker correctness (blocking)\n")
    for name, status, note in rows:
        print(f"  {name:<{width}}  {status:<5}  {note}")

    cleared = all([ok, ok_conv, ok_iso, ok_tol])
    print(f"\nGate A: {'CLEARED' if cleared else 'NOT CLEARED'}\n")
    return 0 if cleared else 1


if __name__ == "__main__":
    raise SystemExit(main())
