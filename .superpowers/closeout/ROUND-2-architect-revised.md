# Architect Round 2 — revised plan. What changed and what is still contested.

Full reasoning is in the agent transcript; this is the operative record.

## CONCEDED WITHOUT DEFENCE
A1 (reliability mate[8]), A2 (`commit_sha == HEAD` has no fixed point), A6 (post-merge
pytest writes to src/), A4 (F2 understated — d2/d3 hole), A5 (point estimates violate R6),
A7 (P1.5 not parallel; floors one-sided), O2, O3, O5, O6, O7.

## THE DEPTH CAP IS WITHDRAWN
R2's depth cap did not parse, prohibited three controls committed on the branch being
merged, and contradicted P1.5 one line below. The "distribution proves teeth" argument is
deleted as rhetoric with wrong arithmetic (4/4/3/1, not 4/5/3).

REPLACED BY **THE CLOSED OBSERVATION SET** — exactly four scheduled observations, and that
closure is the terminating device:
  O-A  full suite pass/fail on a clean checkout
  O-B  working-tree cleanliness after every suite run
  O-C  two-sided exact pins on every published number
  O-D  adversarial review at named checkpoints, by a reader who did not write the thing

  R1 Coverage: every published number has a named guard WATCHED FAILING, with recorded
     output, via a registry entry. Applied honestly this forces N-7 and forces all four
     ladder levels to be pinned — QA was right that R1 had unused teeth.
  R2 Termination: a control needs its own control ONLY IF its failure is a SILENT FALSE
     GREEN and none of O-A..O-D reveals it. **To add a control you must name the
     observation that fails to reveal the defect.** The regress terminates because the
     list is closed; extending it is a human decision recorded in the design spec.
  R3 Loud beats guarded. R4 Prefer artifact observation over guarding the guard.
  R5 CORRECTED — layers ratchet, review discovers. Zero of eleven found by layers 1-3.
     A new layer is justified only when a defect review already caught COMES BACK.
     O-D must be scheduled and budgeted like any other control (new item N-11).
  R6 Disclose with a measured bound AND a CI where the quantity is stochastic.

A worked observation-assignment table is provided for every control in the tree, which is
what QA demanded and what makes the rule checkable line by line.

## ARCHITECT PUSH-BACK (three places)
P-1 **O1 OVERSTATES.** §7 criterion 1 IS measured. Verified by collection:
    test_b3_worked_example_boundary_case_assembles,
    test_b4_worked_example_boundary_case_assembles,
    test_b4_worked_example_unequal_split_boundary_case_assembles.
    QA is right the row was RENAMED and the criterion silently substituted, and right that
    two rows are attestations inside a "6 PASS" count. Wrong that it is unmeasurable.
    Consequence is BETTER than either document proposed: restore criterion 1 as its own row
    pointing at those three node IDs (a genuinely measured criterion — a strengthening),
    keep self-consistency as separate informational, and label attested rows attested.
P-2 The B9 attack targets a fix the architect did not propose (suffix allowlist, not
    removing normalisation). QA's costing of the real fix at 15-25 lines is ADOPTED, and
    that fix is now explicitly NOT scheduled (B9 ACCEPT under R3); the 3-line suffix guard
    is scheduled and honestly described as bounding blast radius, not fixing B9.
P-3 "Fitted to a preference ordering" is falsified by B1/B3 — at 1.5 serialised days it is
    the most expensive B-item and was ruled FIX in both rounds. But the distribution
    argument is deleted regardless; QA's logic is unanswerable.
P-4 O2's "12 catches over 11 instances" is not itself a defect (overlap is expected). But
    the architect found a STRONGER version independently: **the design spec §1 table
    enumerates TWELVE shapes while the document claims eleven instances** — the likely root
    of the cross-ledger numbering drift.

## NEW FINDING THE ARCHITECT ADDED
**The mate[8] repair is NOT UNIQUE.** QA measured 0.9971; the architect measured 0.9967
with hole_a.position_tol = hole_b.position_tol = 0.49965. Both satisfy "margin = +3.5e-4
under min()". The construction must be SPECIFIED in the §7 correction, not just the
outcome. Until agreed, no repaired number may be quoted. (Decision D-D.)

## DECISION AGENDA FOR THE HUMAN (two sittings)
D-A **Gate A oracle strategy — first; everything waits on it.** Three options:
    (1) split the criterion, NIST becomes a PMI-EXTRACTION oracle against the published 421
        annotations — real, citable, licence-free, but validates the reader not the decision,
        and needs FCF contents not the 21/6/11 counts we read today;
    (2) NIST MTC / box assembly with CMM data — ships separately, we would be DERIVING the
        verdict and must publish the derivation;
    (3) state the limitation: no public assemblability oracle exists.
    ARCHITECT RECOMMENDS 1 + 3. Explicitly warns against 2 under time pressure: the
    uniformly-positive page-prose variant would manufacture a Gate A PASS that discriminates
    nothing.
D-B Is TolAnalyst blocking for Gate A? §4.3 and §7 prose say clearable licence-free; the §7
    table and gate_a.py say otherwise. Pick one in writing.
