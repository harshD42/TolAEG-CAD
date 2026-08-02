# Staleness Audit and Repair of Tracked Documentation

**Status:** completed 2026-08-01, against `main` @ `30eb333`.
**Scope:** the tracked design specs, implementation plans, `BLOCKERS.md`, the literature
index, the NIST fixture provenance note, and `CLAUDE.md`. Records no new measurement except
where a figure is explicitly marked *measured here*.
**Canonical values for every contested quantity:**
`docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`. Where this file and that one
appear to disagree, that one is live.

## 0. Method, and the rule that governed every repair

The project's dominant failure mode is the test or metric that cannot fail. The documentation
analogue is the **statement that cannot be wrong** — a figure with no provenance, in a file
nobody re-reads, which is quietly carried into the next document. This audit sweeps for those.

Two repair modes, chosen per file and never mixed:

- **Approved specs** get an **appended, dated, numbered amendment** that quotes the superseded
  text and states why it was superseded. The precedent is design-spec amendments `2026-08-01f`
  and `2026-08-01g`; this audit matches their form and continues their letter sequence, so no
  two amendments in the project share an identifier. The original text is never overwritten.
- **Working documents** (plans, `BLOCKERS.md`, provenance notes) get a direct correction where
  the line is a *pointer*, and an **appended annotation** where the line is a
  *contemporaneous record of what was believed at the time*. Executed plans are records; their
  task bodies and acceptance criteria were not edited.

**Nothing frozen was touched.** `CLAUDE.md` freezes the pre-registered Gate A/B/C/D thresholds
in design spec §7. No value in §7 changed, and the corpus-count correction was deliberately
placed in a **new §14** rather than in §7's correction log, precisely because appending there
would have forced an edit to §7's frozen sentence *"All seven predate any experimental data."*

**No constant, threshold, seed set or exclusion band was changed. Nothing was staged or
committed.**

**What this audit did not do.** It did not run `pytest`, `scripts/gate_a.py` or
`scripts/check_suite_integrity.py`. The concurrency rule in `CLAUDE.md` forbids running the
suite while other processes read `src/`, and other agents were writing concurrently. The
handed-down verified state (428 tests, Gate A 7 PASS / 0 FAIL / 3 SKIP) is therefore **relied
on, not reproduced**, except where §4 below says otherwise. Only
`tests/test_observation_assignment.py` was run, because this audit edits the document that
test parses.

---

## 1. Defects found and fixed (22)

### 1.1 `docs/superpowers/specs/2026-08-01-suite-integrity-design.md` — 5 defects

Repaired by a new **§10 Amendments** section carrying `2026-08-01i`, `j` and `k`, plus a
forward-pointer under the Status line so a reader entering at §1 knows the amendments exist.

| # | Line(s) | Superseded text | Amendment |
|---|---|---|---|
| D1 | 7, 73, 139, 140 | the instance count **eleven** — §1 prose, §4's Layer 3 note, §8's first success criterion, and §8's `2 + 3 + 7` distribution | `2026-08-01i` (the C1 amendment) |
| D2 | 143 | *"Gate A remains untouched"* | `2026-08-01j` |
| D3 | 143 | *"and still reports 6 PASS / 3 SKIP"* | `2026-08-01j` |
| D4 | 39 | *"Full suite at time of writing: **280 passed**"* | `2026-08-01k` |
| D5 | 38, 52, 112 | *"There is no CI and no git remote"*, plus the two *"dormant until a remote exists"* caveats it licenses | `2026-08-01k` |

**D1 is the C1 amendment that was owed.** §1's *table* enumerates twelve — Insensitive 4,
Tautological 2, Unreachable 2, Drifted 2, Structurally impossible 1, Unencoded 1 — and the
table is the enumeration of record. §8's distribution names **eleven distinct** instances and
omits exactly one: the **Unencoded** row, the 39-cell IT table check run once in a shell and
never committed. Verified row by row against
`docs/superpowers/specs/2026-08-01-observation-assignment.md` §4.

That omission is not an arithmetic slip. Unencoded is **the only one of the twelve no layer
can catch**, because no layer can observe a verification that left no artifact — so a coverage
map built by walking the three layers was always going to drop precisely that row, and a
success criterion asserting full coverage was itself an instance of the defect the document
exists to prevent. The amendment also records two consequences: refer to instances **by name,
not by number** (only positions 2, 3, 4, 5, 6 and 10 are attested anywhere), and instances
**5** and **6** are **FIXED-NO-LAYER** — they live in `tests/` and `scripts/`, outside Layer
1's six-module scope, so §8 credits Layers 1 and 2 with catches they structurally cannot make.

