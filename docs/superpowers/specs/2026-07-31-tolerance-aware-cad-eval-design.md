# Tolerance-Aware Evaluation for Generative CAD — Design (v2)

**Date:** 2026-07-31 (v1), revised same day after literature review
**Author:** Harsh Dwivedi (Northeastern University, MS AI)
**Co-author/advisor:** SolidWorks AI Director
**Status:** Revised after 95-paper literature review; awaiting re-approval

---

## 0. What changed in v2, and why

A literature review of 95 papers forced three structural changes. All are pre-data.

**(1) The v1 headline claim was scooped.** ASSEMCAD (arXiv 2607.05123, 6 July 2026),
Appendix H.5 "Surface-Area Bias", states verbatim: *"global CD implicitly weights each part's
error by its surface area fraction... Large-surface-area components dominate the score
regardless of functional importance, while small but mechanically critical parts (fasteners,
bearings, shafts) contribute negligibly."* Verified directly from the PDF, not secondhand.
The v1 framing — "Chamfer is area-weighted, therefore functionally blind" — is no longer novel.

**(2) The statistical design was broken.** Spearman's ρ against a binary outcome has a hard
ceiling set by the base rate. At a 5% assembly-failure rate a *perfect* predictor scores
ρ ≈ 0.377; at 2%, ρ ≈ 0.242. Under v1's thresholds we would have declared a "strong finding"
for a metric with AUC = 1.0. See §7.

**(3) Reproducing published baseline numbers is not achievable.** Three papers report DeepCAD
validity as 46.1% / 50.82% / 58.10%, and BrepGen self-reports 62.9% while others re-measure it
at 47.74% and 68.23%. A ±5% reproduction gate was unmeetable by construction.

The response is not to abandon the project but to move its center of gravity. The metric
critique becomes supporting evidence; **the tolerance-grounded checker becomes the headline.**
That part of the space is genuinely empty (§2).

---

## 1. Motivation

Generative CAD models output **nominal geometry only**. A real mechanical part is nominal
geometry *plus tolerances*, and the question that decides whether it is usable is not "how
close is this shape?" but "will it assemble and function?"

Those differ in a way that matters: two parts each fully within tolerance can still fail to
assemble. This is not a corner case — it is the reason ASME Y14.5's fixed and floating
fastener formulas exist.

**Central hypothesis (H1):** a substantial fraction of generative-CAD output that scores well
on nominal geometric metrics is functionally unassemblable, and nominal metrics cannot predict
which. H1 is falsifiable; §7 fixes the thresholds.

---

## 2. Novelty position (defended against nearest prior work)

| Prior work | What it does | What it leaves open |
|---|---|---|
| **ASSEMCAD** 2607.05123 App. H.5 | Analytical: CD is area-weighted at the **part** level. Claims bias is *independent* of function. No measurement. | Feature level; the *inverse*-correlation thesis; empirical quantification; IoU |
| **MUSE** 2605.28579 | Benchmarks "assemblable" text-to-CAD via a **rubric-based VLM judge** | No tolerances, no GD&T, no Y14.5, no Monte Carlo. A rubric, not arithmetic |
| **CADTestBench** 2605.07807 | Deterministic executable tests | Geometry/topology only; no variation, no fits |
| **Beyond Statistical Similarity** 2302.02913 | Canonical "similarity ≠ engineering value" position paper | Not 3D-geometry specific; no tolerance model |
| **KAN tolerance-aware DFM** 2601.06334 | Tolerances as **inputs** to a manufacturability classifier | Single-part, tabular, no GD&T semantics, no assembly |
| **politopix / PolitoCAT** (1509.08763) | The one real GD&T-aware assemblability tool: polytope Minkowski sums | Academic, non-GitHub, unmaintained; no Y14.5 feature control frames, no fastener formulas, no ISO 286 |
| **JoinABLe / AutoMate / Linkify** | Learn *where* parts mate | No notion of whether they mate *given variation* |
| **OCCT XCAF `XCAFDoc_DimTolTool`** | *Reads* STEP AP242 semantic PMI | Reader only. Nothing computes on it |

