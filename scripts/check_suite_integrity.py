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
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CORE_MODULES = ("types", "y14_5", "iso286", "montecarlo", "checker", "reliability")

CORE_TEST_SUBSET = [f"tests/test_{name}.py" for name in CORE_MODULES]

# MEASURED, not chosen. A floor pinned at a round number is not a measurement,
# and this project's drift class is precisely a threshold that stops tracking
# what it bounds.
#
# Originally measured 91.64% TOTAL branch coverage on 2026-08-01 (233 stmts /
# 15 miss / 90 branch / 12 partial; checker 100.00%, reliability 98.53%,
# types 91.84%, iso286 88.89%, y14_5 87.34%, montecarlo 85.19%).
#
# RE-MEASURED 94.12% on 2026-08-01, same day, after Task 4's mutation-score
# triage added targeted tests to all six core test files (killing survivors
# like the zero-width tolerance band in types.py and the governing_part /
# equal-mmc-boundary gaps in y14_5.py). Those tests exercise branches Layer 1
# was not previously covering, so the honest floor moved with them -- leaving
# the old 91.64 in place would have re-created exactly the "floor that stops
# tracking what it bounds" defect this constant's own comment warns against.
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
COVERAGE_FLOOR = 94.12  # re-measured 2026-08-01 after Task 4's test additions


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


# MEASURED, not chosen. Set from an actual run -- see Step 4.
#
# Measured 2026-08-01, run 3. Recorded verbatim so the pin stays a measurement.
#
# 93.85% aggregate mutation score, via the exact run_mutation_score()
# invocation below, AFTER triaging every survivor from the pre-fix baseline.
#
# THE DENOMINATOR, SPELLED OUT, because an earlier version of this comment got
# it wrong. Run 2 (the diagnostic run that produced the survivor list) measured
# per module: types 66/5, y14_5 339/40, iso286 515/169, montecarlo 97/44,
# checker 24/8, reliability 77/9 as (total jobs / surviving). That is 1,118
# TOTAL JOBS, of which 468 are INCOMPETENT (cannot execute at all), leaving
#     650 VIABLE mutants, 275 of them surviving -> 375/650 = 57.69% killed.
# 1,118 is the total-jobs figure, NOT the viable denominator; describing the
# 275 survivors as "275 of 1,118 viable" made the arithmetic incoherent and is
# corrected here. Run 3 re-measured the same 650-mutant denominator after the
# triage: 610 killed, 40 surviving -> 610/650 = 93.8462%, displayed 93.85%.
#
# NOT EVERY RUN-3 SURVIVOR IS ACCOUNTED FOR. 40 survived run 3 and 23 were
# documented equivalent, so ~17 were neither killed nor documented. Some are
# now known: three `condition is "..."` mutants in y14_5.py were wrongly filed
# as equivalent (they are live -- CPython does not intern the string
# checker.py builds with str.replace) and are killed by tests added in the
# fix round; the `hole.mmc % fastener.mmc` mutant in fixed_fastener_tolerance
# was wrongly counted killed and is now killed for real. The remainder is
# UNTRIAGED, and is reported as untriaged rather than absorbed into the
# equivalent count. See task-4-fix-report.md.
#
# WHY A TOLERANCE AND NOT AN EXACT PIN. The comparison in run_mutation_score()
# uses the RAW score while the value below is its 2-decimal display rounding,
# so an exact pin can fail on an unchanged tree: the raw 93.8462 is BELOW a
# literal 93.85 floor. Separately, cosmic-ray's per-mutant timeout is
# load-sensitive (57.63% vs 57.69% on two nominally identical runs). 0.50pp is
# wider than both effects and far narrower than any real regression.
#
# Raising MUTATION_MEASURED is routine. Widening MUTATION_TOLERANCE requires a
# recorded reason here, and LOWERING MUTATION_MEASURED does too -- for the same
# reason as COVERAGE_FLOOR above.
MUTATION_MEASURED = 93.85
MUTATION_TOLERANCE = 0.50
MUTATION_FLOOR = MUTATION_MEASURED - MUTATION_TOLERANCE

