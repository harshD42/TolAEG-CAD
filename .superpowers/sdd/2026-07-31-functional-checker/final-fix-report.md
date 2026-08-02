# Final fix wave report — feat/functional-checker

Base commit: `3dfc69d` ("feat: Gate A report covering spec v2 criteria")

## C1 — `fastener_assembles` argument-order bug (Critical)

**Root cause:** `floating_fastener_tolerance`/`fixed_fastener_tolerance` were called with `hole_a`
only, so the allowable tolerance ignored `hole_b`'s SIZE entirely.

**Fix** (`src/tolcad/y14_5.py`): compute the governing hole as `min(hole_a.mmc, hole_b.mmc)` —
the smaller hole is always the geometrically limiting case — and pass that into the tolerance
formula. Added explicit `hole_a` INTERNAL-type validation (previously only reachable via
`_check_fastener_pair` when `hole_a` happened to be the one fed into the tolerance function).
`detail` now records `governing_hole` ("hole_a"/"hole_b"), `governing_hole_mmc`, and both
individual hole MMCs.

**Verification:** Ø8.5/Ø8.05 holes, both `position_tol=0.3`, M8 bolt, `condition="floating"`:
both argument orders now give `assembles=False`, `margin=-0.24999999999999928` — identical
regardless of order (previously: `True`/`+0.2` vs `False`/`-0.25`).

**Test added:** `tests/test_y14_5.py::test_argument_order_does_not_change_verdict_for_asymmetric_hole_sizes`
— varies hole SIZE (not just `position_tol`), asserts identical verdict/margin under swap and
correct `governing_hole_mmc` in both orders.

## C2 — `verdict_stability` vacuous for `iso_fit` mates (Critical)

**Root cause:** `_perturb` only perturbs dict-valued top-level entries; `iso_fit` mates have no
sub-dicts (`nominal`, `designation`, `n`, `seed` are scalars), so perturbation was a provable
no-op. Separately, the boundary-band check compared `abs(margin)` (a Tier-2 yield in [0,1])
against `BOUNDARY_BAND * epsilon` (an mm-scale quantity) — incommensurable units.

**Fix** (`src/tolcad/reliability.py`): `verdict_stability` now raises `ValueError` for any mate
whose `type` is not in `{virtual_condition, floating_fastener, fixed_fastener}` (`_TIER1_TYPES`).
Module docstring now states the Tier-1-only scope prominently, explaining why margins aren't
comparable across tiers.

**Test added:** `tests/test_reliability.py::test_iso_fit_mate_is_rejected` — asserts `ValueError`
(matching "Tier 1") for an `iso_fit` mate.

## C3 — Gate A's ">=0.95 verdict stability" claim was never measured (Critical)

