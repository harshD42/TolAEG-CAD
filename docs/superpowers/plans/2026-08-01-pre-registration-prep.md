# Pre-Registration Prep Implementation Plan (Phase 3.5a)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the four benchmark-integrity gaps that Phase 3's final review left open, so that Phase 3.5's public pre-registration freezes a corpus definition that is defensible.

**Architecture:** Five independent, small changes to the existing generator. Nothing new is designed: the fastener feature library gains a tapped-hole table, `MateSpec` gains one field, the sampled fit set loses one entry, one NIST file becomes a committed test fixture, and two self-referential test assertions get teeth. The checker core is not touched at all — every change is in `tolcad.gen`, `validation/`, or tests.

**Tech Stack:** Python 3.13, CadQuery 2.8.0, OCP (OCCT 7.x bindings), numpy, pytest 9.0.2.

## Why this plan exists

Phase 3 merged to `master` at `2c8a8f0` with all nine tasks complete and its final whole-branch review clean. Four issues were deliberately deferred by the human at that review, on the grounds that they shape what pre-registration freezes and therefore must land *before* Phase 3.5, not after:

- **I4** — fixed and floating fasteners produce *identical* STEP geometry, so the distinction is unlearnable from the reference geometry even though the two use different Y14.5 formulas. Separately, `src/tolcad/y14_5.py:80-81` names a projected tolerance zone as a load-bearing precondition that the generator does not emit, making every fixed-fastener verdict optimistic by the core module's own contract.
- **H7/h6** — line-to-line at MMC, so its label turned on one Monte Carlo draw in 100,000 (85 True / 23 False across the corpus).
- **I2** — ISO-fit verdicts are predictable from the shaft letter.
- **I5** — on a fresh clone the oracle read path is only ever asserted to return zeros.

## Decisions already made by the human — do not re-litigate

1. **Drop line-to-line fits from the sampled set.** A fit whose ground truth turns on one sample in 100k is noise, not a test item.
2. **Always emit projected zones and record the field.** Stay inside the already-verified ASME Y14.5 Appendix B-4 mathematics. **Do NOT implement B-5.** Adding new closed-form standards code to `y14_5.py` is out of scope for this plan.
3. **Tier 2 contributes the clearance *yield*; Tier 1 carries the boolean.** I2 is structural, not a sampling artifact — see the finding below. It gets *documented and pinned*, not "fixed".

### The I2 finding, stated precisely, because Task 1 pins it as a test

`tolcad/montecarlo.py:57` defines `assembles = yield_frac >= 1.0`, i.e. zero interference anywhere in the tolerance range. For a hole-basis fit that means `hole_min > shaft_max`. With `hole_min = nominal` (H holes have zero lower deviation) and `shaft_max = nominal + es`, the verdict is True exactly when the shaft's upper deviation `es <= 0` — which *is* the definition of a clearance-class shaft letter (a–h) as against transition/interference (j–zc).

So the ISO-fit boolean is determined by the shaft letter as a matter of arithmetic, at every diameter. This was confirmed empirically over nominals 3–180 mm: `g6` True everywhere, `k6`/`p6` False everywhere. **Varying the nominal cannot flip it.** The continuous yield does vary usefully (`k6` spans 0.661 at 6 mm to 0.848 at 3 mm), which is why Tier 2's contribution is the yield.

---

## Global Constraints

- **All dimensions in millimetres, stored as `float`.** ISO 286 publishes micrometres; conversion happens only at the table boundary in `iso286.py` and nowhere else.
- **The checker core must stay CAD-free.** `types`, `y14_5`, `iso286`, `montecarlo`, `checker`, `reliability` must not import CadQuery, OCP, or `tolcad.gen`. `tests/test_architecture.py` enforces this; do not weaken it.
- **`validation/` is one-directional.** It may import core; core may never import it.
- **`spec.py`, `features.py`, `sampler.py` and `layout.py` must remain CAD-free.**
- **Tier 1 is exact.** `EPS = 1e-9`, no rounding.
- **Tier 2 is statistical and must always report a seed.**
- **Pre-registered Gate A/B/C/D thresholds in design spec §7 are FROZEN.** Do not touch them or `scripts/gate_a.py`.
- **Do NOT generate a research corpus.** Spec §12 puts pre-registration first. Measurement sweeps that write nothing are fine; committed test batches stay small.
- **Do NOT modify `src/tolcad/y14_5.py`.** Its B-4 mathematics is verified against the primary standard. This plan satisfies its precondition; it does not change its formulas.
- **Every headline path runs with no SolidWorks licence.**

## File structure

| File | Change | Responsibility |
|---|---|---|
| `src/tolcad/gen/features.py` | Modify | Drop `H7/h6`; add the tapping-drill table and `tapped_hole_for` |
| `src/tolcad/gen/spec.py` | Modify | Add `projected_zone_mm` and its validation |
| `src/tolcad/gen/sampler.py` | Modify | Tapped `hole_b` for fixed fasteners; set the projected zone |
| `tests/gen/test_features.py` | Modify | Pin the fit set, the tapping table, and the I2 structural fact |
| `tests/gen/test_spec.py` | Modify | Projected-zone validation and round-trip |
| `tests/gen/test_sampler.py` | Modify | Fixed mates carry a tapped `hole_b` and a projected zone |
| `tests/gen/test_layout.py` | Modify | Give the margin-constant assertions teeth |
| `tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp` | Create | Committed AP242 fixture, 396 KB |
| `tests/fixtures/NIST-PROVENANCE.md` | Create | Where the fixture came from and under what terms |
| `tests/test_ap242_pmi.py` | Modify | Positive control that runs on a fresh clone |

