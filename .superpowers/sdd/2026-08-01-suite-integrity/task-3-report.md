# Task 3 report: The integrity script and branch coverage

Branch: `feat/suite-integrity`. Starting HEAD: `2e2cabc`. Final commit: `3f26dc8`.

## Step 1-2: RED (verbatim, before the script existed)

Wrote `tests/test_suite_integrity_script.py` exactly as given in the brief. Ran
`python -m pytest tests/test_suite_integrity_script.py -v` before creating the
script. Verbatim output:

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0 -- ...python.exe
cachedir: .pytest_cache
rootdir: C:\Users\harsh\Downloads\Projects\Paper1
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.1.0
collecting ... collected 4 items

tests/test_suite_integrity_script.py::test_the_script_exists FAILED      [ 25%]
tests/test_suite_integrity_script.py::test_it_names_the_six_core_modules FAILED [ 50%]
tests/test_suite_integrity_script.py::test_the_coverage_floor_is_a_measured_value_not_a_round_number FAILED [ 75%]
tests/test_suite_integrity_script.py::test_the_script_reports_and_exits_nonzero_when_a_layer_fails FAILED [100%]

================================== FAILURES ===================================
___________________________ test_the_script_exists ____________________________
    def test_the_script_exists():
>       assert SCRIPT.is_file()
E       AssertionError: assert False
E        +  where False = is_file()
E        +    where is_file = WindowsPath('C:/Users/harsh/Downloads/Projects/Paper1/scripts/check_suite_integrity.py').is_file
tests\test_suite_integrity_script.py:10: AssertionError
_____________________ test_it_names_the_six_core_modules ______________________
    import check_suite_integrity as mod
E   ModuleNotFoundError: No module named 'check_suite_integrity'
_______ test_the_coverage_floor_is_a_measured_value_not_a_round_number ________
    import check_suite_integrity as mod
E   ModuleNotFoundError: No module named 'check_suite_integrity'
________ test_the_script_reports_and_exits_nonzero_when_a_layer_fails _________
tmp_path = WindowsPath('...pytest-119\\test_the_script_reports_and_ex0')
>       assert proc.returncode == 1, "a failing layer must exit nonzero"
E       AssertionError: a failing layer must exit nonzero
E       assert 2 == 1
E   stderr="...python.exe: can't open file '...\\scripts\\check_suite_integrity.py': [Errno 2] No such file or directory\n"
============================== 4 failed in 0.11s ==============================
```

All 4 failed for the expected reason (script absent), confirming RED before
any implementation existed.

## Step 3-4: script + measurement

Created `scripts/check_suite_integrity.py` from the brief's code block
verbatim, with `COVERAGE_FLOOR = 0.0` first, then ran it:

```
$ python scripts/check_suite_integrity.py
Suite integrity - tests that cannot fail (non-blocking for Gate A)

  Core branch coverage               PASS   48.00% (floor 0.00%)

