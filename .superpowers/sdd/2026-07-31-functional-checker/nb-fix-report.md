# NB-1 / NB-2 fix report

## NB-1: `fastener_assembles` pooled-clearance model

Rewrote `src/tolcad/y14_5.py::fastener_assembles` to implement the verified model:

- Floating: `margin = (H_a - F) + (H_b - F) - (T_a + T_b)`
- Fixed:    `margin = (H_a - F) - (T_a + T_b)` (hole_b's MMC does not appear)

Changes made:
1. Guard `H_i < F` for holes the fastener must physically pass through: both
   holes for floating, `hole_a` only for fixed. Raises `ValueError`. Tested by
   `test_floating_raises_when_hole_a_below_fastener_mmc`,
   `test_floating_raises_when_hole_b_below_fastener_mmc`,
   `test_fixed_raises_when_hole_a_below_fastener_mmc`, and (negative case)
   `test_fixed_does_not_raise_when_hole_b_below_fastener_mmc`.
2. `margin` documented as DIAMETRAL in the function docstring; `detail` now
   carries `"margin_unit": "diametral_mm"` and `"radial_slack": margin / 2.0`.
3. Removed `governing_hole` / `governing_hole_mmc` from `detail`. Replaced
   with `clearance_a`, `clearance_b` (None for fixed), `position_tol_a`,
   `position_tol_b`, `hole_a_mmc`, `hole_b_mmc`, `fastener_mmc`.
4. Feature-type validation is now condition-dependent: `hole_a` must always
   be INTERNAL; `hole_b` must be INTERNAL only when `condition == "floating"`.
   For `"fixed"`, `hole_b`'s feature_type is unconstrained (may be EXTERNAL,
   e.g. a press-fit pin).
5. Added symmetry tests: `test_floating_fully_swap_invariant` (full
   `(H_a,T_a)<->(H_b,T_b)` swap invariance), `test_fixed_symmetric_in_position_tol_swap_only`
   (T-only swap invariance), and `test_fixed_not_swap_invariant_on_full_hole_swap`
   (explicitly asserts fixed is NOT fully swap-invariant).
6. Documented the three scope limits (projected tolerance zone assumption on
   `T_b` in the fixed case, unmodelled datum shift, and out-of-scope items:
   composite tolerance, pattern analysis, tilt beyond projected zone, thread
   class, fastener bending) in the function docstring.
7. Documented why ignoring MMC bonus is exact (not conservative) — the
   algebraic cancellation — and the one unsafe corner (a fixed feature
   distinct from the shank carrying its own MMC modifier), also in the
   function docstring. The model assumes RFS on the fixed feature.
8. Recomputed every existing fastener test's expected value from the new
   formula (arithmetic below) instead of preserving the old wrong values.

### Recomputed test values

All use `M8_BOLT` = `FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL)`, so `F = mmc = 8.0`.

**`test_floating_fastener_assembles_at_allowable_tolerance`**
H_a=H_b=8.5, T_a=T_b=0.5:
`margin = (8.5-8.0) + (8.5-8.0) - (0.5+0.5) = 1.0 - 1.0 = 0.0` → assembles (unchanged from old value; coincidence of the symmetric case).

**`test_floating_fastener_fails_above_allowable_tolerance`** (changed: was -0.1)
H_a=H_b=8.5, T_a=T_b=0.6:
`margin = (8.5-8.0) + (8.5-8.0) - (0.6+0.6) = 1.0 - 1.2 = -0.2`

**`test_fixed_fastener_is_stricter_than_floating`**
H_a=H_b=8.5, T_a=T_b=0.5, fixed:
`margin = (8.5-8.0) - (0.5+0.5) = 0.5 - 1.0 = -0.5` (still fails; no assertion on the exact value in this test, only `assembles`).

**`test_asymmetric_holes_worse_on_hole_a`** (changed: was asserted False, now True)
H_a=H_b=8.5, T_a=0.6, T_b=0.1, floating:
`margin = (8.5-8.0) + (8.5-8.0) - (0.6+0.1) = 1.0 - 0.7 = +0.3` → assembles.

**`test_asymmetric_holes_worse_on_hole_b`** (changed: was asserted False, now True)
H_a=H_b=8.5, T_a=0.1, T_b=0.6, floating:
`margin = (8.5-8.0) + (8.5-8.0) - (0.1+0.6) = 1.0 - 0.7 = +0.3` → assembles (floating is symmetric, same value as above).