`build.py` needs **no change**: it already reads `mate.hole_b["nominal"]`, so a tapped diameter flows through automatically. `layout.py` needs no change: `feature_radii_mm` already takes the larger of the two holes.

---

### Task 1: Drop line-to-line fits, and pin the Tier 2 structural fact

**Files:**
- Modify: `src/tolcad/gen/features.py`
- Test: `tests/gen/test_features.py`

**Interfaces:**
- Consumes: `tolcad.iso286.fit_from_designation`, `tolcad.checker.check`
- Produces: `SUPPORTED_FITS: tuple[str, ...]` reduced to `("H7/g6", "H7/k6", "H7/p6")`

`H7/h6` is line-to-line: hole minimum and shaft maximum are both exactly the nominal, so exact worst-case clearance is zero and the Monte Carlo verdict turns on whether any of 100,000 draws lands on the boundary. Measured across the corpus it came out 85 True / 23 False with margins of only 1.0 or 0.99999 — one clearance failure in 100k. That is a coin toss wearing a ground-truth label.

This task also adds two tests that *document* the I2 structural fact rather than trying to defeat it, so that (a) the paper's disclosure is backed by an executable assertion, and (b) nobody later "fixes" the fit set by adding another letter and assumes the leak went away.

- [ ] **Step 1: Write the failing tests**

Append to `tests/gen/test_features.py`:

```python
def test_no_supported_fit_is_line_to_line():
    """A fit whose worst-case clearance is exactly zero has a coin-toss label.

    H7/h6 was in this set and came out 85 True / 23 False across the corpus,
    decided by whether any of 100k Monte Carlo draws landed on the boundary.
    Its margin was only ever 1.0 or 0.99999 -- one clearance failure in 100k.
    """
    from tolcad.iso286 import fit_from_designation

    for designation in SUPPORTED_FITS:
        hole, shaft = fit_from_designation(20.0, designation)
        assert hole.min_size != shaft.max_size, (
            f"{designation} is line-to-line at 20 mm (hole min == shaft max == "
            f"{hole.min_size}); its verdict is decided by sampling noise"
        )


def test_supported_fits_still_contain_both_verdict_classes():
    """Dropping a fit must not leave the ISO set all-passing or all-failing."""
    from tolcad.checker import check

    verdicts = {
        d: check({"type": "iso_fit", "nominal": 20.0, "designation": d,
                  "seed": 12345, "n": 100_000}).assembles
        for d in SUPPORTED_FITS
    }
    assert any(verdicts.values()), f"no clearance fit left: {verdicts}"
    assert not all(verdicts.values()), f"no interference fit left: {verdicts}"


def test_iso_fit_verdict_is_fixed_by_the_shaft_letter_at_every_size():
    """DOCUMENTS a structural property; this is a disclosure, not a bug.

    assembles is `yield >= 1.0`, i.e. zero interference anywhere in the
    tolerance range, which for a hole-basis fit means hole_min > shaft_max.
    Since hole_min == nominal and shaft_max == nominal + es, the verdict is
    True exactly when es <= 0 -- the definition of a clearance-class shaft
    letter. It therefore CANNOT vary with diameter, and no amount of nominal
    variation will make these labels harder to guess from the designation.
    Tier 2's contribution to the benchmark is the YIELD, not this boolean.
    """
    from tolcad.checker import check

    nominals = (6.0, 10.0, 20.0, 50.0, 120.0)
    for designation in SUPPORTED_FITS:
        seen = {
            check({"type": "iso_fit", "nominal": n, "designation": designation,
                   "seed": 999, "n": 100_000}).assembles
            for n in nominals
        }
        assert len(seen) == 1, (
            f"{designation} changed verdict across {nominals}: {seen}. If this "
            f"ever fails the structural argument above is wrong -- re-derive it "
            f"before relying on the disclosure."
        )


def test_iso_fit_yield_does_vary_with_size():
    """The continuous signal Tier 2 actually contributes, unlike the boolean.

    Guards against the yield collapsing to a constant, which would leave
    Tier 2 contributing nothing at all once the boolean is set aside.
    """
    from tolcad.checker import check

    yields = {
        n: check({"type": "iso_fit", "nominal": n, "designation": "H7/k6",
                  "seed": 999, "n": 100_000}).margin
        for n in (6.0, 20.0, 120.0)
    }
    assert len(set(yields.values())) > 1, (
        f"H7/k6 yield is constant across diameters: {yields}"
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/gen/test_features.py -v -k "line_to_line or verdict_classes or shaft_letter or yield_does_vary"`
Expected: `test_no_supported_fit_is_line_to_line` FAILS with a message naming `H7/h6` (hole min == shaft max == 20.0). The other three should PASS already — they document existing behaviour, so they are regression pins rather than red tests. If `test_iso_fit_verdict_is_fixed_by_the_shaft_letter_at_every_size` fails, STOP: the structural argument in this plan is wrong and the human must be told before anything else changes.