**D2/D3 were superseded by a decision, not by drift**, and the amendment says so rather than
restating the criterion as met. *"Gate A remains untouched"* was a correct constraint **on
that branch**; design-spec amendment `2026-08-01g` deliberately overrode it, adding criterion
1 as a measured row and labelling two attestation rows as attestations. A criterion was
*added*; none was weakened or removed. Deleting the criterion would have hidden that it was
overridden on purpose.

### 1.2 `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md` — 1 defect

| # | Line(s) | Superseded text | Repair |
|---|---|---|---|
| D6 | 6, 12, 418 | *"95-paper literature review"*, *"A literature review of 95 papers"*, *"Literature study (95 papers fetched)"* | new **§14**, amendment `2026-08-01h`, plus a pointer under the Status line |

**This figure was false when written, not overtaken.** Commit `3897213` — the commit that
*introduced this very v2 revision* — is titled *"Spec v2: reframe after 111-paper literature
review"*, and `papers/literature/INDEX.md` already said **111** in that same commit. Verified
three independent ways at `30eb333`, measured here: 111 arXiv-ID bullets in `INDEX.md`; the
eleven section subtotals in that file summing to 111 (4+17+3+5+5+15+4+3+11+10+34); and 111
PDFs on disk under `papers/literature/`.

Correcting it is safe pre-data because **Gate D's ≥ 80 criterion is unchanged and is met at
either figure**, so the correction cannot move a gate verdict in either direction. §7 is
untouched.

### 1.3 `docs/superpowers/specs/2026-08-01-observation-assignment.md` — 1 defect

| # | Line | Superseded text | Repair |
|---|---|---|---|
| D7 | 138 | *"§8's success criterion still needs its C1 amendment; that is scheduled, not done here."* | dated note; the sentence is left standing as a correct record of what was then outstanding |

The note points at `2026-08-01i/j/k` and adds the FIXED-NO-LAYER consequence for instances 5
and 6, which this document did not carry.

**Constraint respected:** this file is machine-parsed by
`tests/test_observation_assignment.py`, whose `_worked_rows()` treats *any* four-cell markdown
table row in the file as an assignment row requiring a Yes/No verdict naming an observation.
The repair is therefore prose only — no table was added. Re-run after the edit: **23 passed**.

### 1.4 `.superpowers/BLOCKERS.md` — 6 defects

The file already carried an append-only reconciliation note (close-out Task 8) covering four
figures, including **both defects named in the audit brief** — B1's `~12 untriaged survivors`
(line 32) and line 78's `Eleven historical instances`. Those were already correctly annotated;
no further action was taken on them. A full sweep found **six more the note missed**, repaired
by a **second append-only note** matching the first one's declared convention.

| # | Line | Superseded | Now |
|---|---|---|---|
| D8 | 8 | `main @ cedd86a`, `feat/suite-integrity @ 7979396 (UNMERGED)` | branch merged; `main` @ `30eb333` |
| D9 | 9 | `376 tests pass` | 428 |
| D10 | 9 | `Gate A exit 1, 6 PASS / 3 SKIP` | 7 PASS (5 measured, 2 attested) / 0 FAIL / 3 SKIP, exit 1 |
| D11 | 22 | A3 `Needs a CI workflow` | `.github/workflows/ci.yml` exists and is green |
| D12 | 49 | B7 `k=2 gives 0.9518 and is NOT caught (0.0018 margin); k=3 gives 0.9068` | k=2 **0.9392, caught**; k=3 **0.8950** |
| D13 | 63 | C1 `eleven-historical-instance coverage map` | twelve; and C1's spec amendment is now written |

**D12 matters most of the six, and it is superseded in the *favourable* direction** — which
is exactly why it needed saying out loud rather than quietly enjoying. Restoring the twelfth
reliability mate under amendment `2026-08-01f` **tightened** the instrument: a 2× perturbation
that previously slipped through by 0.0018 is now caught. B7's substance survives — instance 4
is improved and bounded, **still not closed** — and the disclosed 2–3× headroom bound is now
*better* than the disclosure claims. Provenance: the docstring of
`tests/test_gate_a.py::test_the_reliability_row_reads_pass_from_the_real_measurement` and
ledger-reconciliation §1, *reliability mean*.

**D11 is annotated, not closed.** Whether a live CI discharges Gate A's third SKIP is a Gate A
verdict; this audit does not issue Gate A verdicts.

### 1.5 `CLAUDE.md` — 4 defects

