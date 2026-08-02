# Task 2 report: fixed fasteners get a tapped hole

Branch `feat/pre-registration-prep`, starting HEAD `422c21f` (Task 1's landing commit,
`SUPPORTED_FITS = ("H7/g6", "H7/k6", "H7/p6")`). Baseline full suite at that HEAD:
**190 passed, 2 deselected**.

## Step 1-2: RED

Appended the four tests to `tests/gen/test_features.py` and the two tests to
`tests/gen/test_sampler.py`, verbatim from the brief. Ran:

```
python -m pytest tests/gen/test_features.py tests/gen/test_sampler.py -v -k "tapp or fixed_fasteners_get or structurally"
```

Verbatim output (trimmed of repeated traceback boilerplate for the parametrized cases,
all twelve failed):

```
collecting ... collected 37 items / 25 deselected / 12 selected

tests/gen/test_features.py::test_tapping_drill_is_tabulated_for_every_fastener_size FAILED [  8%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[3.0-2.5] FAILED [ 16%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[4.0-3.3] FAILED [ 25%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[5.0-4.2] FAILED [ 33%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[6.0-5.0] FAILED [ 41%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[8.0-6.8] FAILED [ 50%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[10.0-8.5] FAILED [ 58%]
tests/gen/test_features.py::test_tapped_hole_matches_the_coarse_pitch_series[12.0-10.2] FAILED [ 66%]
tests/gen/test_features.py::test_tapped_hole_is_always_smaller_than_its_fastener FAILED [ 75%]
tests/gen/test_features.py::test_unknown_fastener_size_rejected_by_tapped_hole FAILED [ 83%]
tests/gen/test_sampler.py::test_fixed_fasteners_get_a_tapped_hole_b_and_floating_ones_do_not FAILED [ 91%]
tests/gen/test_sampler.py::test_a_fixed_mate_is_structurally_not_a_floating_mate FAILED [100%]

FAILURES:
- All test_features.py failures: ImportError: cannot import name 'TAPPING_DRILL_MM'
  (or 'tapped_hole_for') from 'tolcad.gen.features'.
- test_fixed_fasteners_get_a_tapped_hole_b_and_floating_ones_do_not:
    AssertionError: a fixed fastener's hole_b must be tapped, i.e. smaller than the fastener
    assert 3.4 < 3.0
     +  where 3.0 = MateSpec(kind='fixed_fastener', nominal_mm=3.0,
        hole_a={'nominal': 3.4, ...}, hole_b={'nominal': 3.4, ...}, ...).nominal_mm
- test_a_fixed_mate_is_structurally_not_a_floating_mate:
    Failed: DID NOT RAISE <class 'ValueError'>

====================== 12 failed, 25 deselected in 0.16s ======================
```

This matches the brief's prediction exactly: ImportError on the features side,
assertion/no-raise failures on the sampler side because `hole_b` still carried the
same clearance diameter as `hole_a` for both fastener kinds.

## Step 3: Implementation

Applied verbatim from the brief:
- `src/tolcad/gen/features.py`: added `TAPPING_DRILL_MM` (after `SUPPORTED_FITS`,
  same position as `_CLEARANCE_HOLE_MM`/`_GRADE_INDEX` block precedes it) and
  `tapped_hole_for` (after `clearance_hole_for`).
- `src/tolcad/gen/sampler.py`: added `tapped_hole_for` to the `features` import,
  and inside `_tier1_mate` computed `hole_b = hole if kind == "floating_fastener"
  else tapped_hole_for(fastener_mm)`, then built `hole_b=dict(hole_b,
  position_tol=tol_b)` in the returned `MateSpec`. The allowable/`tol_a`/`tol_b`
  arithmetic above it (which uses `hole`, i.e. `hole_a`, per B-4's `T=(H-F)/2`
  for the fixed case) was left untouched.

`build.py` and `layout.py` were not touched, per the brief.

## Step 4: GREEN

```
python -m pytest tests/gen/test_features.py tests/gen/test_sampler.py -v
...
37 passed in 0.60s
```

Full suite:

```
python -m pytest -q -m "not slow"
...
202 passed, 2 deselected in 23.42s
```

