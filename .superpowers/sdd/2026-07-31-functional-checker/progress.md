# SDD ledger — plan: docs/superpowers/plans/2026-07-31-functional-checker.md

Branch: feat/functional-checker
Base: 03063d3

Known-intentional plan choices (pre-flight scan, adjudicate fast if a reviewer raises them):
- Task 6 ships an xfail test (strict=False) that stays red until the ISO 286 transcription source is recorded. Deliberate: it is the gate that proves the tables were verified against print. It does assert.
- Task 9 second test is expected red until Task 10 creates tolcad.checker. Documented in the plan.

Task 1: complete (commits 03063d3..0aebabb, review clean)
Task 1: minor (deferred): pytest "slow" marker not registered in pyproject — Task 8 registers it by design, no action needed
Task 2: complete (commits 0aebabb..e4e735a, review clean)
Task 2: minor (deferred): no negative-path tests for FeatureOfSize.__post_init__ ValueError branches
Task 3: complete (commits e4e735a..d292eef, review clean)
Task 3: minor (deferred): no test for position_tol exceeding MMC (behaviour correct, just unverified)
Task 4: fix round 1/5 (2 addressed, 0 open; commits 50a833b..99c6a99)
Task 4: complete (commits d292eef..99c6a99, review clean)
Task 4: minor (deferred): hole_b type check runs before condition validity check, so a bad condition string reports the hole_b error first
Task 4: ACTION FOR HUMAN: y14_5.py carries "CITATION PENDING HUMAN VERIFICATION" for both fastener formulas. Domain expert must verify against ASME Y14.5 before any derived number enters the paper.
Task 5: complete (commits 99c6a99..786fff4, review clean)
Task 5: minor (deferred): new tests redefine FeatureOfSize inline instead of reusing M8_BOLT/CLEARANCE_HOLE constants
Task 5: minor (deferred): task-5-report claims constants were reused; they were not (report inaccuracy, no functional impact)
Note: plan Task 5 step 4 says "18 tests"; actual is 20. Plan text error, harmless.
Task 6: fix round 1/5 (2 addressed, 0 open; commits 43801cc..ea9f878)
Task 6: complete (commits 786fff4..ea9f878, review clean)
Task 6: ACTION FOR HUMAN: iso286.py TRANSCRIPTION SOURCE placeholder unfilled; test_transcription_source_recorded stays xfail until a real ISO 286-1 edition+table is recorded. No derived number may enter the paper until it flips.
Task 6: minor (deferred): _SHAFT_LETTER_GRADE_RANGE covers only k; adding f/e/d later needs both classification sets AND the grade-range map updated
Task 7: complete (commits ea9f878..3bdb544, review clean)
Task 7: minor (deferred): types.py Verdict.margin docstring says "in mm of slack"; Tier 2 overloads it as yield in [0,1]. Documented locally in montecarlo.py but not cross-referenced in types.py.
Task 8: complete (commits 3bdb544..e1c31cd, review clean, zero findings)
Task 8: EVIDENCE for spec correction 2026-07-31a: measured 5-seed spread on H7/k6 uniform is 0.04700 at N=1k, 0.01320 at N=10k, 0.00337 at N=100k (threshold 0.005). Confirms the N=10k->100k pre-data correction was necessary and correctly sized.
Task 9: fix round 1/5 (3 addressed, 0 open; commits 784c0d0..e4011a0)
Task 9: complete (commits e1c31cd..e4011a0, review clean)
Task 9: minor (deferred): lint misses "from importlib import import_module; import_module(...)" bare-name form, and __import__ aliased via builtins
Task 9: minor (deferred): expected-core-module-name list in test_architecture is hardcoded; needs updating when core modules are added/renamed
Task 10: complete (commits e4011a0..c073df9, review clean). Full suite now 56 passed, 1 xfailed, 0 failed.
Task 10: minor (deferred, FLAG TO FINAL REVIEW): check() defaults n=10_000 for iso_fit, but Gate A stability needs N=100_000. No test is compromised (test_convergence hardcodes 100k), but a Phase 3/4 caller relying on the default would silently get a non-Gate-A-stable yield. Needs a docstring caveat at minimum.
Task 10: minor (deferred): missing nested keys raise raw KeyError rather than the friendlier ValueError used for the top-level type check
Task 11: complete (commits c073df9..2eb8032, review clean). Gate A runs: 3 PASS, 1 SKIP, NOT CLEARED, exit 1 -- the intended end state.
Task 11: minor (deferred): gate_a.py header prints an em dash; under PYTHONIOENCODING=cp1252 it would raise UnicodeEncodeError before the verdict line. verify_literature.py already has an _ascii() helper convention it does not follow. Task 14 rewrites main() with a plain hyphen, which should resolve it -- confirm at Task 14 review.
Task 12: fix round 1/5 (2 addressed, 0 open; commits fd3e4f3..8524206)
Task 12: complete (commits 2eb8032..8524206, review clean). Full suite 65 passed, 1 xfailed.
Task 12: NOTE: pyproject pythonpath now ["src","."]. Necessary (validation/ is outside the installed package) but it removed the runtime ModuleNotFoundError backstop. AST lint is now SOLE enforcement of core-vs-validation isolation; hardened against exec/eval and documented in pyproject.
Task 12: minor (deferred): test docstrings tagged "Finding CORS" instead of the Finding 1/2/3 convention -- cosmetic garble
Task 12: minor (deferred): exec(f"import {x}") f-string form not flagged (correct per string-literals-only spec, but undocumented)
Task 13: fix round 1/5 (4 findings: vacuous metric, no positive control, aliasing, empty-denominator; commits 66b29ba..365a01f)
Task 13: fix round 2/5 (3 findings: seed-fished positive control, false 20-30% docstring claim, undocumented sensitivity limit; commits 365a01f..280072a)
Task 13: complete (commits 8524206..280072a, all 7 addressed, review clean). Full suite 72 passed, 1 xfailed.
Task 13: KEY LESSON: the original metric could never return <1.0 (band 10*eps > max achievable delta 8*eps). Plan design error. Positive control now detects on 60/60 seeds, values [0.890,0.990].
Task 13: LIMITATION FOR THE PAPER: reliability metric only detects instability for margins within ~2-3*epsilon of zero. A 1.0 means "no instability detected within the tested band", NOT "checker proven reliable". Documented in module docstring.
Task 13: minor (deferred): test_aliasing_is_handled_correctly is documentation-only and would pass with the aliasing bug reinstated; fix is verified correct by inspection instead
Task 14: complete (commits 280072a..3dfc69d, review clean). Full suite 74 passed, 1 xfailed. Gate A: 4 PASS, 2 SKIP, NOT CLEARED, exit 1.
Task 14: minor (deferred): unused "threshold" unpacked in the oracle loop -- latent trap for whoever wires Phase 3
Task 14: minor (deferred): unhandled exception in _pytest_passes would traceback rather than record a graceful FAIL row
ALL 14 TASKS COMPLETE.

