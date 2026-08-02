# SDD ledger — plan: docs/superpowers/plans/2026-08-01-suite-integrity.md

Branch: feat/suite-integrity
Base: cedd86a (master, after the ISO 273 merge aa50b46 + IT-pin merge a2f2186
      + spec 5e7b509 + plan cedd86a)
Design spec: docs/superpowers/specs/2026-08-01-suite-integrity-design.md
Prior ledgers: .superpowers/sdd/2026-08-01-iso273-traceability/progress.md and the
               two before it.

Baseline at cedd86a: 280 passed. Gate A exit 1, 6 PASS / 3 SKIP.
Tier 1 ladder, seeds 0-199: d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%.

WHY THIS PLAN. Eleven documented instances of "the test that cannot fail", three
of them on the immediately preceding branch. Awareness has already been tried and
failed: the pattern was in project memory and in nearly every review prompt of
this session, and three new instances still landed. This builds mechanical
detection instead.

HONEST FRAMING, recorded so nobody mistakes it later: THIS SATISFIES NO GATE
CRITERION. It is not on the critical path to Gate B. It is insurance on the
numbers Phase 4 will produce. The human was shown that framing explicitly and
chose to build it now anyway, on the grounds that Phase 4 is where such a defect
stops being embarrassing and becomes a published number that is wrong.

SPIKED FACTS (verified by execution 2026-08-01, do not re-litigate):
  * mutmut 3.7.0 REFUSES to run natively on Windows -- exits directing to WSL.
    cosmic-ray installs, imports and exposes its CLI natively. cosmic-ray is the tool.
  * Workflow: cosmic-ray init <cfg> <db> ; cosmic-ray exec <cfg> <db> ; cr-report <db>.
    Report tail gives "total jobs: N" and "surviving mutants: M (P%)".
  * *** THE TEST-COMMAND MUST BE THE WHOLE CORE SUBSET. *** Spiked both ways on
    types.py: per-file gave 12 survivors of 66 (18.2%); full core subset gave
    5 of 66 (7.58%). checker.py and y14_5.py tests exercise types.py heavily, so
    a per-file command inflates survivors and measures nothing.
  * types.py: 66 mutants, 28s against the full subset. Core is 827 lines, so
    expect ~600-700 mutants and ~5 min for all six modules.
  * Core test subset: 128 tests in 0.14s.
  * cosmic-ray emits TestOutcome.INCOMPETENT for mutants that cannot execute
    (RemoveDecorator on a dataclass). Neither killed nor surviving -- must leave
    the denominator.
  * core.autocrlf=true, so tracked files are CRLF on disk. Anchors containing a
    newline will not match naively. The runner normalises \r\n -> \n for matching
    and restores from the ORIGINAL BYTES.
  * No CI, no git remote.

A REAL FINDING FROM THE SPIKE, for Task 4's triage: types.py has 5 surviving
  mutants against the full core subset, including `if upper_dev < lower_dev` ->
  `<=` surviving. That means NO TEST CONSTRUCTS A ZERO-WIDTH TOLERANCE BAND
  (upper_dev == lower_dev) -- a legitimate case, a basic dimension with no
  tolerance. That is a genuine coverage gap in the most foundational module.

ANCHORS AND NODE IDS: every registry anchor was verified to occur exactly once
  (after newline normalisation) and every test node id verified via
  --collect-only, during planning. One anchor FAILED that check and was fixed:
  "_MIN_WALL_MM = 4.0" matches TWICE in layout.py (docstring line 32, assignment
  line 67), so the anchor carries a leading newline. Also "ISO-10303-21;" is NOT
  usable for the fixture -- it appears twice (header and END-ISO-10303-21;) --
  so the binary anchor is "HEADER;\r\n", which occurs once.

