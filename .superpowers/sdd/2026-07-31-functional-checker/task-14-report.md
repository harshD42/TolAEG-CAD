# Task 14 Report — Gate A report v2 criteria

## Summary

Replaced `main()` in `scripts/gate_a.py` with the brief's version, which reports all
six spec v2 §7 criteria (four measured via pytest, two oracle-gated), added the
`NIST_EXPECTED` constant, fixed the em-dash header line to plain ASCII, and appended
two new tests to `tests/test_gate_a.py`. Final end state confirmed as required:

**Gate A: NOT CLEARED, exit code 1, four PASS / two SKIP.**

No `data/nist_pmi_expected.csv` or `data/tolanalyst_verdicts.csv` was created; the
`data/` directory does not exist in this repo, and both oracle criteria correctly
report SKIP because their source files are absent.

---

## Step-by-step

### Step 1 — Read the brief and existing files

Read `.superpowers/sdd/2026-07-31-functional-checker/task-14-brief.md` in full.
Read the existing `scripts/gate_a.py` (from Task 11) and `tests/test_gate_a.py`
(two existing tests) to confirm the starting state matched the brief's description:
- Constants `REPO`, `TOLANALYST_EXPORT`, `AGREEMENT_THRESHOLD = 0.95` present.
- `_pytest_passes(target) -> bool` present, unchanged.
- Old `main()` computed PASS/FAIL/SKIP for four criteria (Y14.5, Monte Carlo,
  Validation isolation, TolAnalyst agreement) — missing "NIST PMI conformance"
  and "Checker reliability".
- Old header used a Unicode em dash: `print("\nGate A — checker correctness (blocking)\n")`.

Confirmed `data/` does not exist anywhere in the repo (`ls data/` →
"No such file or directory"), so both oracle files are absent by default — no
fabrication needed or performed.

### Step 2 — Append the two new tests (test-first)

Appended `test_gate_a_reports_v2_criteria` and `test_gate_a_not_cleared_without_oracles`
to `tests/test_gate_a.py`, verbatim from the brief. Did not modify the two existing
tests (`test_gate_a_script_runs_without_solidworks_export`,
`test_gate_a_reports_every_criterion`).

Ran `pytest tests/test_gate_a.py -v` before touching `scripts/gate_a.py` to confirm
the new test failed as expected (missing "NIST PMI conformance" and "Checker
reliability" criteria in stdout, since old `main()` didn't emit them). This matched
the brief's Step 2 expectation.

### Step 3 — Replace `main()` in `scripts/gate_a.py`

Added the constant near the existing ones:

```python
NIST_EXPECTED = REPO / "data" / "nist_pmi_expected.csv"
```

Replaced `main()` wholesale with the brief's version (using the `record()` closure
that maps `True`/`False`/`None` → `PASS`/`FAIL`/`SKIP` and appends `ok is True` to
`passes`), and fixed the header line to plain ASCII per the brief's explicit
instruction:

```python
print("\nGate A - checker correctness (blocking)\n")
```

(hyphen, not em dash — avoids `UnicodeEncodeError` under `PYTHONIOENCODING=cp1252`).

Final `scripts/gate_a.py` (relevant section):

```python
REPO = pathlib.Path(__file__).parent.parent
NIST_EXPECTED = REPO / "data" / "nist_pmi_expected.csv"
TOLANALYST_EXPORT = REPO / "data" / "tolanalyst_verdicts.csv"
AGREEMENT_THRESHOLD = 0.95  # pre-registered, DO NOT LOOSEN


def main() -> int:
    rows: list[tuple[str, str, str]] = []
    passes: list[bool] = []

    def record(name: str, ok: bool | None, note: str) -> None:
        rows.append((name, {True: "PASS", False: "FAIL", None: "SKIP"}[ok], note))
        passes.append(ok is True)

    record("Y14.5 worked examples", _pytest_passes("tests/test_y14_5.py"),
           "100% required")
    record("Monte Carlo convergence", _pytest_passes("tests/test_convergence.py"),
           "+/-0.5% at N=100k")
    record("Checker reliability", _pytest_passes("tests/test_reliability.py"),
           ">=0.95 verdict stability")
    record("Validation isolation", _pytest_passes("tests/test_architecture.py"),
           "no core imports")

    # Oracles: populated in Phase 3, when generated geometry can feed both engines.
    for name, path, threshold in (
        ("NIST PMI conformance", NIST_EXPECTED, 1.00),
        ("TolAnalyst agreement", TOLANALYST_EXPORT, AGREEMENT_THRESHOLD),
    ):
        if not path.exists():
            record(name, None, f"no export at {path.name}")
            continue
        record(name, False, "harness ready; comparison runs in Phase 3")

    width = max(len(r[0]) for r in rows)
    print("\nGate A - checker correctness (blocking)\n")
    for name, status, note in rows:
        print(f"  {name:<{width}}  {status:<5}  {note}")

    cleared = all(passes)
    print(f"\nGate A: {'CLEARED' if cleared else 'NOT CLEARED'}\n")
    return 0 if cleared else 1
```

