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