PRE-FLIGHT SCAN (clean; known-intentional):
  - Task 3 Step 3 ships COVERAGE_FLOOR = 0.0 and Task 4 ships MUTATION_FLOOR = 0.0,
    both replaced in each task's Step 4 from a measured run. That two-step is
    deliberate: the plan refuses to guess a threshold.
  - Two tests assert the floors are NOT round numbers. That is intentional, not
    cargo-culting -- a floor pinned at 80 or 90 is a choice, not a measurement.
  - Task 1's runner-guard tests deliberately construct invalid DeclaredMutations
    and assert they are rejected. The registry must guard itself.

NEXT: Task 1 (declared-mutation runner). Base = cedd86a.

SI-1: complete (commit 95bea17, review clean / approved). 286 passed (+6), +1.5s
  wall clock. Gate A exit 1 unchanged. Tree clean. No tests/__init__.py needed --
  Python 3.13 namespace packages plus the existing pythonpath resolved the import.
SI-1: CONTROLLER-VERIFIED the core property independently -- pointed the runner at
  a mutation NO test can detect (a docstring reword in types.py) and it correctly
  raised "still PASSED with src/tolcad/types.py corrupted", leaving the file
  byte-identical. The mechanism does the thing it exists to do.
SI-1: the reviewer verified BOTH shipped entries are genuine experiments by reading
  the target tests, not by trusting the report; confirmed the byte-identity check
  runs AFTER the try/finally so it observes the restored state; and confirmed no
  conftest.py or pytest.ini anywhere deselects the `mutation` marker.

SI-1: *** IMPORTANT STRUCTURAL NOTE, CARRIED TO SI-2's REVIEW ***
  expect="pass" has no protection against a SEMANTICALLY INERT mutation.
  __post_init__ only rejects find == replace; it cannot verify the mutation
  touches a code path the target test exercises. For expect="fail" this is
  self-correcting -- the runner measures a real outcome change. For expect="pass"
  a trivially inert anchor (a comment edit) would satisfy the runner while
  proving nothing, and expect="pass" is precisely the direction created to close
  seed fishing. SI-2 ships the only such entry.
  CONTROLLER'S PRE-ANALYSIS of that entry, to be checked not trusted: the seed
  mutation changes "seed": 12345 -> 24680 inside a live check() call, so it IS
  behaviourally load-bearing (different draws). The guarded conclusion -- that
  the fit set spans both verdict classes -- is arithmetically determined and so
  survives any seed, which is what makes expect="pass" correct here rather than
  vacuous. The production change that WOULD make it fail is re-adding a
  line-to-line fit such as H7/h6 to SUPPORTED_FITS, which is exactly the change
  Phase 3.5a made and reverted. So it can fail, for a plausible reason.
SI-1: minor (deferred): _count_and_apply normalises CRLF->LF across the WHOLE file,
  not just around the anchor. Harmless for Python targets, but a future non-Python
  text target that is line-ending sensitive could fail for the wrong reason and be
  misread as the guard reacting.
SI-1: minor (deferred): restoration is exception-safe but not crash-safe -- SIGKILL
  mid-write would leave a mutated file. Compensated by the git status check.
SI-1: minor (deferred): nothing enforces function-level test selectors; the two
  runner-guard fixtures use whole-file selectors, safe only because they
  short-circuit at the occurrence check.

SI-2: complete (commit 2e2cabc, review APPROVED). 296 passed (+10), +8.35s. Gate A
  exit 1. Ladder unchanged. Tree clean. All 9 entries behaved as declared.
