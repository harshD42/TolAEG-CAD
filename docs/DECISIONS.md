# tolcad — Decision Register

**Status:** compiled 2026-08-01 at `main` @ `30eb333`. Records no new measurement.
**Companions:**
`docs/superpowers/specs/2026-08-01-ledger-reconciliation.md` (one canonical value per contested
quantity — **read it for numbers; this file does not restate them**),
`docs/superpowers/specs/2026-08-01-observation-assignment.md` (the stopping criterion, worked).

## Why this file exists

Most of the decisions below existed only in `.superpowers/sdd/**/progress.md`. Those ledgers were
deliberately gitignored until 2026-08-01 and so did not survive a clone at all; they are now tracked
([P-6](#p-6)), but that only moves the problem — the rulings are scattered across ~19,000 lines of
contemporaneous, mutually contradictory hour-by-hour narrative, most of it superseded. The ledger
reconciliation lifted the contested *numbers* into a tracked spec; this file does the same for the
*rulings*. Without it a fresh session re-litigates settled questions — or, worse, silently reverses
one and nothing notices, because almost every entry here is a case where the naive "fix" is the
wrong answer.

This register is **append-only in spirit**: correct an entry by adding a superseding entry and
marking the old one, never by rewriting history. Every entry names *who* decided, because
"pre-registration-shaping choices are the human's, not the agent's" is itself a standing rule
(`.superpowers/sdd/2026-08-01-procedural-generator/progress.md:223-225`).

### Reading an entry

| Field | Meaning |
|---|---|
| **Kind** | `HUMAN RULING` · `FROZEN` · `DESIGN RATIONALE` · `DEFERRED` · `REVERSAL` |
| **Decision** | one sentence, the operative content |
| **Decided by / when** | human vs agent, and the date |
| **Why** | the reasoning, not the outcome |
| **Reopens if** | the concrete trigger that would legitimately re-open it |
| **Provenance** | `file:line` — the contemporaneous record |

`HUMAN RULING` means the human ruled in session and an agent recorded it. Agents may not reverse
one. An agent decision (`agent`) may be revisited by a later agent **with recorded reasoning**.

---

# 0. Do not re-litigate

Ten-second check before reopening an argument. Each line names the entry that settles it.

| Question someone will ask again | Answer | Entry |
|---|---|---|
| "Should we put `H7/h6` back in the sampled fit set?" | No. Its label is one Monte Carlo draw in 100k. | [B-1](#b-1) |
| "The ISO-fit labels are guessable from the shaft letter — bug?" | No, structural arithmetic. Documented and pinned, not fixed. Tier 2 contributes the *yield*. | [B-2](#b-2) |
| "`y14_5.py` needs projected zones — should the generator stop emitting them / should we add B-5?" | Generator always emits them; **B-5 stays unimplemented**. | [B-3](#b-3), [B-4](#b-4) |
| "The tapping drills should be nominal minus pitch — 6.75, 10.25?" | **No.** 6.80 / 10.20 are correct, from the ISO/R 235 preferred drill series. | [S-3](#s-3) |
| "`_IT_MICRONS` IT12–IT14 look 1000× too big." | Correct as stored. ISO 286-1 publishes IT01–IT11 in µm and IT12–IT18 in **mm**. | [S-1](#s-1) |
| "The tapped hole's tolerance band has no standard citation." | Deliberate. Flat, documented, standard-free, provably inert. Do not invent a citation. | [S-4](#s-4) |
| "The floating-fastener margin should be the pooled sum of both parts' slack." | **No.** Per-part `min()`. Already tried pooled; it was wrong for a standards reason. | [Y-1](#y-1) |
| "Gate A reliability should be re-measured at one seed / the mate set retuned." | No. Multi-seed aggregate; mate set, threshold, band and seed set are all fixed. | [G-2](#g-2), [G-3](#g-3), [I-9](#i-9) |
| "Gate A prints FAIL/SKIP — can we relax a §7 threshold?" | **No.** §7 thresholds are frozen; changing one after seeing data voids the result. | [G-1](#g-1) |
| "`scripts/gate_a.py` is frozen too, right?" | No — only §7 *thresholds* are. The file is amendable pre-data under a logged entry. | [G-8](#g-8) |
| "Publish §7 verbatim in the pre-registration?" | No — it contains a statement that was false of our own instrument. Publish tables **plus** corrections. | [G-6](#g-6) |
| "Make TolAnalyst a blocking Gate A oracle?" | No. Supplementary. Forced by §4.3, not chosen. | [G-5](#g-5) |
| "Score the checker against NIST assemblability ground truth?" | There is none. NIST is a PMI-**extraction** oracle; the limitation is stated. | [G-4](#g-4) |
| "Switch to numpy legacy `RandomState` for stream stability?" | No. Pin `numpy==2.4.1`. | [E-1](#e-1) |
| "The mutation score reads 100% against a 95.89 pin — just re-pin it." | **DO NOT.** That disagreement is the control working. Resolution belongs to P1.5. | [I-3](#i-3) |
| "Make the coverage/mutation checks simple floors again." | No. Two-sided by construction; a one-sided floor is how the pin drifted. | [I-2](#i-2) |
| "Layer 1 coverage is only ~95% — measure `gen/` too." | No. `gen/` is out of Layer 1 scope by design; including it measures an intended exclusion. | [I-1](#i-1) |
| "Add a control for X." | Only if its failure is a **silent false green** *and* you can name which of O-A…O-D fails to reveal it. | [P-1](#p-1), [P-2](#p-2) |
| "Add a fifth observation to the stopping criterion." | Human decision only. The list's closure is the terminating device. | [P-1](#p-1) |
| "Add a Layer 4." | Only when a defect review already caught **comes back**. Awareness is not a control. | [P-3](#p-3) |
| "The ledgers say 0.9982 / eleven instances / ~12 survivors." | Superseded. **Quote the spec, never a ledger.** | [P-5](#p-5) |
| "Rewrite the wrong figures in the old ledgers." | No. They are contemporaneous records. Reconciliation is append-only. | [P-4](#p-4) |
| "Should `.superpowers/sdd/` be tracked?" | It **is**, since 2026-08-01 — reversing an earlier recommendation. Review `.diff` artifacts stay ignored. | [P-6](#p-6) |
| "Where does a correction to this spec that is *not* a §7 threshold go?" | §14, never §7 — appending to §7 would edit frozen text. | [G-11](#g-11) |
| "Run `pytest` and `gate_a.py` at the same time." | Refused by a lock, exit 2. Not advice — enforced. | [I-10](#i-10) |
| "The registry can be defeated by deleting an entry and its guard name together." | Known and accepted (B4). Paper-trail mechanism; no in-repo fix exists. | [I-6](#i-6) |
| "Gate A reliability headroom is closed." | No — **improved, not closed**. 2–3×, disclosed with a CI-bounded k-sweep. | [I-9](#i-9) |
| "This plan snippet is the spec — implement it verbatim." | No. Six consecutive tasks found plan snippets that could not run or could not fail. | [P-7](#p-7) |

---

# 1. Benchmark scope, degeneracy and what gets frozen

<a id="b-1"></a>
### B-1 — Drop line-to-line fits (`H7/h6`) from the sampled set

- **Kind:** HUMAN RULING
- **Decision:** `SUPPORTED_FITS` is reduced to `("H7/g6", "H7/k6", "H7/p6")`; no sampled fit may be
  line-to-line at MMC.
- **Decided by / when:** human, 2026-08-01, at the Phase 3 review, before Phase 3.5a.
- **Why:** `H7/h6` has hole minimum and shaft maximum both exactly at nominal, so exact worst-case
  clearance is zero and the Monte Carlo verdict turns on whether any of 100,000 draws lands on the
  boundary. Measured across the corpus under explicit per-mate seeds it came out 85 True / 23 False
  with margins of only 1.0 or 0.99999 — one clearance failure in 1e5. "A fit whose ground truth
  turns on one sample in 100k is noise, not a test item." Under the accidental fallback `seed=0` it
  had been uniformly True, which is how it survived unnoticed.
- **Reopens if:** never as a *sampled* item without a new ruling. `iso286.fit_from_designation`
  still *supports* the designation; only sampling was withdrawn.
- **Provenance:** `docs/superpowers/plans/2026-08-01-pre-registration-prep.md:22,76`;
  `.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:12,56`;
  `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:260-263,328-331`.
  Executable guard: `tests/gen/test_features.py::test_no_supported_fit_is_line_to_line`.

<a id="b-2"></a>
### B-2 — I2 (ISO-fit labels predictable from the shaft letter) is documented and pinned, not fixed

- **Kind:** HUMAN RULING · DESIGN RATIONALE
- **Decision:** Tier 2 contributes the **clearance yield** to the benchmark; Tier 1 carries the
  boolean. The predictability of the `assembles` flag from the shaft letter is disclosed as a
  structural limitation and pinned by a test, not engineered away.
- **Decided by / when:** human, 2026-08-01 (pre-registration prep).
- **Why:** `montecarlo.py:57` defines `assembles = yield_frac >= 1.0` — zero interference anywhere
  in the tolerance range. For a hole-basis fit that means `hole_min > shaft_max`; with
  `hole_min == nominal` (H holes have zero lower deviation) and `shaft_max == nominal + es`, the
  verdict is True exactly when `es <= 0`, which *is* the definition of a clearance-class shaft
  letter (a–h) versus transition/interference (j–zc). It is arithmetic, not sampling, and it cannot
  vary with diameter — confirmed empirically over nominals 3–180 mm. The continuous yield *does*
  vary usefully. Suppressing the leak would mean changing the definition of `assembles`; disclosing
  it costs a paragraph.
- **Reopens if:** `test_iso_fit_verdict_is_fixed_by_the_shaft_letter_at_every_size` ever fails —
  then the structural argument is wrong and must be re-derived **before** the disclosure is relied
  on. Also if `assembles` stops being `yield_frac >= 1.0`.
- **Provenance:** `docs/superpowers/plans/2026-08-01-pre-registration-prep.md:24,26-30,115-139`;
  `.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:15-16,19-27`;
  `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:202,332`.

<a id="b-3"></a>
### B-3 — The generator always emits a projected tolerance zone, and records the field

- **Kind:** HUMAN RULING
- **Decision:** every `fixed_fastener` mate carries a positive `projected_zone_mm`, validated at
  construction, serialised into the sidecar, and **absent** from `to_check_dict()`.
- **Decided by / when:** human, 2026-08-01 (the I4 second pass, before any corpus generation).
- **Why:** `src/tolcad/y14_5.py:181-193` names a projected tolerance zone as a *load-bearing
  precondition* of the B-4 mathematics: without one, every fixed-fastener verdict is optimistic
  (unsafe) by the core module's own contract. The generator was that module's only producer and
  emitted none. Recording the field satisfies the precondition inside already-verified mathematics.
  It is excluded from `to_check_dict()` because B-4 has no `P` term — emitting it to the checker
  would imply the checker consumes it, which it does not.
- **Reopens if:** B-5 is ever implemented ([B-4](#b-4)), or per-part plate thicknesses land — the
  cross-object guard must then follow the **crossed part**, not the assembly scalar (residual R-f).
- **Provenance:** `docs/superpowers/plans/2026-08-01-pre-registration-prep.md:23,15`;
  `.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:13-14,122-125,253-259`;
  `src/tolcad/gen/spec.py:46-53,62-90,151-171`.

<a id="b-4"></a>
### B-4 — ASME Y14.5 Appendix B-5 stays unimplemented

- **Kind:** HUMAN RULING · FROZEN (for the pre-registration window)
- **Decision:** `y14_5.py` implements B-3 and B-4 only. B-5 (the non-projected fixed-fastener case,
  `H = F + T1 + T2·(1 + 2P/D)`) is **not** implemented, and adding new closed-form standards code
  to `y14_5.py` is out of scope.
- **Decided by / when:** human, 2026-08-01; re-affirmed and carried forward on the ISO 273 branch.
- **Why:** the B-4 mathematics is verified against the primary standard; B-5 would be new unverified
  standards code in a checker-core module immediately before a public freeze. The precondition is
  satisfied by the generator instead ([B-3](#b-3)), which is cheaper and does not touch a verified
  module. The pre-registration must state "B-4 only, so fixed verdicts **assume** a projected zone".
- **Reopens if:** the benchmark ever needs to score drawings *without* projected zones — then B-5 is
  required and this is a new verified-standards task, not an edit.
- **Provenance:** `docs/superpowers/plans/2026-08-01-pre-registration-prep.md:23,44`;
  `.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:13-14,125,266`;
  `.superpowers/sdd/2026-08-01-iso273-traceability/progress.md:67`;
  `src/tolcad/y14_5.py:181-193`; `.superpowers/closeout/ROUND-0-architect-plan.md:105`.

<a id="b-5"></a>
### B-5 — I4 (fixed and floating are geometrically identical) lands before any corpus generation

- **Kind:** HUMAN RULING · REVERSAL (of the "defer to a later pass" position)
- **Decision:** fixed-fastener mates get a **tapped** `hole_b` (sub-fastener diameter) so the two
  fastener kinds are structurally distinguishable in the exported geometry; this ships before Phase
  3.5, not after.
- **Decided by / when:** human, 2026-08-01. First deferred at the procedural-generator final review
  ("second pass"), then scheduled as the first item of pre-registration prep.
- **Why:** the two kinds use different Y14.5 formulas but drilled identical through holes in both
  plates, so the distinction was unlearnable from the reference geometry. That shapes what
  pre-registration freezes, and "far cheaper before pre-registration than after". Verified by
  execution first: a fixed mate with a Ø6.8 tapped `hole_b` against an M8 fastener returns
  `assembles=True`, because B-4 never reads `hole_b`'s size — and the *same* dict submitted as
  `floating_fastener` correctly raises. That asymmetry is what makes the kinds distinguishable, and
  it is pinned.
- **Reopens if:** thread geometry is ever modelled — today the kinds differ only by hole diameter,
  and the pre-registration must say so as a known limitation.
- **Provenance:** `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:208-211,334-336`;
  `docs/superpowers/plans/2026-08-01-pre-registration-prep.md:15,17`;
  `.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:17,29-35,90-94`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:107`.

<a id="b-6"></a>
### B-6 — The difficulty ladder must straddle 1.0 at every level with a rising failure rate

- **Kind:** HUMAN RULING
- **Decision:** `_TOL_FRACTION_RANGE` is tuned so that both verdict classes are present at **every**
  difficulty and the Tier 1 failure rate is strictly increasing d1→d4.
- **Decided by / when:** human, 2026-08-01, scoping the procedural-generator fix wave.
- **Why:** the original ladder was a cliff — Tier 1 mates could not fail below d4 by construction,
  so d1–d3 drew *all* their negatives from `iso_fit`, and combined with [B-2](#b-2) a model could
  score 100% below d4 by regexing the shaft letter. The anti-degeneracy guard that was supposed to
  catch this was provably blind: a flat ladder, `(0.0,0.0)` and `(5.0,5.0)` all passed it.
- **Reopens if:** the clearance-hole table changes — the ladder is calibrated against it and must be
  re-measured. Also if `layout.py`'s margin rationale (max applied fraction ≈ 1.34) is pushed higher.
- **Provenance:** `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:46-52,182-193,244-254,287-289`.
- **Note:** the reviewer's *suggested* replacement ranges were measured and **rejected** — they gave
  d4 zero assemblable Tier 1 mates, i.e. the same degeneracy inverted. Subagent suggestions are not
  automatically right; measure before adopting.

<a id="b-7"></a>
### B-7 — The tolerance schema belongs to the reference design, never invented per model

- **Kind:** FROZEN (methodological commitment)
- **Decision:** given a reference assembly with its ground-truth tolerance schema, that schema is
  applied to the *predicted* geometry. Tolerances are never assigned per-model post hoc.
- **Decided by / when:** human (design spec author), 2026-07-31.
- **Why:** otherwise the experiment measures our own tolerance assignment rather than the model.
- **Reopens if:** never within Paper 1's design.
- **Provenance:** `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md:114-118`.

<a id="b-8"></a>
### B-8 — Tier 3 mates are out of scope and stated as a limitation

- **Kind:** FROZEN
- **Decision:** freeform surface mates, kinematic mechanisms and form defects are excluded; tolerance
  loop length is bounded at ≤ 4 contributors.
- **Decided by / when:** human, 2026-07-31.
- **Why:** Tier 1 has *zero checker error* by construction (closed-form), so a Tier 1 failure is
  unambiguously the model's. Tier 3 needs C-space/polytope methods and would import checker error
  into the headline claim. Scope creep into Tier 3 is a named risk with this as its mitigation.
- **Reopens if:** never for Paper 1.
- **Provenance:** `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md:104-112,406,434`.

<a id="b-9"></a>
### B-9 — Absolute hole placement and per-assembly plate sizing

- **Kind:** REVERSAL · DESIGN RATIONALE
- **Decision:** `build.py` drills via `pushPoints` on a `CenterOfBoundBox` workplane (absolute
  positions), and plate size/pitch are derived per assembly by the CAD-free `tolcad/gen/layout.py`;
  `build_assembly` **refuses** an undersized plate.
- **Decided by / when:** agent, 2026-08-01, under human-scoped fix wave; controller-reproduced.
- **Why:** `.faces(">Z").workplane()` defaults to `centerOption="ProjectedOrigin"`, which inherits
  the parent workplane origin, so `.center(x,0)` was a *relative* offset — three requested holes
  produced two. Every exported STEP contradicted its own sidecar schema, invalidating anything
  derived from it. Fixing placement alone was insufficient: with correct absolute placement the
  fixed 40 mm plate overhung the edge in 195/200 seeds, hence per-assembly sizing.
  **Superseded ledger note:** the earlier P3-5 entry "the plate-edge overlap risk did not bite" is
  **wrong** — it rested on `isValid()`/`Volume()>0`, which is exactly the evidence class that cannot
  see this defect.
- **Reopens if:** never in this direction. `test_drilling_holes_removes_material` was rewritten to
  compare volume **removed**, not total, because a d4 plate is now bigger than a d1 plate — do not
  "restore" the total-volume comparison.
- **Provenance:** `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:55-56,161-180,205,232-242`.
- **Known breaking change, accepted:** the undersized-plate guard breaks hand-built specs that take
  the 40.0 mm default.

<a id="b-10"></a>
### B-10 — Every Tier 2 mate carries an explicit `mc_seed`, never the checker fallback

- **Kind:** DESIGN RATIONALE · REVERSAL
- **Decision:** `MateSpec` carries `mc_seed`/`mc_n`, emitted into the `iso_fit` branch of
  `to_check_dict`, serialised, and surviving `from_json`. The sampler assigns
  `mc_seed = 10_000 + seed*4 + index` — reproducible, collision-free, and **never 0**.
- **Decided by / when:** agent, 2026-08-01, human-scoped fix wave.
- **Why:** `spec.py` previously emitted no seed, so the checker silently fell back to `seed=0`.
  CLAUDE.md's "Tier 2 always reports a seed" was met only in `Verdict.detail`, not in the sidecar a
  reproducer actually reads. 0 is excluded precisely because it is the fallback — a mate carrying 0
  is indistinguishable from a mate carrying nothing.
- **Reopens if:** never. The `mc-seed-base-shifted` registry entry (`expect="pass"`) guards the
  independence of conclusions from the seed base.
- **Provenance:** `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:195-199,256-263`.

---

# 2. Standards transcription and traceability

<a id="s-1"></a>
### S-1 — ISO 286-1 publishes IT01–IT11 in µm but IT12–IT18 in **mm**; convert at the table boundary only

- **Kind:** DESIGN RATIONALE · REVERSAL (of CLAUDE.md's earlier blanket claim)
- **Decision:** `_IT_MICRONS` is micrometres throughout. The IT12–IT14 rows were multiplied by 1000
  on entry. Unit conversion happens at the `iso286.py` table boundary **and nowhere else**.
- **Decided by / when:** human read the primary standard 2026-08-01; agent implemented and corrected
  CLAUDE.md in the same task.
- **Why:** ISO 286-1:2010 Table 1 carries two separate span labels across the grade columns. Pasting
  the published IT12–IT18 figures directly makes them **1000× too small** — and 0.00043 mm is
  narrower than IT5, small enough to pass every ordering-free test in the suite. This is the exact
  shape of defect that produces a silently wrong published number. CLAUDE.md's previous blanket
  "ISO 286 tables publish micrometres" was false for precisely the grades that were being added.
- **Reopens if:** IT15–IT18 are ever added — same trap, same conversion, and the module docstring's
  TRANSCRIPTION SOURCE paragraph is the thing to read first.
- **Provenance:** `.superpowers/sdd/2026-08-01-iso273-traceability/progress.md:28-37,76-82`;
  `CLAUDE.md:9-12`; `src/tolcad/iso286.py` module docstring.
- **Guards:** all 39 IT12–IT14 cells and all 52 IT5–IT8 cells are pinned as a *second reading* off
  the primary-source scan, independent of `src/`; the tabulated grade set is **declared**
  (`sorted(_IT_MICRONS) == [5, 6, 7, 8, 12, 13, 14]`), not emergent. Registry entries
  `it7-row-transposed` and `it-grade-set-widened` were both watched failing.

<a id="s-2"></a>
### S-2 — Clearance-hole tolerances are H12/H13/H14 per ISO 273 series, not a flat constant

- **Kind:** HUMAN RULING
- **Decision:** the fine/medium/coarse clearance-hole series carry H12/H13/H14 respectively, cited to
  ISO 273-1979(E), replacing a single flat tolerance constant.
- **Decided by / when:** human, 2026-08-01, after reading the primary standard.
- **Why:** ISO 273's tolerance-field note is verbatim *"The following tolerance fields are given for
  information only, for use where it is desirable to specify tolerances: fine series : H12, medium
  series : H13, coarse series : H14."* **"For information only" means offered, not mandated** — the
  human chose to take the option so the schema cites the standard rather than an invented constant.
  Because that was a *choice*, the pre-registration must disclose it as one.
- **Reopens if:** never silently. Impact was measured and bounded before the change: hole
  `MMC = nominal + lower_dev` and `lower_dev` is 0, so the upper deviation **cannot** move a Tier 1
  verdict or any ladder point. If that stops being true, re-measure the ladder.
- **Provenance:** `.superpowers/sdd/2026-08-01-iso273-traceability/progress.md:14-20,39-54,65-66`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:105`.

<a id="s-3"></a>
### S-3 — ISO 2306 tapping drills come from the ISO/R 235 preferred series and are **not** nominal-minus-pitch

- **Kind:** DESIGN RATIONALE
- **Decision:** `TAPPING_DRILL_MM` holds the published ISO 2306-1972 Table 1 coarse-pitch values,
  including **M8 → 6.80** and **M12 → 10.20**. `6.75` and `10.25` are *wrong*.
- **Decided by / when:** human verified against the primary standard, 2026-08-01.
- **Why:** ISO 2306 Clause 0 states the drill is only *approximately* `D − P`; actual sizes are
  selected from the ISO/R 235 preferred drill series. A reader who "knows" the subtraction rule will
  see 6.80 as a rounding error and correct it. All seven coarse-pitch values match the standard
  exactly. The caveat is in the code: `src/tolcad/gen/features.py:19` says *do not "correct"* them.
- **Reopens if:** never for coarse pitch. A fine-pitch table would be a new transcription task
  against the same standard.
- **Provenance:** `.superpowers/sdd/2026-08-01-iso273-traceability/progress.md:22-27`;
  `src/tolcad/gen/features.py:19,85-89`;
  `.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:112-113`.

<a id="s-4"></a>
### S-4 — The tapped hole keeps a flat, documented, standard-free tolerance band

- **Kind:** HUMAN RULING
- **Decision:** `_TAPPED_HOLE_UPPER_DEV_MM` is a declared simplification with **no** standards
  citation, and none may be invented for it.
- **Decided by / when:** human, 2026-08-01, carried forward on the ISO 273 branch.
- **Why:** it is provably inert *twice over* — B-4's margin never references `hole_b.mmc`, and
  `mmc = nominal + lower_dev` so an upper deviation could not affect it even if it were read. A
  citation attached to an inert number would be a false claim of traceability in a branch whose
  entire purpose is traceability. Bounded, not pinned, deliberately.
- **Reopens if:** `y14_5` or `checker._feature` ever reads `.lmc` or `.min_size` on the fixed
  feature — then the number reaches a verdict and needs real provenance.
- **Provenance:** `.superpowers/sdd/2026-08-01-iso273-traceability/progress.md:67-70,232-235`;
  `src/tolcad/gen/features.py` docstring. Guard: registry entry `tapped-hole-upper-dev-nonzero`.

<a id="s-5"></a>
### S-5 — The fastener's inline deviation band was hoisted and given the same declared-inert treatment

- **Kind:** REVERSAL
- **Decision:** `sampler._tier1_mate`'s inline `-0.1/+0.0` fastener band became
  `_FASTENER_LOWER_DEV_MM` / `_FASTENER_UPPER_DEV_MM`, with an inertness argument attached and a pin
  over every sampled Tier 1 mate.
- **Decided by / when:** agent, 2026-08-01, after the whole-branch review found it (I-3).
- **Why:** it was uncited **and uncommented** — so the traceability branch's own completion claim
  ("the only remaining untraced number is the tapped hole's") was false, with the schema about to be
  frozen publicly. External feature ⇒ `mmc = nominal + upper_dev = nominal`, and
  `y14_5.fastener_assembles` reads only `.mmc`.
- **Reopens if:** the verdict path ever reads anything other than `.mmc` on the fastener (parked
  residual R-2). Note also (R-7): **`-0.1` IS published** — it round-trips into the sidecar via
  `AssemblySpec.to_json()`. Inert ≠ invisible; the pre-registration must name both declared-inert
  untraced numbers.
- **Provenance:** `.superpowers/sdd/2026-08-01-iso273-traceability/progress.md:226-236,268-272,301-307,324-325`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:105`.

<a id="s-6"></a>
### S-6 — Adding IT12–IT14 silently widened a checker-core public API; the widening was pinned, not reverted

- **Kind:** REVERSAL · DESIGN RATIONALE
- **Decision:** `H12/g12`, `H13/h13`, `H14/p14` now return a fit where they previously raised. That
  widening is **kept** (it is correct per ISO 286-1 Tables 4/5, which give g/h/p for all standard
  grades) and is now stated in the docstring and pinned by tests, including the surviving `k`
  IT4–IT7 restriction and the continued rejection of `H9/g9`.
- **Decided by / when:** agent, 2026-08-01, after the whole-branch review reproduced it (I-2).
- **Why:** the accepted input set of a checker-core public surface changed as an *unannounced side
  effect* with no test. The values were right; the silence was the defect.
- **Reopens if:** any new IT row is added — the accepted g/h/p set widens again. The grade-set
  declaration ([S-1](#s-1)) is what makes that loud instead of silent.
- **Provenance:** `.superpowers/sdd/2026-08-01-iso273-traceability/progress.md:216-222,263-267,296-300,339-340`.

<a id="s-7"></a>
### S-7 — Load-bearing literal floors must sit strictly **above** their derived requirements

- **Kind:** REVERSAL · DESIGN RATIONALE
- **Decision:** `_LITERAL_WALL_FLOOR_MM` and `_LITERAL_EDGE_FLOOR_MM` were raised to 3.8 and 1.9,
  strictly above their derived requirements (3.780 / 1.890), and both are guarded symmetrically by
  `test_the_literal_floors_are_not_below_the_derived_ones`. Production constants `_MIN_WALL_MM = 4.0`
  and `_EDGE_MARGIN_MM = 5.0` were **not** changed.
- **Decided by / when:** agent, 2026-08-01, over two rounds (the wall literal first, the edge literal
  after the review found the asymmetry).
- **Why:** the wall literal 3.7 had silently stopped being a floor once the ISO 273 tolerance change
  raised the true requirement to 3.78 — neither layout test noticed, because the derived test
  recomputes and the literal test passes at 4.0 ≥ 3.7. The edge literal was worse: `1.89` was
  already a **ulp below** its requirement `1.8900000000000001` and was passing on the epsilon alone.
  A guard against staleness that covers only one of two symmetric literals is the same bug in a new
  instance.
- **Reopens if:** the ladder ceiling, `_CLEARANCE_HOLE_MM` or `_HOLE_UPPER_DEV_MM` moves. Measured
  trip points: d4 hi > 1.52, or the M12-loose hole > 14.836, or `_HOLE_UPPER_DEV_MM` > 0.65, or
  `_MIN_WALL_MM` < 3.55.
- **Provenance:** `.superpowers/sdd/2026-08-01-iso273-traceability/progress.md:44-54,159-168,182-195,199-213,258-262`;
  `.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:193-217,284`.
- **Documentation correction recorded here because it is now committed:** the "5.5% headroom" figure
  was computed with a different denominator from its sibling "12.7%". Correct value is **5.8%**
  (excess-over-required). Fixed; recorded so nobody re-derives 5.5%.

---

# 3. The ASME Y14.5 model

<a id="y-1"></a>
### Y-1 — Floating fastener is a per-part `min()`, **not** a pooled sum

- **Kind:** REVERSAL (three states) · DESIGN RATIONALE · **highest re-litigation risk in the file**
- **Decision:**
  `floating: margin = min(H_a − F − T_a, H_b − F − T_b)`
  `fixed:    margin = (H_a − F) − (T_a + T_b)`  (`H_b` does not appear)
- **Decided by / when:** agent, 2026-07-31/08-01, after two wrong intermediate models and an
  explicit standards re-reading. Human ratified by accepting the branch.
- **Why, and the full history, because each superseded state is individually plausible:**
  1. **Original:** `fastener_assembles` ignored `hole_b`'s MMC entirely → same joint, opposite
     verdicts depending on argument order. Falsely **optimistic**. (Critical C1.)
  2. **First fix — `min(hole_a.mmc, hole_b.mmc)`. WRONG, and it was the controller's error.** For a
     *fixed* fastener `min()` always selects the tapped hole, whose MMC is physically meaningless;
     for *floating* it cross-pairs the smallest hole with the largest tolerance across different
     parts. Both falsely **pessimistic**. Existing tests could not catch it because every
     fixed-fastener test passed the same hole twice.
  3. **Second fix (`f77d200`) — pooled disc-intersection,
     `(H_a−F) + (H_b−F) − (T_a+T_b)`.** Geometrically correct and validated by a differential test
     against an independent reference implementation: 0 mismatches over 20,000 random draws.
  4. **Final — per-part `min()`.** The pooled form is *the correct answer to a different question*:
     whether one specific pair of parts can physically assemble. It is strictly more permissive.
     ASME Y14.5-2018 B-3 is explicit: *"Any number of parts with different hole sizes and positional
     tolerances may be mated, provided the formula H = F + T or T = H − F is applied to each part
     individually."* Y14.5 governs **drawing conformance and interchangeability** — each part must
     be acceptable against its own drawing without reference to the mating part's actual deviations.
     So the pooled form was wrong for a *standards* reason, not a geometric one.
- **Reopens if:** the project ever needs pairwise physical assemblability rather than drawing
  conformance — then the pooled form is right, and it is a **different function**, not an edit.
- **Anti-regression guard:** `test_per_part_rule_discriminates_against_pooled_model` exists solely to
  fail if pooling is reintroduced (H_a=8.6, T_a=0.65, H_b=8.2, T_b=0.0, F=8.0: per-part False,
  pooled True).
- **Provenance:** `src/tolcad/y14_5.py:105-133,114-122,221-233`;
  `.superpowers/sdd/2026-07-31-functional-checker/y145-per-part-fix.md:1-17,100-106`;
  `.superpowers/sdd/2026-07-31-functional-checker/progress.md:59,72-83,103-116`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:19-27`.
- **Stale record, flagged:** `.superpowers/sdd/2026-07-31-functional-checker/progress.md:108-110`
  still says the per-part model is "ALSO wrong (too conservative)". That sentence was true of the
  question then being asked and is false of the shipped model. The live adjudication is the
  `y14_5.py` docstring. See [X-1](#x-1).

<a id="y-2"></a>
### Y-2 — Ignoring the MMC bonus is **exact**, not merely conservative

- **Kind:** DESIGN RATIONALE
- **Decision:** the model evaluates at MMC and applies no bonus tolerance.
- **Decided by / when:** agent, 2026-08-01, with the proof written into the docstring.
- **Why:** substituting size-dependent clearance `(S_i − F)` and size-dependent applied tolerance
  `(T_i + |S_i − H_i|)` makes the `S_a`, `S_b` terms cancel exactly — the virtual condition `H − T`
  is size-invariant. So MMC evaluation *is* the exact worst case. A reader who "adds bonus
  tolerance" would be adding a term that provably cancels.
- **Reopens if:** a fixed feature distinct from the fastener shank (e.g. a press-fit locating pin)
  ever carries its own MMC modifier — the cancellation fails and the model becomes **unsafe**. The
  model therefore assumes RFS on the fixed feature in the `"fixed"` condition; that assumption is
  documented, not implicit.
- **Provenance:** `src/tolcad/y14_5.py:164-179`.

<a id="y-3"></a>
### Y-3 — `margin` is diametral, and the explicit `H < F` guard is load-bearing

- **Kind:** DESIGN RATIONALE
- **Decision:** `margin` is a diameter-of-clearance quantity; radial slack is `margin / 2` and is
  reported separately in `detail["radial_slack"]`. A hole the fastener must pass through is checked
  explicitly against `F` at MMC and raises `ValueError`.
- **Decided by / when:** agent, 2026-08-01 (NB-1 fix wave).
- **Why:** treating `margin` as radial silently halves or doubles the slack — the failure class that
  produced an earlier wrong model. The `H < F` guard exists because the algebra does not detect it:
  `H_a=7.9, H_b=9.0, T=0, F=8.0` evaluates to margin +0.9 "assembles" despite the fastener not
  fitting `hole_a` at all. For `"fixed"`, only `hole_a` is checked — `hole_b` is not a clearance
  hole, which is exactly what makes the tapped-hole design in [B-5](#b-5) valid.
- **Reopens if:** never. The asymmetric check is deliberate, not an oversight.
- **Provenance:** `src/tolcad/y14_5.py:141-146,148-162,210-219`.

<a id="y-4"></a>
### Y-4 — Tier 1 compares at `EPS = 1e-9`, no looser

- **Kind:** FROZEN
- **Decision:** `types.EPS = 1e-9`. Tier 1 is exact; no rounding, no wider tolerance.
- **Decided by / when:** human (project convention), 2026-07-31.
- **Why:** Tier 1's whole value is that closed-form conditions have *zero checker error*, so a Tier 1
  failure is unambiguously the model's ([B-8](#b-8)). Loosening `EPS` transfers checker error into
  the headline claim. The three ASME Appendix B worked examples all land at exactly 0.0 margin (float
  noise ~1e-16), so 1e-9 is already four to seven orders of margin over the real requirement — there
  is no engineering pressure to widen it.
- **Reopens if:** never without invalidating [B-8](#b-8)'s rationale.
- **Provenance:** `CLAUDE.md:13`; `src/tolcad/types.py:8`;
  `.superpowers/sdd/2026-07-31-functional-checker/y145-per-part-fix.md:108-110`.

<a id="y-5"></a>
### Y-5 — `position_tol_a/b` on `MateSpec` are the single source of truth

- **Kind:** DESIGN RATIONALE
- **Decision:** `to_check_dict()` injects `position_tol_a/b` into copies of the hole dicts,
  **overriding** any `position_tol` the input dicts carry.
- **Decided by / when:** agent, 2026-08-01 (procedural generator Task 2).
- **Why:** two places to set the same quantity is a drift hazard. Setting both is harmless; the
  dedicated fields win. Recorded because a later task will otherwise embed `position_tol` in hole
  dicts and be confused when it has no effect.
- **Reopens if:** the `virtual_condition` kind is ever sampled — `position_tol_b` is currently dead
  for it (only `position_tol_a` is used, for both hole and pin) and unexercised.
- **Provenance:** `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:18-27`.

---

# 4. Gate A, the pre-registration, and the freeze discipline

<a id="g-1"></a>
### G-1 — Gate A/B/C/D thresholds in design spec §7 are FROZEN

- **Kind:** FROZEN · **the single most important entry in this file**
- **Decision:** the threshold values in `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`
  §7 must not be revised. No post-data threshold change is permitted, ever.
- **Decided by / when:** human, 2026-07-31, as the project's founding integrity commitment.
- **Why — the reasoning matters more than the rule:** a threshold chosen *after* seeing data is not a
  test, it is a description. Pre-registration exists so that "strong finding" cannot be manufactured
  by moving the line; a registration timestamped after data generation is worthless, and reviewers
  punish unverifiable pre-registration claims harder than no claim at all. The design already
  survived one near-miss of exactly this shape: under v1's thresholds the project would have declared
  a "strong finding" for a metric with AUC = 1.0, because Spearman ρ against a binary outcome is
  ceiling-bounded by the base rate. That was caught **pre-data** and fixed by correction 2026-07-31b;
  the same change made after data would have been indefensible.
- **The seven pre-data corrections (a–g) are the *only* legitimate changes**, each logged, each
  labelled pre-data, each with its reason:
  | ID | Change | Reason |
  |---|---|---|
  | 2026-07-31a | Gate A convergence N 10k → 100k | ±0.5% was unachievable by *correct* code at N=10k; threshold unchanged |
  | 2026-07-31b | Gate B statistic ρ → AUC / Somers' D | ρ is base-rate ceiling-bounded; v1 thresholds uninterpretable |
  | 2026-07-31c | Gate B point estimates → CI bounds | point estimates reward noise: underpowered ⇒ "strong finding" |
  | 2026-07-31d | Gate D baseline reproduction → CADBench unified protocol | published numbers disagree by up to 15 points; ±5% unmeetable |
  | 2026-08-01e | Reliability = multi-seed aggregate, not one draw | see [G-2](#g-2) |
  | 2026-08-01f | Reliability mate set repaired under a construction rule | see [G-3](#g-3) |
  | 2026-08-01g | Gate A splits measured from attested; criterion 1 restored | see [G-7](#g-7) |
- **Reopens if:** **never after data generation.** Before data, a change is permitted only as a new
  numbered correction-log entry that states what was wrong and why the change is not motivated by an
  observed result.
- **Provenance:** `CLAUDE.md:37-40`; design spec `:205-280,275`; `.superpowers/BLOCKERS.md:68`;
  `docs/superpowers/plans/2026-08-01-closeout.md:24`.

<a id="g-2"></a>
### G-2 — Checker reliability is a multi-seed aggregate over a pre-registered seed set (correction 2026-08-01e)

- **Kind:** FROZEN · REVERSAL
- **Decision:** report the mean over seeds 0–199 with a bootstrap CI and the fraction of seeds
  passing, and compare the **mean** to 0.95. The 0.95 threshold, the mate set, the exclusion band and
  the seed set all stay fixed; only the *estimator* changed.
- **Decided by / when:** human, 2026-08-01, as a pre-data amendment.
- **Why:** as first implemented the criterion evaluated `verdict_stability` at one pinned seed. Across
  1000 seeds the value ranged 0.8333–1.0000 and 12.2% fell below 0.95 — so the reported PASS was one
  Bernoulli draw at roughly 88% pass probability. Separately, with twelve tested mates the reachable
  values quantise, making 0.95 *degenerate*: it silently means "zero flips out of twelve". Disclosed
  openly because the single-seed 1.0000 that was being printed is not a stable property of the
  checker. **Changing the estimator is legitimate pre-data; changing the threshold would not be.**
- **Reopens if:** never. Any temptation to retune the mate set to move the number is post-hoc
  instrument tuning — see [I-9](#i-9).
- **Provenance:** design spec `:223-233`;
  `.superpowers/sdd/2026-07-31-functional-checker/progress.md:117-125`.

<a id="g-3"></a>
### G-3 — D-D: the reliability mate-set repair uses a **construction rule**, which determines the number rather than choosing it (correction 2026-08-01f)

- **Kind:** HUMAN RULING · REVERSAL · **most dangerous to lose**
- **Decision:** every sensitive-band mate is rebuilt so that it has **exactly one binding part at
  ±3.5e-4, with every other part slack at ≥10×**. The resulting mean is whatever that rule produces.
- **Decided by / when:** human, 2026-08-01 (decision D-D), after two independent reviewers produced
  two *different* repaired means from the same stated intent.
- **Why — the whole point is the shape of the decision, not the value:**
  `gate_a.py:108` documented a reliability mate's margin as a **SUM** of both parts' slack, while
  `y14_5.py:228` implements ASME B-3's per-part **`min()`** ([Y-1](#y-1)). `min(0.0, 3.5e-4) = 0.0`,
  so the mate intended to sit inside the sensitive band sat at *exactly zero*, fell in the exclusion
  band, and was silently dropped — `tested` fell from 12 to 11 while `tested > 0` stayed green and
  the published mean stayed plausible. A second mate had the identical defect latent, surviving only
  because `min()` picked its negative branch. Because "repair mate[8]" was under-specified, QA
  measured one repaired mean and the architect measured another; **until the construction was
  specified, no repaired number could be quoted.** Specifying the rule removes the choice.
  The construction is *also* why the repair is provably a bug fix and not post-hoc tuning: it was
  found by adversarial review before any data existed, and the verdict did not move.
- **Reopens if:** never as a *choice*. If `_RELIABILITY_MATES` or `_RELIABILITY_EPSILON` ever changes,
  the k-sweep must be re-measured ([I-9](#i-9)) and the construction rule re-applied, not re-argued.
- **Two consequences that must not be lost:**
  - The frozen §7 correction-01e sentence *"at 12 tested mates the only values reachable near the
    threshold are 1.0000 and 0.9167"* was **false when written** (eleven were tested) and is **true
    of the repaired instrument**. Correction 01f records both facts. This is why [G-6](#g-6) forbids
    publishing §7 verbatim.
  - The **3.5e-4 sensitive-band magnitude was chosen after the seed was pinned.** It is a free
    parameter — a smaller value fails more often — and must be declared in the paper as a design
    choice, never presented as forced.
- **Provenance:** `docs/superpowers/plans/2026-08-01-closeout.md:18`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:24-27,31-37,100-105`;
  `.superpowers/sdd/2026-08-01-closeout/task-3-report.md:1-60`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:16-46`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:60-64`;
  design spec `:234-250,277-280`.
- **Instructive failure worth keeping:** the test written *into the plan* to prevent recurrence
  contained the same blind spot — it bound the band to `BOUNDARY_BAND × ε` (2e-4), which is the
  band's **floor**, not its ceiling, and would have passed the latent defective mate while falsely
  failing two healthy ones. Three artifacts — both proposed repairs *and* the test meant to prevent
  their recurrence — converged on one misreading. See [P-7](#p-7).

<a id="g-4"></a>
### G-4 — D-A: the NIST oracle is split, and the missing ground truth is stated as a limitation

- **Kind:** HUMAN RULING
- **Decision:** NIST becomes a PMI-**extraction** oracle scored against its published annotations,
  **and** the paper states plainly that no public assemblability ground truth exists for generative
  CAD.
- **Decided by / when:** human, 2026-08-01 (decision D-A). **Settled by measurement, not preference.**
- **Why:** all 17 NIST AP242 files contain **zero** `NEXT_ASSEMBLY_USAGE_OCCURRENCE` entries — they
  are single parts, so TolAnalyst has nothing to open and cannot supply the missing column. NIST
  publishes annotation semantics, not assemblability verdicts, and `data/nist_pmi_expected.csv` does
  not exist. The predicate "decidable case" in §7's frozen threshold is defined nowhere, so an empty
  denominator would trivially satisfy "100% on decidable cases".
  **The rejected option is the important part of this ruling:** NIST's download page states in prose
  that FTC 07/08/09/10 fit together and CTC 02/04 do. That is design intent, not published ground
  truth, is not in the fetched archive, and is **uniformly positive** — six cases, all True, zero
  negatives. A ground-truth column derived from it, scored against the frozen 1.00 threshold, would
  be cleared perfectly by a checker hard-coded to `return True`. That is *worse than no oracle*: it
  manufactures a Gate A PASS that discriminates nothing.
- **Reopens if:** a genuinely published assemblability dataset appears (e.g. NIST MTC / box assembly
  with CMM data). Even then the verdict would be **derived** by us, and the derivation must be
  published.
- **Provenance:** `docs/superpowers/plans/2026-08-01-closeout.md:15`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:15-18`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:133-153`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:25`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:67-76`.
- **Still open:** the operationalisation of "decidable case" must be fixed **before any case is
  inspected** and go into the pre-registration.

<a id="g-5"></a>
### G-5 — D-B: TolAnalyst is supplementary, not blocking

- **Kind:** HUMAN RULING
- **Decision:** SolidWorks TolAnalyst is a supplementary black-box oracle. It cannot block Gate A.
- **Decided by / when:** human, 2026-08-01 (decision D-B). **Forced, not chosen.**
- **Why:** design spec §4.3 requires every headline number to reproduce with no SolidWorks licence,
  and project memory records that inverting this would make the co-author's access *"a reproducibility
  liability instead of a credibility asset"*. §4.3 and §7's prose already said licence-free while the
  §7 *table* and `gate_a.py` implied otherwise; this picks one in writing. Agreement rates only —
  never mechanism, never internals (IP constraint).
- **Reopens if:** never. Note the compositional fact this resolves: with TolAnalyst licence-gated and
  NIST lacking ground truth ([G-4](#g-4)), Gate A had **no clearable external-oracle route at all**.
- **Provenance:** `docs/superpowers/plans/2026-08-01-closeout.md:16`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:19-22`;
  design spec `:131-137,288`; `CLAUDE.md:17`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:146-148`.

<a id="g-6"></a>
### G-6 — The pre-registration publishes §7's tables **plus** the corrections with superseded text shown, not §7 verbatim

- **Kind:** HUMAN RULING (D-E) · REVERSAL
- **Decision:** "publish §7 verbatim" is **withdrawn**. Publish the tables, the complete correction
  log, and the superseded text visibly marked. File **all five** pre-data amendments.
- **Decided by / when:** human, 2026-08-01 (decision D-E), on the architect's recommendation over
  QA's narrower count of two.
- **Why:** §7 lines 227–228 state a falsehood about our own instrument ([G-3](#g-3)) — checkable by a
  reviewer in twenty seconds. Publishing it verbatim would publish that falsehood. And *"a long
  pre-data correction log is a credibility asset; a short one bought by leaving false statements in
  place is not."* The pre-registration must also state the per-part `min()` form explicitly, because
  mistaking it for a sum is precisely what produced the defect.
- **Reopens if:** never. The five amendments are: the fresh-clone estimator; the reliability mate set
  plus the false "12 tested / 0.9167"; the NIST operationalisation; TolAnalyst optionality;
  suite-integrity design §8's success criterion.
- **Provenance:** `docs/superpowers/plans/2026-08-01-closeout.md:20`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:28`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:85-89,135-140`.

<a id="g-7"></a>
### G-7 — Gate A distinguishes **measured** rows from **attested** rows, and criterion 1 is restored (correction 2026-08-01g)

- **Kind:** REVERSAL · DESIGN RATIONALE
- **Decision:** every Gate A row prints its evidence kind as `VERDICT(measured|attested)`; attested
  rows print who attested, when, and against which edition and table; the report foots a tally
  stating the split. §7's criterion 1 (agreement with published Y14.5 worked examples) is restored as
  its own **measured** row pointed at three ASME node IDs, with the old "Y14.5 self-consistency"
  check retained as informational.
- **Decided by / when:** agent, 2026-08-01, under the human's D-E amendment authority; architect
  push-back P-1 against QA's stronger claim.
- **Why:** two rows PASS iff a marker string is *absent* from source — that is a human attestation,
  and reported inside an undifferentiated "6 PASS" it reads as a measurement. Separately, criterion 1
  had been **renamed** in the harness to "Y14.5 self-consistency", whose own note admits it is
  "arithmetic derived from the same two unverified formulas the implementation uses" — so §7's
  criterion 1 was reported by nothing. QA concluded it was unmeasurable; the architect verified by
  collection that the three Appendix B worked examples *are* encoded as tests at the standard's own
  inputs (B-3 F=6.0 H=6.44 T=0.44; B-4 T=0.22; B-4 unequal split T1=0.18 T2=0.26), so the
  self-consistency objection does not reach them. A criterion was **added**; none weakened.
- **Reopens if:** never in the direction of collapsing the split. An attested row is not a
  measurement and must never be counted as one.
- **Provenance:** design spec `:251-273`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:150-157`;
  `.superpowers/sdd/2026-08-01-closeout/task-6-report.md:123,156-162,180`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:159-168`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:39-47`.
- **R1 ruling attached (implementer's, correct):** the restored criterion 1 is a *published Gate A
  number*, and cosmic-ray never runs `gate_a.py`, so Layer 2 structurally cannot reach it. Without a
  Layer 3 entry the new published number would have had **no layer at all**. Hence registry entry
  `y14-5-worked-example-boundary-shifted`, watched failing.

<a id="g-8"></a>
### G-8 — `scripts/gate_a.py` is **not** frozen; only §7 thresholds are

- **Kind:** DESIGN RATIONALE · precedent
- **Decision:** `gate_a.py` may be amended pre-data under a logged, labelled correction-log entry.
- **Decided by / when:** established by correction 2026-08-01e (which already amended it pre-data);
  restated explicitly in the close-out plan.
- **Why:** CLAUDE.md freezes the **thresholds in design spec §7**, not a file. Reading the freeze as
  covering `gate_a.py` would have made Gate A permanently unable to report criterion 1 honestly
  ([G-7](#g-7)) and permanently unable to close its fresh-clone SKIP. Note this cuts both ways —
  earlier work correctly refused to touch it (`.superpowers/BLOCKERS.md:68` says "scripts/gate_a.py
  untouched"), so the precedent must be cited explicitly whenever it is edited.
- **Reopens if:** after pre-registration. Then `gate_a.py` edits become post-data and require the
  same scrutiny as a threshold change.
- **Provenance:** `docs/superpowers/plans/2026-08-01-closeout.md:24`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:68-70`;
  `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:87`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:21`.

<a id="g-9"></a>
### G-9 — The four ladder counts and the corpus digest are pinned executably and will be frozen at pre-registration

- **Kind:** FROZEN (pending) · REVERSAL
- **Decision:** all four exact Tier 1 ladder counts plus the corpus digest are pinned two-sided by
  `tests/gen/test_ladder_pin.py` over a written-down recipe in `scripts/measure_ladder.py`, on a
  pinned numpy. **Values: see the reconciliation spec §1, "Tier 1 ladder".**
- **Decided by / when:** agent, 2026-08-01, forced by QA finding A4/F2.
- **Why:** the four numbers appeared in BLOCKERS.md and five ledgers and would have gone straight
  into the pre-registration **pinned by nothing executable**. The only committed guard was a
  monotonicity assertion plus bands over the two *endpoints* at 80 seeds, not 200; d2 and d3 had no
  band at all. Demonstrated, not argued: mutating only `_TOL_FRACTION_RANGE[2]` moved d2 by up to
  19.3 percentage points with **every guard green** in 30 of 35 candidates. The corpus digest was
  additionally unreproducible because its recipe was never recorded.
- **Reopens if:** never silently. A ladder change is a benchmark change and must be a logged decision
  with a re-measurement; the `ladder-d2-row-shifted` registry entry exists to prove the pin notices a
  **middle-row** change, which is the case the old guard missed.
- **Provenance:** `.superpowers/closeout/ROUND-1-qa-critique.md:77-88`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:15,50`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:38-41,144-146`;
  `docs/superpowers/specs/2026-08-01-observation-assignment.md:87`.

<a id="g-10"></a>
### G-10 — Phase 3.5 ordering: no research corpus may be generated before the public pre-registration

- **Kind:** FROZEN
- **Decision:** nothing generates corpus data until the pre-registration is posted (design spec §12).
  Measurement sweeps that write nothing are fine; committed test batches stay small.
- **Decided by / when:** human, 2026-07-31 (design spec v2), enforced in every plan since.
- **Why:** a pre-registration timestamped after data generation is worthless. This is the reason the
  ISO 273 traceability work, the I4 repair and the ladder pin all had to land *before* the freeze
  rather than after — they change what gets frozen.
- **Reopens if:** never. It is the ordering constraint the whole phase plan exists to protect.
- **Provenance:** design spec `:413-428`; `.superpowers/BLOCKERS.md:26,71`;
  `docs/superpowers/plans/2026-08-01-pre-registration-prep.md:43`;
  `.superpowers/sdd/2026-08-01-iso273-traceability/progress.md:354`.

<a id="g-11"></a>
### G-11 — Corrections to non-threshold material go in design spec **§14**, never in §7

- **Kind:** DESIGN RATIONALE · FROZEN (convention)
- **Decision:** the design spec carries **two** correction logs. §7's is reserved for the
  pre-registered Gate A/B/C/D thresholds and their estimators. §14 holds post-approval, pre-data
  corrections to everything **else** in the document. Same form — superseded text shown, never
  overwritten, reason stated — different scope.
- **Decided by / when:** agent, 2026-08-01.
- **Why the split is not bureaucratic:** appending a non-threshold correction to §7's log would have
  forced an edit to its sentence *"All seven predate any experimental data"* — **frozen text**
  ([G-1](#g-1)). Without a second home, every correction to the document would either have to
  violate the freeze or go unrecorded. A reader who "tidies" the two logs into one re-creates that
  bind.
- **First entry, `2026-08-01h` (pre-data):** the literature corpus is **111 papers, not 95**. Three
  statements are superseded — the Status line, §0's opening, and §12's Phase 1 row. **The figure was
  false when written, not overtaken by later work:** the v2 revision commit is itself titled
  "…111-paper literature review", and `papers/literature/INDEX.md` said 111 in that same commit.
  Verified three independent ways. It cannot move a gate verdict in either direction — Gate D's
  "≥ 80 papers reviewed" is met at either figure — which is precisely why it is safe to make
  pre-data. **Nothing in §7 is touched.**
- **Reopens if:** never. After pre-registration, a §14 entry becomes a post-data correction and needs
  the same scrutiny as any other.
- **Provenance:** design spec §14 and its amendment banner; `papers/literature/INDEX.md`;
  `scripts/verify_literature.py`.

---

# 5. Environment and reproducibility

<a id="e-1"></a>
### E-1 — D-C: pin `numpy==2.4.1` exactly; do **not** switch to legacy `RandomState`

- **Kind:** HUMAN RULING
- **Decision:** `numpy` is pinned exactly. `default_rng` stays; the legacy `RandomState` API is not
  adopted.
- **Decided by / when:** human, 2026-08-01 (decision D-C). The architect held its recommendation
  *loosely* and flagged this as **irreversible after Phase 3** — it was still taken.
- **Why:** NEP 19 guarantees stream stability only for legacy `RandomState`, not `Generator`, and
  `default_rng` drives three published quantities: the sampler (the ladder), `montecarlo` (every
  Tier 2 verdict **and** Gate A's frozen ±0.5%-at-N=100k convergence criterion), and
  `verdict_stability`. So the ladder reproduces today but nothing made it reproduce for a reviewer in
  2027. Switching would have burned a day at the worst possible moment, invalidated every ledger
  figure, changed all four ladder counts, and put a soft-deprecated API in a 2026 artifact — while
  Gate D already allows ±1% for sampled quantities. Pinning buys the same reproducibility for a line.
- **Reopens if:** effectively never — after Phase 3 the ladder counts are frozen and a stream change
  invalidates them. The pre-registration must state that the ladder is **conditional on
  numpy==2.4.1**, and the pin's failure message prints `numpy.__version__`.
- **Provenance:** `docs/superpowers/plans/2026-08-01-closeout.md:17`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:23`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:17,51`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:186-191`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:79-83,149-150`.

<a id="e-2"></a>
### E-2 — Committed binary fixtures require a `.gitattributes` rule; the working tree is not evidence about the blob

- **Kind:** DESIGN RATIONALE · REVERSAL
- **Decision:** `.gitattributes` carries `*.stp binary`. Any future committed binary fixture needs an
  equivalent rule.
- **Decided by / when:** agent (implementer, out of brief), 2026-08-01; reviewer judged it justified
  rather than scope creep.
- **Why:** the repo has `core.autocrlf=true`, which **silently normalised** the NIST `.stp` fixture's
  CRLF to LF on commit — storing a 391,739-byte blob while the provenance note claimed 396,445
  byte-identical bytes. Invisible locally, because checkout re-expands LF→CRLF; a clone with a
  different `autocrlf` would have received a mangled fixture, defeating the entire point of
  committing it. **`"it looks right in my working tree" is not evidence about the blob."**
- **Reopens if:** `.gitattributes` gains a later `* text=auto` line — it is **last-match-wins**, so
  appending that silently re-arms the bug with a green suite. Guard: `assert_is_the_nist_original`
  plus `tests/test_gitattributes_clone.py`.
- **Provenance:** `.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:158-170,172-181,243-252,267-269`.
- **History deliberately not rewritten:** intermediate commit `d312ad6` still contains the corrupt
  blob. Two commits were kept rather than squashed, because the history honestly recording the defect
  and its fix is worth more than a tidy single commit. No clone lands on `d312ad6`; anyone bisecting
  precisely to it gets the wrong fixture.

<a id="e-3"></a>
### E-3 — The Windows CI leg does **not** set `autocrlf=true`; the brief's causal story was backwards

- **Kind:** REVERSAL · DESIGN RATIONALE
- **Decision:** no `git config core.autocrlf true` step was added to the Windows CI job. The reason is
  a comment block in `ci.yml`.
- **Decided by / when:** agent, 2026-08-01, correcting the plan.
- **Why:** the plan asserted `autocrlf=true` *exposes* a CRLF corruption. Measured: it **hides** it —
  `autocrlf=true` self-heals on checkout, while `input` and `false` expose it. More fundamentally the
  corruption is a **commit-time** event (a contributor's `git add`/`commit`), and CI never commits.
  Forcing `autocrlf=true` on checkout would make a corrupted commit look fine. The real coverage
  already exists in `tests/test_gitattributes_clone.py`, which parametrises `core.autocrlf` across
  `true`/`input`/`false` in its own nested clones.
- **Reopens if:** someone re-reads ROUND-0 F4 ("ubuntu-latest defaults to autocrlf=false, so a
  Linux-only CI exercises the SAFE direction") and re-adds the step. F4's conclusion — that a
  Linux-only CI proves nothing about this — stands; its proposed mechanism does not.
- **Provenance:** `.superpowers/sdd/2026-08-01-closeout/progress.md:181-189`;
  `.superpowers/sdd/2026-08-01-closeout/task-7-report.md:49-140`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:19`.

<a id="e-4"></a>
### E-4 — The Layer 2 integrity job is gated **off** the push path

- **Kind:** DESIGN RATIONALE
- **Decision:** CI has two jobs. `suite` runs on ubuntu + windows on every push. `integrity` (Layer 2
  mutation testing) runs on `workflow_dispatch` and a weekly schedule only.
- **Decided by / when:** agent, 2026-08-01, per architect finding F12.
- **Why:** Layer 2 takes roughly 25 minutes, not "a few minutes". **A gate people route around is
  worse than no gate.**
- **Reopens if:** Layer 2 gets materially faster.
- **Provenance:** `.superpowers/closeout/ROUND-0-architect-plan.md:35,60`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:100-101`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:181-189`.

<a id="e-5"></a>
### E-5 — The NIST archive download was approved for exactly one URL

- **Kind:** HUMAN RULING
- **Decision:** the ~14 MB `nist.gov` PMI conformance suite download is approved. **Approval covers
  that one URL only.**
- **Decided by / when:** human, 2026-08-01, asked and answered in session.
- **Why:** network fetches are not implicitly authorised; the scope was stated narrowly at the time so
  a later agent cannot generalise it. The payload is never committed (`data/nist_pmi/` is gitignored)
  and is reproducible via `scripts/fetch_nist_pmi.py`.
- **Reopens if:** any other URL. A new download needs a new approval.
- **Provenance:** `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:68-70`; `.gitignore`.

<a id="e-6"></a>
### E-6 — `validation/` is optional and strictly one-directional

- **Kind:** FROZEN
- **Decision:** `validation/` may import core; **core may never import `validation/`**. The checker
  core (`types`, `y14_5`, `iso286`, `montecarlo`, `checker`, `reliability`) stays numpy-only and
  CAD-free; `spec.py`, `features.py`, `sampler.py` and `layout.py` must also remain CAD-free.
- **Decided by / when:** human, 2026-07-31 (design spec §5).
- **Why:** every headline number must reproduce with no SolidWorks licence and no CAD stack. If core
  could reach into `validation/`, the licence dependency would leak into the headline path — the
  named risk "reproducibility broken by SW dependency", whose mitigation *is* this rule.
- **Reopens if:** never.
- **Provenance:** design spec `:151-155,407`; `CLAUDE.md:15-16`;
  `docs/superpowers/plans/2026-08-01-pre-registration-prep.md:37-39`.
- **Enforcement note, load-bearing:** `pyproject` `pythonpath = ["src","."]` is necessary (because
  `validation/` sits outside the installed package) but it **removed the runtime
  `ModuleNotFoundError` backstop**. The AST import-lint in `tests/test_architecture.py` is therefore
  the *sole* enforcement, hardened against `exec`/`eval`. Do not weaken it, and do not assume the
  import would fail at runtime — it would not.

---

# 6. Suite integrity: the three layers and their pins

<a id="i-0"></a>
### I-0 — Build the anti-vacuity machinery now, even though it satisfies no gate criterion

- **Kind:** HUMAN RULING
- **Decision:** the suite-integrity branch was built before Phase 4, with its own framing recorded
  honestly: **it satisfies no gate criterion and is not on the critical path to Gate B.**
- **Decided by / when:** human, 2026-08-01, shown that framing explicitly and choosing it anyway.
- **Why:** it is insurance on the numbers Phase 4 will produce. Phase 4 is where a "test that cannot
  fail" stops being embarrassing and becomes a published number that is wrong. Recorded so nobody
  later mistakes it for gate work — or, conversely, deletes it as non-essential.
- **Reopens if:** never retroactively.
- **Provenance:** `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:13-23`;
  `docs/superpowers/specs/2026-08-01-suite-integrity-design.md:24-28`.

<a id="i-1"></a>
### I-1 — Layer 1 coverage is scoped to the **six core modules**; `gen/` is omitted

- **Kind:** REVERSAL · DESIGN RATIONALE
- **Decision:** coverage is measured over `types`, `y14_5`, `iso286`, `montecarlo`, `checker`,
  `reliability` only. `gen/` is omitted via `[tool.coverage.run]` in `pyproject.toml`, with the reason
  recorded there.
- **Decided by / when:** agent, 2026-08-01, in the SI-3 fix round after an external review.
- **Why:** the first floor was measured with `--cov=src/tolcad`, which pulls in `~222` statements of
  `gen/` that the core test subset never exercises **by design** — an intended permanent exclusion.
  The consequence was not a cosmetic scope error: core coverage could have **halved** without
  tripping the floor. `gen/` is a non-goal for Layer 1 (CadQuery mutants are slow and frequently
  geometrically meaningless) and is covered by Layer 3 instead, which is where its historical
  instances actually lived. Deleting the omit is not silent — the number collapses and the gate fails.
- **Reopens if:** `gen/` ever gets a fast, meaningful mutation story. Note that earlier coverage
  figures differ by **scope**, not drift; comparing across the scope change is a category error.
  Values: reconciliation spec §1, "branch coverage".
- **Provenance:** `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:155-163`;
  `docs/superpowers/specs/2026-08-01-suite-integrity-design.md:27,55-61`.
- **Recorded irony:** the layer built to catch metrics that cannot fail shipped one of its own, and it
  took an external review to see it.

<a id="i-2"></a>
### I-2 — Coverage and mutation pins are **two-sided**, not floors

- **Kind:** REVERSAL · **most dangerous to lose**
- **Decision:** both checks fail when `abs(measured − PINNED) > TOLERANCE`, with a distinct message
  for upward detachment. `COVERAGE_MEASURED`/`MUTATION_MEASURED` + `TOLERANCE`, not `FLOOR`.
- **Decided by / when:** agent, 2026-08-01, forced by QA finding A7.
- **Why — this is the entry a maintainer is most likely to undo, thinking they are simplifying:**
  a one-sided floor **never flags an improvement**, so the pin detaches silently the moment the next
  test lands. That is exactly how `MUTATION_MEASURED` drifted **four times its own tolerance** while
  passing green — *inside the layer built to catch drift*. Re-pinning without going two-sided would
  restore the identical condition. The comment "raising the pin is routine" is not a control: nothing
  makes you, and R5 says awareness has demonstrably failed.
  It then **fired on its first real encounter**, reporting a genuine upward drift a one-sided floor
  would have swallowed.
- **Reopens if:** never. A one-sided floor is a known-defective design here.
- **Provenance:** `.superpowers/closeout/ROUND-1-qa-critique.md:121-129`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:94-98,159-171`;
  `docs/superpowers/specs/2026-08-01-observation-assignment.md:34-36,83`;
  `.superpowers/BLOCKERS.md:90-94`.
- **Prior instance of the same class:** `MUTATION_FLOOR` originally compared a **raw float** against
  its own 2-decimal display rounding, so the gate was already failing deterministically on an
  unchanged tree — it would have cried wolf on first use, which is how gates get disabled.

<a id="i-3"></a>
### I-3 — DO NOT RE-PIN the mutation score to its current measurement

- **Kind:** HUMAN-ADJACENT STANDING ORDER · DEFERRED · **most dangerous to lose**
- **Decision:** the mutation pin and the last measurement **disagree by design**. Do not re-pin.
  Resolution belongs to P1.5 (the serialised Layer 2 re-measure plus full survivor re-triage).
  Values: reconciliation spec §1, "mutation score".
- **Decided by / when:** agent, 2026-08-01, recorded in the ledger, BLOCKERS.md **and** the tracked
  reconciliation spec — three places, because it is a one-keystroke mistake.
- **Why:** the two-sided pin fired correctly ([I-2](#i-2)); re-pinning would silence a working
  control. The observed score is *perfect*, and SI-4 left a documented set of equivalent mutants plus
  an untriaged remainder that should not have vanished — either the fix round killed more than it
  recorded, or the denominator moved. **Given this project's history, a perfect score is exactly the
  shape that warrants scrutiny rather than acceptance.** Recorded, not believed.
- **Reopens if:** P1.5 runs — one clean cosmic-ray run alone, then a re-run requiring the survivor set
  to have actually shrunk by the claimed amount, then re-pin both constants two-sided.
- **Provenance:** `.superpowers/sdd/2026-08-01-closeout/progress.md:159-171,326-328`;
  `.superpowers/BLOCKERS.md:90-96`; reconciliation spec §1.
- **Related standing fact:** the last time anyone *enumerated* a survivor set was run 3. Every figure
  since is arithmetic over a score. That is why P1.5 is a **re-measurement**, not a new control.

<a id="i-4"></a>
### I-4 — The Layer 2 test command must be the **whole core subset**, never per-file

- **Kind:** DESIGN RATIONALE
- **Decision:** cosmic-ray runs against the full six-module core test subset as its test command.
- **Decided by / when:** agent, 2026-08-01, spiked both ways before the plan was written.
- **Why:** measured on `types.py`, a per-file command gave 12 survivors of 66 while the full core
  subset gave 5 of 66. `checker.py` and `y14_5.py` tests exercise `types.py` heavily, so a per-file
  command **inflates survivors and measures nothing**. Any per-file score is a methodology note, never
  a score for the layer.
- **Reopens if:** never.
- **Provenance:** `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:30-33`;
  reconciliation spec §1 (the 18.2% figure is recorded there as superseded for this reason).

<a id="i-5"></a>
### I-5 — `INCOMPETENT` mutants leave the denominator; `1,118` is total **jobs**, not viable mutants

- **Kind:** DESIGN RATIONALE
- **Decision:** cosmic-ray's `TestOutcome.INCOMPETENT` mutants (those that cannot execute at all, e.g.
  `RemoveDecorator` on a dataclass) are neither killed nor surviving and are excluded from the
  denominator.
- **Decided by / when:** agent, 2026-08-01 (spike); re-confirmed in the SI-4 fix round.
- **Why:** this caused a real, propagated arithmetic error — a score computed over total jobs instead
  of viable mutants. The mislabelled denominator then produced a "survivors unsurveyed" inference that
  was wrong: the survey **was** complete; the denominator was not.
- **Reopens if:** never. Any Layer 2 figure must state which denominator it uses.
- **Provenance:** `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:38-40,255-261,296-304`.

<a id="i-6"></a>
### I-6 — B4 ACCEPTED: the registry can be defeated by one joint commit, and no in-repo fix exists

- **Kind:** DEFERRED (accepted residual) · DESIGN RATIONALE
- **Decision:** `test_the_registry_still_covers_every_critical_guard` can be defeated by a single
  commit that deletes a registry entry **and** its name from `_CRITICAL_GUARDS` together. Accepted as
  a paper-trail mechanism, stated in the test's own docstring, and disclosed with its bound.
- **Decided by / when:** agent (ROUND-0 disposition), 2026-08-01; QA conceded the ACCEPT is correct.
- **Why:** no in-repo mechanism can stop a deliberate two-line commit by a solo author. The
  observation-assignment table's verdict is "**No — O-D**, and no mechanical control can do better."
  Stating it plainly beats leaving a future reviewer to rediscover it.
- **Reopens if:** the project gains multiple committers and code-owner review.
- **Provenance:** `.superpowers/BLOCKERS.md:43-45`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:79`;
  `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:142-146,186-188`;
  `docs/superpowers/specs/2026-08-01-observation-assignment.md:81`.

<a id="i-7"></a>
### I-7 — B5 DEFERRED **with a named trigger**: `expect="pass"` cannot detect a semantically inert mutation

- **Kind:** DEFERRED (with trigger)
- **Decision:** accept the limitation for now. **Trigger: on adding a SECOND `expect="pass"` entry,
  require a `witness_test` field.**
- **Decided by / when:** agent (ROUND-0 disposition), 2026-08-01.
- **Why:** `DeclaredMutation.__post_init__` only rejects `find == replace`; it cannot verify the
  mutation reaches a code path the target test exercises. For `expect="fail"` this is self-correcting
  — the runner measures a real outcome change. For `expect="pass"` a trivially inert anchor (a comment
  edit) satisfies the runner while proving nothing, and `expect="pass"` is precisely the direction
  created to close seed fishing. It is tolerable today because there is exactly **one** such entry
  (`mc-seed-base-shifted`) and its load-bearingness was verified by hand.
- **Reopens if:** a second `expect="pass"` entry is added. **That is the trigger.**
- **Provenance:** `.superpowers/BLOCKERS.md:45-46`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:80`;
  `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:82-97`.
- **⚠ Trigger is not where it was supposed to be.** ROUND-0 said *"Write the trigger into the
  docstring, not into memory."* It is not in `tests/mutation_registry.py`'s `DeclaredMutation`
  docstring (verified 2026-08-01) — it lives only in ROUND-0 and now here. Putting it in the docstring
  is a one-line, zero-risk follow-up.

<a id="i-8"></a>
### I-8 — B6 ACCEPTED: `mc-seed-base-shifted` is a narrow tripwire, not general seed-robustness

- **Kind:** DEFERRED (accepted residual) · REVERSAL (of the entry's original `why=` wording)
- **Decision:** the entry stays, with its `why=` text rewritten to state its real scope: a tripwire
  for a line-to-line fit re-entering `SUPPORTED_FITS`, **not** a general closure of the seed-fishing
  class.
- **Decided by / when:** agent, 2026-08-01 (SI-3 fix round F-3, and ROUND-0's B6 ACCEPT).
- **Why:** the mutation is genuinely load-bearing (margins move), but the guarded booleans are
  seed-invariant **by construction** for the current `SUPPORTED_FITS` — because
  `test_iso_fit_verdict_is_fixed_by_the_shaft_letter` documents `assembles == (es <= 0)`
  ([B-2](#b-2)). So it fires only on the exact [B-1](#b-1) reintroduction path. The original wording
  overstated it as making the control honest against seed choice in general — an overstated guard is
  worse than a narrow one, because it is trusted for work it does not do.
  The seed-fishing **class** is closed elsewhere: by the pre-registration committing every statistic
  to a pre-declared seed set.
- **Reopens if:** a currently seed-*sensitive* published quantity appears — then it needs its own
  companion entry.
- **Provenance:** `.superpowers/BLOCKERS.md:47-48`;
  `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:82-97,132-141,182-184`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:81`.

<a id="i-9"></a>
### I-9 — B7: REJECT the fix, disclose a **CI-bounded** k-sweep instead. Instance 4 is improved, not closed

- **Kind:** HUMAN-RATIFIED DISPOSITION · DEFERRED (accepted residual) · REVERSAL (of the disclosure form)
- **Decision:** do **not** retune `_RELIABILITY_MATES` to close the Gate A reliability headroom.
  Disclose the measured k-sweep with bootstrap CIs, in the form *"reliably detects ≥2.5×; reliably
  fails to detect ≤1.5×; indeterminate at 2×."* Any instance map must record instance 4 as **PARTIAL**,
  not CAUGHT.
- **Decided by / when:** agent (ROUND-0 REJECT), amended by QA (ROUND-1 A5), settled in ROUND-2.
- **Why, both halves:**
  - *Why reject the fix:* "fixing" means retuning the mate set **after seeing the k-sweep** — post-hoc
    instrument tuning, strictly worse than the residual. Correction 2026-08-01e independently forbids
    it ("the mate set stays fixed").
  - *Why the disclosure form changed:* the first disclosure was three bare point estimates.
    "k=2 is not caught (0.0018 margin)" is a point-estimate claim whose CI **contains the threshold**
    — precisely what correction 2026-07-31c forbids. Worse, 0.0018 was 0.02 of a mate when per-seed
    values quantise at 1/11: **presenting rounding as a margin**. R6 requires a measured bound, and a
    bound with a CI where the quantity is stochastic.
- **Reopens if:** `_RELIABILITY_MATES` or `_RELIABILITY_EPSILON` changes — re-measure. **This is
  currently outstanding:** the D-D repair restored the twelfth mate and *tightened* the instrument, so
  the disclosed bound is now **better than the disclosure claims**. The k-sweep must be re-measured
  before it enters the pre-registration.
- **Provenance:** `.superpowers/BLOCKERS.md:49-51`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:82`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:89-104`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:118-125`;
  `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:165-180,223-228`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:130-133`.

<a id="i-10"></a>
### I-10 — Mutual exclusion between the mutation layer and readers of `src/` is **enforced**, and the guard lives in `main()`

- **Kind:** DESIGN RATIONALE · **most dangerous to lose**
- **Decision:** `run_declared_mutation` holds `.mutation-in-progress` (gitignored, carrying pid and
  start time) around the mutate/run/restore/verify region. `scripts/gate_a.py` and
  `scripts/check_suite_integrity.py` refuse to start while it exists and **exit 2** — distinct from
  both scripts' 0/1. The guard sits in `main()` in both scripts, **not** at module scope.
- **Decided by / when:** agent, 2026-08-01 (close-out Task 9), required by R2 against its own author.
- **Why the control exists:** `gate_a.py` shells out to a fresh interpreter that reads the checker core
  **from disk** while a declared mutation has `src/tolcad/reliability.py` mutated. That is a published
  Gate A number measured against a mutated checker — a silent false green that **none** of O-A…O-D
  reveals: O-A passes, O-C's pins compare a real number to a constant, and O-B is *structurally blind*
  because the tree is clean **after** the run. Watched, not argued: with the lock held and no guard,
  `gate_a` printed a full clean report and exited 1.
- **Why in `main()` and not at module scope — do not "simplify" this:** `tests/test_gate_a.py` imports
  `scripts.gate_a` at collection, and two registry entries target tests in that file, so those
  subprocesses import `gate_a` **while the lock is held, by construction, every run**. A module-level
  `SystemExit(2)` makes them exit non-zero at import; `_target_test_passes` reads that as "failed under
  mutation"; both are `expect="fail"`, so both experiments would report SUCCESS **having never observed
  their mutation**. The guard would have blinded two critical guards inside the layer built to catch
  blind guards. **Importing is always safe; *measuring* is what must not overlap.**
- **Why exit 2 specifically:** `check_suite_integrity` already exits 1 on the detached mutation pin, so
  "refused" and "failed the pin" needed different codes. `tests/test_gate_a.py` had four `!= 0` asserts
  that would treat them identically; the new tests pin `== 2` exactly.
- **Reopens if:** never in the direction of removing it. CLAUDE.md's concurrency paragraph is now a
  description of an enforced mechanism, not advice.
- **Provenance:** `.superpowers/sdd/2026-08-01-closeout/progress.md:59-62,252-324`;
  `docs/superpowers/specs/2026-08-01-observation-assignment.md:89,93-107`;
  `CLAUDE.md:18-29`; `.gitignore` (`.mutation-in-progress` rationale).
- **Refusal wording is a decision too:** the plan's "Wait for the suite to finish." is precisely wrong
  for the case that strands a human — a run killed mid-mutation leaves the lock and every later run
  refuses forever with nothing to wait for. The shipped message is a **procedure**: `git status
  --short` over `src/` and `tests/fixtures/`, `git checkout --` to clear a leftover mutant, delete the
  lock, re-run.

<a id="i-11"></a>
### I-11 — Layer 3 thresholds are pinned at the **measured baseline**, never at a round number

- **Kind:** DESIGN RATIONALE
- **Decision:** Layer 1 and Layer 2 thresholds are pinned at what was measured. Two tests assert the
  pins are **not** round numbers. Lowering a pin requires a recorded reason in the gate script.
- **Decided by / when:** agent, 2026-08-01 (design spec + plan).
- **Why:** a floor pinned at 80 or 90 is a *choice*, not a measurement — and a silently lowered floor
  is itself an instance of the drift class. The plan deliberately ships `FLOOR = 0.0` first and
  replaces it from a measured run in a later step, because it refuses to guess a threshold.
- **Reopens if:** never.
- **Provenance:** `docs/superpowers/specs/2026-08-01-suite-integrity-design.md:61,69`;
  `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:60-64`.

<a id="i-12"></a>
### I-12 — B12 REJECT, **conditional on a standing ruling**: the mutation score is never a published number

- **Kind:** DEFERRED (conditional) · FROZEN (scope of "published")
- **Decision:** mutation score, coverage floor and survivor counts are **engineering telemetry**, not
  published numbers. They appear in README and CI only, never in the paper or the pre-registration.
- **Decided by / when:** agent (ROUND-0 disposition), 2026-08-01; the pre-registration contents list
  marks them EXPLICITLY NOT FROZEN.
- **Why:** roughly 84% of `iso286` mutation kills are mechanical table pinning rather than behavioural
  assertions, so the headline kill count overstates behavioural depth. With **no published number**,
  that imbalance cannot distort anything. Freezing the score would re-open the objection.
- **Reopens if:** **the author cites the mutation score anywhere in the paper.** Then this flips from
  REJECT to FIX and the behavioural-depth imbalance must be characterised.
- **Provenance:** `.superpowers/BLOCKERS.md:58-60`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:85,90,115`.

<a id="i-13"></a>
### I-13 — B8 REJECTED as not-a-defect; B9 and B10 ACCEPTED under R3/R4

- **Kind:** DEFERRED (accepted residuals)
- **Decision:**
  - **B8** (`_uninterned` duplicated across three test files): **not a defect.** Each copy asserts its
    own postcondition, so drift fails loudly at point of use. What remains is DRY aesthetics.
  - **B9** (`_count_and_apply` normalises CRLF→LF across the whole file): accepted. The real fix is
    15–25 lines (match on normalised, patch original bytes) and is **explicitly not scheduled**. A
    three-line suffix guard bounds blast radius to `.py/.md/.toml/.yml/.yaml/.cfg` and is honestly
    described as bounding, not fixing.
  - **B10** (restoration is exception-safe but not crash-safe under SIGKILL): accepted. No in-process
    mechanism survives SIGKILL; a killed run produces no green verdict to be false, and O-B catches the
    residue on the next run.
- **Decided by / when:** agent (ROUND-0/ROUND-2 dispositions), 2026-08-01.
- **Why:** R3 — a defect whose failure mode is a visible error, crash or false RED is never "fixed".
  Only silent false greens qualify. R4 — cover a residual by observing the artifact (O-B) rather than
  guarding the guard.
- **Reopens if:** a non-Python, line-ending-sensitive text target is added to the registry (B9), or a
  `_uninterned` copy loses its postcondition assertion (B8).
- **Provenance:** `.superpowers/BLOCKERS.md:54-57`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:78,83,84`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:48-51`;
  `docs/superpowers/specs/2026-08-01-observation-assignment.md:85-86`.

<a id="i-14"></a>
### I-14 — The historical-instance map uses a closed vocabulary; the string ban is deleted

- **Kind:** REVERSAL
- **Decision:** each instance-map row carries a verdict from a closed vocabulary — **CAUGHT** (name
  the artifact) / **PARTIAL** (artifact + measured bound) / **FIXED-NO-LAYER** (fixed and guarded by a
  specific test, but no layer covers it) / **ACCEPTED** (name the ruling) — with a non-empty evidence
  cell. The planned `assert "not caught" not in doc` string ban is **deleted**.
- **Decided by / when:** agent, 2026-08-01 (ROUND-0 C1, amended in ROUND-2 after QA's O5).
- **Why:** the string ban **forbade what B7 requires** — [I-9](#i-9) mandates disclosing that 2× is
  not caught, and the ban pressured the wording away from it. Two dispositions that forbid each other
  is a defect in the plan, not in the wording. Its sibling assertion (`assert f"| {n} |" in doc`) was
  also replaced: it passes against eleven rows of "TODO". And "eleven CAUGHTs" would itself have been
  a fresh instance of the failure mode.
  **FIXED-NO-LAYER exists because it is true:** instances 5 (module-level `pytestmark` skip) and 6
  (fetcher `exit 1` branch) live in `tests/` and `scripts/`, while Layer 1's coverage is scoped to six
  modules under `src/tolcad` ([I-1](#i-1)). No layer reaches them.
- **Reopens if:** never in the direction of a coverage claim without evidence.
- **Provenance:** `.superpowers/closeout/ROUND-0-architect-plan.md:33,86`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:169-176,193-195`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:127-133`;
  reconciliation spec §1, "instance count".

<a id="i-15"></a>
### I-15 — Refer to historical instances **by name**, never by ordinal

- **Kind:** REVERSAL · FROZEN (naming convention)
- **Decision:** the twelve enumerated shape-instances are referred to by name. **No new ordinal may be
  minted.** Counts and attested ordinals: reconciliation spec §1, "instance count".
- **Decided by / when:** agent, 2026-08-01 (close-out Task 8).
- **Why:** the design spec's §1 table enumerates one more instance than its own prose and §8
  distribution claim — the omitted row is the **Unencoded** one (a 39-cell IT table check run once in
  a shell), which is both the only shape no layer can catch and the same shape as the artifacts that
  discovered the discrepancy. Because the base count was wrong by one, every ordinal minted later is
  unreliable; only a minority are attested in code or spec text, and the remaining positions **cannot
  be reconstructed** from surviving ledgers. Inventing them would be the same defect in a new coat.
- **Reopens if:** never.
- **Provenance:** `docs/superpowers/specs/2026-08-01-observation-assignment.md:116-143`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:199-206`;
  `.superpowers/BLOCKERS.md:97-98`; reconciliation spec §1.
- **Consequence still open:** suite-integrity design spec §8's success criterion needs its C1
  amendment. Scheduled, not done.

<a id="i-16"></a>
### I-16 — Layer 3 runs the **full** experiment, and the restore is verified byte-identical

- **Kind:** DESIGN RATIONALE
- **Decision:** every declared mutation performs five steps: substring occurs **exactly once**; target
  test **passes at baseline**; apply; assert the declared outcome; restore and assert
  **byte-identical**. Restoration is in a `finally` block.
- **Decided by / when:** agent, 2026-08-01 (design spec §4).
- **Why:** *the anti-vacuity mechanism must not itself become vacuous.* Without step 1 an ambiguous or
  no-op patch makes the check meaningless; without step 2 a permanently broken test satisfies the
  registry; without step 5 a botched restore silently corrupts the tree. A restore failure is the most
  dangerous outcome and must never be swallowed — which is why the `OSError` path was upgraded to a
  loud `AssertionError` naming the file and the recovery command, raised from the `finally` block so
  it masks any in-flight error.
- **Reopens if:** never.
- **Provenance:** `docs/superpowers/specs/2026-08-01-suite-integrity-design.md:82-90,124-127`;
  `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:190-199`.

---

# 7. Process, evidence and record-keeping

<a id="p-1"></a>
### P-1 — The stopping criterion is a **closed set of four observations**; only a human may add a fifth

- **Kind:** FROZEN · REVERSAL (replaces the withdrawn depth cap)
- **Decision:** O-A (full suite on a clean checkout) · O-B (working-tree cleanliness after every run)
  · O-C (two-sided exact pins) · O-D (adversarial review at named checkpoints). **The closure of this
  list is the terminating device.** No agent may add a fifth.
- **Decided by / when:** architect + QA, converged 2026-08-01; ratified by the human adopting the
  close-out plan.
- **Why:** the earlier device was a **depth cap** (number ← guard ← meta-guard, depth 3 prohibited).
  It was withdrawn without defence: it did not parse under either reading, it prohibited three
  controls already committed on the branch being merged, it contradicted the plan's own P1.5 one line
  below, and three depth-3 defects in the project's history had **already fired**. The replacement is
  honest about what it is — *"every termination argument bottoms out in a stipulation; this one is
  explicit, enumerable, and requires naming which observation fails before a control may be added."*
- **Reopens if:** a human adds an observation, recorded in the design spec.
- **Provenance:** `.superpowers/closeout/ROUND-1-qa-critique.md:58-76`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:10-36`;
  `docs/superpowers/specs/2026-08-01-observation-assignment.md:19-36`;
  `docs/superpowers/plans/2026-08-01-closeout.md:31-42`.
- **O-C's scope is deliberately wider than "published numbers":** it also covers **instrument-
  composition** quantities — denominators, `tested`/`excluded`, seed-set sizes — *because of*
  [G-3](#g-3). No pin on the published mean would have caught that defect; the mean looked fine.

<a id="p-2"></a>
### P-2 — R2: **O-D discovers; it does not guard**

- **Kind:** DESIGN RATIONALE · REVERSAL (of an ambiguity in the plan's prose)
- **Decision:** a control needs its own control **only if** its failure mode is a silent false green
  **and** none of O-A…O-D reveals it. For R2's purposes, count O-D as revealing a defect only when a
  *scheduled, budgeted* checkpoint is specifically charged with looking for it. **A one-time discovery
  by O-D does not discharge R2 for recurrence.**
- **Decided by / when:** agent, 2026-08-01 (close-out Task 8, resolving a contradiction it found).
- **Why:** R2 as written and Task 9's rationale ("only O-D found it, therefore a control is required")
  contradicted each other. Without this reading a future reader could refuse **every** proposed
  control by pointing at O-D. O-A, O-B and O-C are standing observations that run unattended and fail
  loudly; O-D has a duty cycle measured in review-days and cannot be relied on to find the same defect
  again next Tuesday.
- **Reopens if:** never. This distinction is load-bearing for [I-10](#i-10)'s existence.
- **Provenance:** `docs/superpowers/specs/2026-08-01-observation-assignment.md:55-70`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:222-226`.

<a id="p-3"></a>
### P-3 — R5: layers ratchet, **review discovers**. Awareness is explicitly not a control

- **Kind:** REVERSAL · DESIGN RATIONALE
- **Decision:** a new detection layer is justified **only when a defect review already caught comes
  back**. A note in `CLAUDE.md` or a line in a prompt is **not** a control.
- **Decided by / when:** QA (ROUND-1 O3), adopted by the architect in ROUND-2.
- **Why:** ROUND-0's original R5 said "new layers require an executed mutation, not an argument", and
  cited the history as showing "the marginal control that pays is EXECUTE THE MUTATION". QA
  re-classified the same history **at the point of discovery** rather than at proof-of-fix: executed
  mutation 1/11; executed non-mutation measurement 2/11; **code review reading a diff or source
  5/11**; self-review 1/11; doc-vs-artifact cross-check 2/11. Five got an executed mutation *afterwards
  as proof of fix* — conflating that with discovery was the error. **Zero** of the instances were found
  by the Layer 1/2/3 machinery. The record supports "commission a hostile review" at least as strongly.
  And the awareness clause is empirical, not rhetorical: the pattern was in project memory and in
  nearly every review prompt of the session, and three new instances still landed.
- **Reopens if:** a layer ever *discovers* (not merely ratchets) an instance.
- **Provenance:** `.superpowers/closeout/ROUND-0-architect-plan.md:96`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:178-184`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:30-32`;
  `docs/superpowers/specs/2026-08-01-observation-assignment.md:47-52`.
- **Corollary, N-11, the highest-leverage open item:** adversarial review must be **scheduled and
  budgeted as a deliverable** with named checkpoints — before pre-registration, before each published
  number enters a draft, and before Gate D. It has no cost estimate. See [D-6](#d-6).

<a id="p-4"></a>
### P-4 — Ledger lines are never rewritten; reconciliation is append-only

- **Kind:** FROZEN
- **Decision:** the contemporaneous SDD ledger lines stay as written. Reconciliation appends a
  canonical value per contested quantity with provenance, and marks every other recorded figure
  SUPERSEDED with the reason.
- **Decided by / when:** agent, 2026-08-01 (close-out Task 8), following the same discipline already
  applied to `.superpowers/BLOCKERS.md`.
- **Why:** the ledgers' entire value is that they are contemporaneous — each was written against the
  tree as it stood that hour, which is why they disagree. Rewriting them would destroy the evidence
  that Gate D's traceability requirement actually rests on. Anyone grepping will still hit the old
  numbers; the reconciliation is the file that says which one is live.
- **Reopens if:** never.
- **Provenance:** reconciliation spec §0; `.superpowers/BLOCKERS.md:83-101`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:235-250`.

<a id="p-5"></a>
### P-5 — Standing rule: the pre-registration quotes the **spec**, never a ledger

- **Kind:** FROZEN · **most dangerous to lose**
- **Decision:** every published claim cites the tracked spec (or an executable pin), never an SDD
  ledger.
- **Decided by / when:** agent, 2026-08-01 (close-out Task 3, Finding 5), carried into the
  reconciliation spec as a standing rule and stamped on the footer of all six ledgers.
- **Why:** roughly a dozen historical ledgers still quote the superseded reliability figure, and they
  now **outnumber the correct one in a grep**. Deliberately not rewritten ([P-4](#p-4)) — so the only
  protection is the citation discipline. Same applies to the instance count, the survivor count, the
  coverage figures and the mutation score.
- **Reopens if:** never.
- **Provenance:** `.superpowers/sdd/2026-08-01-closeout/progress.md:137-140,248`;
  reconciliation spec §0; the append-only footer on all six `progress.md` files.

<a id="p-6"></a>
### P-6 — The SDD ledgers are now **tracked**, reversing a recommendation made hours earlier

- **Kind:** REVERSAL · DESIGN RATIONALE
- **State 1 (close-out Task 8, agent recommendation):** *leave the nested ignore.* Gate D requires
  every *claim* traceable from a clone to a logged run — an adjudicated value + provenance + an
  executable pin, all of which were already tracked. It does **not** require the raw hour-by-hour
  ledgers. Committing ~100 mutually contradictory ledgers would make the **wrong** figures a
  permanent part of the artifact of record and would make [P-5](#p-5) much harder to hold; they also
  carry agent-process detail that invites reviewers to litigate process rather than method. The
  stated risk ("one `rm -rf` from gone") is a **backup** problem, not a version-control problem.
  Explicitly flagged as the human's call and not acted on unilaterally.
- **State 2 (2026-08-01, current): tracked.** `.superpowers/sdd/.gitignore`'s blanket `*` was
  replaced with `*.diff`, and a `README.md` was added to the directory labelling the hazard. 101
  files, ~19,279 lines. Review `.diff` artifacts remain ignored — every commit they span is in
  history, so `git diff <a>..<b>` reconstructs any of them exactly.
- **What caused the change:** two things, one requirement and one argument.
  1. **A different requirement arrived:** the work has to resume from a clone on another machine
     with the learnings intact. Untracked ledgers do not clone. State 1 correctly answered the
     question it was asked ("what does Gate D's traceability need"); it was overturned by a question
     it was not asked.
  2. **The decisive argument is self-referential and was missed the first time.** §1 of the
     reconciliation spec — the document whose entire purpose is to make claims traceable — cites the
     ledgers **by `path:line`** as its provenance. Under the ignore rule every one of those citations
     **dangles in a clone.** That is the *Unencoded* shape one level up: the earlier reasoning was
     locally valid and globally wrong, and **nothing in the closed observation set would have caught
     it** ([P-1](#p-1)).
- **Reopens if:** it should not. But note the tension State 1 identified is *real and unresolved*:
  the wrong figures are now permanently in the artifact of record, so [P-5](#p-5) ("quote the spec,
  never a ledger") is now doing more work than before, not less. The append-only footer on every
  `progress.md` naming the canonical file is the mitigation.
- **Provenance:** `.superpowers/sdd/2026-08-01-closeout/task-8-report.md:190-233`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:215-221`;
  reconciliation spec §3 and its "Amendment 2026-08-01, superseding the table above";
  `.superpowers/sdd/.gitignore`; `.superpowers/sdd/README.md`.
- **Corrects a widely repeated claim, still worth knowing:** ROUND-0's F9 said `.superpowers/` is
  "UNTRACKED AND NOT IGNORED". That was **false** and was verified false — half was tracked, the
  other half ignored by a nested rule, and nothing was untracked-and-unignored. The reversal above
  was made for the right reason, not for F9's reason.

<a id="p-7"></a>
### P-7 — Plan snippets are drafts, not scripture; a test written in a plan and never run is not a test

- **Kind:** DESIGN RATIONALE (process rule with a measured base rate)
- **Decision:** every code snippet in a plan document is checked against real source before
  implementation, and every test must be **watched failing** before it is trusted.
- **Decided by / when:** emergent, recorded explicitly at close-out Task 3 and reinforced through
  Task 9.
- **Why — this has a measured base rate, which is why it is a rule and not a platitude.** In the
  close-out plan alone, **six consecutive tasks** found the plan's own snippet defective:
  | Task | What the plan snippet did |
  |---|---|
  | T3 | bound the sensitive band to its **floor** instead of its ceiling; would have passed the latent defective mate and falsely failed two healthy ones; referenced two attributes that do not exist and called a 4-arg function with none |
  | T6 | `_row` was a nested local, `_run_gate_a_stdout` did not exist, `_pytest_passes` took one arg not three, three line refs were stale |
  | T7 | the causal story about `autocrlf` was **backwards** ([E-3](#e-3)) |
  | T8 | asserted substrings appear *anywhere* in a document — satisfied by a table of "yes"/"no" with no reasoning |
  | T9 | asserted `returncode != 0` against a script that **exits 1 on a clean tree by design** |
  | T9 | placed a guard at module scope that would have neutered two critical guards ([I-10](#i-10)) |
  Independently, an implementer's own first draft compared **character offsets** of two strings in
  module source and passed against a runner rewritten to hold the lock around nothing — offsets cannot
  see block structure. Recorded rather than quietly fixed: the dominant failure mode reappeared inside
  the control added to close it, on the first attempt, in a task whose brief warned about exactly it.
- **Reopens if:** never.
- **Provenance:** `.superpowers/sdd/2026-08-01-closeout/progress.md:107-120,173-177,208-213,262-292`;
  `.superpowers/sdd/2026-08-01-closeout/task-3-report.md:1-60`.

<a id="p-8"></a>
### P-8 — Layer 2 must never run concurrently with anything else; and hand-verify mutants with `PYTHONDONTWRITEBYTECODE=1`

- **Kind:** DESIGN RATIONALE (operational)
- **Decision:** cosmic-ray mutates the working tree **in place** and reads both `src/` and `tests/`
  from disk. It runs alone. When hand-verifying a mutant, set `PYTHONDONTWRITEBYTECODE=1` and clear
  `__pycache__`.
- **Decided by / when:** agent, 2026-08-01, after a controller process failure and a false kill.
- **Why:** a reviewer was dispatched alongside a cosmic-ray run, saw shifting diffs, hit a spurious
  test failure and observed `src/tolcad/y14_5.py` holding a live mutation — it had the sense to
  isolate itself in a separate worktree. Separately, a size-preserving mutation (`-` → `%`) plus a
  same-second rewrite is served from a **stale `.pyc`** and reports a **FALSE KILL**; this bit once
  before it was caught. A stronger fix (running Layer 2 against an isolated copy or worktree) is a
  design change and was deliberately **not** taken.
- **Reopens if:** Layer 2 is moved to an isolated worktree — then the concurrency constraint relaxes
  for cosmic-ray, though [I-10](#i-10)'s lock is a separate mechanism for Layer 3.
- **Provenance:** `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:233-251,284-287,321-329`;
  `.superpowers/BLOCKERS.md:74`.

<a id="p-9"></a>
### P-9 — `"".join(["x"])` does not defeat string interning

- **Kind:** DESIGN RATIONALE (a fact, recorded because it silently invalidated four tests)
- **Decision:** runtime-built strings intended to defeat interning must use a **two-piece** join and
  **assert their own postcondition**.
- **Decided by / when:** agent (SI-4 fix round, found unprompted), 2026-08-01.
- **Why:** CPython's `str.join` returns the single item itself, so `"".join(["x"]) is "x"` is `True`.
  The "runtime-built" strings in `test_checker.py` and `test_montecarlo.py` **were** the interned
  literals, and four `is` mutants recorded as killed were never killed — four tests that could not
  fail, inside the layer built to catch tests that cannot fail.
- **Reopens if:** never. `_uninterned` is duplicated across three test files and each copy must keep
  its postcondition assertion ([I-13](#i-13)).
- **Provenance:** `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:273-278,321-329`.

<a id="p-10"></a>
### P-10 — Triage verdicts are verified by applying the mutant, not by reading it

- **Kind:** DESIGN RATIONALE
- **Decision:** every "equivalent" and every "killed" ruling in a mutation triage must be verified by
  applying the mutant in an isolated copy.
- **Decided by / when:** agent, 2026-08-01 (SI-4 fix round).
- **Why:** nine triage verdicts were wrong — four "equivalent" that were **live** and five "killed"
  that did not kill. Two of the live ones were safety-relevant: `condition is "fixed"` raises
  `TypeError` through `check()`, and `condition is "floating"` silently **deletes** the `hole_b`
  clearance guard that `y14_5.py:154-162` exists to enforce for every mate routed through `check()`.
- **Reopens if:** never.
- **Provenance:** `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:267-272,314-319`;
  reconciliation spec §1 (the corrected equivalent count).

<a id="p-11"></a>
### P-11 — Merging `feat/suite-integrity` first, with the tree-cleanliness control in the same commit

- **Kind:** HUMAN RULING (authorised) · DESIGN RATIONALE
- **Decision:** merge to `main` before any close-out work, and land `tests/conftest.py`'s
  tree-cleanliness finalizer (O-B) **in the same commit as the merge**.
- **Decided by / when:** architect recommendation ROUND-0, amended by QA A6, human-authorised
  2026-08-01.
- **Why merge first:** the diff touched **zero files under `src/`** — tests and tooling only, so it
  could not regress a headline number; `main` was a strict ancestor; both floors passed on
  re-measurement (stale in the safe direction). "Twelve open items" is an argument **for** merging: on
  `main` they are visible with a running gate; on a branch they rot.
  **Why the control ships in the same commit:** the merge premise was verified but the inference was
  wrong. At *runtime* plain `pytest` writes to five `src/` files and a tracked fixture, and a restore
  had already failed once in roughly a dozen Windows runs. The correct rationale is "zero production
  delta, **non-zero runtime footprint**, mitigated by a depth-0 cleanliness control landing in the
  same phase." The control must guard the hazard the merge introduces, not follow it.
- **Reopens if:** n/a (done).
- **Provenance:** `.superpowers/closeout/ROUND-0-architect-plan.md:39-43`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:106-119`;
  `docs/superpowers/plans/2026-08-01-closeout.md:61-72`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:65,87-93`.
- **Process note kept deliberately:** the merge's own precondition went stale (two docs commits landed
  after the architect verified the fast-forward). The implementer ran `--ff-only`, got "Not possible to
  fast-forward", and **stopped rather than forcing**. Fourth time a subagent caught a handed-down
  premise that had gone stale.

<a id="p-12"></a>
### P-12 — Subagent findings are not automatically right

- **Kind:** DESIGN RATIONALE (process rule)
- **Decision:** a reviewer's or fixer's finding is checked against real source before it is acted on,
  in both directions.
- **Decided by / when:** emergent, recorded 2026-08-01.
- **Why:** two recorded cases, in opposite directions. (a) A review finding claimed a widened
  clearance table would leave "every test in the repo still passing" — false; `test_sampler.py:87`
  pins the d4 failure rate and also fires. The finding's **conclusion** stood (that guard is about
  label balance, so it would miss the geometry path) but its "every test" clause did not, and the
  fixer corrected the reviewer with the re-review confirming. (b) The reviewer's *suggested* ladder
  ranges were measured and rejected ([B-6](#b-6)).
- **Reopens if:** never.
- **Provenance:** `.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:232-236,271-277`;
  `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:299-302`.

<a id="p-13"></a>
### P-13 — Two open findings were ruled on by the human rather than by an agent, and the rulings differed

- **Kind:** HUMAN RULING (×3, grouped because they set the precedent for how such findings are routed)
- **Decisions:**
  1. **FIX** — the module-level `pytestmark` in `tests/test_ap242_pmi.py` skipped
     `test_missing_file_raises` under a reason untrue of it.
  2. **ADD A TEST** — the NIST fetcher's mismatch → warn → `exit 1` branch had **zero** automated
     coverage; deviation from the plan's three-test surface was explicitly authorised.
  3. **PARK, DO NOT FIX** — `assert all(isinstance(v.assembles, bool) ...)` in `test_end_to_end.py`.
- **Decided by / when:** human, 2026-08-01, each asked and answered in session because each was
  plan-mandated (i.e. the plan itself specified the defective shape).
- **Why each, and why they differ — this is the calibration record:**
  1. An unconditionally-skipped test is a *pure* instance of the dominant failure mode; design spec
     line 252 makes "fresh clone, no licence, runs end-to-end" an explicit success criterion, and the
     fresh-clone-without-data path is the only place the mislabelled skip does damage; nothing frozen
     is touched. The fix had to be **evidenced by a simulated fresh clone** showing 1 passed / 1
     skipped, not merely "2 passed".
  2. The uncovered branch is the guard protecting oracle integrity if NIST changes the archive
     upstream, and it had been exercised only by one manual run where the count happened to match.
     Required shape was specified: a small fake ZIP in `tmp_path`, offline, **plus a positive control**
     (exactly 17 → return 0), because the negative alone would pass against a `main()` that always
     returned 1.
  3. **Not a real coverage gap.** Tier 1 verdict correctness is owned by the exact closed-form tests in
     `test_y14_5.py` and `test_checker.py`; the test's other assertions do real work; and
     strengthening it would hardcode sampler output into an integration test. The reviewer agreed with
     the park **but noted the reasoning does not extend to the sampler** — and the sampler's own guard
     test was indeed the next Critical found.
- **Reopens if:** (3) only if Tier 1 verdict correctness stops being owned elsewhere.
- **Provenance:** `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:80-89,96-114,126-138,141-148,220-222`.

---

# 8. Deliberately deferred, with triggers

Each of these was *decided to be deferred*, not forgotten. The trigger column is the point at which
deferring stops being defensible.

<a id="d-1"></a>
### D-1 — P1.5: Layer 2 re-measure and full survivor re-triage

- **Kind:** DEFERRED
- **Why deferred:** ~1.5 **serialised** days during which nothing may edit `src/` **or** `tests/`,
  because cosmic-ray reads both from disk. It is not parallelisable and was out of scope for the
  close-out plan's nine tasks.
- **Trigger:** it owns the resolution of [I-3](#i-3) (the detached mutation pin) and is the first item
  for the next round permitted a cosmic-ray run. Required shape: one run alone → triage → **re-run and
  require the survivor set to have actually shrunk by the claimed amount** → re-pin both constants
  two-sided.
- **Provenance:** `.superpowers/sdd/2026-08-01-closeout/progress.md:73-74,326-328`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:54`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:121-129`; reconciliation spec §1.

<a id="d-2"></a>
### D-2 — Baseline runnability audit — **must precede pre-registration**

- **Kind:** DEFERRED · **highest-consequence deferral in this file**
- **Why deferred:** ~1 day, and it is Phase 4 infrastructure work.
- **Trigger:** **before the freeze, unconditionally.** Gate C's frozen ">=6 of >=8 baseline models"
  is **unmeetable if fewer than 8 actually run**, and that is *unrecoverable after the freeze* —
  §7 thresholds cannot be revised post-data ([G-1](#g-1)). The related risk is that `metrics/`,
  `harness/` and `analysis/` do not exist at all, and ≥8 baselines must be integrated behind
  CADBench's unified protocol; the architect **declined to estimate** it and warned explicitly that it
  must not be estimated from the checker's velocity.
- **Provenance:** `.superpowers/sdd/2026-08-01-closeout/progress.md:75-77`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:27,66,117-119`;
  design spec `:172-184,318-324`.

<a id="d-3"></a>
### D-3 — P2.3: the fresh-clone receipt (Gate A's third SKIP)

- **Kind:** DEFERRED (design settled, implementation pending)
- **Why deferred:** needs CI to have run at least once.
- **Design already settled — do not redesign:** the receipt is valid iff its `commit_sha` is an
  **ancestor** of HEAD **and** `git diff --name-only <sha>..HEAD` touches nothing outside `docs/`,
  `papers/`, `.superpowers/`, `README*`, `LICENSE` — a **denylist**, because the allowlist form
  already missed `.gitattributes` and `cosmic-ray.toml`. The naive `commit_sha == HEAD` form has **no
  fixed point** (CI runs at X, committing the receipt produces Y, the row then fails forever).
- **Honest ceiling, must be disclosed in the row:** it is a **self-report**. Printing the workflow URL
  makes it checkable by a third party, not enforced. Disclose it beside [I-6](#i-6)'s ruling.
- **Trigger:** CI has run; then it is a `gate_a.py` amendment under [G-8](#g-8), logged pre-data, and
  it also amends suite-integrity design §8 ("Gate A remains untouched and still reports 6 PASS /
  3 SKIP").
- **Provenance:** `docs/superpowers/plans/2026-08-01-closeout.md:1085`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:78-80`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:48-56`;
  `.superpowers/closeout/ROUND-2-architect-revised.md:102-106,153-155`.

<a id="d-4"></a>
### D-4 — The k-sweep must be re-measured before it enters the pre-registration

- **Kind:** DEFERRED
- **Why deferred:** the D-D repair ([G-3](#g-3)) landed after the sweep was measured.
- **Trigger:** **before the pre-registration text is written.** Restoring the twelfth mate *tightened*
  the instrument, so the disclosed bound in [I-9](#i-9) is now better than the disclosure claims —
  publishing the old sweep would understate the instrument.
- **Provenance:** `.superpowers/sdd/2026-08-01-closeout/progress.md:130-133`.

<a id="d-5"></a>
### D-5 — Suite-integrity design spec §8's success criterion needs its C1 amendment

- **Kind:** DEFERRED (partially discharged 2026-08-01)
- **Why deferred:** scheduled but not done in the close-out plan.
- **Trigger:** it is one of the five pre-data amendments [G-6](#g-6) commits to filing. §8 claims a
  coverage distribution that omits the Unencoded instance ([I-15](#i-15)) and claims "all eleven
  instances are caught" when instances 5 and 6 are FIXED-NO-LAYER ([I-14](#i-14)).
- **Progress:** an amendment banner has since been added to the suite-integrity design spec naming
  four superseded statements — the instance count, the Gate A row count, the "280 passed" figure, and
  "no CI and no git remote" (which also discharges the "dormant until a remote exists" caveats). It
  also records that **§1's table is correct as written; it is the prose around it that miscounts.**
  Confirm the amendment section it points to is complete before treating this as closed.
- **Provenance:** `.superpowers/sdd/2026-08-01-closeout/progress.md:326-328`;
  `docs/superpowers/specs/2026-08-01-observation-assignment.md:136-138`;
  `.superpowers/closeout/ROUND-1-qa-critique.md:169-176`.

<a id="d-6"></a>
### D-6 — N-11: schedule and budget adversarial review as a deliverable

- **Kind:** DEFERRED · **described by its own author as the highest-leverage item in the plan**
- **Why deferred:** it is a process commitment, not code, and it has **no cost estimate** — the
  architect explicitly invited attack on that point.
- **Trigger:** named checkpoints — before pre-registration, before each published number enters a
  draft, before Gate D. R5 ([P-3](#p-3)) makes it a *control*, and O-D's duty cycle is what
  [P-2](#p-2) constrains.
- **Supporting evidence for why it pays:** the reliability drift was **seen in July and rationalised
  away**. A ledger recorded the exact symptom (`tested=11, excluded=1` vs `tested=12, excluded=0`
  previously) and reasoned it benign *without ever asking which mate left*. Not a testing gap — a
  reading habit. The data was on the page.
- **Provenance:** `.superpowers/closeout/ROUND-2-architect-revised.md:32,113-116,159`;
  `.superpowers/sdd/2026-08-01-closeout/progress.md:82-83,122-128`.

<a id="d-7"></a>
### D-7 — Parked residuals carried forward, by branch

- **Kind:** DEFERRED (bundle)
- These were each individually adjudicated as non-blocking and left standing. Listed so they are not
  rediscovered as new findings.
  - **ISO 273 branch:** R-2 the fastener inertness test guards only the MMC-construction half (direct
    fix: mutate `_FASTENER_LOWER_DEV_MM` and assert corpus verdicts byte-identical); R-3 the `k`
    IT4–IT7 restriction test covers only grades 12–14; R-5 frozen-corpus constants outside the hashed
    six (`SERIES_TOLERANCE_GRADE`, `FASTENER_SIZES`, `SUPPORTED_FITS`, `_ISO_FIT_NOMINALS_MM`,
    `_PLATE_THICKNESS_MM`) are covered only behaviourally; R-6 two near-vacuous sub-assertions,
    including a grep guard evadable by writing `-0.10`; **R-7 `-0.1` is published in the sidecar**.
  - **Pre-registration-prep branch:** R-b `test_spec.py:322` restates the guard rather than
    independently checking it; R-c the `_EDGE_MARGIN_MM` half of the derived-floor test is effectively
    unfailable (the `_MIN_WALL_MM` half carries the finding); R-d `test_end_to_end.py` still uses
    `importorskip` rather than the `needs_ocp` marker; R-e `.gitattributes` is untested by
    construction (closing it needs the clean-clone CI run); R-f `plate_thickness_mm` is one scalar for
    both plates.
  - **Procedural-generator branch:** P-b `test_sampler.py:71` imports `_mc_seed_for` from production;
    P-c `test_layout.py:13-15` asserts a property of `features.py`; P-d `layout.py` accepts
    `hole_b=None` but `build.py` would `TypeError`; **P-e `100_000` is duplicated as a default in
    `spec.py`, `sampler.py` and `checker.py`** — real drift risk between the sidecar default and the
    checker fallback, worth a follow-up; P-f/P-g test hygiene.
  - **Cross-cutting:** `check()` defaults `n=10_000` for `iso_fit` while Gate A stability needs
    `N=100_000` — no test is compromised, but a caller relying on the default silently gets a
    non-Gate-A-stable yield.
  - **Not delivered:** `LICENSE` and `README.md` appear in the close-out plan's file structure but no
    task shipped them, and neither exists at `30eb333`. Contribution 1 claims "the first such **open**
    tool" — **a repo with no licence is not open source.** This blocks the open-tool claim and is a
    Phase-0 item that fell through.
- **Provenance:** `.superpowers/sdd/2026-08-01-iso273-traceability/progress.md:296-325,348-350`;
  `.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:286-309`;
  `.superpowers/sdd/2026-08-01-procedural-generator/progress.md:311-325`;
  `.superpowers/sdd/2026-07-31-functional-checker/progress.md:37`;
  `docs/superpowers/plans/2026-08-01-closeout.md:51`;
  `.superpowers/closeout/ROUND-0-architect-plan.md:31,47`.

<a id="d-8"></a>
### D-8 — Three publication gates that were closed, recorded so they are not reopened

- **Kind:** DEFERRED → CLOSED
- The functional-checker branch ended with three items gating publication. All three are now closed;
  recorded here because the *reason each existed* is still binding.
  1. **Multi-seed reliability estimator** per amendment 2026-08-01e — closed. See [G-2](#g-2).
  2. **ASME Y14.5 fastener formulas verified against print by a domain expert** — closed by human
     attestation (ASME Y14.5-2018 Nonmandatory Appendix B, B-3 and B-4, symbols per B-2.1). It is an
     **attested** Gate A row, not a measured one ([G-7](#g-7)) — the harness reads a human record and
     cannot re-derive it.
  3. **ISO 286 edition + table number recorded in `iso286.py`** — closed by human attestation
     (ISO 286-1:2010 Table 1, Tables 4 and 5). Same attested-not-measured status.
- **Reopens if:** either attestation marker is removed from source, which flips the corresponding row
  back to SKIP by construction.
- **Provenance:** `.superpowers/sdd/2026-07-31-functional-checker/progress.md:19,26,127-136`;
  `.superpowers/sdd/2026-08-01-closeout/task-6-report.md:156-162`.

---

<a id="x-1"></a>
# 9. Recorded contradictorily and **not** adjudicated here

Flagged rather than resolved, because resolving them is a decision, not a compilation task.

### X-1 — The registry size — **found contradictory, since adjudicated**

- **The contradiction:** the reconciliation spec originally listed the declared-mutation registry
  size among quantities that are *not contested* and gave a single live value. Executed against the
  tree at `30eb333`, `len(REGISTRY)` returned a **larger** number, and the close-out ledger's own T9
  entry refers to a count matching the tree rather than the spec.
- **Diagnosis:** the figure was **already stale when written** — close-out Task 6 had added a registry
  entry ([G-7](#g-7)'s R1 ruling) before the reconciliation was authored. A stale number appeared
  inside the one document whose entire purpose is to hold the non-stale ones, within hours of it
  being written, and no guard caught it. **The registry size is not executably pinned; that is why.**
- **Status: adjudicated** by an amendment to the reconciliation spec §2 on 2026-08-01, which
  canonicalises the measured count with `tests/mutation_registry.py::REGISTRY` as provenance and
  records the error rather than silently overwriting it.
- **Residual for a human:** whether the registry size should be **executably pinned** under O-C(b) as
  an instrument-composition quantity. That question belongs to P1.5 ([D-1](#d-1)).

### X-2 — Whether the per-part `min()` model was ever "wrong"

- `.superpowers/sdd/2026-07-31-functional-checker/progress.md:108-110` states the reviewer's per-part
  model was "ALSO wrong (too conservative)". `src/tolcad/y14_5.py:105-133` implements exactly that
  model and argues at length that it is the standards-conformant one.
- **Diagnosis:** both are true of *different questions* — the ledger line was assessing physical
  pairwise assemblability, the docstring is assessing drawing conformance. The docstring is the live
  adjudication and [Y-1](#y-1) records the full chain. **Not a live contradiction**, but it reads as
  one to anyone who greps the ledger first, and the pre-registration must state the per-part form
  explicitly.
- **Action:** none required. Recorded so the ledger line is not treated as a live objection.

### X-3 — `.gitattributes` protection: "closed" vs "untested by construction"

- The pre-registration-prep ledger records the CRLF hole as **CLOSED** by
  `assert_is_the_nist_original`, and in the same ledger records residual **R-e**: `.gitattributes`
  "remains untested by construction — the hash notices corruption only after a clone."
- **Diagnosis:** likely reconciled by `tests/test_gitattributes_clone.py`, which post-dates R-e and
  performs real nested clones across all three `autocrlf` settings. I did not verify that it fully
  discharges R-e, and Gate A's "Fresh clone pipeline" row is still a SKIP ([D-3](#d-3)).
- **Action for a human:** decide whether R-e is discharged by the clone test or still needs the CI
  fresh-clone receipt. The two records disagree about whether a gap exists.
