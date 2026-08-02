# Task 6 report — Gate A separates measured from attested, and criterion 1 restored

Commit: **05d4dae** on `main`, pushed to `origin` (`928ca1f..05d4dae`).
Base: 928ca1f. Full suite **399 passed**. Gate A **exit 1**. Zero `src/` delta.

---

## 0. What the brief got wrong, and what I changed

Per the standing instruction from the Task 3 finding, I checked every symbol and
signature in the brief against real source before writing. Three corrections:

1. **`_row(...)` did not exist at module level.** It was a *nested local
   function* inside `test_gate_a_reports_final_wave_criteria`
   (`tests/test_gate_a.py:101` at base), closing over a `lines` set built in that
   test. The brief's tests call it at module scope, so as written they would have
   raised `NameError`, not the intended assertion.
2. **`_run_gate_a_stdout()` did not exist at all.** Nothing in the file spawned
   Gate A through a named helper; all six existing tests inlined
   `subprocess.run(...)`.
3. **`_row(prefix)`'s implied arity is a footgun here.** A one-argument `_row`
   must either close over a run (the old nested form) or spawn its own. Gate A
   costs ~2.2 s per run, and the brief's first test calls `_row` twice after
   already calling `_run_gate_a_stdout()` — three runs for one test, and worse,
   two assertions reading two *different* runs. I gave the module-level helper
   the signature `_row(prefix: str, out: str)` with `out` **required**, and
   passed the captured stdout explicitly. The brief's test bodies are otherwise
   verbatim.

I also deleted the nested `_row` and repointed
`test_gate_a_reports_final_wave_criteria` at the module-level one, so there is
one helper rather than two with different signatures.

**Verified rather than trusted**, as instructed:

