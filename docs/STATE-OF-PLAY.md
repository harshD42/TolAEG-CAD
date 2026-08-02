# tolcad — State of Play

**As of:** 2026-08-01, `main` @ `30eb333`. Tree clean. CI green on `ubuntu-latest` and
`windows-latest`.
**Canonical numbers:** `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`. That file
adjudicates every contested quantity and marks the superseded ones. Cite it; do not restate its
figures from memory, and never quote a number out of `.superpowers/sdd/` — those ledgers are
contemporaneous logs and most of their figures are superseded.

---

## 1. What this is

`tolcad` is an open, GD&T-aware functional checker for toleranced CAD assemblies, plus a
procedural generator that produces toleranced assemblies from a seed. It supports the paper
*Nominally Correct, Functionally Wrong*. The claim is not "Chamfer distance is area-weighted"
(ASSEMCAD 2607.05123 App. H.5 already says that) but the stronger, empty-space claim in the
design spec §2: **assemblability under manufacturing variation is measurable deterministically
from published standards (ASME Y14.5-2018, ISO 286-1, ISO 273, ISO 2306); nobody has measured it
for generative CAD; and doing so changes model rankings.** Tier 1 is closed-form and exact
(`H = F + T` floating, `H = F + 2T` fixed, `VC_pin ≤ VC_hole`), so a Tier 1 failure is
unambiguously the model's, not the checker's. Tier 2 is Monte Carlo over ISO 286 fits and always
reports a seed. Tier 3 (freeform, kinematic, form defects) is out of scope and stated as a
limitation.

---

## 2. What is built and working

### Checker core — `src/tolcad/`, numpy-only, 827 lines across six modules

| Module | Lines | What it does | Standard | What pins it |
|---|---|---|---|---|
| `types.py` | 80 | `FeatureOfSize`, `FeatureType`, `Verdict`; `EPS = 1e-9`. All dimensions mm, float. | ASME Y14.5 feature-of-size semantics | `tests/test_types.py` (7) |
| `y14_5.py` | 270 | Tier 1 exact: virtual condition, bonus tolerance under MMC, floating/fixed fastener. Per-part `min()` form of ASME B-3, **not** a pooled sum — the module documents why at length. | ASME Y14.5-2018 §7 + Nonmandatory App. B | `tests/test_y14_5.py` (48), incl. the three published App. B worked examples at the standard's own inputs (B-3 F=6.0/H=6.44/T=0.44; B-4 T=0.22; B-4 unequal T1=0.18/T2=0.26); registry entry `y14-5-worked-example-boundary-shifted` |
| `iso286.py` | 192 | Hole-basis limits and fits, `fit_from_designation`. Shaft letters g/h/p (any tabulated grade) and k (grades 4–7 only, rejected elsewhere rather than guessed). | ISO 286-1 Table 1 (IT), Tables 4/5 (deviations) | `tests/test_iso286.py` (44): the 52-cell IT5–IT8 pin, all 39 IT12–IT14 cells, the grade-set declaration; registry entries `it7-row-transposed`, `it-grade-set-widened` |
| `montecarlo.py` | 71 | Tier 2 stack-up: truncated-normal / uniform size sampling, `clearance_yield`. Every result carries seed and N. | — (statistical layer over ISO 286 limits) | `tests/test_montecarlo.py` (16), `tests/test_convergence.py` (2, `slow`) |
| `checker.py` | 55 | Top-level dispatch over the four mate kinds. Mates arrive as plain dicts so `gen/` can emit JSON without importing `tolcad`. | — | `tests/test_checker.py` (11) |
| `reliability.py` | 159 | Gate A test–retest: verdict stability under input perturbation, multi-seed aggregate with bootstrap CI. Docstring states the honest bound: it detects instability only for mates within ~2–3ε of the boundary; a 1.0 is "no instability in the tested band", not a proof of reliability. | design spec §7 criterion 5, amendments 2026-08-01e/f | `tests/test_reliability.py` (17), incl. exact pins on `tested`/`excluded` and the D-D construction rule; registry entries `reliability-perturbation-neutered`, `reliability-perturbation-tripled` |

The core has one runtime dependency: `numpy==2.4.1`, pinned exactly (decision D-C — `Generator`'s
stream is not covered by NEP 19, so an unpinned numpy silently invalidates the ladder pin).

### Generator — `src/tolcad/gen/`, optional `[gen]` extra (CadQuery)

