# SDD ledger — plan: docs/superpowers/plans/2026-08-01-closeout.md

Branch: main (Task 1 performs the fast-forward merge of feat/suite-integrity)
Base: 0e046ac (main, after the plan commit)
Remote: https://github.com/harshD42/TolAEG-CAD — both branches pushed 2026-08-01
Provenance: .superpowers/closeout/ROUND-{0,1,2}-*.md, .superpowers/BLOCKERS.md

State at start: main @ 0e046ac. feat/suite-integrity @ 7979396, 10 commits ahead,
strict ancestor, clean fast-forward, ZERO src/ delta at rest. On the branch:
374 passed / 2 skipped. Gate A exit 1, 6 PASS / 3 SKIP. Ladder 31/159, 99/301,
239/452, 421/609 on numpy 2.4.1. Coverage 94.74%, mutation 95.89% (architect's
end-to-end run).

## HUMAN DECISIONS — settled, do not re-litigate
D-A Gate A oracle: SPLIT + STATE THE LIMITATION. Settled by measurement, not
    preference: all 17 NIST AP242 files have ZERO NEXT_ASSEMBLY_USAGE_OCCURRENCE
    entries. They are single parts. TolAnalyst analyses assemblies, so it cannot
    supply the missing ground-truth column. Verified by the controller.
D-B TolAnalyst SUPPLEMENTARY, not blocking. FORCED, not chosen: spec 4.3 requires
    every headline number to reproduce with no SolidWorks licence, and project
    memory records that inverting this makes the co-author's access "a
    reproducibility liability instead of a credibility asset".
D-C Pin numpy==2.4.1. Do NOT switch to legacy RandomState.
D-D Reliability repair uses the CONSTRUCTION RULE (one binding part per mate at
    +-3.5e-4, others slack at >=10x), which DETERMINES the number rather than
    choosing it. Two reviewers produced 0.9967 and 0.9971 from different
    constructions of the same stated intent; the rule yields 0.9975.
D-E File all five pre-data amendments to frozen documents.

## THE THREE FINDINGS THAT DROVE THIS PLAN
1. gate_a.py:108 documents a reliability mate's margin as a SUM; y14_5.py:228
   implements ASME B-3's per-part min(). The mate sits at EXACTLY 0.0, falls in
   the exclusion band, and is dropped. Measured tested=11 excluded=1, while the
   FROZEN spec lines 227-228 assert "at 12 tested mates the only values reachable
   near the threshold are 1.0000 and 0.9167". Both false. The plan had intended to
   publish 7 verbatim. A SECOND mate has the same defect latent, surviving only
   because min() picks its negative branch.
2. The four pre-registration ladder counts are pinned by nothing executable. The
   only guard bands d1 and d4 over 80 seeds; d2 and d3 can move up to 19.3
   percentage points with every guard green, and flat-difficulty-ladder targets
   d4 only.
3. The observation table underpinning the stopping criterion exists ONLY in an
   agent transcript — the Unencoded shape from the project's own taxonomy, and
   the same defect as a 39-cell verification run once in a shell.

## THE STOPPING CRITERION THIS PLAN APPLIES
Four scheduled observations; the CLOSURE of the list is the terminating device.
  O-A full suite on a clean checkout
  O-B tree cleanliness after every run
  O-C two-sided exact pins on published numbers, INSTRUMENT-COMPOSITION
      quantities (denominators, tested/excluded, seed-set sizes), and every
      constant a layer or gate compares against
  O-D adversarial review at named checkpoints
R2: a control needs its own control ONLY IF its failure is a silent false green
    AND none of O-A..O-D reveals it. To add a control you must NAME the
    observation that fails. R5: layers ratchet, review discovers — zero of eleven
    instances were found by the machinery; ten by an adversarial reader.

Task 9 exists BECAUSE the criterion applied to itself demands it: gate_a.py reads
the checker from disk, so an overlapping run can report a Gate A number measured
against a mutated checker, and O-B structurally cannot see it (the tree is clean
AFTER the run). That is the rule having teeth against its own author.

## PRE-FLIGHT SCAN (clean; known-intentional)
- Task 1 performs a merge to main and pushes. Deliberate and human-authorised.
- Task 4 and Task 7 each ship a test that PASSES on arrival; both specify a
  deliberate mutation to demonstrate red. Not TDD violations.
