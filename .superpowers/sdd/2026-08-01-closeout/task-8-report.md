# Task 8 report: the stopping criterion, committed; the ledgers, reconciled

Base: `main` @ 2184485. Result: `main` @ **db93822**
(`db93822289eb3300f73cfb53fe5be46bd66b1c96`), pushed to
`https://github.com/harshD42/TolAEG-CAD` (`2184485..db93822  main -> main`).

## Files

- Created `tests/test_observation_assignment.py` (23 tests).
- Created `docs/superpowers/specs/2026-08-01-observation-assignment.md`.
- Created `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md` — **not in the
  brief**; added because the SDD ledgers are gitignored (see §5) and Gate D's
  traceability needs the canonical values in a file a clone can see.
- Modified `.superpowers/BLOCKERS.md` (tracked): append-only reconciliation note.
- Modified six `.superpowers/sdd/*/progress.md` ledgers: append-only pointer notes.
  These are gitignored and therefore **not** in the commit; they are local only.
- **`.gitignore` NOT modified.** The brief's premise for touching it was false (§5).

## 1. RED — verbatim

First run, before either document existed:

```
$ python -m pytest tests/test_observation_assignment.py -v
...
E       AssertionError: C:\Users\harsh\Downloads\Projects\Paper1\docs\superpowers\specs\2026-08-01-observation-assignment.md does not exist. The observation-assignment table exists only in an agent transcript -- the Unencoded shape from the design spec's own taxonomy, one session expiry from gone.
E       assert False
E        +  where False = is_file()
E        +    where is_file = WindowsPath('C:/Users/harsh/Downloads/Projects/Paper1/docs/superpowers/specs/2026-08-01-observation-assignment.md').is_file

FAILED tests/test_observation_assignment.py::test_the_observation_table_is_committed
FAILED tests/test_observation_assignment.py::test_every_observation_and_rule_is_defined
FAILED ...::test_every_named_control_has_exactly_one_assignment_row[run_declared_mutation]
FAILED ...::test_every_named_control_has_exactly_one_assignment_row[test_the_registry_still_covers_every_critical_guard]
FAILED ...::test_every_named_control_has_exactly_one_assignment_row[B2]
FAILED ...::test_every_named_control_has_exactly_one_assignment_row[B3]
FAILED ...::test_every_named_control_has_exactly_one_assignment_row[re-run-and-compare]
FAILED ...::test_every_named_control_has_exactly_one_assignment_row[B10]
FAILED ...::test_every_named_control_has_exactly_one_assignment_row[B9]
FAILED ...::test_every_named_control_has_exactly_one_assignment_row[ladder pin]
FAILED ...::test_every_named_control_has_exactly_one_assignment_row[mate[8]]
FAILED ...::test_every_named_control_has_exactly_one_assignment_row[mutual exclusion]
FAILED ...::test_every_row_names_the_observation_that_decides_it
FAILED ...::test_the_mutual_exclusion_row_is_justified_by_O_B_being_blind
============================= 14 failed in 0.13s ==============================
```

After adding the reconciliation guards (still before either document existed):

```
E       AssertionError: C:\...\docs\superpowers\specs\2026-08-01-ledger-reconciliation.md does not exist. Gate D requires every claim traceable to a logged run, and the SDD ledgers disagree with themselves on nearly every quantity. They are also gitignored, so the canonical values must be recorded somewhere a clone can see.
...
23 failed in 0.14s
```

### 1.1 RED is not enough — the guard was watched failing on a *decoration* table

An existence check passes against a table of "yes"/"no" with no reasoning. So the
mutation that matters is not "delete the file", it is "make the table decorative".
Executed and watched, then restored byte-identically:

```
mutation: "Yes - none of O-A...O-D reveals it, and the failure"
       -> "Yes, a control is needed here, and the failure"

E  AssertionError: row "mutual exclusion between the mutation layer and readers of
   `src/` (Task 9's `mutation_lock`)": verdict 'Yes, a control is needed here, ...'
   names no observation. R2 requires naming the observation that reveals the defect
   (No) or the fact that none does (Yes).
1 failed, 22 passed in 0.10s
RESTORED byte-identical: True
```

