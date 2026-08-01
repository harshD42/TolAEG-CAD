# QA critique, Round 1 — 2026-08-01

Verdict: **adoptable with six amendments, not a rewrite.** Every attack below carries
file:line or executed output. Concessions are listed first so Round 2 does not waste
effort defending them.

## CONCEDED WITHOUT ARGUMENT (do not re-defend)
10 commits ahead / strict ancestor / clean fast-forward. **Zero src/ delta** (verified).
F2, F3, F5, F6, F7, F9, F10, F11, F12 all verified. B4 ACCEPT correct. B8 REJECT correct.
Merge-first is the right structural call. F1 is a genuine catch the inventory missed.
QA also withdrew a suspected cosmic-ray shell-quoting bug before raising it
(`cosmic_ray/testing.py:46` uses `shlex.split`).

---

## A1 [CRITICAL, NEW, BLOCKS PHASE 3] The frozen reliability mate set is broken and the
## frozen correction log states a false number about it. CONTROLLER-VERIFIED.

`scripts/gate_a.py:108` documents mate[8]'s margin as a SUM:
    `margin = (8.5-8.0)+(8.5-8.0) - (0.5+0.49965) = +3.5e-4`
`src/tolcad/y14_5.py:228` implements `margin = min(margin_a, margin_b)` — deliberately,
per ASME B-3's per-part rule, which the module documents at length.

`min(0.5-0.5, 0.5-0.49965) = 0.0`. The mate intended to sit at +3.5e-4 sits at EXACTLY
ZERO, falls inside the boundary band, and is silently excluded.

MEASURED: `tested=11, excluded=1` — not 12/0. Band is now asymmetric (2 positive, 3 negative).

FROZEN spec lines 227-228 state: *"at 12 tested mates the only values reachable near the
threshold are 1.0000 and 0.9167."* Both figures are wrong. Real per-seed values are
{0.9091, 1.0} over eleven tested mates. The plan commits to publishing §7 **verbatim** —
i.e. publishing a false statement about our own instrument, checkable in 20 seconds.

The guard written for exactly this class misses it: the branch's new
`test_gate_a_reliability_criterion_holds_for_the_real_measurement` asserts `tested > 0`,
which catches TOTAL degeneracy and misses PARTIAL degeneracy — and the partial degeneracy
is live underneath it. Fourteenth instance, on a PUBLISHED Gate A number, not telemetry.

Repairing mate[8] does NOT move the verdict:
    AS SHIPPED  mean=0.9982 CI=[0.9964,0.9995] tested=11 excluded=1
    REPAIRED    mean=0.9971 CI=[0.9946,0.9992] tested=12 excluded=0
So this is a bug fix to the instrument, provably not post-hoc tuning.

REQUIRED: new critical-path item before Phase 3 — fix the two contradicted comments, repair
or explicitly retire mate[8], pin tested/excluded, file a §7 correction replacing
"12 tested mates / 0.9167". Pre-data this is permitted; after pre-registration it is not.

