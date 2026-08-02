# Task 5 report — close the three guard gaps review found

Base: main @ 4094bd5. Result: main @ 928ca1f, pushed.

## Verification against real source (per the Task 3/4 lesson)

Before trusting the brief's code, checked every symbol/anchor/arithmetic claim against
the actual source rather than the plan document:

- `_TAPPED_HOLE_UPPER_DEV_MM = 0.2` exists at `src/tolcad/gen/features.py:61`, exactly
  as the brief's `find` string states.
- `_FASTENER_LOWER_DEV_MM` is real (`src/tolcad/gen/sampler.py:79`, value `-0.1`), and
  the pre-registration language the brief's `why` refers to is real too:
  `docs/superpowers/plans/2026-08-01-iso273-traceability.md:505-506` names
  `_TAPPED_HOLE_UPPER_DEV_MM` and `_FASTENER_LOWER_DEV_MM` side by side as "the two
  declared-inert untraced numbers." Only `_FASTENER_LOWER_DEV_MM` had an existing
  registry entry (`fastener-upper-dev-nonzero`) before this task — confirming gap 1.
- **Arithmetic check on the tapped-hole mutation.** `TAPPING_DRILL_MM[3.0] == 2.5`
  (`features.py:90`). `FASTENER_SIZES = (3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0)`
  (`features.py:38`) — 3.0 is iterated first in
  `test_tapped_hole_is_always_smaller_than_its_fastener`'s loop. The assertion is
  `hole["nominal"] + hole["upper_dev"] < f`. With the brief's mutation
  (`0.2` -> `0.9`): `2.5 + 0.9 = 3.4`, and `3.4 < 3.0` is False, so the assertion
  fails on the very first loop iteration. **0.9 does break it; no change needed.**
- **Case-sensitive-guard anchor uniqueness.** `grep -no "were checked against the
  primary standard" src/tolcad/gen/features.py` returns exactly one hit, at line 4
  (the ISO 273 clearance-hole paragraph). The near-identical ISO 2306 tapping-drill
  paragraph at line 84 reads "...checked against the primary standard..." — no
  leading "were" — so it does not collide with the anchor. Target test
  `test_features_module_cites_its_primary_sources` asserts
  `"not been checked against the primary" not in text.lower()`. The brief's
  replacement text is "were **NOT** been checked against the primary standard",
  which lowercases to "...were not been checked against the primary standard...",
  containing the forbidden substring — so the assertion trips and the test fails
  under mutation, for the reason intended (this is instance 10: the original guard
  was case-sensitive, so an uppercase "NOT" once slipped past a purely case-sensitive
  check; the guard now calls `.lower()` first).
- `pathlib` was already imported at the top of `tests/test_declared_mutations.py`
  (line 8) from prior tasks, so the brief's "add `import pathlib`" step was a no-op;
  not re-added to avoid a duplicate import.

**No corrections to the brief's code were needed this time** — every symbol, anchor,
and piece of arithmetic checked out against the real source.

## Step 2 — RED (verbatim)

```
collecting ... collected 23 items
...
tests/test_declared_mutations.py::test_the_registry_still_covers_every_critical_guard FAILED [ 82%]
tests/test_declared_mutations.py::test_both_expectation_directions_are_exercised PASSED [ 86%]
tests/test_declared_mutations.py::test_every_registry_name_is_unique PASSED [ 91%]
tests/test_declared_mutations.py::test_every_registry_entry_names_a_single_test PASSED [ 95%]
tests/test_declared_mutations.py::test_text_targets_have_a_known_safe_suffix PASSED [100%]

================================== FAILURES ===================================
_____________ test_the_registry_still_covers_every_critical_guard _____________
...
E       AssertionError: declared mutations were removed: ['case-sensitive-guard-uppercased', 'tapped-hole-upper-dev-nonzero']. If a guard is genuinely obsolete, remove it from _CRITICAL_GUARDS in the same commit and say why.
E       assert not frozenset({'case-sensitive-guard-uppercased', 'tapped-hole-upper-dev-nonzero'})

tests\test_declared_mutations.py:158: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_declared_mutations.py::test_the_registry_still_covers_every_critical_guard
======================== 1 failed, 22 passed in 11.71s ========================
```

The two new meta-tests (`test_every_registry_entry_names_a_single_test`,
`test_text_targets_have_a_known_safe_suffix`) passed immediately because the existing
12 entries already all use function-level `::` selectors and all-`.py` text targets —
they only bite on future regressions, not this one. The expected failure (missing
`_CRITICAL_GUARDS` names) is exactly what fired.

## Step 4 — GREEN (verbatim, 14 entries)