_CONFIG = REPO_ROOT / "cosmic-ray.toml"


def _mutate_one_module(module: str, workdir: Path) -> tuple[int, int, int]:
    """Run cosmic-ray over one core module. Returns (total, survived, incompetent)."""
    config = tomllib.loads(_CONFIG.read_text(encoding="utf-8"))
    config["cosmic-ray"]["module-path"] = f"src/tolcad/{module}.py"

    cfg_path = workdir / f"cr-{module}.toml"
    # Re-emit the config with only the field we changed; cosmic-ray reads TOML.
    cfg_path.write_text(
        "[cosmic-ray]\n"
        f'module-path = "src/tolcad/{module}.py"\n'
        f"timeout = {config['cosmic-ray']['timeout']}\n"
        "excluded-modules = []\n"
        f"test-command = \"{config['cosmic-ray']['test-command']}\"\n"
        "\n[cosmic-ray.distributor]\n"
        'name = "local"\n',
        encoding="utf-8",
    )
    session = workdir / f"{module}.sqlite"

    subprocess.run(["cosmic-ray", "init", str(cfg_path), str(session)],
                   cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    subprocess.run(["cosmic-ray", "exec", str(cfg_path), str(session)],
                   cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    report = subprocess.run(["cr-report", str(session)],
                            cwd=REPO_ROOT, capture_output=True, text=True).stdout

    total = int(re.search(r"total jobs:\s*(\d+)", report).group(1))
    survived = int(re.search(r"surviving mutants:\s*(\d+)", report).group(1))
    # INCOMPETENT mutants fail to execute at all (RemoveDecorator on a
    # dataclass, for instance). They are neither killed nor surviving, so
    # counting them either way distorts the score.
    incompetent = report.count("TestOutcome.INCOMPETENT")
    return total, survived, incompetent


def run_mutation_score() -> tuple[float, bool]:
    """Aggregate killed / (total - incompetent) across the six core modules.

    *** CONCURRENCY HAZARD -- DO NOT CALL THIS ALONGSIDE ANYTHING ELSE THAT
    READS src/tolcad/. *** cosmic-ray mutates each target module IN PLACE on
    disk for the duration of a single mutant's test run, then restores it,
    one mutant at a time. On every normal exit observed during this layer's
    development the restore was clean and byte-exact (`git diff src/` empty,
    independently-diffed files matching HEAD). The hazard is ABNORMAL
    termination -- killing this process, a crash mid-mutant -- which can
    leave a checker-core file sitting on disk with a live mutant still
    applied. Even on a normal exit, a concurrent reader can observe a live
    mutant mid-run, simply because the file is genuinely mutated for the
    seconds that mutant's test command executes; this happened once during
    this layer's own development (a code-review pass reading the tree while
    this function was mid-run).

    Recovery: `git status --short` -- a checker-core file showing modified
    with no corresponding intentional edit is a leftover mutant.
    `git checkout -- src/` restores it from HEAD (discards ALL uncommitted
    changes under src/, so check `git status` first if there is real
    unstaged work under src/ to preserve).
    """
    if shutil.which("cosmic-ray") is None:
        # Unavailable is a FAILURE, never a skip. A silently skipped integrity
        # layer is the exact failure mode this whole exercise exists to remove.
        raise RuntimeError(
            "cosmic-ray is not installed; install the [dev] extra. This layer "
            "does not skip."
        )

    totals = survived_all = incompetent_all = 0
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        for module in CORE_MODULES:
            total, survived, incompetent = _mutate_one_module(module, workdir)
            totals += total
            survived_all += survived
            incompetent_all += incompetent

    denominator = totals - incompetent_all
    if denominator <= 0:
        raise RuntimeError("no viable mutants were generated; the config is wrong")
    killed = denominator - survived_all
    score = 100.0 * killed / denominator
    return score, score >= MUTATION_FLOOR


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
        mutation_score, mutation_ok = run_mutation_score()
        rows.append(
            (
                "Mutation score",
                f"{mutation_score:.2f}%",
                f"{MUTATION_FLOOR:.2f}%",
                mutation_ok,
            )
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
