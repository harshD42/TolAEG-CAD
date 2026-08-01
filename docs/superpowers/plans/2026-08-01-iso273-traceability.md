# ISO 273 Traceability Implementation Plan (Phase 3.5b)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every dimension in the generator's feature library traceable to a cited primary standard, so no untraced number survives into Phase 3.5 pre-registration.

**Architecture:** Three small changes. `iso286.py` gains IT12–IT14. `features.py` stops applying a flat hole tolerance and derives each clearance hole's upper deviation from the ISO 273 series grade at its diameter. `layout.py`'s test floor is re-measured against the now-larger worst-case hole growth. No new module, no CAD, no checker-core logic change.

**Tech Stack:** Python 3.13, numpy, pytest 9.0.2. CadQuery is not involved in any task here.

## Why this plan exists

The human obtained and read the primary sources on 2026-08-01. Results:

- **ISO 273-1979(E), Table 1** — all 21 of our clearance-hole diameters (M3–M12 × fine/medium/coarse) match **exactly**. Our internal names close/normal/loose map onto the standard's fine/medium/coarse.
- **ISO 2306-1972, Table 1 (coarse pitch series)** — all 7 of our tapping-drill diameters match **exactly**, including M8 → 6.80 and M12 → 10.20. Those two are *not* nominal-minus-pitch (6.75, 10.25); ISO 2306 §0 explains the drill diameter is only *approximately* D − P, with the actual sizes selected from ISO/R 235 preferred drill diameters.
- **ISO 273 tolerance fields** — the standard states: *"The following tolerance fields are given for information only, for use where it is desirable to specify tolerances: fine series : H12, medium series : H13, coarse series : H14."*

Our code currently applies a flat `+0.2/-0.0 mm` to every clearance hole at every diameter, commented only as "H13-ish". That is not H12, H13, or H14, and it does not vary with diameter. The human decided to implement the standard's grades.

## A trap that must not be lost — read before touching `iso286.py`

**ISO 286-1:2010 Table 1 publishes IT01–IT11 in micrometres and IT12–IT18 in MILLIMETRES.** The header carries two separate span labels. `_IT_MICRONS` stores micrometres, so the new rows must be converted on entry (0.12 mm → 120), and pasting the published figures directly would make every new value 1000× too small.

`CLAUDE.md` currently says *"ISO 286 tables publish micrometres; convert at the table boundary and nowhere else."* That is true for the grades we had (IT5–IT8) and **false for exactly the grades this plan adds.** Task 1 corrects it.

## What this change can and cannot move

Hole MMC is `nominal + lower_dev`, and every clearance hole has `lower_dev = 0.0`. **The upper deviation therefore cannot move any Tier 1 verdict, nor the difficulty ladder.** Measured reference, which every task must re-confirm: d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1% over seeds 0-199.

It does move one thing, already computed:

| | flat +0.2 | ISO 273 grades |
|---|---|---|
| worst hole | any | M12 coarse Ø14.5, IT14 |
| radius growth at LMC | 0.100 | 0.215 |
| worst-case excursion | 1.775 | 1.890 |
| required wall (2×) | 3.550 | **3.780** |
| `_MIN_WALL_MM` | 4.0 | 4.0 — **still sufficient**, headroom 12.7% → 5.5% |
| required edge (1×) | 1.775 | 1.890 vs `_EDGE_MARGIN_MM` 5.0 — ample |

**No constant needs to change.** But `tests/gen/test_layout.py`'s literal floor asserts `_MIN_WALL_MM >= 3.7`, and the true requirement becomes 3.78 — so that literal is now *below* the real requirement and must be raised. Note that neither existing layout test fails on its own: the derived-floor test recomputes from the tables and still passes (4.0 ≥ 3.78), and the literal test still passes (4.0 ≥ 3.7). The staleness is silent, which is why Task 3 addresses it explicitly.

## Global Constraints