**Verification of the load-bearing property.** `record()` appends `ok is True` to
`passes` for every criterion, regardless of status. For a SKIP (`ok=None`),
`ok is True` evaluates to `False`, so `passes` gets a `False` entry — identical in
effect to a FAIL. `cleared = all(passes)` therefore cannot be `True` while any
criterion is SKIP (or FAIL). A SKIP can never count as a PASS by construction, not
just by convention.

### Step 4 — Run the full suite and the gate script

Command: `python -m pytest -v`

Full output (tail, all lines shown since suite is short):

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\harsh\Downloads\Projects\Paper1
configfile: pyproject.toml
testpaths: tests
collecting ... collected 75 items

tests/test_architecture.py::test_bare_relative_import_of_validation_is_caught PASSED [  1%]
tests/test_architecture.py::test_dynamic_import_of_validation_is_caught PASSED [  2%]
tests/test_architecture.py::test_exec_with_validation_import_is_caught PASSED [  4%]
tests/test_architecture.py::test_eval_with_validation_import_is_caught PASSED [  5%]
tests/test_architecture.py::test_innocent_exec_call_is_not_flagged PASSED [  6%]
tests/test_architecture.py::test_no_core_module_imports_validation PASSED [  8%]
tests/test_architecture.py::test_core_imports_without_numpy_optional_deps_beyond_declared PASSED [  9%]
tests/test_checker.py::test_dispatches_virtual_condition PASSED          [ 10%]
tests/test_checker.py::test_dispatches_floating_fastener PASSED          [ 12%]
tests/test_checker.py::test_dispatches_iso_fit PASSED                    [ 13%]
tests/test_checker.py::test_unknown_mate_type_rejected PASSED            [ 14%]
tests/test_checker.py::test_missing_type_key_rejected PASSED             [ 16%]
tests/test_convergence.py::test_yield_stable_across_seeds_at_100k_samples PASSED [ 17%]
tests/test_convergence.py::test_convergence_improves_with_sample_count PASSED [ 18%]
tests/test_gate_a.py::test_gate_a_script_runs_without_solidworks_export PASSED [ 20%]
tests/test_gate_a.py::test_gate_a_reports_every_criterion PASSED         [ 21%]
tests/test_gate_a.py::test_gate_a_reports_v2_criteria PASSED             [ 22%]
tests/test_gate_a.py::test_gate_a_not_cleared_without_oracles PASSED     [ 24%]
tests/test_iso286.py::test_it7_at_20mm_is_21_microns PASSED              [ 25%]
tests/test_iso286.py::test_it6_at_20mm_is_13_microns PASSED              [ 26%]
tests/test_iso286.py::test_it_grade_respects_size_band_boundaries PASSED [ 28%]
tests/test_iso286.py::test_h_hole_has_zero_fundamental_deviation PASSED  [ 29%]
tests/test_iso286.py::test_g_shaft_deviation_at_20mm_is_minus_7_microns PASSED [ 30%]
tests/test_iso286.py::test_h7g6_at_20mm_matches_published_limits PASSED  [ 32%]
tests/test_iso286.py::test_h7g6_is_a_clearance_fit PASSED                [ 33%]
tests/test_iso286.py::test_h7p6_is_an_interference_fit PASSED            [ 34%]
tests/test_iso286.py::test_unsupported_size_rejected PASSED              [ 36%]
tests/test_iso286.py::test_malformed_designation_rejected PASSED         [ 37%]
tests/test_iso286.py::test_h7h6_at_20mm_matches_expected_limits PASSED   [ 38%]
tests/test_iso286.py::test_h7k6_at_20mm_matches_expected_limits PASSED   [ 40%]
tests/test_iso286.py::test_unclassified_shaft_letter_rejected PASSED     [ 41%]
tests/test_iso286.py::test_h7k8_rejects_unsupported_k_grade PASSED       [ 42%]
tests/test_iso286.py::test_transcription_source_recorded XFAIL (Fail...) [ 44%]
tests/test_montecarlo.py::test_samples_stay_within_tolerance_limits PASSED [ 45%]
tests/test_montecarlo.py::test_uniform_distribution_spans_the_range PASSED [ 46%]
tests/test_montecarlo.py::test_clearance_fit_yields_fully PASSED         [ 48%]
tests/test_montecarlo.py::test_interference_fit_never_clears PASSED     [ 49%]
tests/test_montecarlo.py::test_transition_fit_yields_partially PASSED   [ 50%]
tests/test_montecarlo.py::test_identical_seeds_give_identical_results PASSED [ 52%]
tests/test_montecarlo.py::test_seed_is_recorded_in_detail PASSED         [ 53%]
tests/test_nist_harness.py::test_loads_expected_verdicts PASSED         [ 54%]
tests/test_nist_harness.py::test_agreement_is_fraction_of_matching_verdicts PASSED [ 56%]
tests/test_nist_harness.py::test_disagreements_are_listed_for_root_causing PASSED [ 57%]
tests/test_nist_harness.py::test_no_overlap_is_an_error_not_a_silent_pass PASSED [ 58%]
tests/test_reliability.py::test_far_from_boundary_verdicts_never_flip PASSED [ 60%]
tests/test_reliability.py::test_near_boundary_cases_are_excluded_not_counted_as_failures PASSED [ 61%]
tests/test_reliability.py::test_stability_is_deterministic_for_a_given_seed PASSED [ 62%]
tests/test_reliability.py::test_empty_input_rejected PASSED             [ 64%]
tests/test_reliability.py::test_positive_control_detects_instability PASSED [ 65%]
tests/test_reliability.py::test_zero_denominator_is_distinguishable_from_verified_stability PASSED [ 66%]
tests/test_reliability.py::test_aliasing_is_handled_correctly PASSED    [ 68%]
tests/test_smoke.py::test_package_imports PASSED                        [ 69%]
tests/test_types.py::test_internal_feature_mmc_is_smallest_size PASSED  [ 70%]
tests/test_types.py::test_external_feature_mmc_is_largest_size PASSED   [ 72%]
tests/test_types.py::test_verdict_is_immutable PASSED                   [ 73%]
tests/test_y14_5.py::test_virtual_condition_external_adds_position_tolerance PASSED [ 74%]
tests/test_y14_5.py::test_virtual_condition_internal_subtracts_position_tolerance PASSED [ 76%]
tests/test_y14_5.py::test_assembly_guaranteed_when_pin_vc_fits_hole_vc PASSED [ 77%]
tests/test_y14_5.py::test_assembly_fails_when_pin_vc_exceeds_hole_vc PASSED [ 78%]
tests/test_y14_5.py::test_exact_boundary_case_assembles PASSED          [ 80%]
tests/test_y14_5.py::test_rejects_swapped_feature_types PASSED          [ 81%]
tests/test_y14_5.py::test_floating_fastener_tolerance_is_hole_mmc_minus_fastener_mmc PASSED [ 82%]
tests/test_y14_5.py::test_fixed_fastener_tolerance_is_half_the_floating_value PASSED [ 84%]
tests/test_y14_5.py::test_floating_fastener_assembles_at_allowable_tolerance PASSED [ 85%]
tests/test_y14_5.py::test_floating_fastener_fails_above_allowable_tolerance PASSED [ 86%]
tests/test_y14_5.py::test_fixed_fastener_is_stricter_than_floating PASSED [ 88%]
tests/test_y14_5.py::test_asymmetric_holes_worse_on_hole_a PASSED       [ 89%]
tests/test_y14_5.py::test_asymmetric_holes_worse_on_hole_b PASSED       [ 90%]
tests/test_y14_5.py::test_unknown_condition_rejected PASSED            [ 92%]
tests/test_y14_5.py::test_rejects_external_hole_b PASSED               [ 93%]
tests/test_y14_5.py::test_no_bonus_at_mmc PASSED                       [ 94%]
tests/test_y14_5.py::test_full_bonus_at_lmc_for_internal_feature PASSED [ 96%]
tests/test_y14_5.py::test_full_bonus_at_lmc_for_external_feature PASSED [ 97%]
tests/test_y14_5.py::test_partial_bonus_mid_range PASSED                [ 98%]
tests/test_y14_5.py::test_actual_size_outside_limits_rejected PASSED    [100%]