- `spec.py` (182) — `AssemblySpec`/`MateSpec`. `MateSpec.to_check_dict()` returns exactly the dict
  shape `checker.check` already accepts, so generation and checking meet at a tested interface.
  Four kinds: `virtual_condition`, `floating_fastener`, `fixed_fastener`, `iso_fit`.
- `sampler.py` (166) — seed → `AssemblySpec`, deterministic, no CAD dependency. Difficulty 1–4
  sets loop length (capped at 4 per spec §4.1) and how tightly position tolerances crowd the
  allowable. Pinned by `tests/gen/test_ladder_pin.py`; registry entries `flat-difficulty-ladder`,
  `ladder-d2-row-shifted`, `fastener-upper-dev-nonzero`, `mc-seed-base-shifted`.
- `features.py` (155) — canonical mating features. All 21 clearance-hole diameters checked against
  **ISO 273-1979(E) Table 1** on 2026-08-01; the internal names close/normal/loose map to the
  standard's fine/medium/coarse, and each hole carries its series tolerance grade (H12/H13/H14) at
  its own diameter via `iso286`, not a flat constant. All 7 tapping drills checked against **ISO
  2306-1972 Table 1**; M8→6.8 and M12→10.2 are *not* nominal-minus-pitch and must not be
  "corrected". Registry entries `m12-clearance-diameter`, `tapped-hole-upper-dev-nonzero`.
- `layout.py` (127) — plate sizing and feature placement derived from the sampled radii, so the
  layout cannot be outgrown by a change to the feature tables. Registry entries
  `zeroed-wall-margin`, `stale-literal-wall-floor`.
- `build.py` (85) — `AssemblySpec` → CadQuery geometry, two stacked plates, one feature per mate.
  Absolute placement via `pushPoints` on a `CenterOfBoundBox` workplane; the relative-offset bug it
  documents is load-bearing history.
- `export.py` (35) — STEP AP242 plus a **sidecar** tolerance schema. Separate files by design
  (spec §4.2): the schema belongs to the reference design and is later applied to *predicted*
  geometry.

### `scripts/`

| Script | What it does | Exit codes |
|---|---|---|
| `gate_a.py` | Prints the Gate A report over spec §7's criteria, each row labelled `VERDICT(measured\|attested)`. | 0 cleared / 1 not cleared / **2 refused, a declared mutation is in flight** |
| `check_suite_integrity.py` | Runs Layers 1 and 2 (branch coverage, mutation score) against two-sided pins. | 0 / 1 / **2 refused** |
| `measure_ladder.py` | Re-measures the four Tier 1 ladder counts over seeds 0–199 and computes the corpus digest. `LADDER_RECIPE` is written down so the digest means something. | — |
| `fetch_nist_pmi.py` | Fetches and hash-verifies the NIST MBE PMI conformance suite into `data/nist_pmi/` (17 AP242 files present). | 0/1 |
| `fetch_literature.sh`, `verify_literature.py` | Literature corpus tooling. 111 PDFs live in `papers/literature/`; only `INDEX.md` and `_fetch_log.txt` are tracked. | — |

### `validation/` — optional, one-directional

May import core; core may never import it, enforced by an AST lint in `tests/test_architecture.py`
(10 tests) that catches direct imports, bare relatives, `importlib`/`__import__`, and `exec`/`eval`
obfuscation. Since `pythonpath` includes the repo root, that lint is the *sole* enforcement — it
must not be weakened.

- `ap242_pmi.py` — reads semantic PMI from STEP AP242 via OCCT XCAF. Verified by execution against
  `nist_ftc_06_asme1_ap242-e2.stp`: 47 dimensions, 27 geometric tolerances, 59 datums. Graphical
  PMI is out of scope.
- `nist_pmi.py` — compares our verdicts against a NIST expected-verdict CSV. **The CSV does not
  exist** (see §4).
- `tolanalyst.py` — ingests a manually exported TolAnalyst verdict CSV. Black-box oracle: agreement
  rates only, never mechanism. No SolidWorks internals anywhere in the repo.

### `tests/` — 428 passing

28 files. Notable non-obvious ones:

- `conftest.py` — **O-B**: a session-scoped finalizer failing the run if `git status --porcelain
  src/ tests/fixtures/` is non-empty afterwards. It cannot see corruption that existed only
  *during* the run; that is what the mutation lock is for.
- `mutation_registry.py` — Layer 3 data (15 entries) plus `run_declared_mutation` and
  `mutation_lock`.
- `test_declared_mutations.py` (15) — Layer 3 execution, in every `pytest` run. Holds
  `_CRITICAL_GUARDS` (15 names).