Suite integrity: OK
```

**Measured: 48.00%.** This is below 90%, so per the brief's own escalation
rule I did not silently pin it — I pulled the per-file breakdown first:

```
Name                         Stmts   Miss Branch BrPart  Cover   Missing
------------------------------------------------------------------------
src\tolcad\__init__.py           1      0      0      0   100%
src\tolcad\checker.py           19      0      8      0   100%
src\tolcad\gen\__init__.py       0      0      0      0   100%
src\tolcad\gen\build.py         35     35     10      0     0%   18-85
src\tolcad\gen\export.py        15     15      0      0     0%   9-35
src\tolcad\gen\features.py      25     25      8      0     0%   34-150
src\tolcad\gen\layout.py        33     33      8      0     0%   63-127
src\tolcad\gen\sampler.py       42     42      4      0     0%   9-160
src\tolcad\gen\spec.py          72     72     36      0     0%   8-182
src\tolcad\iso286.py            50      5     22      3    89%   119, 132, 147-148, 161
src\tolcad\montecarlo.py        21      2      6      2    85%   34, 37
src\tolcad\reliability.py       48      1     20      0    99%   82
src\tolcad\types.py             41      2      8      2    92%   34, 38
src\tolcad\y14_5.py             53      5     26      5    87%   31, 47, 49, 204, 208
------------------------------------------------------------------------
TOTAL                          455    237    156     12    48%
```

### Finding: the 48% is scope dilution, not weak core testing

The six `CORE_MODULES` files individually measure **87-100%**
(checker 100%, reliability 99%, types 92%, iso286 89%, y14_5 87%,
montecarlo 85%) — a healthy core. The 48.00% TOTAL happens because the
brief's `run_coverage()` passes `--cov=src/tolcad` (the whole installed
package), which also pulls in `src/tolcad/gen/` (222 statements, 66
branches, entirely 0% here) even though `CORE_TEST_SUBSET` only runs the six
core test files and never touches `gen/`. `gen/` is explicitly and
deliberately out of `CORE_MODULES` scope per the test docstring
("CadQuery mutants are slow and frequently geometrically meaningless"), but
the `--cov` target is not correspondingly narrowed to just the core files.

I did not change `run_coverage()` or the `--cov` scope — Step 4 authorizes
only replacing the `COVERAGE_FLOOR` constant, the script is otherwise
verbatim from the brief, and no test in the brief's own suite requires a
narrower `--cov` target. I am flagging this discrepancy for a human to
decide whether Layer 1 should later be rescoped (e.g.
`--cov=src/tolcad --cov-config` excluding `gen/`, or per-module `--cov`
flags) so the number tracks "core coverage" rather than "core coverage
diluted by an intentionally-untested sibling package."

### Remaining actual gaps (worth a look regardless of scope):

- `iso286.py` lines 119, 132, 147-148, 161 — uncovered
- `montecarlo.py` lines 34, 37 — uncovered
- `reliability.py` line 82 — uncovered
- `types.py` lines 34, 38 — uncovered
- `y14_5.py` lines 31, 47, 49, 204, 208 — uncovered

### Floor pinned

Per "pin what you measure," I pinned `COVERAGE_FLOOR = 48.0` (the literal
measured TOTAL from the exact `run_coverage()` invocation as shipped), with a
dated comment recording both the measurement and the scope-dilution finding
above, so a future reader isn't misled into thinking core coverage is 48%.

```python
# Measured 48.00% TOTAL branch coverage on 2026-08-01 via the exact
# run_coverage() invocation below (--cov=src/tolcad, core test subset only).
# NOTE for whoever revisits this: the six CORE_MODULES files individually
# measure 87-100% (checker 100%, iso286 89%, montecarlo 85%, reliability 99%,
# types 92%, y14_5 87%) -- the 48% TOTAL is diluted by src/tolcad/gen/ (0%,
# ~222 stmts/66 branches), which is in scope for --cov=src/tolcad but not
# exercised by CORE_TEST_SUBSET and is deliberately excluded from
# CORE_MODULES. Pinning the measured TOTAL as-is per the task's instruction
# to pin what is measured, not a scope-adjusted number; see
# task-3-report.md for the uncovered-branch detail this floor does not
# by itself surface.
COVERAGE_FLOOR = 48.0  # measured 2026-08-01; see note above
```

Re-ran after pinning:

```
$ python scripts/check_suite_integrity.py
Suite integrity - tests that cannot fail (non-blocking for Gate A)

  Core branch coverage               PASS   48.00% (floor 48.00%)

Suite integrity: OK
```
Exit code: 0.

## Step 5: GREEN

```
$ python -m pytest tests/test_suite_integrity_script.py -v
tests/test_suite_integrity_script.py::test_the_script_exists PASSED      [ 25%]
tests/test_suite_integrity_script.py::test_it_names_the_six_core_modules PASSED [ 50%]
tests/test_suite_integrity_script.py::test_the_coverage_floor_is_a_measured_value_not_a_round_number PASSED [ 75%]
tests/test_suite_integrity_script.py::test_the_script_reports_and_exits_nonzero_when_a_layer_fails PASSED [100%]
============================== 4 passed in 0.09s ==============================
```

## Step 6: `--self-test-failure` path

```
$ python scripts/check_suite_integrity.py --self-test-failure > out.txt 2>&1
$ echo $?
1
```
Captured stdout:
```
Suite integrity - tests that cannot fail (non-blocking for Gate A)

  Self-test (synthetic failure)      FAIL   n/a (floor n/a)

