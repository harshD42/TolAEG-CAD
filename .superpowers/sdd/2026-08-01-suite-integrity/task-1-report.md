# Task 1 report: declared-mutation runner and its anti-vacuity contract

## RED (Step 2) — verbatim

Command: `python -m pytest tests/test_declared_mutations.py -v`

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0 -- ...python.exe
cachedir: .pytest_cache
rootdir: C:\Users\harsh\Downloads\Projects\Paper1
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 0 items / 1 error

=================================== ERRORS ====================================
______________ ERROR collecting tests/test_declared_mutations.py ______________
ImportError while importing test module 'C:\Users\harsh\Downloads\Projects\Paper1\tests\test_declared_mutations.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
...\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_declared_mutations.py:10: in <module>
    from tests.mutation_registry import REGISTRY, DeclaredMutation, run_declared_mutation
E   ModuleNotFoundError: No module named 'tests.mutation_registry'
=========================== short test summary info ===========================
ERROR tests/test_declared_mutations.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.13s ===============================
```

Matches the brief's expectation exactly: `ModuleNotFoundError` for `tests.mutation_registry` at collection.

## `tests/__init__.py` decision

**Not needed.** After creating `tests/mutation_registry.py` and adding the `mutation` marker
to `pyproject.toml`, `from tests.mutation_registry import ...` resolved without an
`__init__.py`. Python 3.13 treats `tests/` as an implicit namespace package once `.`
(the repo root) is on `pythonpath` — no package marker required. Checked before adding
one, per the brief's instruction, and did not add it since it wasn't necessary.

## GREEN (Step 4) — verbatim

Command: `python -m pytest tests/test_declared_mutations.py -v`

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0 -- ...python.exe
cachedir: .pytest_cache
rootdir: C:\Users\harsh\Downloads\Projects\Paper1
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 6 items

tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[it7-row-transposed] PASSED [ 16%]
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[zeroed-wall-margin] PASSED [ 33%]
tests/test_declared_mutations.py::test_a_no_op_patch_is_rejected PASSED  [ 50%]
tests/test_declared_mutations.py::test_an_ambiguous_patch_is_rejected PASSED [ 66%]
tests/test_declared_mutations.py::test_an_invalid_expectation_is_rejected PASSED [ 83%]
tests/test_declared_mutations.py::test_a_mutation_that_changes_nothing_is_rejected PASSED [100%]

============================== 6 passed in 1.55s ==============================
```

2 registry entries (`it7-row-transposed`, `zeroed-wall-margin`) plus 4 runner-guard tests, all
passing. Neither the `it7-row-transposed` nor the `zeroed-wall-margin` mutation reported an
occurrence count other than 1 — newline normalisation is working; `\n_MIN_WALL_MM = 4.0`
matched exactly once in `layout.py`, not the 2 it would have matched without CRLF
normalisation (docstring line 32 + assignment line 67 both contain the bare
`_MIN_WALL_MM = 4.0` substring).

## Full suite (Step 4 cont'd)

- With this change: `python -m pytest -q` → **286 passed in 25.79s** (280 baseline + 6 new
  tests from `tests/test_declared_mutations.py`).
- Baseline re-measured for comparison (via `git stash -u` / `git stash pop`, no permanent
  change): **280 passed in 24.23s**.
- **Added wall-clock time: ~1.5s** for the full suite. The two declared mutations each spawn
  two pytest subprocesses (baseline-passes check, then under-mutation check), which accounts
  for the added time; it is modest because the two targeted test selectors
  (`test_iso286.py::test_all_52_it5_to_it8_cells_match_iso286_table_1` and
  `gen/test_layout.py::test_the_margin_constants_are_actually_large_enough`) are themselves fast.

## Gate A (Step 6)

Command: `python scripts/gate_a.py > <file> 2>&1; echo "EXITCODE=$?"` (exit code captured
directly after the script, not through a pipe).

```
EXITCODE=1
```

Output:

```
Gate A - checker correctness (blocking)

  Y14.5 self-consistency          PASS   100% required; NOT standard-verified (see Y14.5 citation verified)
  Monte Carlo convergence         PASS   +/-0.5% at N=100k
  Checker reliability             PASS   mean 0.9982 over 200 pre-registered seeds (95% bootstrap CI [0.9964, 0.9995], 10000 resamples); fraction of seeds >= 0.95: 0.9800 (tested=11, excluded=1, tested |margin| in [3.50e-04, 4.50e-01]); threshold 0.95
  Validation isolation            PASS   no core imports
  Y14.5 citation verified         PASS   citation verified against standard
  ISO 286 transcription verified  PASS   transcription verified against standard
  NIST PMI conformance            SKIP   no export at nist_pmi_expected.csv
  TolAnalyst agreement            SKIP   no export at tolanalyst_verdicts.csv
  Fresh clone pipeline            SKIP   requires a clean-clone CI run to verify honestly; not checked in-process

Gate A: NOT CLEARED
```

6 PASS / 3 SKIP, exit code 1 — matches expectation. `scripts/gate_a.py` was not modified
(confirmed via `git status --short` below; the file does not appear).

## Working tree cleanliness (Step 7)

Immediately after every declared-mutation run (both in the ad-hoc verification and inside the
committed test suite), `git status --short` showed only the three intended new/modified files —
no trace of `src/tolcad/iso286.py` or `src/tolcad/gen/layout.py` having been left mutated. This
is the direct evidence that the `finally`-block restoration plus the post-restore byte-identical
assertion in `run_declared_mutation` worked as designed.

After the commit:

```
$ git status --short
(clean — no output)
```

## Commit

SHA: `95bea176be585e5f6a0826352054912f2371e13d` (short: `95bea17`)

```
feat: declared-mutation runner, with its own anti-vacuity contract

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

3 files changed, 235 insertions(+): `pyproject.toml`, `tests/mutation_registry.py`,
`tests/test_declared_mutations.py`.

## Self-review

- `tests/mutation_registry.py` and `tests/test_declared_mutations.py` were written verbatim
  from the brief — no simplification of the three load-bearing clauses (exact-one-occurrence
  check, pre-mutation pass check, `finally`-guarded byte-identical restore).
- `pyproject.toml`'s `mutation` marker was added alongside `slow`, not in place of it, and is
  not deselected anywhere (no `-m` filter added to `addopts`), so it runs by default in every
  invocation as required.
- No checker-core module (`types`, `y14_5`, `iso286`, `montecarlo`, `checker`, `reliability`)
  or `scripts/gate_a.py` was permanently modified — the only files touched by `git diff`/`git
  status` are the two new test-support files and the one-line `pyproject.toml` addition. The
  two production files declared as mutation targets (`iso286.py`, `gen/layout.py`) are
  transiently mutated and byte-identically restored by the runner itself, verified both by the
  runner's own assertion and by the empirical `git status --short` check after each run.
- No `_IT_MICRONS`, `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`, `_TOL_FRACTION_RANGE`,
  `_MIN_WALL_MM`, or `_EDGE_MARGIN_MM` constant was permanently changed.
- `tests/__init__.py` was not added; confirmed unnecessary given Python 3.13's implicit
  namespace-package resolution with `pythonpath = ["src", "."]`.

## Concerns

- None blocking. One thing worth flagging for future tasks (SI-2 onward): each declared
  mutation costs roughly two subprocess pytest invocations of its target selector, so as the
  registry grows to the full 9+ entries mentioned in later tasks, the added wall-clock cost
  will scale roughly linearly with the number of entries times the cost of their target test
  selectors. At ~1.5s for 2 entries this is currently negligible, but is worth watching once
  the registry is much larger.