**Fix** (`scripts/gate_a.py`): added module-level `RELIABILITY_THRESHOLD = 0.95` (matches spec
section 7; not a pre-registered threshold being changed — it's new). Added a fixed, seeded set
of 6 Tier 1 mates (`_RELIABILITY_MATES`, `epsilon=1e-4`, `seed=20260731`), all with margins
comfortably outside the boundary band. Gate A now actually calls `verdict_stability(...)`,
compares the result to `RELIABILITY_THRESHOLD`, and prints the measured value in the note
column. The "Checker reliability" row's PASS now requires both `tests/test_reliability.py`
passing (kept as a separate concern) **and** the measured value meeting the threshold.

**Measured value in this run:** `1.0000` (tested=6, excluded=0).

## C4 — Circular Y14.5 row + invisible pending-citation markers (Critical)

**Fix** (`scripts/gate_a.py`):
- (a) Renamed row `"Y14.5 worked examples"` → `"Y14.5 self-consistency"`, note now states
  "NOT standard-verified (see Y14.5 citation verified)".
- (b) Added row `"Y14.5 citation verified"` — SKIP while `CITATION PENDING HUMAN VERIFICATION`
  appears in `src/tolcad/y14_5.py` (checked by reading the file directly, not a marker string
  match choice — genuinely re-derived each run).
- (c) Added row `"ISO 286 transcription verified"` — SKIP while `replace this line` appears in
  `src/tolcad/iso286.py`'s module docstring. `tests/test_iso286.py` is now also run as a
  prerequisite of the `"Monte Carlo convergence"` PASS (Monte Carlo depends on the ISO 286
  tables, so the transcription guard is no longer decoupled from that claim).

Updated `tests/test_gate_a.py`: renamed the string assertion for the renamed row, and added
`test_gate_a_reports_final_wave_criteria` asserting the two new SKIP rows are present and
literally read SKIP, plus that the reliability row shows a measured value.

## I5 — Gate A had no achievable pass state for the oracle rows (Important)

**Fix** (`scripts/gate_a.py`): the oracle loop now calls `nist_pmi.load_expected`/`agreement`
and `tolanalyst.load_verdicts`/`agreement` for real when the CSV exists (still SKIP when it
doesn't — no CSVs were created, per the constraint). `AGREEMENT_THRESHOLD` and the NIST 1.00
threshold are now both actually referenced in the comparison. Since our verdict set (`ours`) is
legitimately empty until Phase 3, `agreement()` raises `ValueError` on no-overlap; this is
caught and recorded as FAIL with the reason, rather than silently passing. Verified by
temporarily dropping a synthetic CSV into `data/` (then deleting it, per the "do not create
oracle data" constraint) — the row switched from SKIP to a real FAIL driven by the actual
`agreement()` call.

`sys.path.insert(0, str(REPO))` was added to `gate_a.py` because, run as `python scripts/gate_a.py`,
`sys.path[0]` is `scripts/`, not the repo root, so `validation/` would not otherwise import
outside of pytest's `pythonpath` setting.

## I6 — Spec criterion 7 unreported (Important)

**Fix** (`scripts/gate_a.py`): added row `"Fresh clone pipeline"`, reported SKIP with note that
it requires a clean-clone CI run and is not verified in-process.

## Escalated minors — all fixed

- `src/tolcad/types.py`: `Verdict.margin` docstring now documents both units (Tier 1 mm-of-slack
  vs Tier 2 yield-in-[0,1]) and states they are not comparable.
- `tests/test_architecture.py`: `_imports_from_code` now catches bare-name `import_module(...)`
  calls (after `from importlib import import_module`) and `__import__` accessed as an attribute
  (e.g. `builtins.__import__(...)`), in addition to the previously-caught attribute/bare-name
  forms. Added `test_bare_name_import_module_call_is_caught` and
  `test_dunder_import_as_attribute_is_caught`.
- `src/tolcad/checker.py`: `iso_fit` branch default `n` changed from `10_000` to `100_000` to
  match Gate A's stability sample count.
- `tests/test_architecture.py`: renamed "Finding CORS" → "Finding 4" (three docstrings + one
  inline comment), removing the nonsense provenance tag.
- `tests/test_reliability.py::test_aliasing_is_handled_correctly`: rewritten to count actual
  perturbation draws via a `_CountingRNG` wrapper around `np.random.Generator`, comparing an
  aliased mate (7 draws: hole perturbed once + fastener) against a non-aliased control (11
  draws: hole_a + hole_b independently + fastener) — falsifiable if the aliasing dedup regresses.
- `tests/test_montecarlo.py::test_uniform_distribution_spans_the_range`: now also asserts
  `samples.std() == pytest.approx(0.00605, abs=1e-3)`, which discriminates uniform from normal
  sampling (normal std ~0.00351 for the same feature) — the prior mean-only assertion could not.

## Full suite

```
79 passed, 1 xfailed in 9.99s
```
(up from 74 passed/1 xfailed — 5 new tests: C1 order test, C2 iso_fit-rejection test, 2
architecture-lint tests, 1 new Gate A row-coverage test; `test_aliasing_is_handled_correctly`
and `test_uniform_distribution_spans_the_range` were rewritten in place, not added.)

The only xfail is the deliberate `tests/test_iso286.py::test_transcription_source_recorded`,
unchanged per the constraint not to remove the pending-citation markers.

## Gate A — full stdout

```
Gate A - checker correctness (blocking)

  Y14.5 self-consistency          PASS   100% required; NOT standard-verified (see Y14.5 citation verified)
  Monte Carlo convergence         PASS   +/-0.5% at N=100k
  Checker reliability             PASS   measured 1.0000 (tested=6, excluded=0); threshold 0.95
  Validation isolation            PASS   no core imports
  Y14.5 citation verified         SKIP   CITATION PENDING HUMAN VERIFICATION marker present in y14_5.py
  ISO 286 transcription verified  SKIP   placeholder 'replace this line' present in iso286.py docstring
  NIST PMI conformance            SKIP   no export at nist_pmi_expected.csv
  TolAnalyst agreement            SKIP   no export at tolanalyst_verdicts.csv
  Fresh clone pipeline            SKIP   requires a clean-clone CI run to verify honestly; not checked in-process

Gate A: NOT CLEARED

EXIT=1
```

Measured checker reliability: **1.0000** (tested=6, excluded=0; threshold 0.95).

4 PASS, 5 SKIP, NOT CLEARED, exit 1 — matches the required end state (a SKIP never counts as a
pass; the oracle CSVs were not created, per constraints).

## Findings not fixed

None. All BLOCKING findings (C1–C4, I5, I6) and all escalated minors were fixed in this pass.