SI-2: the reviewer independently re-verified EVERY anchor against the live tree
  rather than trusting the report -- fixture bytes and SHA, _CLEARANCE_HOLE_MM,
  _TOL_FRACTION_RANGE, _FASTENER_UPPER_DEV_MM -- and confirmed all eight
  expect="fail" entries break the correct guard FOR THE CORRECT REASON, with no
  "breaks by import error" or "breaks by unrelated assertion" cases. It also
  confirmed HEADER;\r\n occurs exactly once while ISO-10303-21; occurs twice,
  and that the m12 mutation crosses the ISO 286 band boundary as intended (a
  WITHIN-band typo would NOT be caught -- that is the diameter pin's job).

SI-2: *** CONTROLLER'S OWN ERROR, FOUND BY THE REVIEWER. *** The design spec's
  Layer 3 seed table (section 4) lists a NINTH kind of entry --
  "reliability measurement | perturb by a realistic amount | Gate A's reliability
  criterion" -- and section 8 claims Layer 3 catches "reliability range" and
  "Gate A headroom" as distinct instances. NO SUCH ENTRY EXISTS IN THE REGISTRY.
  When writing the plan I substituted "stale-literal-wall-floor" for it and did
  not notice the swap, so the registry has 9 entries but not the 9 the spec named.
  CONSEQUENCE: instances 2 (reliability metric mathematically incapable of
  returning below 1.0) and 4 (Gate A measurement with 1000x headroom) are
  currently covered by NOTHING. SI-5's instance map is about to assert all eleven
  are caught, so this would either fail that test or invite fudging the map.
  Must be closed before SI-5.

SI-2: IMPORTANT (plan-mandated, carried forward): mc-seed-base-shifted is a narrow
  TRIPWIRE, not a general closure of the seed-fishing class. Reviewer confirmed the
  controller's pre-analysis independently: the mutation is load-bearing (margins
  move) but the guarded booleans are seed-invariant BY CONSTRUCTION for the current
  SUPPORTED_FITS, because test_iso_fit_verdict_is_fixed_by_the_shaft_letter
  documents assembles == (es <= 0). It fires only if a line-to-line fit such as
  H7/h6 re-enters SUPPORTED_FITS -- the exact Phase 3.5a reintroduction path. The
  why= text overstates this as making the control "honest" against seed choice in
  general. Fix the wording; optionally add a companion entry on a currently
  seed-SENSITIVE quantity.
SI-2: IMPORTANT (acknowledged design limitation): the registry-covers test can be
  defeated by ONE joint commit that deletes an entry and its name from
  _CRITICAL_GUARDS together. Paper-trail mechanism, not a technical one. Matches
  design section 9's open question but should be stated plainly, not left for a
  future reviewer to rediscover.

SI-3: complete (commit 3f26dc8), but shipped a defective floor -- see the fix
  round below.

FIX ROUND (28a478b..0b6e878, on top of 3f26dc8). 305 passed (+5). Gate A exit 1,
  6 PASS / 3 SKIP. Ladder unchanged: d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%
  over seeds 0-199. Tree clean. Report: fix-round-report.md.

F-1 CLOSED. COVERAGE_FLOOR 48.0 -> 91.64, and the SCOPE changed, which is the
  actual fix. --cov=src/tolcad included src/tolcad/gen/ (~222 stmts) that the
  core subset never exercises by design, so 48% was mostly measuring an intended
  permanent exclusion and core coverage could halve without tripping it. gen/ is
  now omitted via [tool.coverage.run] in pyproject.toml with the reason recorded
  there; [tool.coverage.report] precision = 2 keeps the pin a measurement.
  Deleting the omit is not silent: the number falls to ~48% and the gate fails.
  THE IRONY, RECORDED: the layer built to catch metrics that cannot fail shipped
  one of its own, and it took an external review to see it.

F-2 CLOSED, BOTH INSTANCES. Two entries, neither subsuming the other:
  * reliability-perturbation-neutered -- instance 2. _PERTURBABLE -> (), so
    verdict_stability is structurally incapable of returning below 1.0 while
    still reporting tested=100. test_positive_control_detects_instability fails
    ("expected stability < 1.0 but got 1.0 (tested=100)"). Gate A does NOT
    notice this one: it reads 1.0000 and passes.
  * reliability-perturbation-tripled -- instance 4. 3x perturbation with the
    exclusion band left at epsilon: mean over the 200 pre-registered seeds goes
    0.9982 -> 0.9068, below the 0.95 threshold. Caught by the new
    test_gate_a_reliability_criterion_holds_for_the_real_measurement. The unit
    positive control does NOT notice this one (value is still < 1.0).
  MEASURED HEADROOM, for SI-5's map and for anyone re-tuning the mate set:
  k=1 0.9982 PASS, k=2 0.9518 PASS (NOT caught, 0.0018 of margin), k=3 0.9068
  FAIL. So the criterion's sensitivity is roughly 2-3x, not 1000x and not
  infinite. Re-measure if _RELIABILITY_MATES or _RELIABILITY_EPSILON changes.
  Registry is now 11 entries; _CRITICAL_GUARDS is 11.

