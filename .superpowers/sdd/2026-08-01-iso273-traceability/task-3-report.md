# Task 3 report: Re-measure the layout margin and retire the stale literal floor

## Summary

Implemented the brief exactly: raised the literal-floor test's assertion,
hoisted both literals (`_LITERAL_WALL_FLOOR_MM = 3.78`,
`_LITERAL_EDGE_FLOOR_MM = 1.89`) to module constants in
`tests/gen/test_layout.py`, added `test_the_literal_floor_is_not_below_the_derived_one`,
and updated `src/tolcad/gen/layout.py`'s docstring margin derivation to the
new 0.215 mm worst-case radius growth and 3.78 mm / 1.890 mm requirements.
No production constant was touched: `_MIN_WALL_MM` stays `4.0` and
`_EDGE_MARGIN_MM` stays `5.0` (verified below).

One deviation from the brief's literal code: the new test's assertion needed
a `- 1e-9` floating-point slack (`assert _LITERAL_WALL_FLOOR_MM >= required - 1e-9`),
matching the style already used by
`test_the_margin_constants_still_cover_the_tables_they_came_from`. Without it,
`3.78 >= 3.7800000000000002` fails on floating-point noise even when the
literal is numerically correct — confirmed by running the test verbatim as
written in the brief and seeing exactly that spurious failure before adding
the epsilon.

I also updated the stale prose inside `test_the_margin_constants_are_actually_large_enough`'s
docstring (it still cited the pre-ISO-273 "0.1 mm radius growth" / 3.55 / 1.775
figures right next to a `3.78` assertion) and the `1.775`/`3.55` reference at
the bottom of `layout.py`'s module docstring, so no stale numbers were left
sitting beside the corrected ones. This is documentation only; no assertion
values beyond what the brief specified were changed.

## Mutation contrast (the finding)

**Half 1 — stale literal (`_LITERAL_WALL_FLOOR_MM` temporarily set to `3.7`),
`python -m pytest tests/gen/test_layout.py -v`:**

```
tests/gen/test_layout.py::test_largest_clearance_hole_needs_more_than_the_old_hardcoded_pitch PASSED [ 10%]
tests/gen/test_layout.py::test_pitch_leaves_a_wall_between_the_widest_neighbours PASSED [ 20%]
tests/gen/test_layout.py::test_plate_leaves_an_edge_margin_around_the_outermost_feature PASSED [ 30%]
tests/gen/test_layout.py::test_positions_are_symmetric_about_the_plate_centre PASSED [ 40%]
tests/gen/test_layout.py::test_radii_track_the_larger_of_the_two_mating_holes PASSED [ 50%]
tests/gen/test_layout.py::test_sampler_records_a_plate_big_enough_for_its_own_features PASSED [ 60%]
tests/gen/test_layout.py::test_plate_size_is_serialised_in_the_sidecar PASSED [ 70%]
tests/gen/test_layout.py::test_the_margin_constants_still_cover_the_tables_they_came_from PASSED [ 80%]
tests/gen/test_layout.py::test_the_margin_constants_are_actually_large_enough PASSED [ 90%]
tests/gen/test_layout.py::test_the_literal_floor_is_not_below_the_derived_one FAILED [100%]

================================== FAILURES ===================================
_____________ test_the_literal_floor_is_not_below_the_derived_one _____________

    required = 2.0 * _worst_case_radial_excursion_mm()
>   assert _LITERAL_WALL_FLOOR_MM >= required - 1e-9, (
        f"the literal floor {_LITERAL_WALL_FLOOR_MM} is below the derived "
        f"requirement {required:.4f}; recompute it from the tables"
    )
E   AssertionError: the literal floor 3.7 is below the derived requirement 3.7800; recompute it from the tables
E   assert 3.7 >= (3.7800000000000002 - 1e-09)

tests\gen\test_layout.py:185: AssertionError
=========================== short test summary info ===========================
FAILED tests/gen/test_layout.py::test_the_literal_floor_is_not_below_the_derived_one
========================= 1 failed, 9 passed in 0.13s ==============================
```

Exactly one test fails — the new guard — and it names the 3.78 requirement.
Every other layout test, including `test_the_margin_constants_are_actually_large_enough`
(which now checks `_MIN_WALL_MM >= _LITERAL_WALL_FLOOR_MM`, i.e. `4.0 >= 3.7`)
and `test_the_margin_constants_still_cover_the_tables_they_came_from` (the
derived-floor test, `4.0 >= 3.78`), still passes. This reproduces the brief's
claim precisely: the stale `3.7` literal was silently non-binding before this
task, and neither pre-existing test caught it.

**Half 2 — restored (`_LITERAL_WALL_FLOOR_MM = 3.78`),
`python -m pytest tests/gen/test_layout.py -v`:**

```
tests/gen/test_layout.py::test_largest_clearance_hole_needs_more_than_the_old_hardcoded_pitch PASSED [ 10%]
tests/gen/test_layout.py::test_pitch_leaves_a_wall_between_the_widest_neighbours PASSED [ 20%]
tests/gen/test_layout.py::test_plate_leaves_an_edge_margin_around_the_outermost_feature PASSED [ 30%]
tests/gen/test_layout.py::test_positions_are_symmetric_about_the_plate_centre PASSED [ 40%]
tests/gen/test_layout.py::test_radii_track_the_larger_of_the_two_mating_holes PASSED [ 50%]
tests/gen/test_layout.py::test_sampler_records_a_plate_big_enough_for_its_own_features PASSED [ 60%]
tests/gen/test_layout.py::test_plate_size_is_serialised_in_the_sidecar PASSED [ 70%]
tests/gen/test_layout.py::test_the_margin_constants_still_cover_the_tables_they_came_from PASSED [ 80%]
tests/gen/test_layout.py::test_the_margin_constants_are_actually_large_enough PASSED [ 90%]
tests/gen/test_layout.py::test_the_literal_floor_is_not_below_the_derived_one PASSED [100%]

============================= 10 passed in 0.09s ==============================
```