- **All dimensions in millimetres, stored as `float`.** ISO 286-1 publishes IT01–IT11 in µm and IT12–IT18 in mm; both convert to µm at the `iso286.py` table boundary and nowhere else.
- **Do NOT modify `y14_5.py`, `montecarlo.py`, `checker.py`, `types.py`, or `reliability.py`.** `iso286.py` is checker-core and IS modified here, additively — no existing value may change.
- **`spec.py`, `features.py`, `sampler.py`, `layout.py` stay CAD-free.** No task here imports CadQuery or OCP.
- **`validation/` is one-directional**; core may never import it.
- **Tier 1 is exact**, EPS = 1e-9.
- **Pre-registered Gate A/B/C/D thresholds in design spec §7 are FROZEN**; `scripts/gate_a.py` untouched.
- **Do NOT generate a research corpus.** Spec §12 puts pre-registration first.
- **No existing `_IT_MICRONS`, `_DEVIATION_MICRONS`, or `_SIZE_BANDS` value may change.** 117 of them were verified against primary tables on 2026-08-01. This plan only appends rows.

## File structure

| File | Change | Responsibility |
|---|---|---|
| `src/tolcad/iso286.py` | Modify | Append IT12–IT14 rows; document the mm/µm split |
| `CLAUDE.md` | Modify | Correct the "publishes micrometres" claim |
| `src/tolcad/gen/features.py` | Modify | Per-series ISO 273 grades; primary-source citations |
| `tests/test_iso286.py` | Modify | Pin the new rows and the unit boundary |
| `tests/gen/test_features.py` | Modify | Pin per-series deviations and the citations |
| `tests/gen/test_layout.py` | Modify | Raise the stale literal floor |

---

### Task 1: Extend `iso286.py` to IT12–IT14

**Files:**
- Modify: `src/tolcad/iso286.py`
- Modify: `CLAUDE.md`
- Test: `tests/test_iso286.py`

**Interfaces:**
- Consumes: nothing new
- Produces: `it_grade(nominal_mm, grade)` accepting grades 12, 13 and 14 in addition to 5–8

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_iso286.py`:

```python
def test_it12_to_it14_are_tabulated():
    """ISO 273 assigns H12/H13/H14 to its three clearance-hole series, so the
    generator cannot cite the standard without these grades."""
    for grade in (12, 13, 14):
        assert it_grade(20.0, grade) > 0.0


@pytest.mark.parametrize("nominal, grade, expected_mm", [
    # ISO 286-1:2010 Table 1. These are published in MILLIMETRES, not
    # micrometres -- the table has a separate span label for IT12-IT18.
    (4.0, 12, 0.12), (4.0, 13, 0.18), (4.0, 14, 0.30),
    (8.0, 12, 0.15), (8.0, 13, 0.22), (8.0, 14, 0.36),
    (14.0, 12, 0.18), (14.0, 13, 0.27), (14.0, 14, 0.43),
])
def test_it12_to_it14_match_iso286_table_1(nominal, grade, expected_mm):
    assert it_grade(nominal, grade) == pytest.approx(expected_mm)


def test_the_new_rows_did_not_land_a_thousand_times_too_small():
    """ISO 286-1 publishes IT12-IT18 in mm while _IT_MICRONS stores um.

    Pasting 0.43 straight into a micrometre table yields 0.00043 mm, which is
    smaller than IT5 and would sail through every other test in this file.
    IT14 must exceed IT8 at the same size, always.
    """
    for nominal in (4.0, 8.0, 14.0, 100.0, 400.0):
        assert it_grade(nominal, 12) > it_grade(nominal, 8)
        assert it_grade(nominal, 13) > it_grade(nominal, 12)
        assert it_grade(nominal, 14) > it_grade(nominal, 13)


def test_new_rows_span_every_size_band():
    """A short row would silently misalign against _SIZE_BANDS."""
    from tolcad.iso286 import _IT_MICRONS, _SIZE_BANDS
    for grade in (12, 13, 14):
        assert len(_IT_MICRONS[grade]) == len(_SIZE_BANDS)