- `test_gate_a.py` (20) — pins Gate A's row structure, the criterion-1 node IDs, and the exit codes
  exactly (`== 2` for refusal, not `!= 0`).
- `test_observation_assignment.py` (8) — parses the observation-assignment table; requires every
  verdict cell to *name* an observation, so a table of bare "yes"/"no" fails.
- `test_gitattributes_clone.py`, `test_tree_cleanliness.py`, `test_suite_integrity_script.py` —
  the meta-layer.
- `.github/workflows/ci.yml` — two jobs. Suite job on ubuntu+windows matrix, Python 3.13, fresh
  install of `[dev,gen]`. Integrity job (Layer 2, ~25 min) is on `workflow_dispatch` + weekly cron
  **only**, deliberately off the push path.

---

## 3. The verified numbers

Every row is measured, not asserted. "Pin" means an executable two-sided check (O-C). Contested
quantities are adjudicated in
`docs/superpowers/specs/2026-08-01-ledger-reconciliation.md` §1 — cited below as **[LR §1]**.

| Quantity | Value | Provenance | Pinned? |
|---|---|---|---|
| Full suite | **428 passed** | `.superpowers/sdd/2026-08-01-closeout/progress.md`, T9 @ `bdd632c`; re-verified at `30eb333` | **No.** Nothing asserts the suite count; O-A is pass/fail only |
| Gate A | **exit 1** — 7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP | `python scripts/gate_a.py`; spec amendment 2026-08-01g | `tests/test_gate_a.py` pins the rows and the exit code |
| Tier 1 ladder, seeds 0–199 | **d1 31/159 (19.5%), d2 99/301 (32.9%), d3 239/452 (52.9%), d4 421/609 (69.1%)** | `4094bd5`; **[LR §1]** "Tier 1 ladder (post-fix)" — eight independent re-measurements returned these bit-identically | Yes: `tests/gen/test_ladder_pin.py`, exact counts, two-sided, on numpy 2.4.1 |
| Corpus digest | `c035c2d99d377c1f1c6f912c9c690e47376e012eee37f4283c41de0051336fa3` | `scripts/measure_ladder.py::corpus_digest` + `LADDER_RECIPE` | Yes: `test_the_corpus_digest_is_reproducible` |
| Pre-fix d4 failure rate | **478/609 = 78.5%** (the number the ladder repair moved) | **[LR §1]**; the widely-echoed `69.1%` in a pre-fix sentence is a post-fix value carried backwards | n/a — historical |
| Branch coverage, six core modules | **94.74% ± 0.50** | `check_suite_integrity.py::COVERAGE_MEASURED` @ `062316e`; re-measured green at `05d4dae`. **[LR §1]** — the 48.0 / 91.64 / 94.12 figures differ by *scope* and by *added tests*, not by regression | Yes, two-sided |
| Mutation score, six core modules | **pin 95.89% ± 0.50; last measurement 100.00% → FAIL** | pin @ `062316e`; observation from T6 @ `05d4dae`. **[LR §1]** — **DO NOT RE-PIN**, see §7 | Yes, two-sided — and it is currently firing |
| Untriaged Layer 2 survivors | **21 as of run 3; the count for the current tree is UNKNOWN** | **[LR §1]** — 40 measured survivors minus 19 corrected equivalents. Every later figure (~12, ~17, ~27, 0) is arithmetic over a score, not an enumeration | No. Owned by P1.5 |
| Gate A reliability | **mean 0.9975**, 95% bootstrap CI **[0.9954, 0.9992]** over 10,000 resamples, fraction of seeds ≥ 0.95 = **0.9700**, **tested=12, excluded=0**, 200 pre-registered seeds (0–199) | `cac4644`, spec amendment 2026-08-01f, construction rule D-D. **[LR §1]** — the ~12 ledgers quoting 0.9982/tested=11 measured a defective mate set | Yes: mean, `tested`, `excluded` and the one-binding-part rule all pinned in `tests/test_reliability.py` |
| Declared-mutation registry | **15 entries, 15 critical guards** | `tests/mutation_registry.py`, `tests/test_declared_mutations.py::_CRITICAL_GUARDS` | Yes: `test_the_registry_still_covers_every_critical_guard` |
| Historical "cannot fail" instances | **twelve enumerated, referred to BY NAME** | suite-integrity design §1 table, counted row by row. **[LR §1]** — the "eleven" in that document's prose and §8 omits the **Unencoded** row | `tests/test_observation_assignment.py` parses §4's table |
| Literature corpus | **111 papers** | `papers/literature/` (111 PDFs, untracked); Gate D requires ≥80 reviewed | No |
| numpy | **2.4.1**, exact | `pyproject.toml` (D-C) | Yes, by install |

