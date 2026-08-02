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