=== FINAL WHOLE-BRANCH REVIEW (opus) ===
BLOCKING: 4 Critical + 2 Important. Verified independently by controller:
  C1 fastener_assembles ignores hole_b MMC -> same joint, opposite verdicts by arg order, falsely optimistic. CONFIRMED.
  C2 _perturb is a provable no-op on iso_fit mates (no sub-dicts) -> reliability vacuous for all of Tier 2. CONFIRMED.
  C3 Gate A prints "Checker reliability PASS >=0.95" but nothing ever measures 0.95.
  C4 "Y14.5 worked examples" row is circular; gate never runs test_iso286.py so the transcription guard is outside the gate.
  I5 Gate A has no achievable pass state; AGREEMENT_THRESHOLD unreferenced.
  I6 spec 7 criterion 7 (fresh clone) has no row.
Triage: 7 deferred minors escalated to FIX BEFORE MERGE (L22,L29,L34,L37,L44,L51,L53).
Dispatching ONE consolidated fix wave.

=== FIX WAVE RE-REVIEW (opus) — 2 LOAD-BEARING RESIDUALS, BRANCH BLOCKED ===
Fix wave 4441bbe addressed C1-C4, I5, I6 and all escalated minors. Re-review found
TWO new High findings introduced BY the fix wave. Both confirmed independently.

NB-1 (High, correctness) BLOCKED: the C1 fix instruction (use min(hole_a.mmc, hole_b.mmc))
  was WRONG. Controller error, not implementer error.
  - FIXED fastener: min() always selects the tapped hole, whose MMC is physically
    meaningless. Verified: Ø8.5 clearance + M8 tapped, tol 0.1 -> code says assembles=False
    margin -0.100; Y14.5 says T=(8.5-8.0)/2=0.25, margin +0.15, ASSEMBLES.
  - FLOATING fastener: min(H) - max(T) cross-pairs the smallest hole with the largest
    tolerance across DIFFERENT parts. Verified: A(8.5,tol .5) + B(8.05,tol .02), each within
    its own budget -> code says False margin -0.450; correct answer ASSEMBLES.
  Both errors are falsely PESSIMISTIC (the original bug was falsely optimistic).
  CORRECT MODEL: floating -> margin = min(H_a - F - T_a, H_b - F - T_b), per part.
                 fixed    -> allowable from the CLEARANCE hole only.
  Existing tests cannot catch it: every fixed-fastener test passes the same hole twice.