---

## 4. Gate status

Thresholds are frozen by `CLAUDE.md`. The correction log in design spec §7 holds **seven**
pre-data corrections (2026-07-31a–d, 2026-08-01e–g); no post-data change is permitted.

### Gate A — checker correctness (blocking). **NOT CLEARED, exit 1.**

| §7 criterion | Threshold | Current | Kind |
|---|---|---|---|
| Agreement with published Y14.5 worked examples (Tier 1) | 100% | **PASS** — the three ASME App. B examples run as named node IDs | measured |
| *(informational)* Y14.5 self-consistency | — | PASS, explicitly **not** a §7 criterion | measured |
| Monte Carlo convergence at N=100k | ±0.5% over 5 seeds | **PASS** | measured |
| Checker reliability | ≥ 0.95 | **PASS** at 0.9975 | measured |
| Import-lint: no core module imports `validation/` | Pass | **PASS** | measured |
| Y14.5 citation verified | — | **PASS** — attested by Harsh Dwivedi, 2026-08-01, `2562bef`, against ASME Y14.5-2018 | **attested** |
| ISO 286 transcription verified | — | **PASS** — attested, ISO 286-1:2010 Tables 1/4/5, 117 values across 13 size bands | **attested** |
| Agreement with NIST MBE PMI suite (FTC/CTC) | 100% on decidable cases | **SKIP** — no expected-verdict CSV exists | — |
| Verdict agreement with TolAnalyst, ≥500 Tier 2 assemblies | ≥ 95% | **SKIP** — no export | — |
| Fresh clone, no SW licence, full pipeline | Runs end-to-end | **SKIP** — needs a receipt from a real clean-clone CI run; a pass claimed from inside this checkout would not establish it | — |

**Why A cannot presently clear**, stated plainly — this is not an engineering backlog, it is an
oracle problem:

1. **TolAnalyst is licence-gated.** Human decision **D-B** made it *supplementary, not blocking* —
   forced, not chosen, because spec §4.3 requires every headline number to reproduce with no
   SolidWorks licence. **That decision has not been written into the frozen §7 table**, which still
   lists it as a Gate A criterion, so `gate_a.py` still SKIPs it and still exits 1.
2. **The NIST suite has no assemblability ground truth.** Measured, not assumed: all 17 AP242 files
   in `data/nist_pmi/` have **zero** `NEXT_ASSEMBLY_USAGE_OCCURRENCE` entries. They are single
   parts. TolAnalyst analyses assemblies, so it cannot supply the missing column either. Decision
   **D-A**: split the criterion — NIST becomes a **PMI-extraction** oracle against the published
   annotation counts (real, citable, licence-free, but it validates the *reader*, not the
   *decision*) — **and state the limitation**. Also not yet written into the spec.
3. **No public dataset pairs GD&T tolerances with assemblability ground truth.** Survey result over
   the 111-paper corpus, tabulated in `docs/superpowers/plans/2026-08-01-closeout.md`: NIST has PMI
   but no assemblies; AutoMate (2105.12238) has assemblies and states outright there is no ground
   truth; MUSE has judgments but from a VLM rubric, not arithmetic; ASSEMCAD's two uses of
   "tolerance" are a mesh epsilon; politopix has GD&T polytopes but is unmaintained. This is
   **evidence, not an admission** — it is what justifies building the generator, and it belongs in
   the pre-registration's limitations section as a survey result.
4. **The fresh-clone row needs a receipt.** CI now exists and is green on both platforms; P2.3 (the
   receipt mechanism) is designed but unbuilt.

So: two of the three SKIPs are closed by *amending the frozen spec with the already-settled D-A and
D-B*, not by writing code. That amendment is pre-data and therefore permitted. Until it is filed,
Gate A's exit code is a true report of a stale criterion set.

### Gate B — the finding. **Not started.** Requires Phase 4 data.
Primary statistic AUC/Somers' D, within-model primary and pooled secondary, 95% CIs from a
model-level cluster bootstrap. Strong = upper CI < 0.65; Null = lower CI > 0.80; the null
contingency reframes the work as a benchmark/resource paper and is still publishable.

### Gate C — mechanism. **Not started, and at risk before it starts.**
Requires normalized error ratio ≥ 2.0× (bootstrap CI excluding 1.0), holding across **≥6 of ≥8
baseline models**. Nobody has yet verified that eight of the nine named baselines actually run.
See §6, item 1.

