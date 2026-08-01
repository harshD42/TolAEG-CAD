# Suite Integrity: Detecting Tests That Cannot Fail — Design

**Status:** approved 2026-08-01. Supersedes nothing; additive to the existing gate structure.

## 1. Problem

This project's dominant failure mode is **the test or metric that cannot fail**. Eleven instances are documented across Phases 0–3.5b. Every one passed, looked correct, and was caught only by someone asking, by hand, "what change would make this fail?"

| Shape | Instances observed |
|---|---|
| **Insensitive** — the assertion holds under the exact mutation it exists to catch | anti-degeneracy guard satisfied entirely by `iso_fit` mates; NIST fixture positive control passing against the CRLF corruption it was written to detect; case-sensitive text guard defeated by `NOT` vs `not`; seed-fished positive control |
| **Tautological** — the assertion restates the code | self-referential layout margin constants (`pitch - (a+b) >= _MIN_WALL_MM` reduces to `x >= x - ε`); `nominal + 0.0 == nominal` |
| **Unreachable** — never actually executes | module-level `pytestmark` skipping a test with no dependency on the skipped fixture; fetcher's mismatch → `exit 1` branch with zero coverage |
| **Drifted** — was meaningful, silently stopped being | literal wall floor overtaken by its own derived requirement; Gate A measurement with 1000× headroom |
| **Structurally impossible** — the metric cannot return the failing value | reliability metric mathematically incapable of returning below 1.0 |
| **Unencoded** — the verification happened but left no guard | 39-cell IT table check run once in a shell, never committed as a test |

**Awareness is not the intervention.** The pattern was recorded in project memory, cited in nearly every review prompt of the 2026-08-01 session, and three new instances still landed on the final branch. Any solution that depends primarily on remembering will fail the same way.

## 2. Goal and non-goals

**Goal.** Make "this test cannot fail" a condition the repository detects mechanically, before it reaches a published number.

**Non-goals.**
- Not a research gate. Gate A/B/C/D thresholds are frozen by `CLAUDE.md`; nothing here is folded into them.
- Not a general-purpose quality metric. Coverage and mutation score are instruments for one specific defect class, not targets to maximise.
- Not applied to `gen/`. CadQuery mutants are slow and frequently geometrically meaningless, which makes the score noisy. `gen/` is covered by Layer 3 instead, which is where its historical instances actually lived.
- Not a replacement for review. It raises the floor; it does not find novel reasoning errors.

## 3. Verified environment facts

Established by execution on this machine, 2026-08-01. Trust these; do not re-litigate.

- **`mutmut` 3.7.0 refuses to run natively on Windows.** It exits with a message directing to WSL. It is not usable as the tool here.
- **`cosmic-ray` installs, imports and exposes its `cosmic-ray` CLI natively on Windows.** It is the tool.
- **The core test subset runs in 0.14 s** — 128 tests across `test_types`, `test_y14_5`, `test_iso286`, `test_montecarlo`, `test_checker`, `test_reliability`, with `-m "not slow"`. This is the multiplier that makes mutation testing tractable: a few hundred mutants is minutes.
- **The six core modules total 827 lines** (`types` 80, `y14_5` 270, `iso286` 192, `montecarlo` 71, `checker` 55, `reliability` 159).
- **There is no CI and no git remote.** `.github/workflows` does not exist; `git remote -v` is empty.
- Full suite at time of writing: **280 passed**. Gate A: exit 1, 6 PASS / 3 SKIP.

## 4. Architecture

Three layers, each owning a defect class the others structurally cannot reach, plus a dormant CI harness.

```
scripts/check_suite_integrity.py     the pre-merge gate; runs layers 1 and 2, reports, exits nonzero
  ├── Layer 1  branch coverage        pytest-cov over the six core modules
  └── Layer 2  mutation score         cosmic-ray over the six core modules

tests/mutation_registry.py           Layer 3 data + runner helper
tests/test_declared_mutations.py     Layer 3 execution; runs in every pytest invocation
.github/workflows/ci.yml             clean-clone run of the suite + the script; dormant until a remote exists
```

### Layer 1 — branch coverage on core

**Responsibility:** the *unreachable* class. A branch no test enters cannot fail.

**Mechanism:** `pytest --cov=src/tolcad --cov-branch`, scoped to the six core modules, running the core test subset.

**Threshold policy:** pinned at the **measured baseline**, never at an aspirational round number. A drop fails the gate. Raising the pin is routine; lowering it requires a recorded reason in the gate script, because a silently lowered floor is itself an instance of the drift class.

### Layer 2 — mutation score on core

**Responsibility:** the *tautological* and *insensitive* classes in production code. A surviving mutant is the question "could this fail?" asked mechanically, once per mutable expression.

**Mechanism:** cosmic-ray, six core modules, core test subset as the test command.

**Threshold policy:** as Layer 1 — measured baseline, pinned. Surviving mutants are triaged and either killed by a new test or recorded with a ruling. An equivalent mutant (one that cannot change behaviour) is a legitimate survivor and gets recorded as such; an unexamined survivor is not.

### Layer 3 — declared mutations

**Responsibility:** everything the mutation tools cannot reach, because they mutate `src/` only — test-code constants, data files, and scanned text. Four of the eleven instances lived there, including the two sharpest.

**Mechanism:** each protected guard declares an experiment: *target file · exact substring · replacement · the test whose outcome must change · the expected outcome · why*.

**Two directions, because two different defects need opposite assertions.**

