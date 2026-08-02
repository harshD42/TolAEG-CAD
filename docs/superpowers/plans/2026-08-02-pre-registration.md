# Phase 3.5 Public Pre-Registration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish an immutably timestamped public pre-registration of the *Nominally Correct, Functionally Wrong* study — hypotheses, metrics, the exact Gate A/B/C/D criteria, the analysis plan, the seeds, the corpus recipe and digest, the baselines and the limitations — before any research corpus is generated.

**Architecture:** Eleven tasks in three movements. **Movement 1 (Tasks 1–6)** makes the freeze *legal*: a precondition gate that refuses to proceed, one stale measurement re-taken, three numbered pre-data amendments to frozen documents, and one recorded ruling. **Movement 2 (Tasks 7–9)** writes the artifact: the pre-registration body, its limitations section, and a freeze manifest with an executable verifier. **Movement 3 (Tasks 10–11)** subjects it to an adversarial reader and then publishes it somewhere that cannot be quietly edited afterwards.

**Tech Stack:** Markdown (the deliverable), Python 3.13, numpy 2.4.1, pytest 9.0.2. OSF Registries + Zenodo for publication.

---

## Global Constraints

- **Quote the SPEC, never a ledger.** Standing rule from `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md` §0. Roughly a dozen ledgers under `.superpowers/sdd/` still carry the superseded reliability figure (`mean 0.9982, tested=11, excluded=1`) and they **outnumber the correct one in a grep**. Task 9 Step 3 enforces this mechanically; do not treat it as advice.
- **Canonical numbers come from `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md` §1**, cited below as **[LR §1]**. `docs/STATE-OF-PLAY.md` §3 is a convenient index onto it, not an independent source.
- **Gate A/B/C/D *thresholds* in design spec §7 are FROZEN** (`CLAUDE.md`). No threshold, seed set, exclusion band or table constant may change in this plan. A numbered *pre-data amendment* that corrects a falsehood or records an already-settled human decision is a different act and is permitted — precedent 2026-08-01f and 2026-08-01g.
- **No research corpus may be generated before Task 11 completes.** Design spec §12 orders Phase 3.5 before Phase 4. Measurement over the existing 200-seed calibration corpus is not corpus generation.
- **No value may change** in `_IT_MICRONS`, `_DEVIATION_MICRONS`, `_SIZE_BANDS`, `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`, `_TOL_FRACTION_RANGE`, `_MIN_WALL_MM`, `_EDGE_MARGIN_MM`, `_MC_SEED_BASE`, `_MC_SAMPLES`, `_PLATE_THICKNESS_MM`, `RELIABILITY_SEEDS`, `RELIABILITY_THRESHOLD`, `_RELIABILITY_EPSILON`, `BOUNDARY_BAND`. Several of these are inputs to the frozen corpus digest; moving one invalidates the freeze.
- **Do not touch `src/tolcad/` at all in this plan.** Task 2 explains why the reliability sweep monkeypatches in a harness rather than adding a parameter to `_perturb`: the declared-mutation entry `reliability-perturbation-tripled` matches the literal string `rng.uniform(-epsilon, epsilon)`, so editing that line breaks a critical guard.
- **`pytest` mutates and restores tracked files.** Never run it concurrently with `scripts/gate_a.py`, `scripts/check_suite_integrity.py`, or `scripts/measure_reliability_sweep.py` (Task 2 creates it and it imports the checker). This is enforced — `run_declared_mutation` holds `.mutation-in-progress` and both existing readers exit 2.
- **Tier 1 is exact**, `EPS = 1e-9`. **Tier 2 is statistical and always reports a seed.**
- **Every headline number reproduces with no SolidWorks licence** (design spec §4.3).

## Baseline facts, measured at `main` @ `30eb333` on 2026-08-02

Every row below was established by running the command, not by reading a document. Task 1 re-establishes them and **stops the plan** if any has moved.

| Fact | Value | Command |
|---|---|---|
| HEAD | `30eb333` | `git log --oneline -1` |
| Tests collected | **428** | `python -m pytest --collect-only -q` |
| Gate A | exit **1**; `7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP` | `python scripts/gate_a.py` |
| Ladder counts | d1 31/159, d2 99/301, d3 239/452, d4 421/609 | `tests/gen/test_ladder_pin.py::EXPECTED_COUNTS` |
| Corpus digest | `c035c2d99d377c1f1c6f912c9c690e47376e012eee37f4283c41de0051336fa3` | `tests/gen/test_ladder_pin.py::EXPECTED_DIGEST` |
| Reliability | mean **0.9975**, CI [0.9954, 0.9992], frac 0.9700, tested 12, excluded 0 | `python scripts/gate_a.py` |
| Registry | **15** entries, **15** critical guards | `grep -c "DeclaredMutation(" tests/mutation_registry.py` |
| `.superpowers/sdd` | **tracked**, 101 files | `git ls-files .superpowers/sdd \| wc -l` |
| git remote | `origin https://github.com/harshD42/TolAEG-CAD.git` | `git remote -v` |
| Tags | **none** | `git tag` |
| `README`, `LICENSE` | **absent** | `ls README* LICENSE*` |

Two documents state otherwise and are wrong: suite-integrity design §3 says *"There is no CI and no git remote"* and *"280 passed"*. Both are false at `30eb333`. Task 5 fixes them.

---

## File structure

| File | Change | Responsibility |
|---|---|---|
| `docs/preregistration/PRECONDITIONS.md` | Create | Task 1's refusal gate receipt — the commands, their outputs, and the go/no-go |
| `scripts/measure_reliability_sweep.py` | Create | Re-measure the B7 headroom k-sweep reproducibly |
| `tests/test_reliability_sweep_pin.py` | Create | Two-sided exact pins on the sweep (O-C) |
| `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md` | Modify | Amendments 2026-08-02h (D-A) and 2026-08-02i (D-B) in the §7 correction log |
| `scripts/gate_a.py` | Modify | Harness rows follow the amended §7 — a `SUPPLEMENTARY` kind; the NIST split |
| `tests/test_gate_a.py` | Modify | Pin the amended row structure and the tally |
| `docs/superpowers/specs/2026-08-01-suite-integrity-design.md` | Modify | Amendment C1: twelve not eleven; §3's environment facts; §8's superseded Gate A claim |
| `tests/test_observation_assignment.py` | Modify | Assert the §8 distribution sums to twelve and names Unencoded |
| `docs/preregistration/P1-5-RULING.md` | Create | The recorded ruling on whether P1.5 blocks the freeze |
| `docs/preregistration/PREREGISTRATION.md` | Create | **The deliverable.** Hypotheses, metrics, gates, analysis plan, seeds, corpus, baselines |
| `docs/preregistration/FREEZE-MANIFEST.md` | Create | What is frozen, where, and at which hash |
| `scripts/verify_freeze.py` | Create | Recompute the manifest and diff it against the tree |
| `tests/test_freeze_manifest.py` | Create | The verifier passes at the freeze commit, and can fail |
| `docs/preregistration/ADVERSARIAL-REVIEW-01.md` | Create | Task 10's charge sheet, findings and responses |
| `docs/preregistration/PUBLICATION-RECEIPT.md` | Create | DOIs, URLs, hashes, timestamps |

`docs/preregistration/` is a new directory holding public-facing artifacts, deliberately separate from `docs/superpowers/` (internal working documents).

## Cross-references to work owned elsewhere

All three landed while this plan was being written and are **verified present** in the working tree (they were not yet committed at `30eb333`; Task 1 re-checks):

- **`docs/superpowers/plans/2026-08-02-baseline-containerization.md`** — the baseline runnability audit. Its stated deliverable is `harness/RESULTS.md`, and its framing matches this plan's precondition P1 exactly ("Lose two models and a frozen criterion becomes unmeetable, and after the Phase 3.5 freeze there is no honest recovery"). Task 1 *consumes its result* and must not duplicate it.
- **`docs/superpowers/plans/2026-08-02-mutation-survivor-triage.md`** — P1.5, in seven serialised tasks. Task 6's ruling references it as the scheduled work, not as a blocker.
- **`docs/SPIKES.md`** — the spike register. Referenced **by title**, per instruction. Four of its entries bear on this plan:
  - *"Do at least eight of the nine named baselines actually run?"* (Band 1) — precondition P1; owned by the baseline plan.
  - *"What is the B7 k-sweep on the repaired twelve-mate instrument?"* (Band 3) — **Task 2 resolves this spike.** Its "cheapest decisive form" asks for k=1.5 and k=2.5 first; Task 2 measures all five, so the cheap form is subsumed.
  - *"Is the set of NIST 'decidable cases' non-empty?"* (Band 4) — Task 3's spike is the same question, narrowed to whether machine-comparable annotation counts exist.
  - *"Can Gate A ever exit 0 as §7 is currently frozen?"* (Band 4) — answered in the doing by Tasks 3 and 4. That spike's own fallback is *"a pre-data amendment to §7… It must be filed before the pre-registration timestamp"*, and it names the same three unfiled amendments this plan files: the NIST operationalisation (Task 3), the TolAnalyst optionality (Task 4), and the suite-integrity §8 C1 amendment (Task 5).

**Task 11's spike is NOT in the register.** *"Pre-registration immutability venue"* is new; add it to `docs/SPIKES.md` in Band 4 when Task 11 begins, so the register stays the single index of open unknowns.

**Working-tree caution.** At the time of writing, parallel sessions had `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`, `…/2026-08-01-ledger-reconciliation.md`, `…/2026-08-01-suite-integrity-design.md` and `CLAUDE.md` modified but uncommitted. Every citation in this plan is by **section and quoted text, never by line number**, for that reason. Task 1 Step 1 requires a clean tree before anything proceeds.

---

### Task 1: Refuse to proceed unless the freeze would be valid

**Files:**
- Create: `docs/preregistration/PRECONDITIONS.md`

**Interfaces:**
- Consumes: the baseline audit's result from `docs/superpowers/plans/2026-08-02-baseline-containerization.md`
- Produces: a go/no-go receipt every later task cites; the frozen `FREEZE_BASE_SHA`

Pre-registration publishes the gates *before* the data, so the result cannot be reverse-engineered from the outcome. That is only worth anything if the gates are *meetable* and *true* at the moment of freezing. Two of the preconditions below are **unrecoverable after the freeze**: Gate C's `≥6 of ≥8` cannot be lowered post hoc without invalidating Gate C, and a threshold amended after data exists is not an amendment, it is the thing pre-registration exists to prevent.

This task therefore has one output that matters: **GO or NO-GO.** A NO-GO stops the plan. It does not soften a criterion, and it does not proceed "provisionally".

- [ ] **Step 1: Establish the tree state and compare it against the frozen baseline**

Run each command and paste its output into `docs/preregistration/PRECONDITIONS.md`:

```bash
git log --oneline -1
git status --porcelain
ls .mutation-in-progress 2>/dev/null && echo "LOCK PRESENT - STOP" || echo "no mutation lock"
python -m pytest --collect-only -q 2>&1 | tail -1
python scripts/gate_a.py; echo "gate_a exit=$?"
grep -c "DeclaredMutation(" tests/mutation_registry.py
git ls-files .superpowers/sdd | wc -l
git remote -v
git tag
```

Compare against the **Baseline facts** table in this plan's header. Expected: `30eb333` (or a descendant whose diff touches only `docs/`), clean tree, no lock, `428 tests collected`, `gate_a exit=1` with the tally `7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP`, `15`, `101`, the `TolAEG-CAD` remote, no tags.

**If tests collected ≠ 428 or the Gate A tally differs, STOP.** Something moved that this plan's numbers were verified against. Report the delta to the human; do not reconcile it yourself.

- [ ] **Step 2: Read the baseline runnability audit's verdict — the unrecoverable one**

Gate C's frozen criterion is *"Effect holds across ≥ 6 of the ≥ 8 baseline models"* (design spec §7, Gate C). The spec names **nine** models in §6 under "Baselines — ≥8 models, not 3": CAD-Recode (2412.14042), cadrille (2505.22914), CAD-Coder/MIT (2505.14646 — **not** Beihang 2505.19713), Text-to-CadQuery (2505.06507), DeepCAD (2105.09492), Text2CAD (2409.17106), BrepGen (2401.15563), DTGBrepGen (2503.13110), HoLa (2504.14257). That is **one spare**.

```bash
ls docs/superpowers/plans/2026-08-02-baseline-containerization.md
```

- **If the file does not exist, or exists but records no completed audit: NO-GO.** Write NO-GO into `PRECONDITIONS.md` with the reason and stop. This plan cannot proceed on an assumption about how many baselines run.
- **If the audit reports ≥ 8 runnable:** record the count, the per-model evidence pointer, and GO on this precondition.
- **If the audit reports < 8 runnable:** **NO-GO, and escalate to the human as a design question, not a bug.** The options are (a) find more baselines before freezing, (b) freeze a *different* Gate C criterion now, pre-data, as a numbered amendment with the audit as its justification. Option (b) is legitimate *only before* the freeze and only with the audit attached. It is not available afterwards. Do not choose between them; present them.

- [ ] **Step 3: Enumerate the remaining preconditions and their owners**

Record this table in `PRECONDITIONS.md`, filling the Status column:

| # | Precondition | Why it must precede the freeze | Owner | Status |
|---|---|---|---|---|
| P1 | ≥8 of 9 baselines verified runnable | Gate C's `≥6 of ≥8` is unmeetable below 8, and unrecoverable after the freeze | Baseline-containerization plan | *(Step 2)* |
| P2 | B7 reliability k-sweep re-measured | The disclosed 2–3× bound was measured against the defective `tested=11` mate set. Restoring the twelfth mate *tightened* the instrument. A pre-registration must not publish a stale bound. **[LR §1]**, reliability section, final note | **This plan, Task 2** | |
| P3 | D-A written into §7 (NIST splits; limitation stated) | §7 still implies NIST can supply an assemblability verdict. All 17 AP242 files have zero `NEXT_ASSEMBLY_USAGE_OCCURRENCE` | **This plan, Task 3** | |
| P4 | D-B written into §7 (TolAnalyst supplementary) | §7 lists TolAnalyst as a blocking Gate A criterion while §4.3 requires licence-free reproduction. The frozen document contradicts itself | **This plan, Task 4** | |
| P5 | Suite-integrity design §8 C1 amendment | §8 claims eleven instances where §1 enumerates twelve, and asserts a Gate A row count superseded by 2026-08-01g. §3's environment facts are false | **This plan, Task 5** | |
| P6 | P1.5 blocking status ruled and recorded | Ambiguity here is itself a defect: an unruled blocker silently becomes a reason to unfreeze later | **This plan, Task 6** | |
| P7 | Research-corpus seed range chosen by the human, **disjoint from 0–199** | The difficulty ladder was *calibrated* on seeds 0–199 (the repair moved d4 from 478/609 to 421/609 on exactly those seeds). Reusing them for the research corpus is calibrating on the evaluation set | **Human**, recorded in Task 7 | |
| P8 | No research corpus generated | Design spec §12 | Standing | |