### Gate D — publication readiness. **Not started.**
Needs Gate A pass, a Gate B verdict, fresh-clone reproduction of headline numbers (exact for
deterministic, ±1% for sampled), CADBench unified-protocol baseline reproduction within ±5%, ≥80
papers reviewed (**111 — met**), a public pre-registration timestamp *before* data generation, and
every claim traceable to a logged run. What that requirement actually needs is not the raw
hour-by-hour ledgers in a clone but the *adjudicated* value, its provenance, and its executable pin
— which are the ledger-reconciliation spec, the design specs, and the pins under `tests/` and
`scripts/`, all tracked. Whether the SDD ledgers themselves are tracked is in flux: they were
git-ignored via `.superpowers/sdd/.gitignore` containing `*` at `30eb333`, and a session in progress
is reversing that to track everything except the regenerable `*.diff` files, with a `README.md`
warning readers not to quote figures from them. Check `git ls-files .superpowers/sdd` before
relying on either state; the ledger-reconciliation spec's §3 table records the pre-reversal one.

---

## 5. The three-layer anti-vacuity gate

The project's dominant failure mode is **"the test that cannot fail"** — twelve enumerated
instances across six shapes (Insensitive ×4, Tautological ×2, Unreachable ×2, Drifted ×2,
Structurally impossible ×1, Unencoded ×1), catalogued in
`docs/superpowers/specs/2026-08-01-suite-integrity-design.md` §1 and governed by
`docs/superpowers/specs/2026-08-01-observation-assignment.md`.

| Layer | Defect class | Mechanism | Status |
|---|---|---|---|
| 1 — branch coverage | *Unreachable* | `pytest --cov --cov-branch` over the six core modules, core subset only (`gen/` is omitted in `pyproject.toml`, deliberately — leaving it in put ~222 never-exercised statements in the denominator and dragged the total to 48%, turning the floor into a number core coverage could halve without tripping) | **Green**, 94.74% ± 0.50 |
| 2 — mutation score | *Tautological*, *Insensitive* in production code | cosmic-ray over the same six modules. (`mutmut` 3.7.0 refuses to run natively on Windows; cosmic-ray is the tool.) | **Firing**: 100.00% vs a 95.89% ± 0.50 pin |
| 3 — declared mutations | Everything `src/`-only mutators cannot reach: test constants, data files, scanned text | 15 registry entries. Each is a full experiment: substring occurs exactly once → target test passes at baseline → mutate → assert the declared outcome → restore → assert byte-identical. `expect="fail"` is the default; `expect="pass"` closes seed-fishing. | **Green**, runs in every `pytest` invocation |

**The mutation lock, added 2026-08-01 (`bdd632c`).** `run_declared_mutation` holds
`.mutation-in-progress` (gitignored, carrying pid and start time) around the
mutate/run/restore/verify region. `scripts/gate_a.py` and `scripts/check_suite_integrity.py` refuse
to start while it exists and **exit 2**, distinct from both scripts' 0/1. The hazard it closes is
real and specific: `gate_a.py` shells out to a fresh interpreter that reads the checker core *from
disk*, so an overlapping run can print a Gate A number measured against a mutated
`src/tolcad/reliability.py`. O-B is structurally blind to it — the tree is clean *after* the run.
The guard lives in `main()`, not at module scope: `tests/test_gate_a.py` imports `scripts.gate_a`
at collection, and two registry entries target tests in that file, so a module-level
`SystemExit(2)` would have made two critical guards report success having never observed their
mutation. Recovery from a stranded lock: `git status --short src/ tests/fixtures/`,
`git checkout --` any leftover mutant, delete `.mutation-in-progress`, re-run.

### The decisive finding about this machinery

**Zero of the historical instances were found by the three layers. Ten were found by an adversarial
reader over a diff.** (Observation-assignment spec, R5.) The layers are a **recurrence ratchet, not
a detector**. Corollaries that must survive into the pre-registration:

- **Awareness is explicitly not a control.** The pattern was in project memory and in nearly every
  review prompt of the 2026-08-01 session, and three new instances still landed.
- **O-D discovers; it does not guard.** A one-time discovery by review does not discharge R2 for
  that defect's recurrence.
- The pattern reappeared *inside the controls built to close it*, repeatedly and on the record: the
  reliability test written into the plan document computed the band's floor and called it the
  ceiling; the first draft of the mutation-lock test compared character offsets and passed against
  a runner with the lock reduced to `with mutation_lock(): pass`; six consecutive close-out tasks
  found the plan's own snippet did not hold. **A test written in a plan and never run is not a
  test.**