The verdict still read "Yes" and still sounded reasonable. The guard rejected it
because it no longer named an observation. That is the property that makes the table
an instrument rather than prose.

## 2. The table's contents

Four observations (O-A clean-checkout suite, O-B tree cleanliness, O-C two-sided
exact pins including instrument-composition quantities, O-D adversarial review),
rules R1–R6, and ten worked rows: *control · failure mode · revealed by · needs its
own control?*

| Control | Revealed by | Verdict |
|---|---|---|
| `run_declared_mutation`, the declared-mutation runner | O-B (plus O-A next run) | No — O-B |
| `test_the_registry_still_covers_every_critical_guard` | O-D only | No — O-D; no mechanical control can (B4) |
| B2, the OSError→AssertionError restore conversion | O-B | No — the branch only fires when the tree is already corrupt |
| B3, no post-triage survivor verification | O-C, now two-sided | No — **and the verdict changed because O-C changed** |
| re-run-and-compare survivor control (proposed, not built) | O-C | No — **R2 forbids building it** |
| B10, restoration not crash-safe | O-B, O-A | No — a SIGKILLed run produces no green to be false |
| B9, whole-file CRLF normalisation | O-A + the suffix guard | No — loud (R3); the suffix guard bounds blast radius, does not fix B9 |
| the ladder pin | O-C, all four counts + digest | No — O-C applied honestly, no new control |
| `mate[8]`'s partial degeneracy | O-C clause (b) only | No — **this instance is why O-C names instrument composition** |
| mutual exclusion (Task 9) | **none** | **Yes** — O-B is structurally blind |

**Tested on Task 9's case, as required.** Walked cold in §3.1 of the spec: silent
false green (yes) → O-A no → O-B no, *and not contingently* (O-B observes the tree
**after** the run; the corruption exists only **during** it) → O-C no (the number is
real; the instrument was wrong) → O-D found it but cannot be scheduled per run →
verdict Yes, named failing observation **O-B**. The table produced the answer without
appeal to judgement.

### 2.1 One thing the plan left ambiguous, now decided in writing

R2 says "none of O-A…O-D reveals it", yet the plan's own Task 9 rationale says "only
O-D found it" and *still* demands a control. Read literally those contradict. §2.1 of
the spec resolves it: **O-D discovers; it does not guard.** O-D is scheduled at
checkpoints with a duty cycle in review-days, so a one-time discovery does not
discharge R2 for that defect's recurrence — which is exactly R5. Without this, a
future reader could refuse every proposed control by pointing at O-D.

## 3. Reconciliation: canonical values and provenance

Recorded in `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`, one
`CANONICAL` line per quantity, guarded by the test.