F-3 CLOSED. mc-seed-base-shifted's why= now states its real scope: a narrow
  tripwire for a line-to-line fit re-entering SUPPORTED_FITS, not a general
  seed-robustness check. Entry kept.

F-4 CLOSED. The paper-trail limit of test_the_registry_still_covers_every_
  critical_guard is now in its docstring, along with the related gap that
  nothing forces a NEW guard to be registered.

FIX ROUND, NEW FINDING (fixed in the same round): running two entries that
  target the SAME file back to back raised OSError [Errno 22] on the RESTORE
  write and left src/tolcad/reliability.py MUTATED in the working tree. Once in
  roughly a dozen runs on Windows; likely the scanner or write-back holding the
  file just written. The design's "restore mismatch must be loud" was satisfied
  in letter but the operator saw a pathlib traceback, not the named-file
  message. The write is now retried with backoff, and a persistent failure
  raises a loud AssertionError naming the file and the git command, from the
  finally block so it masks any in-flight error. Two new tests cover both
  paths. This upgrades but does not eliminate SI-1's "not crash-safe" note.

FIX ROUND, STILL OPEN (for SI-4/SI-5 to consider, NOT fixed here):
  * Nothing at Gate A level notices a VACUOUS reliability 1.0 obtained by
    excluding every mate -- gate_a.py prints tested= but no gate row asserts it.
    The new test_gate_a_... guard asserts tested > 0, so the test layer covers
    it; the gate script itself still does not.
  * Design spec section 4's seed table and section 8's distribution now
    understate the registry: 11 entries, not 9. SI-5 should reconcile the map
    against the registry rather than against the table.

SI-3 + FIX ROUND: reviewed together (the controller found SI-3's central defect
  itself and folded it into the fix round rather than review-then-fix; the
  deviation is recorded here deliberately). Commits 28a478b..0b6e878.
  VERDICT: APPROVED, all four findings ADDRESSED. 305 passed. Coverage floor
  re-pinned 48.0 -> 91.64 with gen/ omitted. Registry grew 9 -> 11 entries.
  The reviewer verified the complementarity claim by RUNNING both new entries,
  not by accepting the report: neutered-perturbation is caught by the unit
  control but NOT Gate A; tripled-perturbation is caught by Gate A but NOT the
  unit control. Genuinely non-redundant.
SI-3/fix: IMPORTANT residual -- run_declared_mutation's OSError -> AssertionError
  conversion is UNTESTED. Only the lower-level _write_bytes_resiliently retry has
  coverage. An untested error branch inside the module built to catch untested
  branches. Carry to the final review.
SI-3/fix: IMPORTANT residual -- the Gate A reliability guard has measured 2-3x
  headroom, not eliminated headroom. k=2 gives 0.9518 and is NOT caught (0.0018
  of margin); k=3 gives 0.9068 and is. Reviewer's phrasing, which is the honest
  one: "headroom reduced from absurd to modest", not "excessive headroom
  eliminated". Instance 4 is improved, not fully closed. SI-5's instance map must
  say that rather than claiming a clean catch.
SI-3/fix: minor -- if the MUTATE write (not the restore write) exhausts retries,
  the operator gets a bare OSError without the friendly recovery message.
  Asymmetric and untested.

