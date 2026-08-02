# Task 4 report: pin all four ladder counts, reproducibly

Base: main @ cac4644. Result: main @ 4094bd5, pushed to origin.

## Measured counts and digest (verbatim)

```
  d1: 31/159 = 19.50% fail
  d2: 99/301 = 32.89% fail
  d3: 239/452 = 52.88% fail
  d4: 421/609 = 69.13% fail
  corpus digest: c035c2d99d377c1f1c6f912c9c690e47376e012eee37f4283c41de0051336fa3
  recipe: {"seeds": "range(0, 200)", "difficulties": [1, 2, 3, 4], "counted": "Tier 1 mates only (kind != 'iso_fit')", "statistic": "check(mate.to_check_dict()).assembles is False"}
```

Counts match the expected 31/159, 99/301, 239/452, 421/609 exactly (rounded rates
19.5%/32.9%/52.9%/69.1% also match). numpy confirmed at 2.4.1
(`python -c "import numpy; print(numpy.__version__)"` -> `2.4.1`). No STOP condition
triggered.

Digest is 64 hex characters (verified with `len()`), i.e. a normal SHA-256 hex
digest — no typo/truncation in the printed value.

## RED output

Before `scripts/measure_ladder.py` existed:

```
ERROR collecting tests/gen/test_ladder_pin.py
ModuleNotFoundError: No module named 'scripts.measure_ladder'
```

(`scripts/` has no `__init__.py`; it works as a Python 3 implicit namespace
package under `pythonpath = ["src", "."]`. Confirmed precedent:
`tests/test_gate_a.py` already imports `from scripts.gate_a import ...` and
`import scripts.gate_a`, so this is not a new pattern.)

## GREEN output

After implementing `scripts/measure_ladder.py` and filling `EXPECTED_DIGEST`
with the measured value:

```
tests/gen/test_ladder_pin.py::test_each_ladder_level_matches_its_exact_pinned_counts[1] PASSED
tests/gen/test_ladder_pin.py::test_each_ladder_level_matches_its_exact_pinned_counts[2] PASSED
tests/gen/test_ladder_pin.py::test_each_ladder_level_matches_its_exact_pinned_counts[3] PASSED
tests/gen/test_ladder_pin.py::test_each_ladder_level_matches_its_exact_pinned_counts[4] PASSED
tests/gen/test_ladder_pin.py::test_the_corpus_digest_is_reproducible PASSED
============================== 5 passed in 0.36s ==============================
```

## Declared-mutation entry behaviour

Added `ladder-d2-row-shifted` (target `src/tolcad/gen/sampler.py`, anchor
`    2: (0.65, 1.16),` -> `    2: (0.70, 1.24),`, `expect="fail"`) and its name
to `_CRITICAL_GUARDS` in `tests/test_declared_mutations.py`.

Ran it in isolation first:

```
tests/test_declared_mutations.py::test_declared_mutation_behaves_as_declared[ladder-d2-row-shifted] PASSED
============================== 1 passed in 1.21s ===============================
```

"PASSED" here means the runner's own assertions held: the anchor matched
exactly once, the target test passed *before* the mutation, the target test
(`test_each_ladder_level_matches_its_exact_pinned_counts`, all four
parametrized cases) genuinely **failed** under the mutated d2 row (only d2's
count moved — d1/d3/d4 are independent RNG streams keyed by
`(seed, difficulty)`, so the anchor change is isolated to the d2 sub-test), and
`sampler.py` was restored byte-identically afterward (`git status --short`
showed no residual diff on `src/`). This is the proof the pin works: before
this task, mutating this exact anchor left every existing guard green; now the
new pin catches it. No live finding here — the guard performed as designed on
the first attempt, so nothing needed rebinding.

Then ran the full registry (26 tests: 5 new ladder-pin tests + 11 mutation
entries incl. the new one + 10 registry-mechanics tests) together — all 26
passed, confirming the new entry doesn't disturb any pre-existing declared
mutation:

```
============================= 26 passed in 13.55s =============================
```

## Full suite

```
collected 388 items
...
============================ 388 passed in 48.03s =============================
```

