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