```
collecting ... collected 25 items
...
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[tapped-hole-upper-dev-nonzero] PASSED [ 52%]
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[case-sensitive-guard-uppercased] PASSED [ 56%]
...
tests/test_declared_mutations.py::test_the_registry_still_covers_every_critical_guard PASSED [ 84%]
tests/test_declared_mutations.py::test_both_expectation_directions_are_exercised PASSED [ 88%]
tests/test_declared_mutations.py::test_every_registry_name_is_unique PASSED [ 92%]
tests/test_declared_mutations.py::test_every_registry_entry_names_a_single_test PASSED [ 96%]
tests/test_declared_mutations.py::test_text_targets_have_a_known_safe_suffix PASSED [100%]

============================= 25 passed in 12.96s =============================
```

Both new `test_declared_mutation_behaves_as_declared` parametrizations passed, meaning
`run_declared_mutation` observed: target test passes before mutation, anchor occurs
exactly once, target test genuinely **fails** under mutation (matching `expect="fail"`),
and the file is restored byte-identically. **Neither new entry reported its target
test still passing under mutation** — no live instance of the defect was found; this
is the desired outcome per Step 4's stop condition.

## Full suite

```
392 passed in 39.35s
```

Up from the recorded 388 (net +4: the two new `REGISTRY`-parametrized mutation tests
plus the two new meta-tests).

## Gate A (no pipe)

```
$ python scripts/gate_a.py
Gate A - checker correctness (blocking)

  Y14.5 self-consistency          PASS   100% required; NOT standard-verified (see Y14.5 citation verified)
  Monte Carlo convergence         PASS   +/-0.5% at N=100k
  Checker reliability             PASS   mean 0.9975 over 200 pre-registered seeds (95% bootstrap CI [0.9954, 0.9992], 10000 resamples); fraction of seeds >= 0.95: 0.9700 (tested=12, excluded=0, tested |margin| in [3.50e-04, 4.50e-01]); threshold 0.95
  Validation isolation            PASS   no core imports
  Y14.5 citation verified         PASS   citation verified against standard
  ISO 286 transcription verified  PASS   transcription verified against standard
  NIST PMI conformance            SKIP   no export at nist_pmi_expected.csv
  TolAnalyst agreement            SKIP   no export at tolanalyst_verdicts.csv
  Fresh clone pipeline            SKIP   requires a clean-clone CI run to verify honestly; not checked in-process

Gate A: NOT CLEARED

EXIT:1
```

Exit code 1, 6 PASS / 3 SKIP — unchanged from the baseline recorded in `progress.md`,
as expected: this task does not touch anything Gate A reads.

## Tree cleanliness

Before commit: `git status --short` showed only the two intended files modified
(`tests/mutation_registry.py`, `tests/test_declared_mutations.py`) — confirming every
mutation target (`src/tolcad/gen/features.py` for both new entries) was restored
byte-identically by the runner, with nothing left mutated under `src/` or
`tests/fixtures/`.

After commit:

```
$ git status --short
(empty)
```

## Commit and push

```
[main 928ca1f] feat: guard the tapped-hole constant, instance 10, and selector granularity
 2 files changed, 57 insertions(+)

$ git push origin main
   4094bd5..928ca1f  main -> main
```

Commit SHA: `928ca1f`.

## Self-review

- All three gaps from the adversarial review are closed: `_TAPPED_HOLE_UPPER_DEV_MM`
  now has an executed guard matching its guarded twin; historical instance 10 (the
  case-sensitive text guard) now has a registry entry; and two meta-tests now enforce
  function-level selectors and safe text-target suffixes for every current and future
  entry.
- `_CRITICAL_GUARDS` was updated in the same commit as the two new `REGISTRY` entries,
  per the module's own stated discipline (deletion/omission must be explicit and show
  up in the diff).
- Did not touch `scripts/gate_a.py`, any of the frozen constants
  (`_IT_MICRONS`, `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`, `_TOL_FRACTION_RANGE`,
  `_MIN_WALL_MM`, `_EDGE_MARGIN_MM`, `_TAPPED_HOLE_UPPER_DEV_MM` itself), or anything
  under `src/` permanently — the two new mutations only touch `src/tolcad/gen/features.py`
  transiently inside the declared-mutation runner's own mutate/restore cycle, verified
  restored byte-identically by both the runner's own internal check and the pre-commit
  `git status --short`.
- No deviations from the brief were required: the anchor, the arithmetic, and the
  constant/pre-registration cross-references all checked out against the real source
  on inspection, unlike Task 3's plan-only snippet. This is recorded above rather than
  assumed.
- One thing worth flagging for whoever reads this next: `_CRITICAL_GUARDS`'
  own known limitation (documented in its docstring) still applies unchanged — it's a
  paper-trail mechanism, defeated by a single commit removing an entry and its name
  together. Not a new gap; unchanged by this task.
