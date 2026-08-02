### Task 3: The integrity script and branch coverage

**Files:**
- Create: `scripts/check_suite_integrity.py`
- Modify: `.gitignore`
- Test: `tests/test_suite_integrity_script.py`

**Interfaces:**
- Consumes: nothing from earlier tasks
- Produces: `scripts/check_suite_integrity.py` as a CLI exiting 0 on pass, 1 on failure; `CORE_MODULES` and `COVERAGE_FLOOR` as module constants

Layer 1 catches the *unreachable* class: a branch no test enters cannot fail. The fetcher's mismatch → `exit 1` guard sat uncovered for a whole phase.

- [ ] **Step 1: Write the failing test**

Create `tests/test_suite_integrity_script.py`:

```python
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "check_suite_integrity.py"


def test_the_script_exists():
    assert SCRIPT.is_file()


def test_it_names_the_six_core_modules():
    """Layer 1 and 2 scope. gen/ is deliberately excluded -- CadQuery mutants
    are slow and frequently geometrically meaningless."""
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert set(mod.CORE_MODULES) == {
        "types", "y14_5", "iso286", "montecarlo", "checker", "reliability",
    }


def test_the_coverage_floor_is_a_measured_value_not_a_round_number():
    """A floor pinned at an aspirational round number is not a measurement.

    The project's drift class is exactly this: a threshold that stops tracking
    what it is supposed to bound. Whatever the measured baseline is, it is
    almost certainly not 80 or 90.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert mod.COVERAGE_FLOOR not in (0, 50, 60, 70, 75, 80, 85, 90, 95, 100), (
        f"COVERAGE_FLOOR {mod.COVERAGE_FLOOR} looks aspirational rather than "
        f"measured. Run the script, read the number, pin that."
    )


def test_the_script_reports_and_exits_nonzero_when_a_layer_fails(tmp_path):
    """Exercised via --self-test, which forces one layer to report failure."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--self-test-failure"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert proc.returncode == 1, "a failing layer must exit nonzero"
    assert "FAIL" in proc.stdout
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_suite_integrity_script.py -v`
Expected: FAIL — the script does not exist.

- [ ] **Step 3: Write the script's Layer 1**

Create `scripts/check_suite_integrity.py`:

```python
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

# MEASURED, not chosen. Set from an actual run on 2026-08-01 -- see Step 4.
# A floor pinned at a round number is not a measurement, and this project's
# drift class is precisely a threshold that stops tracking what it bounds.
COVERAGE_FLOOR = 0.0  # replaced in Step 4 with the measured value


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
```

The output shape deliberately mirrors `scripts/gate_a.py` so the two read alike.

- [ ] **Step 4: Measure the baseline and pin it**

Run: `python scripts/check_suite_integrity.py`

Read the measured branch coverage. **Set `COVERAGE_FLOOR` to that measured value**, not to a round number above or below it. Record the measurement in a comment beside the constant, with the date.

Re-run: the script must now report PASS for Layer 1 and exit 0.

Then `python -m pytest tests/test_suite_integrity_script.py -v` — all pass.

**If the measured coverage is below 90%**, report the uncovered branches rather than pinning a low floor silently: uncovered core branches are themselves findings, and the human should see them before the number is frozen.

- [ ] **Step 5: Commit**

Add to `.gitignore`:

```
# Suite-integrity artifacts: regenerable, not tracked.
.coverage
htmlcov/
*.sqlite
```

```bash
git add scripts/check_suite_integrity.py tests/test_suite_integrity_script.py .gitignore
git commit -m "feat: suite-integrity script with a measured branch-coverage floor"
```

---