382 (Task 3 baseline) + 5 (`test_ladder_pin.py`) + 1 (`ladder-d2-row-shifted`
declared-mutation parametrization) = 388. Matches exactly.

## Gate A

Run without a pipe:

```
python scripts/gate_a.py; echo "EXIT CODE: $?"
```

```
  Y14.5 self-consistency          PASS
  Monte Carlo convergence         PASS
  Checker reliability             PASS   mean 0.9975 ... fraction >= 0.95: 0.9700 (tested=12, excluded=0)
  Validation isolation            PASS
  Y14.5 citation verified         PASS
  ISO 286 transcription verified  PASS
  NIST PMI conformance            SKIP
  TolAnalyst agreement            SKIP
  Fresh clone pipeline            SKIP

Gate A: NOT CLEARED
EXIT CODE: 1
```

6 PASS / 3 SKIP, exit code 1 — matches the expected baseline from Task 3
exactly (unchanged, as expected: this task does not touch the checker core or
`scripts/gate_a.py`).

## Tree cleanliness and push

Before commit:

```
 M pyproject.toml
 M tests/mutation_registry.py
 M tests/test_declared_mutations.py
?? scripts/measure_ladder.py
?? tests/gen/test_ladder_pin.py
```

— exactly the five files the brief names, nothing under `src/` left modified
(the declared-mutation run against `sampler.py` restored it byte-identically,
confirmed by its absence from this list).

Committed as `4094bd5` ("feat: pin all four ladder counts and the corpus
digest, on a pinned numpy"). `git status --short` after commit: clean (no
output). Pushed: `cac4644..4094bd5  main -> main` to
`https://github.com/harshD42/TolAEG-CAD.git`.

## Self-review

- The brief's code for both `tests/gen/test_ladder_pin.py` and
  `scripts/measure_ladder.py` ran **as written**, with only two additions
  beyond copy-paste: filling `EXPECTED_DIGEST` (deliberately left `None` in
  the brief) and confirming the `scripts.` namespace-package import works
  (it does, matching existing usage in `tests/test_gate_a.py`).
- Before trusting the brief's interfaces, I read `src/tolcad/gen/sampler.py`,
  `src/tolcad/gen/spec.py` (`MateSpec.to_check_dict`, `AssemblySpec.to_json`),
  and `src/tolcad/checker.py` (`check(mate: dict) -> Verdict`) to confirm the
  call signatures, arities, and dict shapes the test/script rely on actually
  match — given Task 3's finding that a prior plan-embedded test snippet had
  wrong arity and nonexistent symbols and was never executed. Everything
  matched; no fixes were needed this time.
- Confirmed the `find` anchor `    2: (0.65, 1.16),` occurs in
  `src/tolcad/gen/sampler.py` and is unique enough for the registry's own
  "occurs exactly once" check (proved by the mutation run succeeding rather
  than raising `AssertionError: ... occurs N times`).
- Verified the printed digest is a genuine 64-hex-char SHA-256 (`len(d) ==
  64`) before pinning it, rather than trusting the terminal's word-wrap by
  eye.
- Confirmed independently that no value in `_TOL_FRACTION_RANGE`,
  `_IT_MICRONS`, `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`, `_MIN_WALL_MM`, or
  `_EDGE_MARGIN_MM` was changed at rest — the only `src/` touch is the
  transient, restored mutation during the declared-mutation test run.
- `pyproject.toml`'s `numpy>=1.26` was replaced with `numpy==2.4.1` per D-C;
  no other pyproject.toml lines were touched.
- Did not touch `scripts/gate_a.py`, per the global constraint.

## Concerns

None outstanding. The one thing worth flagging for future readers: the new
`ladder-d2-row-shifted` entry's `test` selector targets
`test_each_ladder_level_matches_its_exact_pinned_counts` without a specific
`[2]` parametrize id, so all four parametrized cases run under
`_target_test_passes` (pytest's `-x` stops at the first failure it hits, but
the subprocess call is still considered failed as a whole if any one
sub-case fails). This is correct and matches the brief exactly — flagging only
so a future reader doesn't mistake "the whole function is the target" for an
oversight.
