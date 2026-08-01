# Tolerance-Aware Evaluation for Generative CAD — Design

**Date:** 2026-07-31
**Author:** Harsh Dwivedi (Northeastern University, MS AI)
**Status:** Approved for planning

---

## 1. Motivation

Every generative CAD paper evaluates with Chamfer distance, IoU, and B-rep validity rate.
All three measure *nominal geometric similarity*, and all three are **area-weighted**.

Functional criticality in mechanical design is approximately **inversely** area-weighted:

- A 0.05 mm error on a bore receiving a bearing scraps the part.
- A 2 mm error on a cosmetic boss is irrelevant.
- The bore contributes almost nothing to Chamfer distance. The boss dominates it.

The same holds for mating faces, hole patterns, chamfer leads, and datum surfaces —
small in area, decisive in function.

**Central hypothesis (H1):** standard CAD generation metrics are not merely noisy proxies
for functional correctness; they are *structurally biased against it*. A model can climb the
DeepCAD leaderboard while getting systematically worse at the features that determine
whether the part works.

H1 is falsifiable. Section 7 defines the thresholds that decide it.

---

## 2. Two-paper structure

| | Paper 1 (this spec) | Paper 2 (deferred) |
|---|---|---|
| Type | Evaluation / diagnosis | Method |
| Claim | Nominal metrics are functionally blind | Tolerance-aware generation closes the gap |
| Risk | Low — contributions exist regardless of H1 | High — depends on beating baselines |
| Depends on | Nothing | Paper 1's checker and benchmark |

Paper 2 is scoped in Section 9 but **not** built until Paper 1 clears Gate D.
This ordering is deliberate: Paper 1 constructs the measuring instrument Paper 2 needs,
and Paper 1 remains publishable even if Paper 2's method fails.

---

## 3. Contributions (Paper 1)

1. **Diagnosis.** Quantified decorrelation between nominal metrics and functional validity
   across open CAD generators.
2. **An open functional checker.** GD&T-aware, validated against SolidWorks TolAnalyst.
   No comparable open-source tool exists (see Section 4.2).
3. **A procedural assembly benchmark.** Parametric assemblies with ground-truth tolerance
   schemas, reproducible from a seed, difficulty-controllable.

---

## 4. Scope

### 4.1 Mate-type tiers

Complexity is driven by **mate type**, not part count. A two-part freeform mate is harder
than a five-part bolted stack. Scope is therefore defined by tier:

| Tier | Mates | Checker | Included |
|---|---|---|---|
| 1 | Floating fastener, fixed fastener, pin-in-hole position patterns | Closed-form ASME Y14.5 | **Yes — core** |
| 2 | Shaft/bore ISO 286 fits, planar datum stacks | Monte Carlo | **Yes** |
| 3 | Freeform surface mates, kinematic mechanisms, form defects | C-space / polytope | **No — stated limitation** |

Additional bound: **tolerance loop length ≤ 4 contributors.** The loop, not the part count,
is the complexity unit. Proper datum reference frame assignment keeps loops short by
construction. In practice: 2 parts typical, 3 maximum.

**Tier 1 rationale.** Closed-form Y14.5 conditions have *zero checker error* — they are
equations from a standard, not simulations:

- Floating fastener: `H = F + T`
- Fixed fastener: `H = F + 2T`
- Virtual condition: assembly guaranteed iff `VC_pin ≤ VC_hole`

where `H` = hole MMC, `F` = fastener MMC, `T` = position tolerance. When a model fails a
Tier 1 check, the failure is unambiguously the model's. No reviewer can attribute it to
checker error. This is the cleanest available ground for the headline claim.

### 4.2 Tooling split

Open tooling is the default path. SolidWorks is an optional oracle.

| Job | Tool | Rationale |
|---|---|---|
| Data generation | CadQuery / OCC → STEP AP242 | Reproducible from seed, no license |
| Tolerance checker | Own Python (ISO 286, virtual condition, Monte Carlo) | Must be open to be usable |
| Baselines | Published models, published datasets | Comparability |
| Validation oracle | SolidWorks TolAnalyst | Independent confirmation of checker |
| Real-world OOD set | SolidWorks (public/synthetic parts only) | Industrial complexity |

**Hard constraint.** Every headline number must be reproducible on a machine with no
SolidWorks license. Anything license-gated lives in an optional validation script behind a
clean interface. If TolAnalyst becomes load-bearing for a main result, that is a design
failure and must be refactored.

**No internal or proprietary company data. Ever.** Open datasets and procedural generation only.

Justification for building the checker: OCCT can *represent* semantic PMI via XDE
(`STEPCAFControl_Reader`/`Writer`) per AP242 recommended practices, but nothing open can
*analyze* it. `tol-stack` is a small 1-D Monte Carlo library, not meaningfully GD&T-aware.
FreeCAD's AP242 support is acknowledged incomplete. Real stack-up analysis is entirely
commercial (TolAnalyst, CETOL, 3DCS). The checker is therefore a genuine community
contribution, not merely internal tooling.