The brief asked for this file to be confirmed rather than assumed. It was updated the same
day and **the mutation/concurrency paragraph is materially incomplete**.

| # | Superseded | Now | Verified against |
|---|---|---|---|
| D14 | mutation target list omits **`src/tolcad/y14_5.py`** | added | `tests/mutation_registry.py`, entry `y14-5-worked-example-boundary-shifted` |
| D15 | *"and one tracked fixture"* omits **`tests/gen/test_layout.py`** and **`tests/gen/test_features.py`** | both named | ibid., 15 entries enumerated by target |
| D16 | *"`tests/conftest.py` fails the run if the tree is left dirty"* overstates the control's reach | scope stated exactly: `src/` and `tests/fixtures/` only | `tests/conftest.py:15` |
| D17 | Commands list omits `scripts/check_suite_integrity.py`, the pre-merge gate | added, with the exit-2 convention | `.github/workflows/ci.yml`, `scripts/check_suite_integrity.py` |

**D14 is the serious one.** The omitted module is `y14_5.py` — the module **Gate A's criterion
1 is measured against**. `gate_a.py` shells out to a fresh interpreter that reads the checker
from disk, so the exact hazard the paragraph exists to warn about was understated at its
sharpest point. The registry's 15 entries were enumerated directly by target file: `iso286`
×2, `reliability` ×2, `y14_5` ×1, `gen/sampler` ×3, `gen/layout` ×1, `gen/features` ×3, the
NIST `.stp` fixture ×1, `tests/gen/test_layout.py` ×1, `tests/gen/test_features.py` ×1 = 15.

A pointer to the ledger reconciliation was also added, carrying its standing rule: **quote the
spec, never a ledger** — the superseded reliability figure still outnumbers the correct one in
a grep.

### 1.6 `tests/fixtures/NIST-PROVENANCE.md` — 1 defect

| # | Line | Superseded | Repair |
|---|---|---|---|
| D18 | 30 | *"Design spec line 252 makes 'fresh clone, no licence, runs end-to-end' an explicit success criterion"* | direct correction to a **§7 Gate A table** reference, with a dated note |

Line 252 of the design spec today falls inside amendment `2026-08-01g`; amendments
`2026-08-01e/f/g` added roughly 50 lines to §7 after this note was written. A line number into
an append-only document is stale by construction, so the citation was converted to a section
reference rather than re-pointed at a new line number. This is a *pointer*, not a record of
belief, which is why it was corrected directly.

Everything else in this file was re-verified and is **correct**: size 396,445 bytes ✓, SHA-256
`85a5752d…` ✓ (both recomputed here), the 21/6/11 PMI counts ✓, the
`assert_is_the_nist_original` function name ✓, and the claim that the reader returns the same
counts from the CRLF-mangled copy ✓ (`tests/test_ap242_pmi.py:47,111`).

### 1.7 Plans — 4 defects

All five in-scope plans are **executed** plans. Their task bodies and acceptance criteria are
contemporaneous records, so each got an appended `## Staleness note ... (APPEND-ONLY)` rather
than in-place edits.

| # | Plan | Superseded |
|---|---|---|
| D19 | `2026-08-01-suite-integrity.md` | `6 PASS / 3 SKIP` (×3, incl. the *"gate_a.py must remain untouched"* constraint at line 26); `eleven` (×6, incl. the test name `test_the_instance_map_accounts_for_all_eleven`); `no CI and no git remote` + `dormant until a git remote exists`; the `280 passed` baseline |
| D20 | `2026-08-01-iso273-traceability.md` (line 484) and `2026-08-01-pre-registration-prep.md` (line 836) | `Gate A exits 1 with 6 PASS / 3 SKIP` |
| D21 | `2026-08-01-closeout.md` (lines 42, 1116) | `eleven` historical instances in R5's evidence sentence |
| D22 | `2026-07-31-functional-checker.md` (lines ~100–127) | Step 5's embedded `CLAUDE.md` block, superseded by ordinary growth of the live file |

`2026-08-01-procedural-generator.md` swept clean — no note appended.

**Deliberately *not* flagged in D21:** closeout lines 309, 419, 724, 735, 780 and 940 quote
`tested=11`, `{0.9091, 1.0}`, `"6 PASS"` and the contested-quantity list **as the defects the
tasks were commissioned to fix**. They are correct in that role.

### 1.8 `papers/literature/INDEX.md` — 0 defects

Already correct at **111 papers**, and it is the corroborating source for D6. Bullet count,
section subtotals and PDFs on disk all agree at 111. The referenced reproduction scripts
`scripts/fetch_literature.sh` and `scripts/verify_literature.py` both exist. **No change
made.**