202 = 190 (baseline) + 12 (new tests). No regressions, no unexpected new failures.

## Knock-on effects (confirmed, not assumed)

**(a) `tests/gen/test_build.py` containment sweep.**

```
python -m pytest tests/gen/test_build.py -v -m "not slow"
...
19 passed in 8.43s
```

`test_features_are_contained_and_disjoint_across_the_seed_sweep[1..4]` (each
parametrized case sweeps `range(50)` seeds, per its own source) passed at every
difficulty 1-4. It computes expected removed volume from `mate.hole_b["nominal"]`
via `_expected_removed_volume`, so it now derives that volume from the smaller
tapped diameter for fixed mates automatically, and the exact-equality
(`rel=1e-9, abs=1e-9`) containment/disjointness check still holds — confirming
`build.py`'s reliance on `mate.hole_b["nominal"]` picked up the change with no
code edit required.

**(b) Plate-size assertions.**

`test_a_plate_too_small_for_its_features_is_rejected` passed. `layout.py`'s
`feature_radii_mm` takes the max of the two hole diameters per mate, and since
`hole_a` (the clearance hole) is always >= the new tapped `hole_b`, the plate
sizing is driven by the same (larger) clearance-hole diameter as before — no
plate-size assertion regressed.

## Mandatory measurement: Tier 1 failure-rate table, seeds 0-199

```
python -c "
from tolcad.checker import check
from tolcad.gen.sampler import sample_assembly
for d in (1,2,3,4):
    f=t=0
    for s in range(200):
        for m in sample_assembly(s,d).mates:
            if m.kind=='iso_fit': continue
            t+=1
            if not check(m.to_check_dict()).assembles: f+=1
    print(f'd{d}: {f}/{t} = {100*f/t:.1f}% fail')
"
```

Output:

```
d1: 31/159 = 19.5% fail
d2: 99/301 = 32.9% fail
d3: 239/452 = 52.9% fail
d4: 421/609 = 69.1% fail
```

**Table did NOT move** — identical to the reference (d1 19.5% / d2 32.9% / d3 52.9% /
d4 69.1%) at `422c21f`, to the fraction count and percentage. This is exactly as
predicted: floating mates keep `hole_b = hole` unchanged (both `hole_a` and
`hole_b` are still the same clearance hole for that kind), so their inputs to B-4
are bit-for-bit identical to before. Fixed mates now get a tapped `hole_b`, but
`fastener_assembles` never reads `hole_b`'s size in the fixed case, so their B-4
inputs are unaffected too. Both mate kinds' Tier 1 verdicts are therefore
unchanged.

## Commit

SHA: `ae63279`
Message: `feat: fixed fasteners thread into a tapped hole, so the kinds differ in geometry`
(plus the `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>` trailer).
Files: `src/tolcad/gen/features.py`, `src/tolcad/gen/sampler.py`,
`tests/gen/test_features.py`, `tests/gen/test_sampler.py` (4 files changed,
124 insertions, 1 deletion).

## Self-review notes

- Diffed `src/tolcad/gen/features.py` and `src/tolcad/gen/sampler.py` against the
  brief's exact code blocks: both match verbatim (constant table, docstrings,
  `hole_b` selection line, and the comment above it).
- Confirmed `y14_5.py` was not touched (`git diff` shows only the four listed files
  staged; no other tracked file changed).
- Confirmed `build.py` and `layout.py` are untouched, as instructed, and that their
  existing reliance on `mate.hole_b["nominal"]` / `max(hole_a, hole_b)` diameters
  was sufficient to propagate the change with zero code edits there.
- `tapped_hole_for` reuses `_HOLE_UPPER_DEV_MM` (+0.2/-0.0) for the tapped hole's
  tolerance band, same as `clearance_hole_for` — consistent with the rest of the
  module's H13-ish convention; no new tolerance constant was invented.
- No stray blank-line/formatting issues in the diff; two-blank-line separation
  before top-level defs matches the file's existing style.

## Concerns

None. Every predicted outcome (RED failures, GREEN pass count, both knock-on
effects, and the unchanged failure-rate table) matched exactly on the first
attempt; no deviation required investigation.
