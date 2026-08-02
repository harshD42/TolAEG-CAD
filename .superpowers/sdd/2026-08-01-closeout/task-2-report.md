# Task 2 report: make both integrity pins two-sided

Commit: `062316e` on `main` (parent `d7285f9`), pushed to
`https://github.com/harshD42/TolAEG-CAD` (`d7285f9..062316e main -> main`).

## RED (Step 2) — verbatim

Command: `python -m pytest tests/test_suite_integrity_script.py -v -k "measurement_above_the_pin or both_pins"`

(The brief's literal `-k "two_sided or both_pins"` matched only 1 test, because
`test_a_measurement_above_the_pin_fails_too`'s name contains neither
substring — pytest `-k` is a keyword substring match on the node id, not the
docstring. Re-ran with a keyword that actually selects both new tests.)

```
collecting ... collected 9 items / 7 deselected / 2 selected

tests/test_suite_integrity_script.py::test_a_measurement_above_the_pin_fails_too FAILED [ 50%]
tests/test_suite_integrity_script.py::test_both_pins_are_measured_values_not_round_numbers FAILED [100%]

================================== FAILURES ===================================
_________________ test_a_measurement_above_the_pin_fails_too __________________
    ...
>       ok_low, msg_low = mod.check_two_sided(90.0, 95.0, 0.5)
                          ^^^^^^^^^^^^^^^^^^^
E       AttributeError: module 'check_suite_integrity' has no attribute 'check_two_sided'

tests\test_suite_integrity_script.py:112: AttributeError
____________ test_both_pins_are_measured_values_not_round_numbers _____________
    ...
>           value = getattr(mod, name)
                    ^^^^^^^^^^^^^^^^^^
E           AttributeError: module 'check_suite_integrity' has no attribute 'COVERAGE_MEASURED'

tests\test_suite_integrity_script.py:130: AttributeError
=========================== short test summary info ===========================
FAILED tests/test_suite_integrity_script.py::test_a_measurement_above_the_pin_fails_too
FAILED tests/test_suite_integrity_script.py::test_both_pins_are_measured_values_not_round_numbers
======================= 2 failed, 7 deselected in 0.08s =======================
```

## Directional-assertion gate (extra, before implementing for real)

The brief's closing instruction says to watch the "improvement must also
fail" assertion fail specifically, not just the `ImportError`/`AttributeError`
above. To do that honestly, I first landed a deliberately **one-sided**
`check_two_sided` stub (only checks the lower bound) and re-ran just that
test:

```
tests/test_suite_integrity_script.py::test_a_measurement_above_the_pin_fails_too FAILED [100%]

    ok_high, msg_high = mod.check_two_sided(99.0, 95.0, 0.5)
>   assert not ok_high, "an improvement must also fail -- the pin has detached"
E   AssertionError: an improvement must also fail -- the pin has detached
E   assert not True

tests\test_suite_integrity_script.py:116: AssertionError
1 failed, 8 deselected in 0.07s
```

This confirms the test fails on the exact directionality assertion, not
merely on a missing symbol. Only after seeing this did I implement the real,
symmetric `check_two_sided`.

## GREEN (Step 4)

`python -m pytest tests/test_suite_integrity_script.py -v`:

```
tests/test_suite_integrity_script.py::test_the_script_exists PASSED      [ 11%]
tests/test_suite_integrity_script.py::test_it_names_the_six_core_modules PASSED [ 22%]
tests/test_suite_integrity_script.py::test_the_coverage_pin_is_a_measured_value_not_a_round_number PASSED [ 33%]
tests/test_suite_integrity_script.py::test_the_script_reports_and_exits_nonzero_when_a_layer_fails PASSED [ 44%]
tests/test_suite_integrity_script.py::test_the_cosmic_ray_config_runs_the_whole_core_subset PASSED [ 55%]
tests/test_suite_integrity_script.py::test_the_mutation_pin_is_measured_not_aspirational PASSED [ 66%]
tests/test_suite_integrity_script.py::test_the_mutation_tolerance_covers_the_display_rounding_it_is_pinned_from PASSED [ 77%]
tests/test_suite_integrity_script.py::test_a_measurement_above_the_pin_fails_too PASSED [ 88%]
tests/test_suite_integrity_script.py::test_both_pins_are_measured_values_not_round_numbers PASSED [100%]

9 passed in 0.13s
```

Full suite (`python -m pytest -q`):

```
........................................................................ [ 18%]
........................................................................ [ 37%]
........................................................................ [ 56%]
........................................................................ [ 75%]
........................................................................ [ 94%]
....................                                                     [100%]
380 passed in 37.42s
```

