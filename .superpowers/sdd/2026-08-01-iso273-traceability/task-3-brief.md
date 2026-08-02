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
- The only remaining untraced number in the feature library is the tapped hole's tolerance band, documented as a deliberate simplification and provably inert
- The layout floors are re-measured against the new worst case, with no constant changed

**Deliberately NOT done here:**
- Changing `_MIN_WALL_MM` or `_EDGE_MARGIN_MM`. The arithmetic says 4.0 and 5.0 still suffice.
- Implementing ASME Y14.5 B-5. Unchanged decision.
- Adding IT grades beyond 12-14, or shaft letters beyond g/h/k/p. Only what ISO 273 requires.
- Generating the research corpus. Spec §12 still puts pre-registration first — and after this plan, pre-registration is unblocked.

## Open question for the human

The tapped hole keeps a flat +0.2/-0.0 band with no standard behind it. It is provably inert today, since `hole_b`'s size never enters B-4. If a later phase ever makes the tapped feature load-bearing — a press-fit dowel under an MMC modifier, say, which `y14_5.py`'s docstring already flags as the one case where its bonus-cancellation argument fails — that number stops being free and needs a real source.