D-C **RNG commitment — irreversible after Phase 3.** default_rng drives the sampler (ladder),
    montecarlo (EVERY Tier 2 verdict AND Gate A's frozen +-0.5% convergence criterion), and
    verdict_stability (0.9982). ARCHITECT RECOMMENDS PIN, DO NOT SWITCH — switching burns a
    day at the worst moment, invalidates every ledger figure, and puts a soft-deprecated API
    in a 2026 artifact; Gate D already allows +-1% for sampled quantities. HOLDS LOOSELY.
D-D Which mate[8] repair construction (see above).
D-E How many pre-data frozen-document amendments. Architect counts FIVE, not QA's two:
    fresh-clone estimator; reliability mate + the false "12 tested / 0.9167"; NIST
    operationalisation; TolAnalyst optionality; suite-integrity §8's success criterion.
    Architect argues file all five — a long pre-data correction log is a credibility asset;
    a short one bought by leaving false statements in place is not.

## SEQUENCE (Phase 0 changed materially)
Phase 0 (1 day) — merge; **P0.2 tree-cleanliness control IN THE SAME COMMIT, before push**
  (it guards the hazard the merge introduces); **P0.3 re-pin BOTH floors TWO-SIDED**
  (re-pinning without two-sided restores the defect); P0.5 ledger reconciliation BEFORE
  committing .superpowers; LICENSE; README.
Phase 1 (3-3.5 d) — N-1 reliability repair [CP]; P1.1 four exact counts + digest + recipe +
  MIDDLE-ROW registry entry [CP]; P1.2 numpy pin [CP]; D-A/D-B encoding [CP];
  **P1.5 [SERIALISING, 1.5 d — nothing may edit src/ OR tests/, cosmic-ray reads both from
  disk]**; P1.6 clone test; P1.8 two meta-guards; N-7 guard the tapped-hole constant; P1.9.
Phase 2 (1-1.5 d) — P2.1 CI two jobs (ubuntu+windows matrix, windows sets autocrlf=true;
  integrity job on workflow_dispatch+weekly ONLY, per F12); **P2.3 receipt redesigned:
  ancestor-of-HEAD + `git diff --name-only <sha>..HEAD` touches nothing under src/, tests/,
  scripts/, pyproject.toml OR .github/workflows/ + both exit codes 0. Honest ceiling stated
  in the row: this is a SELF-REPORT; printing the workflow URL makes it checkable by a third
  party, not enforced.**; N-5 Gate A measured-vs-attested split + restored criterion-1 row;
  P2.4 instance map + §8 amendment + missing instance-10 entry.
Phase 3 — pre-registration. Phase 4 — corpus, UNESTIMATED.

## ELEVEN NEW ITEMS N-1..N-11. TOTALS: 28 items.
FIX NOW 15 · FIX LATER 2 · ACCEPT AS RESIDUAL 5 · REJECT 3 · DECISION 3.
(No claim is made that this distribution demonstrates anything — see P-3.)

N-11 is the highest-leverage item in the document: **schedule and budget adversarial review
as a deliverable** with named checkpoints (before pre-registration; before each published
number enters a draft; before Gate D). This exchange is an instance of that control and it
found A1 in one pass.

## B7 DISCLOSURE, NOW CI-BOUNDED (Round 0's three bare point estimates withdrawn)
  k=1.0  0.9982  CI[0.9964,0.9995]  not caught
  k=1.5  0.9791  CI[0.9732,0.9850]  largest unambiguous NOT-caught
  k=2.0  0.9518  CI[0.9427,0.9605]  CI STRADDLES 0.95 -> INDETERMINATE
  k=2.5  0.9264  CI[0.9159,0.9368]  smallest unambiguous caught
  k=3.0  0.9068  CI[0.8950,0.9186]  caught
Bound: "reliably detects >=2.5x; reliably fails to detect <=1.5x; indeterminate at 2x."
Re-measure after N-1 (tested becomes 12, quantum 1/12). Instance 4 is PARTIAL, not CAUGHT.

## C1 INSTANCE MAP — the string ban is deleted (it banned what B7 requires)
Closed vocabulary per row, with a non-empty evidence cell; PARTIAL rows must carry a numeric
bound: CAUGHT (name the artifact) / PARTIAL (artifact + measured bound) / **FIXED-NO-LAYER**
(fixed and guarded by a specific test, but no layer covers it — instances 5 and 6, since
Layer 1's coverage is scoped to six modules under src/tolcad while those live in tests/ and
scripts/) / ACCEPTED (name the ruling). The sibling `assert f"| {n} |" in doc` is also
replaced — it passes against eleven rows of "TODO".

## PRE-REGISTRATION — key change
"Publish §7 verbatim" is WITHDRAWN. Lines 227-228 state a falsehood about our own instrument.
Publish the tables PLUS the corrections, with superseded text shown. Also: state the
per-part min() form explicitly, because mistaking it for a sum is exactly what produced A1.
Item 26 now discloses that the anti-vacuity layer **has never discovered an instance and is
a recurrence ratchet, not a detector.**

## COST — CONCEDED
5.5-6 engineering days plus two decision sittings. Bottom-up table provided. Two
underweighted drivers: P1.5 serialises the whole repo for 1.5 days, and N-1 plus the ledger
reconciliation are new work that did not exist in Round 0.

## RESIDUAL DISAGREEMENTS, with what would settle each
D-1 the repaired mean (0.9967 vs 0.9971) — settled by agreeing the construction (D-D).
D-2 RNG pin vs switch — human judgement; architect holds its position loosely.
D-3 five pre-data amendments vs two — editorial, human's call.
D-4 D-A itself — no amount of engineering settles it.

## WHERE THE ARCHITECT INVITES ROUND-3 ATTACK
1. P2.3's receipt is a SELF-REPORT; ancestor+clean-paths prevents staleness, not forgery.
   "If you disagree, say what enforcement you would accept."
2. R2's closed observation set is a STIPULATION — governance dressed as a rule. Defence:
   every termination argument bottoms out in a stipulation; this one is explicit,
   enumerable, and requires naming which observation fails before a control may be added.
3. N-11 has NO COST ESTIMATE, and it is the highest-leverage item.
4. Phase 4 remains unestimated.
