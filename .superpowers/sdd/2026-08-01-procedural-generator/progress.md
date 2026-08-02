# SDD ledger — plan: docs/superpowers/plans/2026-08-01-procedural-generator.md

Branch: feat/procedural-generator
Base: dd7a883

Known-intentional plan choices (pre-flight scan; adjudicate fast if a reviewer raises them):
- Task 7 tests SKIP until Task 8 fetches the NIST suite. Documented in both tasks; re-run Task 7 after Task 8.
- Task 9 has no implementation step by design -- it is the integration gate, tests only.
- Task 1 step 2 expects a NameError-shaped failure, not a normal assertion failure.

Environment already spiked and verified before the plan was written: cadquery 2.8.0,
OCP XCAF read+write PMI, NIST suite downloads, OCCT reads ftc_06 as 47/27/59.

P3-1: complete (commits dd7a883..71afffb, review clean). 111 passed. Lint verified non-vacuous by planting "import cadquery" in checker.py -> fails; removed -> passes.
P3-1: minor (deferred): startswith("tolcad.gen") would also match a hypothetical tolcad.generic; stricter only, no false negative.
P3-2: fix round 1/5 (2 addressed, 0 open; commits c4e99a1..4ce9dd6)
P3-2: complete (commits 71afffb..4ce9dd6, review clean). 123 passed, gate exit 1.
P3-2: KEY DESIGN: position_tol_a/b are the SINGLE SOURCE OF TRUTH. to_check_dict()
  injects them into copies of the hole dicts, overriding any position_tol the input
  dicts carry. Tasks 3-6 must set position_tol_a/b on MateSpec and need NOT embed
  position_tol inside the hole dicts -- doing both is harmless, but the dedicated
  fields win.
P3-2: minor (deferred): position_tol_b is dead for the virtual_condition kind
  (only position_tol_a is used, for both hole and pin). The sampler does not emit
  virtual_condition mates, so it is unexercised. Close it if that changes.
P3-2: minor (deferred): a position_tol is injected into the fastener dict for the
  floating/fixed kinds where Y14.5 never reads it. Harmless, meaningless.

=== SESSION BOUNDARY 2026-08-01 ===
NEXT: P3-3 (mating-feature library). Plan task 3. Base = 4ce9dd6.
Environment is installed and verified: cadquery 2.8.0, OCP XCAF, pytest 9.0.2.
Resume with: superpowers:subagent-driven-development on
docs/superpowers/plans/2026-08-01-procedural-generator.md, starting at Task 3.

=== SESSION RESUMED 2026-08-01 (second session) ===
Tasks 3-5 were executed by the controller directly under executing-plans + TDD
(red verified, then green) before the human asked to switch to SDD. They did NOT
go through a task-reviewer subagent; the final whole-branch review must cover them.

P3-3: complete (commit 039d781, TDD red->green, 9 tests pass). Plan predicted 10
  tests; actual is 9 (6 plain + a 3-way parametrize) -- plan miscount, not a gap.
P3-3: note -- every clearance-hole value matches the ISO 273 fine/medium/coarse
  series, but is NOT verified against the primary standard, so no edition is cited.
  Docstring says so explicitly. Open question for the human still stands.
P3-4: complete (commit d53969e, TDD red->green, 6 tests pass)
P3-4: note -- Tier 1 mates NEVER fail below difficulty 4, by construction:
  _TOL_FRACTION_RANGE caps the applied fraction at 1.0 for d1-3, so
  margin = C*(1-f) >= 0 always. Only iso_fit supplies negative verdicts at d1-3.
  Measured over seeds 0-199: d3 = 452 Tier1 pass / 0 fail, 71 iso pass / 77 fail;
  d4 = 131 Tier1 pass / 478 fail. Arithmetic matches y14_5.fastener_assembles, so
  this is plan-specified, not a bug. Flagged to the human -- worth revisiting
  BEFORE Phase 3.5 pre-registration freezes the difficulty ladder.
P3-5: complete (commit 6876671, TDD red->green, 4 tests pass)
P3-5: note -- swept 160 assemblies (seeds 0-39 x difficulty 1-4): all solids valid
  with positive volume. The plate-edge overlap risk (large hole near the boundary)
  did not bite at plate_size 40 / pitch 12.