**`test_argument_order_does_not_change_verdict_for_asymmetric_hole_sizes`** (changed: was -0.25, now -0.05)
big=8.5, tight=8.05, T_a=T_b=0.3, floating:
`margin = (8.5-8.0) + (8.05-8.0) - (0.3+0.3) = 0.5 + 0.05 - 0.6 = -0.05` → still fails, order-independent.

**New: `test_allows_external_hole_b_when_fixed`**
hole_a=8.5 (T=0.1), press_fit_pin mmc=9.0 (T=0.1), fixed:
`margin = (8.5-8.0) - (0.1+0.1) = 0.5 - 0.2 = 0.3` → assembles.

**New: `test_fixed_does_not_raise_when_hole_b_below_fastener_mmc`** (spec's exact example)
H_a=9.0, H_b=7.9, T_a=T_b=0.0, F=8.0, fixed:
`margin = (9.0-8.0) - (0.0+0.0) = 1.0` → assembles, no ValueError (H_b's undersize is irrelevant in fixed).

**New symmetry tests** (arithmetic in test docstrings):
- `test_floating_fully_swap_invariant`: H_a=8.5/T=0.3, H_b=8.6/T=0.4 → full swap gives identical margin (both directions compute the same sum).
- `test_fixed_symmetric_in_position_tol_swap_only`: H_a=8.5, H_b=8.6, swapping only T_a<->T_b: both give `margin = (8.5-8.0) - (0.3+0.4) = -0.2`.
- `test_fixed_not_swap_invariant_on_full_hole_swap`: original `margin = 0.5 - 0.7 = -0.2`; fully swapped (H_b's size now feeds the formula) `margin = 0.6 - 0.7 = -0.1` — different, as required.

`checker.py` was left unchanged: it still constructs `hole_b` as INTERNAL
unconditionally for both `floating_fastener` and `fixed_fastener` dict
dispatch. No test exercises an EXTERNAL `hole_b` through `check()`, and NB-1
scoped the condition-dependent validation to `fastener_assembles` itself
(callers that want a press-fit-pin `hole_b` must call `fastener_assembles`
directly with `FeatureType.EXTERNAL`, as the new unit test does). This is a
pre-existing limitation of the dict-based dispatch layer, not something NB-1
asked to change, and is noted here for visibility rather than silently left.

## NB-2: Gate A reliability sensitive band

`scripts/gate_a.py::_RELIABILITY_MATES` now includes 6 new mates (2 per Tier
1 type: `virtual_condition`, `floating_fastener`, `fixed_fastener`) with
`|margin| ≈ 3.5e-4`, deliberately placed inside the sensitive band
`[BOUNDARY_BAND * epsilon, ~5*epsilon] = [2e-4, 5e-4]` given
`_RELIABILITY_EPSILON = 1e-4`. One mate per type is margin ≈ +3.5e-4
(assembles), one is ≈ -3.5e-4 (fails), so both verdict directions are
represented. The original 6 far-from-boundary mates were kept so the
measurement still spans both regimes.

`src/tolcad/reliability.py::StabilityResult` gained `min_abs_margin` /
`max_abs_margin` fields (computed over tested, non-excluded mates), and
`gate_a.py`'s report line now prints the tested band, e.g.:

```
Checker reliability  PASS  measured 1.0000 (tested=12, excluded=0, tested |margin| in [3.50e-04, 8.50e-01]); threshold 0.95
```

Verified the metric is no longer tautological: running `verdict_stability`
over the new mate set across seeds 0-299 (ad hoc check, not committed to the
suite) gives values ranging from 0.9167 to 1.0000, with 34/300 seeds scoring
below 1.0 — i.e. the perturbation can and does flip verdicts for some seeds
now. For the pinned `_RELIABILITY_SEED = 20260731`, the measured value is
1.0000 with `tested=12, excluded=0`, which clears the (untouched)
`RELIABILITY_THRESHOLD = 0.95`. No mate was tuned to force this outcome; the
sensitive-band mates were chosen purely to land inside the target band, and
the row reports whatever the seed produces (had it fallen below 0.95 the row
would read FAIL, per the constraint).

## Verification

- `python -m pytest -q` → 87 passed, 1 xfailed (the deliberate
  `test_transcription_source_recorded` xfail; no other change).
- `python scripts/gate_a.py` → exit 1, `NOT CLEARED` (unchanged — still
  blocked on the unrelated SKIP rows: pending citation markers, missing
  oracle CSVs, fresh-clone criterion — none of which NB-1/NB-2 touch).

## Findings not fixed

None. Both NB-1 and NB-2 were fully implemented as specified; no scope item
was left out.