---

## 2. Defects found and deliberately NOT fixed (11)

### 2.1 Out of scope — in `tests/`, `scripts/` or `.github/` (3)

**L1 — `tests/conftest.py`: the O-B finalizer false-positives on any documentation edit under
`tests/fixtures/`, and its recovery advice destroys work. This is the most serious finding of
the audit.** Observed, not theorised: running
`pytest tests/test_observation_assignment.py` after editing `tests/fixtures/NIST-PROVENANCE.md`
produced

    THE SUITE LEFT TRACKED FILES MODIFIED. A declared mutation did not restore.
    Recover with `git checkout -- src/ tests/fixtures/` ...
     M tests/fixtures/NIST-PROVENANCE.md

The finalizer at `tests/conftest.py:15` runs `git status --porcelain src/ tests/fixtures/`, a
**path-based** check. `tests/fixtures/` contains exactly two files: the `.stp` fixture, which
*is* a declared-mutation target, and `NIST-PROVENANCE.md`, which is documentation. So any
uncommitted edit to the provenance note is reported as an unrestored mutation, and the
prescribed recovery — `git checkout -- src/ tests/fixtures/` — **would delete that edit.** The
control is loud, which is right, but it is loud about the wrong thing and it hands the
operator a destructive instruction. Not fixed: `tests/` is out of scope, and narrowing the
watch set is a control-design decision. **Immediate consequence: `pytest` will report this
teardown error until this audit's `NIST-PROVENANCE.md` change is committed.**

**L2 — `tests/mutation_registry.py:396–411` carries superseded reliability figures in a live
rationale, and contradicts the file it points at.** The `why=` string for
`reliability-perturbation-tripled` states that tripling *"takes the mean over the 200
pre-registered seeds from 0.9982 to 0.9068"* and that *"2x measures 0.9518 and is NOT
caught"*, then says the bound *"is documented in the target test's docstring"*. That docstring
(`tests/test_gate_a.py:245–260`) says the opposite post-repair: k=1 **0.9975**, k=2 **0.9392
FAIL (caught)**, k=3 **0.8950**, and explicitly labels the older figures *"the previous
ledger"*. So the registry rationale is the **superseded 0.9982 / tested=11 figure surviving
inside the anti-vacuity layer itself**, in the one entry that guards Gate A's reliability row.
It changes no assertion and no threshold — it is prose — but it is the highest-visibility
remaining instance of the figure the reconciliation exists to retire. Not fixed: `tests/` is
out of scope. **Recommend fixing before pre-registration.**

**L3 — `.github/workflows/ci.yml:5` says *"full pytest suite (currently 402 tests)"*.** The
verified count is 428. A comment only. Out of scope.

### 2.2 Cannot tell whether correcting it would be reacting to an outcome (2)

**L4 — the observation-assignment table does not consider the two `tests/gen/` mutation
targets.** Its `run_declared_mutation` row and its B10 row both assign the restore-residue
failure mode to **O-B**, and both are *literally accurate as written* — each says "a `src/`
file". But the layer also mutates `tests/gen/test_layout.py` and `tests/gen/test_features.py`,
which O-B's watch set excludes (L1). So for those two targets, a SIGKILLed run leaves residue
that O-B does not see. Left alone deliberately: the rows contain no false statement, so this
is a **new finding rather than a staleness defect**, and altering a "revealed by" or verdict
cell is an R2 adjudication — a control decision reserved for a human. Flagged for the same
owner as P1.5.

**L5 — `.superpowers/BLOCKERS.md:3` says `17 items`; the sections count A(5) + B(12) + C(1) =
18.** Whether C1 was intended to sit outside the inventory total or a row was added after the
header was written cannot be determined from the file. **Recorded in the appended note as an
observation, explicitly not corrected.**

### 2.3 Correctly frozen, or correctly already handled (3)

**L6 — design spec §7 lines ~227–228**, the `2026-08-01e` sentence *"at 12 tested mates the
only values reachable near the threshold are 1.0000 and 0.9167"*. False when written (eleven
were tested), **true of the repaired instrument**. Already fully handled by amendment
`2026-08-01f`, which records both facts. Frozen, correctly handled, **untouched**.

**L7 — `.superpowers/BLOCKERS.md` lines 32 and 78** (`~12` untriaged survivors; `eleven`
instances), the two defects named in the audit brief. **Already annotated** by the existing
close-out Task 8 append-only note. No action needed; confirmed rather than duplicated.

