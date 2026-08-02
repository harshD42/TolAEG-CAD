# SDD ledger — plan: docs/superpowers/plans/2026-08-01-pre-registration-prep.md

Branch: feat/pre-registration-prep
Base: 7ac01ed (master, immediately after the Phase 3 merge 2c8a8f0 + the plan commit)
Prior phase ledger: .superpowers/sdd/2026-08-01-procedural-generator/progress.md

This plan closes the four items the Phase 3 whole-branch review deferred. It is the
LAST thing before Phase 3.5 public pre-registration (design spec section 12), which is
why these land now: they change what gets frozen.

HUMAN DECISIONS already made — do not re-litigate, do not re-ask:
  1. Drop line-to-line fits (H7/h6) from the sampled set.
  2. Always emit projected zones and record the field. STAY INSIDE B-4.
     Explicitly NOT implementing ASME Y14.5 B-5.
  3. Tier 2 contributes the clearance YIELD; Tier 1 carries the boolean. I2 is
     structural, so it gets documented and pinned rather than "fixed".
  4. (from the Phase 3 review) I4 lands before any corpus generation. This is it.

THE I2 FINDING, so no reviewer re-derives it: montecarlo.py:57 defines
  assembles = yield_frac >= 1.0, i.e. zero interference anywhere in the tolerance
  range. For a hole-basis fit that means hole_min > shaft_max. hole_min == nominal
  (H holes have zero lower deviation) and shaft_max == nominal + es, so the verdict
  is True exactly when es <= 0 — the definition of a clearance-class shaft letter
  (a-h) versus transition/interference (j-zc). It is arithmetic, not sampling, and it
  CANNOT vary with diameter. Confirmed empirically over nominals 3-180 mm: g6 True
  everywhere, k6/p6 False everywhere. The continuous yield does vary usefully
  (k6 spans 0.661 at 6 mm to 0.848 at 3 mm).

CONTROLLER-VERIFIED BY EXECUTION before the plan was written (trust these):
  * A fixed mate with hole_a Ø9.0 clearance and hole_b Ø6.8 TAPPED against an M8
    fastener returns assembles=True, margin=0.2. y14_5 does not check hole_b's size
    in the fixed case and its MMC never enters B-4, so a sub-fastener diameter is
    correct there. BONUS INVARIANT: the same dict submitted as floating_fastener
    correctly raises ValueError ("hole_b MMC 6.8 is smaller than fastener MMC 8.0").
    Task 2 pins that — it is what makes the two kinds structurally distinguishable.
  * nist_ctc_01_asme1_ap242-e1.stp is the smallest AP242 file in the NIST suite with
    non-trivial PMI: 396,445 bytes, reads as exactly 21 dimensions / 6 geometric
    tolerances / 11 datums, parses with no OCCT warnings.
  * Baseline at 7ac01ed: 188 passed, 2 deselected. Gate A exit 1, 6 PASS / 3 SKIP.
  * Tier 1 failure rate by difficulty, seeds 0-199: d1 19.5%, d2 32.9%, d3 52.9%,
    d4 69.1%. Tasks 1 and 2 both require re-measuring this and reporting it.

PRE-FLIGHT SCAN (clean; these are known-intentional, adjudicate fast if raised):
  - Task 1 Step 2: three of the four new tests PASS on arrival. They are regression
    pins documenting existing behaviour, labelled as such, with an explicit stop
    condition if the structural-fact test fails. Not a TDD violation.
  - Task 5 has no implementation step: the constants are already correct, the test is
    what was missing. Red is demonstrated by a deliberate mutation, not by absence.
  - Task 3 will break existing MateSpec(kind="fixed_fastener", ...) fixtures in the
    test suite. The plan says to add projected_zone_mm=8.0 to them and explicitly
    forbids switching them to floating_fastener to dodge the new validation.

