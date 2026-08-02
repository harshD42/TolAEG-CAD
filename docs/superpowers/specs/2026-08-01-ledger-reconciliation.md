# Ledger Reconciliation: one canonical value per contested quantity

**Status:** approved 2026-08-01. Records no new measurement; adjudicates existing ones.
**Guard:** `tests/test_observation_assignment.py` — exactly one `CANONICAL` line per section,
each citing provenance.
**Companion:** `docs/superpowers/specs/2026-08-01-observation-assignment.md`.

## 0. Method, and what this document deliberately does not do

Gate D requires every claim traceable to a logged experiment run. The SDD ledgers under
`.superpowers/sdd/` are those logs — and they disagree with themselves on nearly every
quantity, because each was written contemporaneously against the tree as it stood that hour.

**The original ledger lines are NOT REWRITTEN.** Their entire value is that they are
contemporaneous. Reconciliation here is **append-only**: this file names one canonical value
per quantity with its provenance, and marks every other recorded figure SUPERSEDED with the
reason it was superseded. Anyone grepping the ledgers will still hit the old numbers; this is
the file that tells them which one is live.

**Why this lives in `docs/` and not in a ledger.** `.superpowers/sdd/.gitignore` contains a
single `*`, so every SDD progress ledger is deliberately untracked. A canonical value recorded
only there would be invisible to a clone, which is precisely the audience Gate D's traceability
requirement exists for. See §8.

**Standing rule, carried from the 2026-08-01 reliability repair:** the pre-registration must
quote the **spec**, never a ledger. Roughly a dozen ledgers still contain the superseded
reliability figure and they outnumber the correct one in a grep.

---

## 1. Contested quantities

### pre-fix d4 Tier 1 failure rate

The Tier 1 d4 failure rate as measured **before** the difficulty-ladder repair (C2).

- **CANONICAL: 478/609 = 78.5%.** Provenance: `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:50`
  (`d4 = 131 Tier1 pass / 478 fail`, and 131 + 478 = 609) corroborated at the same file line 185
  (`Tier 1 failures are 0 at d1, d2 AND d3; 478/609 at d4`).
- SUPERSEDED: `0% / 0% / 0% / 69.1%` at
  `.superpowers/sdd/2026-08-01-procedural-generator/final-fix-wave-report.md:251` and echoed in
  that ledger's progress at line 246. **Reason: the 69.1% in that sentence is the POST-fix d4
  value carried backwards into a pre-fix claim.** The `0 / 0 / 0` part of it is correct; only
  the fourth number is wrong. This is a transcription error, not a disagreement between runs —
  the two figures were never measurements of the same tree.

### Tier 1 ladder (post-fix, the number pre-registration will freeze)

Included because it is what disambiguates the row above, and because it is the one quantity in
this file that is pinned executably rather than adjudicated.

- **CANONICAL: d1 31/159 = 19.5%, d2 99/301 = 32.9%, d3 239/452 = 52.9%, d4 421/609 = 69.1%,
  seeds 0–199, numpy 2.4.1, corpus digest `c035c2d99d377c1f…`.** Provenance:
  `tests/gen/test_ladder_pin.py` and `scripts/measure_ladder.py`, commit `4094bd5` — a two-sided
  exact pin on all four counts, re-confirmed by every task since.
- No other value has ever been recorded for the post-fix ladder: eight independent
  re-measurements across four plans all returned these counts bit-identically. SUPERSEDED: none.

### untriaged survivors (Layer 2)

The count of cosmic-ray survivors that were neither killed by a new test nor recorded as
equivalent mutants.

- **CANONICAL: 21, as of run 3 (2026-08-01), derived as 40 measured survivors minus 19 corrected
  documented equivalents. The count for the CURRENT tree is UNKNOWN and is owned by P1.5.**
  Provenance: `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:261,301` (run 3's 93.85%
  = 610/650, i.e. 40 survivors) and the SI-4 fix round's correction of the equivalent count from
  23 to 19 (`task-4-fix-report.md:129`, nine mutants mislabelled — four "equivalent" that were
  live, five "killed" that did not kill).
- SUPERSEDED: **~17** — derived as 40 − 23 in the same round that corrected the equivalents to
  19. Arithmetically stale by exactly the correction.
- SUPERSEDED: **~12** (`.superpowers/BLOCKERS.md:32`, and carried into the closeout progress
  ledger). No run produces this figure; it is an unsourced carry-forward.
