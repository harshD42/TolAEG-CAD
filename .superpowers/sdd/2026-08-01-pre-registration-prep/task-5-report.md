# Task 5 report: Give the layout margin constants teeth

## Summary

Added `test_the_margin_constants_are_actually_large_enough` to
`tests/gen/test_layout.py`, verbatim from the brief. No production code was
changed in the final diff. `src/tolcad/gen/layout.py` was temporarily
mutated to demonstrate the RED step, then restored and verified
byte-identical to HEAD via `git diff`.

## Step 1-2: mutation run (RED step)

`_MIN_WALL_MM` was temporarily set to `0.0` in
`src/tolcad/gen/layout.py` (from `4.0`). Ran:

```
python -m pytest tests/gen/test_layout.py -v
```

Output:

```
collecting ... collected 8 items

tests/gen/test_layout.py::test_largest_clearance_hole_needs_more_than_the_old_hardcoded_pitch PASSED [ 12%]
tests/gen/test_layout.py::test_pitch_leaves_a_wall_between_the_widest_neighbours PASSED [ 25%]
tests/gen/test_layout.py::test_plate_leaves_an_edge_margin_around_the_outermost_feature PASSED [ 37%]
tests/gen/test_layout.py::test_positions_are_symmetric_about_the_plate_centre PASSED [ 50%]
tests/gen/test_layout.py::test_radii_track_the_larger_of_the_two_mating_holes PASSED [ 62%]
tests/gen/test_layout.py::test_sampler_records_a_plate_big_enough_for_its_own_features PASSED [ 75%]
tests/gen/test_layout.py::test_plate_size_is_serialised_in_the_sidecar PASSED [ 87%]
tests/gen/test_layout.py::test_the_margin_constants_are_actually_large_enough FAILED [100%]

================================== FAILURES ===================================
_____________ test_the_margin_constants_are_actually_large_enough _____________

    ...
>       assert _MIN_WALL_MM >= 3.7, (
            f"_MIN_WALL_MM {_MIN_WALL_MM} leaves no ligament between two features "
            f"leaning toward each other"
        )
E       AssertionError: _MIN_WALL_MM 0.0 leaves no ligament between two features leaning toward each other
E       assert 0.0 >= 3.7

tests\gen\test_layout.py:86: AssertionError
=========================== short test summary info ===========================
FAILED tests/gen/test_layout.py::test_the_margin_constants_are_actually_large_enough
========================= 1 failed, 7 passed in 0.14s =========================
```

**Contrast confirmed:** the new test (`test_the_margin_constants_are_actually_large_enough`)
FAILED against the zeroed constant, while both pre-existing margin tests —
`test_pitch_leaves_a_wall_between_the_widest_neighbours` and
`test_plate_leaves_an_edge_margin_around_the_outermost_feature` — PASSED, because
they compare geometry against the very constant that was just zeroed rather than
against a literal floor. This is exactly the defect the brief describes: the old
tests cannot fail no matter how small the constant is; the new test can.

## Step 4: restore and verify byte-identical

Restored `_MIN_WALL_MM = 4.0` in `src/tolcad/gen/layout.py`. Verified:

```
$ git diff src/tolcad/gen/layout.py
(empty output)

$ git status --porcelain
 M tests/gen/test_layout.py
```

`layout.py` shows no diff against HEAD — confirmed byte-identical. Only
`tests/gen/test_layout.py` is modified.

## Step 5: post-restore layout test run

```
python -m pytest tests/gen/test_layout.py -v
...
collected 8 items

tests/gen/test_layout.py::test_largest_clearance_hole_needs_more_than_the_old_hardcoded_pitch PASSED [ 12%]
tests/gen/test_layout.py::test_pitch_leaves_a_wall_between_the_widest_neighbours PASSED [ 25%]
tests/gen/test_layout.py::test_plate_leaves_an_edge_margin_around_the_outermost_feature PASSED [ 37%]
tests/gen/test_layout.py::test_positions_are_symmetric_about_the_plate_centre PASSED [ 50%]
tests/gen/test_layout.py::test_radii_track_the_larger_of_the_two_mating_holes PASSED [ 62%]
tests/gen/test_layout.py::test_sampler_records_a_plate_big_enough_for_its_own_features PASSED [ 75%]
tests/gen/test_layout.py::test_plate_size_is_serialised_in_the_sidecar PASSED [ 87%]
tests/gen/test_layout.py::test_the_margin_constants_are_actually_large_enough PASSED [100%]

============================== 8 passed in 0.10s ==============================
```

All 8 tests pass.

## Step 6: full suite (no `-m` filter, includes slow)

```
python -m pytest -q
...
213 passed in 23.94s
```

Baseline at HEAD (before this task's test was added) was 210 passed, 2
deselected under `-m "not slow"`; without any `-m` filter the true baseline
was 212 passed (210 + the 2 slow tests). Adding one new test brings the
full, unfiltered count to 213 passed — consistent with baseline + 1, no
regressions.

## Step 7: Gate A

```
python scripts/gate_a.py > out.txt 2>&1; echo "EXITCODE:$?"
EXITCODE:1
```

Gate A report:

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

Exit code 1, 6 PASS / 3 SKIP — matches expected (Gate A is still "NOT CLEARED"
only because of the three honestly-documented SKIPs, unrelated to this task).

## Step 8: commit

Committed as `5d04d6f1da7ed7d51b493584a66cce2eb31a3336`:

```
commit 5d04d6f1da7ed7d51b493584a66cce2eb31a3336
Author: harshD42 <harsh.dwivedi42@gmail.com>

    test: pin the layout margins to literals, not to themselves

    Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

 tests/gen/test_layout.py | 27 +++++++++++++++++++++++++++
 1 file changed, 27 insertions(+)
```

## Step 9: self-review

`git show --stat 5d04d6f` confirms exactly one file changed:
`tests/gen/test_layout.py`, 27 insertions, 0 deletions, 0 deletions in
production code. No file under `src/` appears in the commit. `layout.py`
constants are `_MIN_WALL_MM = 4.0` and `_EDGE_MARGIN_MM = 5.0`, unchanged
from HEAD.

## Concerns

None. The mutation-test contrast came out exactly as the brief predicted:
the two pre-existing margin tests are structurally unable to fail from a
zeroed constant (they compare geometry to the constant itself, not to a
fixed floor), while the new test catches it immediately. No production code
was touched; the temporary mutation was fully reverted and verified via an
empty `git diff`. Full suite and Gate A numbers are unchanged from baseline
except for the one new passing test.
