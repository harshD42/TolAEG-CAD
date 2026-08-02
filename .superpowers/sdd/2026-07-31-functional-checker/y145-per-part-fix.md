# Floating-fastener per-part correction: test updates

## Context

`fastener_assembles` in `src/tolcad/y14_5.py` was corrected from a POOLED
floating model, `margin = (H_a-F) + (H_b-F) - (T_a+T_b)`, to the PER-PART
rule mandated by ASME Y14.5-2018 Nonmandatory Appendix B, section B-3:

    margin = min(H_a - F - T_a,  H_b - F - T_b)

The FIXED model (B-4) is unchanged:

    margin = (H_a - F) - (T_a + T_b)

The implementation change was already present in the working tree and was
NOT modified by this task. Only `tests/test_y14_5.py` and
`tests/test_reliability.py` were edited.

## Tests fixed (recomputed arithmetic)

### 1. `test_floating_fastener_fails_above_allowable_tolerance`
H_a=H_b=8.5, F=8.0, T_a=T_b=0.6:
- margin_a = margin_b = 8.5-8.0-0.6 = -0.1
- margin = min(-0.1, -0.1) = **-0.1** (was -0.2 under pooled model)
- assembles: False (unchanged verdict, new magnitude)

### 2. `test_asymmetric_holes_worse_on_hole_a`
H_a=H_b=8.5, F=8.0, T_a=0.6, T_b=0.1:
- margin_a = 8.5-8.0-0.6 = -0.1
- margin_b = 8.5-8.0-0.1 = +0.4
- margin = min(-0.1, +0.4) = **-0.1**
- assembles: **False** (was True under pooled model, margin +0.3) — hole_a's
  own deficit now governs instead of being averaged away by hole_b's surplus.

### 3. `test_asymmetric_holes_worse_on_hole_b`
H_a=H_b=8.5, F=8.0, T_a=0.1, T_b=0.6 (tolerances swapped from case 2):
- margin_a = 8.5-8.0-0.1 = +0.4
- margin_b = 8.5-8.0-0.6 = -0.1
- margin = min(+0.4, -0.1) = **-0.1**
- assembles: **False** (was True, margin +0.3). Matches case 2 exactly,
  confirming min() is commutative in (H_a,T_a)<->(H_b,T_b).

### 4. `test_floating_fully_swap_invariant`
H_a=8.5, T_a=0.3; H_b=8.6, T_b=0.4; F=8.0:
- margin_a = 8.5-8.0-0.3 = 0.2
- margin_b = 8.6-8.0-0.4 = 0.2
- margin = min(0.2, 0.2) = **0.2** (was 0.4 under pooled model)
- Swapped (H_a=8.6/T=0.4, H_b=8.5/T=0.3): margin_a=0.2, margin_b=0.2,
  margin = 0.2 — swap-invariance confirmed under the new formula too.

### 5. `test_argument_order_does_not_change_verdict_for_asymmetric_hole_sizes`
big: H=8.5, T=0.3; tight: H=8.05, T=0.3; F=8.0:
- margin_big = 8.5-8.0-0.3 = +0.2
- margin_tight = 8.05-8.0-0.3 = -0.25
- margin = min(+0.2, -0.25) = **-0.25** (was -0.05 under pooled model)
- assembles: False (unchanged verdict, new magnitude); order-independence
  re-verified (min is commutative).

### 6. `test_detail_radial_slack_is_half_the_diametral_margin`
hole_a=hole_b=8.5, T_a=T_b=0.1, F=8.0:
- margin_a = margin_b = 8.5-8.0-0.1 = 0.4
- margin = min(0.4, 0.4) = **0.4** (was 0.8 under pooled model)
- radial_slack = margin / 2 = **0.2** (was 0.4)

### 7. `test_min_max_abs_margin_report_actual_extremes_of_tested_set` (test_reliability.py)
`_mate(t)` passes the SAME hole dict as both `hole_a` and `hole_b`, so
per-part floating reduces to `margin = min(H-F-T, H-F-T) = H-F-T`, with
H-F = 8.5-8.0 = 0.5:
- position_tol=0.05 -> margin = 0.5-0.05 = **0.45** (was 0.90)
- position_tol=0.10 -> margin = 0.5-0.10 = **0.40** (was 0.80)
- position_tol=0.20 -> margin = 0.5-0.20 = **0.30** (was 0.60)
- min_abs_margin = **0.30** (was 0.6), max_abs_margin = **0.45** (was 0.9)

All values above were cross-checked by executing `fastener_assembles` /
`verdict_stability` directly against the corrected implementation, not
just derived on paper.

## New tests added (Appendix B worked examples)

### `test_b3_worked_example_boundary_case_assembles` (B-3)
"Given that the fasteners in Figure B-1 are 6 diameter maximum and the
clearance holes are 6.44 diameter minimum ... T = 6.44 - 6 = 0.44 diameter
for each part."
F=6.0, H_a=H_b=6.44, T_a=T_b=0.44 (floating):
- margin = min(6.44-6.0-0.44, 6.44-6.0-0.44) = min(0.0, 0.0) = **0.0**
- assembles: True (exact boundary)

### `test_b4_worked_example_boundary_case_assembles` (B-4)
"T = (6.44-6)/2 = 0.22 diameter for each part."
F=6.0, H_a=H_b=6.44, T_a=T_b=0.22 (fixed):
- margin = (6.44-6.0) - (0.22+0.22) = 0.44 - 0.44 = **0.0**
- assembles: True (exact boundary)

### `test_b4_worked_example_unequal_split_boundary_case_assembles` (B-4)
"When 2T is 0.44, if T1 = 0.18, then T2 = 0.26."
F=6.0, H_a=6.44, T_a=0.18, T_b=0.26 (fixed):
- margin = (6.44-6.0) - (0.18+0.26) = 0.44 - 0.44 = **0.0**
- assembles: True (exact boundary)

### `test_per_part_rule_discriminates_against_pooled_model` (B-3, anti-regression)
H_a=8.6, T_a=0.65; H_b=8.2, T_b=0.0; F=8.0 (floating):
- Per-part: margin_a = 8.6-8.0-0.65 = -0.05; margin_b = 8.2-8.0-0.0 = +0.20;
  margin = min(-0.05, +0.20) = **-0.05** -> assembles False
- Pooled (old, wrong) model would give:
  (8.6-8.0)+(8.2-8.0)-(0.65+0.0) = 0.6+0.2-0.65 = **+0.15** -> assembles True
- This test exists specifically to fail if pooling is ever reintroduced.

All four new tests were executed against the corrected implementation; the
boundary cases returned `margin` on the order of 1e-16 (floating-point
noise around the exact 0.0), well within the module's EPS tolerance.

## Verification

- `python -m pytest -q` -> **106 passed, 1 xfailed** (the deliberate
  `test_transcription_source_recorded` xfail; no other failures).
- `python scripts/gate_a.py` -> exit code **1** (NOT CLEARED), as required:
  all gates that currently run (Y14.5 self-consistency, Monte Carlo
  convergence, checker reliability, validation isolation) PASS; the
  remaining gates SKIP because of the still-present `CITATION PENDING
  HUMAN VERIFICATION` and `replace this line` markers, and missing
  external export files — none of these were touched.
- `src/tolcad/y14_5.py`, `src/tolcad/iso286.py`, and all other source
  modules were not modified by this task.
- `GATE_A_TOLERANCE`, `AGREEMENT_THRESHOLD`, `RELIABILITY_THRESHOLD`,
  `_RELIABILITY_SEED`, `_RELIABILITY_MATES` were not touched.