P3-6: complete (commits 6876671..a78d5c4, review clean). 145 passed, 2 deselected.
P3-6: reviewer raised one "cannot verify from diff": whether the importorskip-gated
  tests actually ran rather than silently skipping. Controller resolved: baseline was
  121 tests; 121+9(P3-3)+6(P3-4)+4(P3-5)+5(P3-6) = 145 exactly, so they ran. Not a gap.

P3-7: implemented (commit a09ee2f), status DONE_WITH_CONCERNS. 2 SKIPPED, not passed --
  data/nist_pmi/ did not exist yet, so the headline 47/27/59 assertion was NOT
  exercised. Sanity checks that do not need the data did pass (module imports; OCP
  imports resolve; read_pmi_counts raises FileNotFoundError on a missing path).
  MUST re-run tests/test_ap242_pmi.py after P3-8 fetches the data. Review dispatched.
P3-8: HUMAN APPROVED the ~14MB nist.gov download (asked and answered this session).
  Approval covers that one URL only.

P3-8: complete-pending-review (commit ae2b3ac). Fetcher exit 0, 17 AP242 files.
  *** THE HEADLINE ORACLE CLAIM IS NOW VERIFIED AGAINST REAL DATA: ***
  nist_ftc_06_asme1_ap242-e2.stp reads as EXACTLY 47 dimensions / 27 geometric
  tolerances / 59 datums. No discrepancy. This retroactively verifies P3-7, whose
  tests had only skipped. Full suite 150 passed, 2 deselected. No payload committed.
P3-8: implementer deviation (justified, accepted): the brief's fetcher docstring
  wrapped "without any / restrictions" across a line break, which would have failed
  the brief's OWN test asserting the contiguous substring "without any restrictions".
  Re-wrapped the lines; wording unchanged. A plan bug the implementer caught.
P3-7: fix round 1/5 dispatched. Finding was plan-mandated, so it went to the human:
  module-level pytestmark skipped test_missing_file_raises under a reason untrue of
  it. HUMAN RULED: FIX (approved this session). Grounds: (a) project's documented
  dominant failure mode is "the metric that cannot fail" -- 4 instances in 14 tasks;
  an unconditionally-skipped test is a pure instance; (b) design spec line 252 makes
  "fresh clone, no licence, runs end-to-end" an explicit success criterion, and the
  fresh-clone-without-data path is the only place the mislabelled skip does damage;
  (c) nothing frozen is touched -- CLAUDE.md freezes only the spec 7 gate thresholds.
  Fix must be evidenced by a simulated fresh clone (rename the .stp aside) showing
  1 passed / 1 skipped, not merely 2 passed.

P3-7: fix round 1/5 (1 addressed, 0 open; commit 211633c). Re-review verdict ADDRESSED.
  Evidence supplied as demanded: fixture renamed aside -> 1 passed / 1 skipped (was
  2 skipped before the fix); fixture restored and confirmed; 150 passed after.
P3-7: complete (commits a78d5c4..211633c, review clean after 1 fix round).
P3-8: complete (commits a09ee2f..ae2b3ac, review clean / approved).
P3-8: OPEN QUESTION TO HUMAN (plan-mandated finding, Important): the three tests in
  tests/test_fetch_nist.py never import or execute fetch_nist_pmi.main(). They check
  file existence and two substring greps. So the mismatch branch -- observed AP242
  count != EXPECTED_AP242_FILES (17) -> warn to stderr -> return 1 -- has ZERO
  automated coverage. That branch is the guard protecting oracle integrity if NIST
  changes the archive upstream, and it was exercised only by one manual run where the
  count happened to match. Same failure class as the P3-7 finding and as the project's
  documented dominant failure mode ("the metric that cannot fail"). Plan-mandated
  because the brief specifies exactly those three tests.
P3-8: minor (deferred): response.read() buffers the whole ~14MB archive in memory
  rather than streaming. Brief-verbatim, fine at this size.
P3-8: minor (deferred): no exception handling around the network call; an interrupted
  download surfaces a raw traceback. Brief-verbatim, acceptable for a research fetcher.

P3-8: HUMAN RULED on the open question above: ADD A TEST for the mismatch branch.
  Deviation from the plan's three-test surface is authorised. Required shape: build a
  small fake ZIP in tmp_path whose AP242 count is wrong, point the fetcher at it,
  assert it warns and returns 1. Offline, no network. Fix round queued behind P3-9 to
  avoid two agents racing on the git index.