P7 is a **new precondition this plan adds.** It is not in `docs/STATE-OF-PLAY.md` §6 and it is load-bearing: the ladder's four frozen counts are a property of seeds 0–199, and a research corpus drawn from those same seeds would inherit a tuned difficulty distribution. Measured detail for Task 7's use: `sampler._mc_seed_for(seed, mate_index) = 10_000 + seed*4 + mate_index`, and across the calibration corpus the real `iso_fit` Monte Carlo seeds span **10006–10791**, so any research corpus with assembly seed ≥ 200 is disjoint in Monte Carlo seed space too.

- [ ] **Step 4: Write the verdict**

`PRECONDITIONS.md` ends with exactly one line of the form:

```
VERDICT: GO  (all preconditions discharged or owned in-plan; P1 discharged externally at <ref>)
```

or

```
VERDICT: NO-GO  (P<n> unmet: <one sentence>)
```

**A NO-GO ends this plan.** Do not start Task 2.

- [ ] **Step 5: Commit**

```bash
git add docs/preregistration/PRECONDITIONS.md
git commit -m "docs: pre-registration precondition gate, with verdict"
```

---

### Task 2: Re-measure the B7 reliability headroom sweep, and pin it

**Files:**
- Create: `scripts/measure_reliability_sweep.py`
- Create: `tests/test_reliability_sweep_pin.py`

**Interfaces:**
- Consumes: `scripts.gate_a._RELIABILITY_MATES`, `_RELIABILITY_EPSILON`, `RELIABILITY_SEEDS`, `RELIABILITY_THRESHOLD`, `_aggregate_reliability`; `tolcad.reliability._perturb`
- Produces: `SWEEP_K: tuple[float, ...]`; `measure_sweep() -> dict[float, dict]`; `classify(row: dict, threshold: float = RELIABILITY_THRESHOLD) -> str` returning one of `"DETECTED"`, `"NOT DETECTED"`, `"INDETERMINATE"`

The disclosed bound — *"reliably detects ≥2.5×; reliably fails to detect ≤1.5×; indeterminate at 2×"* — was measured against the **defective** mate set, where `mate[8]` sat at exactly 0.0 and was silently excluded (`tested=11`). The D-D repair restored the twelfth mate and **tightened** the instrument: k=2 now fails at 0.9392 where it previously passed at 0.9518 (**[LR §1]**, reliability section, closing note). Better than claimed, but stale — and nothing executable reproduced even the old sweep.

**There is a trap in this measurement and it has the shape of the project's dominant failure mode.** The obvious implementation scales `epsilon` at the call site. `verdict_stability` excludes any mate with `|margin| < BOUNDARY_BAND * epsilon`, and the sensitive-band mates sit at `|margin| = 3.5e-4`. At k≥2 the band becomes `2 × 2e-4 = 4e-4` and swallows all six of them: `tested` collapses 12 → 6, the survivors are all slack, every verdict trivially survives, and the sweep reports **mean = 1.0000 at every k ≥ 2**. That is a metric mathematically incapable of returning below 1.0 — historical instance 2's *Structurally impossible* shape, rebuilt inside the measurement written to bound it. This was measured, not hypothesised:

```
naive epsilon scaling:  k=2.0 mean=1.0000 tested=6 excluded=6
                        k=3.0 mean=1.0000 tested=6 excluded=6
```

The correct experiment is the one `tests/mutation_registry.py`'s `reliability-perturbation-tripled` entry already performs: **scale the perturbation, leave the exclusion band at the unscaled epsilon.**

- [ ] **Step 1: Write the failing test**

Create `tests/test_reliability_sweep_pin.py`:

```python
"""The reliability headroom sweep, pinned two-sided as exact counts.

O-C. The published bound is a claim about the INSTRUMENT, so its
instrument-composition quantities are pinned too -- `tested` above all.
Every stability value is a multiple of 1/12 and the mean is taken over 200
seeds, so mean * 2400 is an exact integer. Pinning that integer rather than a
rounded rate is deliberate: a rate hides a change in its denominator, which is
exactly how `tested` fell 12 -> 11 unnoticed for four ledgers.
"""

import pytest

from scripts.gate_a import RELIABILITY_SEEDS, RELIABILITY_THRESHOLD
from scripts.measure_reliability_sweep import SWEEP_K, classify, measure_sweep

DENOMINATOR = 2400  # len(RELIABILITY_SEEDS) * tested == 200 * 12

# Measured 2026-08-02 at 30eb333 on numpy 2.4.1, 200 pre-registered seeds
# (0-199), bootstrap seed 0, 10,000 resamples.
EXPECTED_STABLE = {1.0: 2394, 1.5: 2340, 2.0: 2254, 2.5: 2194, 3.0: 2148}
EXPECTED_CI = {
    1.0: (0.9954, 0.9992),
    1.5: (0.9692, 0.9804),
    2.0: (0.9300, 0.9483),
    2.5: (0.9038, 0.9242),
    3.0: (0.8842, 0.9058),
}
EXPECTED_VERDICT = {
    1.0: "NOT DETECTED",
    1.5: "NOT DETECTED",
    2.0: "DETECTED",
    2.5: "DETECTED",
    3.0: "DETECTED",
}


@pytest.fixture(scope="module")
def sweep():
    return measure_sweep()


def test_the_sweep_covers_the_declared_multipliers(sweep):
    assert tuple(sweep) == SWEEP_K == (1.0, 1.5, 2.0, 2.5, 3.0)
    assert len(RELIABILITY_SEEDS) == 200


@pytest.mark.parametrize("k", [1.0, 1.5, 2.0, 2.5, 3.0])
def test_every_sweep_row_tests_all_twelve_mates(sweep, k):
    """THE guard for this task. Scaling `epsilon` instead of the perturbation
    pushes the six sensitive-band mates into the exclusion band, leaving six
    slack mates whose verdicts cannot flip -- so the sweep reports 1.0000 at
    every k and the bound it publishes is unfalsifiable. Historical instance 2's
    shape, inside the measurement written to bound instance 4.
    """
    assert sweep[k]["tested"] == 12, (
        f"k={k} tested {sweep[k]['tested']} of 12 mates. The exclusion band has "
        f"swallowed sensitive-band mates; this row cannot report instability."
    )
    assert sweep[k]["excluded"] == 0


@pytest.mark.parametrize("k", [1.0, 1.5, 2.0, 2.5, 3.0])
def test_each_sweep_row_matches_its_exact_pinned_stability_count(sweep, k):
    measured = sweep[k]["mean"] * DENOMINATOR
    assert measured == pytest.approx(EXPECTED_STABLE[k], abs=1e-6), (
        f"k={k} measured {measured:.4f}/{DENOMINATOR} stable verdicts, pinned "
        f"{EXPECTED_STABLE[k]}/{DENOMINATOR}. This bound is published in the "
        f"pre-registration; re-measure the WHOLE sweep and re-pin, and record "
        f"the change in the deviations table."
    )


@pytest.mark.parametrize("k", [1.0, 1.5, 2.0, 2.5, 3.0])
def test_each_sweep_row_matches_its_pinned_bootstrap_ci(sweep, k):
    lo, hi = EXPECTED_CI[k]
    assert sweep[k]["ci_low"] == pytest.approx(lo, abs=5e-5)
    assert sweep[k]["ci_high"] == pytest.approx(hi, abs=5e-5)


@pytest.mark.parametrize("k", [1.0, 1.5, 2.0, 2.5, 3.0])
def test_the_published_bound_is_ci_based_not_point_based(sweep, k):
    """A mean below 0.95 whose CI straddles 0.95 is INDETERMINATE, not caught.
    The old disclosure got this right and the new one must not regress it.
    """
    assert classify(sweep[k]) == EXPECTED_VERDICT[k]


def test_the_sweep_brackets_the_threshold_in_both_directions(sweep):
    """A sweep entirely on one side of 0.95 would bound nothing."""
    verdicts = {classify(sweep[k]) for k in SWEEP_K}
    assert "DETECTED" in verdicts and "NOT DETECTED" in verdicts, (
        f"the sweep does not bracket the {RELIABILITY_THRESHOLD} threshold: {verdicts}"
    )


def test_gate_a_operating_point_is_the_k_equals_one_row(sweep):
    """k=1 must reproduce the published Gate A reliability figure exactly.
    If it does not, the sweep is measuring something other than Gate A."""
    assert sweep[1.0]["mean"] == pytest.approx(0.9975, abs=5e-5)
    assert sweep[1.0]["fraction_passing"] == pytest.approx(0.9700, abs=5e-5)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_reliability_sweep_pin.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.measure_reliability_sweep'`.

- [ ] **Step 3: Write the script**

Create `scripts/measure_reliability_sweep.py`. **This exact text was executed at `30eb333` and produced the table in Step 4** — do not paraphrase it:

```python
#!/usr/bin/env python
"""Re-measure the Gate A reliability headroom sweep (the "B7 k-sweep").

WHY THIS EXISTS. The disclosed headroom bound for Gate A's reliability
criterion -- "reliably detects >=2.5x, reliably fails to detect <=1.5x,
indeterminate at 2x" -- was measured against the DEFECTIVE mate set, the one
where mate[8] sat at exactly 0.0 and was silently excluded (tested=11). The
repair under construction rule D-D restored the twelfth mate and TIGHTENED the
instrument, so the old bound is stale. A pre-registration must not publish a
stale bound, and no script reproduced even the old one.

Usage: python scripts/measure_reliability_sweep.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import tolcad.reliability as _rel  # noqa: E402
from scripts.gate_a import (  # noqa: E402
    _RELIABILITY_EPSILON,
    _RELIABILITY_MATES,
    RELIABILITY_SEEDS,
    RELIABILITY_THRESHOLD,
    _aggregate_reliability,
)

# The perturbation multipliers swept. k=1.0 is Gate A's actual operating point.
SWEEP_K = (1.0, 1.5, 2.0, 2.5, 3.0)

_ORIGINAL_PERTURB = _rel._perturb


def _sweep_one(k: float):
    """Aggregate reliability with the PERTURBATION scaled by k.

    The exclusion band stays at BOUNDARY_BAND * epsilon with the UNSCALED
    epsilon. That asymmetry is the whole point and it is not an oversight:

      * Scaling the perturbation is what the declared-mutation registry entry
        `reliability-perturbation-tripled` does -- it rewrites
        `rng.uniform(-epsilon, epsilon)` to `rng.uniform(-3.0*epsilon,
        3.0*epsilon)` inside `_perturb`, leaving `verdict_stability`'s
        exclusion test reading the original epsilon. This function reproduces
        that experiment continuously instead of at one hard-coded multiplier.

      * Scaling `epsilon` at the CALL SITE instead is WRONG and silently so.
        `verdict_stability` excludes any mate with |margin| < BOUNDARY_BAND *
        epsilon. The six sensitive-band mates sit at |margin| = 3.5e-4, so at
        k >= 2 the band (2 * 2e-4 = 4e-4) swallows them: `tested` collapses
        12 -> 6, the six survivors are all slack, every verdict trivially
        survives, and the sweep reports mean = 1.0000 at EVERY k >= 2. That is
        a metric mathematically incapable of returning below 1.0 -- the exact
        shape of historical instance 2 ("Structurally impossible"), rebuilt
        inside the measurement written to bound instance 4. The assertion in
        measure_sweep and the pin in tests/test_reliability_sweep_pin.py exist
        to make that mistake loud rather than plausible.

    Monkeypatching rather than adding a `scale` parameter to `_perturb` is
    deliberate: `reliability-perturbation-tripled` matches the literal string
    `rng.uniform(-epsilon, epsilon)` in src/tolcad/reliability.py, so editing
    that line to take a scale factor would break a critical guard. The
    measurement harness bends; the checker core does not.
    """
    _rel._perturb = lambda mate, epsilon, rng: _ORIGINAL_PERTURB(mate, k * epsilon, rng)
    try:
        return _aggregate_reliability(
            _RELIABILITY_MATES,
            epsilon=_RELIABILITY_EPSILON,
            seeds=RELIABILITY_SEEDS,
            threshold=RELIABILITY_THRESHOLD,
        )
    finally:
        _rel._perturb = _ORIGINAL_PERTURB


def measure_sweep() -> dict[float, dict]:
    """Return {k: {mean, ci_low, ci_high, fraction_passing, tested, excluded}}."""
    out: dict[float, dict] = {}
    for k in SWEEP_K:
        a = _sweep_one(k)
        assert a.tested == 12, (
            f"k={k} measured tested={a.tested}, expected 12. The exclusion band "
            f"has swallowed sensitive-band mates, so this row cannot report "
            f"instability at all. Do NOT record it -- see _sweep_one's docstring."
        )
        out[k] = {
            "mean": a.mean,
            "ci_low": a.ci_low,
            "ci_high": a.ci_high,
            "fraction_passing": a.fraction_passing,
            "tested": a.tested,
            "excluded": a.excluded,
        }
    return out


def classify(row: dict, threshold: float = RELIABILITY_THRESHOLD) -> str:
    """CI-based verdict. Point estimates are not enough: a mean below the
    threshold whose CI straddles it is INDETERMINATE, not 'detected'."""
    if row["ci_high"] < threshold:
        return "DETECTED"
    if row["ci_low"] > threshold:
        return "NOT DETECTED"
    return "INDETERMINATE"


def main() -> int:
    rows = measure_sweep()
    print(f"  threshold {RELIABILITY_THRESHOLD}, {len(RELIABILITY_SEEDS)} seeds, "
          f"epsilon {_RELIABILITY_EPSILON}")
    for k, r in rows.items():
        print(f"  k={k:<4} mean={r['mean']:.4f} "
              f"CI=[{r['ci_low']:.4f},{r['ci_high']:.4f}] "
              f"frac>=thr={r['fraction_passing']:.4f} "
              f"tested={r['tested']} excluded={r['excluded']}  {classify(r)}")
    print("  " + json.dumps({str(k): v for k, v in rows.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the script and confirm it reproduces the pinned table**

Run: `python scripts/measure_reliability_sweep.py`

Expected, exactly (measured at `30eb333`):

```
  threshold 0.95, 200 seeds, epsilon 0.0001
  k=1.0  mean=0.9975 CI=[0.9954,0.9992] frac>=thr=0.9700 tested=12 excluded=0  NOT DETECTED
  k=1.5  mean=0.9750 CI=[0.9692,0.9804] frac>=thr=0.7150 tested=12 excluded=0  NOT DETECTED
  k=2.0  mean=0.9392 CI=[0.9300,0.9483] frac>=thr=0.4450 tested=12 excluded=0  DETECTED
  k=2.5  mean=0.9142 CI=[0.9038,0.9242] frac>=thr=0.3000 tested=12 excluded=0  DETECTED
  k=3.0  mean=0.8950 CI=[0.8842,0.9058] frac>=thr=0.2250 tested=12 excluded=0  DETECTED
