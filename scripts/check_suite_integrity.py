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

# O-C: two-sided pins. A one-sided floor never flags an improvement, so the pin
# silently detaches from the tree the moment the next test lands -- which is
# exactly how the mutation pin drifted 2.04pp, four times its own tolerance,
# inside the layer built to catch drift. Raising a MEASURED value is routine and
# expected; widening a TOLERANCE requires a recorded reason here.
#
# HISTORY. Coverage was previously a one-sided COVERAGE_FLOOR = 94.12 (itself
# re-measured from an original 91.64 after Task 4's mutation-score triage added
# branch-covering tests -- see git history for that derivation). Mutation was
# previously MUTATION_MEASURED = 93.85 with a derived MUTATION_FLOOR, also
# one-sided. Both floors independently pass at the values below, so this is a
# re-pin onto a two-sided check, not a threshold change.
#
# SCOPE, unchanged from the coverage floor's original comment: the coverage
# measurement omits src/tolcad/gen/ via [tool.coverage.run] omit in
# pyproject.toml -- see the comment there for why. The mutation measurement
# aggregates killed / (total - incompetent) across the six core modules; see
# run_mutation_score() below for the exact arithmetic.
COVERAGE_MEASURED = 94.74   # measured 2026-08-01, gen/ omitted
COVERAGE_TOLERANCE = 0.50
MUTATION_MEASURED = 95.89   # measured 2026-08-01, six core modules
MUTATION_TOLERANCE = 0.50


def check_two_sided(measured: float, pinned: float, tolerance: float) -> tuple[bool, str]:
    """True iff `measured` is within `tolerance` of `pinned`, in either direction."""
    delta = measured - pinned
    if delta < -tolerance:
        return False, f"{measured:.2f} is below the pin {pinned:.2f} by {-delta:.2f}"
    if delta > tolerance:
        return False, (
            f"{measured:.2f} is ABOVE the pin {pinned:.2f} by {delta:.2f} -- the "
            f"tree improved and the pin has detached. Re-pin it and record why."
        )
    return True, f"{measured:.2f} within {tolerance:.2f} of {pinned:.2f}"


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
    ok, msg = check_two_sided(measured, COVERAGE_MEASURED, COVERAGE_TOLERANCE)
    print(f"Core branch coverage: {msg}")
    return measured, ok


# WHY A TOLERANCE AND NOT AN EXACT PIN. The comparison in run_mutation_score()
# uses the RAW score while MUTATION_MEASURED is its 2-decimal display rounding,
# so an exact pin can fail on an unchanged tree: a raw score can be BELOW its
# own displayed rounding (run 3 of the pre-fix layer measured 610/650 =
# 93.8462%, displayed 93.85% -- the raw value was below the literal 93.85).
# Separately, cosmic-ray's per-mutant timeout is load-sensitive (57.63% vs
# 57.69% observed on two nominally identical runs). 0.50pp is wider than both
# effects and far narrower than any real regression. The same tolerance is
# used for coverage, which has no analogous rounding gap but benefits from the
# same margin against measurement noise.
#
# THE DENOMINATOR, for the current MUTATION_MEASURED = 95.89: aggregate killed
# / (total - incompetent) across the six core modules, via the exact
# run_mutation_score() invocation below. See task-4-fix-report.md and
# task-2-report.md for the full per-module breakdown and triage history.

_CONFIG = REPO_ROOT / "cosmic-ray.toml"


def _mutate_one_module(module: str, workdir: Path) -> tuple[int, int, int]:
    """Run cosmic-ray over one core module. Returns (total, survived, incompetent)."""
    config = tomllib.loads(_CONFIG.read_text(encoding="utf-8"))
    # module-path is deliberately NOT read from the file: cosmic-ray takes one
    # module per session, so this function supplies it per call. Only timeout
    # and test-command are inherited from cosmic-ray.toml.

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
    proc = subprocess.run(["cr-report", str(session)],
                          cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    report = proc.stdout

    # Same principle as run_coverage(): refuse to report a number that was not
    # measured. An unguarded .group(1) turns a cr-report format change into a
    # bare AttributeError, which reads like a bug in this script rather than
    # what it is -- the measurement having silently stopped being parseable.
    def _count(label: str) -> int:
        match = re.search(rf"{label}:\s*(\d+)", report)
        if match is None:
            raise RuntimeError(
                f"could not parse '{label}' from cr-report output for "
                f"{module}; refusing to report a number that was not "
                f"measured.\n{report[-2000:]}"
            )
        return int(match.group(1))

    total = _count("total jobs")
    survived = _count("surviving mutants")
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
    one mutant at a time. On all THREE normal exits observed during this
    layer's development (three full runs; see task-4-report.md section 3) the
    restore was clean and byte-exact (`git diff src/` empty,
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
    ok, msg = check_two_sided(score, MUTATION_MEASURED, MUTATION_TOLERANCE)
    print(f"Mutation score: {msg}")
    return score, ok


def _print_report(rows: list[tuple[str, str, str, bool]]) -> None:
    print("Suite integrity - tests that cannot fail (non-blocking for Gate A)")
    print()
    for name, measured, pin, ok in rows:
        status = "PASS" if ok else "FAIL"
        print(f"  {name:<34} {status:<6} {measured} (pin {pin})")
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
            (
                "Core branch coverage",
                f"{measured:.2f}%",
                f"{COVERAGE_MEASURED:.2f}% +/- {COVERAGE_TOLERANCE:.2f}",
                ok,
            )
        )
        mutation_score, mutation_ok = run_mutation_score()
        rows.append(
            (
                "Mutation score",
                f"{mutation_score:.2f}%",
                f"{MUTATION_MEASURED:.2f}% +/- {MUTATION_TOLERANCE:.2f}",
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
