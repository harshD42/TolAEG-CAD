### Task 11: Gate A report script

**Files:**
- Create: `scripts/gate_a.py`
- Test: `tests/test_gate_a.py`

**Interfaces:**
- Consumes: pytest results, `validation.tolanalyst.agreement`
- Produces: `scripts/gate_a.py` CLI printing a per-criterion pass/fail table and exiting non-zero on any failure

This script is how "did we clear Gate A?" gets answered with evidence rather than
narrative. The TolAnalyst criterion is reported as SKIPPED when no export file is
present, so the script runs without a SolidWorks license — but Gate A is only
**cleared** when it is present and passing.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gate_a.py
import subprocess
import sys
import pathlib

REPO = pathlib.Path(__file__).parent.parent


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
        "Y14.5 worked examples",
        "TolAnalyst agreement",
        "Monte Carlo convergence",
        "Validation isolation",
    ]:
        assert criterion in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gate_a.py -v`
Expected: FAIL — `scripts/gate_a.py` does not exist, stdout is empty

- [ ] **Step 3: Write the script**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_gate_a.py -v`
Expected: PASS, 2 tests

- [ ] **Step 5: Run the full suite and the gate**

Run: `pytest -v && python scripts/gate_a.py`
Expected: all tests pass; Gate A reports NOT CLEARED with TolAnalyst SKIP. That is the
correct state at the end of this plan — the oracle comparison needs the Phase 3 generator.

- [ ] **Step 6: Commit**

```bash
git add scripts/gate_a.py tests/test_gate_a.py
git commit -m "feat: Gate A report script"
```

---

