# Final fix wave — whole-branch review of `feat/iso273-traceability`

Date: 2026-08-01
Baseline: `4db2f8f`, 258 passed
Range: `4db2f8f..2621be5` (3 commits)

| SHA | Subject |
|---|---|
| `0459fe0` | test: guard both literal layout floors against their derived requirements |
| `a92d812` | docs: correct iso286's grade parenthetical, pin the widened designation set |
| `2621be5` | docs: name the fastener's untraced tolerance and pin its inertness |

Status: **all findings in scope addressed.** No blockers. Out-of-scope items untouched.

---

## I-1 — anti-staleness guard covered the wall floor only

`tests/gen/test_layout.py`, `src/tolcad/gen/layout.py`.

Confirmed the reported defect before fixing: `_LITERAL_EDGE_FLOOR_MM = 1.89` was
below its derived requirement `1.8900000000000001`, passing only on the `1e-9`
epsilon, and no test compared the edge literal to anything derived.

Fix:

- `_LITERAL_WALL_FLOOR_MM` 3.78 → **3.8**, `_LITERAL_EDGE_FLOOR_MM` 1.89 → **1.9**.
  Rounding up restores their stated role as a *conservative* second floor rather
  than a restatement of the derivation. Comment records why, including the ulp
  incident, so a future pass does not "tidy" them back down to the derived values.
- `test_the_literal_floor_is_not_below_the_derived_one` renamed to
  `test_the_literal_floors_are_not_below_the_derived_ones` and given the mirrored
  edge assertion. Both comparisons keep the `1e-9` epsilon.
- Docstrings in both files updated to describe the new arrangement.

Production constants unchanged: `_MIN_WALL_MM = 4.0`, `_EDGE_MARGIN_MM = 5.0`.
Derived requirements unchanged at 3.78 / 1.890.

### Mutation demonstration (verbatim)

With `_LITERAL_EDGE_FLOOR_MM` temporarily set to `1.5`:

```
$ python -m pytest tests/gen/test_layout.py -v
...
        required_wall = 2.0 * _worst_case_radial_excursion_mm()
        required_edge = _worst_case_radial_excursion_mm()

        assert _LITERAL_WALL_FLOOR_MM >= required_wall - 1e-9, (
            f"the literal wall floor {_LITERAL_WALL_FLOOR_MM} is below the derived "
            f"requirement {required_wall:.4f}; recompute it from the tables"
        )
>       assert _LITERAL_EDGE_FLOOR_MM >= required_edge - 1e-9, (
            f"the literal edge floor {_LITERAL_EDGE_FLOOR_MM} is below the derived "
            f"requirement {required_edge:.4f}; recompute it from the tables"
        )
E       AssertionError: the literal edge floor 1.5 is below the derived requirement 1.8900; recompute it from the tables
E       assert 1.5 >= (1.8900000000000001 - 1e-09)

tests\gen\test_layout.py:204: AssertionError
=========================== short test summary info ===========================
FAILED tests/gen/test_layout.py::test_the_literal_floors_are_not_below_the_derived_ones
========================= 1 failed, 9 passed in 0.13s =========================
```

The new assertion is the only failure; the other nine layout tests pass, which is
exactly the silent-floor pattern the guard exists to break. Literal restored to
1.9; `tests/gen/test_layout.py` then reports `10 passed`.

---

## I-2 — false docstring, silently widened checker-core API

`src/tolcad/iso286.py`, `tests/test_iso286.py`.

(a) Both parentheticals corrected from `(5-8 as currently tabulated)` to
`(5-8 and 12-14 as currently tabulated)`. Added a paragraph stating explicitly
that the accepted set for `g`/`h`/`p` *widens whenever a row is added to
`_IT_MICRONS`*, that adding IT12–IT14 for ISO 273 therefore also made `H12/g12`,
`H13/h13` and `H14/p14` valid where they previously raised, and that this is
correct per ISO 286-1 Tables 4 and 5 (g, h, p given for all standard tolerance
grades).

(b) Three tests appended pinning the surface in both directions:

- `test_iso273_grades_are_accepted_for_unrestricted_shaft_letters` — parametrized
  over `H12/g12`, `H13/h13`, `H14/p14`; each returns a well-ordered fit.