- [ ] **Step 3: Drop the fit**

In `src/tolcad/gen/features.py`, replace the `SUPPORTED_FITS` line and its context with:

```python
# Hole-basis fits the generator samples. One clearance (g6), one transition
# (k6), one interference (p6).
#
# H7/h6 WAS HERE AND WAS DELIBERATELY REMOVED. It is line-to-line: an H hole's
# lower deviation is zero and an h shaft's upper deviation is zero, so hole
# minimum and shaft maximum are both exactly the nominal and the exact
# worst-case clearance is 0. tolcad.montecarlo scores `assembles` as
# `yield >= 1.0` against a strict `clearance > 0`, so the label came down to
# whether any of 100,000 samples landed exactly on the boundary: 85 True /
# 23 False across the corpus, margin only ever 1.0 or 0.99999. That is
# sampling noise wearing a ground-truth label, and it would have surfaced as
# irreducible, unexplainable model-vs-checker disagreement. Removed before
# pre-registration rather than after.
SUPPORTED_FITS: tuple[str, ...] = ("H7/g6", "H7/k6", "H7/p6")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/gen/test_features.py -v`
Expected: PASS.

Then run the whole suite: `python -m pytest -q -m "not slow"`. It was **188 passed, 2 deselected** at `2c8a8f0`.

**A shift is expected here and must be checked, not assumed away.** `rng.choice(SUPPORTED_FITS)` now draws from three entries rather than four, so the sampled corpus changes. The two ladder guard tests in `tests/gen/test_sampler.py` assert the Tier 1 failure rate stays inside `0.10 <= d1 <= 0.30` and `0.60 <= d4 <= 0.80` and is strictly monotone. If either now fails, do NOT widen the bands. Re-measure and report the table:

```bash
python -c "
from tolcad.checker import check
from tolcad.gen.sampler import sample_assembly
for d in (1,2,3,4):
    f=t=0
    for s in range(200):
        for m in sample_assembly(s,d).mates:
            if m.kind=='iso_fit': continue
            t+=1
            if not check(m.to_check_dict()).assembles: f+=1
    print(f'd{d}: {f}/{t} = {100*f/t:.1f}% fail')
"
```

The reference table at `2c8a8f0` is d1 19.5%, d2 32.9%, d3 52.9%, d4 69.1%. Report the new one in your report either way.

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/gen/features.py tests/gen/test_features.py
git commit -m "fix: drop line-to-line H7/h6, whose label was sampling noise"
```

---

### Task 2: Fixed fasteners get a tapped hole, so the two kinds differ in geometry

**Files:**
- Modify: `src/tolcad/gen/features.py`
- Modify: `src/tolcad/gen/sampler.py`
- Test: `tests/gen/test_features.py`, `tests/gen/test_sampler.py`

**Interfaces:**
- Consumes: `FASTENER_SIZES`
- Produces: `TAPPING_DRILL_MM: dict[float, float]`; `tapped_hole_for(fastener_mm: float) -> dict` returning the same checker-ready hole dict shape as `clearance_hole_for`

Today the sampler gives `hole_a` and `hole_b` the *same* clearance diameter for both fastener kinds, and `build.py` drills both plates identically. Two assemblies with byte-identical STEP geometry can therefore carry different ground-truth verdicts, because floating scores `min(H_a - F - T_a, H_b - F - T_b)` while fixed scores `(H_a - F) - (T_a + T_b)`. A model cannot possibly learn that distinction from the reference geometry, which makes it an unfair benchmark item.

A real fixed-fastener joint has a *tapped* or press-fit feature in the second part — an M8 screw threads into a Ø6.8 tapping drill, not a Ø9.0 clearance hole. Modelling that makes the two kinds visibly different.

**This is compatible with the checker exactly as written, and was verified by execution.** `y14_5.fastener_assembles` checks `hole_a.mmc >= fastener.mmc` but deliberately does not check `hole_b` in the fixed case — its docstring says "hole_b is not a clearance hole in the fixed case, so its size is not checked here" — and `hole_b`'s MMC never enters the B-4 formula. A fixed mate with `hole_a` Ø9.0 and a tapped `hole_b` Ø6.8 against an M8 fastener returns `assembles=True, margin=0.2`. There is a bonus invariant: the *same* dict submitted as `floating_fastener` correctly raises `ValueError`, because a Ø6.8 hole cannot pass an Ø8 fastener. Task 2 pins that.

- [ ] **Step 1: Write the failing tests**

Append to `tests/gen/test_features.py`:

```python
def test_tapping_drill_is_tabulated_for_every_fastener_size():
    from tolcad.gen.features import TAPPING_DRILL_MM
    assert set(TAPPING_DRILL_MM) == set(FASTENER_SIZES)


@pytest.mark.parametrize("fastener_mm, expected", [
    (3.0, 2.5), (4.0, 3.3), (5.0, 4.2), (6.0, 5.0),
    (8.0, 6.8), (10.0, 8.5), (12.0, 10.2),
])
def test_tapped_hole_matches_the_coarse_pitch_series(fastener_mm, expected):
    from tolcad.gen.features import tapped_hole_for
    assert tapped_hole_for(fastener_mm)["nominal"] == pytest.approx(expected)


