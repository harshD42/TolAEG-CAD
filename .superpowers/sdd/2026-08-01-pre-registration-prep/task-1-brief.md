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