**The gap, stated precisely:** across ~30 generative CAD systems and ~40 assembly-learning
papers surveyed, **none emits tolerances**; **no public CAD dataset carries tolerance ground
truth**; and **no maintained open tool evaluates assemblability under GD&T**. Parsing
infrastructure exists (OCCT XCAF); an analysis engine on top of it does not.

**Our claim is therefore not "CD is area-weighted."** It is: *assemblability under
manufacturing variation is measurable deterministically from published standards, nobody has
measured it for generative CAD, and doing so changes model rankings.*

Near-misses to distinguish explicitly in related work: HistCAD's 19 **sketch constraints**
(design intent, not manufacturing variation) and MatchMaker's **clearance erosion** (a
simulation heuristic, not a tolerance).

---

## 3. Contributions

1. **An open, standards-grounded functional checker.** ASME Y14.5 virtual condition and
   fixed/floating fastener conditions (exact) plus ISO 286 fits with Monte Carlo stack-up.
   Validated against the **NIST MBE PMI conformance suite** (public) and SolidWorks TolAnalyst
   (optional). The first such open tool.
2. **A procedural toleranced-assembly benchmark.** Ground-truth tolerance schemas,
   reproducible from a seed, difficulty-controllable. Justified because no such dataset exists.
3. **An empirical study.** How often do generative CAD models produce nominally-plausible,
   functionally-unassemblable output — and can nominal metrics predict it? Extends ASSEMCAD's
   part-level analytical claim to the **feature** level, tests the stronger **inverse**-
   correlation thesis they did not assert, covers **IoU** which they did not treat, and
   supplies the measurement their appendix lacks.

---

## 4. Scope

### 4.1 Mate-type tiers

Complexity is driven by **mate type**, not part count.

| Tier | Mates | Checker | Included |
|---|---|---|---|
| 1 | Floating fastener, fixed fastener, pin-in-hole position patterns | Closed-form ASME Y14.5 | **Yes — core** |
| 2 | Shaft/bore ISO 286 fits, planar datum stacks | Monte Carlo | **Yes** |
| 3 | Freeform surface mates, kinematic mechanisms, form defects | C-space / polytope | **No — stated limitation** |

Bound: **tolerance loop length ≤ 4 contributors.** The loop, not part count, is the complexity
unit. In practice 2 parts typical, 3 maximum.

Tier 1 rationale: closed-form conditions have **zero checker error** — `H = F + T` (floating),
`H = F + 2T` (fixed), and `VC_pin ≤ VC_hole`. A Tier 1 failure is unambiguously the model's.

### 4.2 Tolerance assignment — a methodological commitment

The tolerance schema belongs to the **reference design**, not to the prediction. Given a
reference assembly with its ground-truth tolerance schema, we apply *that* schema to the
*predicted* geometry and check assembly. We never invent tolerances per-model post hoc.
Otherwise we would be measuring our own tolerance assignment rather than the model.

### 4.3 Tooling split

| Job | Tool | Rationale |
|---|---|---|
| Data generation | CadQuery / OCC → STEP AP242 | Reproducible from seed, no license |
| Tolerance checker | Own Python | Must be open to be usable |
| Baselines | Published models under CADBench's unified protocol | Comparability (see §6) |
| Validation oracle A | **NIST MBE PMI conformance suite** | Public, authoritative, license-free |
| Validation oracle B | SolidWorks TolAnalyst | Independent industrial confirmation |

**No internal or proprietary company data, and no disclosure of SolidWorks implementation
details.** TolAnalyst is a black-box oracle: report agreement rates, never mechanism.
Publication is cleared; the co-author is the SolidWorks AI Director.

**Hard constraint.** Every headline number reproduces with no SolidWorks license. Adding the
NIST suite as oracle A means Gate A itself is now clearable license-free — a strict improvement
over v1, where the only oracle was license-gated.

---

## 5. Architecture