def test_tapped_hole_is_always_smaller_than_its_fastener():
    """This is what makes a fixed joint geometrically distinguishable.

    A tapped hole the fastener could pass through would be a clearance hole,
    and the two fastener kinds would look identical again.
    """
    from tolcad.gen.features import tapped_hole_for
    for f in FASTENER_SIZES:
        hole = tapped_hole_for(f)
        assert hole["nominal"] + hole["upper_dev"] < f, (
            f"M{f} tapped hole is not smaller than the fastener at LMC"
        )


def test_unknown_fastener_size_rejected_by_tapped_hole():
    from tolcad.gen.features import tapped_hole_for
    with pytest.raises(ValueError, match="fastener"):
        tapped_hole_for(7.0)
```

Append to `tests/gen/test_sampler.py`:

```python
def test_fixed_fasteners_get_a_tapped_hole_b_and_floating_ones_do_not():
    """Guards I4: identical geometry for two kinds with different formulas.

    Before this, hole_a and hole_b carried the same clearance diameter for
    both kinds, so the exported STEP could not express which formula applied.
    """
    seen_fixed = seen_floating = 0
    for seed in range(60):
        for difficulty in (1, 2, 3, 4):
            for mate in sample_assembly(seed, difficulty).mates:
                if mate.kind == "fixed_fastener":
                    seen_fixed += 1
                    assert mate.hole_b["nominal"] < mate.nominal_mm, (
                        "a fixed fastener's hole_b must be tapped, i.e. smaller "
                        "than the fastener"
                    )
                elif mate.kind == "floating_fastener":
                    seen_floating += 1
                    assert mate.hole_b["nominal"] > mate.nominal_mm, (
                        "a floating fastener's hole_b must be a clearance hole"
                    )
    assert seen_fixed > 0 and seen_floating > 0, "corpus lacks one of the kinds"


def test_a_fixed_mate_is_structurally_not_a_floating_mate():
    """The geometry itself now encodes which formula applies.

    A tapped hole_b cannot pass the fastener, so submitting a fixed mate as
    floating raises. That is the invariant making the two kinds learnable.
    """
    fixed = next(
        m for seed in range(60)
        for m in sample_assembly(seed, 4).mates
        if m.kind == "fixed_fastener"
    )
    as_floating = dict(fixed.to_check_dict(), type="floating_fastener")
    with pytest.raises(ValueError, match="hole_b MMC"):
        check(as_floating)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/gen/test_features.py tests/gen/test_sampler.py -v -k "tapp or fixed_fasteners_get or structurally"`
Expected: FAIL — `ImportError` / `cannot import name 'TAPPING_DRILL_MM'` for the features tests, and assertion failures for the sampler tests (today `hole_b["nominal"]` is the clearance diameter, which is larger than the fastener for both kinds).

- [ ] **Step 3: Add the tapping table and the sampler change**

In `src/tolcad/gen/features.py`, after `_CLEARANCE_HOLE_MM` and its `_GRADE_INDEX`, add:

```python
# Tapping drill diameter for a coarse-pitch metric thread, mm. A screw threading
# into one of these does NOT pass through it -- that is exactly what makes a
# fixed-fastener joint geometrically distinct from a floating one, where the
# fastener clears both parts.
#
# Same provenance caveat as _CLEARANCE_HOLE_MM above: these match the common
# coarse-pitch tapping-drill series (nominal minus pitch) as reproduced in
# general engineering references, but have NOT been checked against the primary
# standard, so no edition is cited. They affect realism, not correctness: the
# checker's B-4 verdict never reads hole_b's size in the fixed case.
TAPPING_DRILL_MM: dict[float, float] = {
    3.0: 2.5,
    4.0: 3.3,
    5.0: 4.2,
    6.0: 5.0,
    8.0: 6.8,
    10.0: 8.5,
    12.0: 10.2,
}
```

and after `clearance_hole_for`, add:

```python
def tapped_hole_for(fastener_mm: float) -> dict:
    """Return a checker-ready hole dict for the tapped feature of a fixed joint.

    The fastener threads into this hole rather than passing through it, so the
    diameter is deliberately BELOW the fastener's. y14_5.fastener_assembles does
    not check hole_b's size in the fixed case -- its docstring is explicit that
    hole_b is not a clearance hole there and its MMC never enters the B-4
    formula -- so a sub-fastener diameter here is correct, not a violation.
    """
    if fastener_mm not in TAPPING_DRILL_MM:
        raise ValueError(
            f"fastener size {fastener_mm} not tabulated; have {FASTENER_SIZES}"
        )
    return {
        "nominal": TAPPING_DRILL_MM[fastener_mm],
        "lower_dev": 0.0,
        "upper_dev": _HOLE_UPPER_DEV_MM,
        "position_tol": 0.0,
    }