*** CONTROLLER PROCESS FAILURES THIS ROUND, recorded so they are not repeated ***
  1. MISROUTED RESUME. The SI-4 implementer (aa7ec0c0) paused; the controller sent
     the resume to the SI-3 REVIEWER (ae046d91) instead. The reviewer correctly
     refused to act on work outside its assignment and flagged the misroute rather
     than complying. That refusal is the only reason it was caught.
  2. CONCURRENT COSMIC-RAY IN A SHARED WORKING TREE. The controller dispatched a
     reviewer alongside SI-4's cosmic-ray run. cosmic-ray mutates files IN PLACE,
     so the reviewer saw shifting diffs, hit a spurious test failure, and observed
     src/tolcad/y14_5.py holding a live mutation. It had the sense to isolate
     itself in a separate git worktree.
     RESOLUTION: the controller waited for the run to exit rather than racing it,
     then verified cosmic-ray HAD restored iso286.py correctly (the in-flight
     mutant was IT7 band 2, 15 -> 14; confirmed back to 0.015). No corruption
     survived. LESSON, now being written into the code itself: Layer 2 must never
     run concurrently with anything else, and a run killed mid-flight can leave a
     checker-core file mutated. SI-4 is adding that warning to cosmic-ray.toml and
     run_mutation_score's docstring.
     A stronger fix -- running Layer 2 against an isolated copy or worktree -- is
     NOT being done now; it is a design change and belongs to the final review.

## SI-4 fix round (review of 0b6e878..7b1f807: NEEDS FIXES -> addressed)

SI-4/fix: F-1 RECONCILED FROM THE RUN-2 ARTEFACTS, no new cosmic-ray run.
  The survey WAS complete: the six `surviving mutants:` counts sum to exactly
  275, which is the set that was triaged. The defect was a mislabelled
  denominator -- 1,118 is TOTAL JOBS; viable is 1,118 - 468 INCOMPETENT = 650.
  375/650 = 57.69%, the number run 2 actually printed. "1,118 = 1,586 total jobs
  - 468" in the report was an addition where a subtraction belonged; no
  1,586-job run ever existed. Run 3's 93.85% = 610/650, i.e. 40 survivors.
SI-4/fix: RESIDUAL, CARRIED. 40 run-3 survivors vs 23 documented equivalents
  leaves ~17 UNTRIAGED. Four are now identified and killed; the rest need
  another cosmic-ray run and are recorded as untriaged in three places rather
  than absorbed into the equivalent count. FIRST ITEM for the next round that
  is allowed a run.
SI-4/fix: NINE TRIAGE VERDICTS WERE WRONG, each verified by applying the mutant
  in an isolated copy. Four "equivalent" that are live (three `condition is
  "..."` in y14_5 -- one of which deletes the hole_b clearance guard for every
  mate routed through check() -- plus `condition >= "fixed"`), and five
  "killed" that did not kill. All killed now. Corrected: 256 killed / 19
  equivalent, not 252 / 23.
SI-4/fix: ROOT CAUSE OF FOUR OF THEM -- `"".join(["x"])` DOES NOT DEFEAT
  INTERNING. CPython's str.join returns the single item itself, so the
  "runtime-built string" in test_checker.py and test_montecarlo.py WAS the
  interned literal and those four `is` mutants were never killed. A test that
  could not fail, inside the layer built to catch tests that cannot fail.
  Replaced with a two-piece join that asserts its own postcondition.
SI-4/fix: F-2 WAS LIVE, NOT HYPOTHETICAL. Raw run-3 score 610/650 = 93.8462 is
  BELOW a literal MUTATION_FLOOR = 93.85, so the gate failed deterministically
  on an unchanged tree. Now MUTATION_MEASURED = 93.85, MUTATION_TOLERANCE =
  0.50, MUTATION_FLOOR = 93.35 (derived). timeout untouched -- no evidence the
  30s budget is tight.