```
gen/          Procedural assembly generator
              seed -> (CadQuery program, STEP AP242, tolerance schema, functional spec)
checker/      tier1.py  closed-form Y14.5      (exact)
              tier2.py  Monte Carlo stack-up   (statistical)
metrics/      Chamfer, IoU, validity under CADBench's unified protocol
harness/      Uniform runner over baseline models
analysis/     AUC / Somers' D, cluster bootstrap, stratification, figures
validation/   OPTIONAL. NIST + TolAnalyst cross-checks. Never imported by the above.
```

Dependency rule: `validation/` may import core; nothing imports `validation/`. Enforced by
an import-lint test.

---

## 6. Experiments

**E1 — Prevalence.** What fraction of generative CAD output fails a Tier 1/2 functional check?
**E2 — Mechanism.** Error stratified by feature size and functional role, at the **feature**
level (bores, mating faces, hole patterns) — the level ASSEMCAD did not address.
**E3 — Predictability.** Can nominal metrics predict functional failure? Primary statistic
**AUC / Somers' D** (§7), reported within-model and pooled.
**E4 — Decision error.** *"選ecting the model with better Chamfer picks the functionally worse
model X% of the time."* Per the metric-critique literature, this framing persuades where a
correlation coefficient does not.
**E5 — Adversarial family.** A constructed set of assemblies scoring excellently on
Chamfer/IoU and failing functionally. One vivid counterexample outperforms a coefficient.

### Baselines — ≥8 models, not 3

Three models is too few: with model-level clustering the effective sample size collapses
(ICC 0.1 over 3 clusters of 333 gives n_eff ≈ 29). Going from 3 → 8+ models is the single
highest-value design change available.

Runnable, verified code+weights: **CAD-Recode** (2412.14042), **cadrille** (2505.22914),
**CAD-Coder/MIT** (2505.14646), **Text-to-CadQuery** (2505.06507), **DeepCAD** (2105.09492),
**Text2CAD** (2409.17106), **BrepGen** (2401.15563), **DTGBrepGen** (2503.13110),
**HoLa** (2504.14257, HF Space). Plus prompted frontier VLMs emitting CadQuery.

*Note: two distinct papers are titled "CAD-Coder" — 2505.14646 (MIT, code+weights) and
2505.19713 (Beihang). Do not conflate.*

### Ablations

- Metric decorrelation across fit classes (clearance / transition / interference)
- Error vs. feature size — the mechanism plot
- Tier 1 (exact) vs. Tier 2 (statistical) criterion
- Fixed vs. floating fastener
- Loop length 1 → 4
- Criticality weighting: uniform / mate-participation / datum-aware
- Monte Carlo sample-count convergence and distribution (normal vs uniform)
- Procedural → real OOD transfer (NIST, Fusion 360 Gallery)
- With vs. without filtering failed generations (range-restriction check)

### Compute

Primary: RHEL box, 4× A6000 Ada. Ablation farm: Windows/WSL box, 4 concurrent single-GPU
configs. Ablations are embarrassingly parallel; results synced manually.

---

## 7. Success criteria (pre-registered)

**Thresholds are fixed before any experiment runs and must not be revised afterward.**

*Correction log (pre-data).*
- *2026-07-31a:* Gate A convergence sample count raised N=10k → 100k. At N=10k the binomial
  SE for a transition fit (p≈0.6) is ≈0.0049, so the expected 5-seed range is ≈0.011 — the
  ±0.5% threshold was unachievable by correct code. Threshold unchanged, sample count corrected.
- *2026-07-31b:* Gate B primary statistic changed from Spearman ρ to **AUC / Somers' D**.
  Reason: ρ against a binary outcome is ceiling-bounded by the base rate — at a 5% failure
  rate a perfect predictor scores ρ≈0.377, inside v1's "strong finding" band. The v1
  thresholds were uninterpretable. AUC is base-rate invariant.
- *2026-07-31c:* Gate B decision rules changed from point estimates to **CI bounds**. Point
  estimates reward noise: an underpowered experiment yields a low statistic and therefore a
  "strong finding". Interval rules remove that perverse incentive.