```

The k=1.0 row must reproduce Gate A's published `mean 0.9975 / frac 0.9700` exactly; if it does not, the sweep is not measuring Gate A's criterion and everything downstream is void.

**The re-measured bound, which Task 7 publishes:**

> Gate A's reliability criterion **reliably detects** a perturbation-magnitude degradation of **≥2×** (at k=2 the 95% bootstrap CI [0.9300, 0.9483] lies entirely below the 0.95 threshold) and **reliably fails to detect ≤1.5×** (CI [0.9692, 0.9804], entirely above). The indeterminate region is **between 1.5× and 2×**. Superseded bound: "detects ≥2.5×, fails to detect ≤1.5×, indeterminate at 2×", measured against the defective `tested=11` mate set.

Gate A's headroom instance stays **PARTIAL, not CLOSED** — the bound is tighter, not absent. Say so in those words in Task 7.

- [ ] **Step 5: Prove the guard can fail**

The `tested == 12` pin passes against the correct script, so passing proves nothing. Demonstrate it fires:

```bash
python -c "
import sys; sys.path.insert(0,'.')
from scripts.gate_a import (_RELIABILITY_MATES, _RELIABILITY_EPSILON, RELIABILITY_SEEDS,
                            RELIABILITY_THRESHOLD, _aggregate_reliability)
for k in (1.0, 2.0, 3.0):
    a = _aggregate_reliability(_RELIABILITY_MATES, epsilon=k*_RELIABILITY_EPSILON,
                               seeds=RELIABILITY_SEEDS, threshold=RELIABILITY_THRESHOLD)
    print(f'naive epsilon scaling k={k}: mean={a.mean:.4f} tested={a.tested} excluded={a.excluded}')
"
```

Expected: `k=1.0 mean=0.9975 tested=12`, then `k=2.0 mean=1.0000 tested=6 excluded=6` and `k=3.0 mean=1.0000 tested=6 excluded=6`. Paste that output into your report. **That contrast is the finding**, and it is why the pin asserts `tested`, not just the mean.

- [ ] **Step 6: Run the tests and the full suite**

Run: `python -m pytest tests/test_reliability_sweep_pin.py -v` — expected PASS, **23** tests (three parametrized over five multipliers, plus three unparametrized, plus the coverage check).
Then: `python -m pytest -q`. Baseline was **428 passed**; expect **451**.

Do **not** run `python scripts/gate_a.py` while pytest is running.

- [ ] **Step 7: Commit**

```bash
git add scripts/measure_reliability_sweep.py tests/test_reliability_sweep_pin.py
git commit -m "feat: re-measure and pin the reliability headroom sweep on the repaired mate set"
```

---

### Task 3: Amendment 2026-08-02h — write decision D-A into the frozen §7 (NIST splits)

**Files:**
- Modify: `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md` (§7 correction log and the Gate A table)
- Modify: `scripts/gate_a.py`
- Modify: `tests/test_gate_a.py`

**Interfaces:**
- Consumes: `validation.ap242_pmi.read_pmi_counts`, `PmiCounts`
- Produces: a Gate A row named `"NIST PMI extraction"` replacing `"NIST PMI conformance"`

**Amending a frozen document is exactly the act the freeze exists to prevent, so the bar is deliberately high.** Every amendment in this plan must satisfy all four:

1. **Pre-data.** No corpus exists; §12 forbids one until Task 11.
2. **Filed as a numbered amendment** in §7's correction log, in date order, continuing the letter sequence (`a`–`d`, `e`, `f`, `g` → **`h`**).
3. **Shows the superseded text verbatim**, so a reader can see what changed.
4. **Justified as correcting a falsehood or recording a decision already made** — never as reacting to data.

Read amendments **2026-08-01f** (design spec §7, lines beginning `- *2026-08-01f (pre-data):*`) and **2026-08-01g** before writing; they are the form to follow. Note what they do: they state the defect, quote the false sentence, give the measurement, and end with how it was found.

D-A is **settled** (close-out plan, "Human decisions already made — do not re-litigate"): *NIST becomes a PMI-extraction oracle scored against its published annotations; we state plainly that no public assemblability ground truth exists for generative CAD.* It was settled **by measurement**: all 17 NIST AP242 files contain zero `NEXT_ASSEMBLY_USAGE_OCCURRENCE` entries — they are single parts.

- [ ] **Step 1: SPIKE — do NIST's published annotation counts exist in machine-comparable form?**

**Spike. Time box: 0.5 day.** Cross-reference `docs/SPIKES.md`, spike *"NIST published PMI annotation counts"*.

The amendment's wording depends on the answer and must not be written before it is known.

Question: does NIST publish, for the 17 AP242 files in `data/nist_pmi/`, per-file counts of dimensions / geometric tolerances / datums that our reader can be scored against? The MBE PMI Validation and Conformance Test Suite ships test-case *definitions* and drawings; whether those yield a machine-comparable count per file is **UNVERIFIED**.

Confirm by: locating a NIST-published table or annotation file enumerating the PMI per test case, and reconciling it against two counts we have already established by execution — `nist_ftc_06_asme1_ap242-e2.stp` reads 47 dimensions / 27 geometric tolerances / 59 datums, and the committed fixture `tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp` reads 21 / 6 / 11.

- **Outcome A — counts exist and reconcile.** The criterion becomes measured agreement against NIST's published counts. `validation/nist_pmi.py` gets an expected-counts CSV and the row can genuinely PASS.
- **Outcome B — counts exist but disagree with our reader.** *This is a finding, not a blocker.* Record the disagreement, root-cause it as the criterion's own text requires ("all others root-caused"), and write the amendment around the reconciled subset.
- **Fallback (Outcome C — no machine-comparable counts).** The criterion becomes: *the PMI-extraction reader is validated against the two files whose counts are established by execution, and the reader-validation-only scope is stated as a limitation.* The row is `PASS(measured)` on a two-file positive control with the narrowness disclosed, **not** a claim of suite-wide conformance. **Do not** invent counts, and do not let a human attestation of hand-counted PMI be labelled `measured`.

Record the outcome in your report before Step 2. If the spike overruns 0.5 day, take the fallback and move on — the fallback is honest and it is not the bottleneck.

- [ ] **Step 2: Write the failing test**

Append to `tests/test_gate_a.py`:

```python
def test_the_nist_row_is_a_pmi_extraction_oracle_not_an_assemblability_one():
    """Decision D-A, written into section 7 as amendment 2026-08-02h.

    All 17 NIST AP242 files have zero NEXT_ASSEMBLY_USAGE_OCCURRENCE entries --
    they are single parts, so the suite cannot supply an assemblability verdict
    for anything. Reporting it under a name that implies it can is the frozen
    document asserting something false about its own oracle.
    """
    out = _run_gate_a_stdout()
    line = _row("NIST PMI extraction", out)
    assert "extraction" in line.lower()
    assert "NIST PMI conformance" not in out, (
        "the old row name implies suite-wide conformance including assemblability"
    )


def test_the_nist_row_states_the_missing_ground_truth_in_its_own_note():
    """The limitation travels with the row, not only in a distant document."""
    line = _row("NIST PMI extraction", _run_gate_a_stdout())
    assert "no assemblability ground truth" in line.lower(), (
        "a reader of the Gate A report must not have to go elsewhere to learn "
        "that this oracle validates the READER, not the DECISION"
    )
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python -m pytest tests/test_gate_a.py -v -k "nist_row"`
Expected: FAIL — the row is still named `NIST PMI conformance`, so `_row("NIST PMI extraction", out)` finds nothing.

- [ ] **Step 4: File the amendment**

Append to the correction log in design spec §7, immediately after the `2026-08-01g` entry, adjusting the bracketed spike outcome to match Step 1:

```markdown
- *2026-08-02h (pre-data):* Gate A's NIST criterion is **split**, recording human
  decision D-A, which was settled by measurement well before this filing and had
  simply never been written into this section. The superseded row read:
  "Agreement with **NIST MBE PMI conformance suite** (FTC/CTC parts) — **100%**
  on decidable cases; all others root-caused", and the surrounding prose called
  it "the important one: it makes Gate A clearable without any commercial
  licence". The clearability claim stands; the implied scope does not. **All 17
  AP242 files in the suite contain zero `NEXT_ASSEMBLY_USAGE_OCCURRENCE`
  entries** — they are single parts. The suite therefore cannot supply an
  assemblability verdict for any assembly, and no amount of root-causing turns a
  single part into one. Reported under a name suggesting otherwise, the criterion
  asserted something false about its own oracle. It is replaced by two things:
  (1) a **PMI-extraction** criterion — our AP242 semantic-PMI reader is scored
  against NIST's published annotations [OUTCOME A/B: 100% agreement on the N
  reconciled files, disagreements root-caused] / [OUTCOME C: validated against
  the two files whose counts are established by execution — FTC-06 at 47
  dimensions / 27 geometric tolerances / 59 datums and the committed fixture
  CTC-01 at 21 / 6 / 11 — with the reader-validation-only scope stated as a
  limitation]; and (2) a **stated limitation**, that no public dataset pairs GD&T
  tolerances with assemblability ground truth, which is a survey result over the
  111-paper corpus and is the evidence justifying the procedural generator. This
  criterion validates the **reader**, not the **decision**, and the amended row
  says so in its own note. **No threshold was lowered:** the extraction criterion
  keeps 100%. A criterion was narrowed to what its oracle can actually decide,
  and the part it cannot decide was moved from an implicit promise to an explicit
  limitation. Pre-data: no research corpus exists (§12).
```

Then replace the NIST row in §7's Gate A table:

```markdown
| Agreement with **NIST MBE PMI** published annotations (PMI *extraction*) | **100%** on reconciled files; disagreements root-caused. Validates the reader, not the assemblability decision — see 2026-08-02h |
```

- [ ] **Step 5: Update the harness so §7 and `gate_a.py` agree**

In `scripts/gate_a.py`, rename the first tuple entry in the oracle loop (around line 530) from `"NIST PMI conformance"` to `"NIST PMI extraction"`, and extend its SKIP note so the limitation is printed on the row itself:

```python
    for name, path, load_fn, agreement_fn, threshold in (
        # 2026-08-02h: renamed from "NIST PMI conformance". The suite's 17 AP242
        # files have zero NEXT_ASSEMBLY_USAGE_OCCURRENCE entries -- single parts.
        # This oracle scores the PMI READER against published annotations; it
        # cannot score an assemblability DECISION, and the note says so on the
        # row so a reader of the report never has to go elsewhere to learn it.
        ("NIST PMI extraction", NIST_EXPECTED, nist_pmi.load_expected, nist_pmi.agreement, 1.00),
        ("TolAnalyst agreement", TOLANALYST_EXPORT, tolanalyst.load_verdicts, tolanalyst.agreement, AGREEMENT_THRESHOLD),
    ):
        if not path.exists():
            record(name, None, MEASURED, f"no export at {path.name}" + (
                "; NIST has no assemblability ground truth (all 17 AP242 files "
                "are single parts, zero NEXT_ASSEMBLY_USAGE_OCCURRENCE) -- this "
                "row scores the PMI reader only, per amendment 2026-08-02h"
                if name == "NIST PMI extraction" else ""
            ))
            continue
```

**Update the row-name lists in the pre-existing tests too.** `tests/test_gate_a.py::test_gate_a_reports_every_criterion` and `::test_gate_a_reports_v2_criteria` enumerate row names; grep for the old string and change it everywhere:

```bash
grep -rn "NIST PMI conformance" tests/ scripts/ docs/
```

**Do not** change `cleared = all(passes)` in this task, and **do not** aim for a particular exit code. If the spike's Outcome A lets this row become a real PASS, that is an output of the measurement. Gate A still has the TolAnalyst and fresh-clone SKIPs, so it still exits 1.

- [ ] **Step 6: Run**

Run: `python -m pytest tests/test_gate_a.py -v`, then `python -m pytest -q`, then (not concurrently) `python scripts/gate_a.py; echo $?`.
Expected: tests PASS; Gate A prints the renamed row with the limitation in its note and still exits 1. Paste the full report.

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md scripts/gate_a.py tests/test_gate_a.py
git commit -m "docs: amendment 2026-08-02h files decision D-A, splitting the NIST criterion"
```

---

### Task 4: Amendment 2026-08-02i — write decision D-B into the frozen §7 (TolAnalyst supplementary)

**Files:**
- Modify: `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`
- Modify: `scripts/gate_a.py`
- Modify: `tests/test_gate_a.py`

**Interfaces:**
- Consumes: `MEASURED`, `ATTESTED`, `_KINDS` from `scripts/gate_a.py`
- Produces: `SUPPLEMENTARY = "supplementary"`, added to `_KINDS`; rows of that kind are printed and tallied but excluded from `cleared`

This is the amendment with the most consequence, which is why it is its own task: it changes whether a Gate A criterion can block. Reviewer note — a reviewer may accept Task 3 and reject this one.

**The frozen document currently contradicts itself.** §7's Gate A table lists *"Verdict agreement with TolAnalyst, ≥500 Tier 2 assemblies — ≥ 95%"* as a blocking criterion, while §4.3 states the **hard constraint** that *"Every headline number reproduces with no SolidWorks license"* and adds that the NIST oracle makes Gate A *"clearable license-free — a strict improvement over v1, where the only oracle was license-gated."* Both cannot be true: a blocking criterion that requires a commercial licence is precisely a licence-gated Gate A. D-B resolves it, and D-B was **forced, not chosen**.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_gate_a.py`:

```python
def test_tolanalyst_is_supplementary_and_cannot_block_gate_a():
    """Decision D-B, filed as amendment 2026-08-02i.

    Spec section 4.3's hard constraint is that every headline number reproduces
    with NO SolidWorks licence. A blocking criterion that requires one is a
    licence-gated Gate A, which section 4.3 says in the same breath it is not.
    """
    out = _run_gate_a_stdout()
    line = _row("TolAnalyst agreement", out)
    assert "(supplementary)" in line, (
        f"TolAnalyst must be labelled supplementary, got: {line}"
    )


def test_a_supplementary_row_does_not_change_the_cleared_verdict():
    """The label must have teeth: a supplementary FAIL cannot block, and a
    supplementary PASS cannot clear. Otherwise 'supplementary' is decoration."""
    import scripts.gate_a as mod

    assert mod.SUPPLEMENTARY in mod._KINDS
    assert mod.SUPPLEMENTARY not in (mod.MEASURED, mod.ATTESTED)
    assert mod.is_blocking(mod.MEASURED) is True
    assert mod.is_blocking(mod.ATTESTED) is True
    assert mod.is_blocking(mod.SUPPLEMENTARY) is False


def test_the_tally_reports_supplementary_rows_separately():
    """A supplementary row folded into 'N PASS' inflates the blocking count --
    the same defect amendment 2026-08-01g fixed for attested rows."""
    out = _run_gate_a_stdout()
    assert "supplementary" in out.lower()
    assert "blocking" in out.lower(), (
        "the tally must say how many rows are blocking, or a reader counts "
        "supplementary rows as gate criteria"
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_gate_a.py -v -k "tolanalyst_is_supplementary or supplementary_row or tally_reports_supplementary"`
Expected: FAIL — `AttributeError: module 'scripts.gate_a' has no attribute 'SUPPLEMENTARY'`.

- [ ] **Step 3: File the amendment**

Append to §7's correction log after `2026-08-02h`:

```markdown
- *2026-08-02i (pre-data):* **TolAnalyst becomes SUPPLEMENTARY, not blocking**,
  recording human decision D-B. The superseded Gate A row read: "Verdict
  agreement with TolAnalyst, ≥500 Tier 2 assemblies — **≥ 95%**, disagreements
  root-caused". It is not deleted and its threshold is not lowered: when a
  TolAnalyst export exists the criterion is still evaluated at ≥95% and still
  reported, and a disagreement is still root-caused. What changes is that it no
  longer gates. **This corrects a contradiction inside the frozen document
  rather than reacting to data.** §4.3 states as a hard constraint that "every
  headline number reproduces with no SolidWorks license", and says in the same
  paragraph that adding the NIST oracle makes "Gate A itself now clearable
  license-free — a strict improvement over v1, where the only oracle was
  license-gated". A blocking criterion obtainable only under a commercial
  licence contradicts both sentences; §7 and §4.3 could not both be satisfied.
  The decision was **forced, not chosen** — project memory records that
  inverting it "would make their access a reproducibility liability instead of a
  credibility asset". `scripts/gate_a.py` gains a third evidence kind,
  `supplementary`, printed as `VERDICT(supplementary)` and excluded from the
  `cleared` conjunction, and the tally now states how many rows are blocking so
  a supplementary row cannot be miscounted as a gate criterion — the same defect
  2026-08-01g fixed for attested rows. **No threshold, seed set, exclusion band
  or table constant was touched, and no criterion was deleted.** Pre-data: no
  research corpus exists (§12).
```

Then edit §7's Gate A table row and add a footnote under the table:

```markdown
| Verdict agreement with TolAnalyst, ≥500 Tier 2 assemblies | **≥ 95%**, disagreements root-caused — **SUPPLEMENTARY, non-blocking** (2026-08-02i) |
```

Also amend §4.3's table row for "Validation oracle B" to read `SolidWorks TolAnalyst (supplementary, non-blocking — see §7 amendment 2026-08-02i)`.

- [ ] **Step 4: Implement the third kind**

In `scripts/gate_a.py`, extend the kind constants (currently at lines 122–124):

```python
MEASURED = "measured"
ATTESTED = "attested"
# 2026-08-02i (D-B): a criterion that is reported but cannot gate. TolAnalyst is
# licence-gated, and spec section 4.3 requires every headline number to
# reproduce without a SolidWorks licence, so it cannot both be required and be
# licence-free. It is still evaluated at >=95% and still root-caused when an
# export exists; it simply does not enter `cleared`.
SUPPLEMENTARY = "supplementary"
_KINDS = (MEASURED, ATTESTED, SUPPLEMENTARY)


def is_blocking(kind: str) -> bool:
    """True iff a row of this kind participates in the Gate A verdict."""
    assert kind in _KINDS, f"unknown kind {kind!r}"
    return kind != SUPPLEMENTARY
```

In `main()`, make `record` respect it — replace the `passes.append(...)` line:

```python
    def record(name: str, ok: bool | None, kind: str, note: str) -> None:
        # `kind` is positional and required: defaulting it to MEASURED would
        # let a future attested row inherit the stronger label by silence,
        # which is the exact defect this correction exists to remove.
        assert kind in _KINDS, f"{name}: kind must be one of {_KINDS}, got {kind!r}"
        rows.append((name, ok, kind, note))
        if is_blocking(kind):
            passes.append(ok is True)
```

In the oracle loop, give the TolAnalyst entry its own kind. Replace the shared loop with an explicit per-oracle kind so the label cannot be inherited by silence:

```python
    for name, path, load_fn, agreement_fn, threshold, kind in (
        ("NIST PMI extraction", NIST_EXPECTED, nist_pmi.load_expected,
         nist_pmi.agreement, 1.00, MEASURED),
        # 2026-08-02i: supplementary. Reported, never gating.
        ("TolAnalyst agreement", TOLANALYST_EXPORT, tolanalyst.load_verdicts,
         tolanalyst.agreement, AGREEMENT_THRESHOLD, SUPPLEMENTARY),
    ):
```