P35-1: implemented (commit 422c21f). Step 2 gave the expected 1 FAIL (the
  line-to-line test, naming H7/h6) + 3 PASS regression pins. The hard-stop test
  (verdict fixed by shaft letter at every size) PASSED, so the structural argument
  holds and no block was triggered. Full suite 190 passed / 2 deselected (188 + 4).
P35-1: measured Tier 1 failure rate seeds 0-199 AFTER the change:
  d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1% -- BIT-IDENTICAL to the reference.
  Both ladder guard tests still pass; no bands widened.
  WHY IDENTICAL (worth remembering): numpy's rng.choice over a tiny array consumes
  the same number of bit-generator words for 3 vs 4 elements, so the shared RNG
  stream for downstream draws is unperturbed -- and Tier 1 verdicts never depended
  on which fit was chosen anyway. Do not assume a choice() tuple resize shifts the
  corpus; measure it.
P35-1: review dispatched.

P35-1: complete (commits 7ac01ed..422c21f, review clean / approved).
  Reviewer independently re-ran the grep and verified each of the four new tests
  against real production fields rather than taking the report's word: confirmed
  Verdict.assembles is a real bool off `yield_frac >= 1.0` (so the len(seen)==1
  assertion is falsifiable, not vacuous), and FeatureOfSize.min_size/max_size are
  computed properties. Also confirmed the SUPPORTED_FITS audit-trail comment is
  accurate and specific -- it is the paper's record of why an item left the
  benchmark, so vagueness there would have been a real defect.
P35-1: minor (deferred): the implementer's report enumerated the `h6` grep hits
  incompletely -- it missed src/tolcad/gen/spec.py:31, a comment in MateSpec's
  docstring citing H7/h6 as the motivating example for explicit mc_seed. Reviewer
  verified it is benign (a general statement about line-to-line fits, and
  iso286.fit_from_designation still supports the designation), so nothing is
  stranded. Optional follow-up: note there that h6 is no longer SAMPLED, only
  supported. Surface to the final review.

P35-2: implemented (commit ae63279). RED gave 12 failures (ImportError on the
  features side, assertion/no-raise on the sampler side), then GREEN. Suite 202
  passed / 2 deselected (190 + 12). Both knock-on effects confirmed: the 50-seed
  containment sweep in test_build.py still passes with the smaller tapped diameter
  flowing through, and no plate-size assertion regressed.
P35-2: Tier 1 failure-rate table UNCHANGED (19.5/32.9/52.9/69.1), as predicted --
  hole_b's size enters neither B-3 nor B-4.
P35-2: CONTROLLER-VERIFIED INDEPENDENTLY over seeds 0-39 x d1-4: 165 fixed mates
  all carry a tapped hole_b smaller than their fastener; 142 floating mates all
  carry a clearance hole_b larger than theirs; and a sampled fixed mate's dict
  submitted as floating_fastener correctly raises. I4's geometry half is closed.
  Example: M3 -> hole_a Ø3.4 clearance, hole_b Ø2.5 tapped.
P35-2: review dispatched, with a specific instruction to check that the allowable
  is still derived from hole_a (the clearance hole) and not from the new tapped
  hole_b -- deriving it from Ø6.8 instead of Ø9.0 would go negative and silently
  corrupt every fixed-fastener label.

P35-2: complete (commits 422c21f..ae63279, review clean / approved, ZERO issues at
  any severity). The reviewer traced each concern through production rather than
  trusting the report:
  * The allowable-arithmetic trap is CLEAR: sampler still derives it from `hole`
    (the clearance hole). Had it used tapped_hole_for, M8 would give 6.8-8.0 = -1.2.
  * test_tapped_hole_is_always_smaller_than_its_fastener compares hole LMC against
    the fastener, which is STRICTLY STRONGER than the MMC-vs-MMC condition
    y14_5:215-219 actually enforces -- conservative in the safe direction.
  * The "hole_b MMC" regex is unambiguous: checker.py forces both holes INTERNAL so
    the feature-type branch cannot fire, and hole_a is unmodified, so exactly one
    raise path is reachable and that substring appears nowhere else in y14_5.
  * Tapping values cross-checked against the coarse-pitch series (nominal minus
    pitch); M8/M12 use the conventionally rounded 6.8/10.2 rather than 6.75/10.25.
    Provenance caveat is honest and matches the _CLEARANCE_HOLE_MM convention.
  * y14_5.py, build.py and layout.py confirmed absent from the diff.