P3-9: implemented (commit bbac3dc). 3/3 passed FIRST RUN, no production module touched
  -- the integration gate confirms P3-1..P3-8 compose without modification.
  Full suite 153 passed, 2 deselected (was 150, exactly +3).
  Gate A: exit 1 (NOT CLEARED, correct by design at this phase).
    6 PASS: Y14.5 self-consistency, Monte Carlo convergence, checker reliability,
            validation isolation, Y14.5 citation verified, ISO 286 transcription.
    3 SKIP: NIST PMI conformance, TolAnalyst agreement, fresh-clone pipeline.
  Review dispatched, with an explicit "could this test ever fail?" instruction on all
  three tests -- especially the isinstance(bool) assertion and the zero-PMI-count
  assertion, both of which smell like they could pass against anything.
P3-8: fix round 1/5 dispatched (mismatch-branch test). Demanded BOTH a negative case
  (wrong AP242 count -> return 1) and a POSITIVE CONTROL (exactly 17 -> return 0),
  because the negative alone would pass against a main() that always returned 1.
  Also demanded a deliberate-failure check and no network access.

P3-8: fix round 1/5 (1 addressed, 0 open; commit b6f89b7). Re-review: all six required
  elements ADDRESSED, no new breakage. Negative test (2 AP242 -> return 1, warns) AND
  the mandatory positive control (17 -> return 0, no stderr) both present as separate
  tests. Network made structurally impossible: urlopen monkeypatched to raise, URL
  repointed to example.invalid, archive pre-created so the download branch is never
  entered. Real data/nist_pmi/ untouched (DEST redirected to tmp_path). Production
  script unmodified. Deliberate-failure evidence: forcing ap242_count=17 in the
  negative test produced "assert 0 == 1" FAILED, then reverted.
P3-8: complete (commits a09ee2f..b6f89b7, review clean after 1 fix round). 155 passed.
P3-9: complete (commits 211633c..bbac3dc, review approved, 1 parked).
P3-9: PARKED (human ruled: park, do not fix) -- Important, plan-mandated:
  `assert all(isinstance(v.assembles, bool) ...)` in test_end_to_end.py is a type-only
  smoke check; a checker with an inverted or constant verdict bug would pass it.
  RULING: not a real coverage gap. Tier 1 verdict correctness is owned by the exact
  closed-form tests in test_y14_5.py and test_checker.py, and this test's other
  assertions (mate count, lossless round-trip, STEP size, zero-PMI contrast) do real
  work. Strengthening it would hardcode sampler output into an integration test.
  Final whole-branch review should triage this.

=== ALL NINE PLAN TASKS COMPLETE ===
Branch state: dd7a883..b6f89b7. Full suite 155 passed, 2 deselected.
Gate A exit 1 (NOT CLEARED), 6 PASS / 3 SKIP -- correct by design at this phase.
NOTE: this repo's default branch is `master`, NOT `main`.

=== FINAL WHOLE-BRANCH REVIEW (opus, merge base dd7a883..b6f89b7) ===
VERDICT: NOT READY TO MERGE. 2 Critical, 5 Important, 7 Minor.
All global constraints verified upheld (mm/float, core CAD-free, validation
one-directional, EPS exact, spec 7 thresholds untouched, no corpus path, no payload
committed). The problems are in correctness and in benchmark degeneracy, not architecture.

