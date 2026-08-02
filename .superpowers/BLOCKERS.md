# Complete open-item inventory, 2026-08-01

Compiled by the controller for the architect pass. 17 items. Verified against
the four SDD ledgers under .superpowers/sdd/ and the repo state at this commit.

## Repo state
- Remote: https://github.com/harshD42/TolAEG-CAD (created 2026-08-01, both branches pushed)
- `main` @ cedd86a  |  `feat/suite-integrity` @ 7979396 (UNMERGED, 8 commits ahead)
- On the feature branch: 376 tests pass. Gate A exit 1, 6 PASS / 3 SKIP.
- Tier 1 difficulty ladder, seeds 0-199: d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%
- Layer 1 coverage floor 94.12%. Layer 2 mutation: MEASURED 93.85, TOLERANCE 0.50, FLOOR 93.35.

## A. Blocks publication (5)

A1. Gate A SKIP - NIST PMI conformance. Needs a verdict CSV comparing our checker
    against NIST decidable cases. The AP242 *read* path exists and is verified
    (47/27/59 on ftc_06); the comparison corpus does not exist. Phase 4 work.
A2. Gate A SKIP - TolAnalyst agreement, >=95% over >=500 Tier 2 assemblies.
    Needs the human's SolidWorks access. Black-box oracle; report agreement only,
    never internals (IP constraint).
A3. Gate A SKIP - "Fresh clone, no SW licence, full pipeline runs end-to-end".
    NOW UNBLOCKED: a remote exists. Needs a CI workflow. Also the ONLY mechanism
    that can validate the .gitattributes binary-fixture rule, since CRLF
    normalisation is only observable across a fresh clone.
A4. Phase 3.5 PUBLIC PRE-REGISTRATION. Spec section 12: must be timestamped
    BEFORE any corpus generation. Blocks A5 entirely. Needs human decisions, not code.
A5. Phases 4-6: corpus, >=8 baselines, E1-E5, Gates B/C/D. Blocked by A4.

## B. Suite-integrity quality items, block nothing (12)

Small work:
B1. ~12 run-3 mutation survivors UNTRIAGED. Recorded as UNTRIAGED in three places,
    not absorbed. Needs one cosmic-ray run (~5 min) plus triage.
B2. run_declared_mutation's OSError -> AssertionError conversion is UNTESTED.
    Only the lower-level _write_bytes_resiliently retry has coverage. An untested
    error branch inside the module built to catch untested branches.
B3. No post-triage verification that the survivor set ACTUALLY shrank by the
    claimed amount. Proposed by the fix agent; nothing currently prevents another
    false-kill claim.

Accepted design limits (documented in code):
B4. _CRITICAL_GUARDS can be defeated by ONE joint commit removing an entry and its
    name together. Paper-trail mechanism, not technical. Design spec section 9.
B5. expect="pass" cannot detect a SEMANTICALLY INERT mutation. __post_init__ only
    rejects find == replace; it cannot verify the mutation reaches a code path the
    target test exercises.
B6. mc-seed-base-shifted is a narrow TRIPWIRE for an H7/h6 reintroduction, not a
    general closure of the seed-fishing class. Now honestly documented.
B7. Gate A reliability headroom is 2-3x, not eliminated. k=2 gives 0.9518 and is
    NOT caught (0.0018 margin); k=3 gives 0.9068 and is. Historical instance 4 is
    IMPROVED, NOT CLOSED. Any instance map must say so.

Cosmetic / theoretical:
B8.  _uninterned duplicated across three test files; must not drift.
B9.  _count_and_apply normalises CRLF->LF across the WHOLE file, not just the anchor.
B10. Restoration is exception-safe but not crash-safe (SIGKILL mid-write).
B11. Nothing enforces function-level test selectors in registry entries.
B12. ~84% of iso286 mutation kills are mechanical table pinning rather than
     behavioural assertions. Legitimate but weaker; the "252 kills" headline
     overstates behavioural depth. (Corrected to 256 killed / 19 equivalent.)

## C. Unstarted
C1. SI-5: CI workflow + the eleven-historical-instance coverage map. Partially
    closes A3. The map must be VERIFIED, not asserted -- a map claiming coverage
    it lacks would itself be the defect this branch exists to eliminate.

## Hard constraints any plan must respect
- Gate A/B/C/D thresholds in design spec section 7 are FROZEN. scripts/gate_a.py untouched.
- Checker core (types, y14_5, iso286, montecarlo, checker, reliability) stays numpy-only.
- validation/ is one-directional; core may never import it.
- No research corpus before A4.
- No value may change in _IT_MICRONS, _DEVIATION_MICRONS, _SIZE_BANDS,
  _CLEARANCE_HOLE_MM, TAPPING_DRILL_MM, _TOL_FRACTION_RANGE, _MIN_WALL_MM, _EDGE_MARGIN_MM.
- cosmic-ray mutates the working tree IN PLACE. Never concurrent with anything else.
- Every headline number must reproduce with no SolidWorks licence.

## The project's documented dominant failure mode
Eleven historical instances of "the test or metric that cannot fail", plus several
found while building the detector itself, including four tests that could not fail
INSIDE the anti-vacuity layer. Awareness has demonstrably failed as a control: the
pattern was in memory and in every review prompt and three new instances still landed.

## RECONCILIATION NOTE, appended 2026-08-01 by close-out Task 8 (APPEND-ONLY)

This inventory is a frozen record of the repo state at the commit named above and
is NOT REWRITTEN. Four of its figures have since been superseded:

- line 10, the ladder, still holds (d1 19.5 / d2 32.9 / d3 52.9 / d4 69.1) and is
  now pinned executably by `tests/gen/test_ladder_pin.py`.
- line 11, `coverage floor 94.12` and `MEASURED 93.85 / FLOOR 93.35`: superseded.
  Both pins are now TWO-SIDED at COVERAGE_MEASURED 94.74 and MUTATION_MEASURED
  95.89, tolerance 0.50 each. The current tree measures mutation 100.00, which the
  two-sided pin correctly reports as FAIL; that is the control working and it must
  NOT be re-pinned outside P1.5.
- B1's `~12 untriaged survivors`: superseded and unsourced. The last enumerated
  count is 21 at run 3; the current count is unknown.
- line 78's `Eleven historical instances`: superseded. The design spec's section 1
  table enumerates TWELVE; section 8's distribution omits the Unencoded row.

Canonical values, provenance, and the reason each figure was superseded:
`docs/superpowers/specs/2026-08-01-ledger-reconciliation.md` (tracked).
The stopping criterion's worked observation table, previously existing only in an
agent transcript: `docs/superpowers/specs/2026-08-01-observation-assignment.md`.