- *2026-07-31d:* Gate D baseline-reproduction criterion replaced. Published numbers for the
  same baseline on the same dataset disagree by up to 15 points across papers, so ±5% was
  unmeetable. Replaced with CADBench unified-protocol reproduction.

All four predate any experimental data. **No post-data threshold change is permitted.**

### Gate A — Checker correctness (blocking)

| Criterion | Threshold |
|---|---|
| Agreement with published Y14.5 worked examples (Tier 1) | **100%** — closed-form, must be exact |
| Agreement with **NIST MBE PMI conformance suite** (FTC/CTC parts) | **100%** on decidable cases; all others root-caused |
| Verdict agreement with TolAnalyst, ≥500 Tier 2 assemblies | **≥ 95%**, disagreements root-caused |
| Monte Carlo convergence at N=100k | **± 0.5%** range across 5 seeds |
| Checker reliability (test–retest under input perturbation) | **≥ 0.95**, reported |
| Import-lint: no core module imports `validation/` | **Pass** |
| Fresh clone, no SW license, full pipeline | **Runs end-to-end** |

The NIST criterion is new in v2 and is the important one: it makes Gate A clearable without
any commercial license.

### Gate B — The finding

Primary statistic: **AUC** of nominal metric predicting functional validity. Reported
**within-model** (primary) and **pooled** (secondary), with 95% CIs from a **model-level
cluster bootstrap**. Base rate and tie counts reported alongside, always.

| Outcome | Threshold (CI-based) | Consequence |
|---|---|---|
| **Strong** | upper CI bound **< 0.65** | Nominal metrics are not usable proxies. Full framing. |
| **Moderate** | CI overlaps [0.65, 0.80] | Partial proxy. Softer framing, still a paper. |
| **Null** | lower CI bound **> 0.80** | Nominal metrics are adequate proxies. **Pivot** — see below. |
| **Inconclusive** | none of the above | Report as inconclusive. Do not spin. |

Spearman ρ and Kendall τ-b are reported as secondary for comparability with prior work, with
the base-rate ceiling stated explicitly.

**Null contingency.** If nominal metrics do track functional validity, that is a genuine
negative result. The checker, the NIST-validated implementation, and the procedural benchmark
retain full value, and the paper reframes as a **benchmark and resource contribution**.
**This is the floor, and it is still publishable.** It is the reason for evaluation-first ordering.

### Gate C — Mechanism (supporting)

| Criterion | Threshold |
|---|---|
| Normalized error ratio, mating features vs. bulk surfaces | **≥ 2.0×**, bootstrap CI excludes 1.0 |
| Effect holds across ≥ 6 of the ≥ 8 baseline models | Direction consistent |
| Within-model estimates reported, not only pooled | Required — guards against Simpson's paradox |

### Gate D — Publication readiness (blocking for Paper 2)

| Criterion | Threshold |
|---|---|
| Gate A | Pass |
| Gate B | Strong, Moderate, or a clean Null |
| Reproducibility: fresh clone → headline numbers | Exact for deterministic; ±1% for sampled (fixed seed) |
| Baselines reproduce **CADBench unified-protocol** numbers | Within ±5%; cross-paper disagreement reported as a finding, not an error |
| Related work | ≥ 80 papers reviewed; novelty defended against ASSEMCAD, MUSE, CADTestBench, politopix, KAN-DFM |
| Pre-registration | Public timestamp (OSF/AsPredicted) **before** data generation, + deviations table |
| Every claim in the draft | Traceable to a logged experiment run |

### What "success" will mean

Per gate: **pass/fail with the command and output establishing it** — not narrative judgment.

**Committed:** honest evaluation, unmoved thresholds, and a plain statement if the result is null.
**Not committed:** acceptance at any venue. Reviewer variance is outside our control.

---

## 8. Statistical protocol (binding)

Derived from the metric meta-evaluation literature. Deviating from this requires a logged
correction.

1. **Primary statistic AUC / Somers' D** (`D = 2·AUC − 1`), base-rate invariant.
2. **Cluster bootstrap resampling models and assemblies.** Naive i.i.d. bootstrap understates
   the CI by roughly 5× in this design.
