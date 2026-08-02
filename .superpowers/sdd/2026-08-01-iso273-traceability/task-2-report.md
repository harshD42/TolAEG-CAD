# Task 2 report: ISO 273 clearance-hole tolerance grade

## Status
Complete. All steps in the brief executed as written; no deviations from the
prescribed values or code.

## RED (Step 2) — verbatim

Command: `python -m pytest tests/gen/test_features.py -v -k "series or flat or widens or mmc or cites"`

```
collecting ... collected 34 items / 15 deselected / 19 selected

tests/gen/test_features.py::test_fastener_sizes_are_the_common_metric_series PASSED [  5%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[3.0-2.5] PASSED [ 10%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[4.0-3.3] PASSED [ 15%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[5.0-4.2] PASSED [ 21%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[6.0-5.0] PASSED [ 26%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[8.0-6.8] PASSED [ 31%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[10.0-8.5] PASSED [ 36%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[12.0-10.2] PASSED [ 42%]
tests/gen/test_features.py::test_each_series_carries_its_iso273_tolerance_grade FAILED [ 47%]
tests/gen/test_features.py::test_clearance_hole_upper_dev_comes_from_the_series_grade[3.0-close-0.12] FAILED [ 52%]
tests/gen/test_features.py::test_clearance_hole_upper_dev_comes_from_the_series_grade[3.0-loose-0.3] FAILED [ 57%]
tests/gen/test_features.py::test_clearance_hole_upper_dev_comes_from_the_series_grade[8.0-close-0.15] FAILED [ 63%]
tests/gen/test_features.py::test_clearance_hole_upper_dev_comes_from_the_series_grade[8.0-normal-0.22] FAILED [ 68%]
tests/gen/test_features.py::test_clearance_hole_upper_dev_comes_from_the_series_grade[8.0-loose-0.36] FAILED [ 73%]
tests/gen/test_features.py::test_clearance_hole_upper_dev_comes_from_the_series_grade[12.0-loose-0.43] FAILED [ 78%]
tests/gen/test_features.py::test_clearance_hole_tolerance_is_no_longer_flat FAILED [ 84%]
tests/gen/test_features.py::test_tolerance_widens_with_series_at_a_fixed_fastener FAILED [ 89%]
tests/gen/test_features.py::test_hole_mmc_is_unaffected_by_the_tolerance_change PASSED [ 94%]
tests/gen/test_features.py::test_features_module_cites_its_primary_sources FAILED [100%]

================================== FAILURES ===================================
_____________ test_each_series_carries_its_iso273_tolerance_grade _____________
    from tolcad.gen.features import SERIES_TOLERANCE_GRADE
E   ImportError: cannot import name 'SERIES_TOLERANCE_GRADE' from 'tolcad.gen.features'

__ test_clearance_hole_upper_dev_comes_from_the_series_grade[3.0-close-0.12] __
    assert hole["upper_dev"] == pytest.approx(expected_upper_dev)
E   assert 0.2 == 0.12 ± 1.2e-07
E     Obtained: 0.2
E     Expected: 0.12 ± 1.2e-07
(same pattern for the other 5 parametrized cases: obtained 0.2 in every case)

____________ test_clearance_hole_tolerance_is_no_longer_flat ____________
E   AssertionError: tolerance is constant across all holes: {0.2}
E   assert 1 > 1

____________ test_tolerance_widens_with_series_at_a_fixed_fastener ____________
E   AssertionError: M3.0: 0.2, 0.2, 0.2
E   assert 0.2 < 0.2

____________ test_features_module_cites_its_primary_sources ____________
    assert "ISO 2306" in text
E   assert 'ISO 2306' in '...Clearance-hole diameters follow the common metric
    close/normal/loose series...but it has NOT been checked against the primary
    standard text...'

=========================== short test summary info ===========================
FAILED test_each_series_carries_its_iso273_tolerance_grade
FAILED test_clearance_hole_upper_dev_comes_from_the_series_grade[3.0-close-0.12]
FAILED test_clearance_hole_upper_dev_comes_from_the_series_grade[3.0-loose-0.3]
FAILED test_clearance_hole_upper_dev_comes_from_the_series_grade[8.0-close-0.15]
FAILED test_clearance_hole_upper_dev_comes_from_the_series_grade[8.0-normal-0.22]
FAILED test_clearance_hole_upper_dev_comes_from_the_series_grade[8.0-loose-0.36]
FAILED test_clearance_hole_upper_dev_comes_from_the_series_grade[12.0-loose-0.43]
FAILED test_clearance_hole_tolerance_is_no_longer_flat
FAILED test_tolerance_widens_with_series_at_a_fixed_fastener
FAILED test_features_module_cites_its_primary_sources
10 failed, 9 passed, 15 deselected in 0.12s
```