---

## 5. Architecture

Five components, each independently testable, communicating through explicit interfaces.

```
gen/          Procedural assembly generator
              seed -> (CadQuery program, STEP AP242, tolerance schema, functional spec)

checker/      Functional checker
              (geometry, tolerance schema, functional spec) -> verdict + yield estimate
              tier1.py  closed-form Y14.5      (exact)
              tier2.py  Monte Carlo stack-up   (statistical)

metrics/      Nominal metrics
              (predicted, reference) -> Chamfer, IoU, B-rep validity
              Reproduces published baseline numbers exactly.

harness/      Model runner
              Uniform interface over CAD-Recode, cadrille, CAD-Coder, prompted VLMs

analysis/     Statistics and figures
              Rank correlation, stratification, bootstrap CIs, plots

validation/   OPTIONAL. SolidWorks TolAnalyst cross-check. Never imported by the above.
```

Dependency rule: `validation/` may import from the others; nothing imports from
`validation/`. Enforced by an import-lint test.

---

## 6. Experiments

**E1 — Headline.** Baselines evaluated on nominal metrics and functional yield.
The story lands if functional yield is low *and badly ordered* relative to Chamfer/IoU.

**E2 — Mechanism.** Error stratified by feature size and functional role.
Prediction: normalized error on mating features substantially exceeds bulk-surface error,
and is invisible in aggregate Chamfer.

**E3 — Rank correlation.** Spearman ρ between each nominal metric and functional yield,
with bootstrap confidence intervals. The paper's most quotable number.

### Ablations

- Metric decorrelation across fit classes (clearance / transition / interference)
- Error vs. feature size — the mechanism plot
- Tier 1 (exact) vs. Tier 2 (statistical) criterion
- Fixed vs. floating fastener condition
- Loop length 1 → 4
- Test-time functional re-ranking vs. *k* (1 → 64)
- Verifier ablation: exact kernel vs. learned proxy vs. small-LM verifier
- Model scale 3B / 7B / 14B — does functional correctness emerge with scale?
- Curriculum over assembly complexity
- Procedural → real OOD transfer
- Monte Carlo sample count convergence

### Compute

Primary: RHEL box, 4× A6000 Ada (192 GB), `torchrun`.
Ablation farm: Windows/WSL box, 4 concurrent single-GPU configs.
The boxes are not networked; ablations are embarrassingly parallel, results synced manually.

---

## 7. Success criteria (pre-registered)

**These thresholds are fixed before any experiment runs and must not be revised afterward.**
Revising a threshold after seeing data invalidates the result. If a threshold turns out to be
badly chosen, that is recorded as a deviation in the paper, not silently changed.

### Gate A — Checker correctness (blocking)

Project does not proceed past Phase 2 unless all pass:

| Criterion | Threshold |
|---|---|
| Agreement with published Y14.5 worked examples (Tier 1) | **100%** — closed-form, must be exact |
| Verdict agreement with TolAnalyst, ≥500 Tier 2 assemblies | **≥ 95%**, all disagreements root-caused |
| Monte Carlo convergence: yield estimate stability at N=10k | **± 0.5%** across 5 seeds |
| Import-lint: no core module imports `validation/` | **Pass** |
| Fresh clone, no SW license, full pipeline | **Runs end-to-end** |

Failing Gate A means the checker is wrong, which means every downstream number is wrong.
No exceptions, no partial credit.

### Gate B — The finding (determines paper strength)

Primary statistic: Spearman ρ between Chamfer distance and functional yield,
across ≥3 baseline models × ≥1000 generated assemblies, with bootstrap 95% CI.

| Outcome | Threshold | Consequence |
|---|---|---|
| **Strong** | \|ρ\| < 0.3, CI excludes 0.5 | H1 supported. Full framing. Target TMLR / ICLR / CVPR. |
| **Moderate** | 0.3 ≤ \|ρ\| < 0.6 | H1 partially supported. Softer framing, still a paper. |
| **Null** | \|ρ\| ≥ 0.6 | H1 rejected. **Pivot** — see below. |

**Null contingency.** If nominal metrics *do* track functional validity, that is a real and
useful negative result, but a weak paper on its own. In that case the paper reframes as a
**benchmark and resource contribution**: the open checker and procedural generator retain
full value, and the finding becomes "nominal metrics are adequate for Tier 1–2 assembly
validity — tolerance-aware evaluation is unnecessary in this regime." Target shifts to a
workshop or dataset track. **This is the floor, and it is still publishable.** That is the
central reason for the evaluation-first ordering.

### Gate C — Mechanism (supporting)

| Criterion | Threshold |
|---|---|
| Normalized error ratio, mating features vs. bulk surfaces | **≥ 2.0×**, bootstrap CI excludes 1.0 |
| Effect holds across ≥3 baseline models | Direction consistent, all 3 |

Gate C is what turns Gate B from a correlation into an *explanation*. Passing B but failing C
means we have a phenomenon without a mechanism — reportable, but materially weaker.

