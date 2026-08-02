# Task 2 report: the full seed registry

## RED (Step 2) — verbatim

Command: `python -m pytest tests/test_declared_mutations.py -v -k "critical_guard or both_expectation"`

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0 -- ...python.exe
cachedir: .pytest_cache
rootdir: C:\Users\harsh\Downloads\Projects\Paper1
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 9 items / 7 deselected / 2 selected

tests/test_declared_mutations.py::test_the_registry_still_covers_every_critical_guard FAILED [ 50%]
tests/test_declared_mutations.py::test_both_expectation_directions_are_exercised FAILED [100%]

================================== FAILURES ===================================
_____________ test_the_registry_still_covers_every_critical_guard _____________

    def test_the_registry_still_covers_every_critical_guard():
        """An entry must not be deletable to silence a failure."""
        present = {m.name for m in REGISTRY}
        missing = _CRITICAL_GUARDS - present
>       assert not missing, (
            ...
        )
E       AssertionError: declared mutations were removed: ['crlf-corrupted-nist-fixture', 'fastener-upper-dev-nonzero', 'flat-difficulty-ladder', 'it-grade-set-widened', 'm12-clearance-diameter', 'mc-seed-base-shifted', 'stale-literal-wall-floor']. If a guard is genuinely obsolete, remove it from _CRITICAL_GUARDS in the same commit and say why.

_______________ test_both_expectation_directions_are_exercised ________________

    def test_both_expectation_directions_are_exercised():
        """expect="pass" is what catches seed fishing; losing it loses that class."""
        directions = {m.expect for m in REGISTRY}
>       assert directions == {"fail", "pass"}, (
            ...
        )
E       AssertionError: registry only exercises {'fail'}. Asserting a guard CAN fail says nothing about whether a passing result passes for the right reason.
E       assert {'fail'} == {'fail', 'pass'}
E         Extra items in the right set:
E         'pass'

=========================== short test summary info ===========================
FAILED tests/test_declared_mutations.py::test_the_registry_still_covers_every_critical_guard
FAILED tests/test_declared_mutations.py::test_both_expectation_directions_are_exercised
======================= 2 failed, 7 deselected in 0.06s ========================
```

Exactly as the brief predicted: seven missing names enumerated, and `{'fail'}` only from
the expectation-directions test.

## GREEN (Step 4) — verbatim

Command: `python -m pytest tests/test_declared_mutations.py -v`

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0 -- ...python.exe
cachedir: .pytest_cache
rootdir: C:\Users\harsh\Downloads\Projects\Paper1
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 16 items

tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[it7-row-transposed] PASSED [  6%]
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[zeroed-wall-margin] PASSED [ 12%]
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[it-grade-set-widened] PASSED [ 18%]
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[flat-difficulty-ladder] PASSED [ 25%]
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[stale-literal-wall-floor] PASSED [ 31%]
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[crlf-corrupted-nist-fixture] PASSED [ 37%]
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[m12-clearance-diameter] PASSED [ 43%]
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[fastener-upper-dev-nonzero] PASSED [ 50%]
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[mc-seed-base-shifted] PASSED [ 56%]
tests/test_declared_mutations.py::test_a_no_op_patch_is_rejected PASSED  [ 62%]
tests/test_declared_mutations.py::test_an_ambiguous_patch_is_rejected PASSED [ 68%]
tests/test_declared_mutations.py::test_an_invalid_expectation_is_rejected PASSED [ 75%]
tests/test_declared_mutations.py::test_a_mutation_that_changes_nothing_is_rejected PASSED [ 81%]
tests/test_declared_mutations.py::test_the_registry_still_covers_every_critical_guard PASSED [ 87%]
tests/test_declared_mutations.py::test_both_expectation_directions_are_exercised PASSED [ 93%]
tests/test_declared_mutations.py::test_every_registry_name_is_unique PASSED [100%]

============================== 16 passed in 9.02s ==============================
```

9 registry entries (7 new + 2 from Task 1) plus 7 runner/meta tests, all passing. No
entry reported an "occurs N times" anchor mismatch, and no `expect="fail"` entry reported
the target test still passing under mutation. **`mc-seed-base-shifted` (`expect="pass"`)
survived the reseed from 12345 to 24680** — `test_supported_fits_still_contain_both_verdict_classes`
still passed, so the seed-fishing guard is genuine: the surviving ISO fit set spans both
verdict classes for both seeds, not just the originally chosen one. No finding to report here.

## Full suite (Step 4 cont'd)

Baseline re-measured via `git stash -u` / `git stash pop` (no permanent change, confirmed
`git status --short` clean immediately after popping):