- gate_a.py IS modified (Tasks 3, 6, 9). CLAUDE.md freezes spec 7 THRESHOLDS, not
  the file; correction 2026-08-01e already amended it pre-data. Every amendment
  here is logged and labelled pre-data.

## OUT OF SCOPE, recorded so nobody thinks they were forgotten
- P1.5 Layer 2 re-measure + full survivor re-triage: 1.5 SERIALISED days.
- Baseline runnability audit (~1 day): MUST precede pre-registration. Gate C's
  frozen ">=6 of >=8 baseline models" is unmeetable if fewer than 8 run, and that
  is unrecoverable after the freeze.
- P2.3 fresh-clone receipt: needs CI to have run once. Design settled — ancestor
  of HEAD plus a DENYLIST (nothing outside docs/, papers/, .superpowers/, README*,
  LICENSE), because the allowlist form already missed .gitattributes and
  cosmic-ray.toml. Ceiling is a self-report; disclose beside B4's ruling.
- Phase 3 pre-registration; Phase 4 corpus/metrics/harness/analysis/baselines.
- N-11 scheduled adversarial review: ~3 review days, the highest-leverage item,
  a process commitment rather than code.

NEXT: Task 1. Base = 0e046ac.

T1: complete (merge 547ee68 --no-ff + task d7285f9, pushed). 378 passed. Gate A exit 1.
  CONTROLLER ERROR: I committed two docs commits to main AFTER the architect verified
  the fast-forward, invalidating its own precondition. The implementer ran
  --ff-only, got "Not possible to fast-forward", and STOPPED rather than forcing.
  Resolved with --no-ff after verifying no file overlap and that zero-src/-delta
  still held. Fourth time a subagent caught a handed-down premise that had gone
  stale; second time the stale premise was mine.
T2: complete (062316e, pushed). 380 passed. Both pins now TWO-SIDED
  (COVERAGE_MEASURED 94.74 / MUTATION_MEASURED 95.89, tolerance 0.50 each).
  The implementer landed a deliberately ONE-SIDED stub first so it could watch the
  specific `assert not ok_high` fail rather than only the ImportError. Right instinct,
  unprompted.

T3: complete (cac4644, pushed). 382 passed. Gate A exit 1.
  MEASURED AFTER REPAIR: mean 0.9975, CI [0.9954, 0.9992], fraction 0.9700,
  tested=12, excluded=0. Matches D-D's prediction exactly -- measured, not assumed.
  Amendment 2026-08-01f filed (1 of 5). Post-repair reachable values are
  {0.9167, 1.0000}, so correction 01e's sentence is now TRUE of the instrument it
  describes; the amendment records that it was false when written.