### Gate D — Publication readiness (blocking for Paper 2)

| Criterion | Threshold |
|---|---|
| Gate A | Pass |
| Gate B | Strong or Moderate |
| Reproducibility: fresh clone → all headline numbers | **Exact** for deterministic metrics; **within ±1% relative** for sampled ones (fixed seed). One command. |
| Baseline numbers reproduce published values | **Within ±5% relative** of published Chamfer/IoU; any larger gap root-caused and documented before use |
| Related work | ≥ 50 papers reviewed, novelty explicitly defended against nearest 5 |
| Every claim in the draft | Traceable to a logged experiment run |
| Ablation table | Complete, no unexplained gaps |

### What "success" will mean at the end

On completion I will report, per gate, **pass/fail with the command and output that
establishes it** — not a narrative judgment. Specifically:

- Gate A: verified or not. Binary, no interpretation.
- Gate B: the measured ρ with CI, mapped to the pre-registered band.
- Gate C: the measured ratio with CI.
- Gate D: itemized checklist.

**What I can commit to:** that these gates are honestly evaluated, that no threshold is moved
after the fact, and that if the result is null I will say so plainly rather than reframing it
into a false positive.

**What I cannot commit to:** acceptance at any particular venue. Reviewer variance is high and
outside our control. The gates maximize the probability and, more importantly, make our
actual position legible at every stage.

---

## 8. Venue strategy

| Outcome | Target |
|---|---|
| Gate B strong + Gate C pass | TMLR (rolling, rewards rigor, no acceptance lottery) → then ICLR/CVPR |
| Gate B moderate | TMLR or CVPR/NeurIPS workshop |
| Gate B null | Workshop or dataset/benchmark track |

arXiv preprint on Gate D clearance regardless of venue outcome — establishes priority and is
visible to PhD admissions committees immediately.

**Non-technical dependency:** an academic co-author or letter-writer from Northeastern Khoury,
in addition to the industry co-author. For the stated PhD-admissions goal, an academic letter
is worth more than a marginal improvement in results. This should be pursued in parallel with
Phase 1, not after submission.

---

## 9. Paper 2 (scoped, not built)

**Claim:** a tolerance-aware objective or test-time verifier substantially improves functional
yield at near-zero cost to nominal metrics.

Pre-registered gates:

| Criterion | Threshold |
|---|---|
| Functional yield improvement over best baseline | **≥ 10 points absolute** |
| Nominal metric degradation (Chamfer) | **≤ 5% relative** |
| Improvement holds on OOD real data | Direction consistent, ≥ 5 points |

If yield improvement < 10 points, Paper 2 is **not submitted as a method paper**; the method
folds into Paper 1's revision as an additional baseline. Deciding this in advance prevents
months spent salvaging a weak method.

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| Checker is subtly wrong | TDD against published worked examples; TolAnalyst cross-check; Gate A blocking |
| H1 is false | Gate B null contingency — benchmark paper floor |
| Scope creep into Tier 3 | Tier 3 explicitly out; stated as limitation |
| Reproducibility broken by SW dependency | Import-lint test; fresh-clone check in Gate A and D |
| IP / employer conflict | Open tooling only, no internal data, manager as co-author, written clearance before Phase 0 |
| Baselines won't reproduce | Budget time in Phase 4; document deviations rather than hide them |
| Post-hoc threshold revision | Thresholds frozen in this document, in git, before Phase 4 |

---

## 11. Phases

| Phase | Work | Primary skills |
|---|---|---|
| 0 | Repo setup, CLAUDE.md, worktrees, **IP clearance in writing** | `init`, `using-git-worktrees` |
| 1 | Literature study (≥50 papers), related-work draft, novelty defense | `pdf` |
| 2 | Checker — TDD against Y14.5 worked examples, TolAnalyst validation, **Gate A** | `test-driven-development`, `requesting-code-review` |
| 3 | Procedural generator | `test-driven-development` |
| 4 | Baselines + E1/E2/E3, **Gate B, Gate C** | `dispatching-parallel-agents`, `systematic-debugging`, `verification-before-completion` |
| 5 | Ablations | `dispatching-parallel-agents` |
| 6 | Figures, writing, **Gate D** | `dataviz`, `verification-before-completion` |

Phase 1 precedes Phase 2 deliberately: novelty is defended **before** significant code is
written, so a scoop or prior-art discovery costs a week rather than a quarter.

**Note on planning granularity.** This spec covers a multi-month project and is too large for a
single implementation plan. Each phase gets its own plan, written just before that phase begins,
so later plans can incorporate what earlier phases discovered. Phase 0–2 are planned first.

---

## 12. Out of scope

- Tier 3 mates (freeform surfaces, kinematic mechanisms, form defects)
- Contact mechanics, FEA, thermal effects
- Tolerance *synthesis* (allocating tolerances) — analysis only
- Manufacturing cost modeling
- Any proprietary or employer-internal data
- Paper 2's method (scoped in Section 9, built only after Gate D)