def test_existing_grades_are_untouched():
    """117 values were verified against primary tables; this plan only appends."""
    assert it_grade(4.0, 5) == pytest.approx(0.005)
    assert it_grade(4.0, 8) == pytest.approx(0.018)
    assert it_grade(14.0, 7) == pytest.approx(0.018)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_iso286.py -v -k "it12 or new_rows or thousand or untouched"`
Expected: FAIL with `ValueError: IT grade 12 not tabulated; have [5, 6, 7, 8]`. `test_existing_grades_are_untouched` should PASS already — it is a regression pin.

- [ ] **Step 3: Append the rows**

In `src/tolcad/iso286.py`, replace the `_IT_MICRONS` comment and dict with:

```python
# IT grade tolerance, micrometres, indexed parallel to _SIZE_BANDS.
#
# UNIT TRAP. ISO 286-1:2010 Table 1 publishes IT01-IT11 in MICROMETRES and
# IT12-IT18 in MILLIMETRES -- the table carries two separate span labels across
# the grade columns. Everything below is micrometres, so the IT12-IT14 rows were
# multiplied by 1000 on entry: the published 0,43 mm for IT14 at >10-18 is the
# 430 here. Pasting the published figures directly would make them 1000x too
# small, and 0.00043 mm is narrower than IT5 -- small enough to pass every
# ordering-free test in the suite. tests/test_iso286.py pins the ordering
# IT8 < IT12 < IT13 < IT14 specifically to catch that.
_IT_MICRONS: dict[int, list[int]] = {
    5: [4, 5, 6, 8, 9, 11, 13, 15, 18, 20, 23, 25, 27],
    6: [6, 8, 9, 11, 13, 16, 19, 22, 25, 29, 32, 36, 40],
    7: [10, 12, 15, 18, 21, 25, 30, 35, 40, 46, 52, 57, 63],
    8: [14, 18, 22, 27, 33, 39, 46, 54, 63, 72, 81, 89, 97],
    # ISO 273 assigns H12/H13/H14 to its fine/medium/coarse clearance-hole
    # series, so the generator needs these three grades to cite the standard.
    12: [100, 120, 150, 180, 210, 250, 300, 350, 400, 460, 520, 570, 630],
    13: [140, 180, 220, 270, 330, 390, 460, 540, 630, 720, 810, 890, 970],
    14: [250, 300, 360, 430, 520, 620, 740, 870, 1000, 1150, 1300, 1400, 1550],
}
```

Then update the module docstring's TRANSCRIPTION SOURCE paragraph, appending:

```
IT12-IT14 were added on 2026-08-01 from the same ISO 286-1:2010 Table 1, all 13
size bands each. NOTE the unit change: Table 1 publishes IT01-IT11 in micrometres
and IT12-IT18 in millimetres, so these three rows were converted on entry. See the
comment on _IT_MICRONS.
```

- [ ] **Step 4: Correct `CLAUDE.md`**

The Conventions section currently reads:

```
- **All dimensions are millimetres (float).** ISO 286 tables publish micrometres;
  convert at the table boundary and nowhere else.