| Quantity | Canonical | Provenance | Superseded |
|---|---|---|---|
| pre-fix d4 rate | **478/609 = 78.5%** | procedural-generator `progress.md:50` (`131 pass / 478 fail`, 131+478=609), corroborated at `:185` | `0/0/0/69.1%` — the 69.1% is the **post**-fix d4 carried backwards; a transcription error, not two runs disagreeing |
| Tier 1 ladder (post-fix) | **31/159, 99/301, 239/452, 421/609**, seeds 0–199, numpy 2.4.1, digest `c035c2d99d377c1f…` | `tests/gen/test_ladder_pin.py` @ 4094bd5 | none — eight re-measurements, bit-identical |
| untriaged survivors | **21 at run 3** (40 measured − 19 corrected equivalents); **current count UNKNOWN**, owned by P1.5 | suite-integrity `progress.md:261,301`; `task-4-fix-report.md:129` | ~17 (used the pre-correction 23); ~12 (unsourced carry-forward, BLOCKERS B1); ~27 (inferred from 95.89, never enumerated); 0 (inferred from 100.00) |
| branch coverage | **94.74%** | `COVERAGE_MEASURED` @ 062316e, two-sided ±0.50; re-measured green in T6 @ 05d4dae | 48.0 (superseded by **scope** — included `gen/`, a category error); 91.64; 94.12 |
| mutation score | **pin 95.89 ± 0.50; last measurement 100.00 — they disagree, and that is the control working. DO NOT RE-PIN.** | `MUTATION_MEASURED` @ 062316e; the 100.00 observation is T6 @ 05d4dae | 93.85 + derived floor 93.35 (drift F1); 57.69 (run 2, different denominator); 75.4 (wrong denominator, 1118 not 650); 18.2 (per-file `types.py` spike — a methodology note, never a layer score) |
| reliability | **mean 0.9975, CI [0.9954, 0.9992], fraction 0.9700, tested=12, excluded=0**, 200 seeds | T3 @ cac4644 under construction rule D-D; amendment 2026-08-01f; re-confirmed by running `gate_a.py` at 2184485 | 0.9982 / tested=11 / excluded=1 in ~12 ledgers; reachable-values `{0.9091, 1.0}`; frozen §7 lines 227–228; candidate repairs 0.9967 and 0.9971 |
| instance count | **twelve enumerated shapes, referred to BY NAME not by number** | suite-integrity design spec §1 table, counted row by row: 4+2+2+2+1+1 | eleven (§1 prose, §4, §8, BLOCKERS:78); the ordinals "thirteenth" and "fifteenth" as a scheme |

### 3.1 The root cause, verified rather than repeated

The brief said the §1 table enumerates twelve against eleven claimed. That is true —
and the *mechanism* is sharper than "a miscount". §8's distribution (Layer 1 catches
2, Layer 2 catches 3, Layer 3 catches 7) names **eleven distinct** instances, and I
mapped all twelve §1 entries against them one by one. Exactly one §1 entry appears
nowhere in §8:

> **Unencoded** — the 39-cell IT table check run once in a shell, never committed.

The instance the coverage map silently drops is the one shape no layer can catch,
because no layer can observe a verification that left no artifact — and it is the
identical shape as this task's own subject. Both are now closed: the IT table is the
committed 52-cell IT5–IT8 pin with an executed `it7-row-transposed` registry entry,
and the observation table is this commit.

Corroboration for twelve being the true base: ROUND-0 calls F1 the "thirteenth
instance" and T3 Finding 1 calls itself "instance fifteen". Both are consistent with a
base of twelve, not eleven.

Only instances **2, 3, 4, 5, 6, 10** are attested in code or spec text. The other six
positions cannot be reconstructed from the surviving ledgers, and inventing them would
be the same defect in a new coat — hence "by name, not by number".

### 3.2 Not rewritten

The original ledger lines stand. All notes are append-only footers pointing at the
canonical file, added to `BLOCKERS.md` and to the six `progress.md` ledgers. A test
asserts the reconciliation document itself claims append-only status, so the promise
is guarded rather than stated.

## 4. Full suite, Gate A, clean tree

```
$ python -m pytest -q
425 passed in 61.40s (0:01:01)          # 402 + 23 new

$ python scripts/gate_a.py > /dev/null 2>&1; echo "GATE_A_EXIT=$?"
GATE_A_EXIT=1                            # no pipe; 7 PASS (5 measured, 2 attested) / 3 SKIP

$ git status --short
(empty)

$ git log --oneline -1
db93822 docs: commit the observation-assignment table and reconcile the ledgers
```

`scripts/check_suite_integrity.py` still FAILS on mutation 100.00 vs pin 95.89. Out of
scope, untouched, and now recorded as the canonical open discrepancy.

## 5. `.superpowers/` tracking — measured, and a recommendation, not a decision

**The brief's premise is false, and I did not act on it.** It says "remove
`.superpowers/` from being untracked-and-unignored: commit it". Measured at 2184485:

```
$ git ls-files .superpowers/
.superpowers/BLOCKERS.md
.superpowers/closeout/ROUND-0-architect-plan.md
.superpowers/closeout/ROUND-1-qa-critique.md
.superpowers/closeout/ROUND-2-architect-revised.md

$ git check-ignore -v .superpowers/sdd/2026-08-01-closeout/progress.md
.superpowers/sdd/.gitignore:1:*    .superpowers/sdd/2026-08-01-closeout/progress.md

$ git status --short --untracked-files=all .superpowers/
(empty)
```