- The three node IDs exist and pass. `pytest --collect-only -q` returns exactly
  `test_b3_worked_example_boundary_case_assembles`,
  `test_b4_worked_example_boundary_case_assembles`,
  `test_b4_worked_example_unequal_split_boundary_case_assembles`; running them
  gives `3 passed in 0.04s`. Their docstrings do quote the standard's own inputs
  (`tests/test_y14_5.py:343`, `:365`, `:385` — note the brief's `:339, :361,
  :381` are three lines stale, pointing at the docstring interiors of the
  preceding test; the *tests* are the ones named).
- `_pytest_passes(target: str)` took exactly **one** target. The brief's
  restored row needs three, so I widened it to `_pytest_passes(*targets)` with
  an `assert targets` guard. All four existing call sites are single-target and
  unaffected.
- Rows were recorded as `(name, status_string, note)` 3-tuples with the verdict
  word *already stringified at record time*, then printed with a hardcoded
  `{status:<5}`. A `kind` bolted onto the string would have fought that, so I
  moved the stringification to print time: `rows` now holds
  `(name, ok, kind, note)` and the status column is computed as
  `f"{verdict_word[ok]}({kind})"` with a derived column width.

---

## 1. RED — verbatim

`python -m pytest tests/test_gate_a.py -v -k "measured_rows or criterion_one"`

```
E       AssertionError: attested rows must be labelled; otherwise a reader counts them as measurements
E       assert 'PASS(attested)' in '\nGate A - checker correctness (blocking)\n\n  Y14.5 self-consistency          PASS   100% required; NOT standard-verified (see Y14.5 citation verified)\n  Monte Carlo convergence         PASS   +/-0.5% at N=100k\n  Checker reliability             PASS   mean 0.9975 over 200 pre-registered seeds (95% bootstrap CI [0.9954, 0.9992], 10000 resamples); fraction of seeds >= 0.95: 0.9700 (tested=12, excluded=0, tested |margin| in [3.50e-04, 4.50e-01]); threshold 0.95\n  Validation isolation            PASS   no core imports\n  Y14.5 citation verified         PASS   citation verified against standard\n  ISO 286 transcription verified  PASS   transcription verified against standard\n  NIST PMI conformance            SKIP   no export at nist_pmi_expected.csv\n  TolAnalyst agreement            SKIP   no export at tolanalyst_verdicts.csv\n  Fresh clone pipeline            SKIP   requires a clean-clone CI run to verify honestly; not checked in-process\n\nGate A: NOT CLEARED\n\n'

tests\test_gate_a.py:402: AssertionError
___________ test_criterion_one_is_restored_as_its_own_measured_row ____________

    def test_criterion_one_is_restored_as_its_own_measured_row():
        """Spec section 7 criterion 1 is agreement with PUBLISHED worked examples.

        gate_a renamed it to "self-consistency" and noted that is arithmetic derived
        from the same unverified formulas -- so the published-examples criterion was
        reported by nothing. The three examples ARE encoded; point the row at them.
        """
>       line = _row("Y14.5 published worked examples", _run_gate_a_stdout())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\test_gate_a.py:418:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

prefix = 'Y14.5 published worked examples'
out = '\nGate A - checker correctness (blocking)\n\n  Y14.5 self-consistency          PASS   100% required; NOT standard-ver...            SKIP   requires a clean-clone CI run to verify honestly; not checked in-process\n\nGate A: NOT CLEARED\n\n'

    def _row(prefix: str, out: str) -> str:
        ...
        matches = [ln.strip() for ln in out.splitlines() if ln.strip().startswith(prefix)]
>       assert len(matches) == 1, f"expected exactly one {prefix!r} row, got {matches}"
E       AssertionError: expected exactly one 'Y14.5 published worked examples' row, got []
E       assert 0 == 1
E        +  where 0 = len([])

tests\test_gate_a.py:38: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_gate_a.py::test_gate_a_distinguishes_measured_rows_from_attested_ones
FAILED tests/test_gate_a.py::test_criterion_one_is_restored_as_its_own_measured_row
====================== 2 failed, 14 deselected in 4.32s =======================
```

Both failed for the intended reason: no kind label anywhere in the report, and
no published-worked-examples row at all.

---

## 2. Implementation

`scripts/gate_a.py`:

- `MEASURED` / `ATTESTED` constants and a `_KINDS` tuple.
- `record(name, ok, kind, note)` — `kind` is **positional and required**, and
  asserted to be one of `_KINDS`. Deliberately not defaulted to `MEASURED`: a
  default would let a future attested row inherit the stronger label by silence,
  which is the exact defect this correction removes.
- Status column renders `PASS(measured)`, `PASS(attested)`, `SKIP(measured)`,
  `FAIL(measured)`. Column widths derived, not hardcoded.
- New first row, **"Y14.5 published worked examples"**, `MEASURED`, running
  `_pytest_passes(*_Y14_5_WORKED_EXAMPLE_TESTS)` — the three node IDs from the
  brief, all verified to collect and pass.
- **"Y14.5 self-consistency" kept**, unchanged in name and verdict, its note
  prefixed `INFORMATIONAL, not a spec section 7 criterion`. Its `kind` stays
  `MEASURED` because it *is* a measurement (of the whole Tier 1 suite, which is
  broader than the three published examples); what it is not is a §7 criterion.
- The two attested rows print provenance: **who, when, which edition and table**,
  plus a plain statement that the harness reads a human record and cannot
  re-derive it. Attribution is taken from the commits that removed the pending
  markers (`git log -S`), so it is checkable rather than self-asserted:
  `2562bef` (Harsh Dwivedi, 2026-08-01) for both, with `13e3b97` named for the
  later-same-day IT12–IT14 rows so the ISO attestation does not over-claim.
- A tally line at the foot of the report stating the split.

`tests/test_gate_a.py` — the brief's two tests plus four more:

- `test_the_criterion_one_node_ids_exist_and_pass` — anti-vacuity: collects the
  three node IDs by exact ID and requires `3 passed`, so a rename reports *which*
  selector went stale instead of leaving the Gate A row to show a bare FAIL.
- `test_the_attested_rows_print_their_evidence` — an attestation with no
  provenance is just a green word.
- `test_the_tally_states_the_measured_attested_split` — recomputes the split
  from the rendered rows and requires the tally to agree, and requires the split
  to be non-degenerate in *both* directions (a tally reading "7 measured, 0
  attested" would have re-created the original defect).
- `test_every_gate_a_row_declares_a_kind` — checks the *rendered* output, since
  `record`'s assertion is only reached if `record` is actually called.

---

## 3. Gate A report after the change (full, verbatim)

```
Gate A - checker correctness (blocking)

  Y14.5 published worked examples  PASS(measured)  100% required (spec section 7, criterion 1); 3 worked examples printed in ASME Y14.5-2018 Nonmandatory Appendix B, evaluated at the standard's own inputs (B-3 F=6.0/H=6.44/T=0.44; B-4 T=0.22; B-4 unequal split T1=0.18/T2=0.26)
  Y14.5 self-consistency           PASS(measured)  INFORMATIONAL, not a spec section 7 criterion: whole Tier 1 suite, 100% required; NOT standard-verified (see Y14.5 citation verified)
  Monte Carlo convergence          PASS(measured)  +/-0.5% at N=100k
  Checker reliability              PASS(measured)  mean 0.9975 over 200 pre-registered seeds (95% bootstrap CI [0.9954, 0.9992], 10000 resamples); fraction of seeds >= 0.95: 0.9700 (tested=12, excluded=0, tested |margin| in [3.50e-04, 4.50e-01]); threshold 0.95
  Validation isolation             PASS(measured)  no core imports
  Y14.5 citation verified          PASS(attested)  ATTESTED by Harsh Dwivedi, 2026-08-01, commit 2562bef: ASME Y14.5-2018 Nonmandatory Appendix B, sections B-3 and B-4, checked against the primary text; symbols per B-2.1. NOT a measurement -- this row reads a human record (the absence of the pending marker) and cannot re-derive the finding
  ISO 286 transcription verified   PASS(attested)  ATTESTED by Harsh Dwivedi, 2026-08-01, commit 2562bef: ISO 286-1:2010 Table 1 (IT grades), Table 4 and Table 5 (shaft deviations), all 117 IT5-IT8 and H/g/h/k/p values across 13 size bands, checked against the primary tables; the IT12-IT14 rows were added later the same day from the same Table 1 in commit 13e3b97. NOT a measurement -- this row reads a human record (the absence of the placeholder) and cannot re-derive it
  NIST PMI conformance             SKIP(measured)  no export at nist_pmi_expected.csv
  TolAnalyst agreement             SKIP(measured)  no export at tolanalyst_verdicts.csv
  Fresh clone pipeline             SKIP(measured)  requires a clean-clone CI run to verify honestly; not checked in-process

  7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP. An attested PASS is a human's record of checking this code against a published standard; the harness reads that record and cannot re-derive it.

Gate A: NOT CLEARED
```

Before: `6 PASS / 3 SKIP`. After: `7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP`.
A criterion added; none weakened or removed.

---

## 4. The amendment as filed

Inserted in `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`
§7's correction log, immediately after 2026-08-01f. The closing line was
updated from **"All six predate any experimental data"** to **"All seven"**.

```markdown
- *2026-08-01g (pre-data):* Gate A's report now distinguishes measured rows from
  human attestations. Two rows ("Y14.5 citation verified", "ISO 286
  transcription verified") PASS iff a marker string is absent from source, which
  is an attestation; reported inside an undifferentiated "6 PASS" they read as
  measurements. Separately, this section's criterion 1 — agreement with published
  Y14.5 worked examples — had been renamed in the harness to "Y14.5
  self-consistency", whose own note records it is "arithmetic derived from the
  same two unverified formulas the implementation uses", so criterion 1 was
  reported by nothing. The three published ASME Y14.5-2018 Nonmandatory Appendix B
  worked examples **are** encoded as tests, at the standard's own inputs (B-3
  F=6.0, H=6.44, T=0.44; B-4 T=0.22; B-4 unequal split T1=0.18, T2=0.26), so the
  self-consistency objection does not reach them; criterion 1 is restored as its
  own **measured** row pointed at those three node IDs, and the self-consistency
  check is retained as informational. Every row now prints its evidence kind as
  `VERDICT(measured|attested)`, attested rows print who attested, when, and
  against which edition and table, and the report foots a tally that states the
  split. Gate A goes from "6 PASS / 3 SKIP" to
  **"7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP"** — a criterion *added*,
  none weakened or removed. Because the criterion-1 verdict is a published Gate A
  number, it carries a declared-mutation entry
  (`y14-5-worked-example-boundary-shifted`) that was watched failing: shifting the
  B-3 margin 0.01 off the standard's own boundary turns the row to `FAIL(measured)`.
  No threshold, seed set, exclusion band or table constant was touched.
```

I departed from the brief's draft text in three places, all additive: it said
"section 7's criterion 1" where the entry now sits *inside* §7 (changed to
"this section's"); I added the measured before/after tally so the amendment
records the number it produced; and I recorded the R1 entry, which the brief did
not anticipate. Threshold values, the seed set, `BOUNDARY_BAND` and the §7
criteria table are byte-unchanged.

---

## 5. R1 ruling — **added, in scope**

**Ruling: I added the declared-mutation entry.**

R1 (ROUND-0 architect plan, line 92): *"every published number has exactly one
named guard, WATCHED FAILING at least once by an executed mutation with recorded
output. Not argued. Executed."*

Reasons for adding rather than deferring:

1. The criterion-1 row is a Gate A verdict that will be published in the
   pre-registration alongside the reliability mean. The reliability row already
   carries an entry (`reliability-perturbation-tripled`) on exactly this
   reasoning; treating criterion 1 differently would be inconsistent.
2. The task's own framing is that criterion 1 was *reported by nothing*. Shipping
   the restoration and then leaving its guard unexecuted would half-fix that: the
   row would exist, but nobody would have watched it fail. `test_gate_a.py` is
   test code and `gate_a.py` is a script, so **Layer 2 cannot reach either** —
   cosmic-ray mutates `src/` and its test command never runs `gate_a.py`. Without
   a Layer 3 entry the row's guard is covered by no layer at all.
3. It is cheap: one registry entry, ~5.5 s, no new machinery.
4. `test_declared_mutations.py` already names the gap in its own docstring —
   *"nothing forces a NEW guard to be registered, so a future test protecting a
   new published number could be added with no entry and no layer would notice."*
   This task is precisely that situation, arriving.

The entry, in `tests/mutation_registry.py`, and added to `_CRITICAL_GUARDS`:

```
name    y14-5-worked-example-boundary-shifted
target  src/tolcad/y14_5.py
find    "        margin = min(margin_a, margin_b)"        (occurs exactly 1x)
replace "        margin = min(margin_a, margin_b) - 0.01"
test    tests/test_gate_a.py::test_criterion_one_is_restored_as_its_own_measured_row
expect  fail
```

Why this anchor: ASME B-3 states F=6.0 with H=6.44 requires T=0.44 per part, so
the published example sits at margin **exactly 0.0**. Subtracting 0.01 moves the
model off the standard's own boundary and the example stops assembling — a
minimal, standards-anchored corruption rather than an arbitrary one.

**Verified to behave as declared**, two ways.

The runner (which itself asserts the anchor matches once, the target test passes
*before* mutation, and the file is restored byte-identically):

```
python -m pytest "tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[y14-5-worked-example-boundary-shifted]" -q
.                                                                        [100%]
1 passed in 5.54s
```

And watched failing directly, with the mutation applied by hand and reverted:

```
>       assert "PASS" in line and "measured" in line
E       assert ('PASS' in "Y14.5 published worked examples  FAIL(measured)  100% required (spec section 7, criterion 1); 3 worked examples print...dix B, evaluated at the standard's own inputs (B-3 F=6.0/H=6.44/T=0.44; B-4 T=0.22; B-4 unequal split T1=0.18/T2=0.26)")
tests\test_gate_a.py:413: AssertionError
1 failed, 1 error in 2.35s
RESTORED IDENTICAL: True
```

The row reads `FAIL(measured)` under the mutation. (The trailing `1 error` is
Task 1's session finalizer correctly noticing the deliberately mutated tree
during that manual demonstration; `git status` was clean immediately after.)

---

## 6. Verification

**Full suite** (392 at base → **399**; +6 in `test_gate_a.py`, +1 declared
mutation):

```
python -m pytest -q
399 passed in 59.87s
```

**Gate A exit code, unpiped:**

```
$ python scripts/gate_a.py
$ echo "EXIT_CODE_NO_PIPE=$?"
EXIT_CODE_NO_PIPE=1
```

Exit 1 as required — the three SKIPs remain.

**Tree clean:**

```
$ git status --short
(no output)
```

Also confirmed `git diff HEAD --stat -- src/` is empty: **zero `src/` delta**.

**Push:**

```
To https://github.com/harshD42/TolAEG-CAD.git
   928ca1f..05d4dae  main -> main
```

Files changed: `scripts/gate_a.py`, `tests/test_gate_a.py`,
`tests/mutation_registry.py`, `tests/test_declared_mutations.py`,
`docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`.
5 files, +337 / −26.

---

## 7. Self-review, and one finding for the controller

Constraint check:

- `src/` untouched. ✅
- No threshold value, seed-set entry, `BOUNDARY_BAND` or table constant changed.
  ✅ The §7 criteria table is byte-identical.
- The self-consistency row is neither weakened nor deleted; it keeps its name,
  its test target and its PASS, and gains an INFORMATIONAL note. ✅
- Amendment numbered `2026-08-01g`, labelled `(pre-data)`, matching 01f's style.
  ✅ Closing count updated six → seven.

Judgement calls worth flagging:

- **`SKIP(measured)` reads slightly oddly** for the three unresolved rows —
  nothing has been measured yet. I kept it because the kind states what evidence
  the row *rests on when it clears*, and suppressing it for SKIPs would let a
  future attested row arrive as a SKIP with no label. The tally line carries the
  explanation. If a reviewer prefers, a third kind (`pending`) would be a
  one-line change, but it goes beyond the brief's two-kind instruction.
- **Node-ID line numbers in the brief were stale** (`:339, :361, :381` vs the
  actual `:343, :365, :385`). The *node IDs* were correct, which is what matters;
  I pinned by ID, not by line.

**FINDING, pre-existing and outside this task — Layer 2's mutation pin has
detached upward.** Running `python scripts/check_suite_integrity.py` reports:

```
  Core branch coverage               PASS   94.74% (pin 94.74% +/- 0.50)
  Mutation score                     FAIL   100.00% (pin 95.89% +/- 0.50)
Suite integrity: FAILED (Mutation score)
```

This is **not** caused by this commit, and the argument is decisive rather than
circumstantial: `cosmic-ray.toml`'s test command is a fixed six-file subset
(`test_types`, `test_y14_5`, `test_iso286`, `test_montecarlo`, `test_checker`,
`test_reliability`) that includes none of the files I touched, and the `src/`
delta is zero. The most likely cause is commit `380d36a` ("test: kill the nine
mutants the triage recorded wrongly"), which landed *after* 95.89 was measured —
i.e. Task 2's two-sided pin is doing exactly the job it was built for, flagging
an improvement that would previously have detached silently. No prior closeout
task appears to have run Layer 2 end-to-end, so this looks like its first
observation. **It needs a re-pin with a recorded reason, which is a measurement
decision I have deliberately left to the controller** — and note `cosmic-ray
exec` carries the documented do-not-run-concurrently hazard. Layer 1 coverage is
unmoved at exactly 94.74.

Also noted, not acted on: `progress.md` still ends `NEXT: T4 ... Base = cac4644`
despite T4 (`4094bd5`) and T5 (`928ca1f`) having landed. The ledger's `NEXT:`
lines read as controller-authored, so I did not edit it.