Matched the brief's prediction exactly: `ImportError` for `SERIES_TOLERANCE_GRADE`,
deviation assertions failing at the old flat `0.2`, and
`test_hole_mmc_is_unaffected_by_the_tolerance_change` passing on arrival (the
deliberate regression pin).

## GREEN (Step 4)

`python -m pytest tests/gen/test_features.py -v` → **34 passed** (all pre-existing
tests plus the 6 new test functions / 11 new test items, none broken).

## Full suite

`python -m pytest -q` (no marker filter) → **244 passed** (baseline 233 + 11 new
test items from the parametrized additions, 0 failed).
`python -m pytest -q -m "not slow"` → 242 passed, 2 deselected.

## Measured Tier 1 failure-rate table (seeds 0-199)

| difficulty | failures / total | rate | required (unchanged) |
|---|---|---|---|
| d1 | 31/159 | 19.5% | 19.5% |
| d2 | 99/301 | 32.9% | 32.9% |
| d3 | 239/452 | 52.9% | 52.9% |
| d4 | 421/609 | 69.1% | 69.1% |

Unchanged to one decimal place, confirming the upper-deviation change cannot
move any Tier 1 verdict (hole MMC = nominal + lower_dev, and lower_dev stays 0).

## Layout derived-floor test (`tests/gen/test_layout.py`)

`test_the_margin_constants_still_cover_the_tables_they_came_from` — **PASSED**.

Re-derived by hand to confirm the brief's prediction:
- Largest allowable (M12 loose): hole MMC 14.5 − fastener 12.0 = 2.5 mm.
- Largest radius growth: M12 loose `upper_dev` / 2 = 0.215 / 2... — actual
  computed value from `_worst_case_radial_excursion_mm()` is 0.215 mm (radius
  growth term), giving:
  - `largest_allowable = 2.5`, `largest_fraction (d4) = 1.34`, `largest_radius_growth = 0.215`
  - `required_wall = 2 * (2.5 * 1.34 / 2 + 0.215) = 3.78 mm`
- Compared against `_MIN_WALL_MM = 4.0` → 4.0 ≥ 3.78, test passes, matching the
  brief's prediction exactly.

Full `tests/gen/test_layout.py` run: 9 passed, 0 failed.

## Commit

SHA: `d78c39e2b0536a88ade2f499dd10f7a5fbaac1b4`
Message: `feat: clearance holes carry their ISO 273 series tolerance grade` +
`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>` trailer.

Files touched: `src/tolcad/gen/features.py`, `tests/gen/test_features.py` only.
No checker-core module (`types`, `y14_5`, `iso286`, `montecarlo`, `checker`,
`reliability`) touched. No CAD import introduced. `_CLEARANCE_HOLE_MM` and
`TAPPING_DRILL_MM` dict values unchanged (diff confirms no line inside either
dict literal changed).

## Self-review notes

- Diff matches the brief's prescribed code verbatim: module docstring,
  `SERIES_TOLERANCE_GRADE`, `_TAPPED_HOLE_UPPER_DEV_MM` (with its "provably
  inert" rationale), the rewritten `clearance_hole_for`, the `_HOLE_UPPER_DEV_MM`
  → `_TAPPED_HOLE_UPPER_DEV_MM` rename in `tapped_hole_for`, and the
  `it_grade` import.
- **Concern (out of scope, flagging only):** the comment block directly above
  `TAPPING_DRILL_MM` (unchanged, lines ~69-78) still reads "Same provenance
  caveat as `_CLEARANCE_HOLE_MM` above ... have NOT been checked against the
  primary standard, so no edition is cited." This now contradicts the new
  module docstring, which states ISO 2306 Table 1 *was* checked against the
  primary standard on 2026-08-01 and matches exactly. The brief's Step 3 did
  not list this comment block among the ones to replace, and the
  `test_features_module_cites_its_primary_sources` regression test only forbids
  the exact substring "not been checked against the primary" (lowercase
  "not"), which this comment avoids by capitalizing "NOT" — so the test does
  not catch the inconsistency. I left it untouched per the brief's literal
  scope, but a follow-up should reconcile or remove this stale caveat since it
  now reads as self-contradictory within the same file.
- No other concerns. All six required tests pass, the regression pin behaved
  as designed, the ladder is provably unmoved, and the layout floor test's
  arithmetic matches the brief's prediction to the decimal.