======================== 74 passed, 1 xfailed in 6.16s ========================
```

Result: **74 passed, 1 xfailed, 0 failed** (the pre-existing deliberate xfail
`test_transcription_source_recorded` still xfails as expected; the suite grew from
72 to 74 passed because of the two new tests added in this task — total collected
items 75 = 74 passed + 1 xfailed).

Command: `python scripts/gate_a.py`

Full stdout and exit code:

```
Gate A - checker correctness (blocking)

  Y14.5 worked examples    PASS   100% required
  Monte Carlo convergence  PASS   +/-0.5% at N=100k
  Checker reliability      PASS   >=0.95 verdict stability
  Validation isolation     PASS   no core imports
  NIST PMI conformance     SKIP   no export at nist_pmi_expected.csv
  TolAnalyst agreement     SKIP   no export at tolanalyst_verdicts.csv

Gate A: NOT CLEARED

EXIT CODE: 1
```

Additionally verified the em-dash fix directly: ran
`PYTHONIOENCODING=cp1252 python scripts/gate_a.py` and confirmed it produces the
identical table with no `UnicodeEncodeError` and exit code 1 (this would have
crashed before printing the verdict table under the old `—` header).

### Step 5 — Commit

```
$ git add scripts/gate_a.py tests/test_gate_a.py
$ git commit -m "feat: Gate A report covering spec v2 criteria"
[feat/functional-checker 3dfc69d] feat: Gate A report covering spec v2 criteria
 2 files changed, 53 insertions(+), 34 deletions(-)