```

In `src/tolcad/gen/sampler.py`, change the import line to add `tapped_hole_for`:

```python
from tolcad.gen.features import (
    FASTENER_SIZES, SUPPORTED_FITS, clearance_hole_for, iso_fit_mate_features,
    tapped_hole_for,
)
```

and inside `_tier1_mate`, replace the two `hole_a=`/`hole_b=` arguments of the returned `MateSpec`. The body up to and including the `tol_a`/`tol_b` lines is unchanged; replace from `return MateSpec(` onward with:

```python
    # hole_a is always the clearance hole the fastener passes through. hole_b is
    # a second clearance hole for a floating joint, but a TAPPED hole for a fixed
    # one -- that difference is what lets the exported STEP express which Y14.5
    # formula applies. Without it the two kinds were byte-identical geometry
    # carrying different ground truth, which is unlearnable by construction.
    hole_b = hole if kind == "floating_fastener" else tapped_hole_for(fastener_mm)

    return MateSpec(
        kind=kind,
        nominal_mm=fastener_mm,
        hole_a=dict(hole, position_tol=tol_a),
        hole_b=dict(hole_b, position_tol=tol_b),
        fastener=fastener,
        designation=None,
        position_tol_a=tol_a,
        position_tol_b=tol_b,
    )
```

Note the allowable arithmetic above it is already correct and must not change: for the fixed case it uses `hole` (that is `hole_a`, the clearance hole) and halves it, which is B-4's `T = (H - F)/2`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/gen/test_features.py tests/gen/test_sampler.py -v`
Expected: PASS.

Then the full suite: `python -m pytest -q -m "not slow"`.

Two knock-on effects to confirm rather than assume:
1. `tests/gen/test_build.py`'s containment sweep computes expected removed volume from `mate.hole_b["nominal"]`, so it follows the smaller tapped diameter automatically. It must still pass for all 50 seeds at every difficulty.
2. `layout.feature_radii_mm` takes `max` of the two hole diameters, so plates get no smaller than the clearance hole requires. Confirm no plate-size assertion regresses.

Re-run the failure-rate table from Task 1 Step 4 and report it. Tier 1 verdicts should be **unchanged** by this task — `hole_b`'s size does not enter either formula — so a moved table means something is wrong; investigate before proceeding.

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/gen/features.py src/tolcad/gen/sampler.py tests/gen/test_features.py tests/gen/test_sampler.py
git commit -m "feat: fixed fasteners thread into a tapped hole, so the kinds differ in geometry"
```

---

### Task 3: Record the projected tolerance zone the B-4 verdict assumes

**Files:**
- Modify: `src/tolcad/gen/spec.py`
- Modify: `src/tolcad/gen/sampler.py`
- Test: `tests/gen/test_spec.py`, `tests/gen/test_sampler.py`

**Interfaces:**
- Consumes: nothing new
- Produces: `MateSpec.projected_zone_mm: float | None = None`, serialised in the sidecar

`src/tolcad/y14_5.py:80-81` states, as a load-bearing precondition rather than a footnote: *"This module implements B-4 only, so applying it to a drawing without a projected tolerance zone is OPTIMISTIC (unsafe); the generator must emit projected zones."* This generator is that generator, and it currently emits nothing of the kind. Every fixed-fastener verdict in the corpus is therefore optimistic by the core module's own contract.

The fix is to make the assumption explicit in the schema. The projection distance `P` is physically the thickness of the part the fastener passes through before entering the tapped feature — that is `plate_thickness_mm`.

**The checker does not consume this field, and `to_check_dict()` must not emit it.** B-4's formula has no `P` term; `P` appears only in B-5, which this plan explicitly does not implement. The field's job is to state in the published schema the condition under which the recorded verdict is valid.

- [ ] **Step 1: Write the failing tests**

Append to `tests/gen/test_spec.py`:

```python
def test_fixed_fastener_requires_a_projected_zone():
    """y14_5.py names the projected zone a precondition of its B-4 formula.

    Without one, the recorded verdict is optimistic and the schema does not
    say so. Refusing to build such a mate is how that stays true.
    """
    with pytest.raises(ValueError, match="projected_zone_mm"):
        MateSpec(
            kind="fixed_fastener", nominal_mm=8.0,
            hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            hole_b={"nominal": 6.8, "lower_dev": 0.0, "upper_dev": 0.2},
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None, position_tol_a=0.2, position_tol_b=0.2,
        )


def test_projected_zone_must_be_positive():
    with pytest.raises(ValueError, match="projected_zone_mm"):
        MateSpec(
            kind="fixed_fastener", nominal_mm=8.0,
            hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            hole_b={"nominal": 6.8, "lower_dev": 0.0, "upper_dev": 0.2},
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None, position_tol_a=0.2, position_tol_b=0.2,
            projected_zone_mm=0.0,
        )


def test_non_fixed_kinds_must_not_carry_a_projected_zone():
    """B-3 (floating) has no projection term; carrying one would imply it does."""
    with pytest.raises(ValueError, match="projected_zone_mm"):
        MateSpec(
            kind="floating_fastener", nominal_mm=8.0,
            hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            hole_b={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None, position_tol_a=0.2, position_tol_b=0.2,
            projected_zone_mm=8.0,
        )


def test_projected_zone_is_not_sent_to_the_checker():
    """B-4 has no P term -- that is B-5, which tolcad does not implement.

    Emitting it would imply the checker consumes it, which it does not.
    """
    mate = MateSpec(
        kind="fixed_fastener", nominal_mm=8.0,
        hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
        hole_b={"nominal": 6.8, "lower_dev": 0.0, "upper_dev": 0.2},
        fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
        designation=None, position_tol_a=0.2, position_tol_b=0.2,
        projected_zone_mm=8.0,
    )
    assert "projected_zone_mm" not in mate.to_check_dict()
    assert check(mate.to_check_dict()).assembles is True
```

Append to `tests/gen/test_sampler.py`:

```python
def test_every_sampled_fixed_fastener_records_its_projected_zone():
    seen = 0
    for seed in range(60):
        for difficulty in (1, 2, 3, 4):
            spec = sample_assembly(seed, difficulty)
            for mate in spec.mates:
                if mate.kind != "fixed_fastener":
                    assert mate.projected_zone_mm is None
                    continue
                seen += 1
                assert mate.projected_zone_mm == pytest.approx(
                    spec.plate_thickness_mm
                ), "the projection is the thickness the fastener passes through"
    assert seen > 0, "no fixed fasteners sampled"


def test_projected_zone_survives_the_sidecar_round_trip():
    from tolcad.gen.spec import AssemblySpec
    spec = next(
        s for seed in range(60)
        for s in [sample_assembly(seed, 4)]
        if any(m.kind == "fixed_fastener" for m in s.mates)
    )
    assert AssemblySpec.from_json(spec.to_json()) == spec
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/gen/test_spec.py tests/gen/test_sampler.py -v -k "projected"`
Expected: FAIL — `TypeError: MateSpec.__init__() got an unexpected keyword argument 'projected_zone_mm'` for the tests that pass it, and the `pytest.raises` tests failing because no error is raised.

- [ ] **Step 3: Add the field, the validation, and the sampler wiring**

In `src/tolcad/gen/spec.py`, add the field immediately after `mc_n`:

```python
    # ASME Y14.5 Appendix B-4 -- the formula y14_5.fastener_assembles implements
    # for the fixed case -- is titled "...When Projected Tolerance Zone Is Used"
    # and assumes exactly that. y14_5.py states the precondition outright: apply
    # B-4 without a projected zone and the margin is OPTIMISTIC, i.e. unsafe.
    # B-5 covers the non-projected case with a (1 + 2P/D) multiplier on T2, and
    # tolcad does NOT implement it. Recording the projection here is how the
    # published schema states the condition its verdict is valid under.
    # The projection is the thickness of the part the fastener crosses before
    # reaching the tapped feature. Required and positive for fixed_fastener;
    # None for every other kind, since no other formula has a projection term.
    projected_zone_mm: float | None = None
```

In the same file, add to `__post_init__`, inside the `else:` branch that already handles `floating_fastener` / `fixed_fastener`, and add a guard for the other kinds. Replace the whole `__post_init__` validation body after the `mc_n` check with:

```python
        if self.kind not in VALID_KINDS:
            raise ValueError(
                f"unknown mate kind {self.kind!r}; have {sorted(VALID_KINDS)}"
            )
        if self.kind != "fixed_fastener" and self.projected_zone_mm is not None:
            raise ValueError(
                f"projected_zone_mm applies only to fixed_fastener (Y14.5 B-4); "
                f"{self.kind} carries no projection term, got "
                f"{self.projected_zone_mm}"
            )
        if self.kind == "iso_fit":
            if not self.designation:
                raise ValueError("iso_fit mate requires a designation such as 'H7/g6'")
        elif self.kind == "virtual_condition":
            if self.fastener is None:
                raise ValueError("virtual_condition mate requires a fastener")
            if self.hole_a is None:
                raise ValueError("virtual_condition mate requires hole_a")
        else:  # floating_fastener or fixed_fastener
            if self.fastener is None:
                raise ValueError(f"{self.kind} mate requires a fastener")
            if self.hole_a is None:
                raise ValueError(f"{self.kind} mate requires hole_a")
            if self.hole_b is None:
                raise ValueError(f"{self.kind} mate requires hole_b")
            if self.kind == "fixed_fastener" and not (
                self.projected_zone_mm is not None and self.projected_zone_mm > 0.0
            ):
                raise ValueError(
                    "fixed_fastener requires a positive projected_zone_mm: "
                    "y14_5 implements ASME Y14.5 B-4, which assumes a projected "
                    "tolerance zone, and is optimistic without one. Got "
                    f"{self.projected_zone_mm}"
                )
```

In `src/tolcad/gen/sampler.py`, add a module constant next to `_MC_SAMPLES`:

```python
# The plate thickness the sampler builds to. Also the projection distance for a
# fixed fastener: the fastener crosses part_a's full thickness before it reaches
# the tapped feature in part_b. Kept as one constant so the recorded projected
# zone and the built geometry cannot drift apart.
_PLATE_THICKNESS_MM = 8.0
```

Change `_tier1_mate`'s returned `MateSpec` to add one argument after `position_tol_b=tol_b,`:

```python
        projected_zone_mm=(
            _PLATE_THICKNESS_MM if kind == "fixed_fastener" else None
        ),
```

and change the `AssemblySpec(...)` construction at the end of `sample_assembly` to set the thickness explicitly:

```python
    return AssemblySpec(
        seed=seed,
        difficulty=difficulty,
        mates=mates,
        plate_size_mm=plate_size_for_mates(mates),
        plate_thickness_mm=_PLATE_THICKNESS_MM,
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/gen/test_spec.py tests/gen/test_sampler.py -v`
Expected: PASS.

Then the full suite: `python -m pytest -q -m "not slow"`.

**Existing `MateSpec(kind="fixed_fastener", ...)` constructions in the test suite will now raise.** Grep for them and add `projected_zone_mm=8.0`:

```bash
grep -rn "fixed_fastener" tests/
```

Do not work around the new validation by switching those fixtures to `floating_fastener` — that would silently delete fixed-case coverage.

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/gen/spec.py src/tolcad/gen/sampler.py tests/gen/test_spec.py tests/gen/test_sampler.py
git commit -m "feat: record the projected tolerance zone B-4 assumes"
```

---

### Task 4: A committed AP242 fixture, so the oracle has a positive control on a fresh clone

**Files:**
- Create: `tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp` (copied from `data/nist_pmi/`, 396,445 bytes)
- Create: `tests/fixtures/NIST-PROVENANCE.md`
- Modify: `tests/test_ap242_pmi.py`

**Interfaces:**
- Consumes: `validation.ap242_pmi.read_pmi_counts`, `PmiCounts`
- Produces: no new API

On a fresh clone, `data/nist_pmi/` does not exist, so the 47/27/59 assertion skips. What remains exercised is a `FileNotFoundError` check and `tests/gen/test_end_to_end.py`'s assertion that our *own* exports have **zero** PMI. A `read_pmi_counts` stubbed to `return PmiCounts(0, 0, 0)` passes that entire fresh-clone suite. Design spec line 252 makes "fresh clone, no licence, runs end-to-end" an explicit success criterion, so this is precisely the configuration where the licence-free oracle's read path has no positive coverage at all.

Committing one small AP242 file fixes it. `nist_ctc_01_asme1_ap242-e1.stp` is the smallest NIST AP242 file with non-trivial PMI: **396,445 bytes**, reading as **21 dimensions, 6 geometric tolerances, 11 datums** — verified by execution, and it parses with no OCCT warnings. NIST states its files "can be used without any restrictions", so redistributing one in the repo is permitted.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ap242_pmi.py`:

```python
FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "nist_ctc_01_asme1_ap242-e1.stp"


def test_reads_nonzero_pmi_from_the_committed_fixture():
    """Positive control that runs on a FRESH CLONE, with no fetch step.

    Without this, the only oracle assertions a fresh clone exercises are
    zero-counts and a FileNotFoundError -- so a read_pmi_counts stubbed to
    `return PmiCounts(0, 0, 0)` would pass the whole suite, and the
    zero-PMI contrast in test_end_to_end.py would prove nothing. Design spec
    line 252 makes the fresh-clone path an explicit success criterion.

    Exact counts, verified by execution 2026-08-01, not bounds.
    """
    assert FIXTURE.is_file(), (
        "the AP242 fixture must be committed, not fetched -- that is the whole "
        "point of it"
    )
    counts = read_pmi_counts(FIXTURE)
    assert counts == PmiCounts(dimensions=21, geometric_tolerances=6, datums=11)


def test_the_fixture_and_the_fetched_suite_disagree_about_counts():
    """Guards a reader that returns a constant regardless of its input.

    Skips without the fetched suite, but on a developer machine it proves the
    two files are distinguished. The fixture test above is the fresh-clone
    guarantee; this one is the stronger check when both are available.
    """
    if not FTC06.is_file():
        pytest.skip("NIST suite not fetched; run scripts/fetch_nist_pmi.py")
    assert read_pmi_counts(FIXTURE) != read_pmi_counts(FTC06)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_ap242_pmi.py -v`
Expected: FAIL on `test_reads_nonzero_pmi_from_the_committed_fixture` — the fixture file does not exist yet, so the `FIXTURE.is_file()` assertion fires.

- [ ] **Step 3: Commit the fixture and its provenance**

```bash
mkdir -p tests/fixtures
cp data/nist_pmi/nist_ctc_01_asme1_ap242-e1.stp tests/fixtures/
```

Create `tests/fixtures/NIST-PROVENANCE.md`:

```markdown
# NIST AP242 test fixture

`nist_ctc_01_asme1_ap242-e1.stp` (396,445 bytes) is one file from the NIST MBE
PMI Validation and Conformance Test Suite, redistributed here unmodified.

- Source archive: https://www.nist.gov/system/files/documents/noindex/2024/06/19/NIST-PMI-STEP-Files.zip
  (reached from https://www.nist.gov/document/nist-pmi-step-files)
- Fetcher for the full suite: `scripts/fetch_nist_pmi.py`
- Terms: NIST states the test cases, CAD models and STEP files "can be used
  without any restrictions", and asks for acknowledgement.

## Why this one is committed when the rest of the suite is gitignored

The full ~14 MB suite stays out of git and is reproducible via the fetcher. This
single file is committed because it is the ONLY positive control the semantic-PMI
read path has on a fresh clone. Without it, every oracle assertion a fresh clone
runs is either a zero-count or a FileNotFoundError, and a `read_pmi_counts`
stubbed to return zeros would pass the entire suite. Design spec line 252 makes
"fresh clone, no licence, runs end-to-end" an explicit success criterion.

It is the smallest AP242 file in the suite carrying non-trivial PMI: 21
dimensions, 6 geometric tolerances, 11 datums.
```

Confirm `.gitignore`'s `data/nist_pmi/` entry does not also match `tests/fixtures/`:

```bash
git check-ignore -v tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp || echo "NOT ignored - good"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_ap242_pmi.py -v`
Expected: PASS, 4 tests.

Prove the fresh-clone claim rather than asserting it — temporarily move the fetched suite aside and confirm the fixture test still runs:

```bash
mv data/nist_pmi data/nist_pmi.bak
python -m pytest tests/test_ap242_pmi.py -v
mv data/nist_pmi.bak data/nist_pmi
```

Expected in the middle run: the fixture test **PASSES** (it does not depend on the fetched data), while the 47/27/59 test and the disagreement test skip. Paste that output. Restore the directory and re-confirm all four pass.

Then the full suite: `python -m pytest -q -m "not slow"`.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/ tests/test_ap242_pmi.py
git commit -m "test: commit one AP242 fixture as the oracle's fresh-clone positive control"
```

---

### Task 5: Give the layout margin constants teeth

**Files:**
- Test: `tests/gen/test_layout.py`

**Interfaces:** none — tests only.

`tests/gen/test_layout.py` imports `_MIN_WALL_MM` and `_EDGE_MARGIN_MM` from production and compares against them, so setting either constant to `0.0` breaks no test. That is not harmless: a zero wall makes adjacent Ø14.5 holes exactly tangent, which the containment test also cannot catch, because tangency has zero intersection volume. The result would be a degenerate zero-ligament B-rep in the reference geometry.

- [ ] **Step 1: Write the failing test**

Append to `tests/gen/test_layout.py`:

```python
def test_the_margin_constants_are_actually_large_enough():
    """The other margin tests compare against these constants, so they cannot
    fail if the constants go to zero. This one spells the numbers out.

    A zero wall makes adjacent holes exactly tangent. The containment test in
    test_build.py cannot catch that either, because tangency has zero
    intersection volume -- it would sail through as a degenerate B-rep with no
    ligament between neighbouring features.

    The floors come from layout.py's own derivation: the widest feature is
    Ø14.5, the largest allowable position tolerance is 2.5 mm diametral, and
    the ladder applies at most ~1.34x of it, so an axis can sit ~1.75 mm off
    nominal and a radius can grow 0.1 mm. Two neighbours leaning together
    consume 3.7 mm; one leaning at an edge consumes 1.85 mm.
    """
    from tolcad.gen.layout import _EDGE_MARGIN_MM, _MIN_WALL_MM

    assert _MIN_WALL_MM >= 3.7, (
        f"_MIN_WALL_MM {_MIN_WALL_MM} leaves no ligament between two features "
        f"leaning toward each other"
    )
    assert _EDGE_MARGIN_MM >= 1.85, (
        f"_EDGE_MARGIN_MM {_EDGE_MARGIN_MM} lets a feature leaning at the edge "
        f"break out of the plate"
    )
```

- [ ] **Step 2: Run the test to verify it fails**

The test passes against the current constants (4.0 and 5.0), so passing alone proves nothing. Demonstrate it can fail: temporarily set `_MIN_WALL_MM = 0.0` in `src/tolcad/gen/layout.py`, run

`python -m pytest tests/gen/test_layout.py -v`

and confirm this new test FAILS while the two pre-existing margin tests still PASS — that contrast is the finding. Paste both results, then restore `4.0`.

- [ ] **Step 3: No implementation needed**

This task adds no production code. The constants are already correct; the test is what was missing.

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest -q` (including slow) and `python scripts/gate_a.py`
Expected: all pass; Gate A still exits 1 with 6 PASS / 3 SKIP.

- [ ] **Step 5: Commit**

```bash
git add tests/gen/test_layout.py
git commit -m "test: pin the layout margins to literals, not to themselves"
```

---

## Plan completion state

At the end of Task 5:

- No sampled fit has a coin-toss label; the surviving three still span clearance, transition and interference
- The ISO-fit label leak is documented and pinned by an executable assertion, and Tier 2's contribution is the yield
- Fixed and floating fasteners are geometrically distinguishable, and a fixed mate is *structurally* not a floating one
- The projected tolerance zone B-4 assumes is recorded in the published schema
- The oracle read path has a positive control that runs on a fresh clone
- The layout margins cannot be zeroed without a test failing

**Deliberately NOT done here:**
- **ASME Y14.5 B-5** (the non-projected fixed-fastener case). The human chose to stay inside verified B-4 mathematics rather than add new closed-form standards code to the module where a wrong formula already bit this project once. Revisit only with the primary standard text in hand.
- **Writing semantic PMI into our own STEP files.** Still not needed: tolerances live in the sidecar and the NIST oracle only needs the read path.
- **Generating the research corpus.** Spec §12 still puts pre-registration first. This plan is the last thing before it.
- **Tracing the clearance-hole and tapping-drill tables to ISO 273 / ISO 261.** Both are honestly documented as untraced. If either resolves differently, the difficulty ladder is calibrated against the clearance table and must be re-measured.

## Open question for the human

The difficulty ladder was tuned against the *current* feature tables. Task 1 changes the sampled fit set and Task 2 changes `hole_b` for fixed fasteners, so although neither should move a Tier 1 verdict, both tasks require re-measuring the per-difficulty failure rate and reporting it. If the table has drifted outside the guard bands (`0.10-0.30` at d1, `0.60-0.80` at d4), that is a finding for the human, not a reason to widen the bands.