```

Replace with:

```
- **All dimensions are millimetres (float).** ISO 286-1 Table 1 publishes IT01-IT11
  in micrometres but IT12-IT18 in millimetres; convert at the table boundary in
  `iso286.py` and nowhere else. `_IT_MICRONS` is micrometres throughout, so the
  IT12-IT14 rows were multiplied by 1000 on entry.
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_iso286.py -v`
Expected: PASS.

Then the full suite: `python -m pytest -q -m "not slow"`. Baseline is **220 passed** at HEAD. Nothing outside `iso286.py` consumes grades 12-14 yet, so no other test should change.

- [ ] **Step 6: Commit**

```bash
git add src/tolcad/iso286.py tests/test_iso286.py CLAUDE.md
git commit -m "feat: tabulate IT12-IT14, noting ISO 286-1 publishes them in mm"
```

---

### Task 2: Derive clearance-hole tolerance from the ISO 273 series grade

**Files:**
- Modify: `src/tolcad/gen/features.py`
- Test: `tests/gen/test_features.py`

**Interfaces:**
- Consumes: `tolcad.iso286.it_grade` (grades 12-14, from Task 1)
- Produces: `clearance_hole_for(fastener_mm, grade)` returning a diameter-dependent, series-dependent `upper_dev`; `SERIES_TOLERANCE_GRADE: dict[str, int]`

`_HOLE_UPPER_DEV_MM = 0.2` is replaced for clearance holes. It stays for tapped holes — see below, that is deliberate and provably inert.

- [ ] **Step 1: Write the failing tests**

Append to `tests/gen/test_features.py`:

```python
def test_each_series_carries_its_iso273_tolerance_grade():
    """ISO 273-1979 Table 1 note: fine H12, medium H13, coarse H14."""
    from tolcad.gen.features import SERIES_TOLERANCE_GRADE
    assert SERIES_TOLERANCE_GRADE == {"close": 12, "normal": 13, "loose": 14}


@pytest.mark.parametrize("fastener_mm, grade, expected_upper_dev", [
    # upper_dev == IT at the HOLE diameter (H holes have lower deviation 0).
    # ISO 286-1:2010 Table 1, converted to mm.
    (3.0, "close", 0.12),    # Ø3.2  -> IT12 in >3-6
    (3.0, "loose", 0.30),    # Ø3.6  -> IT14 in >3-6
    (8.0, "close", 0.15),    # Ø8.4  -> IT12 in >6-10
    (8.0, "normal", 0.22),   # Ø9.0  -> IT13 in >6-10
    (8.0, "loose", 0.36),    # Ø10.0 -> IT14 in >6-10
    (12.0, "loose", 0.43),   # Ø14.5 -> IT14 in >10-18
])
def test_clearance_hole_upper_dev_comes_from_the_series_grade(
    fastener_mm, grade, expected_upper_dev
):
    hole = clearance_hole_for(fastener_mm, grade)
    assert hole["upper_dev"] == pytest.approx(expected_upper_dev)
    assert hole["lower_dev"] == 0.0


def test_clearance_hole_tolerance_is_no_longer_flat():
    """The old code applied +0.2 to every hole at every size.

    A regression to a constant would make the schema untraceable again, and
    every other test here would still pass, so assert the variation directly.
    """
    devs = {
        clearance_hole_for(f, g)["upper_dev"]
        for f in FASTENER_SIZES
        for g in ("close", "normal", "loose")
    }
    assert len(devs) > 1, f"tolerance is constant across all holes: {devs}"


def test_tolerance_widens_with_series_at_a_fixed_fastener():
    """H12 < H13 < H14, and the hole diameter grows too, so this is monotone."""
    for f in FASTENER_SIZES:
        close = clearance_hole_for(f, "close")["upper_dev"]
        normal = clearance_hole_for(f, "normal")["upper_dev"]
        loose = clearance_hole_for(f, "loose")["upper_dev"]
        assert close < normal < loose, f"M{f}: {close}, {normal}, {loose}"


def test_hole_mmc_is_unaffected_by_the_tolerance_change():
    """Guards the claim that this cannot move a Tier 1 verdict.

    MMC is nominal + lower_dev and lower_dev is 0, so MMC equals the nominal
    diameter regardless of the grade. If this ever fails, the difficulty ladder
    has moved and the pre-registered numbers are invalid.
    """
    for f in FASTENER_SIZES:
        for g in ("close", "normal", "loose"):
            hole = clearance_hole_for(f, g)
            assert hole["nominal"] + hole["lower_dev"] == hole["nominal"]


