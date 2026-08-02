# SDD ledger — plan: docs/superpowers/plans/2026-08-01-iso273-traceability.md

Branch: feat/iso273-traceability
Base: e8e4a9f (master, after the 3.5a merge 5442926 + the R-a fix merge 44658ba)
Prior ledgers: .superpowers/sdd/2026-08-01-pre-registration-prep/progress.md
               .superpowers/sdd/2026-08-01-procedural-generator/progress.md

Baseline at e8e4a9f: 220 passed (no filter, incl. slow). Gate A exit 1, 6 PASS / 3 SKIP.
Tier 1 ladder, seeds 0-199: d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%.

WHY THIS PLAN: the last untraced numbers in the generator, closed before Phase 3.5
pre-registration freezes them. The human obtained and read the primary standards.

PRIMARY-SOURCE RESULTS (human-verified 2026-08-01, from scans of the standards):
  * ISO 273-1979(E) Table 1 -- all 21 clearance-hole diameters (M3-M12 x
    fine/medium/coarse) MATCH EXACTLY. Our close/normal/loose = their
    fine/medium/coarse.
  * ISO 273 tolerance-fields note, verbatim: "The following tolerance fields are
    given for information only, for use where it is desirable to specify
    tolerances: fine series : H12, medium series : H13, coarse series : H14."
    Note "for information only" -- offered, not mandated. The human chose to take
    the option, so the schema cites the standard rather than a flat constant.
  * ISO 2306-1972 Table 1 (coarse pitch) -- all 7 tapping drills MATCH EXACTLY,
    including M8 -> 6.80 and M12 -> 10.20. Clause 0 explains why these are NOT
    nominal-minus-pitch (6.75 / 10.25): the drill is only APPROXIMATELY D-P, with
    actual sizes selected from the ISO/R 235 preferred drill series. DO NOT let
    anyone "correct" them to the subtraction.
  * ISO 286-1:2010 Table 1 -- the nine IT cells we need, and the full 13-band rows.

*** THE UNIT TRAP, do not lose this ***
ISO 286-1:2010 Table 1 publishes IT01-IT11 in MICROMETRES and IT12-IT18 in
MILLIMETRES -- two separate span labels across the grade columns. _IT_MICRONS is
micrometres throughout, so the new rows convert on entry (0,43 mm -> 430). Pasting
the published figures directly makes them 1000x too small, and 0.00043 mm is
NARROWER THAN IT5 -- small enough to pass every ordering-free test in the suite.
CLAUDE.md's blanket "ISO 286 tables publish micrometres" is false for exactly the
grades this plan adds; Task 1 corrects it.

CONTROLLER-VERIFIED BY EXECUTION before the plan was written:
  * Existing IT5-IT8 cross-check clean against the human's ISO 286-1 scan --
    independent confirmation of the earlier 117-value verification.
  * IMPACT IS BOUNDED. Hole MMC = nominal + lower_dev and lower_dev is 0, so the
    upper deviation CANNOT move a Tier 1 verdict or any ladder point.
    Worst hole: M12 coarse Ø14.5, IT14 in >10-18 = 0.43 mm.
      radius growth  0.100 -> 0.215
      excursion      1.775 -> 1.890
      required wall  3.550 -> 3.780   vs _MIN_WALL_MM 4.0 -- STILL SUFFICIENT
      headroom       12.7% -> 5.5%
      required edge  1.890 vs _EDGE_MARGIN_MM 5.0 -- ample
    => NO CONSTANT CHANGES. But the literal floor asserting _MIN_WALL_MM >= 3.7 is
    now BELOW the true 3.78 requirement, and NEITHER layout test fails on that:
    the derived-floor test recomputes and passes (4.0 >= 3.78), the literal passes
    too (4.0 >= 3.7). It silently stopped being a floor and would accept 3.75.
    That is a tenth instance of the project's signature pattern; Task 3 closes it.

PRE-FLIGHT SCAN (clean; known-intentional, adjudicate fast if a reviewer raises them):
  - Task 1 Step 2 and Task 2 Step 2 each include a regression pin that PASSES on
    arrival (existing IT grades untouched; hole MMC unaffected). Labelled as such.
  - Task 3 has no production code change by design: the constants are already
    adequate. Red is a deliberate mutation of the literal back to its stale value.
  - iso286.py IS a checker-core module and IS modified in Task 1. That is allowed
    and additive -- no existing value may change, and the 117 verified values are
    pinned. The prohibition is on y14_5/montecarlo/checker/types/reliability.