380 = 378 baseline (Task 1's landed count) + 2 new tests. No skips, no
failures.

## Gate A

`python scripts/gate_a.py > out.txt 2>&1; echo $?` (captured directly, no
pipe) → **exit 1**, as expected. Report body unchanged from Task 1's
baseline: 6 PASS / 3 SKIP (NIST PMI conformance, TolAnalyst agreement, Fresh
clone pipeline all SKIP for their documented reasons), so "Gate A: NOT
CLEARED". `scripts/gate_a.py` itself was not touched (Task 3's scope).

## Tree cleanliness

`git status --short` before staging showed only the two intended files
modified:

```
 M scripts/check_suite_integrity.py
 M tests/test_suite_integrity_script.py
```

No `src/` or `tests/fixtures/` files were touched — the session-scoped
finalizer in `tests/conftest.py` did not fire, and none of the forbidden
constants (`_IT_MICRONS`, `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`,
`_TOL_FRACTION_RANGE`, `_MIN_WALL_MM`, `_EDGE_MARGIN_MM`) or `scripts/gate_a.py`
were edited. `cosmic-ray` / `check_suite_integrity.py` itself was never
invoked in this task — only pytest and `scripts/gate_a.py`.

## Commit and push

Commit `062316e`: "fix: make both integrity pins two-sided so an improvement
cannot detach them". Pushed cleanly:

```
To https://github.com/harshD42/TolAEG-CAD.git
   d7285f9..062316e  main -> main
```

## What changed, functionally

`scripts/check_suite_integrity.py`:
- Removed `COVERAGE_FLOOR` (one-sided) → `COVERAGE_MEASURED = 94.74`,
  `COVERAGE_TOLERANCE = 0.50`.
- Removed the derived `MUTATION_FLOOR` → `run_mutation_score` now compares
  directly against `MUTATION_MEASURED = 95.89` / `MUTATION_TOLERANCE = 0.50`
  via `check_two_sided`.
- Added `check_two_sided(measured, pinned, tolerance) -> tuple[bool, str]`:
  fails below `pinned - tolerance` ("... is below the pin ..."), fails above
  `pinned + tolerance` with a message that explicitly says "the tree improved
  and the pin has detached. Re-pin it and record why.", and only passes
  in between.
- Both `run_coverage()` and `run_mutation_score()` now call
  `check_two_sided` and print its message; `main()`'s report rows now show
  `pin <value> +/- <tolerance>` instead of `floor <value>`.

`tests/test_suite_integrity_script.py`:
- Appended the two brief tests verbatim:
  `test_a_measurement_above_the_pin_fails_too` and
  `test_both_pins_are_measured_values_not_round_numbers`.
- Updated three pre-existing tests that referenced the now-removed
  `COVERAGE_FLOOR` / `MUTATION_FLOOR` symbols so they keep testing the same
  invariants against the new names, rather than deleting them:
  - `test_the_coverage_floor_is_a_measured_value_not_a_round_number` →
    renamed `test_the_coverage_pin_is_a_measured_value_not_a_round_number`,
    now asserts on `COVERAGE_MEASURED`.
  - `test_the_mutation_floor_is_measured_not_aspirational` → renamed
    `test_the_mutation_pin_is_measured_not_aspirational`, body unchanged
    (already asserted on `MUTATION_MEASURED`, just had a stale docstring
    referencing the removed `MUTATION_FLOOR`).
  - `test_the_mutation_floor_tolerates_the_display_rounding_it_is_pinned_from`
    → renamed `test_the_mutation_tolerance_covers_the_display_rounding_it_is_pinned_from`;
    replaced the `MUTATION_FLOOR == MEASURED - TOLERANCE` arithmetic
    assertions (which no longer apply — there is no derived floor anymore)
    with two direct `check_two_sided` calls proving a raw score that differs
    from the displayed pin only by rounding still passes in **both**
    directions, which is the property this test actually exists to protect.
  - The pin-not-a-round-number invariant is now covered twice (once per
    constant individually, once for both together in the brief's new test);
    left as intentional redundancy per the instruction to keep the existing
    test rather than delete it.

## Self-review notes

- Verified with `grep -rn "COVERAGE_FLOOR\|MUTATION_FLOOR"` that no live code
  references either removed symbol; the only hits left are prose in a
  `HISTORY` comment block and a docstring, both describing the prior
  one-sided design for context.
- Verified `check_two_sided`'s upward-failure message contains the literal
  substring `"re-pin"` (case-insensitive), which is what
  `test_a_measurement_above_the_pin_fails_too` checks for.
- Double-checked `git diff HEAD~1 HEAD -- scripts/check_suite_integrity.py
  tests/test_suite_integrity_script.py` touches only those two files, and
  that neither `src/` nor `scripts/gate_a.py` appears anywhere in the diff.
- The two `print(...)` calls added inside `run_coverage()` /
  `run_mutation_score()` are new stdout side effects; they don't affect any
  existing assertion (the self-test-failure path in `main()` never calls
  these functions, and `test_the_script_reports_and_exits_nonzero_when_a_layer_fails`
  only checks the subprocess return code and that `"FAIL"` appears somewhere
  in stdout, which is still produced by `_print_report`).

## Concerns

- None blocking. One minor observation for whoever owns Task 5/9: the
  `check_two_sided` messages are now printed twice in a live run of
  `check_suite_integrity.py` — once from inside `run_coverage`/
  `run_mutation_score`, and the summary line again from `_print_report`. This
  is intentional (the brief said "wire both layers through it, and print the
  returned message") but makes the live-run output slightly more verbose than
  before. Not a correctness issue, and Task 5 (the only place that actually
  runs `check_suite_integrity.py` end-to-end) can absorb it if it matters for
  a CI log-format check.
- I did not re-run `check_suite_integrity.py` itself, per the explicit
  instruction not to (cosmic-ray, ~25 min, must not run concurrently with
  anything). The two pinned constants (94.74 / 95.89) are taken as given from
  the architect's end-to-end run and were not re-derived.
