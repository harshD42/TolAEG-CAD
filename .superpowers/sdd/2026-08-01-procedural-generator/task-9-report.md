# Task 9 report: end-to-end generation and a round-trip guard

## Summary

Added `tests/gen/test_end_to_end.py` exactly as specified in the brief, transcribed
verbatim (3 tests). No production code was created or modified — this was a pure
test-addition task, and all three tests passed on the first run, as expected for an
integration gate exercising already-complete modules (Tasks 1-8).

## Step 2: run the new test file

```
python -m pytest tests/gen/test_end_to_end.py -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0 -- ...python.exe
cachedir: .pytest_cache
rootdir: C:\Users\harsh\Downloads\Projects\Paper1
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 3 items

tests/gen/test_end_to_end.py::test_seed_to_verdict_round_trip PASSED     [ 33%]
tests/gen/test_end_to_end.py::test_exported_step_is_readable_by_the_oracle_machinery PASSED [ 66%]
tests/gen/test_end_to_end.py::test_a_batch_of_seeds_generates_without_error PASSED [100%]

============================== 3 passed in 1.48s ==============================
```

All three passed immediately. No fixes to any module were needed.

## Step 4: full suite

```
python -m pytest -q -m "not slow"
```

```
........................................................................ [ 47%]
........................................................................ [ 94%]
.........                                                                [100%]
153 passed, 2 deselected in 16.61s
```

Baseline before this change was 150 passed, 2 deselected. The delta is exactly +3,
matching the three new tests added. No regressions, no other collection changes.

## Step 4 (cont'd): Gate A

```
python scripts/gate_a.py
```

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

Exit code: 1
```

PASS/SKIP breakdown: **6 PASS / 3 SKIP**, exit code **1**.

Per the brief, this is expected and correct at this phase: the three SKIPs
(NIST PMI conformance, TolAnalyst agreement, Fresh clone pipeline) all require
artifacts or CI runs that are deliberately deferred until after Phase 3.5
pre-registration and/or a proper CI environment. Gate A was NOT CLEARED before
this task and remains NOT CLEARED after it — this task does not touch Gate A's
scope (no wiring of the NIST oracle into `scripts/gate_a.py`, no research
corpus generation, per the brief's explicit "deliberately NOT done here" list).

## Production code touched?

**No.** Only `tests/gen/test_end_to_end.py` was created. Nothing in
`tolcad/gen/`, `tolcad/checker/`, or `validation/` was modified. This confirms
Tasks 1-8 are structurally sound: sampler, build, export, spec round-trip, the
checker's `MateSpec.to_check_dict()` contract, and the AP242 PMI reader all
compose correctly on the first attempt.

## Commit

```
commit bbac3dc9fca00c47d615379308ab5b803461ab95
Author: harshD42 <harsh.dwivedi42@gmail.com>

    test: end-to-end seed-to-verdict round trip

    Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

 tests/gen/test_end_to_end.py | 47 ++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 47 insertions(+)
```

Only the single test file is in the diff; nothing else was staged or committed.

## Self-review notes

- The test file's content matches the brief's Step 1 code block verbatim (import
  order, docstrings, assertions, the 5-seed batch loop with `range(5)` — not
  increased, matching the "do not increase the batch, do not add a bulk-generation
  script" constraint).
- `pytest.importorskip("cadquery", ...)` and `pytest.importorskip("OCP", ...)` guard
  the CAD-dependent paths so the file degrades gracefully without the `[gen]` extra,
  consistent with the project's "core must stay CAD-free" convention (this file
  lives under `tests/gen/`, not core, so importing cadquery/OCP here is fine).
- `test_exported_step_is_readable_by_the_oracle_machinery` asserts our own export
  has zero PMI counts (dimensions/geometric_tolerances/datums), which is a
  meaningful contrast now that `tests/test_ap242_pmi.py` proves the same reader
  returns the real 47/27/59 counts against the NIST FTC06 fixture — i.e., zero
  here means "no semantic PMI was written," not "the reader is broken."
- Verified via `git show HEAD` that the commit contains exactly the one new file
  and no incidental changes (no `__pycache__`, no stray formatting-only diffs
  elsewhere).
- Did not touch any pre-registered Gate A/B/C/D thresholds in the design spec.

## Concerns

None. This task closes the loop cleanly: every module built in Tasks 1-8 composed
correctly with no fixes required. The three Gate A SKIPs are pre-existing and
expected at this phase (NIST oracle wiring and TolAnalyst comparison both require
the research corpus, which is intentionally gated behind Phase 3.5
pre-registration per spec §12).