HUMAN DECISIONS carried forward -- do not re-litigate:
  * Implement H12/H13/H14 per series (chosen over keeping the flat constant).
  * ASME Y14.5 B-5 stays unimplemented.
  * The tapped hole keeps a flat, documented, standard-free band. It is provably
    inert: y14_5's B-4 never reads hole_b's size in the fixed case. Do not invent
    a citation for it.

T1: implemented (commit 13e3b97). RED gave the exact expected
  "ValueError: IT grade 12 not tabulated; have [5, 6, 7, 8]", with the
  existing-grades regression pin passing on arrival as designed. Suite 233 passed
  (220 + 13 new cases). Files touched: iso286.py, tests/test_iso286.py, CLAUDE.md.
T1: CONTROLLER-VERIFIED INDEPENDENTLY -- all 39 new cells (3 grades x 13 bands)
  match the human's ISO 286-1 scan exactly when read back through it_grade and
  compared against the PUBLISHED MILLIMETRE values; the ordering
  IT8 < IT12 < IT13 < IT14 holds at every one of the 13 bands; and the diff is
  purely additive (68 insertions, 2 deletions, the deletions being the two
  CLAUDE.md lines that were reworded). The 1000x trap did not bite.
  Spot check: at Ø14 -> IT8 0.027, IT12 0.18, IT13 0.27, IT14 0.43 mm.
T1: review dispatched, asked specifically whether the unit-trap DOCUMENTATION is
  good enough to stop the next editor appending IT15 wrongly, and whether the
  ordering assertion could be satisfied by a uniformly scaled-down row set.

T1: review APPROVED with two Important follow-ups, BOTH gaps in the controller's
  brief rather than implementer errors. Not escalated to the human: neither
  contradicts a human decision, they complete the decision ("cite the standard")
  rather than altering it.
  T1-a iso286.py:3-4 -- the module docstring's OPENING summary still carries the
    blanket "Published in micrometres" claim, four lines above the new
    TRANSCRIPTION SOURCE paragraph that correctly describes the two-range split.
    The file contradicts itself, and a reader who stops at the top gets exactly
    the wrong mental model this task exists to prevent. Same inaccuracy that was
    fixed in CLAUDE.md, left in place here because the brief only scoped the
    TRANSCRIPTION paragraph.
  T1-b tests/test_iso286.py -- the controller's verification of all 39 new cells
    was a ONE-OFF SHELL RUN, never encoded as a test. Per-value coverage exists
    for only 3 of 13 bands, ordering for 5 of 13; the length check catches
    truncation but NOT a same-length transposition of two adjacent bands. So 8 of
    13 bands have no correctness check at all for grades 12-14, and a future edit
    corrupting one would pass CI. Ephemeral evidence is not a guard.
  Reviewer credited the ordering test for correctly anchoring against the
  UNTOUCHED IT8 row, which does close the "uniformly scaled-down rows" loophole.
  Minor (accepted, no action): test_existing_grades_are_untouched covers only 3
  spot values, adequate only because the diff is structurally additive.

  FIX ROUND QUEUED behind T2 -- T2 is running and would race on the git index.

NEXT: T2 running, then T1 fix round 1. Base for T2 = 13e3b97.

FIX ROUND 1 (F-1/F-2/F-3, base d78c39e): DONE. Commits f6300b3 (F-1, iso286
opening summary reworded to match the TRANSCRIPTION SOURCE split), 3652d60
(F-2, all 39 IT12-IT14 cells pinned in tests/test_iso286.py), 3125513 (F-3,
stale TAPPING_DRILL_MM caveat rewritten + guard made case-insensitive). Full
suite 257 passed (244 + 13 new parametrized cases). Gate A exit 1, 6 PASS / 3
SKIP. Ladder unchanged: d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%. Both
mutation demonstrations (IT13 band-5/6 transposition; uppercase-NOT caveat
reinstatement) reproduced the intended failures and were reverted. Diff
scope confirmed limited to iso286.py, tests/test_iso286.py, features.py,
tests/gen/test_features.py. Full report:
.superpowers/sdd/2026-08-01-iso273-traceability/fix-round-report.md

NEXT: Task 3 (re-measure layout floors) still outstanding.