- **Baseline (HEAD, before this task's edits): 286 passed in 25.53s.**
- **With this change: 296 passed in 33.88s** (286 baseline + 10 new tests: 7 declared
  mutations + 3 meta-tests).
- **Added wall-clock time: ~8.35s** for seven new declared mutations plus the three meta
  tests. Consistent with Task 1's estimate of roughly two pytest subprocess runs per
  mutation entry, scaled up from 2 to 9 registry entries (~1.5s for 2 → ~9-10s for 9,
  i.e. roughly linear in registry size as flagged in the Task 1 report's "Concerns").

## Gate A (Step 5)

Command: `python scripts/gate_a.py > <file> 2>&1; echo "EXITCODE=$?"` (exit code captured
directly, not through a pipe).

```
EXITCODE=1
```

Output:

```
Gate A - checker correctness (blocking)

  Y14.5 self-consistency          PASS   100% required; NOT standard-verified (see Y14.5 citation verified)
  Monte Carlo convergence         PASS   +/-0.5% at N=100k
  Checker reliability             PASS   mean 0.9982 over 200 pre-registered seeds (95% bootstrap CI [0.9964, 0.9995], 10000 resamples); fraction of seeds >= 0.95: 0.9800 (tested=11, excluded=1, tested |margin| in [3.50e-04, 4.50e-01]); threshold 0.95
  Validation isolation            PASS   no core imports
  Y14.5 citation verified         PASS   citation verified against standard
  ISO 286 transcription verified  PASS   transcription verified against standard
  NIST PMI conformance            SKIP   no export at nist_pmi_expected.csv
  TolAnalyst agreement            SKIP   no export at tolanalyst_verdicts.csv
  Fresh clone pipeline            SKIP   requires a clean-clone CI run to verify honestly; not checked in-process

Gate A: NOT CLEARED
```

6 PASS / 3 SKIP, exit code 1 — matches expectation. `scripts/gate_a.py` untouched
(confirmed: it does not appear in `git status --short` or the commit diff).

## Tier 1 ladder, seeds 0-199

Ran the exact snippet from `docs/superpowers/plans/2026-08-01-iso273-traceability.md`:

```python
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
```

```
d1: 31/159 = 19.5% fail
d2: 99/301 = 32.9% fail
d3: 239/452 = 52.9% fail
d4: 421/609 = 69.1% fail
```

| level | fraction | percent |
|---|---|---|
| d1 | 31/159 | 19.5% |
| d2 | 99/301 | 32.9% |
| d3 | 239/452 | 52.9% |
| d4 | 421/609 | 69.1% |

Matches the required `d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%` exactly. This task
added test-support entries only (no production number changed), so the ladder was
expected to be bit-identical, and it is.

## Working tree cleanliness (Step 6)

Immediately before staging:

```
$ git status --short
 M tests/mutation_registry.py
 M tests/test_declared_mutations.py
```

Only the two files this task is scoped to modify — no trace of any mutation target
(`src/tolcad/iso286.py`, `src/tolcad/gen/sampler.py`, `src/tolcad/gen/features.py`,
`tests/gen/test_layout.py`, `tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp`,
`tests/gen/test_features.py`) having been left mutated. This is the direct evidence
that `run_declared_mutation`'s `finally`-block restoration plus its post-restore
byte-identical assertion worked for all nine entries, including the binary NIST
fixture mutation.

After the commit:

```
$ git status --short
(clean — no output)
```

## Commit

SHA: `2e2cabc`

```
feat: declare the mutations that must break each published-number guard

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

2 files changed, 143 insertions(+): `tests/mutation_registry.py`, `tests/test_declared_mutations.py`.

## Self-review

- Both files' diffs (`git diff` against the previous commit, reviewed before staging)
  match the brief's Step 1 and Step 3 blocks verbatim — no paraphrasing, no reordering,
  no simplification of the two unusual anchors (`\n_MIN_WALL_MM = 4.0` from Task 1 is
  untouched; the new binary NIST anchor `HEADER;\r\n` was used exactly as specified,
  with `binary=True`).
- All seven new entries reported occurrence count 1 (no "occurs 0 times" / "occurs N
  times" diagnostic from the runner) — every anchor was unique in this working tree,
  confirming the brief's 2026-08-01 verification still holds.
- No `expect="fail"` entry reported the target test still passing under mutation — no
  live defect instance surfaced.
- `mc-seed-base-shifted`, the one `expect="pass"` entry, survived its reseed
  (12345 → 24680): the seed-fishing guard is not itself fished.
- No `_IT_MICRONS`, `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`, `_TOL_FRACTION_RANGE`,
  `_MIN_WALL_MM`, `_EDGE_MARGIN_MM`, or any test's literal floor was permanently
  changed — all seven new mutation targets are declared-mutation targets that the
  runner transiently patches and restores; `git status --short` was clean both before
  and after the commit.
- `scripts/gate_a.py` was not modified; it does not appear in the commit's file list.
- The `mutation` marker was not deselected anywhere; all nine registry entries ran by
  default with a plain `python -m pytest tests/test_declared_mutations.py -v`.
- Full suite count rose from 286 to 296 (7 mutation entries + 3 meta tests = 10 new
  tests), consistent with the brief's expectation of "several seconds" of added runtime
  (measured: ~8.35s).

## Concerns

- None blocking. The registry now covers all nine pre-registered critical guards named
  in the brief, with both expectation directions exercised. The linear growth in
  wall-clock cost per registry entry (flagged in Task 1's report) continues to hold and
  is still modest at 9 entries (~9-10s total for the mutation file), but should be kept
  in mind if the registry grows substantially further, since each entry costs roughly
  two pytest subprocess invocations of its target selector.