**L8 — Gate A's third SKIP.** A live CI is the mechanism BLOCKERS A3 said was missing, but
declaring the SKIP closed is a Gate A verdict. Left to the Gate A owner.

### 2.4 Not re-derived, and said so (3)

**L9 — suite-integrity §4's Layer 3 numerator**, *"**Four** of the eleven instances lived
there"*. The amendment corrects the denominator only. The Unencoded instance left no artifact
in any file, so on its face it does not raise the numerator — but *which* four is not
reconstructible from the surviving ledgers (only six of the twelve positions are attested
anywhere), and inventing the enumeration would be the same defect in a new coat.

**L10 — design spec §2's *"~30 generative CAD systems and ~40 assembly-learning papers
surveyed"*.** This describes a surveyed *subset*, not the corpus, so it does not conflict with
111. Not re-derived; amendment `2026-08-01h` says so explicitly.

**L11 — suite-integrity §3's remaining environment facts**: `mutmut` 3.7.0 unusable on
Windows, `cosmic-ray` usable, the 0.14 s / 128-test core subset, 827 lines across six core
modules. Not re-measured by this audit; `2026-08-01k` leaves them standing as recorded and
says which two bullets it supersedes.

---

## 3. Files modified

| File | Mode |
|---|---|
| `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md` | new §14 + amendment `2026-08-01h` + Status pointer |
| `docs/superpowers/specs/2026-08-01-suite-integrity-design.md` | new §10 + amendments `2026-08-01i/j/k` + Status pointer |
| `docs/superpowers/specs/2026-08-01-observation-assignment.md` | dated note (prose only — the file is machine-parsed) |
| `docs/superpowers/plans/2026-07-31-functional-checker.md` | appended staleness note |
| `docs/superpowers/plans/2026-08-01-closeout.md` | appended staleness note |
| `docs/superpowers/plans/2026-08-01-iso273-traceability.md` | appended staleness note |
| `docs/superpowers/plans/2026-08-01-pre-registration-prep.md` | appended staleness note |
| `docs/superpowers/plans/2026-08-01-suite-integrity.md` | appended staleness note |
| `.superpowers/BLOCKERS.md` | second append-only reconciliation note |
| `tests/fixtures/NIST-PROVENANCE.md` | direct correction of a stale line-number citation + dated note |
| `CLAUDE.md` | direct corrections (mutation target list, conftest scope, commands) + reconciliation pointer |
| `docs/superpowers/specs/2026-08-01-staleness-audit.md` | this file (new) |

Unchanged and confirmed correct: `papers/literature/INDEX.md`,
`docs/superpowers/plans/2026-08-01-procedural-generator.md`.

Not touched, by instruction: `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`,
`docs/STATE-OF-PLAY.md`, `docs/DECISIONS.md`, `docs/SPIKES.md`, `docs/ENVIRONMENT.md`,
`docs/START-HERE.md`, `README.md`, `docs/superpowers/plans/2026-08-02-*.md`, and everything
under `src/`, `scripts/`, `tests/` (except the in-scope `tests/fixtures/NIST-PROVENANCE.md`)
and `.superpowers/sdd/`.

---

## 4. Facts independently measured during this audit

Recorded so they are not re-derived, and so the two that *contradict* something are visible.

| Fact | Value | How |
|---|---|---|
| Literature corpus | **111** | `INDEX.md` bullets, section subtotals, PDFs on disk — three ways |
| Declared-mutation registry | **15** entries | `grep -c "DeclaredMutation(" tests/mutation_registry.py`, and enumerated by target |
| Registry target files | **9 distinct** | 6 under `src/`, 1 fixture, 2 under `tests/gen/` |
| Git remote | `https://github.com/harshD42/TolAEG-CAD` | `git remote -v` |
| CI | `.github/workflows/ci.yml` exists | direct read |
| NIST fixture | 396,445 bytes, SHA-256 `85a5752d…` | recomputed; matches the provenance note |
| `tests/conftest.py` O-B watch set | `src/`, `tests/fixtures/` | direct read, and observed firing |
| `tests/test_observation_assignment.py` after this audit's edits | **23 passed** | run |

**Contradictions with the handed-down verified state:** none in the numbers themselves — the
remote, the CI, the 15-entry registry and the 111-paper corpus all confirm. Two *internal*
contradictions exist in the repo, both out of scope: `.github/workflows/ci.yml` says 402 tests
against the verified 428 (L3), and `tests/mutation_registry.py` contradicts
`tests/test_gate_a.py` on the reliability k-sweep (L2). The 428 count and the Gate A row
breakdown were **not independently reproduced**, for the concurrency reason in §0.