## Full suite

`python -m pytest -q` (no marker filter, repo root):

```
258 passed in 21.08s
```

257 baseline + 1 new test (`test_the_literal_floor_is_not_below_the_derived_one`).

## Gate A

`python scripts/gate_a.py > /dev/null 2>&1; echo $?` (exit code captured
without a pipe):

```
EXIT_CODE=1
```

Tally (6 PASS / 3 SKIP, as expected — `Gate A: NOT CLEARED` because the three
SKIPs are the CI-only/artifact-only checks):

```
Y14.5 self-consistency          PASS   100% required; NOT standard-verified (see Y14.5 citation verified)
Monte Carlo convergence         PASS   +/-0.5% at N=100k
Checker reliability             PASS   mean 0.9982 over 200 pre-registered seeds (95% bootstrap CI [0.9964, 0.9995], 10000 resamples); fraction of seeds >= 0.95: 0.9800 (tested=11, excluded=1, tested |margin| in [3.50e-04, 4.50e-01]); threshold 0.95
Validation isolation            PASS   no core imports
Y14.5 citation verified         PASS   citation verified against standard
ISO 286 transcription verified  PASS   transcription verified against standard
NIST PMI conformance            SKIP   no export at nist_pmi_expected.csv
TolAnalyst agreement            SKIP   no export at tolanalyst_verdicts.csv
Fresh clone pipeline            SKIP   requires a clean-clone CI run to verify honestly; not checked in-process
```

## Tier 1 difficulty ladder, seeds 0-199 (unchanged, as expected)

Ran the exact snippet from the plan (`docs/superpowers/plans/2026-08-01-iso273-traceability.md`):

```
d1: 31/159 = 19.5% fail
d2: 99/301 = 32.9% fail
d3: 239/452 = 52.9% fail
d4: 421/609 = 69.1% fail
```

Matches the reference d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1% exactly. This
task is tests-and-docs only and did not move it, as required.

## Production constants unchanged (confirmed)

```
$ grep -n "^_MIN_WALL_MM\|^_EDGE_MARGIN_MM" src/tolcad/gen/layout.py
59:_MIN_WALL_MM = 4.0
60:_EDGE_MARGIN_MM = 5.0
```

`git diff -- src/tolcad/gen/layout.py` touches only docstring prose (see
below) — no assignment line for either constant appears in the diff hunks.

## Commit

```
4db2f8f test: re-measure the layout floors against the ISO 273 grades
```

`git diff --stat` for the commit:

```
src/tolcad/gen/layout.py  | 25 +++++++++++++++---------
tests/gen/test_layout.py  | 51 ++++++++++++++++++++++++++++++++++++------------
2 files changed, 55 insertions(+), 21 deletions(-)
```

## Self-review

- Confirmed `git diff -- src/tolcad/gen/layout.py` contains no changes to the
  `_MIN_WALL_MM = 4.0` / `_EDGE_MARGIN_MM = 5.0` assignment lines — every hunk
  is inside the module docstring.
- Confirmed `layout.py` remains free of CAD imports (only edited prose,
  `from __future__ import annotations` and `collections.abc.Sequence` are the
  only imports, unchanged).
- Confirmed `_IT_MICRONS`, `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`, and
  `_TOL_FRACTION_RANGE` are untouched by this task (not present in the diff at
  all; this task only touched `layout.py` and `test_layout.py`).
- Re-read the new test's docstring against the brief's language for the
  finding narrative ("NEITHER layout test failed... it had simply stopped
  being a floor") — kept verbatim as given, since it is the crux of the
  finding and worth stating exactly.
- Cleaned up a small residual: `test_the_margin_constants_are_actually_large_enough`
  previously did a redundant local `from tolcad.gen.layout import
  _EDGE_MARGIN_MM, _MIN_WALL_MM` inside its body, duplicating the module-level
  import at the top of the file. Removed it since it's dead weight now that
  the assertions reference the hoisted constants; behavior is identical
  (verified by the full test run).
- Verified by direct computation (`clearance_hole_for` over `FASTENER_SIZES`
  x grades) that `largest_allowable = 2.5`, `largest_radius_growth = 0.215`,
  `largest_fraction = 1.34`, giving `excursion = 1.89` and
  `required_wall = 3.78` — matches the brief's numbers and the hoisted
  literals exactly, confirming the derived-floor test and the literal-floor
  test are consistent with each other post-fix.

## Concerns

- None outstanding for this task. The one departure from the brief's literal
  code (`- 1e-9` epsilon on the new assertion) was necessary to avoid a false
  failure from floating-point representation of `3.78` and is consistent with
  the existing style in the same file; it does not change the test's meaning
  or weaken the guard (3.78 is still required to be at or above the derived
  value to within a wide margin — the actual gap being guarded against, 0.03
  mm to 3.75, is four orders of magnitude larger than the epsilon).
- Gate A's "NOT CLEARED" verdict is expected and unchanged from before this
  task — it is driven by the three CI/artifact-only SKIPs, not by anything in
  this diff.
- Per the plan's "Open question for the human" (unchanged, not addressed by
  this task): the tapped hole (`hole_b`, fixed-fastener kind) still carries a
  flat +0.2/-0.0 band with no ISO citation behind it, documented as
  provably inert today. Out of scope for Task 3.
