# Residual cleanup report (2026-08-01)

## FIX 1 — garbled reduction premise in `fastener_assembles` docstring

Landed already, in commit `1ba787b` ("Spec amendment 2026-08-01e: reliability
needs a multi-seed estimator"). That commit was created by a `git add -A`
during an unrelated spec-doc change and swept in this edit alongside it, so
the commit message does not describe this fix — noted here for provenance.
Content is correct and complete: the symmetric-case premise in
`src/tolcad/y14_5.py` (~line 109) now reads `T_a = T_b = T` (was the
self-contradicting `T_a = T_b = T/2`), with the reduction arithmetic spelled
out for both forms:

> Both forms reduce to the classic Y14.5 single-hole formulas in the
> symmetric case (H_a = H_b = H, T_a = T_b = T, i.e. equal parts):
> floating -> T = H - F per part, fixed -> T = (H - F) / 2 per part.
> (Floating: 2(H-F) - 2T = 0 -> T = H - F. Fixed: (H-F) - 2T = 0 ->
> T = (H-F) / 2.)

## FIX 2 — pinned the swap-invariance test

`tests/test_y14_5.py::test_floating_fully_swap_invariant` previously only
asserted `v1.margin == v2.margin`, which passes under any formula symmetric
in (H_a,T_a)<->(H_b,T_b), including the old buggy `min()` model. Added an
absolute pin derived from the documented formula:

```
H_a=8.5, F=8.0, T_a=0.3; H_b=8.6, T_b=0.4
margin = (H_a-F) + (H_b-F) - (T_a+T_b) = 0.5 + 0.6 - 0.7 = 0.4
```

Both `v1.margin` and `v2.margin` are now asserted `== pytest.approx(0.4)`.

## FIX 3 — coverage for new public surface

- `tests/test_reliability.py`: two new tests —
  `test_min_max_abs_margin_report_actual_extremes_of_tested_set` (three
  mates with hand-derived margins 0.6/0.8/0.9 confirm min/max are the true
  extremes of the *tested* set) and
  `test_min_max_abs_margin_none_when_all_excluded` (all-excluded case
  reports `None`/`None`, not a numeric placeholder).
- `tests/test_y14_5.py`: `test_detail_radial_slack_is_half_the_diametral_margin`
  (asserts `detail["radial_slack"] == margin / 2` with a worked example) and
  `test_detail_margin_unit_states_diametral` (asserts
  `detail["margin_unit"] == "diametral_mm"`).
- `scripts/gate_a.py`: extracted the inline band-formatting expression into
  `_format_margin_band(stability)` (behaviour-preserving refactor — same
  f-string, same fallback, verified identical output) so it is directly
  unit-testable. `tests/test_gate_a.py` gained
  `test_format_margin_band_normal_case`,
  `test_format_margin_band_tested_zero_case`, and
  `test_gate_a_reports_tested_margin_band` (asserts the live `gate_a.py`
  run's "Checker reliability" row contains `"|margin| in ["`, `"tested="`,
  `"excluded="`).

No formula, threshold, seed, or mate set was changed. No `data/` files were
created. `src/tolcad/` still has zero imports of `validation/`. Both
citation-pending markers remain in place.

## Verification

- `python -m pytest -q` (repo root): **94 passed, 1 xfailed** (was 87
  passed, 1 xfailed before this session's added tests — +7 new tests, all
  green; the 1 xfail is the pre-existing deliberate
  `test_transcription_source_recorded`).
- `python scripts/gate_a.py`: exit code **1**, prints `Gate A: NOT CLEARED`
  (unchanged — still blocked on the two oracle exports, the two pending
  citation markers, and the fresh-clone criterion, exactly as before this
  session).

STATUS: all three fixes complete and verified; suite green apart from the
one deliberate xfail; Gate A still correctly NOT CLEARED (exit 1).