- The four observations (O-A suite on a clean checkout; O-B tree cleanliness after every run; O-C
  two-sided exact pins on published numbers, instrument-composition quantities *and* every constant
  a gate compares against; O-D scheduled adversarial review) are a **closed** list. Closure is the
  device that terminates "who checks the checker?". Extending it is a human decision recorded in
  the spec; no agent may add a fifth.

---

## 6. Open items, ordered by what blocks what

**1. Baseline runnability audit — ~1 day. NOT BLOCKED. Blocks pre-registration.**
Verify that at least eight of the nine named baselines (CAD-Recode 2412.14042, cadrille 2505.22914,
CAD-Coder/MIT 2505.14646 — *not* Beihang 2505.19713 —, Text-to-CadQuery 2505.06507, DeepCAD
2105.09492, Text2CAD 2409.17106, BrepGen 2401.15563, DTGBrepGen 2503.13110, HoLa 2504.14257) have
code and weights that actually execute. **This must precede pre-registration.** Gate C's frozen
"≥6 of ≥8 baseline models" is unmeetable if fewer than eight run, and after the freeze it is
unrecoverable — the threshold cannot be lowered post hoc without invalidating the result. This is
the highest-priority unblocked item in the project and nothing else depends on it, which is exactly
why it keeps getting deferred.

**2. P1.5 — Layer 2 re-measure and full survivor triage — 1.5 SERIALISED days. NOT BLOCKED. Blocks
re-pinning the mutation score, and therefore blocks a clean `check_suite_integrity` run.**
Nothing may edit `src/` *or* `tests/` for the duration; cosmic-ray reads both from disk and mutates
the working tree in place. Deliverable: an *enumerated* survivor set (the last enumeration was 21,
at run 3), a ruling per survivor (killed by a new test, or recorded equivalent), an explanation for
the 100.00%, and only then a re-pin. Note it needs a *re-measurement*, not a new control: R2 forbids
building the "re-run-and-compare" layer the SI-4 fix agent proposed, because the two-sided O-C pin
already reveals that defect in both directions on every run.

**3. Amend the frozen spec with D-A and D-B — hours, not days. NOT BLOCKED. Unblocks two of Gate
A's three SKIPs.**
Both decisions are settled and recorded in the close-out plan; neither is in design spec §7 or §4.3.
Filing them is pre-data and permitted. Three of the five amendments decision D-E called for remain
unfiled (2026-08-01f and 01g are filed): the NIST operationalisation, the TolAnalyst optionality,
and the suite-integrity §8 C1 amendment. *Uncertain:* ROUND-2's enumeration of "five" does not map
cleanly onto 01f/01g, so exactly which three remain is ambiguous — reconciling ROUND-2 §D-E against
the filed amendment log would resolve it.

**4. P2.3 — fresh-clone receipt — small. BLOCKED on CI having run (it has). Unblocks Gate A's third
SKIP.**
Design is settled: the receipt is valid if its `commit_sha` is an *ancestor* of HEAD and
`git diff --name-only <sha>..HEAD` touches nothing **outside** `docs/`, `papers/`, `.superpowers/`,
`README*`, `LICENSE` — a **denylist**, because the allowlist form already missed `.gitattributes`
and `cosmic-ray.toml`. Its ceiling is a **self-report**: ancestor+clean-paths prevents staleness,
not forgery. Printing the workflow URL makes it checkable by a third party, not enforced. Disclose
that in the same sentence as the B4 registry-deletion ruling.

