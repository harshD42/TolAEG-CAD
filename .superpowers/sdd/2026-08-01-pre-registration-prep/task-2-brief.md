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

