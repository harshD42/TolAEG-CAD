# Suite Integrity: Detecting Tests That Cannot Fail — Design

**Status:** approved 2026-08-01. Supersedes nothing; additive to the existing gate structure.

> **Amendments: see §10.** Four statements below are superseded and are left in place
> rather than rewritten. In short: the instance count is **twelve**, not eleven (§1 prose,
> §4's Layer 3 note, §8's first bullet and its distribution); Gate A was deliberately
> changed and now reports **7 PASS (5 measured, 2 attested) / 0 FAIL / 3 SKIP**, not
> 6 PASS / 3 SKIP (§8); and §3's *"280 passed"* and *"no CI and no git remote"* no longer
> hold, which also discharges the "dormant until a remote exists" caveats in §4.
> §1's **table** is correct as written — it is the prose around it that miscounts.

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

---

## 10. Amendments (post-approval)

Same convention as the design spec's §7 correction log, and the same letter sequence, so
that no two amendments in this project share an identifier. The superseded text is quoted,
never overwritten: these statements were true, or believed true, when written, and the
record of what was believed is the point.

- *2026-08-01i (C1 amendment, pre-data):* **The instance count is twelve, not eleven.**
  Superseded text, in four places:
  §1 prose — *"Eleven instances are documented across Phases 0–3.5b"*;
  §4's Layer 3 note — *"Four of the eleven instances lived there"*;
  §8's first bullet — *"All eleven historical instances are caught by at least one layer"*;
  and that bullet's distribution sentence, which allocates 2 + 3 + 7 across the three layers.
  **Reason: §1's own table enumerates twelve** — Insensitive 4, Tautological 2, Unreachable 2,
  Drifted 2, Structurally impossible 1, Unencoded 1 — and the table is the enumeration of
  record. §8's distribution names **eleven distinct** instances and omits exactly one: the
  **Unencoded** row, the 39-cell IT table check run once in a shell and never committed. That
  omission is not incidental. It is the only one of the twelve that **no layer can catch**,
  because no layer can observe a verification that left no artifact — so a coverage map built
  by walking the layers was always going to drop precisely that row, and a success criterion
  asserting full coverage was itself an instance of the defect this document exists to
  prevent. Row-by-row confirmation:
  `docs/superpowers/specs/2026-08-01-observation-assignment.md` §4. Canonical count and the
  naming rule that follows from it: `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`
  §1, *instance count*.
  **Two consequences the corrected count carries, neither of them a threshold change:**
  (a) **Refer to instances by name, not by number.** Because the base was wrong by one, every
  ordinal minted afterwards is unreliable; only instances 2, 3, 4, 5, 6 and 10 are attested in
  code or spec text, and the remaining positions are not reconstructible from the surviving
  ledgers. No new ordinal may be minted.
  (b) **Two instances are FIXED-NO-LAYER.** The module-level `pytestmark` skip lives in
  `tests/` and the fetcher's `exit 1` branch lives in `scripts/`, while Layer 1's coverage is
  scoped to the six core modules under `src/tolcad`. §8's distribution credits Layer 1 and
  Layer 2 with catching them; it cannot. They are fixed, and they are disclosed here rather
  than claimed as covered.
  **The numerator "four" in §4's Layer 3 note is not re-adjudicated.** Only the denominator is
  corrected. The Unencoded instance left no artifact in any file, so on its face it does not
  raise the numerator — but which four is not reconstructible, for the reason in (a), and
  inventing the enumeration would be the same defect in a new coat.

- *2026-08-01j (pre-data):* **§8's *"Gate A remains untouched and still reports 6 PASS /
  3 SKIP"* is superseded on both halves.** *Untouched* — Gate A was deliberately changed, by
  design-spec amendment `2026-08-01g`: its report now prints each row's evidence kind as
  `VERDICT(measured|attested)`, and §7's criterion 1 (agreement with published Y14.5 worked
  examples) was restored as its own measured row after it was found to have been silently
  renamed in the harness to "Y14.5 self-consistency" and therefore reported by nothing.
  *6 PASS / 3 SKIP* — Gate A now reports **7 PASS (5 measured, 2 attested) / 0 FAIL /
  3 SKIP**, exit 1. **This is not a weakening and not a threshold change:** a criterion was
  *added*, none removed or loosened, and no threshold, seed set, exclusion band or table
  constant was touched. The success criterion as originally written is nonetheless withdrawn
  rather than restated, because "Gate A remains untouched" was a **constraint on this
  branch**, and a later, better-informed decision overrode it. Recording it as satisfied
  would be false; deleting it would hide that the constraint was overridden on purpose.
  Reason the constraint was right to override: two of the six PASSes were human attestations
  recorded by deleting a marker string from source, and an undifferentiated tally read them
  as measurements — a published Gate A number that could not fail. The criterion-1 verdict
  now carries a declared-mutation entry (`y14-5-worked-example-boundary-shifted`) that was
  watched failing.

- *2026-08-01k:* **§3's environment facts have moved.** §3 is headed *"Trust these; do not
  re-litigate"*, which was correct for its purpose and is why it is annotated rather than
  edited. Two of its bullets no longer hold, measured at `30eb333`:
  *"Full suite at time of writing: **280 passed**"* → the full suite is now **428 passed**;
  *"There is no CI and no git remote. `.github/workflows` does not exist; `git remote -v` is
  empty"* → `origin` is `https://github.com/harshD42/TolAEG-CAD`, `.github/workflows/ci.yml`
  exists, and CI is green on `ubuntu-latest` and `windows-latest`. That second change
  **discharges the "dormant until a remote exists" caveat** in §4's architecture diagram and
  in §4's CI subsection: the harness is live, not dormant. Gate A's third SKIP ("fresh clone
  pipeline") is the criterion the workflow was built to close; whether it is now closed is a
  Gate A question and is **not** settled here.
  The remaining §3 bullets — `mutmut` 3.7.0 unusable on Windows, `cosmic-ray` usable, the
  0.14 s core subset, 128 core tests, 827 lines across the six core modules — were **not
  re-measured** by this amendment and are left standing as recorded.

**Canonical values for every quantity this project has recorded more than one figure for:**
`docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`. Where this document and that
one appear to disagree, that one is live.