- **Tracked:** `BLOCKERS.md` and all three `closeout/ROUND-*.md`.
- **Ignored:** everything under `.superpowers/sdd/`, by a nested `.gitignore`
  containing a single `*`.
- **Untracked-and-unignored: nothing.** There is no accidental state to sweep up, so
  the brief's Step 3 instruction is a no-op resting on a wrong premise. Following it
  literally would have required `git add -f` against a deliberate ignore.

**What Gate D actually needs.** Gate D requires every *claim* traceable to a logged
run. That is satisfied by an adjudicated value plus its provenance plus an executable
pin, all reachable from a clone. It is not satisfied by shipping 100 hour-by-hour
ledgers that contradict each other — committing them verbatim would preserve the
contradictions in the artifact of record, which is what QA's O7 warned about.

**Recommendation: leave the nested ignore in place. Do not track
`.superpowers/sdd/`.** Reasons:

1. The traceability requirement is now met by tracked files: the two new specs, the
   design specs, and the pins in `tests/` and `scripts/`.
2. The ledgers' contradictions are their nature, not a bug — they are contemporaneous.
   Tracking them makes the wrong figures a permanent part of the published record and
   guarantees a future grep returns ~12 ledgers quoting 0.9982 alongside the spec's
   0.9975. The standing rule "quote the spec, never a ledger" is much harder to hold
   once the ledgers ship.
3. They contain agent-process detail (briefs, transcripts of reasoning) that is not
   research provenance and would invite reviewers to litigate process rather than
   method.
4. The stated risk — "one `rm -rf` from gone" — is real but is a *backup* problem, not
   a version-control problem, and it is now largely mooted: everything load-bearing in
   the ledgers has been lifted into two tracked specs by this task.

**If the human disagrees**, the cheap middle path is to track `.superpowers/sdd/`
under an explicit un-ignore (`!*/progress.md`) so only the six progress ledgers ship,
each already carrying an append-only footer that names the canonical file. I did not
do this; it is a one-line `.gitignore` change and a human's call.

## 6. Where the brief did not work as written

Fifth consecutive task with this finding.

1. **"`.superpowers/` is untracked and not ignored" — false.** Half the tree is
   already tracked and the other half is ignored by a nested rule. Verified above.
   Consequence: the brief's Step 3 sentence and its `.gitignore` entry in the file
   list are both void.
2. **The brief's test snippet passes against a decoration table.** It checks that
   strings like `"B2"` and `"mutual exclusion"` appear *anywhere in the document* —
   satisfied by a bulleted list, by prose, or by a four-column table of "yes"/"no"
   with no reasoning. The brief's own framing ("if your table cannot do that, it is
   decoration") describes a property its snippet does not test. Rewritten to parse the
   table: exactly one row per control, and every verdict must name an observation.
   Watched failing on that specific mutation (§1.1).
3. **R2 vs Task 9's rationale contradict on O-D**, and the brief inherits it. Resolved
   in writing (§2.1) rather than left for the next reader.
4. **The reconciliation had nowhere tracked to live.** The brief routes it to
   `.superpowers/sdd/*/progress.md`, every one of which is gitignored — so the
   reconciliation for a Gate D traceability requirement would itself have been
   invisible to a clone. That is the *Unencoded* shape again, one level up. Added the
   tracked companion doc.
5. **Survivor count: no canonical value is defensible.** The brief asks for one value
   among ~12 / ~17 / ~27 / 0. Four of those five figures are arithmetic over a score,
   not enumerations of a set. Recorded the last *enumerated* count (21 at run 3, after
   the equivalents correction from 23 to 19) and stated plainly that the current count
   is unknown. Picking one of the inferences would have manufactured a number.
6. Minor: `progress.md` has **no T7 entry** — Task 7 landed (2184485, CI green both
   platforms) but never appended to the ledger. Recorded by this task.