- `test_an_untabulated_grade_is_still_rejected` — `H9/g9` raises
  `ValueError: IT grade 9 not tabulated`. Widening did not become accept-anything.
- `test_k_is_still_restricted_to_it4_through_it7_after_the_widening` — `H12/k12`,
  `H13/k13`, `H14/k14` all still raise. `k` did **not** pick up the new grades,
  because `_SHAFT_LETTER_GRADE_RANGE` constrains it to the Table 5 "IT4 to IT7"
  column.

No value or logic change in `iso286.py`. Verified by diffing against `4db2f8f`:
the only changed lines in that file are the two parentheticals plus the new
paragraph.

---

## I-3 — traceability claim was not end-to-end

`src/tolcad/gen/sampler.py`, `tests/gen/test_sampler.py`, plan doc.

`sampler.py:76` built the fastener dict with an inline `-0.1 / 0.0` carrying no
comment whatsoever — the one number in the generator with neither a citation nor
an inertness argument, in a benchmark definition about to be frozen publicly.

Fix:

- Hoisted to `_FASTENER_LOWER_DEV_MM = -0.1` and `_FASTENER_UPPER_DEV_MM = 0.0`
  with the same treatment `_TAPPED_HOLE_UPPER_DEV_MM` received: an explicit
  declaration that no standard backs them, that a real citation would be
  ISO 4759-1 or ISO 965, that neither has been obtained, and that inventing one
  is worse than declaring the gap.
- The inertness argument is spelled out structurally: a fastener is an EXTERNAL
  feature, so `mmc = max_size = nominal + upper_dev`; `_FASTENER_UPPER_DEV_MM` is
  `0.0`, so MMC is exactly the nominal; `y14_5.fastener_assembles` reads
  `fastener.mmc` and nothing else — never LMC, never the band width. The lower
  deviation is therefore unreachable from any verdict *at any value*.
- Two tests added:
  - `test_the_fastener_tolerance_is_inert_because_its_mmc_is_the_nominal` —
    constructs a `FeatureOfSize(..., EXTERNAL)` from every sampled Tier 1 mate's
    fastener across seeds 0–49 × d1–d4 and asserts `mmc == nominal`, plus a
    non-vacuity guard on the sample count.
  - `test_the_fastener_tolerance_is_named_and_declared_standard_free` — asserts
    the inline literal has not returned and the declaration is still present.
- Plan §"Plan completion state" amended: the bullet claiming "the only remaining
  untraced number ... is the tapped hole's tolerance band" now names **two**
  numbers, each with its own inertness argument, and records that the earlier
  wording was false. The "Open question for the human" section extended to cover
  the fastener band and the condition under which it stops being free (a non-zero
  upper deviation).

---

## Minor 5 — `features.py` overstated its own guarantees

Reworded rather than pinned, as recommended. The docstring now says that every
value traceable to ISO 273 or ISO 2306 (21 clearance-hole diameters, 7
tapping-drill diameters) is pinned to its exact published figure, and that
`_TAPPED_HOLE_UPPER_DEV_MM` is deliberately *not* pinned — it is arbitrary by
construction, so pinning it would only assert that an arbitrary number has not
changed. It is bounded instead by
`test_tapped_hole_is_always_smaller_than_its_fastener`, which enforces the
property that actually matters. The constant's value is unchanged at 0.2.

---

## Minor 6 — band-boundary case added

`(10.0, "loose", 0.43)` added to
`test_clearance_hole_upper_dev_comes_from_the_series_grade`, with a comment
recording *why* it is the sharpest case: the hole is Ø12.0, in the >10–18 band
(IT14 = 0.43), while the M10 fastener sits in >6–10 (which would give 0.36).
Looking the grade up at the fastener diameter is the natural mistake, and this is
the pair where the two answers differ across a band boundary.

---

## Minor 8 — wrong headroom figure

`src/tolcad/gen/layout.py` docstring. The 5.5% was excess-over-*wall*; the sibling
figure it sat beside used excess-over-*required*. Corrected to **5.8%**
(`(4.0 - 3.78) / 3.78`), and the formula is now stated once, explicitly, above
both figures, with a note that the two denominators are what produced the wrong
number. The sibling edge figure was `~2.6x`, a ratio rather than an excess
percentage; restated as `(5.0 - 1.890) / 1.890 = 165% headroom` so both use the
same formula. `_MIN_WALL_MM` and `_EDGE_MARGIN_MM` unchanged; the derived
requirements remain 3.78 and 1.890.