Suite integrity: FAILED (Self-test (synthetic failure))
```
Exit code without a pipe: **1**. "FAIL" present in stdout. This confirms the
script's own nonzero-exit branch is exercised and covered by the test suite,
which is exactly the class of defect Layer 1 is meant to catch.

## Step 7: full suite + Gate A

```
$ python -m pytest -q
........................................................................ [ 24%]
........................................................................ [ 48%]
........................................................................ [ 72%]
........................................................................ [ 96%]
............                                                             [100%]
300 passed in 32.74s
```
300 = the 296-test baseline + the 4 new tests in this task. No regressions.

```
$ python scripts/gate_a.py > out.txt 2>&1; echo $?
1
```
Gate A stdout unchanged in shape (6 PASS / 3 SKIP, "Gate A: NOT CLEARED"):
```
Gate A - checker correctness (blocking)

  Y14.5 self-consistency          PASS   ...
  Monte Carlo convergence         PASS   ...
  Checker reliability             PASS   ...
  Validation isolation            PASS   no core imports
  Y14.5 citation verified         PASS   citation verified against standard
  ISO 286 transcription verified  PASS   transcription verified against standard
  NIST PMI conformance            SKIP   no export at nist_pmi_expected.csv
  TolAnalyst agreement            SKIP   no export at tolanalyst_verdicts.csv
  Fresh clone pipeline            SKIP   requires a clean-clone CI run to verify honestly; not checked in-process

Gate A: NOT CLEARED
```
Exit code: 1. `scripts/gate_a.py` was not modified (verified via `git status`
and `git diff` — no changes to that file appear anywhere in this task's
diff).

## Step 8-9: commit

`git status --short` before staging showed exactly the three expected
touched paths:
```
 M .gitignore
?? scripts/check_suite_integrity.py
?? tests/test_suite_integrity_script.py
```

Staged and committed those three files only. Commit:

```
3f26dc8 feat: suite-integrity script with a measured branch-coverage floor

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

`git status --short` after commit: clean (no output).

## Step 10: self-review

- `tests/test_suite_integrity_script.py` — byte-for-byte the brief's code
  block; no edits.
- `scripts/check_suite_integrity.py` — the brief's code block verbatim,
  except the `COVERAGE_FLOOR` constant and its adjacent comment (the one
  change Step 4 authorizes). `CORE_MODULES` matches the six required names.
  Output shape (`Suite integrity - ...`, `PASS`/`FAIL` rows, "Suite
  integrity: OK/FAILED (...)") deliberately mirrors `scripts/gate_a.py`'s
  shape but is a fully separate script/file; `gate_a.py` itself has zero
  diff.
- `.gitignore` — added exactly the three-line block from the brief
  (`.coverage`, `htmlcov/`, `*.sqlite`) under a new comment. Note:
  `.coverage` was already present earlier in the file from a prior commit,
  so this introduces a harmless duplicate entry; not worth a follow-up, but
  noting it for completeness.
- No checker-core module (`types`, `y14_5`, `iso286`, `montecarlo`,
  `checker`, `reliability`), no other production file, and no threshold in
  the design spec §7 was touched — confirmed via `git show --stat HEAD`
  (only the three intended files appear).
- `_IT_MICRONS`, `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`,
  `_TOL_FRACTION_RANGE`, `_MIN_WALL_MM`, `_EDGE_MARGIN_MM` — untouched (no
  file containing them was part of this diff).

## Concerns for the human

1. **Scope dilution (the main one).** `COVERAGE_FLOOR = 48.0` is real and
   reproducible, but it measures "core test subset run against the whole
   `tolcad` package including untested `gen/`," not "core module coverage."
   The six core modules alone run 85-100%. If Layer 1's intent is to gate on
   core-module health specifically, a future task should narrow the `--cov`
   target (e.g., per-module `--cov=src/tolcad/<name>` flags or a
   `--cov-config` omit list for `gen/`) and re-measure — at which point the
   floor would jump to something in the 80s, and 48.0 should be retired. I
   did not make that change myself because it exceeds Step 4's scope
   ("replace `COVERAGE_FLOOR`," not "rescope `run_coverage`") and because no
   test in this task's brief exercises or requires a narrower scope.
2. Uncovered lines worth eventual attention regardless of scope:
   `iso286.py:119,132,147-148,161`; `montecarlo.py:34,37`;
   `reliability.py:82`; `types.py:34,38`; `y14_5.py:31,47,49,204,208`.
3. The duplicate `.coverage` entry in `.gitignore` (see self-review) is
   cosmetic only.