and thread `kind` through the three `record(...)` calls inside that loop in place of the literal `MEASURED` (keeping Task 3's NIST note logic).

Finally extend the tally print so the blocking count is explicit:

```python
    n_blocking = sum(1 for _, _, k, _ in rows if is_blocking(k))
    n_supp = sum(1 for _, _, k, _ in rows if not is_blocking(k))
    print(
        f"\n  {n_pass} PASS ({_count(True, MEASURED)} measured, "
        f"{_count(True, ATTESTED)} attested), {n_fail} FAIL, {n_skip} SKIP. "
        f"{n_blocking} rows are blocking; {n_supp} supplementary "
        f"(reported, never gating -- see amendment 2026-08-02i). "
        f"An attested PASS is a human's record of checking this code against a "
        f"published standard; the harness reads that record and cannot re-derive it."
    )
```

- [ ] **Step 5: Run, and report the tally honestly**

Run: `python -m pytest tests/test_gate_a.py -v`, then `python -m pytest -q`, then (not concurrently) `python scripts/gate_a.py; echo $?`.

**Report the new tally and exit code verbatim. Do not tune toward exit 0.** Gate A should still be NOT CLEARED, because the fresh-clone row is still a SKIP and (unless Task 3's spike hit Outcome A) so is NIST extraction. If Gate A *does* clear, stop and report it: a gate clearing as a side effect of a documentation amendment is a claim that needs a human to look at it, not a milestone to announce.

`tests/test_gate_a.py::test_gate_a_not_cleared_without_oracles` may need its reasoning updated; update the assertion's *reason*, never its strictness.

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md scripts/gate_a.py tests/test_gate_a.py
git commit -m "docs: amendment 2026-08-02i files decision D-B, TolAnalyst supplementary"
```

---

### Task 5: Amendment C1 to the suite-integrity design — twelve, not eleven

**Files:**
- Modify: `docs/superpowers/specs/2026-08-01-suite-integrity-design.md` (§1, §3, §4, §8)
- Modify: `tests/test_observation_assignment.py`

**Interfaces:**
- Consumes: the instance taxonomy in suite-integrity design §1
- Produces: a guard asserting §8's distribution sums to twelve and names Unencoded

Three separate falsehoods in one document, all of which the pre-registration would otherwise inherit:

1. **§1 prose, §4's Layer 3 note and §8's success criterion say "eleven"** while §1's own table enumerates **twelve**: Insensitive 4, Tautological 2, Unreachable 2, Drifted 2, Structurally impossible 1, Unencoded 1. §8's distribution (2 + 3 + 7) names eleven *distinct* instances and omits exactly one — the **Unencoded** row, the 39-cell IT table check run once in a shell. That is the only one of the twelve **no layer can catch**, so dropping it turns "all instances are caught by at least one layer" into a claim that is true only because the uncatchable one was deleted from the list. **[LR §1]**, instance-count section.
2. **§8 asserts "Gate A remains untouched and still reports 6 PASS / 3 SKIP."** Superseded by amendment 2026-08-01g: Gate A reports **7 PASS (5 measured, 2 attested), 0 FAIL, 3 SKIP**, and Tasks 3–4 have since renamed a row and added a kind.
3. **§3's "verified environment facts" are false.** It records *"There is no CI and no git remote"* — both exist at `30eb333` (`.github/workflows/ci.yml`; `origin https://github.com/harshD42/TolAEG-CAD.git`) — and *"Full suite at time of writing: 280 passed"*, now 428 before this plan and 446 after Task 2. A section headed "Trust these; do not re-litigate" containing three false statements is the worst possible combination.

This document has **no correction log**. Create one, following §7's form.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_observation_assignment.py`:

```python
import pathlib
import re

SUITE_DESIGN = (
    pathlib.Path(__file__).parent.parent
    / "docs" / "superpowers" / "specs" / "2026-08-01-suite-integrity-design.md"
)


def test_the_suite_integrity_design_counts_twelve_instances_everywhere():
    """Section 1's table enumerates twelve; the prose, section 4 and section 8
    said eleven. The dropped row is Unencoded -- the only one of the twelve NO
    layer can catch -- so 'all instances are caught' was true only because the
    uncatchable one had been removed from the list.
    """
    text = SUITE_DESIGN.read_text(encoding="utf-8")
    assert "Eleven instances" not in text
    assert "all eleven" not in text.lower()
    assert "Twelve instances are documented" in text


def test_the_layer_distribution_accounts_for_the_unencoded_instance():
    """Section 8's distribution must sum to twelve and must say Unencoded is
    caught by NO layer, rather than omitting it and appearing complete."""
    text = SUITE_DESIGN.read_text(encoding="utf-8")
    section8 = text.split("## 8. Success criteria", 1)[1]
    assert "Unencoded" in section8, (
        "section 8's distribution silently omits the Unencoded instance"
    )
    assert re.search(r"caught by no layer|no layer catches", section8, re.I), (
        "the Unencoded instance must be recorded as uncaught, not just listed"
    )


def test_the_suite_integrity_design_has_a_correction_log():
    text = SUITE_DESIGN.read_text(encoding="utf-8")
    assert "Correction log" in text
    assert "2026-08-02-C1" in text


def test_the_suite_integrity_design_states_no_superseded_environment_facts():
    """Section 3 is headed 'Trust these; do not re-litigate'. It contained
    three statements that are false at 30eb333."""
    text = SUITE_DESIGN.read_text(encoding="utf-8")
    assert "There is no CI and no git remote" not in text
    assert "280 passed" not in text
    assert "6 PASS / 3 SKIP" not in text
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_observation_assignment.py -v`
Expected: FAIL — all four new tests fail against the unamended document.

- [ ] **Step 3: Amend the document**

In `docs/superpowers/specs/2026-08-01-suite-integrity-design.md`:

(a) §1 prose — change `Eleven instances are documented across Phases 0–3.5b.` to `Twelve instances are documented across Phases 0–3.5b.`

(b) §4's Layer 3 note — change `Four of the eleven instances lived there` to `Four of the twelve instances lived there`.

(c) §8's first bullet — replace it with:

```markdown
- All **twelve** historical instances are accounted for, and **eleven of the twelve
  are caught by at least one layer**. The mapping is enumerated in the
  implementation plan and **verified by reproducing each instance**, not asserted —
  a success criterion that merely claims coverage would itself be the defect this
  design exists to prevent.
  Distribution: Layer 1 catches 2 (unreachable branch, module-level skip), Layer 2
  catches 3 (tautological assertion, blind anti-degeneracy guard, and the skip
  again by surviving mutants), Layer 3 catches 7 (self-referential constants, CRLF
  fixture, case-sensitive guard, drifted literal floor, reliability range, Gate A
  headroom, seed fishing). Several are caught by more than one layer.
  **The twelfth — the *Unencoded* instance, a 39-cell IT-table check run once in a
  shell and never committed — is caught by no layer, and cannot be.** No mutation
  of `src/`, no branch of a test that was never written, and no registry entry can
  observe a verification that left no artifact. Only O-D reaches it. Recording it
  as uncaught is the point: the earlier "eleven" distribution appeared complete
  precisely because the one instance no layer covers had been dropped from the
  count.
```

(d) §8's Gate A bullet — replace `Gate A remains untouched and still reports 6 PASS / 3 SKIP.` with:

```markdown
- Gate A remains untouched **by this design**. Its reported row set is owned by the
  design spec's correction log, not by this document; see amendments 2026-08-01g,
  2026-08-02h and 2026-08-02i. Do not restate a Gate A tally here — a second copy
  of a number is a second thing to go stale, and this bullet already did.
```

(e) §3 — replace the two false bullets:

```markdown
- **CI and a git remote both exist.** `.github/workflows/ci.yml` runs a two-job
  workflow (suite on ubuntu+windows; the ~25-minute integrity layer on
  `workflow_dispatch` + weekly cron only), and `origin` is
  `https://github.com/harshD42/TolAEG-CAD.git`. *Superseded 2026-08-02-C1: this
  section previously read "There is no CI and no git remote." True when written on
  2026-08-01, false from the close-out's Task 7 onward.*
- Full suite: **428 passed** at `30eb333`. *Superseded 2026-08-02-C1: previously
  "280 passed". Do not re-pin this number here; nothing asserts a suite count (see
  the observation-assignment table's O-A row), so this figure is narrative and
  carries a date and a commit for that reason.*
```

(f) Add a correction log immediately after the `**Status:**` line at the top:

```markdown
**Correction log.**
- *2026-08-02-C1 (pre-data):* Three superseded statements corrected. (1) §1's
  prose, §4's Layer 3 note and §8's success criterion said **eleven** instances
  where §1's own table enumerates **twelve**; §8's distribution named eleven
  distinct instances and omitted exactly the **Unencoded** row — the only one of
  the twelve no layer can catch — so "all instances are caught by at least one
  layer" was true only because the uncatchable one had been dropped. §8 now reads
  eleven-of-twelve caught, with the twelfth recorded as uncaught and uncatchable.
  (2) §8's "Gate A remains untouched and still reports 6 PASS / 3 SKIP" was
  superseded by design-spec amendment 2026-08-01g; the tally is no longer restated
  here at all. (3) §3's "verified environment facts", a section headed "Trust
  these; do not re-litigate", asserted "There is no CI and no git remote" and
  "280 passed", both false at `30eb333`. Filed before the Phase 3.5 freeze because
  the pre-registration cites this document's instance taxonomy, and publishing a
  count this document contradicts internally would carry the error into a
  permanent record. No threshold, layer, pin or registry entry was changed.
```

- [ ] **Step 4: Run**

Run: `python -m pytest tests/test_observation_assignment.py -v`, then `python -m pytest -q`.
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-08-01-suite-integrity-design.md tests/test_observation_assignment.py
git commit -m "docs: amendment C1 -- twelve instances, the uncatchable one named, stale env facts corrected"
```

---

### Task 6: Rule on whether P1.5 blocks the freeze, and record the argument

**Files:**
- Create: `docs/preregistration/P1-5-RULING.md`

**Interfaces:**
- Consumes: **[LR §1]** mutation-score and untriaged-survivor sections
- Produces: a citable ruling that Tasks 7 and 8 reference

An unruled blocker is worse than either answer, because it silently becomes an argument for unfreezing later. The ruling below is this plan's position; Task 10's adversarial reader is explicitly charged with attacking it.

- [ ] **Step 1: Write the ruling**

Create `docs/preregistration/P1-5-RULING.md` with this content:

```markdown
# Does P1.5 block the Phase 3.5 pre-registration?

**RULING: No. P1.5 does not block the freeze, and must be scheduled immediately
after it.** Three conditions attach; they are binding, not caveats.

## What P1.5 is

A 1.5-serialised-day Layer 2 re-measurement and full survivor triage. Nothing may
edit `src/` *or* `tests/` while it runs; cosmic-ray reads both from disk. The
deliverable is an *enumerated* survivor set, a ruling per survivor, an explanation
for the observed 100.00%, and only then a re-pin. **[LR §1]** records the state it
must resolve: the mutation pin is 95.89% ± 0.50, the last measurement was 100.00%,
and the two disagree **by design** — the two-sided pin fired correctly on its
first real encounter. The untriaged survivor count for the current tree is
**UNKNOWN**; the last actual enumeration was 21, at run 3.

## The argument that it does not block

**1. Nothing pre-registered depends on it.** The freeze publishes hypotheses,
metrics, the Gate A/B/C/D criteria, the analysis plan, the seeds, the corpus
recipe and digest, and the limitations. The Layer 2 mutation score is none of
these. The suite-integrity design says so in its own non-goals: *"Not a research
gate. Gate A/B/C/D thresholds are frozen by `CLAUDE.md`; nothing here is folded
into them."* No Gate A criterion reads the mutation score. No published number in
the pre-registration is justified by it.

**2. The irreversibility argument does not reach it.** The reason the baseline
audit blocks is that Gate C's `≥6 of ≥8` cannot be lowered after data exists
without invalidating Gate C — the damage is permanent. The mutation pin has the
opposite property: it can be re-measured and re-pinned at any time, before or
after the freeze, and doing so invalidates nothing, because no pre-registered
claim rests on it. Re-pinning is explicitly routine under the Layer 1/2 threshold
policy. **Blocking is for the unrecoverable. P1.5 is recoverable.**

**3. Running it first would be actively wasteful, and the waste is structural.**
P1.5 requires a frozen `src/` and `tests/` for 1.5 serialised days. This plan
creates `tests/test_reliability_sweep_pin.py` and `scripts/measure_reliability_sweep.py`
(Task 2), and modifies `scripts/gate_a.py`, `tests/test_gate_a.py` and
`tests/test_observation_assignment.py` (Tasks 3–5). Any P1.5 run completed before
those land is measured against a tree that no longer exists and must be redone.
Sequencing P1.5 first does not de-risk the freeze; it buys a stale enumeration.

**4. P1.5 cannot disturb the frozen corpus.** The freeze pins generator behaviour
through the corpus digest
`c035c2d99d377c1f1c6f912c9c690e47376e012eee37f4283c41de0051336fa3` and the four
ladder counts. P1.5's remedies are *adding tests* to kill survivors and *recording
rulings* for equivalents — neither touches `src/tolcad/gen/`. A post-freeze P1.5
therefore lands on a tree whose digest cannot move. Running it *before* the freeze
would give it more scope to perturb the corpus, not less.

## The conditions

**C1 — Disclose, in the limitations section, that the Layer 2 pin is currently
firing.** The pre-registration must state the pin (95.89% ± 0.50), the last
measurement (100.00%), that they disagree, that the survivor count for the current
tree is UNKNOWN, that the last enumeration was 21 at run 3, and that resolution is
scheduled and unstarted. Publishing "a three-layer suite-integrity gate" while one
layer's pin is red, without saying so, would be this project's dominant failure
mode committed in the permanent record. Task 8 owns this.

**C2 — No pre-registered number may be justified by the Layer 2 score.** Verified
at filing: none is. Task 9's freeze manifest re-checks it, because the cheapest way
for this condition to rot is for a later draft to reach for the number as evidence
of suite quality.

**C3 — P1.5 is scheduled immediately after Task 11 and before any corpus
generation.** It is the first Phase 4 item, not a backlog entry. It inherits a tree
that has stopped moving, which is the condition it always needed and never had. The
work is already planned in seven serialised tasks at
`docs/superpowers/plans/2026-08-02-mutation-survivor-triage.md`, and the diagnostic
question is registered as the spike *"Why does the mutation score read 100.00%?"*.
This ruling changes P1.5's *position in the order*, not its content.

## What would overturn this ruling

If P1.5's enumeration shows the 100.00% arises from a **broken instrument** — a
collapsed denominator, a test command that silently stopped running, mutants
recorded killed that were not — then the *conclusion* that the checker core is
well-tested is unsupported, and the pre-registration's claim that Tier 1 is exact
would be resting on less evidence than a reader would assume. That is a real risk
and it is why C1 is mandatory rather than advisory. It is **not** a reason to
block: the pre-registration nowhere claims the mutation score as evidence, and C1
makes the gap explicit. But if P1.5 lands that way, the deviations table must
record it plainly rather than waiting for a reviewer to ask.
```

- [ ] **Step 2: Commit**

```bash
git add docs/preregistration/P1-5-RULING.md
git commit -m "docs: rule that P1.5 does not block the pre-registration, with conditions"
```

---

### Task 7: Write the pre-registration — hypotheses, metrics, gates, analysis plan, seeds, corpus, baselines

**Files:**
- Create: `docs/preregistration/PREREGISTRATION.md` (everything except the limitations section)

**Interfaces:**
- Consumes: design spec §1/§2/§6/§7/§8, **[LR §1]**, Task 2's sweep, Tasks 3–5's amendments, Task 6's ruling
- Produces: the document Tasks 8–11 complete, review and publish

**One human decision is required before this task can finish** (precondition P7): the research-corpus seed range. It must be **disjoint from 0–199**, because the difficulty ladder was calibrated on exactly those seeds — the repair moved d4 from 478/609 to 421/609 measured over them (**[LR §1]**, pre-fix d4 section). Recommended default to put to the human: **assembly seeds 1000–N**, which is disjoint in assembly-seed space and, since `sampler._mc_seed_for(seed, mate_index) = 10_000 + seed*4 + mate_index` and the calibration corpus's real `iso_fit` Monte Carlo seeds span **10006–10791**, disjoint in Monte Carlo seed space as well. Do not choose N yourself.

- [ ] **Step 1: Write the document skeleton and the non-negotiable framing**

Create `docs/preregistration/PREREGISTRATION.md` with these sections in order. Section 10 is written by Task 8.

```markdown
# Pre-Registration: Nominally Correct, Functionally Wrong

**Registered:** <date> · **Repository:** https://github.com/harshD42/TolAEG-CAD
**Frozen at commit:** <FREEZE_SHA> · **Freeze manifest:** `docs/preregistration/FREEZE-MANIFEST.md`
**Status at registration:** no research corpus has been generated. Design spec §12
orders Phase 3.5 before Phase 4, and this document is Phase 3.5.

## 0. What this document is, and the one rule it follows

It publishes the hypotheses, metrics, gate criteria, analysis plan and seeds
BEFORE the data exists, so the result cannot be reverse-engineered from the
outcome. Thresholds are frozen by `CLAUDE.md`; changing one after seeing data
invalidates the result.

**Every number in this document is quoted from a specification or from a committed
executable pin, never from a working ledger.** The project's SDD ledgers under
`.superpowers/sdd/` are contemporaneous logs; roughly a dozen of them still carry
a superseded reliability figure and they outnumber the correct one in a grep. The
adjudicated values live in `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`,
cited throughout as [LR §1].

## 1. Hypotheses
## 2. What is novel, and against what
## 3. The checker, and what "exact" means
## 4. Metrics and the primary statistic
## 5. Gate A — checker correctness (blocking)
## 6. Gate B — the finding
## 7. Gate C — mechanism (supporting)
## 8. Gate D — publication readiness
## 9. The corpus, the seeds, and the analysis plan
## 10. Limitations            <- Task 8
## 11. Deviations table       <- empty at registration, append-only thereafter
```

- [ ] **Step 2: Write §1–§3 — hypotheses and the claim**

State H1 verbatim from design spec §1: *a substantial fraction of generative-CAD output that scores well on nominal geometric metrics is functionally unassemblable, and nominal metrics cannot predict which.*

State the claim verbatim from design spec §2, and be careful which claim it is — it is **not** "Chamfer distance is area-weighted" (ASSEMCAD 2607.05123 App. H.5 already says that): *assemblability under manufacturing variation is measurable deterministically from published standards, nobody has measured it for generative CAD, and doing so changes model rankings.*

Reproduce §2's prior-work table (ASSEMCAD, MUSE, CADTestBench, Beyond Statistical Similarity 2302.02913, KAN tolerance-aware DFM 2601.06334, politopix 1509.08763, JoinABLe/AutoMate/Linkify, OCCT XCAF `XCAFDoc_DimTolTool`) and the near-misses to distinguish (HistCAD's sketch constraints; MatchMaker's clearance erosion).

In §3, state the tier split from design spec §4.1 and **state the per-part `min()` form explicitly**: Tier 1 floating-fastener margin is `min(H_a − F − T_a, H_b − F − T_b)`, ASME B-3's per-part rule, **not** the pooled sum. Mistaking it for a sum is what produced the `mate[8]` defect that made a frozen document state a falsehood about its own instrument. Give the standards: ASME Y14.5-2018 §7 and Nonmandatory Appendix B; ISO 286-1 Tables 1/4/5; ISO 273-1979(E) Table 1; ISO 2306-1972 Table 1. Tier 3 is out of scope and stated as a limitation. Loop length ≤ 4 contributors.

- [ ] **Step 3: Write §4 and §6–§8 — metrics, Gates B, C, D**

From design spec §7 and §8, unchanged:

- Primary statistic **AUC / Somers' D** (`D = 2·AUC − 1`), base-rate invariant. Report **within-model primary, pooled secondary**, 95% CIs from a **model-level cluster bootstrap**. Base rate and tie counts reported alongside, always.
- Gate B: **Strong** = upper CI bound < 0.65; **Moderate** = CI overlaps [0.65, 0.80]; **Null** = lower CI bound > 0.80; otherwise **Inconclusive**. Spearman ρ and Kendall τ-b secondary, with the base-rate ceiling stated.
- **Publish the null contingency IN FULL, in advance.** A null is a genuine negative result; the checker, the validated implementation and the procedural benchmark retain full value and the paper reframes as a benchmark and resource contribution. This is the floor and it is still publishable. Pre-registering the null contingency is what makes it credible later.
- Gate C: normalized error ratio ≥ 2.0× with a bootstrap CI excluding 1.0; **effect holds across ≥6 of the ≥8 baseline models**; within-model estimates reported, not only pooled.
- Gate D: the seven rows of §7's Gate D table verbatim.
- §8's eight binding statistical rules verbatim, especially **no dropping failed generations** (assign worst-case metric values; report both ways) and **negate Chamfer** so all metrics point the same direction.

- [ ] **Step 4: Write §5 — Gate A, with the corrections shown, not the tables verbatim**

**"Publish §7 verbatim" is withdrawn and must not be reinstated.** The pre-2026-08-01f text of lines about the reliability instrument states a falsehood about our own instrument. Publish the tables **plus the corrections with the superseded text shown**.

§5 must contain:

- The Gate A criteria table **as amended** by 2026-08-02h and 2026-08-02i.
- The **complete correction log**: 2026-07-31a–d, 2026-08-01e, 01f, 01g, 2026-08-02h, 2026-08-02i — nine entries — each with its superseded text visible. Say plainly that 01e's sentence *"at 12 tested mates the only values reachable near the threshold are 1.0000 and 0.9167"* was **false when written** (there were eleven tested; reachable values were {0.9091, 1.0}) and is **true of the repaired instrument**.
- **The reliability declaration**, quoted from the spec, never from a ledger:
  - mean **0.9975**, 95% bootstrap CI **[0.9954, 0.9992]** over 10,000 resamples, fraction of seeds ≥ 0.95 = **0.9700**, **tested = 12, excluded = 0**, 200 pre-registered seeds (0–199). [LR §1], amendment 2026-08-01f.
  - The **D-D construction rule**, stated as a rule and not just an outcome: *each sensitive-band mate has exactly one binding part at ±3.5e-4; every other part in that mate is slack at ≥10× the band.* Record that it **determines** the number rather than choosing it — two reviewers produced 0.9967 and 0.9971 from different constructions of the same stated intent.
  - The **3.5e-4 free parameter, declared as a design choice**, per design spec §7's "Also note for §8": it was chosen after the seed was pinned, a smaller value fails more often, and it must be presented as a choice rather than as forced.
  - **The re-measured headroom bound from Task 2**, with its table and its CI-based verdicts, and the superseded bound shown. State that Gate A's headroom instance is **PARTIAL, not CLOSED**.
- The commitment that **no result comes from a single draw**, and the pre-declared seed set for every statistic (§9).

- [ ] **Step 5: Write §9 — corpus, seeds, digest, baselines, analysis plan**

**Calibration corpus (already generated, frozen, cited as the instrument's calibration set — NOT the research corpus):**

| Item | Value | Pin |
|---|---|---|
| Recipe | `scripts/measure_ladder.py::LADDER_RECIPE` — seeds `range(0, 200)`, difficulties `[1,2,3,4]`, counted "Tier 1 mates only (`kind != 'iso_fit'`)", statistic `check(mate.to_check_dict()).assembles is False` | `tests/gen/test_ladder_pin.py` |
| Tier 1 ladder | d1 **31/159** (19.5%), d2 **99/301** (32.9%), d3 **239/452** (52.9%), d4 **421/609** (69.1%) | exact counts, two-sided |
| Corpus digest | `c035c2d99d377c1f1c6f912c9c690e47376e012eee37f4283c41de0051336fa3` | `test_the_corpus_digest_is_reproducible` |
| numpy | `2.4.1`, exact (D-C — `Generator`'s stream is not covered by NEP 19) | `pyproject.toml` |

**Research corpus (NOT yet generated) — declare the recipe, publish the digest at generation time:**

- Assembly seeds: **<HUMAN DECISION, P7 — recommended 1000–N>**, **disjoint from 0–199**. Record the disjointness reason in the document: the ladder was calibrated on 0–199, so reusing them is calibrating on the evaluation set. Note the derived disjointness in Monte Carlo seed space (calibration `iso_fit` seeds span 10006–10791).
- Difficulty mix, assemblies per difficulty: **<HUMAN DECISION>**.
- Commitment: the generated corpus's SHA-256 digest, computed by the same `corpus_digest()` recipe, is published in the deviations table at generation time and before any model is run against it.

**Every seed and sampling constant, pre-declared:**

| Constant | Value | Where |
|---|---|---|
| `RELIABILITY_SEEDS` | `tuple(range(200))` | `scripts/gate_a.py` |
| `RELIABILITY_THRESHOLD` | `0.95` | `scripts/gate_a.py` |
| `_RELIABILITY_EPSILON` | `1e-4` | `scripts/gate_a.py` |
| `BOUNDARY_BAND` | `2.0` (exclusion band `2ε`) | `src/tolcad/reliability.py` |
| `RELIABILITY_BOOTSTRAP_RESAMPLES` | `10_000` | `scripts/gate_a.py` |
| `_BOOTSTRAP_RNG_SEED` | `0` | `scripts/gate_a.py` |
| `SWEEP_K` | `(1.0, 1.5, 2.0, 2.5, 3.0)` | `scripts/measure_reliability_sweep.py` |
| `_MC_SEED_BASE` | `10_000`; `_mc_seed_for(seed, i) = 10_000 + seed*4 + i` | `src/tolcad/gen/sampler.py` |
| `_MC_SAMPLES` | `100_000` (raised from 10k by amendment 2026-07-31a) | `src/tolcad/gen/sampler.py` |
| `_PLATE_THICKNESS_MM` | `8.0`, also the B-4 projected-zone distance | `src/tolcad/gen/sampler.py` |
| `SUPPORTED_FITS` | `("H7/g6", "H7/k6", "H7/p6")` — H7/h6 dropped as line-to-line | `src/tolcad/gen/features.py` |
| `FASTENER_SIZES` | `(3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0)` | `src/tolcad/gen/features.py` |
| `_ISO_FIT_NOMINALS_MM` | `(10.0, 12.0, 16.0, 20.0, 25.0)` | `src/tolcad/gen/sampler.py` |
| Cluster-bootstrap resamples and seed | **<HUMAN DECISION>** — must be fixed here, not at analysis time | Phase 4 |

**Baselines.** Name all nine from design spec §6 with their arXiv IDs — CAD-Recode 2412.14042, cadrille 2505.22914, CAD-Coder/MIT **2505.14646** (*not* Beihang 2505.19713 — two distinct papers share the name; do not conflate), Text-to-CadQuery 2505.06507, DeepCAD 2105.09492, Text2CAD 2409.17106, BrepGen 2401.15563, DTGBrepGen 2503.13110, HoLa 2504.14257 — plus prompted frontier VLMs emitting CadQuery. State the runnability-audit result from Task 1 Step 2 with its evidence pointer, and state that Gate C requires the effect to hold across ≥6 of ≥8.

- [ ] **Step 6: Add §11, the empty deviations table**

```markdown
## 11. Deviations from this pre-registration

Append-only. Empty at registration. Every entry records: date, what changed, why,
whether it was pre-data or post-data, and what it invalidates if anything.

| Date | Change | Reason | Pre/post data | Invalidates |
|---|---|---|---|---|
| — | *(none at registration)* | — | — | — |
```

- [ ] **Step 7: Verify every citation in the document resolves**

Not optional and not a formality — five consecutive plans in this project shipped snippets that did not run as written.

```bash
grep -oE '`[a-zA-Z0-9_./-]+\.(py|md|toml|yml|stp)`' docs/preregistration/PREREGISTRATION.md \
  | tr -d '`' | sort -u | while read -r f; do
    [ -e "$f" ] || echo "MISSING PATH: $f"
  done
```

Expected: no output. Then confirm every quoted scalar appears in a committed pin or spec — Task 9 Step 3 automates this; here just fix anything the path check finds.

- [ ] **Step 8: Commit**

```bash
git add docs/preregistration/PREREGISTRATION.md
git commit -m "docs: pre-registration body -- hypotheses, gates, seeds, corpus, baselines"
```

---

### Task 8: Write the limitations section, honestly and up front

**Files:**
- Modify: `docs/preregistration/PREREGISTRATION.md` (§10)

**Interfaces:**
- Consumes: the close-out plan's literature survey table; Task 6's ruling; Task 2's bound
- Produces: §10, complete

A limitations section written after review is a concession. Written before, it is a claim about the standard the work is held to. This one is separated from Task 7 because a reviewer could accept the study design and reject the honesty of its disclosure — and because this is where the pre-registration earns or loses its credibility.

- [ ] **Step 1: Write §10.1 — no public dataset pairs GD&T with assemblability ground truth**

**Frame it as a survey result, not an admission.** It is what justifies building a generator. Reproduce the table from `docs/superpowers/plans/2026-08-01-closeout.md` ("Literature survey result"), over the 111-paper corpus:

| Source | Assemblies | GD&T tolerances | Assemblability ground truth |
|---|---|---|---|
| NIST MBE PMI suite | ✗ — all 17 AP242 files are single parts, zero `NEXT_ASSEMBLY_USAGE_OCCURRENCE` | ✓ semantic PMI | ✗ |
| AutoMate (2105.12238) | ✓ *"first large scale dataset of BREP CAD assemblies"* | ✗ | ✗ — states outright *"there is no ground truth"*; mating is design intent |
| MUSE (2605.28579) | ✓ | ✗ | ✓ but a VLM rubric, not arithmetic |
| ASSEMCAD / ASSEMBENCH (2607.05123) | ✓ curated mechanical assemblies | ✗ — "tolerance" occurs twice, once as a mesh epsilon | ✗ |
| politopix (1509.08763) | GD&T polytopes | ✓ | academic, unmaintained |

Closing line: assemblies exist, tolerances exist, assemblability judgments exist; **no public dataset has all three**, which is the gap this work fills. Gate D requires ≥80 papers reviewed; 111 were.

- [ ] **Step 2: Write §10.2 — the oracle-independence ceiling**

State plainly: **the ground truth and the checker are the same arithmetic.** The generator emits a tolerance schema and the checker evaluates it under ASME Y14.5 and ISO 286; a model's verdict is therefore scored against our own implementation of the standards. The mitigations and their exact limits:

- The three published ASME Y14.5-2018 Appendix B worked examples are encoded at the standard's own inputs (B-3 F=6.0/H=6.44/T=0.44; B-4 T=0.22; B-4 unequal split T1=0.18/T2=0.26) and run as a **measured** Gate A row. This bounds transcription error on those three points; it does not make the oracle independent.
- The NIST oracle validates the **PMI reader**, not the assemblability **decision** (amendment 2026-08-02h).
- TolAnalyst would be a genuinely independent industrial oracle, and it is **supplementary, non-blocking** (amendment 2026-08-02i) because §4.3 requires licence-free reproduction. **State the trade honestly: reproducibility was bought at the cost of oracle independence.** That is a defensible choice and it must be presented as a choice, not concealed.
- Two Gate A rows are **attested, not measured** — a human's record that source was checked against a published standard, which the harness reads and cannot re-derive.

- [ ] **Step 3: Write §10.3 — the fresh-clone receipt's self-report ceiling**

Design spec §7 requires *"Fresh clone, no SW license, full pipeline — runs end-to-end"*, currently a SKIP. The P2.3 receipt design is settled: valid if its `commit_sha` is an **ancestor** of HEAD and `git diff --name-only <sha>..HEAD` touches nothing **outside** `docs/`, `papers/`, `.superpowers/`, `README*`, `LICENSE` — a **denylist**, because the allowlist form already missed `.gitattributes` and `cosmic-ray.toml`.

**Its ceiling is a self-report: ancestor-plus-clean-paths prevents staleness, not forgery.** Printing the CI workflow URL makes it checkable by a third party; it does not make it enforced. Disclose this **in the same sentence** as the related accepted limit B4 — one commit can delete a registry entry *and* its name from `_CRITICAL_GUARDS` together, and no mechanical control can catch it; only a reader over the diff can.

- [ ] **Step 4: Write §10.4 — the geometry is narrow, and here is the planned generalisation**

State it before a reviewer does: the reference geometry is **two synthetic plates with holes in a line**. Concretely — `build.py` produces two stacked plates with one feature per mate; `layout.py` places features from sampled radii; loop length is capped at 4 contributors; Tier 3 (freeform surfaces, kinematic mechanisms, form defects) is out of scope by design spec §4.1 and §13.

Name the generalisation as **planned**, not as a hope: **AutoMate's BREP assemblies (2105.12238)** can supply real, public, large-scale CAD geometry from real designs, with our tolerance schema applied on top. Say what it does and does not fix — it answers the narrow-geometry criticism; it **does not** solve oracle independence, since the verdicts would still be ours plus TolAnalyst.

- [ ] **Step 5: Write §10.5 — the anti-vacuity machinery has never discovered an instance**

This is the disclosure most likely to be omitted and the one most worth making. Quote the finding: **zero of the twelve historical "cannot fail" instances were found by the three-layer machinery; ten were found by an adversarial reader over a diff.** The layers are a **recurrence ratchet, not a detector**. Corollaries to state:

- **Awareness is explicitly not a control.** The pattern was in project memory and in nearly every review prompt of the 2026-08-01 session, and three new instances still landed.
- **O-D discovers; it does not guard.** A one-time discovery does not discharge R2 for recurrence.
- One of the twelve — the **Unencoded** instance — is caught by **no layer and cannot be** (amendment 2026-08-02-C1).
- Instance *numbers* are unreliable: only instances 2, 3, 4, 5, 6 and 10 are attested in code or spec text, the other six positions cannot be reconstructed, and **no new ordinal may be minted**. Refer to instances by name.
- Instances 5 and 6 are **FIXED-NO-LAYER** — guarded by a specific test, but Layer 1's coverage is scoped to six modules under `src/tolcad` while those live in `tests/` and `scripts/`.

- [ ] **Step 6: Write §10.6 — condition C1 of the P1.5 ruling**

Per `docs/preregistration/P1-5-RULING.md`, state: the Layer 2 mutation pin is **95.89% ± 0.50**, the last measurement was **100.00%**, they **disagree and the two-sided pin is currently firing** — which is the control working, not a failure to hide. The untriaged survivor count for the current tree is **UNKNOWN**; the last actual enumeration was **21, at run 3**; every later figure (~12, ~17, ~27, 0) is arithmetic over a score rather than an enumeration [LR §1]. **DO NOT RE-PIN** until P1.5 produces an enumeration. Say that P1.5 is scheduled immediately post-freeze, and that no pre-registered number is justified by the mutation score.

- [ ] **Step 7: Write §10.7 — the residual disclosures**

Short, specific, each with a bound:

- **The ISO-fit boolean is determined by the shaft letter as a matter of arithmetic**, at every diameter — `assembles` is `yield >= 1.0`, so for a hole-basis fit the verdict is True exactly when the shaft's upper deviation `es <= 0`, which *is* the definition of a clearance-class letter. Pinned by an executable assertion. **Tier 2's contribution to the benchmark is therefore the continuous yield, not this boolean.**
- **Monte Carlo seeds are reused across difficulty levels.** `_mc_seed_for(seed, mate_index)` does not take `difficulty`, so the same (assembly seed, mate index) draws the same stream at every difficulty where it is an `iso_fit` mate. Measured over the calibration corpus: **479 `iso_fit` mates draw on only 191 distinct Monte Carlo seeds; 148 seeds are shared across difficulty levels, none within a level.** The `_mc_seed_for` docstring's word "collision-free" is true *within* a difficulty and false across the corpus. **This is disclosed and deliberately NOT fixed**: changing the seed derivation would move the frozen corpus digest and the four frozen ladder counts. Post-freeze it would be a deviations-table entry.
- **Two untraced constants**, declared inert with the reason: `_FASTENER_LOWER_DEV_MM = -0.1` and `_FASTENER_UPPER_DEV_MM = 0.0`. A fastener is an external feature so its MMC is `nominal + upper_dev`; with `upper_dev = 0.0` the MMC is exactly nominal and `y14_5.fastener_assembles` reads MMC and nothing else. Both carry executed declared-mutation guards.
- **Tier 1 fixed-fastener verdicts assume a projected tolerance zone.** ASME Y14.5 Appendix B-4 assumes one; B-5 covers the non-projected case and **tolcad does not implement it**. The generator records `projected_zone_mm` in the published schema; the checker has no `P` term.
- **`H7/h6` was dropped from the sampled fit set** before pre-registration because it is line-to-line: its label was decided by whether any of 100,000 draws landed on the boundary (85 True / 23 False across the corpus). Disclosed so the fit set's composition is not mistaken for an accident.

- [ ] **Step 8: Verify the limitations section makes no claim the repo contradicts**

For each of §10.2's "two attested rows", §10.6's numbers and §10.7's measured counts, run the command that establishes it and paste the output into your report. Specifically:

```bash
python scripts/gate_a.py 2>&1 | grep -c "attested"
python -c "
import sys; sys.path.insert(0,'.')
from tolcad.gen.sampler import sample_assembly
from collections import defaultdict
owners=defaultdict(set)
for d in (1,2,3,4):
    for s in range(200):
        for i,m in enumerate(sample_assembly(s,d).mates):
            if m.kind=='iso_fit': owners[m.mc_seed].add((d,s,i))
tot=sum(len(v) for v in owners.values())
print('iso_fit mates', tot, '| distinct mc_seeds', len(owners),
      '| shared across difficulties', sum(1 for v in owners.values() if len(v)>1),
      '| mc_seed range', min(owners), max(owners))
"
```

Expected from the second command, measured at `30eb333`: `iso_fit mates 479 | distinct mc_seeds 191 | shared across difficulties 148 | mc_seed range 10006 10791`.

- [ ] **Step 9: Commit**

```bash
git add docs/preregistration/PREREGISTRATION.md
git commit -m "docs: pre-registration limitations, disclosed up front with measured bounds"
```

---

### Task 9: Freeze manifest and an executable verifier

**Files:**
- Create: `docs/preregistration/FREEZE-MANIFEST.md`
- Create: `scripts/verify_freeze.py`
- Create: `tests/test_freeze_manifest.py`

**Interfaces:**
- Consumes: `hashlib`, `pathlib`, `subprocess`
- Produces: `FROZEN_PATHS: tuple[str, ...]`; `digest_of(path: str) -> str`; `manifest_rows() -> list[tuple[str, str]]`; `check_manifest() -> list[str]` returning a list of human-readable discrepancies (empty means clean)

The requirement: *a later reader can diff the published version against the repo and see nothing moved.* A prose list cannot do that. Hashes plus a script can.

- [ ] **Step 1: Write the failing test**

Create `tests/test_freeze_manifest.py`:

```python
"""The freeze manifest must be checkable, and must be able to fail.

A manifest nobody can verify is a promise; a manifest with a verifier is a
receipt. The self-exclusion test matters: a manifest that hashed itself could
never be clean, and the tempting fix -- dropping the check -- is how a manifest
quietly stops covering anything.
"""

import pathlib

import pytest

from scripts.verify_freeze import (
    FROZEN_PATHS,
    MANIFEST,
    check_manifest,
    digest_of,
    manifest_rows,
)

REPO = pathlib.Path(__file__).parent.parent


def test_every_frozen_path_exists():
    missing = [p for p in FROZEN_PATHS if not (REPO / p).is_file()]
    assert not missing, f"the manifest freezes paths that do not exist: {missing}"


def test_the_manifest_does_not_freeze_itself():
    assert MANIFEST not in FROZEN_PATHS, (
        "a manifest that hashes itself can never verify clean"
    )


def test_the_manifest_matches_the_tree():
    discrepancies = check_manifest()
    assert not discrepancies, (
        "the tree has moved since the freeze. Every line below is either a "
        "deviation that belongs in PREREGISTRATION.md section 11, or an "
        "accident:\n" + "\n".join(discrepancies)
    )


def test_the_verifier_notices_a_changed_file(tmp_path):
    """Prove the detector detects, rather than trusting that it does."""
    victim = REPO / FROZEN_PATHS[0]
    original = victim.read_bytes()
    try:
        victim.write_bytes(original + b"\n<!-- transient -->\n")
        assert check_manifest(), "the verifier missed a genuinely changed file"
    finally:
        victim.write_bytes(original)
    assert not check_manifest(), "the verifier did not clear after restore"


def test_the_manifest_freezes_the_documents_the_preregistration_quotes():
    """The design spec, the reconciliation and the pins are the sources the
    published document cites. If any can move unnoticed, the citation is not a
    citation."""
    required = {
        "docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md",
        "docs/superpowers/specs/2026-08-01-ledger-reconciliation.md",
        "docs/superpowers/specs/2026-08-01-suite-integrity-design.md",
        "docs/superpowers/specs/2026-08-01-observation-assignment.md",
        "docs/preregistration/PREREGISTRATION.md",
        "tests/gen/test_ladder_pin.py",
        "tests/test_reliability_sweep_pin.py",
        "scripts/gate_a.py",
        "scripts/measure_ladder.py",
        "scripts/measure_reliability_sweep.py",
    }
    assert required <= set(FROZEN_PATHS), (
        f"not frozen: {sorted(required - set(FROZEN_PATHS))}"
    )


def test_no_preregistered_number_is_quoted_from_a_ledger():
    """The standing rule from the ledger-reconciliation spec, enforced.

    Roughly a dozen ledgers under .superpowers/sdd/ carry the superseded
    reliability figure and they OUTNUMBER the correct one in a grep, so a
    good-faith author searching for the number finds the wrong one first.
    """
    text = (REPO / "docs" / "preregistration" / "PREREGISTRATION.md").read_text(
        encoding="utf-8"
    )
    for superseded in ("0.9982", "tested=11", "tested = 11", "0.9518", "478/609"):
        if superseded in text:
            assert "superseded" in text.lower().split(superseded)[0][-400:], (
                f"{superseded!r} appears without being labelled superseded within "
                f"the preceding 400 characters. It is a SUPERSEDED value [LR section 1]; "
                f"it may be shown only as superseded text, never as a live figure."
            )
    assert ".superpowers/sdd/" not in text, (
        "the pre-registration cites an SDD ledger. Quote the SPEC, never a "
        "ledger -- standing rule, ledger-reconciliation spec section 0."
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_freeze_manifest.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.verify_freeze'`.

- [ ] **Step 3: Write the verifier**

Create `scripts/verify_freeze.py`:

```python
#!/usr/bin/env python
"""Verify that nothing frozen by the pre-registration has moved.

WHY THIS EXISTS. The pre-registration's whole value is that a third party can
check it was not edited to fit the result. A prose list of "what is frozen"
cannot establish that. This recomputes a SHA-256 per frozen path and diffs it
against docs/preregistration/FREEZE-MANIFEST.md.

A discrepancy is not automatically an error -- it may be a legitimate change
that belongs in the deviations table (PREREGISTRATION.md section 11). What it may
never be is unnoticed.

Usage: python scripts/verify_freeze.py
Exit: 0 clean, 1 discrepancies found.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = "docs/preregistration/FREEZE-MANIFEST.md"

# Everything the published pre-registration quotes, cites, or derives a number
# from. MANIFEST itself is deliberately absent: a manifest that hashed itself
# could never verify clean.
FROZEN_PATHS: tuple[str, ...] = (
    "docs/preregistration/PREREGISTRATION.md",
    "docs/preregistration/P1-5-RULING.md",
    "docs/preregistration/PRECONDITIONS.md",
    "docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md",
    "docs/superpowers/specs/2026-08-01-ledger-reconciliation.md",
    "docs/superpowers/specs/2026-08-01-observation-assignment.md",
    "docs/superpowers/specs/2026-08-01-suite-integrity-design.md",
    "scripts/gate_a.py",
    "scripts/measure_ladder.py",
    "scripts/measure_reliability_sweep.py",
    "src/tolcad/y14_5.py",
    "src/tolcad/iso286.py",
    "src/tolcad/montecarlo.py",
    "src/tolcad/reliability.py",
    "src/tolcad/checker.py",
    "src/tolcad/types.py",
    "src/tolcad/gen/sampler.py",
    "src/tolcad/gen/features.py",
    "src/tolcad/gen/layout.py",
    "src/tolcad/gen/spec.py",
    # build/export do not enter the corpus digest (which hashes spec JSON), but
    # they produce the STEP AP242 + sidecar the pre-registration describes as
    # the corpus artifact. Frozen so "the corpus" means one thing.
    "src/tolcad/gen/build.py",
    "src/tolcad/gen/export.py",
    "tests/gen/test_ladder_pin.py",
    "tests/test_reliability_sweep_pin.py",
    "tests/mutation_registry.py",
    "pyproject.toml",
)

_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|", re.MULTILINE)


def digest_of(path: str) -> str:
    """SHA-256 of the file's bytes. Bytes, not text: a line-ending change is a
    change, and this project has already been bitten by CRLF normalisation."""
    return hashlib.sha256((REPO / path).read_bytes()).hexdigest()


def manifest_rows() -> list[tuple[str, str]]:
    """Parse (path, digest) rows out of the manifest's markdown table."""
    text = (REPO / MANIFEST).read_text(encoding="utf-8")
    return _ROW.findall(text)


def check_manifest() -> list[str]:
    """Return a list of discrepancies. Empty means the tree matches the freeze."""
    recorded = dict(manifest_rows())
    problems: list[str] = []

    for path in FROZEN_PATHS:
        if path not in recorded:
            problems.append(f"NOT IN MANIFEST: {path}")
            continue
        if not (REPO / path).is_file():
            problems.append(f"FROZEN PATH MISSING FROM TREE: {path}")
            continue
        actual = digest_of(path)
        if actual != recorded[path]:
            problems.append(
                f"CHANGED SINCE FREEZE: {path}\n"
                f"    manifest {recorded[path]}\n"
                f"    tree     {actual}"
            )

    for path in recorded:
        if path not in FROZEN_PATHS:
            problems.append(f"IN MANIFEST BUT NOT FROZEN_PATHS: {path}")

    return problems


def main() -> int:
    problems = check_manifest()
    if not problems:
        print(f"Freeze verified: {len(FROZEN_PATHS)} paths match the manifest.")
        return 0
    print("FREEZE DISCREPANCIES\n")
    for p in problems:
        print(f"  {p}")
    print(
        "\nEach line above is either a deviation belonging in "
        "PREREGISTRATION.md section 11, or an accident. It may not be neither."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Generate the manifest**

Create `docs/preregistration/FREEZE-MANIFEST.md`. Generate the table body rather than typing it:

```bash
python -c "
import sys; sys.path.insert(0,'.')
from scripts.verify_freeze import FROZEN_PATHS, digest_of
for p in FROZEN_PATHS:
    print(f'| \`{p}\` | \`{digest_of(p)}\` |')
"
```

Wrap that output in a document containing, in this order:

1. **The freeze commit SHA** and the exact command to reproduce it: `git rev-parse HEAD`.
2. **The scalar values frozen, each with its executable pin's node ID** — the four ladder counts and the corpus digest (`tests/gen/test_ladder_pin.py::test_each_ladder_level_matches_its_exact_pinned_counts`, `::test_the_corpus_digest_is_reproducible`); the reliability mean / CI / fraction / tested / excluded (`tests/test_gate_a.py::test_reliability_tested_and_excluded_are_pinned_exactly` and `::test_gate_a_reliability_criterion_holds_for_the_real_measurement`); the five k-sweep rows (`tests/test_reliability_sweep_pin.py`); the numpy pin.
3. **The file table** from the command above, headed `| Path | SHA-256 |`.
4. **How to verify**, quoted so a third party can run it without reading this plan:

```bash
git clone https://github.com/harshD42/TolAEG-CAD.git && cd TolAEG-CAD
git checkout <FREEZE_SHA>
pip install -e ".[dev,gen]"
python scripts/verify_freeze.py      # expect: Freeze verified
python scripts/measure_ladder.py     # expect the four counts and the digest
python scripts/measure_reliability_sweep.py
python -m pytest -q
```

5. **What is deliberately NOT frozen and why:** `docs/STATE-OF-PLAY.md` (a living index), `.superpowers/**` (contemporaneous ledgers, narrative only), `papers/literature/*.pdf` (untracked, reproducible via the fetcher), and `FREEZE-MANIFEST.md` itself.

- [ ] **Step 5: Run the tests**

Run: `python -m pytest tests/test_freeze_manifest.py -v` — expected PASS, 6 tests. The `test_the_verifier_notices_a_changed_file` case is the load-bearing one: it dirties a frozen file, requires the verifier to notice, and restores it.

Then `python scripts/verify_freeze.py; echo $?` — expected `Freeze verified: 26 paths match the manifest.` and exit 0.

Then `python -m pytest -q`. Running total: 428 baseline, +23 (Task 2), +2 (Task 3), +3 (Task 4), +4 (Task 5), +6 here = **466**. Treat a mismatch as a signal to investigate, not as a failure in itself.

**If `test_no_preregistered_number_is_quoted_from_a_ledger` fails, do not weaken it.** Fix the pre-registration: the figure it caught is superseded and must be shown as superseded text or removed.

- [ ] **Step 6: Commit**

```bash
git add docs/preregistration/FREEZE-MANIFEST.md scripts/verify_freeze.py tests/test_freeze_manifest.py
git commit -m "feat: freeze manifest with an executable verifier and the no-ledger-quotes rule"
```

---

### Task 10: Pre-freeze adversarial review — N-11 checkpoint 1

**Files:**
- Create: `docs/preregistration/ADVERSARIAL-REVIEW-01.md`

**Interfaces:**
- Consumes: everything Tasks 1–9 produced
- Produces: findings, responses, and a reviewer's explicit sign-off or refusal

**This is a task, not a suggestion, and it is the highest-leverage item in the plan.** The evidence: **zero of the twelve historical "cannot fail" instances were found by the three-layer machinery; ten were found by an adversarial reader over a diff.** One pass of this control previously found a false statement inside a frozen document.

**Budget: 0.75–1 day of review, plus 0.25 day for the response.** They do not overlap with engineering time. This is N-11's first of three scheduled checkpoints (the others: before each published number enters a draft; before Gate D).

**The reviewer must not be whoever wrote Tasks 1–9.** A fresh subagent with no plan context, or a human. Give them the diff and the charge sheet — not this plan's reasoning, which is the thing under test.

- [ ] **Step 1: Prepare the review package**

```bash
git diff <FREEZE_BASE_SHA>..HEAD > /tmp/prereg.diff
wc -l /tmp/prereg.diff
```

Package: the diff, `docs/preregistration/PREREGISTRATION.md`, `FREEZE-MANIFEST.md`, `P1-5-RULING.md`, and the three amended specs.

- [ ] **Step 2: Issue the charge sheet**

Record it verbatim in `ADVERSARIAL-REVIEW-01.md`, then hand it over. The reviewer answers each in writing:

1. **Find a number in `PREREGISTRATION.md` that no committed artifact reproduces.** For each figure, name the file and node ID that pins it, or flag it.
2. **Find a number quoted from a ledger rather than a spec.** Roughly a dozen ledgers carry the superseded `0.9982 / tested=11`; they outnumber the correct value in a grep, so a good-faith author finds the wrong one first.
3. **Attack each of the three amendments as post-hoc.** For 2026-08-02h, 02i and C1 in turn: is it genuinely correcting a falsehood or recording a settled decision, or is it a threshold being made easier to meet? **Amendment 02i is the one to attack hardest** — it stops a criterion from blocking.
4. **Attack the P1.5 ruling.** The strongest counter-argument is that the pre-registration implicitly claims a well-tested checker and the mutation instrument may be broken. Is condition C1 sufficient, or is it a disclosure standing in for a measurement?
5. **Find a claim in §10 Limitations that is softer than the evidence warrants** — a hedge where the honest word is stronger.
6. **Find a test in this diff that cannot fail.** Specifically probe: `test_the_verifier_notices_a_changed_file`, `test_every_sweep_row_tests_all_twelve_mates`, and the four new `test_observation_assignment.py` tests. For each, name the change that should make it fail and check that it does.
7. **Check the freeze manifest for something that should be frozen and is not.** Anything the pre-registration quotes and the manifest omits can move silently.
8. **Check Gate C's arithmetic against the baseline audit.** If the audit found exactly 8, `≥6 of ≥8` has zero slack: one baseline breaking during Phase 4 makes Gate C unmeetable, unrecoverably.
9. **Name anything in the pre-registration that a Phase 4 result could tempt someone to reinterpret.** Ambiguity in a frozen document is a degree of freedom.
10. **Is anything frozen here that should have stayed open?** Over-freezing is a real failure mode: it converts ordinary engineering into deviations-table entries and creates pressure to route around the register.

- [ ] **Step 3: Record findings and respond**

For each finding: **ACCEPT** (with the commit that fixes it), **REJECT** (with the technical reason — do not perform agreement with a finding you can show is wrong), or **DEFER** (with where it is now tracked). Use the `superpowers:receiving-code-review` skill; verify each finding against the real files before implementing it.

- [ ] **Step 4: Re-run everything the response touched**

Run: `python -m pytest -q`, `python scripts/verify_freeze.py`, `python scripts/gate_a.py`, `python scripts/measure_reliability_sweep.py`.

**If any accepted finding changed a frozen file, regenerate the manifest (Task 9 Step 4) and re-run `tests/test_freeze_manifest.py`.** The manifest predates the fixes; shipping a stale manifest at the freeze would be the freeze's own first violation.

- [ ] **Step 5: Get an explicit verdict**

`ADVERSARIAL-REVIEW-01.md` ends with one line: `REVIEWER VERDICT: CLEAR TO FREEZE` or `REVIEWER VERDICT: NOT CLEAR — <reason>`. Anything else — silence, "looks good", a list with no verdict — counts as NOT CLEAR.

- [ ] **Step 6: Commit**

```bash
git add docs/preregistration/ADVERSARIAL-REVIEW-01.md
git commit -m "docs: N-11 checkpoint 1 -- pre-freeze adversarial review, findings and responses"
```

---

### Task 11: Publish with an immutable public timestamp

**Files:**
- Create: `docs/preregistration/PUBLICATION-RECEIPT.md`
- Modify: `docs/preregistration/PREREGISTRATION.md` (fill the registration date and freeze SHA in the header)

**Interfaces:**
- Consumes: Task 9's manifest, Task 10's verdict
- Produces: DOIs, URLs and timestamps that a third party can check without our cooperation

Design spec §7 Gate D requires *"Pre-registration — Public timestamp (OSF/AsPredicted) **before** data generation, + deviations table"*, and §12 adds that *"a pre-registration timestamped after data generation is worthless, and reviewers punish unverifiable pre-registration claims harder than no claim at all."*

**Do not start this task until Task 10's verdict line reads CLEAR TO FREEZE.**

- [ ] **Step 1: SPIKE — confirm the registry's immutability property before committing to it**

**Spike. Time box: 0.5 day.** Cross-reference `docs/SPIKES.md`, spike *"Pre-registration immutability venue"*.

Confirm, from the provider's own documentation rather than from memory: (a) that OSF Registries' Open-Ended Registration accepts an attached document and mints a DOI; (b) what happens on withdrawal — whether a tombstone with the original timestamp survives, or the record disappears; (c) whether the registration timestamp is visible to a third party without an account. **UNVERIFIED at time of writing.**

Fallback if OSF does not provide a public, non-editable timestamp: Zenodo alone (Step 2's option B), which mints a DOI over an immutable archived snapshot and is sufficient for Gate D's "public timestamp" on its own. Do not let this spike block the freeze past its time box.

- [ ] **Step 2: Record the options and the recommendation**

Write this analysis into `PUBLICATION-RECEIPT.md` before acting on it:

| Option | Immutability | Verdict |
|---|---|---|
| **OSF Registries** (Open-Ended Registration) | Registration is not editable after submission; withdrawal leaves a tombstone with the original timestamp; DOI minted | **PRIMARY.** Gate D names OSF explicitly; it is the artifact reviewers recognise as a pre-registration |
| **Zenodo**, via a GitHub release | Archives an immutable tarball of the repo at a tag and mints a DOI over *that snapshot*; the archive is independent of GitHub | **SECONDARY, and required.** This is what anchors the freeze manifest's hashes to a copy we cannot alter |
| **arXiv** | v1 is permanently retrievable; versions are additive | **LATER, at Gate D.** A preprint venue, not a registry. Registering the study design here would be a category error |
| **AsPredicted** | Timestamped PDF, 9 fixed questions | **REJECTED.** The template is built for simple experimental designs and cannot carry the gate tables, the correction log or the limitations section |
| **Signed git tag** | **NOT IMMUTABLE.** A tag is a mutable ref: `git push --force origin refs/tags/<name>` re-points it, the old object becomes unreachable and is eventually garbage-collected. A GPG signature proves *who* made an object, not that the ref still points at it | **NAVIGATION ONLY.** Create one, and state in the receipt that it is a convenience pointer and carries no immutability guarantee |

**Recommendation: OSF Registries as the canonical pre-registration, Zenodo as the immutable repository snapshot, a signed tag as a pointer that is explicitly not relied upon.** The reason for two DOIs rather than one: OSF timestamps the *claims*, Zenodo timestamps the *code and hashes those claims are checked against*. A reviewer who doubts the pre-registration needs both, and needs them to be independent of us and of each other.

- [ ] **Step 3: Freeze, tag, and publish**

```bash
python -m pytest -q
python scripts/verify_freeze.py            # must print "Freeze verified"
git rev-parse HEAD                          # this is FREEZE_SHA
```

Fill `FREEZE_SHA` and the date into `PREREGISTRATION.md`'s header and into `FREEZE-MANIFEST.md`, regenerate the manifest table (Task 9 Step 4 — editing the header changed the file's hash), re-run `python scripts/verify_freeze.py`, and commit.

Then:

```bash
git tag -s preregistration-2026-08-02 -m "Phase 3.5 pre-registration freeze"
git push origin main --follow-tags
```

Then, **as human actions** — these involve creating accounts, accepting terms and publishing public content, and must be performed by Harsh, not by an agent:

1. Cut a GitHub release at `preregistration-2026-08-02`, with Zenodo integration enabled, and record the Zenodo DOI.
2. Create the OSF Open-Ended Registration, attach `PREREGISTRATION.md` (or its PDF render) plus `FREEZE-MANIFEST.md`, and record the OSF DOI and registration timestamp.

- [ ] **Step 4: Write the receipt**

`PUBLICATION-RECEIPT.md` records: the OSF DOI, URL and registration timestamp; the Zenodo DOI and archive URL; the freeze commit SHA; the signed tag name and its object SHA; the SHA-256 of `PREREGISTRATION.md` as published; and the options analysis from Step 2.

Add a closing paragraph stating the honest ceiling, in the same spirit as §10.3: **the OSF timestamp establishes when the document was registered, not that no corpus existed at that moment.** The evidence for the latter is that no corpus artifact appears anywhere in the repository history before `FREEZE_SHA` — checkable by a third party via `git log`, but a self-report in the same sense the fresh-clone receipt is. State it rather than let a reviewer find it.

- [ ] **Step 5: Update the state of play and hand off to P1.5**

Update `docs/STATE-OF-PLAY.md` §6: item 6 (Phase 3.5) is done, with the DOIs; item 2 (P1.5) is now the immediate next action per the P1.5 ruling's condition C3, before any corpus generation.

- [ ] **Step 6: Commit**

```bash
git add docs/preregistration/PUBLICATION-RECEIPT.md docs/preregistration/PREREGISTRATION.md docs/preregistration/FREEZE-MANIFEST.md docs/STATE-OF-PLAY.md
git commit -m "docs: pre-registration published -- OSF and Zenodo DOIs, freeze receipt"
git push origin main
```

---

## Plan completion state

At the end of Task 11:

- The freeze happened only because a gate confirmed it would be valid, and that gate had the authority to stop the plan
- The B7 headroom bound is re-measured on the repaired instrument, reproducible from a committed script, pinned two-sided on exact integer counts — and the exclusion-band trap that would have made the sweep unfalsifiable is guarded, having been observed producing 1.0000 at every k≥2
- Three numbered pre-data amendments record decisions that were already made, each showing its superseded text; no threshold was lowered and no criterion deleted
- The frozen documents no longer contradict themselves about the instance count, the environment, TolAnalyst, or what the NIST oracle can decide
- P1.5's status is ruled, argued, and conditioned rather than left ambiguous
- The pre-registration publishes the hypotheses, metrics, exact gate criteria, analysis plan, seeds, corpus recipe and digest, baselines and limitations — with the corrections shown rather than the tables verbatim
- The limitations section states the survey result, the oracle-independence ceiling, the self-report ceiling, the narrow geometry with AutoMate named as the planned generalisation, and that the anti-vacuity machinery has never discovered an instance
- A manifest plus an executable verifier lets a third party confirm nothing moved, and a test enforces that no published number was quoted from a ledger
- An adversarial reader who did not write it has issued an explicit verdict
- The timestamp is public and rests on two independent DOIs, with the git tag explicitly labelled as *not* an immutability mechanism

## Deliberately NOT done here

- **Generating the research corpus.** Design spec §12. Task 11 is the last thing before it.
- **P1.5.** Ruled non-blocking with conditions (Task 6); scheduled immediately after Task 11.
- **Fixing the Monte Carlo seed reuse across difficulty levels.** Disclosed in §10.7 instead: changing `_mc_seed_for` would move the frozen corpus digest and the four frozen ladder counts.
- **Re-pinning the Layer 2 mutation score.** [LR §1] says DO NOT RE-PIN until P1.5 produces an enumeration.
- **`README` and `LICENSE`.** Both absent from a public repository. Not on the pre-registration's critical path, but a reviewer following the OSF link will land on a repo with no licence, which undercuts the "open tool" contribution. Raise it with the human at Task 11.
- **The stale `why` text in `tests/mutation_registry.py`'s `reliability-perturbation-tripled` entry**, which still cites the pre-repair `0.9982 → 0.9068` and `2x measures 0.9518 and is NOT caught`. Task 2 supersedes those numbers. The entry's *mechanism* is correct and its guard still fires, so this is documentation drift inside a critical guard — worth fixing, but not by this plan, which must not touch `tests/mutation_registry.py` while the registry is being frozen.

## Estimate

| Task | Days |
|---|---|
| 1 Precondition gate | 0.5 |
| 2 k-sweep re-measure and pin | 0.5 |
| 3 Amendment 02h (NIST) — includes a 0.5-day spike | 1.0 |
| 4 Amendment 02i (TolAnalyst) | 0.5 |
| 5 Amendment C1 (suite integrity) | 0.5 |
| 6 P1.5 ruling | 0.25 |
| 7 Pre-registration body | 1.5 |
| 8 Limitations | 0.75 |
| 9 Freeze manifest and verifier | 0.75 |
| 10 Adversarial review (1.0 review + 0.25 response) | 1.25 |
| 11 Publish — includes a 0.5-day spike | 0.75 |
| **Total** | **8.25** |

Excludes the baseline runnability audit (~1 day, owned by `docs/superpowers/plans/2026-08-02-baseline-containerization.md`) and P1.5 (1.5 serialised days, after Task 11).

## Self-review notes

**Spec coverage.** Design spec §7's Gate A/B/C/D tables → Task 7 Steps 3–4. §8's statistical protocol → Task 7 Step 3. §12's ordering → Global Constraints and Task 11. §7's "Also note for §8" free-parameter declaration → Task 7 Step 4. §6's baselines → Task 1 Step 2 and Task 7 Step 5. Gate D's pre-registration row → Task 11.

**Verification status of every non-obvious claim in this plan.** Executed at `30eb333` on 2026-08-02: the Gate A report and tally; 428 tests collected; the k-sweep table at all five multipliers *and* the naive-epsilon failure mode (`tested` 12→6, mean 1.0000); the exact integer stability counts over a 2400 denominator; the 479/191/148 Monte Carlo seed figures and the 10006–10791 range; `scripts/` importability under `pythonpath = ["src", "."]` with no `__init__.py`; the absence of `README`/`LICENSE`/tags; the `origin` remote; 101 tracked SDD files; 15 registry entries. The full text of `scripts/measure_reliability_sweep.py` in Task 2 Step 3 was run as written and produced Step 4's table.

**Marked UNVERIFIED, with what would confirm each:** NIST's published per-file PMI annotation counts (Task 3's spike — confirm by locating a NIST-published table and reconciling it against the two counts we have by execution); OSF's withdrawal/tombstone behaviour and whether its registration timestamp is third-party visible without an account (Task 11's spike — confirm from OSF's own documentation). `docs/SPIKES.md`, the baseline-containerization plan and the P1.5 plan were UNVERIFIED when drafting began and are now **verified present** in the working tree, uncommitted.

**Projections, not measurements.** The post-task test totals (451 → 453 → 456 → 460 → 466) are arithmetic over the tests this plan adds. A mismatch is a signal to investigate, not a failure.

**Type consistency.** `classify` and `measure_sweep` are used in `tests/test_reliability_sweep_pin.py` with the signatures `scripts/measure_reliability_sweep.py` defines. `is_blocking`, `SUPPLEMENTARY` and `_KINDS` are used in `tests/test_gate_a.py` with the signatures Task 4 Step 4 adds. `FROZEN_PATHS`, `MANIFEST`, `check_manifest`, `digest_of` and `manifest_rows` are used in `tests/test_freeze_manifest.py` with the signatures `scripts/verify_freeze.py` defines. `_row(prefix, out)` and `_run_gate_a_stdout()` are the two-argument and zero-argument helpers that already exist in `tests/test_gate_a.py` — verified against the file, not against the earlier close-out plan, whose snippets show a one-argument `_row`.