T2: complete (commits 13e3b97..d78c39e, review verdict "Needs fixes" on ONE Important
  item -- which the fix round had already closed by the time the review landed, see
  below). The reviewer verified from source rather than the report: it_grade IS called
  with the HOLE's diameter not the fastener's (matters at band boundaries: M10 loose is
  Ø12.0 in >10-18 while the M10 fastener is in >6-10); both verified value tables are
  untouched; and it read y14_5.py to confirm the tapped hole is inert -- finding it
  inert TWICE OVER, since B-4's margin never references hole_b.mmc, and mmc is
  nominal + lower_dev so upper_dev could not affect it even if it were read.
T2: the Important finding was F-3 below, independently identified. The reviewer rated
  the stale comment worse than the implementer framed it: it contradicted the module
  docstring on TWO counts, not one -- (a) whether the values were checked, and (b)
  whether they are nominal-minus-pitch.
T2: minor (deferred): test_hole_mmc_is_unaffected_by_the_tolerance_change asserts
  nominal + lower_dev == nominal against the dict clearance_hole_for just returned,
  where lower_dev is a hardcoded 0.0 -- so it restates the literal rather than
  exercising FeatureOfSize.mmc. It would still catch lower_dev becoming nonzero.
T2: minor (deferred): test_clearance_hole_tolerance_is_no_longer_flat asserts only
  len(devs) > 1, so a partial regression to two buckets would pass. Sibling tests
  close the gap.

FIX ROUND RE-REVIEW: all of F-1/F-2/F-3 ADDRESSED, no new breakage, and T2's parallel
  Important finding confirmed satisfied on both counts. The re-reviewer independently
  traced the band arithmetic and confirmed every probe diameter
  [2,4,8,14,25,40,65,100,150,200,300,350,450] lands STRICTLY INSIDE its band -- none
  sits on a boundary (3/6/10/18/30/50/80/120/180/250/315/400/500), which is the subtle
  way the 39-cell pin could have silently tested the wrong band.
  minor (deferred): within one parametrized band case the three grades are checked in
  a plain loop, so simultaneous same-band multi-grade corruption surfaces one cell per
  rerun. Does not weaken the pin.
  minor (deferred): the assertion message's "(_SIZE_BANDS upper bound, probe N mm)"
  parenthetical reads as if the probe were the bound. Cosmetic.

T3: implemented (commit 4db2f8f). Suite 258 passed. Gate A exit 1, 6 PASS / 3 SKIP.
  Ladder unchanged. _MIN_WALL_MM 4.0 and _EDGE_MARGIN_MM 5.0 CONFIRMED UNCHANGED at
  layout.py:59-60 -- the diff there is docstring prose only.
  MUTATION CONTRAST: with _LITERAL_WALL_FLOOR_MM set back to the stale 3.7, EXACTLY
  ONE test failed -- the new guard, naming 3.7 >= (3.78 - 1e-09) -- while all nine
  other layout tests passed. That contrast is the finding: the old literal was blind.
  Implementer deviation (disclosed, sensible): added a 1e-9 epsilon to the new
  assertion, since 3.78 >= 3.7800000000000002 fails on float representation. Matches
  the epsilon style already used elsewhere in the file. Also corrected stale 3.55 /
  1.775 prose in a neighbouring docstring and in layout.py's trailing paragraph.

STATE: all 3 plan tasks complete + 1 fix round. Branch e8e4a9f..4db2f8f, 6 commits.
Suite 258 passed. Gate A exit 1 (6 PASS / 3 SKIP). Working tree clean.
NEXT: T3 review + whole-branch final review, both dispatched.