**5. Re-measure the B7 k-sweep — small. BLOCKED on nothing; must precede pre-registration.**
Restoring the twelfth reliability mate *tightened* the instrument: k=2 now fails at 0.9392 where it
previously passed at 0.9518. The disclosed bound ("reliably detects ≥2.5×; reliably fails to detect
≤1.5×; indeterminate at 2×") is now *better* than the disclosure claims, and the old sweep must not
enter the pre-registration. Gate A's headroom instance is **PARTIAL, not CLOSED**, and any instance
map must say so with a numeric bound.

**6. Phase 3.5 — public pre-registration. BLOCKED on 1, 3, 5. Blocks Phase 4 entirely.**
Needs human decisions, not code. Must carry a public OSF/AsPredicted timestamp *before* any corpus
generation. Publish the §7 tables **plus the corrections with the superseded text shown** — "publish
§7 verbatim" is withdrawn, because lines 227–228 state a falsehood about our own instrument. State
the per-part `min()` form explicitly: mistaking it for a sum is what produced the mate[8] defect.
Disclose that the anti-vacuity layer has never discovered an instance. Quote the **spec**, never a
ledger — roughly a dozen ledgers still carry the superseded 0.9982/tested=11 and they outnumber the
correct figure in a grep.

**7. Phase 4 — corpus, `metrics/`, `harness/`, `analysis/`, ≥8 baselines, E1–E5, Gates B and C.
BLOCKED on 6. UNESTIMATED.**
Optional extension worth recording now so it is a planned step rather than a reviewer's discovery:
AutoMate's BREP assemblies can serve as *geometry* with our tolerance schema applied on top. It does
not solve oracle independence, but it answers the criticism the current corpus is exposed to — that
the geometry is two synthetic plates with holes in a line.

**8. N-11 — scheduled adversarial review — ~3 review days, NOT BLOCKED, blocks nothing
mechanically, and is the highest-leverage item in the project.**
Three checkpoints, 0.75–1 day each plus 0.25 for the response: before pre-registration, before each
published number enters a draft, before Gate D. They do not overlap with engineering time. The
evidence is the whole of §5: layers ratchet, review discovers. One pass of this control found a
false statement inside a frozen document.

**Smaller carried items** (from `.superpowers/BLOCKERS.md`, block nothing): B2 the untested
OSError→AssertionError conversion (ruled: covered by O-B); B9 whole-file CRLF normalisation in
`_count_and_apply`, real fix costed at 15–25 lines and deliberately *not* scheduled, blast radius
bounded by a suffix allowlist; B10 restoration is exception-safe but not crash-safe; B11 nothing
enforces function-level test selectors; B12 ~84% of `iso286` mutation kills are mechanical table
pinning, so the kill headline overstates behavioural depth. Instances 5 and 6 are **FIXED-NO-LAYER**
— fixed and guarded by a specific test, but Layer 1's coverage is scoped to six modules under
`src/tolcad` while those live in `tests/` and `scripts/`.

---

## 7. Known unresolved contradictions

**The 100.00% mutation score is the live one, and it must not be re-pinned.**
`check_suite_integrity.py` exits 1 because the measured score reads 100.00 against a 95.89 ± 0.50
pin. Read it correctly: **the two-sided pin fired correctly on its first real encounter.** A
one-sided floor would have stayed silently green — which is precisely how `MUTATION_MEASURED`
previously drifted 2.04 pp, four times its own tolerance, *inside the layer built to catch drift*.

The score is not to be accepted on sight. SI-4 left 19 documented equivalent mutants plus an
enumerated 21 untriaged survivors; those cannot have vanished. Either the fix round killed more than
it recorded, or the denominator moved. **A perfect score appearing overnight, in a project whose
documented dominant failure mode is the test that cannot fail, is more likely a broken instrument
than a cured suite.** The most plausible benign cause is commit `380d36a`, which killed nine mutants
after 95.89 was measured — but that is a hypothesis, not a measurement, and 95.89 → 100.00 is larger
than nine kills over a ~650 denominator explains. Resolution belongs to P1.5, which must produce an
*enumeration*, not arithmetic over a score. **Do not re-pin until it does.**

**Secondary, all documented and none blocking:**

- The frozen design spec §7 still lists TolAnalyst as a blocking Gate A criterion while §4.3's prose
  and decision D-B say Gate A is clearable licence-free. Pick one in writing (item 3 above).
- Suite-integrity design §1 enumerates twelve instances; its prose, §4 and §8 say eleven. §8's
  distribution drops exactly the **Unencoded** row — the only one of the twelve no layer can catch.
  §8's success criterion also still asserts "Gate A remains untouched and still reports 6 PASS / 3
  SKIP", which amendment 2026-08-01g superseded. This is the outstanding C1 amendment.
- Instance *numbers* are unreliable. Only instances 2, 3, 4, 5, 6 and 10 are attested in code or
  spec text; the other six positions cannot be reconstructed. **Refer to instances by name.** Do not
  mint a new ordinal.
- `.superpowers/BLOCKERS.md` is a frozen inventory whose lines 10, 11, 32 and 78 are superseded; it
  carries an append-only reconciliation note saying so. Read it for narrative only.
- The ledger-reconciliation spec §2 records the declared-mutation registry size as **14 entries**
  and lists it among the quantities "checked and found NOT contested". The registry holds **15**:
  Task 6 added `y14-5-worked-example-boundary-shifted` after that figure was written, and the
  close-out ledger's own T9 entry says "fifteen critical guards". Stale by one, in a document whose
  purpose is to be the one place figures are not stale.
- That same spec's §3 table records `.superpowers/sdd/**` as ignored. A session in progress is
  reversing that decision (see §4, Gate D).
- The repo has **no `README` and no `LICENSE`** despite being public at
  `https://github.com/harshD42/TolAEG-CAD`. ROUND-2's Phase 0 listed both; neither exists.

---

## 8. Phase history

| Phase | Plan | Merge / final commit | Delivered |
|---|---|---|---|
| 0 + 2 — functional checker | `plans/2026-07-31-functional-checker.md` | `6d3dadf` (merge), through `8ac612a` | Repo scaffold; the six core modules; Tier 1 exact Y14.5, Tier 2 Monte Carlo, ISO 286 tables; `validation/` with the NIST and TolAnalyst harnesses and the import lint; `scripts/gate_a.py`. Ended with the multi-seed reliability estimator (amendment 2026-08-01e) after the single-seed version was found to be one Bernoulli draw with ~88% pass probability. |
| 3 — procedural generator | `plans/2026-08-01-procedural-generator.md` | `2c8a8f0` (merge) | `gen/`: spec, deterministic sampler, feature library, layout, CadQuery build, STEP AP242 + sidecar export; NIST PMI fetch/verify; AP242 semantic-PMI reader verified by execution. The difficulty-ladder repair moved d4 from 478/609 to 421/609. |
| 3.5a — pre-registration prep | `plans/2026-08-01-pre-registration-prep.md` | `5442926`, then `44658ba` | Closed four benchmark-integrity gaps: dropped line-to-line H7/h6 (a label that was sampling noise), gave fixed fasteners real tapped-hole geometry, recorded the projected tolerance zone B-4 assumes, committed an AP242 fixture as a fresh-clone positive control with `.gitattributes` binary marking, and derived the layout floors from their source tables. |
| 3.5b — ISO 273 traceability | `plans/2026-08-01-iso273-traceability.md` | `aa50b46`, then `a2f2186` | Every generator dimension now cites a standard: clearance holes carry their ISO 273 series grade at their own diameter, IT12–IT14 tabulated with the mm/µm split documented at the one conversion point, all 39 IT12–IT14 cells and the IT5–IT8 cells pinned. |
| Suite integrity | `plans/2026-08-01-suite-integrity.md` | `547ee68` (merge) | The three-layer gate: `check_suite_integrity.py` with a measured branch-coverage floor, the cosmic-ray mutation layer, and the declared-mutation registry with its own anti-vacuity contract (occurs-once, passes-at-baseline, restores byte-identical). |
| Close-out | `plans/2026-08-01-closeout.md` | `d7285f9` → `30eb333` (nine tasks, direct on `main`) | Tree-cleanliness finalizer (O-B); both integrity pins made two-sided; the reliability instrument repaired under construction rule D-D (amendment 01f); all four ladder counts and the corpus digest pinned on a pinned numpy; the tapped-hole constant, instance 10 and selector granularity guarded; Gate A split into measured vs attested with criterion 1 restored (amendment 01g); CI on ubuntu+windows exercising the CRLF corruption mode with the integrity layer off the push path; the observation-assignment table and the ledger reconciliation committed as tracked specs; the mutation lock. |

---

## 9. Operating rules for whoever picks this up

- `pytest` **mutates and restores tracked files** — `src/tolcad/{iso286,reliability}.py`,
  `src/tolcad/gen/{sampler,layout,features}.py`, and one tracked fixture. Never run it concurrently
  with `scripts/gate_a.py` or `scripts/check_suite_integrity.py`. This is now *enforced* by the
  mutation lock (both readers exit 2), not merely advised.
- Gate A/B/C/D thresholds in design spec §7 are **frozen**. Changing one after seeing data
  invalidates the result. Amending the spec with a logged *pre-data* correction is a different act
  and is permitted; there are seven such corrections on the record.
- No value may change in `_IT_MICRONS`, `_DEVIATION_MICRONS`, `_SIZE_BANDS`, `_CLEARANCE_HOLE_MM`,
  `TAPPING_DRILL_MM`, `_TOL_FRACTION_RANGE`, `_MIN_WALL_MM`, `_EDGE_MARGIN_MM`.
- Checker core stays numpy-only. `validation/` may import core; core may never import
  `validation/`.
- No research corpus before the pre-registration timestamp.
- Every headline number must reproduce with no SolidWorks licence.

    pytest                              # 428 tests
    pytest -m "not slow"                # skip Monte Carlo convergence
    python scripts/gate_a.py            # exits 1 today, by design
    python scripts/check_suite_integrity.py   # exits 1 today: the mutation pin is firing