P35-3: implemented (commit 164e83a). RED then GREEN. Suite 208 passed / 2 deselected
  (202 + 6). Gate A exit 1, 6 PASS / 3 SKIP. Failure-rate table unchanged.
  Two existing fixtures in test_spec.py needed projected_zone_mm=8.0; neither was
  switched to floating_fastener to dodge the validation. One of them ("rejects
  missing hole_a") would have passed either way because a different ValueError
  fires first -- noted, harmless.
P35-3: CONTROLLER-VERIFIED INDEPENDENTLY: projected_zone_mm IS in the sidecar JSON,
  is ABSENT from to_check_dict() (B-4 has no P term, so emitting it would imply the
  checker consumes it), equals plate_thickness_mm 8.0 for fixed mates, and is None
  for all 235 sampled non-fixed mates. y14_5.py untouched; B-5 not implemented.
P35-3: review dispatched with a specific instruction to check the __post_init__
  rewrite dropped no pre-existing validation branch -- the brief had the implementer
  replace the whole body after the mc_n check, and a silently deleted kind-check
  would be a Critical regression the new tests could not see.

P35-3: complete (commits ae63279..164e83a, review clean / approved).
  * THE FLAGGED CRITICAL RISK IS CLEAR: the __post_init__ rewrite is a strict
    SUPERSET of the prior body -- mc_n, kind-validity, iso_fit, virtual_condition
    and the floating/fixed fastener/hole_a/hole_b checks all still present, same
    order, verbatim. Nothing dropped.
  * Checker isolation verified from source, not from the diff's context: all three
    to_check_dict() branches are explicit dict literals with no asdict()/__dict__
    spread, so the field cannot leak into the checker payload by construction.
    AssemblySpec.to_json DOES use asdict, which is the sidecar path where it belongs.
  * Reviewer grepped independently: sampler.py:132 is the ONLY AssemblySpec(
    construction in src/, so no other caller was left on the coincidentally
    identical 8.0 default. And the two updated fixtures are the only pre-existing
    fixed_fastener constructions in the repo -- the audit was complete.
P35-3: minor (deferred, plan-mandated): validation-order asymmetry. The
  "non-fixed must not carry a zone" guard fires BEFORE the per-kind structural
  checks, while the "fixed must have a positive zone" guard fires AFTER them. So a
  mate wrong in two ways reports different classes of error depending on direction.
  Cosmetic; error-message clarity only.
P35-3: minor (deferred): test_every_sampled_fixed_fastener_records_its_projected_zone
  compares against spec.plate_thickness_mm rather than _PLATE_THICKNESS_MM, so today
  its bite is "the wiring exists" rather than "the values cannot diverge" -- both
  sides currently trace to the same symbol.

P35-4: implemented in TWO commits (d312ad6 then 7ba4e87). Suite 210 passed /
  2 deselected. Simulated fresh clone (data/nist_pmi moved aside): the FIXTURE test
  PASSED while the 47/27/59 and disagreement tests SKIPPED -> 2 passed / 2 skipped.
  Fetched suite restored (34 entries) and all 4 re-confirmed.
P35-4: *** THE IMPLEMENTER CAUGHT A REAL DEFECT NOT IN THE BRIEF. *** This repo has
  core.autocrlf=true, which SILENTLY normalised the binary .stp fixture's CRLF to LF
  on commit -- storing a 391,739-byte blob where the provenance note claims 396,445
  byte-identical bytes. Invisible locally because checkout re-expands LF->CRLF; a
  clone with a different autocrlf would have got a mangled fixture, defeating the
  entire point of committing it. Fixed in the second commit by adding .gitattributes
  with `*.stp binary` and renormalising.
  CONTROLLER-VERIFIED: committed blob SHA-256 now matches the original NIST file
  exactly (85a5752d...), and git cat-file -s reports 396445. Fix confirmed good.
  Two commits kept rather than squashed -- the history honestly records the defect
  and its fix, which is worth more here than a tidy single commit.
  LESSON FOR THE PROJECT: any future committed binary fixture needs a .gitattributes
  rule, and "it looks right in my working tree" is not evidence about the blob.

P35-4: complete (commits 164e83a..7ba4e87, review clean / approved). The reviewer
  judged the out-of-brief .gitattributes JUSTIFIED, not scope creep: the brief's own
  acceptance criterion is a 396,445-byte byte-identical fixture, which the first
  commit silently violated. It also checked the glob's blast radius directly:
  export.py writes `.step`, not `.stp`, so the generator is unaffected; no other
  .stp/.step file is tracked repo-wide; and a sweep for other tracked binary
  extensions (png/jpg/pdf/zip/xlsx) found none, so no pre-existing file was
  corrupted by the same defect and the fix needs to reach no further. A global
  `*.stp binary` is correct here because byte-exactness is inherent to the file
  type, not to this one path.
P35-4: minor (deferred): test_the_fixture_and_the_fetched_suite_disagree_about_counts
  adds little over the two unconditional exact-count tests, and never runs on the
  fresh clone this task exists to protect. Plan-mandated; the brief oversold it as
  "the stronger check". Harmless.
P35-4: minor (historical, not live): the intermediate commit d312ad6 contains the
  391,739-byte CRLF-stripped blob. Only the tip 7ba4e87 has the correct bytes.
  Anyone bisecting to d312ad6 specifically would get the wrong fixture. Not worth
  unwinding; no clone lands on it.
P35-4: minor (deferred): FIXTURE is declared mid-file rather than beside NIST_DIR /
  FTC06 at the top. Exactly as the brief's append text specified. Cosmetic.

P35-5: complete (commits 7ba4e87..5d04d6f, review clean / approved). No production
  code; one test file, 27 insertions.
  MUTATION CONTRAST (the whole justification, shown in ONE run): with
  _MIN_WALL_MM = 0.0, the new test FAILED (assert 0.0 >= 3.7) while BOTH pre-existing
  margin tests PASSED. layout.py confirmed byte-identical afterwards.
  The reviewer proved MECHANICALLY why the old tests were blind: feature_pitch_mm
  returns widest_pair + _MIN_WALL_MM, and the old test asserts
  pitch - (a+b) >= _MIN_WALL_MM - 1e-9, which reduces to
  _MIN_WALL_MM >= _MIN_WALL_MM - 1e-9 -- a tautology true for ANY value including 0.
  Same structure for the edge-margin test. Not merely plausible; exact.
  It also independently re-derived the 3.7 / 1.85 floors against the POST-Task-1-2
  tables: widest clearance hole is still Ø14.5 (Task 2's tapping drills top out at
  10.2 and feature_radii_mm takes max(hole_a, hole_b), so they never bind), and
  _TOL_FRACTION_RANGE[4] is still (0.72, 1.34) -- untouched by Tasks 1-3.
  Nice catch it volunteered: iso_fit mates reach Ø25, larger than Ø14.5, but they
  carry position_tol 0.0 and a much tighter IT band, so the M12-loose clearance hole
  remains the binding case for margin sizing.
  NOT circular: the test reads the constants (unavoidable) but compares them to
  literals derived from external tolerance-stack physics, not to expressions built
  from the constants themselves. That is exactly the distinction the defect turned on.
P35-5: minor (deferred): 3.7 / 1.85 are hardcoded rather than re-derived from
  FASTENER_SIZES / _CLEARANCE_HOLE_MM / _TOL_FRACTION_RANGE at test time, so widening
  the clearance table or raising the d4 ceiling would leave a stale floor passing
  until a human re-checks. Explicitly what the brief asked for; residual maintenance
  dependency, not a defect.

=== ALL FIVE PLAN TASKS COMPLETE, every per-task review clean, zero fix rounds ===
Branch 7ac01ed..5d04d6f, 6 commits. Suite 213 passed (incl. slow). Gate A exit 1,
6 PASS / 3 SKIP. Working tree clean.
NEXT: whole-branch final review dispatched (opus), merge base 7ac01ed.

=== FINAL FIX WAVE (whole-branch review of 5d04d6f) — COMPLETE ===
Commits 5d04d6f..cb48af4, 5 commits. Full report:
  .superpowers/sdd/2026-08-01-pre-registration-prep/final-fix-wave-report.md
All seven items closed in one wave: I-1, I-2, M-1, M-2, M-4, M-5, P35-1.
Suite 220 passed (incl. slow; 213 + 7). Gate A exit 1, 6 PASS / 3 SKIP.
Tier 1 failure rate seeds 0-199 BIT-IDENTICAL: d1 19.5 / d2 32.9 / d3 52.9 /
d4 69.1. Corpus sidecar digest f88582e12117a947 confirms the RNG stream was
not perturbed by naming _ISO_FIT_NOMINALS_MM. No checker-core module touched.
NOTE for the record: the M-1 finding said a 1.7 d4 ceiling leaves "every test
in the repo still passing". It does not — test_sampler.py:87 pins the d4
failure rate to [0.60, 0.80] and also fires. That guard is about label
balance, not geometry, so it would miss a widened _CLEARANCE_HOLE_MM; the
finding's conclusion holds, its "every test" clause did not.

=== FINAL WHOLE-BRANCH REVIEW (opus) + FIX WAVE + SCOPED RE-REVIEW ===
Final review verdict: sound engineering, all four benchmark-integrity gaps genuinely
closed, but NOT ready to merge on two Important items -- both about what gets FROZEN
rather than what was wrong, and both far cheaper before pre-registration than after.

I-1 [CONTROLLER-REPRODUCED] The committed NIST fixture's "unmodified / 396,445 bytes"
  provenance claim was protected by NOTHING THAT COULD FAIL. Controller ran the oracle
  on a CRLF->LF-mangled copy:
      original  396445 bytes -> PmiCounts(21, 6, 11)
      CRLF->LF  391739 bytes -> PmiCounts(21, 6, 11)
  The positive control added in P35-4 PASSED against the exact corruption this branch
  had already suffered once in d312ad6. Instance NINE of the project's signature
  failure mode -- sitting inside the test written to be a positive control.
  Only .gitattributes defended the claim, and it is last-match-wins: appending
  `* text=auto` silently re-arms the bug with a green suite.
I-2 [CONTROLLER-REPRODUCED] AssemblySpec accepted, and round-tripped, a
  fixed_fastener with projected_zone_mm=8.0 inside a plate_thickness_mm=25.0
  assembly -- publishing a sidecar claiming a projected zone SHORTER than the part
  the fastener crosses, which is precisely the under-projected condition
  y14_5.py:80-81 calls OPTIMISTIC/unsafe. MateSpec enforced its intra-object
  invariants; the cross-object one carrying the safety meaning was enforced only by
  a test over the sampler's output. The schema is what gets frozen.

FIX WAVE (5 commits, 5d04d6f..cb48af4): I-1, I-2, M-1, M-2, M-4, M-5, P35-1.
  Suite 213 -> 220 passed. Gate A unchanged (exit 1, 6 PASS / 3 SKIP).
  Tier 1 ladder bit-identical: 19.5 / 32.9 / 52.9 / 69.1. Corpus digest unchanged,
  confirming the _ISO_FIT_NOMINALS_MM extraction did not perturb the RNG stream.
  No constant, no table value, no checker-core module changed. B-5 still unimplemented.
  History NOT rewritten -- d312ad6 with the corrupt blob stays as the honest record.
CONTROLLER-VERIFIED: assert_is_the_nist_original ACCEPTS the real fixture and REJECTS
  the CRLF-mangled copy ("391739 bytes, not the 396445 bytes NIST-PROVENANCE.md
  claims"). The hole is closed.

*** THE FIXER CORRECTED THE REVIEWER, AND THE RE-REVIEW CONFIRMED THE CORRECTION. ***
  M-1's finding claimed a 1.7 d4 fraction would leave "every test in the repo
  passing". False: test_sampler.py:87 pins d4 to [0.60, 0.80] and also fires. The
  finding's CONCLUSION stood (that guard is about label balance, so it would miss a
  widened _CLEARANCE_HOLE_MM reaching the wall through the other factor), but the
  clause did not. Worth recording: subagent findings are not automatically right.

SCOPED RE-REVIEW (opus): all seven ADDRESSED, no new Critical/Important, merge
  recommended. It independently checked ISO 286 deviations (g6 es=-4um at Ø6, -12um
  at Ø120; k6 es=+9um at Ø6; p6 es=+59um at Ø120), confirmed the OCP-gate refactor
  un-gated nothing that needs OCP, confirmed `<` is the right asymmetry (over-
  projection is conservative, so rejecting it would reject a safe spec), and computed
  the exact trip points of the new derived floor (d4 hi > 1.52, or the M12-loose hole
  > 14.836, or _HOLE_UPPER_DEV_MM > 0.65, or _MIN_WALL_MM < 3.55).

PARKED after the re-review (no second fix wave per SDD):
  R-a [MINOR, NEW, surfaced to the human in the finish options rather than parked
    silently] tests/test_ap242_pmi.py:11-17 uses a bare `except ImportError` to set
    _HAVE_OCP, so on a machine WITH the [gen] extra, breaking validation/ap242_pmi.py
    (e.g. renaming PmiCounts) flips four oracle tests to silent skips reporting
    "requires the [gen] extra" instead of failing loudly. Same defect class the wave
    was closing, narrower target. Bounded: the I-1 integrity test sits outside the
    try and always runs, and test_end_to_end.py hard-imports read_pmi_counts, so only
    a PmiCounts-only breakage is fully masked. One-line fix: gate on
    importlib.util.find_spec("OCP") is None and leave the import unguarded.
  R-b test_spec.py:322 corpus sweep restates the guard rather than independently
    checking it (sample_assembly builds an AssemblySpec, so the guard raises before
    the assert). Low tension, not fake. Stands.
  R-c the _EDGE_MARGIN_MM half of the derived-floor test is 5.0 vs 1.775 and needs
    d4 hi > 3.9 to fire -- effectively unfailable. The _MIN_WALL_MM half (4.0 vs 3.55,
    12.7% headroom) is the one carrying the finding. Stands.
  R-d test_end_to_end.py still uses the in-function importorskip("OCP") idiom rather
    than the new per-test needs_ocp marker. Cosmetic inconsistency. Stands.
  R-e .gitattributes remains untested by construction -- the hash notices corruption
    only after a clone. Closing it needs the clean-clone CI run that Gate A's "Fresh
    clone pipeline" row already SKIPs on. Not a separate gap.
  R-f plate_thickness_mm is one scalar for both plates. If per-part thicknesses ever
    land, the I-2 guard must follow the CROSSED part, not the assembly scalar. Worth
    a line in the frozen schema doc.

STATE: all 5 plan tasks complete, every per-task review clean with zero fix rounds,
final review closed after one fix wave. Branch 7ac01ed..cb48af4, 11 commits.

R-a: CLOSED (commit 2680bc0, merged 44658ba). Was parked as a residual minor after
  the fix wave; the human asked for it afterwards. Demonstrated both directions with
  PmiCounts renamed and OCP present: before = "1 passed, 4 skipped" (silently
  claiming the extra was missing), after = ImportError at collection. Also verified
  the genuinely-absent-OCP path still gives 1 passed / 4 skipped rather than an
  error, which is the behaviour the per-test gate exists to preserve.
  R-b..R-f remain parked as recorded above.

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