---

## Verification

**1. Full suite, no marker filter**

```
$ python -m pytest -q
266 passed in 22.07s
```

258 → 266, exactly +8:

| file | new collected tests | what |
|---|---|---|
| `tests/test_iso286.py` | 5 | 3 parametrized (`H12/g12`, `H13/h13`, `H14/p14`) + `H9/g9` rejection + `k` restriction |
| `tests/gen/test_sampler.py` | 2 | fastener-MMC inertness, named-constant guard |
| `tests/gen/test_features.py` | 1 | the `(10.0, "loose", 0.43)` band-boundary case |

The I-1 edge assertion was folded into the existing (renamed) layout test, so it
adds coverage without adding a collected test. No test was removed or skipped.

**2. Gate A**

```
$ python scripts/gate_a.py > /dev/null 2>&1; echo $?
1
```

Exit code 1, tally **6 PASS / 3 SKIP** — unchanged from baseline. `scripts/gate_a.py`
and design spec §7 thresholds untouched. Exit code captured without a pipe.

**3. Tier 1 ladder, seeds 0–199**

| difficulty | fail / total | rate | reference |
|---|---|---|---|
| d1 | 31 / 159 | 19.5% | 19.5% |
| d2 | 99 / 301 | 32.9% | 32.9% |
| d3 | 239 / 452 | 52.9% | 52.9% |
| d4 | 421 / 609 | 69.1% | 69.1% |

Exact match on all four levels. Nothing in this wave moved the ladder, as
required.

**4. Mutation demonstration** — above, verbatim.

**5. Constants and tables**

```
_MIN_WALL_MM 4.0   _EDGE_MARGIN_MM 5.0
_TAPPED_HOLE_UPPER_DEV_MM 0.2   _PLATE_THICKNESS_MM 8.0
```

Table immutability verified structurally rather than by eye: a SHA-256 over the
JSON serialisation of `_IT_MICRONS`, `_DEVIATION_MICRONS`, `_SIZE_BANDS`,
`_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM` and `_TOL_FRACTION_RANGE` was computed at
HEAD and, via a throwaway git worktree, at `4db2f8f`:

```
HEAD    hash 364e7375ecbad327
4db2f8f hash 364e7375ecbad327
```

Identical. No table value changed. Worktree removed and pruned.

---

## Scope compliance

- Not touched: `y14_5.py`, `montecarlo.py`, `checker.py`, `types.py`,
  `reliability.py`, `scripts/gate_a.py`, design spec §7.
- `iso286.py` edited for docstring only, plus tests. No value, no logic.
- `spec.py`, `features.py`, `sampler.py`, `layout.py` remain CAD-free
  (`tests/test_architecture.py` passes).
- Deliberately NOT done, per instruction: pinning the 52 IT5–IT8 cells (deferred
  to a pre-freeze follow-up, recorded in the ledger); changing `_MIN_WALL_MM` or
  `_EDGE_MARGIN_MM`; changing any table value; ASME Y14.5 B-5; inventing a
  citation for either the tapped-hole band or the fastener tolerance.

## Concerns

1. **The IT5–IT8 pinning gap is now asymmetric and visible.** All 39 IT12–IT14
   cells are pinned individually; IT5–IT8 have per-value coverage in only a
   handful of bands. A reader comparing the two blocks will notice. This is a
   deliberate deferral, not an oversight, but it should close before the freeze
   rather than after.

2. **The `g`/`h`/`p` accepted set is still coupled to `_IT_MICRONS`'s contents.**
   It is now documented and pinned in both directions, so the next widening will
   be visible in a diff — but it will still be *implicit*. If the published API
   surface matters after the freeze, an explicit allowed-grade declaration per
   letter would make it declarative rather than emergent. Not urgent; noted
   because the freeze is what raises the cost of the implicit form.

3. **Two untraced numbers remain by design**, both now declared and both proved
   inert by structure and by test. Their inertness depends on two facts holding:
   `hole_b`'s size never entering B-4, and the fastener's upper deviation staying
   zero. Both are asserted, and both assertions name what to do if they fail.