3. **Within-model primary, pooled secondary.** Model heterogeneity alone can manufacture either
   a "strong finding" or a "null" from the same underlying relationship — Simpson's paradox.
4. **No dropping failed generations.** Assign worst-case metric values instead; report the
   analysis both ways. Filtering truncates the range and deflates association mechanically.
5. **One primary nominal metric** (Chamfer), IoU secondary; Holm-adjust. Compare correlations
   with a paired bootstrap of the *difference*, never by CI overlap.
6. **Report base rate, tie counts, and the scatter/box plot** for every reported association.
7. **Report checker reliability** and a disattenuated sensitivity analysis.
8. **Negate Chamfer** so all metrics point the same direction; state this explicitly.

---

## 9. Venue strategy

| Outcome | Target |
|---|---|
| Gate B strong + Gate C pass | TMLR → then ICLR/CVPR |
| Gate B moderate | TMLR or CVPR/NeurIPS workshop |
| Gate B null | Workshop or dataset/benchmark track |

arXiv preprint on Gate D clearance regardless.

**Co-author/advisor:** SolidWorks AI Director (MIT PhD, 27 patents). Still worth arranging an
additional Northeastern Khoury letter-writer; most committees want one from inside academia.

---

## 10. Paper 2 (scoped, not built)

**Claim:** a tolerance-aware objective or test-time verifier substantially improves functional
yield at near-zero cost to nominal metrics.

| Criterion | Threshold |
|---|---|
| Functional yield improvement over best baseline | **≥ 10 points absolute** |
| Nominal metric degradation (Chamfer) | **≤ 5% relative** |
| Holds on OOD real data | Direction consistent, ≥ 5 points |

Below 10 points, Paper 2 is not submitted as a method paper; the method folds into Paper 1's
revision as a baseline.

---

## 11. Risks

| Risk | Mitigation |
|---|---|
| Further scooping — ASSEMCAD App. H may spawn a standalone metrics paper | Re-run the prior-art sweep before submission; check ASSEMCAD's citing papers. Our contribution is the checker, which is harder to scoop |
| Checker is subtly wrong | TDD against Y14.5 worked examples; NIST + TolAnalyst cross-checks; Gate A blocking |
| H1 is false | Gate B null contingency — benchmark paper floor |
| Simpson's paradox drives the headline | Within-model primary; §8 binding |
| Scope creep into Tier 3 | Tier 3 out; stated as limitation |
| Reproducibility broken by SW dependency | Import-lint; NIST oracle removes the license dependency |
| Accidental disclosure of internal data | Open tooling only; TolAnalyst black-box; co-author reviews draft |
| Post-hoc threshold revision | Thresholds + correction log frozen in git before Phase 4 |

---

## 12. Phases

| Phase | Work | Primary skills |
|---|---|---|
| 0 | Repo setup, CLAUDE.md, worktrees | `init`, `using-git-worktrees` |
| 1 | Literature study (95 papers fetched), related-work draft, novelty defense | `pdf` |
| 2 | Checker — TDD vs Y14.5 + NIST, **Gate A** | `test-driven-development`, `requesting-code-review` |
| 3 | Procedural generator | `test-driven-development` |
| 3.5 | **Public pre-registration before any data generation** | — |
| 4 | Baselines + E1–E5, **Gate B, Gate C** | `dispatching-parallel-agents`, `systematic-debugging`, `verification-before-completion` |
| 5 | Ablations | `dispatching-parallel-agents` |
| 6 | Figures, writing, **Gate D** | `dataviz`, `verification-before-completion` |

Phase 3.5 is new in v2 and is ordered deliberately: a pre-registration timestamped after data
generation is worthless, and reviewers punish unverifiable pre-registration claims harder than
no claim at all.

---

## 13. Out of scope

- Tier 3 mates (freeform surfaces, kinematic mechanisms, form defects)
- Contact mechanics, FEA, thermal effects
- Tolerance *synthesis* (allocation) — analysis only
- Manufacturing cost modeling
- Any proprietary or employer-internal data
- Paper 2's method (§10)