NB-2 (High, instrument honesty) BLOCKED: the new gate_a.py reliability measurement is
  unfalsifiable. _RELIABILITY_MATES have |margin| 0.10+ while max |delta margin| is ~5e-4,
  i.e. 206x-1163x headroom. Min over 300 seeds = 1.0000 and no seed can produce otherwise.
  This is the FOURTH instance of the "metric that cannot fail" pattern on this branch
  (Task 4 tautological test, Task 13 vacuous metric, Task 13 seed-fished positive control,
  now this). Fix: include mates with |margin| in the 2-5*epsilon sensitive band, or report
  the tested band alongside the value.

NB-3 (Low, deferred): gate_a.py calls verdict_stability unguarded at top level; a raise
  aborts the gate with a traceback instead of recording FAIL.

I5 PARTIAL (deferred, correct for now): oracle wiring is real and thresholds are referenced,
  but `ours` is hardcoded {} so the pass path is unreachable until Phase 3. Expected.

STATUS: BRANCH BLOCKED. No second fix wave dispatched (per skill: one wave, one re-review,
then surface load-bearing residuals to the human). NO NUMBER FROM THIS INSTRUMENT MAY ENTER
THE PAPER until NB-1 and NB-2 are fixed AND the two human citation checks are done.

=== NB-1 / NB-2 FIX + RE-REVIEW (user chose option 1) ===
NB-1 FIXED (f77d200). Correct model, GD&T-verified BEFORE implementation:
  floating: margin = (H_a-F) + (H_b-F) - (T_a+T_b)   [disc-intersection; necessary AND sufficient]
  fixed:    margin = (H_a-F) - (T_a+T_b)              [hole_a = clearance, H_b absent]
  Both reduce to the classic Y14.5 formulas in the symmetric case.
  NOTE: BOTH prior models were wrong. min(mmc) was the controller's error; the final reviewer's
  proposed min(H_i - F - T_i) per-part model was ALSO wrong (too conservative -- it rejects
  joints where the fastener shifts into the other hole's slack, which is what "floating" means).
  Re-review ran a differential test vs an independent reference implementation:
  0 mismatches over 20,000 random draws.
  Also added: H_i < F guard, diametral-margin documentation, condition-dependent feature-type
  validation (fixed permits EXTERNAL hole_b for press-fit pins), projected-tolerance-zone and
  datum-shift scope limits, and the proof that ignoring MMC bonus is EXACT (virtual condition
  H-T is size-invariant, so bonus cancels).
NB-2 FIXED (81f6d90). Reliability mates now include the 2-5*epsilon sensitive band.
  Genuinely falsifiable: 122/1000 seeds fall below 0.95.

OPEN, LOGGED AS SPEC AMENDMENT 2026-08-01e (NOT a code bug):
  The single-seed reliability estimator is unsound -- one Bernoulli draw at ~88% pass
  probability, and at tested=12 the 0.95 threshold is degenerate (only 1.0000 and 0.9167
  reachable). Threshold and mate set stay fixed; the ESTIMATOR must become a multi-seed
  aggregate (seeds 0-199, mean + bootstrap CI + fraction passing) before any reliability
  figure is printed in the paper.

REMAINING BEFORE PUBLICATION: (1) multi-seed reliability estimator per amendment 2026-08-01e;
(2) ASME Y14.5 fastener formulas verified against print by a domain expert;
(3) ISO 286 edition + table number recorded in iso286.py.

FINAL: cleanup 06f6a6b. 94 passed, 1 xfailed. Gate A 4 PASS / 5 SKIP / NOT CLEARED, exit 1.
All thresholds unedited, both citation markers present, no data/ committed, tree clean.
Branch feat/functional-checker is COMPLETE for Phases 0+2. Three items gate publication:
  (1) multi-seed reliability estimator per spec amendment 2026-08-01e
  (2) ASME Y14.5 fastener formulas verified against print
  (3) ISO 286 edition + table number recorded in iso286.py

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