T3: review APPROVED with two follow-ups. The reviewer independently re-derived every
  load-bearing number from features.py / sampler.py / iso286.py rather than trusting
  the report -- 2.5 allowable (max over all 21 fastener/grade combinations), 1.34
  ladder hi, 0.215 growth, 1.890 excursion, 3.780 wall -- all correct. It also
  confirmed the 1e-9 epsilon deviation is necessary (the product genuinely does not
  land on 3.78 in float64), mirrors an existing pattern at test_layout.py:121, and
  loosens the bound by four orders of magnitude less than the ~0.03 mm gap the guard
  must catch, so it cannot mask a shortfall.
  T3-a [IMPORTANT, plan-mandated gap in the controller's brief] the new drift guard
    protects ONLY the wall literal. _LITERAL_EDGE_FLOOR_MM is still checked only
    against the production constant -- the exact style of check that let the wall
    literal go stale. If the edge literal ever goes stale the same way, nothing in
    the suite notices. A symmetric hole in precisely the bug class this task closes.
    The brief hoisted both literals but supplied verbatim code for only the wall test.
  T3-b [MINOR, CONTROLLER'S OWN ERROR] the "5.5% headroom" figure in layout.py's
    docstring uses a different denominator from the "12.7%" beside it. The sibling
    figure is excess-over-required: (4.0-3.55)/3.55 = 12.68%. The same formula on the
    new numbers gives (4.0-3.78)/3.78 = 5.82%, not 5.5%. 5.5% is excess-over-WALL,
    (4.0-3.78)/4.0. The controller computed it that way in the pre-plan impact
    analysis, wrote it into the plan, and it propagated verbatim into the docstring.
    Documentation only, conservative in direction (real headroom is larger than
    stated), but it is a wrong number now committed. Should read 5.8%.

---

FINAL FIX WAVE (one wave, no second): 4db2f8f..2621be5, 3 commits.
Full report: final-fix-wave-report.md in this directory.

  0459fe0 I-1 + M-8. Raised _LITERAL_WALL_FLOOR_MM 3.78->3.8 and
    _LITERAL_EDGE_FLOOR_MM 1.89->1.9 so both sit strictly ABOVE their derived
    requirements (3.78 / 1.890) and are conservative floors again rather than
    restatements of the derivation. The edge literal was verified to be already a
    ulp BELOW its requirement (1.89 < 1.8900000000000001), passing on the epsilon
    alone -- T3-a was not merely a structural gap, it had already bitten. Renamed
    the guard to test_the_literal_floors_are_not_below_the_derived_ones and gave it
    the mirrored edge assertion; epsilon kept on both. Corrected the 5.5% headroom
    to 5.8% (T3-b) and restated the sibling edge figure as 165% so both use
    excess-over-required. Production constants untouched.
    MUTATION PROVEN: _LITERAL_EDGE_FLOOR_MM=1.5 -> 1 failed, 9 passed, the new
    assertion the only failure.

  a92d812 I-2. iso286.py's docstring claimed twice that g/h/p are valid for grades
    "5-8 as currently tabulated"; _IT_MICRONS has held 5-8 and 12-14 since T1.
    Corrected both, and added a paragraph stating that the accepted set for g/h/p
    WIDENS whenever a row is added, so H12/g12, H13/h13, H14/p14 went from raising
    to returning a fit. Correct per ISO 286-1 Tables 4/5 (all standard grades), but
    an unannounced change to a checker-core public surface. Pinned acceptance of
    the three, rejection of H9/g9, and the surviving k IT4-IT7 restriction. No
    value, no logic change -- diff against 4db2f8f is docstring lines only.

  2621be5 I-3 + M5 + M6. sampler._tier1_mate had an inline -0.1/+0.0 fastener band
    with NO comment at all -- so the plan's "the only remaining untraced number is
    the tapped hole's" was false, with the schema about to be frozen publicly.
    Hoisted to _FASTENER_LOWER_DEV_MM / _FASTENER_UPPER_DEV_MM with the same
    declared-simplification treatment _TAPPED_HOLE_UPPER_DEV_MM got, including the
    inertness argument (external feature -> mmc = nominal + upper_dev = nominal;
    y14_5.fastener_assembles reads only .mmc). Pinned over every sampled Tier 1
    mate. Plan completion statement amended to name BOTH numbers. M5: reworded
    features.py's "all values are pinned" -- _TAPPED_HOLE_UPPER_DEV_MM is bounded,
    not pinned, deliberately. M6: added (10.0,"loose",0.43), the M10 band-boundary
    case where hole-diameter lookup (0.43) and fastener-diameter lookup (0.36)
    disagree.

VERIFICATION: suite 258 -> 266 passed (+8, itemised in the report). Gate A exit 1,
  6 PASS / 3 SKIP, unchanged. Ladder EXACT on all four levels: d1 19.5% (31/159),
  d2 32.9% (99/301), d3 52.9% (239/452), d4 69.1% (421/609). _MIN_WALL_MM 4.0 and
  _EDGE_MARGIN_MM 5.0 unchanged. Table immutability checked by SHA-256 over the
  JSON of _IT_MICRONS, _DEVIATION_MICRONS, _SIZE_BANDS, _CLEARANCE_HOLE_MM,
  TAPPING_DRILL_MM and _TOL_FRACTION_RANGE at HEAD vs a throwaway 4db2f8f worktree:
  364e7375ecbad327 both sides, identical. Working tree clean.

DEFERRED TO PRE-FREEZE FOLLOW-UP (unchanged, deliberately not done in this wave):
  pinning the 52 IT5-IT8 cells the way the 39 IT12-IT14 cells are pinned. Requires
  carefully re-reading 52 values off the primary-source scan; doing it badly is
  worse than not doing it. The asymmetry is now more visible than before, since the
  IT12-IT14 block sits directly above it in tests/test_iso286.py. Should close
  BEFORE the freeze, not after.

STATE: branch e8e4a9f..2621be5, 9 commits. Phase 3.5 pre-registration unblocked.
NEXT: human sign-off, then freeze.

=== FINAL WHOLE-BRANCH REVIEW (opus) + FIX WAVE + SCOPED RE-REVIEW ===
Final review: "ready to merge with fixes", 3 Important, 5 Minor. All three Important
CONTROLLER-REPRODUCED before dispatching the wave:
  I-1 the branch's flagship anti-staleness guard covered the WALL floor only, and
    _LITERAL_EDGE_FLOOR_MM was ALREADY below its derived requirement:
      derived 1.8900000000000001 vs literal 1.89 -> literal >= required is False.
    A ulp, harmless in magnitude, but the identical silent-floor pattern in a fresh
    instance, inside the very test written to close it.
  I-2 adding IT12-14 SILENTLY WIDENED a checker-core public API. Reproduced:
      H7/g6 ACCEPTED (as before); H12/g12, H13/h13, H14/p14 now ACCEPTED where they
      previously raised; H9/g9 still rejected. iso286.py's docstring still said
      g/h/p are valid for grades "(5-8 as currently tabulated)" -- false.
      The VALUES are correct (ISO 286-1 gives g/h/p for all standard grades), but
      the accepted input set changed as an unannounced side effect with no test.
  I-3 sampler.py's inline fastener "lower_dev": -0.1 was uncited AND uncommented --
    unlike the tapped-hole band it had no inertness argument at all. So the plan's
    completion claim that "the only remaining untraced number is the tapped hole's
    tolerance band" was FALSE, in a branch whose entire purpose is traceability.
  M8 was the CONTROLLER'S OWN ERROR: the "5.5% headroom" figure used a different
    denominator from the "12.7%" beside it. Sibling formula gives 5.8%. Computed in
    the pre-plan impact analysis, written into the plan, propagated to the docstring.

FIX WAVE (3 commits, 4db2f8f..2621be5): I-1, I-2, I-3, M5, M6, M8.
  Suite 258 -> 266 passed. Gate A exit 1, 6 PASS / 3 SKIP. Ladder bit-identical
  (19.5 / 32.9 / 52.9 / 69.1). No table or constant value moved; the ONLY executable
  change in the whole diff is sampler.py's constant hoist, value-identical.
  The fixer verified table immutability by SHA-256 over all six tables at HEAD and at
  a throwaway worktree of 4db2f8f -- 364e7375ecbad327 both sides.
CONTROLLER-VERIFIED: both literals now STRICTLY above their derived floors
  (1.9 > 1.890, 3.8 > 3.780), so the 1e-9 epsilon is no longer load-bearing;
  _FASTENER_LOWER_DEV_MM exists as a named constant; the docstring shows the formula
  "(4.0 - 3.78) / 3.78 = 5.8%"; _MIN_WALL_MM 4.0 / _EDGE_MARGIN_MM 5.0 unchanged.

SCOPED RE-REVIEW (opus): all six ADDRESSED, no new Critical/Important. It re-derived
  the margins, re-checked every headroom figure (5.8% / 5.5% / 165% all correct, and
  the ~2.6x -> 165% restatement is the same quantity), confirmed the diff to
  iso286/features/layout is docstring prose with ZERO executable lines, and walked all
  seven new tests naming a reachable failing mutation for each. No new test is
  incapable of failing.

PARKED after the re-review (no second fix wave per SDD; none load-bearing):
  R-1 [highest value, ONE LINE] the accepted-grade set is EMERGENT from _IT_MICRONS's
    contents, not declared. The new test catches IT9 specifically, but adding IT10,
    IT11 or IT15-18 would silently widen g/h/p again with a green suite. Fix:
    assert sorted(_IT_MICRONS) == [5, 6, 7, 8, 12, 13, 14]. SURFACED TO THE HUMAN in
    the finish options rather than parked silently.
  R-2 the fastener inertness test guards only the MMC-CONSTRUCTION half of its stated
    property. It proves an external feature's MMC ignores lower_dev; it says nothing
    about the verdict path continuing to read only .mmc. If y14_5 or checker._feature
    ever read .lmc or .min_size, -0.1 reaches a verdict and the test stays green.
    Verified true today (fastener_assembles touches .mmc and nothing else; build.py
    never references the fastener). y14_5 is frozen, so acceptable. Direct fix:
    mutate _FASTENER_LOWER_DEV_MM and assert corpus verdicts are byte-identical.
  R-3 the k IT4-IT7 restriction test covers only grades 12-14; widening the range to
    (4, 11) would pass green.
  R-4 [pre-existing, already ledgered] the 52 IT5-IT8 cells are not pinned the way
    the 39 IT12-IT14 cells now are. The controller deliberately deferred this:
    doing it means re-reading 52 values off the primary-source scan, and doing that
    badly is worse than not doing it. The asymmetry is now MORE visible, and IT7 is
    arguably more consequential since it feeds the Tier 2 iso_fit yields. Risk is
    bounded today -- the sampler draws iso_fit nominals 10/12/16/20/25, all in bands
    covered by existing spot checks. CLOSE BEFORE THE PUBLIC FREEZE.
  R-5 frozen-corpus constants outside the hashed six (SERIES_TOLERANCE_GRADE,
    FASTENER_SIZES, SUPPORTED_FITS, _ISO_FIT_NOMINALS_MM, _PLATE_THICKNESS_MM) are
    covered only behaviourally, by the ladder reproducing. A structural pin is cheap.
  R-6 two near-vacuous sub-assertions: the acceptance test's bodies (its real content
    is "does not raise"), and the grep guard's '"lower_dev": -0.1' not in text, which
    is evadable by writing -0.10 or reformatting. Neither test is vacuous overall.
  R-7 -0.1 IS published -- it round-trips into the sidecar fastener dict via
    AssemblySpec.to_json(). The claim "cannot move a verdict" is accurate, but the
    number is visible in the frozen benchmark data. Worth knowing at pre-registration.

STATE: 3 plan tasks + 2 fix rounds, all reviews closed. Branch e8e4a9f..2621be5,
9 commits. Suite 266 passed. Gate A exit 1 (6 PASS / 3 SKIP).

=== POST-MERGE CLEANUP (human asked for both before pre-registration) ===
R-1 and R-4 CLOSED. Commit 2ccb1c0, merged a2f2186 on master. Suite 266 -> 280.
  R-4: all 52 IT5-IT8 cells pinned, transcribed from the primary-source scan
    independently of src/ so it is a SECOND READING, not a restatement of the
    module's own values. Same argument that justified pinning the 39 IT12-IT14
    cells -- the human's 2026-08-01 verification of these lived only in a ledger
    sentence. IT7 was the consequential one: it feeds Tier 2 iso_fit yields
    through fit_from_designation, so a corrupted cell moves PUBLISHED NUMBERS,
    not just documentation.
  R-1: the tabulated grade set is now declared, not emergent.
    assert sorted(_IT_MICRONS) == [5, 6, 7, 8, 12, 13, 14].
  BOTH DEMONSTRATED FAILING BEFORE BEING TRUSTED:
    transposing IT7 bands 5<->6 (25 <-> 30 um) -> fails at exactly [5-40] and
      [6-65], correctly localised;
    adding an IT9 row -> trips the grade-set declaration.
    iso286.py restored byte-identical after each (git diff --stat empty).
  Ladder unchanged: d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%. Gate A exit 1.

REMAINING PARKED (R-2, R-3, R-5, R-6, R-7) are all non-blocking and recorded
above. None is load-bearing; R-7 in particular is informational -- the fastener's
-0.1 IS published in the sidecar even though it is inert.

*** THE GENERATOR IS NOW READY FOR PHASE 3.5 PUBLIC PRE-REGISTRATION. ***
master a2f2186. 280 passed. Gate A exit 1, 6 PASS / 3 SKIP.
Nothing may generate corpus data until the pre-registration is posted (spec 12).

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