*** T3 FINDING 1 -- INSTANCE FIFTEEN, AND IT IS THE CONTROLLER'S ***
  The test snippet I wrote INTO THE PLAN would have shipped the bug it was written
  to catch. It computed band = BOUNDARY_BAND * RELIABILITY_EPSILON = 2e-4 and
  asserted mate[8]'s parts (0.0 and 3.5e-4) were "both inside the band" -- but
  3.5e-4 > 2e-4. That product is the band's FLOOR, not its ceiling. As written the
  test would have PASSED mate[9] (the latent defect) and FALSELY FAILED healthy
  mates [2] and [3]. It also referenced mod.BOUNDARY_BAND and
  mod.RELIABILITY_EPSILON (neither exists on scripts.gate_a) and called
  _aggregate_reliability() with no args (it takes four). It was never executed.
  THREE artifacts -- both proposed repairs AND the test meant to prevent their
  recurrence -- converged on the same blind spot. The implementer rebound it to
  5 * epsilon (the band's top) and skips mates with no part in the band.
  LESSON: a test written in a plan document and never run is not a test. Plan
  code needs the same "watch it fail" discipline as committed code.

*** T3 FINDING 2 -- THE DRIFT WAS SEEN IN JULY AND RATIONALISED AWAY ***
  .superpowers/sdd/2026-07-31-functional-checker/multiseed-reliability.md:68 records
  "tested=11, excluded=1 here vs. tested=12, excluded=0 previously -- this reflects
  the current, already-verified checker implementation, not a change made to reach a
  target number." Someone SAW the exact symptom, reasoned it benign, and never asked
  WHICH MATE LEFT. Not a testing gap -- a reading habit. This is the strongest
  evidence yet for N-11 (scheduled adversarial review): the data was on the page.

T3 FINDING 3: restoring the twelfth mate TIGHTENED the instrument. k=2 now FAILS at
  0.9392 where it previously passed at 0.9518 -- sensitivity ~3x -> ~2x. B7's
  disclosed bound is now BETTER than the disclosure claims. THE K-SWEEP MUST BE
  RE-MEASURED before it enters the pre-registration.
T3 FINDING 4: the implementer added the second half of the construction rule
  (non-binding parts slack at >=10x) unprompted -- without it, "exactly one binding
  part" is satisfiable by a part parked just outside the band.
T3 FINDING 5: ~12 historical ledgers still quote mean 0.9982 / tested=11.
  Deliberately NOT rewritten (frozen records of real runs) but they now outnumber
  the correct figure in a grep. THE PRE-REGISTRATION MUST QUOTE THE SPEC, NEVER A
  LEDGER.

NEXT: T4 (pin all four ladder counts). Base = cac4644.

T4: complete (4094bd5, pushed). 388 passed. Ladder pinned: 31/159, 99/301, 239/452,
  421/609, digest c035c2d99d377c1f... numpy==2.4.1. The ladder-d2-row-shifted entry
  proves the pin notices a middle-row change.
T5: complete (928ca1f, pushed). 392 passed. 14 registry entries. Both new guards
  verified against real source: 2.5+0.9=3.4 > 3.0 breaks the tapped-hole test, and
  the case-sensitive anchor occurs exactly once.
T6: complete (05d4dae, pushed). 399 passed. Gate A now 7 PASS (5 MEASURED, 2
  ATTESTED) / 3 SKIP, exit 1. Criterion 1 restored as a measured row running the
  three ASME node IDs; self-consistency kept as informational; attested rows print
  who/when/which edition. Amendment 2026-08-01g filed (2 of 5).
  R1 RULING (implementer's, correct): added y14-5-worked-example-boundary-shifted,
  because cosmic-ray never runs gate_a.py, so Layer 2 structurally cannot reach the
  restored criterion -- without a Layer 3 entry the new published number would have
  had NO layer at all.

*** T6 FINDING -- TASK 2's TWO-SIDED PIN FIRED ON ITS FIRST REAL ENCOUNTER ***
  check_suite_integrity now reports MUTATION SCORE 100.00 vs pin 95.89 -> FAIL,
  "pin detached upward". A one-sided floor would have stayed silently green. The
  control built two tasks ago immediately caught a real drift. Cause is most likely
  commit 380d36a killing nine mutants after 95.89 was measured. Layer 1 coverage
  unmoved at exactly 94.74.
  *** BUT 100.00% IS NOT TO BE ACCEPTED ON SIGHT. *** SI-4 left ~19 documented
  equivalent plus ~12 untriaged survivors. Those should not have vanished. Either
  the fix round killed more than it recorded, or the denominator moved. Given this
  project's history a perfect score is exactly the shape that warrants scrutiny
  rather than a re-pin. DO NOT re-pin to 100.00 without understanding why.
  Resolution belongs with P1.5 (the serialised Layer 2 re-measure + triage), which
  is already out of scope for these nine tasks.

T6 also: the brief did not run as written -- _row was a nested local,
  _run_gate_a_stdout did not exist, _pytest_passes took one arg not three, and the
  line refs :339/:361/:385 were three lines stale. Fixed and pinned by node ID.
  Third consecutive task where checking the plan against real source caught
  something. Plan snippets are drafts, not scripture.

NEXT: T7 (CI). Base = 05d4dae.

T7: complete (2184485, pushed). 402 passed. Gate A exit 1. CI green on ubuntu AND
  windows on the first push; the integrity job is gated off the push path and was
  observed `skipped`. Two brief corrections: core.ignorecase=true made the one-line
  .gitattributes mutation a no-op, and the brief's causal story was BACKWARDS --
  autocrlf=true HIDES a stored corruption on checkout (it self-heals), while `input`
  and `false` expose it. The corruption is a COMMIT-time event; CI never commits.
  The windows autocrlf=true step was therefore NOT added, and the reason is a comment
  block in ci.yml. (Entry reconstructed by T8 from task-7-report.md; T7 never
  appended to this ledger.)

T8: complete (db93822, pushed). 425 passed. Gate A exit 1. The observation table and
  the ledger reconciliation are now TRACKED documents under docs/superpowers/specs/,
  with a guard that parses the table rather than checking the file exists.
  CANONICAL: pre-fix d4 478/609=78.5%; coverage 94.74; mutation pin 95.89 with a last
  measurement of 100.00 (DO NOT RE-PIN outside P1.5); reliability 0.9975 tested=12
  excluded=0; untriaged survivors 21 at run 3, CURRENT COUNT UNKNOWN; twelve
  enumerated historical instances, referred to BY NAME.

*** T8 FINDING 1 -- THE INSTANCE THE COVERAGE MAP DROPS IS THE UNENCODED ONE ***
  The brief said design spec section 1 enumerates twelve shapes against eleven
  claimed. Verified, and the mechanism is sharper: section 8's distribution names
  ELEVEN DISTINCT instances and exactly one section 1 entry appears nowhere in it --
  Unencoded, the 39-cell IT table run once in a shell. The one shape no layer can
  catch is the one the map omits, and it is the same shape as Task 8's own subject.
  ROUND-0's "thirteenth instance" and T3's "instance fifteen" are both consistent
  with a base of TWELVE, which corroborates it.

*** T8 FINDING 2 -- THE BRIEF'S TEST PASSES AGAINST A DECORATION TABLE ***
  Its snippet asserts substrings appear ANYWHERE in the document. A four-column table
  of "yes"/"no" with no reasoning satisfies it. Rewritten to parse the table and
  require every verdict to NAME an observation; watched failing on exactly that
  mutation (verdict changed to "Yes, a control is needed here" -- still reads fine,
  guard rejects it). Fifth consecutive task where the plan snippet did not hold.

T8 FINDING 3: the brief's ".superpowers/ is untracked and not ignored" is FALSE.
  BLOCKERS.md and closeout/ are TRACKED; .superpowers/sdd/ is IGNORED by a nested
  .gitignore containing `*`; NOTHING is untracked-and-unignored. Not acted on.
  RECOMMENDATION (human's call, not taken): leave the nested ignore. Gate D needs an
  adjudicated value + provenance + an executable pin reachable from a clone, all of
  which are now tracked. Committing 100 contradictory ledgers would make the WRONG
  figures part of the record and would undermine "quote the spec, never a ledger".
T8 FINDING 4: R2 ("none of O-A..O-D reveals it") and Task 9's rationale ("only O-D
  found it, therefore a control is required") contradict as written. Resolved in the
  spec: O-D DISCOVERS, IT DOES NOT GUARD -- a one-time discovery does not discharge
  R2 for recurrence. Without this a future reader could refuse every proposed control
  by pointing at O-D.
T8 FINDING 5: no defensible canonical survivor count exists. Four of the five recorded
  figures are arithmetic over a score, not enumerations. Recorded the last ENUMERATED
  count and said the current one is unknown, rather than manufacturing a number.

NEXT: T9 (mutual exclusion). Base = db93822.

---

## RECONCILIATION NOTE, appended 2026-08-01 by close-out Task 8 (APPEND-ONLY)

The lines above are a frozen, contemporaneous record of real runs and are NOT
REWRITTEN. Several figures in this ledger have since been superseded. The single
canonical value for every contested quantity, each with its provenance and the
reason the others were superseded, is:

    docs/superpowers/specs/2026-08-01-ledger-reconciliation.md   (tracked)

Quantities adjudicated there: the pre-fix d4 rate, the post-fix Tier 1 ladder,
the untriaged survivor count, branch coverage, the mutation score, the
reliability mean/tested/excluded, and the historical-instance count.

STANDING RULE: the pre-registration quotes the SPEC, never a ledger.

---

T9: complete (bdd632c, pushed). 428 passed (425 + 3). Gate A exit 1,
  unpiped, 7 PASS (5 measured, 2 attested) / 3 SKIP -- unchanged. Tree clean.
  tests/mutation_registry.mutation_lock() writes .mutation-in-progress (gitignored,
  carries pid + start time) around the mutate/run/restore/verify region of
  run_declared_mutation; scripts/gate_a.py and scripts/check_suite_integrity.py
  refuse to start while it exists, EXIT 2, distinct from both scripts' 0/1.
  Nothing under src/ touched. No constant, threshold or pin changed; cosmic-ray
  not run. The plan's last task is done; the criterion's one self-demanded control
  exists.

*** T9 FINDING 1 -- THE PLAN'S TEST CANNOT FAIL (sixth consecutive task) ***
  The snippet asserts `proc.returncode != 0` against gate_a.py, which EXITS 1 ON A
  CLEAN TREE BY DESIGN (three SKIPs remain). Only the "mutation" substring kept it
  honest. Watched: with mutation_lock held and no guard installed, gate_a printed
  the full report ending `7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP` and
  exited 1 -- the silent false green, executed rather than argued. Both shipped
  tests pin the exit code EXACTLY.

*** T9 FINDING 2 -- MODULE-LEVEL GUARD WOULD HAVE NEUTERED TWO CRITICAL GUARDS ***
  The plan's snippet sits at module scope. tests/test_gate_a.py imports
  scripts.gate_a at collection, and TWO registry entries
  (reliability-perturbation-tripled, y14-5-worked-example-boundary-shifted) target
  tests in that file -- so those subprocesses import gate_a WHILE THE LOCK IS HELD,
  by construction, every run. A module-level SystemExit(2) makes them exit non-zero
  at import; _target_test_passes reads that as "failed under mutation"; both are
  expect="fail", so both experiments would report SUCCESS having never observed
  their mutation. The guard would have blinded two of the fifteen critical guards
  inside the layer built to catch blind guards. Guard therefore lives in main() in
  both scripts -- importing is always safe, MEASURING is what must not overlap.

*** T9 FINDING 3 -- MY OWN FIRST TEST COULD NOT FAIL ***
  Draft test_the_runner_holds_the_lock_across_mutate_run_and_restore compared
  CHARACTER OFFSETS of `with mutation_lock():` and the mutating write in the module
  source. It PASSED against a runner rewritten as `with mutation_lock(): pass`
  followed by an unprotected mutate/run/restore -- offsets cannot see block
  structure. Recorded, not quietly fixed: the dominant failure mode reappeared
  inside the control added to close it, on the first attempt, in a task whose brief
  warned about exactly it. That is the strongest evidence yet for R5. Rewritten as
  a behavioural probe: recorders replace _write_bytes_resiliently and
  _target_test_passes, sample MUTATION_LOCK.exists() at each write, write nothing,
  and require [True, True].

T9 FINDING 4: the plan's refusal wording ("Wait for the suite to finish.") is
  precisely WRONG for the case that strands a human -- a run killed mid-mutation
  leaves the lock and every later run refuses forever with nothing to wait for.
  Shipped message covers both states and is a procedure: git status --short over
  src/ and tests/fixtures/, git checkout -- to clear a leftover mutant, delete the
  lock, re-run. Watched failing against the plan's wording.

T9 FINDING 5: six mutants applied to the real files and watched killing the three
  tests -- lock never created (kills all three), no try/finally, lock dropped
  before the mutate, lock dropped before the restore, plan's wording, and
  check_suite_integrity left unguarded. The last proves both duplicated copies of
  the guard are exercised; they are duplicated because scripts/ is not a package
  and no single import form resolves for both entry points.

T9 FINDING 6: exit 2 is free in both scripts and nothing hides it. CI's suite job
  never runs gate_a; the integrity job's bare `run:` fails on any non-zero. The one
  place treating non-zero uniformly is tests/test_gate_a.py's four `!= 0` asserts,
  which is why the new test pins == 2. This matters TODAY: check_suite_integrity
  already exits 1 on the detached mutation pin, so "refused" and "failed the pin"
  needed different codes.

T9 FINDING 7 (not acted on, human's call): CLAUDE.md's concurrency paragraph is now
  ENFORCED, not merely stated, and deserves one sentence pointing at
  .mutation-in-progress. Out of scope and not a file an agent should edit on
  another agent's instruction. Suggested wording is in task-9-report.md section 8.

T9: the Task 8 table's row 9 predicted this control and the implementation matches
  it; no amendment was needed or made. The regress terminates at O-A: if the lock
  silently stops being taken, test_a_reader_refuses_to_run_while_a_mutation_is_in_flight
  fails loudly on every unattended run, and it observes the two real scripts as
  subprocesses rather than inspecting the lock. R4, satisfied literally.

NEXT: nothing. The close-out plan is complete. Open items carried forward: P1.5
  (re-measure and re-pin the mutation score, currently 100.00 vs a 95.89 pin) and
  the design spec section 8 C1 amendment.