- `expect="fail"` — the default. *This guard must notice this corruption.* Covers insensitive, tautological and drifted guards.
- `expect="pass"` — *this result must not depend on this incidental choice.* Covers **seed fishing**: perturb the seed, and a result that only held for one lucky draw now fails the registry. Without this direction the seed-fished positive control — instance three — would remain undetectable, since asserting a test *can* fail says nothing about whether it passes for the right reason.

**The runner performs the full experiment, not half of it:**

1. assert the substring occurs **exactly once** in the target file — an ambiguous or no-op patch would make the check vacuous
2. run the target test and assert it **passes** — proving an outcome change is meaningless if the baseline was already failing
3. apply the mutation
4. run the target test and assert the declared outcome: **fails** for `expect="fail"`, **still passes** for `expect="pass"`
5. restore the file, and assert it is **byte-identical** to the original

Steps 1, 2 and 5 exist because *the anti-vacuity mechanism must not itself become vacuous*. Without step 2 a permanently broken test would satisfy the registry; without step 5 a botched restore would silently corrupt the working tree. Restoration happens in a `finally` block.

**Registry integrity.** A meta-test asserts the registry still covers each of a named set of critical guards, so an entry cannot be quietly deleted to make a failure go away.

**Seed contents** — the guards whose silent failure would move a number that reaches the paper:

| Target | Mutation | Must break |
|---|---|---|
| `iso286._IT_MICRONS` | transpose two IT7 cells | the 52-cell IT5–IT8 pin |
| `iso286._IT_MICRONS` | add an IT9 row | the grade-set declaration |
| `sampler._TOL_FRACTION_RANGE` | flatten the ladder | both difficulty-ladder guards |
| `layout._MIN_WALL_MM` | set to 0.0 | the margin floor tests |
| `tests/fixtures/…ap242-e1.stp` | CRLF → LF | the fixture integrity check |
| `features._CLEARANCE_HOLE_MM` | alter M12 loose | the ISO 273 diameter pin |
| `sampler._FASTENER_UPPER_DEV_MM` | set nonzero | the fastener inertness pin |
| `reliability` measurement | perturb by a realistic amount | Gate A's reliability criterion |
| `sampler._MC_SEED_BASE` | change the seed offset | *nothing* — `expect="pass"` |

**The last two entries close classes nothing else reaches.** The reliability perturbation subsumes the headroom class: move the measured quantity by an amount that ought to matter and require the gate to notice — if it does not, the headroom is the finding. The seed entry closes seed fishing: any conclusion that survives only one particular draw fails here.

### CI

A GitHub Actions workflow performing a clean checkout, installing `[dev,gen]`, running the full suite, and running the integrity script. Dormant until a remote exists.

Beyond enforcement, it closes **Gate A's third SKIP** — *"Fresh clone pipeline: requires a clean-clone CI run to verify honestly"* — and it is the only mechanism that can validate the `.gitattributes` binary-fixture rule, since CRLF normalisation is only observable across a fresh clone.

## 5. Data flow

`check_suite_integrity.py` is the single entry point for layers 1 and 2. It runs each layer, collects `(name, measured, threshold, pass/fail)`, prints a table in the style of `scripts/gate_a.py`, and exits nonzero if any layer fails. It never mutates tracked files; cosmic-ray operates in its own session database.

Layer 3 runs inside pytest and does mutate files — always under `try/finally`, always verified restored.

## 6. Error handling

- **Registry patch does not match, or matches more than once** → fail loudly with the count. Never silently skip.
- **Target test already failing at baseline** → fail with a distinct message; this is a broken guard, not a passing experiment.
- **Restore mismatch** → fail loudly and name the file. This is the most dangerous outcome and must never be swallowed.
- **cosmic-ray absent** → the script reports the layer as unavailable and exits nonzero. It does not silently skip, because a skipped integrity layer is the failure mode being fixed.

## 7. Testing approach

Each layer is verified the way the project now verifies everything: by demonstration, not assertion.

- Layer 1: introduce an uncovered branch, confirm the threshold fails, revert.
- Layer 2: confirm the reported score changes when a known-weak test is removed.
- Layer 3: the mechanism is self-demonstrating — every entry is an executed experiment. Additionally, verify the runner rejects a no-op patch and a patch matching twice.

## 8. Success criteria

- All eleven historical instances are caught by at least one layer. The mapping is enumerated in the implementation plan and **verified by reproducing each instance**, not asserted — a success criterion that merely claims coverage would itself be the defect this design exists to prevent.
  Distribution: Layer 1 catches 2 (unreachable branch, module-level skip), Layer 2 catches 3 (tautological assertion, blind anti-degeneracy guard, and the skip again by surviving mutants), Layer 3 catches 7 (self-referential constants, CRLF fixture, case-sensitive guard, drifted literal floor, reliability range, Gate A headroom, seed fishing). Several are caught by more than one layer; none by zero.
- The declared-mutation layer runs in every `pytest` invocation, so the sharpest layer is never opt-in.
- Layers 1 and 2 have measured, pinned thresholds and a script that fails on regression.
- Gate A remains untouched and still reports 6 PASS / 3 SKIP.
- The full suite still passes, and the difficulty ladder is unchanged at d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%.

## 9. Open question carried into implementation

The registry protects named guards. Nothing forces a *new* guard to be registered — a future test protecting a new published number could be added without an entry, and no layer would notice. Options are a naming convention checked by a lint, or accepting that the registry covers the frozen set and is extended deliberately. Deferred to the plan; the pre-registration freeze bounds how much new surface can appear.