def test_features_module_cites_its_primary_sources():
    """The provenance caveat is gone, so the citation must actually be there."""
    import pathlib
    import tolcad.gen.features as mod
    text = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
    assert "ISO 273" in text
    assert "ISO 2306" in text
    assert "not been checked against the primary" not in text, (
        "the caveat was removed only because the check was done; do not "
        "reinstate it without also removing the citations"
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/gen/test_features.py -v -k "series or flat or widens or mmc or cites"`
Expected: FAIL — `ImportError` for `SERIES_TOLERANCE_GRADE`, and the deviation tests failing because every hole currently returns `0.2`. `test_hole_mmc_is_unaffected_by_the_tolerance_change` should PASS already.

- [ ] **Step 3: Rewrite the module header and `clearance_hole_for`**

Replace the module docstring of `src/tolcad/gen/features.py` with:

```python
"""Canonical mating features for generated assemblies. No CAD dependency.

CLEARANCE HOLES -- ISO 273-1979(E), Table 1. All 21 diameters below (M3-M12 x
fine/medium/coarse) were checked against the primary standard on 2026-08-01 and
match exactly. This module's internal names close/normal/loose correspond to the
standard's fine/medium/coarse.

The standard also states: "The following tolerance fields are given for
information only, for use where it is desirable to specify tolerances: fine
series : H12, medium series : H13, coarse series : H14." We take that option, so
a hole's upper deviation is the IT value at ITS OWN diameter for ITS series --
not a single constant. An earlier version applied a flat +0.2 mm described only
as "H13-ish", which was not any of the three grades and did not vary with size.

TAPPING DRILLS -- ISO 2306-1972, Table 1 (coarse pitch series). All 7 diameters
checked against the primary standard on 2026-08-01 and match exactly. Note M8 ->
6.8 and M12 -> 10.2 are NOT nominal-minus-pitch (that would give 6.75 and 10.25).
ISO 2306 clause 0 says the drill diameter is only APPROXIMATELY D - P, with the
actual sizes selected from the ISO/R 235 preferred drill series. Do not "correct"
them to the subtraction.

All values are pinned by tests so a silent edit cannot drift them.
"""
```

Replace the `_HOLE_UPPER_DEV_MM` constant block with:

```python
# ISO 273-1979 Table 1, tolerance-fields note. Grade per clearance-hole series.
SERIES_TOLERANCE_GRADE: dict[str, int] = {"close": 12, "normal": 13, "loose": 14}

# Tapped holes: ISO 2306 gives drill DIAMETERS, not tolerances, and ISO 273
# covers clearance holes only, so no standard here fixes a grade for the tapped
# feature. A flat band is used deliberately rather than inventing a citation.
# This is provably inert: y14_5's B-4 formula never reads hole_b's size in the
# fixed-fastener case (its docstring is explicit that hole_b is not a clearance
# hole there), so no verdict in the corpus depends on this number.
_TAPPED_HOLE_UPPER_DEV_MM = 0.2
```

Replace `clearance_hole_for` with:

```python
def clearance_hole_for(fastener_mm: float, grade: str) -> dict:
    """Return a checker-ready hole dict for a fastener at a clearance grade.

    The upper deviation is the ISO 286 IT value for this series' grade AT THE
    HOLE'S OWN DIAMETER, per the ISO 273 tolerance-fields note. Lower deviation
    is zero: these are H holes, so MMC equals the nominal diameter.
    """
    if fastener_mm not in _CLEARANCE_HOLE_MM:
        raise ValueError(
            f"fastener size {fastener_mm} not tabulated; have {FASTENER_SIZES}"
        )
    if grade not in _GRADE_INDEX:
        raise ValueError(f"grade must be one of {sorted(_GRADE_INDEX)}, got {grade!r}")
    nominal = _CLEARANCE_HOLE_MM[fastener_mm][_GRADE_INDEX[grade]]
    return {
        "nominal": nominal,
        "lower_dev": 0.0,
        "upper_dev": it_grade(nominal, SERIES_TOLERANCE_GRADE[grade]),
        "position_tol": 0.0,
    }
```

In `tapped_hole_for`, change `_HOLE_UPPER_DEV_MM` to `_TAPPED_HOLE_UPPER_DEV_MM`. Ensure the import line reads `from tolcad.iso286 import fit_from_designation, it_grade`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/gen/test_features.py -v`
Expected: PASS.

Then the full suite: `python -m pytest -q -m "not slow"`.

**Re-measure the ladder and report the table.** It must be unchanged at d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%, because hole MMC does not depend on the upper deviation:

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

If it moved, STOP and report — the reasoning in this plan is then wrong and pre-registration must not proceed on it.

`tests/gen/test_layout.py`'s derived-floor test recomputes the requirement from `clearance_hole_for`, so it now sees 3.78 mm against `_MIN_WALL_MM = 4.0` and should still pass. If it fails, report the numbers rather than adjusting the constant.

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/gen/features.py tests/gen/test_features.py
git commit -m "feat: clearance holes carry their ISO 273 series tolerance grade"
```

---

### Task 3: Re-measure the layout margin and retire the stale literal floor

**Files:**
- Modify: `tests/gen/test_layout.py`
- Test: same file

**Interfaces:** none — tests only. No production code changes.

The worst-case hole growth rose from 0.100 mm to 0.215 mm (M12 coarse, Ø14.5, IT14). Recomputed worst-case excursion is 1.890 mm, so the required wall is **3.780 mm** against `_MIN_WALL_MM = 4.0` — still sufficient, headroom down from 12.7% to 5.5%. **No constant changes.**

But the literal floor asserts `_MIN_WALL_MM >= 3.7`, which is now *below* the true requirement of 3.78. Neither existing test fails: the derived-floor test recomputes correctly and passes, and the literal passes too. The literal has silently stopped being a floor — it would accept a `_MIN_WALL_MM` of 3.75, which is genuinely too small.

- [ ] **Step 1: Write the failing test**

In `tests/gen/test_layout.py`, find the literal-floor test (it asserts `_MIN_WALL_MM >= 3.7` and `_EDGE_MARGIN_MM >= 1.85`) and change the wall literal to `3.78`, updating its docstring derivation:

```python
    assert _MIN_WALL_MM >= 3.78, (
        f"_MIN_WALL_MM {_MIN_WALL_MM} leaves no ligament between two features "
        f"leaning toward each other"
    )
```

Add alongside it:

```python
def test_the_literal_floor_is_not_below_the_derived_one():
    """The literal is a second, cruder floor -- it must not undercut the real one.

    When clearance holes moved from a flat +0.2 to their ISO 273 series grades,
    the worst-case growth at M12 coarse went from 0.100 to 0.215 mm and the
    required wall rose from 3.55 to 3.78. The literal still said 3.7. NEITHER
    layout test failed: the derived floor recomputed correctly and passed, and
    the literal passed too -- it had simply stopped being a floor, and would
    have accepted a _MIN_WALL_MM of 3.75 that is genuinely too small.

    This test is what notices next time.
    """
    required = 2.0 * _worst_case_radial_excursion_mm()
    assert _LITERAL_WALL_FLOOR_MM >= required, (
        f"the literal floor {_LITERAL_WALL_FLOOR_MM} is below the derived "
        f"requirement {required:.4f}; recompute it from the tables"
    )
```

Hoist the two literals to module constants so both tests read the same numbers:

```python
# Cruder second floors, spelled as numbers so zeroing a production constant is
# caught even if the derivation above is edited. Recompute these whenever the
# clearance-hole table, its tolerance grades, or the difficulty ladder changes.
_LITERAL_WALL_FLOOR_MM = 3.78
_LITERAL_EDGE_FLOOR_MM = 1.89
```

and use them in the literal-floor test.

- [ ] **Step 2: Run the test to verify it fails**

The new test passes once the literal is 3.78, so passing proves nothing. Demonstrate the contrast: temporarily set `_LITERAL_WALL_FLOOR_MM = 3.7` (its stale value), run

`python -m pytest tests/gen/test_layout.py -v`

and confirm `test_the_literal_floor_is_not_below_the_derived_one` FAILS with the 3.78 requirement while every other layout test PASSES — that contrast is the finding. Paste both. Then restore 3.78.

- [ ] **Step 3: No production code changes**

`_MIN_WALL_MM` and `_EDGE_MARGIN_MM` stay at 4.0 and 5.0. If you find yourself editing `src/tolcad/gen/layout.py`, stop: the arithmetic above says the constants are still adequate, and changing them would be unjustified churn.

Do update `layout.py`'s docstring margin derivation, which still cites a 0.1 mm radius growth, to the new 0.215 mm worst case and the 3.78 mm requirement — that is documentation, not a constant.

- [ ] **Step 4: Run the full suite and Gate A**

Run: `python -m pytest -q` (no filter, includes slow), then
`python scripts/gate_a.py > /dev/null 2>&1; echo $?`
Expected: all pass; Gate A exits 1 with 6 PASS / 3 SKIP. Capture the exit code without a pipe — piping to `tail` reports tail's status.

Re-measure and report the ladder one final time. Unchanged: d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%.

- [ ] **Step 5: Commit**

```bash
git add tests/gen/test_layout.py src/tolcad/gen/layout.py
git commit -m "test: re-measure the layout floors against the ISO 273 grades"
```

---

## Plan completion state

At the end of Task 3:

- Every diameter in `features.py` is traceable to ISO 273-1979 Table 1 or ISO 2306-1972 Table 1, cited in the module docstring
- Every clearance hole's tolerance is the ISO 273 series grade at its own diameter, via `iso286.py`
- `iso286.py` carries IT12-IT14 with the mm/µm publication split documented, and `CLAUDE.md` no longer overstates the unit rule
- **Two** numbers in the generator remain untraced, both documented as deliberate standard-free simplifications and both provably inert:
  1. `features._TAPPED_HOLE_UPPER_DEV_MM = 0.2`, the tapped hole's tolerance band. Inert because `y14_5`'s B-4 formula never reads `hole_b`'s size in the fixed-fastener case.
  2. `sampler._FASTENER_LOWER_DEV_MM = -0.1` (with `_FASTENER_UPPER_DEV_MM = 0.0`), the fastener's size tolerance. A real citation would be ISO 4759-1 or ISO 965; neither has been obtained. Inert because a fastener is external, so its MMC is `nominal + upper_dev = nominal`, and `y14_5.fastener_assembles` reads `fastener.mmc` and nothing else — the lower deviation is unreachable from any verdict at any value.

  (An earlier revision of this statement said "the only remaining untraced number ... is the tapped hole's", which was false: the fastener band was inline in `sampler._tier1_mate` and carried no comment at all. Corrected before pre-registration.)
- The layout floors are re-measured against the new worst case, with no constant changed

**Deliberately NOT done here:**
- Changing `_MIN_WALL_MM` or `_EDGE_MARGIN_MM`. The arithmetic says 4.0 and 5.0 still suffice.
- Implementing ASME Y14.5 B-5. Unchanged decision.
- Adding IT grades beyond 12-14, or shaft letters beyond g/h/k/p. Only what ISO 273 requires.
- Generating the research corpus. Spec §12 still puts pre-registration first — and after this plan, pre-registration is unblocked.

## Open question for the human

The tapped hole keeps a flat +0.2/-0.0 band with no standard behind it, and the fastener keeps a flat -0.1/+0.0 one. Both are provably inert today: `hole_b`'s size never enters B-4, and the fastener's upper deviation is zero so its MMC is the nominal. If a later phase ever makes the tapped feature load-bearing — a press-fit dowel under an MMC modifier, say, which `y14_5.py`'s docstring already flags as the one case where its bonus-cancellation argument fails — or ever gives the fastener a non-zero upper deviation, those numbers stop being free and need real sources (ISO 4759-1 or ISO 965 for the fastener).