```

---

## Explicit confirmation of the intended end state

- **Gate A verdict: NOT CLEARED.**
- **Exit code: 1.**
- **Four criteria PASS:** Y14.5 worked examples, Monte Carlo convergence, Checker
  reliability, Validation isolation — each backed by a green pytest run of an
  existing, passing test file (`tests/test_y14_5.py`, `tests/test_convergence.py`,
  `tests/test_reliability.py`, `tests/test_architecture.py`).
- **Two criteria SKIP:** NIST PMI conformance and TolAnalyst agreement — both
  because their oracle export files (`data/nist_pmi_expected.csv`,
  `data/tolanalyst_verdicts.csv`) do not exist. No such files were created and no
  oracle data was fabricated; the `data/` directory itself is absent from the repo.
- **SKIP never counts as PASS:** by construction, `record()` appends `ok is True`
  to the `passes` list for *every* criterion, so a `None` (SKIP) status always
  contributes `False` to `passes`. `cleared = all(passes)` is therefore
  structurally incapable of being `True` while any criterion is SKIP (or FAIL).
  This was verified both by reading the code and by observing the actual run:
  four `True` entries and two `False` entries in `passes` yield `all(passes) ==
  False`, hence `NOT CLEARED` and return code `1`.

This is the correct and intended end state for Task 14: Gate A mechanically
refuses to declare success in the absence of the Phase 3 oracle evidence.

## Notes / constraints respected

- `AGREEMENT_THRESHOLD = 0.95` in `scripts/gate_a.py` was not changed.
- `GATE_A_TOLERANCE = 0.005` in `tests/test_convergence.py` was not touched.
- The two pre-existing tests in `tests/test_gate_a.py` were left untouched; only
  two new tests were appended, verbatim from the brief.
- No files were created under `data/`; no oracle CSVs were fabricated.
- `scripts/gate_a.py` is outside `src/tolcad/`, so importing from `validation/`
  (already done prior to this task, e.g. in the TolAnalyst branch — though the
  new `main()` no longer imports `validation.tolanalyst` since the brief's version
  checks file existence directly) is architecturally permitted per the global
  constraints.