## A2 [CRITICAL] P2.3 is unimplementable as specified
`commit_sha == HEAD` has NO FIXED POINT. CI runs at X, emits a receipt naming X; committing
the receipt produces Y; now HEAD==Y≠X and the row fails, forever. Untracked receipt → absent
in a fresh clone → SKIP, the state A3 exists to escape. Live API fetch → Gate A needs network
and a GitHub account, a worse dependency than the SolidWorks one F6 complains about.
WORKABLE FORM: receipt's commit_sha is an ANCESTOR of HEAD and `git diff --name-only
<sha>..HEAD` touches nothing under src/, tests/, scripts/, pyproject.toml.
Also: P2.3 amends a SECOND frozen document — suite-integrity design §8 states "Gate A remains
untouched and still reports 6 PASS / 3 SKIP". Budget two amendments, not one.

## A3 [MAJOR] R2's depth cap does not parse, prohibits committed controls, and the
## "teeth" argument is invalid
Two readings, both of which prohibit `test_the_registry_still_covers_every_critical_guard`
— committed on the branch being merged, and the very mechanism B4 ACCEPTs. Also prohibits
`test_both_expectation_directions_are_exercised` and `test_every_registry_name_is_unique`.
R2 is invoked EXACTLY ONCE (to reject B2) while B2's two committed siblings
(`test_a_persistent_write_failure_is_raised_not_swallowed`,
`test_a_transient_write_failure_is_retried_then_succeeds`) sit at the same depth unquestioned.
THREE depth-3 defects in the history had ALREADY FIRED: the ulp edge-floor; the
`"".join(["x"])` no-op found by hand-verifying triage claims; and B3 itself — which R2
forbids and P1.5 then reinstates one line below.
TEETH ARGUMENT IS WRONG TWICE: (a) the arithmetic is 4 FIX / 4 ACCEPT / 3 REJECT / 1
FIX-LATER, not 4/5/3; (b) any rule with ≥2 outputs on a heterogeneous list yields a
non-uniform distribution. Diagnostic pattern: EVERY fix lands on something the plan calls
"a one-liner"; EVERY accept/reject lands on something expensive. That is a rule fitted to a
preference ordering.
The rule DOES have teeth unused: R1 honestly applied forces O1 and forces P1.1 to pin all
four ladder levels.

## A4 [MAJOR] F2 understated — a live 19-point silent hole at d2/d3, demonstrated
The monotonicity guard bands only `rates[0]` and `rates[-1]`; d2 and d3 have NO band. The
`flat-difficulty-ladder` registry entry targets the d4 row, so it misses d2/d3 too.
EXECUTED, mutating only `_TOL_FRACTION_RANGE[2]`:
    (0.70,1.24) -> d2 becomes 52.16% vs published 32.89%   GUARD PASSES
    (0.70,1.20) -> d2 becomes 43.85%                        GUARD PASSES
    (0.60,1.10) -> d2 becomes 19.27%                        GUARD PASSES
30 of 35 candidates moved a pre-registered number by up to 19.3pp with every guard green.
(QA confirmed the guard is not useless: three flatter ranges WERE caught.)
REQUIRED: P1.1 pins ALL FOUR exact counts; the registry needs a declared mutation on a
MIDDLE row.

## A5 [MAJOR] B7's REJECT is right; its substitute disclosure is wrong and violates R6
CONCEDED: retuning `_RELIABILITY_MATES` after seeing the sweep would be post-hoc tuning, and
correction 2026-08-01e independently forbids it ("the mate set stays fixed").
BUT the proposed disclosure is three bare point estimates. Measured with a 10,000-resample
bootstrap over the 200 pre-registered seeds:
    k=1.0  0.9982  CI[0.9964,0.9995]  not caught
    k=1.5  0.9791  CI[0.9732,0.9850]  not caught      <- largest unambiguous NOT-caught
    k=2.0  0.9518  CI[0.9427,0.9605]  CI STRADDLES 0.95 -> INDETERMINATE
    k=2.5  0.9264  CI[0.9159,0.9368]  caught          <- smallest unambiguous caught
    k=3.0  0.9068  CI[0.8950,0.9186]  caught
"k=2 is not caught (0.0018 margin)" is a POINT-ESTIMATE claim whose CI contains the
threshold — precisely what correction 2026-07-31c forbids ("point estimates reward noise").
Also 0.0018 is 0.02 of a mate: with tested=11, per-seed values quantise at 1/11 = 0.0909.
Presenting rounding as a margin.
REQUIRED: state the bound as "reliably detects ≥2.5x, reliably fails to detect ≤1.5x,
indeterminate at 2x". ~20 min compute. Not a retune; instrument untouched.

## A6 [MAJOR] Merge premise verified, inference wrong — after merge, plain `pytest` writes to src/
`tests/test_declared_mutations.py:22-25` parametrises over all eleven entries with no skip;
the design spec boasts the layer "runs in every pytest invocation". So on main, the documented
default command mutates `iso286.py`, `reliability.py`, `sampler.py`, `layout.py`, `features.py`
and a tracked fixture, then restores them.
TWO LIVE HAZARDS: (a) B10 ALREADY FIRED — `mutation_registry.py:38-45` records an OSError on
the RESTORE write leaving `reliability.py` mutated, "once in roughly a dozen runs", on the
default command. (b) `scripts/gate_a.py:287` shells out to `_pytest_passes("tests/test_reliability.py")`
in a fresh interpreter reading that file FROM DISK. Run pytest and gate_a concurrently and
Gate A can report a reliability figure measured against a MUTATED checker — a published number
corrupted by a mechanism the merge introduces. The concurrency banner exists only for cosmic-ray.
REQUIRED: P1.7 moves into PHASE 0, before the push. Concurrency warning into CLAUDE.md same
commit. Restate the rationale: "zero production delta, NON-ZERO RUNTIME FOOTPRINT, mitigated
by a depth-0 cleanliness control landing in the same phase."

## A7 [MAJOR] P1.5 cannot be parallel, and re-pinning re-creates F1's class
P1.5 is tagged [par] beside four items that edit tests/ and scripts/, but BLOCKERS.md's hard
constraint says cosmic-ray is never concurrent, and P1.5's own text says "one run, alone".
It is two 25-min serialised runs plus triage of an unknown survivor set (ledgers give ~12,
~17, and — implied by 95.89% — ~27 for the same quantity). Phase 1 is not 1-2 days with it.
BOTH FLOORS ARE ONE-SIDED (`score >= FLOOR`). An improvement is never flagged, so the constant
silently detaches the moment the next test lands. P1.5 re-pins and thereby RESTORES the exact
condition that produced F1. The comment says "raising is routine" — but nothing makes you,
and the plan's own R5 says awareness has demonstrably failed as a control.
REQUIRED: make both checks TWO-SIDED — fail when `abs(measured - PINNED) > TOLERANCE`, with a
distinct upward message. ~10 lines; closes F1's CLASS, not its instance.

## A8 [MAJOR] F7 substantiated and WORSE; F6+F7 compose into a structural fact
All 17 AP242 files are SINGLE PARTS (NEXT_ASSEMBLY_USAGE_OCCURRENCE count 0 in every one).
`data/nist_pmi_expected.csv` does not exist; the only `assembles` data anywhere is a two-row
fixture invented inside a unit test. NIST publishes PMI ANNOTATION SEMANTICS (11 cases, 421
annotations) — no fit, clearance or assembles verdict for any case. "Decidable case", the
predicate in the FROZEN §7 threshold, is defined nowhere; with it undefined a zero-case
denominator trivially satisfies "100% on decidable cases".
THE CORRECTION THAT MAKES IT WORSE: NIST's download page states in prose that FTC 07/08/09/10
fit together and CTC 02/04 do. That is design intent, not published ground truth, not in the
fetched archive, and UNIFORMLY POSITIVE — six cases, all True, zero negatives. A ground-truth
column derived from it, scored against the frozen 1.00 threshold, would be cleared perfectly
by a checker hard-coded to `return True`. Worse than no oracle: it manufactures a Gate A PASS
that discriminates nothing.
F6+F7 COMPOSE: §7's Gate A has exactly two external-oracle rows. TolAnalyst is licence-gated;
NIST has no ground truth. **Gate A, marked blocking, is currently unclearable by any route** —
blocking Gate D, blocking Paper 2. This is ONE structural fact, first on the decision agenda.
THREE HONEST OPTIONS: (1) split the criterion — NIST as PMI-EXTRACTION oracle against the
published 421 annotations (real, citable, licence-free, but validates the reader not the
decision, and needs FCF contents not just counts); (2) NIST MTC / box assembly with CMM data —
ships separately, you would be DERIVING the verdict and must publish the derivation; (3) state
the limitation: no public assemblability oracle exists.

---

## OMISSIONS both documents missed

**O1. Two of Gate A's six PASSes are human attestations, and criterion 1 was silently
substituted.** `gate_a.py:315-329` records "Y14.5 citation verified" and "ISO 286
transcription verified" as PASS iff a marker string is ABSENT from source — the code labels
them "unfalsifiable pass conditions until a human checks". Separately `gate_a.py:270-276`
RENAMED §7's criterion 1 from "Agreement with published Y14.5 worked examples" to "Y14.5
self-consistency", noting it is "arithmetic derived from the same two unverified formulas the
implementation uses". So §7 criterion 1 is measured by nothing and its substitute counts as a
PASS. "6 PASS / 3 SKIP" reads as six measurements; it is three. And the guard is circular:
`tests/test_gate_a.py:105-109` re-derives the expectation from the same input with the same
rule — the "assertion restates the code" shape from the design spec's own taxonomy.

**O2. The spec's "all eleven instances are caught" is false; three CANNOT be caught by the
shipped design.** Instance 10 (case-sensitive guard) has NO registry entry, though the spec
lists it among Layer 3's seven — the IDENTICAL mistake as the SI-2 finding, still open, in the
same document. Layer 1 CANNOT catch instances 5 or 6: coverage is scoped to six modules under
src/tolcad, but instance 5 lives in tests/ and instance 6 in scripts/. The spec's distribution
sums to 12 catches over 11 instances. Instance numbering contradicts across ledgers.
C1 must amend the design spec's §8 SUCCESS CRITERION, not just the map's vocabulary.

**O3. R5's premise is false and inverts its own evidence.** Classified at DISCOVERY, not
proof: executed mutation 1/11; executed non-mutation measurement 2/11; **code review reading a
diff or source 5/11**; self-review 1/11; doc-vs-artifact cross-check 2/11. Ten of eleven were
found by an adversarial reader asking the question over a diff. Five got an executed mutation
afterwards as PROOF OF FIX — conflating that with discovery is the error. NONE of the eleven
was found by the Layer 1/2/3 machinery. The record supports "commission a hostile review" at
least as strongly as "execute the mutation".

**O4. F3's blast radius is three published numbers.** `default_rng` drives the sampler (the
ladder), montecarlo (EVERY Tier 2 verdict AND Gate A's frozen ±0.5%-at-N=100k convergence
criterion), and verdict_stability (the 0.9982 mean). ALTERNATIVE THE PLAN DOES NOT SURFACE:
NEP 19 guarantees the legacy RandomState stream in perpetuity; switching makes all of it
unconditionally reproducible. Cost: all four ladder counts change — zero today, permanent
after Phase 3. Belongs on the decision agenda because it is the last moment it can be taken.

**O5. F11 collides with B7 verbatim.** The instance-map test bans the string "not caught";
the B7 disposition requires disclosing that 2x IS not caught. The two dispositions forbid
each other.

**O6. `_TAPPED_HOLE_UPPER_DEV_MM` is unguarded while its twin is guarded.** QA verified
inertness empirically (0.0 or 5.0 changes zero verdicts over 120 seeds x 4 difficulties), but
no test imports it and there is no registry entry. Its twin has both. The pre-registration
names them as equals — publishing two claims of which one has an executed guard. Under R1
that is a coverage gap; closing it is one registry entry.

**O7. Ledger hygiene.** The pre-fix d4 rate is recorded two incompatible ways in the same
file (0/0/0/69.1% vs 478/609 = 78.5%). "~17 untriaged" is derived as 40−23 in the same round
that corrects equivalents to 19 (giving 21); the file says both "roughly a dozen" and "~17"
three pages apart. Coverage has four recorded values, the mutation score seven. Gate D
requires every claim traceable to a logged run; the logs disagree with themselves on nearly
every quantity. Committing .superpowers preserves the contradictions. Budget a reconciliation.

---

## SIX REQUIRED AMENDMENTS (priority order)
1. New critical-path item for A1 (reliability mate + §7 correction) BEFORE pre-registration.
2. Redesign P2.3 (ancestor-plus-clean-paths); budget the second frozen-doc amendment.
3. Restate or drop R2 with a worked depth assignment for every control in the tree; correct
   R5's premise to adversarial review; delete the distribution-as-teeth argument.
4. Widen C1 to amend design spec §8's success criterion; reconcile the F11/B7 string collision.
5. Sequencing: P1.7 to Phase 0; P1.5 re-tagged serialising and on the critical path; both
   floors two-sided.
6. Promote F6+F7 to one top-of-agenda item ("Gate A is currently unclearable by any route")
   with the three oracle options; amend B7's disclosure to the CI-bounded 1.5x-2.5x form.

## COST
"Three days and one decision session" is NOT credible. P1.5 alone serialises most of a day
and blocks every parallel item; A1 and the ledger reconciliation are new; B9 is not a
one-liner (removing whole-file CRLF normalisation breaks every text anchor by the runner's own
design, so the fix is match-on-normalised / patch-original-bytes); and the decision session
must resolve an oracle strategy, a threshold contradiction, and an RNG commitment that is
irreversible after Phase 3. **Five to six days, decision session in at least two sittings.**