SI-4/fix: METHOD NOTE for anyone verifying mutants by hand -- set
  PYTHONDONTWRITEBYTECODE=1 and clear __pycache__. `-` -> `%` preserves file
  size, so a same-second rewrite is served from a stale .pyc and reports a
  FALSE KILL. This bit once during this round before it was caught.
SI-4/fix: verified 376 passed; gate_a exit 1; ladder d1 19.5 / d2 32.9 /
  d3 52.9 / d4 69.1 unchanged. No src/ behaviour changed -- every kill is
  test-side. See task-4-fix-report.md.

SI-4: implemented 7b1f807, review verdict NEEDS FIXES, fixed in 7b1f807..7979396.
  Final: 376 passed. Gate A exit 1. Ladder unchanged. Tree clean. No src/ change --
  every kill is test-side.

SI-4 REVIEW found two Criticals, both CONTROLLER-CONFIRMED:
  C1 the survivor arithmetic did not close. 275 of 1118 is 75.4% killed, not the
     57.69% reported. RESOLVED BY THE FIX ROUND, and the reviewer's inference was
     half right: the SURVEY WAS COMPLETE, but the DENOMINATOR WAS MISLABELLED.
     1,118 is total JOBS; viable is 650 after 468 INCOMPETENT. 375/650 = 57.6923%
     exactly. No survivors were unsurveyed. BUT run 3's 93.85% = 610/650 = 40
     survivors against 23 documented, so ~17 were neither killed nor documented;
     4 are now killed and ~12 remain, recorded as UNTRIAGED in three places rather
     than absorbed.
  C2 MUTATION_FLOOR compared a RAW float against its own 2-decimal display
     rounding. NOT hypothetical -- controller confirmed raw 610/650 = 93.846154 is
     BELOW a literal 93.85, so the gate was ALREADY failing deterministically on an
     unchanged tree. It would have cried wolf on first use, which is how gates get
     disabled -- the exact failure mode this branch exists to prevent.
     Fixed with MUTATION_MEASURED 93.85 / MUTATION_TOLERANCE 0.50 / FLOOR 93.35.
     timeout left alone: the reviewer timed the test-command at 0.15s against a 30s
     budget, so there is no evidence of timeout pressure.

SI-4 fix round: NINE TRIAGE VERDICTS WERE WRONG, each verified by applying the
  mutant -- 4 "equivalent" that were live survivors, 5 "killed" that did not kill.
  Corrected 252/23 -> 256 killed / 19 equivalent. Two of the live ones were
  safety-relevant: `condition is "fixed"` raises TypeError through check(), and
  `condition is "floating"` silently DELETES the hole_b clearance guard that
  y14_5.py:154-162 exists to enforce.

*** THE BEST CATCH OF THE BRANCH, found by the fix agent unprompted ***
  `"".join(["x"]) is "x"` returns True -- CPython's str.join returns the single
  item itself. So the "runtime-built" strings used to defeat interning WERE the
  interned literals, and four `is` mutants recorded as killed were never killed.
  Four tests that could not fail, inside the layer built to catch tests that
  cannot fail. Replaced with a two-piece join that asserts its own postcondition.
  METHOD NOTE worth keeping: set PYTHONDONTWRITEBYTECODE=1 when hand-verifying
  mutants. `-` -> `%` preserves file size, so a same-second rewrite is served from
  a stale .pyc; that produced one false "killed" before it was caught.

CARRIED TO THE FINAL REVIEW:
  * ~12 run-3 survivors remain UNTRIAGED. The one thing the fix round could not
    close. First item for the next round permitted a cosmic-ray run.
  * Nothing systematically prevents another false kill. Proposed cheap mitigation:
    after triage, re-run Layer 2 and require the survivor set to have ACTUALLY
    shrunk by the claimed amount.
  * run_declared_mutation's OSError -> AssertionError branch is still untested.
  * Instance 4 is IMPROVED, NOT CLOSED -- 2-3x headroom, not eliminated. SI-5's
    instance map must say that rather than claim a clean catch.
  * _uninterned is duplicated across three test files and must not drift.

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