- SUPERSEDED: **~27** — never written as a survivor count, only implied by reading 95.89%
  against a 650 denominator. An inference from a score is not a survivor enumeration.
- SUPERSEDED: **0** — implied by Task 6's observed 100.00%. Same objection, and stronger: a
  perfect score is exactly the shape this project's history says to scrutinise rather than
  accept. Recorded, not believed.

The honest summary: the last time anyone *enumerated* a survivor set was run 3. Every figure
since is arithmetic over a score. That is the finding, and it is why P1.5 is a re-measurement
rather than a new control (see the observation table's `re-run-and-compare` row).

### branch coverage (Layer 1, six core modules)

- **CANONICAL: 94.74%.** Provenance: `scripts/check_suite_integrity.py::COVERAGE_MEASURED`
  (`= 94.74`, `COVERAGE_TOLERANCE = 0.50`, two-sided) pinned at commit `062316e`, re-measured
  green in Task 6's run at `05d4dae`: `Core branch coverage PASS 94.74% (pin 94.74% +/- 0.50)`.
- SUPERSEDED: **48.0** (`.superpowers/sdd/2026-08-01-suite-integrity/task-3-report.md:121`).
  Superseded by **SCOPE, not drift**: it was measured with `--cov=src/tolcad`, which includes
  `gen/` — explicitly excluded from Layer 1 by the design spec's non-goals. Comparing it with
  the later figures is a category error.
- SUPERSEDED: **91.64** — the same measurement after the scope was narrowed to the six core
  modules (`.superpowers/sdd/2026-08-01-suite-integrity/progress.md:155`).
- SUPERSEDED: **94.12** — after the SI-4 survivor triage added tests
  (`.superpowers/sdd/2026-08-01-suite-integrity/task-4-report.md:76`).

Two of the four differ by scope and two by added tests. None is evidence of a coverage
regression, and the pin has been two-sided since Task 2.

### mutation score (Layer 2, six core modules)

This quantity has two canonical facts, and they disagree **by design**. Recording only one of
them is how the contradiction started.

- **CANONICAL: pin 95.89% ± 0.50, last measurement 100.00% — and they disagree, which is the
  control working.** Provenance: `scripts/check_suite_integrity.py::MUTATION_MEASURED = 95.89`
  at commit `062316e` (the architect's end-to-end run, 2026-08-01); the 100.00% observation is
  Task 6's run at `05d4dae`, reported as `Mutation score FAIL 100.00% (pin 95.89% +/- 0.50)`.
  **DO NOT RE-PIN.** The two-sided pin fired correctly on its first real encounter and a
  one-sided floor would have stayed silently green. Resolution belongs to P1.5.
- SUPERSEDED: **93.85** (run 3, 610/650) and its derived floor **93.35** — superseded upward by
  commit `380d36a`, which killed nine mutants after 93.85 was measured. This is the drift F1
  identified: a floor that stopped tracking what it bounded.
- SUPERSEDED: **57.69%** — run 2's standalone diagnostic, a different denominator (650 viable
  of 1,118 jobs) and a pre-triage tree.
- SUPERSEDED: **75.4%** — 275 of 1,118, arithmetic over the wrong denominator; 468 INCOMPETENT
  mutants cannot execute and are correctly excluded. Recorded in the SI-4 report as an error
  found and corrected, not as a result.
- SUPERSEDED: **18.2%** — a `types.py`-only spike (12 survivors of 66) run with a per-file test
  command, which inflates survivors and measures nothing. It is a methodology note, never a
  score for the layer.

### reliability mean (Gate A, checker reliability criterion)

- **CANONICAL: mean 0.9975, 95% bootstrap CI [0.9954, 0.9992] over 10,000 resamples,
  fraction of seeds ≥ 0.95 = 0.9700, tested=12, excluded=0, 200 pre-registered seeds.**
  Provenance: Task 3, commit `cac4644`, measured after the mate-set repair under construction
  rule D-D (one binding part per sensitive-band mate at ±3.5e-4, every other part slack at
  ≥10×); amendment 2026-08-01f; re-confirmed by running `scripts/gate_a.py` at `2184485`.
- SUPERSEDED: **mean 0.9982, tested=11, excluded=1** — carried in roughly a dozen ledgers.
  Measured against the defective mate set: `gate_a.py` documented `mate[8]`'s margin as a SUM
  while `y14_5.py` implements ASME B-3's per-part `min()`, so the mate landed at exactly 0.0,
  fell in the exclusion band, and was silently dropped. A second mate had the same defect
  latent, surviving only because `min()` picked its negative branch.
- SUPERSEDED: reachable-values statement **{0.9091, 1.0} at eleven tested mates**, and the
  frozen design-spec §7 lines 227–228 claim **"at 12 tested mates the only values reachable
  near the threshold are 1.0000 and 0.9167"** — false when written (there were eleven), true of
  the repaired instrument. The amendment records both facts; the pre-registration publishes the
  tables plus the corrections with the superseded text shown, not the tables verbatim.
- SUPERSEDED: the reviewers' candidate repairs **0.9967** and **0.9971** — two different
  constructions of the same stated intent. D-D settles it by specifying the construction, which
  *determines* 0.9975 rather than choosing it.
- Note, not a supersession: restoring the twelfth mate **tightened** the instrument (k=2 now
  fails at 0.9392 where it previously passed at 0.9518). B7's disclosed 2–3× headroom bound is
  therefore better than the disclosure claims, and the k-sweep must be re-measured before it
  enters the pre-registration.

### instance count (the "test that cannot fail" history)

- **CANONICAL: twelve enumerated shape-instances, referred to BY NAME rather than by number.**
  Provenance: `docs/superpowers/specs/2026-08-01-suite-integrity-design.md` §1 table, counted
  row by row: Insensitive 4, Tautological 2, Unreachable 2, Drifted 2, Structurally impossible
  1, Unencoded 1.
- SUPERSEDED: **eleven** — the count in that same document's §1 prose, §8 success criterion and
  §4 Layer 3 note, and in `.superpowers/BLOCKERS.md:78`. §8's distribution names eleven
  *distinct* instances and omits exactly one: the **Unencoded** row (the 39-cell IT table check
  run once in a shell). It is the only one of the twelve no layer can catch, and it is the same
  shape as the observation table this reconciliation ships beside.
- SUPERSEDED as a numbering scheme: the ordinals **thirteenth** (ROUND-0 F1) and **fifteenth**
  (T3 Finding 1). Both are consistent with a base of twelve, not eleven — which is
  corroborating evidence for the canonical count, and also why no new ordinal may be minted.
  Only instances **2** (reliability metric), **3** (seed-fished positive control), **4** (Gate A
  1000× headroom), **5** (module-level `pytestmark` skip, in `tests/`), **6** (fetcher `exit 1`
  branch, in `scripts/`) and **10** (case-sensitive text guard) are attested in code or spec
  text. The remaining six positions cannot be reconstructed from the surviving ledgers, and
  inventing them would be the same defect in a new coat.
- Consequence, scheduled elsewhere: §8's success criterion still needs its C1 amendment, and
  instances 5 and 6 are FIXED-NO-LAYER — Layer 1's coverage is scoped to six modules under
  `src/tolcad`, while those two live in `tests/` and `scripts/`.

---

## 2. Quantities checked and found NOT contested

Recorded so a later reader does not re-open them: the Gate A row count (7 PASS — 5 measured, 2
attested — 0 FAIL, 3 SKIP, exit 1), the corpus digest, the numpy pin (2.4.1), and the registry
size (14 entries) each have exactly one live value across every ledger.

## 3. Tracking status of `.superpowers/`, and what Gate D actually needs

Measured at `2184485`, not assumed:

| Path | Git status | Mechanism |
|---|---|---|
| `.superpowers/BLOCKERS.md` | **tracked** | — |
| `.superpowers/closeout/ROUND-{0,1,2}-*.md` | **tracked** | — |
| `.superpowers/sdd/**` | **ignored** | `.superpowers/sdd/.gitignore` containing `*` |

Nothing under `.superpowers/` is untracked-and-unignored, so there is no accidental state to
clean up. The nested ignore is a deliberate earlier choice: the SDD ledgers are retained
locally as a provenance record.

**What Gate D's traceability requirement actually needs** is that every *published* claim can
be traced from a clone to a logged run. It does not need the raw hour-by-hour ledgers in the
clone; it needs the adjudicated value, its provenance, and the executable pin. Those are §1 of
this file, the design specs, and the pins in `tests/` and `scripts/` — all tracked. The
recommendation is in the task report; this section records the measurement it rests on.