C1 [CONFIRMED BY CONTROLLER'S OWN EXECUTION] build.py:42-43 -- holes land at CUMULATIVE,
  not absolute, positions. `.faces(">Z").workplane()` defaults to
  centerOption="ProjectedOrigin", which INHERITS the parent workplane origin, so
  `.center(x,0)` is a relative offset from the previous hole, not an absolute coord.
  Controller reproduced directly: requested x=[-12,0,12] -> actual cylinder centres
  [-12.0, 0.0]. Three holes requested, two produced.
  Controller measured over seeds 0-29 x d2-4: 42/90 assemblies have a part_a hole
  count != tier-1 mate count. Non-integer centroids are partial cylinders (edge notches).
  IMPACT: every exported STEP contradicts its own sidecar schema. The STEP is the
  reference geometry predictions get scored against (spec 4.2/5), so any number derived
  from it is invalid.
  Both candidate fixes verified working by the controller:
    centerOption="CenterOfBoundBox" -> [-12.0, 0.0, 12.0]
    .pushPoints([...]).hole(d)      -> [-12.0, 0.0, 12.0]
  WHY NO TEST CAUGHT IT: test_build.py asserts only validity, positive volume, a
  d4-vs-d1 TOTAL volume comparison, and determinism. None asserts hole count, position,
  or containment. All four pass against a build that drops half its features.
  *** CONTROLLER CORRECTION: the P3-5 ledger note above ("the plate-edge overlap risk
  did not bite") is WRONG. It was based on isValid()/Volume()>0, which is exactly the
  evidence class that cannot see this. It bit. ***

C2 sampler.py:22-27 + test_sampler.py:33-45 -- the difficulty ladder is a cliff, and its
  anti-degeneracy guard test is provably blind to the Tier 1 sampler.
  Reviewer's seeds 0-199 measurement matches the controller's independent one exactly:
  Tier 1 failures are 0 at d1, d2 AND d3; 478/609 at d4.
  Reviewer mutation-tested the guard test against production:
    _TOL_FRACTION_RANGE -> (0.0,0.0) : test PASSES (all mates trivially assemble)
    _TOL_FRACTION_RANGE -> (5.0,5.0) : test PASSES (all mates fail hard)
    flat ladder (0.2,0.5) everywhere : test PASSES, and the ENTIRE 155-test suite passes
  Both its assertions are satisfied entirely by iso_fit mates, so the test is orthogonal
  to what its name and docstring claim. This is a FIFTH instance of the project's
  documented dominant failure mode -- inside the test written to prevent it.
  Nothing on this branch asserts that difficulty affects tolerance tightness at all.

I1 spec.py:58-63 -- iso_fit emits no mc seed/n, so checker falls back to seed=0.
  H7/h6 is line-to-line at MMC, so its label is decided by sampling noise: over 30 MC
  seeds the verdict is True in 23 and False in 7. 23% of seeds would relabel every
  H7/h6 mate. CLAUDE.md's "Tier 2 always reports a seed" is met only in Verdict.detail,
  not in the sidecar a reproducer actually reads.
I2 iso_fit labels are 100% predictable from the designation string (g6/h6 -> always
  True, k6/p6 -> always False, zero variance over 800 mates). Since d1-3 draw ALL their
  negatives from iso_fit (C2), a model can score 100% below d4 by regexing the letter.
I3 plate 40mm / pitch 12mm undersized vs the Ø14.5 max hole. With CORRECT absolute
  placement, d4 overhangs the plate edge in 195/200 seeds and merges neighbours in
  98/200. So C1's fix ALONE is not sufficient -- geometry sizing must change too.
I4 build.py drills an identical through hole in both plates for fixed AND floating, so
  the two kinds are geometrically indistinguishable despite different ground-truth
  formulas -- unlearnable from the reference geometry. Also: y14_5.py:80-81 states as a
  load-bearing precondition "the generator must emit projected zones"; this branch is
  that generator and emits none, so every fixed_fastener verdict is optimistic by the
  core module's own contract.
I5 on a fresh clone the only exercised oracle assertions are zeros; a read_pmi_counts
  stubbed to return PmiCounts(0,0,0) passes the whole fresh-clone suite.

Minors (7): no archive checksum; position_tol injected into fastener dict pollutes the
  published schema; frozen dataclass with mutable dict fields; test_sampler.py:10-12
  `len(specs) > 1` should be `== 20`; 1/3847 boundary-exact label; CORE_LIGHT_MODULES
  omits __init__; DEST.glob counts pre-existing files.

Reviewer AGREED with the human's P3-9 park ruling, but noted the reasoning does not
  extend to the sampler -- and C2 is exactly the sampler's guard test failing.

AWAITING HUMAN DECISION on fix scope: C1/I3/C2-guard are unambiguous bugs, but the
  ladder VALUES (C2a), I2 and I4 shape what Phase 3.5 pre-registers, and memory records
  an explicit rule that pre-registration-shaping choices are the human's, not mine.

=== FINAL FIX WAVE (b6f89b7..1098ca1) — full write-up in final-fix-wave-report.md ===
HUMAN SCOPED: C1, I3, C2(a), C2(b), I1. Deferred to a second pass: I2, I4, I5, 7 minors.
Suite 155 -> 186 passed, 2 deselected (188 with slow). Gate A unchanged: exit 1, 6 PASS / 3 SKIP.
NIST fixture present and untouched; nothing staged; data/nist_pmi/ still gitignored.

9d198a8 C1+I3. build.py drills via pushPoints on a CenterOfBoundBox workplane, so
  positions are absolute. New CAD-free tolcad/gen/layout.py derives pitch (widest
  adjacent radius pair + 4 mm wall) and plate size (span + 2*(max radius + 5 mm edge
  margin)); sampler records plate_size_mm per assembly; build_assembly REFUSES an
  undersized plate. Containment/non-intersection proven by an exact removed-volume
  identity over seeds 0-49 x d1-4 (all of them, not a sample).
  MUTATION: reverting _drill to the relative chain fails 10 new tests, e.g.
  part_a cylinders [-24.0,-18.0,0.0] vs expected [-18.0,-6.0,6.0,18.0].
  Pre-existing test_drilling_holes_removes_material rewritten to compare volume
  REMOVED, not total: plates are now sized per assembly so a d4 plate is BIGGER
  than a d1 plate. Strictly stronger than the original, not weaker.

a6412fa C2. New ladder 1:(.60,1.09) 2:(.65,1.16) 3:(.70,1.25) 4:(.72,1.34).
  MEASURED Tier 1 failure rate over seeds 0-199: d1 31/159=19.5%, d2 99/301=32.9%,
  d3 239/452=52.9%, d4 421/609=69.1%. Was 0/0/0/69.1%.
  Reviewer's suggested start MEASURED AND REJECTED: 11.3/40.2/87.2/100.0% -- d4 would
  have had zero assemblable Tier 1 mates, the same degeneracy inverted.
  Guard rewritten to filter Tier 1 and run at EVERY difficulty; new test asserts the
  failure rate is strictly increasing, with band checks on the ends.
  MUTATIONS: flat (0.2,0.5), (0.0,0.0), (5.0,5.0) and the ORIGINAL b6f89b7 ladder all
  now FAIL. All four PASSED the test that was replaced.
  RNG draw count unchanged, so sizes/grades/kinds/designations are bit-identical to
  b6f89b7; only position tolerances moved.

1098ca1 I1. MateSpec.mc_seed / mc_n (defaults last), emitted in the iso_fit branch of
  to_check_dict, serialised, survive from_json. Sampler: mc_seed = 10_000 + seed*4 +
  index -- reproducible, collision-free, never 0 (0 is the checker fallback).
  MUTATION: deleting the keys gives KeyError:'seed' and assert 0 == 10006.
  *** H7/h6 UNDER PER-MATE SEEDS: 85 True / 23 False over 108 mates (was uniformly
  True under the accidental seed 0). Margins are only 1.0 or 0.99999 -- one clearance
  failure in 100k samples. g6 still always True, k6/p6 still always False.
  THIS IS INPUT TO THE DEFERRED I2 DECISION, NOT A DECISION. SUPPORTED_FITS untouched. ***

CONCERNS RAISED FOR THE HUMAN (detail in final-fix-wave-report.md section 7):
  1. H7/h6 is now the only fit not readable off the designation letter, and its signal
     is 1 part in 1e5 of sampling noise. Pre-registration should rule on whether that
     is a test item or a coin toss. Not decided here.
  2. I4 still open and it touches the geometry about to be frozen: fixed and floating
     remain geometrically identical, and y14_5's "generator must emit projected zones"
     precondition is still unmet.
  3. The ladder is calibrated to the current clearance-hole table. Re-measure if the
     ISO 273 open question from Task 3 ever changes those values.
  4. build_assembly's undersized-plate guard is a breaking change for hand-built specs
     that take the 40.0 mm default.
  5. The seeds 0-49 x d1-4 containment sweep adds ~8 s (suite 16.6 s -> 23.4 s) and is
     deliberately NOT marked slow.
  6. layout.py's margin rationale assumes max applied fraction ~1.34; revisit if the
     ladder is ever pushed higher. The containment test checks nominal geometry and
     would not catch the rationale going stale.

=== FINAL FIX WAVE (commits b6f89b7..1098ca1, 3 commits) ===
9d198a8 C1+I3 absolute placement + plate sized from radii (new CAD-free gen/layout.py)
a6412fa C2a+C2b ladder retuned, guard tests rewritten
1098ca1 I1 explicit mc_seed / mc_n

HUMAN DECISIONS driving this wave: (1) fix everything that shapes pre-registration;
(2) ladder must straddle 1.0 at every difficulty with a rising failure rate;
(3) I4 deferred to a second pass, before any corpus generation.

CONTROLLER-VERIFIED INDEPENDENTLY (not taken on the subagent's word):
  suite 186 passed / 2 deselected (was 155/2)
  tier1 failure rate seeds 0-199: d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%
    (was 0 / 0 / 0 / 69.1%) -- monotone AND both classes present at every level
  hole count+position wrong in 0/90 assemblies (was 42/90)
  C1 root cause reproduced directly before the fix: requested x=[-12,0,12] gave
    cylinders at [-12.0, 0.0]; both candidate fixes verified to give [-12,0,12]

The fixer MEASURED AND REJECTED the reviewer's suggested ladder ranges: they yield
  11.3/40.2/87.2/100.0%, i.e. d4 with ZERO assemblable Tier 1 mates. Good catch --
  it would have replaced one degenerate end of the ladder with the other.

SCOPED RE-REVIEW (opus): all five ADDRESSED, no new Critical/Important, merge
  recommended. Notable independent checks it made: the containment identity is sound
  (measured volume is bounded above by the ideal sum unconditionally, so overhang and
  overlap cannot compensate) with 137x numeric headroom, not borderline; the
  RNG-invariance claim is true so sizes/grades/kinds are bit-identical to b6f89b7;
  _mc_seed_for is injective where it matters; zero Tier 1 mates now sit within EPS of
  the boundary (smallest |margin| 1e-4 over 1521 mates).

PARKED MINORS from the re-review (no second fix wave per SDD; all test-hygiene):
  P-a test_layout.py:22-33 imports _MIN_WALL_MM/_EDGE_MARGIN_MM from production and
    compares against them, so zeroing those constants breaks no test. Tangent holes
    have zero intersection volume so the containment test misses it too. RULING: real
    instance of the project's signature pattern, but Minor and one line to fix --
    SURFACED TO THE HUMAN in the finish options rather than parked silently.
  P-b test_sampler.py:71 imports _mc_seed_for from production (has independent teeth
    via != 0 and the checker-detail assertion). RULING: weaker than it reads, stands.
  P-c test_layout.py:13-15 asserts a property of features.py, not layout.py. Stands.
  P-d layout.py accepts hole_b=None but build.py would TypeError on it. Pre-existing
    build-side limitation; sampler never emits virtual_condition. Stands.
  P-e 100_000 duplicated as a default in spec.py, sampler.py and checker.py. Drift
    risk between the sidecar default and the checker fallback. Stands, worth a follow-up.
  P-f the two ladder tests each rebuild the same 80x4 verdict set. Stands.
  P-g spec.py validates mc_n before kind, so the less interesting error wins. Stands.

CARRIED FORWARD TO PHASE 3.5 -- MUST BE DECIDED BEFORE PRE-REGISTRATION:
  * H7/h6 relabelling. With explicit per-mate seeds it is now 85 True / 23 False over
    108 occurrences, where the accidental seed=0 had made it uniformly True. Margins
    are only 1.0 or 0.99999 -- ONE clearance failure in 100k samples. Is that a test
    item or a coin toss? The human must rule. Entangled with I2.
  * I2 iso_fit labels 100% predictable from the designation letter (g6/h6 vs k6/p6).
  * I4 fixed and floating are geometrically identical in the STEP, so the distinction
    is unlearnable from reference geometry; and y14_5.py:80-81 states "the generator
    must emit projected zones" as a load-bearing precondition, still unmet. HUMAN
    RULED: second pass, BEFORE any corpus generation.
  * I5 fresh-clone oracle coverage asserts only zeros; a stubbed read_pmi_counts
    returning PmiCounts(0,0,0) passes the whole fresh-clone suite.
  * The clearance-hole table is still untraced to ISO 273 primary text, and the ladder
    is calibrated against it -- re-measure the ladder if that resolves differently.

STATE: all 9 plan tasks complete, final review clean after one fix wave.
Branch dd7a883..1098ca1. Suite 186 passed / 2 deselected. Gate A exit 1, 6 PASS/3 SKIP.

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
