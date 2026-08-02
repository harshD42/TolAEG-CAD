# Fix round report — F-1/F-2/F-3 (documentation-and-test consistency)

Branch: `feat/iso273-traceability`. Starting HEAD: d78c39e. Commit range: `d78c39e..3125513`.

## Status

All three findings fixed, committed in three logical units, no out-of-scope files touched.

## Commits

- `f6300b3` — fix: reconcile iso286 opening summary with the mm/um table split (F-1)
- `3652d60` — test: pin all 39 IT12-IT14 cells against ISO 286-1 Table 1 (F-2)
- `3125513` — fix: correct stale tapping-drill caveat, guard case-insensitively (F-3)

## F-1 — `src/tolcad/iso286.py` opening summary

Reworded the module docstring's opening two lines so they are true of both
grade ranges (IT01-IT11 in micrometres, IT12-IT18 in millimetres, both
converted to micrometres on entry into `_IT_MICRONS`), instead of the blanket
"Published in micrometres" claim that contradicted the TRANSCRIPTION SOURCE
paragraph four lines below. No value or logic changed — confirmed by diff
(docstring lines only).

## F-2 — 39-cell verification

Added `test_all_39_it12_to_it14_cells_match_iso286_table_1` to
`tests/test_iso286.py`, parametrized over all 13 size bands using probe
diameters strictly inside each band (2, 4, 8, 14, 25, 40, 65, 100, 150, 200,
300, 350, 450), pinning all 3 x 13 = 39 published ISO 286-1:2010 Table 1
millimetre values against `it_grade`. Assertion messages name the grade and
band index for diagnosability.

**Mutation demonstration:** temporarily swapped the adjacent IT13 values at
band indices 5 and 6 (0.39 and 0.46, i.e. `_IT_MICRONS[13]` entries 390/460)
in `src/tolcad/iso286.py`. Result:

```
FAILED tests/test_iso286.py::test_all_39_it12_to_it14_cells_match_iso286_table_1[5-40]
FAILED tests/test_iso286.py::test_all_39_it12_to_it14_cells_match_iso286_table_1[6-65]
AssertionError: IT13 at size band index 5 (_SIZE_BANDS upper bound, probe 40 mm): expected 0.39 mm, got 0.46 mm
AssertionError: IT13 at size band index 6 (_SIZE_BANDS upper bound, probe 65 mm): expected 0.46 mm, got 0.39 mm
2 failed, 47 passed in 0.08s
```

All other tests in the file — including the length check and the
`IT8 < IT12 < IT13 < IT14` ordering check — still passed, confirming the new
test is the only one that catches this class of corruption. Reverted the
swap; `pytest tests/test_iso286.py -q` returned `49 passed`.

## F-3 — stale tapping-drill caveat and case-sensitive guard

(a) Rewrote the comment above `TAPPING_DRILL_MM` in `src/tolcad/gen/features.py`
to state the ISO 2306-1972 Table 1 verification (matching the module
docstring), keeping the still-true note that M8->6.8 and M12->10.2 come from
the ISO/R 235 preferred drill series rather than nominal-minus-pitch.

(b) Made `test_features_module_cites_its_primary_sources`'s regression guard
case-insensitive (`text.lower()`).

**Mutation demonstration:** temporarily reinstated a line containing
`"have NOT been checked against the primary standard"` in
`src/tolcad/gen/features.py`. With the fixed (case-insensitive) assertion:

```
FAILED tests/gen/test_features.py::test_features_module_cites_its_primary_sources
AssertionError: ... 'not been checked against the primary' is contained here: ...
1 failed, 33 deselected in 0.08s
```

Confirmed separately (via a standalone check of the original case-sensitive
substring test against the same mutated file) that the pre-fix assertion
would have returned `True` (i.e. passed, missing the stale caveat) —
demonstrating the guard was case-sensitive-evadable before this fix. Reverted
the mutation; `pytest tests/gen/test_features.py -q` returned `34 passed`.

## Verification

1. `python -m pytest -q` (no marker filter): **257 passed** (baseline 244 + 13
   new parametrized cases from the F-2 test).
2. `python scripts/gate_a.py > /dev/null 2>&1; echo $?` (exit code captured
   without piping): **1**. Full report: 6 PASS / 3 SKIP (NIST PMI conformance,
   TolAnalyst agreement, Fresh clone pipeline all SKIP as expected).
3. Tier 1 ladder, seeds 0-199, re-measured:
   d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1% — unchanged from the reference,
   as expected since this round touched only documentation and tests.
4. Both mutation demonstrations above, with verbatim output; both reverted
   and confirmed green afterward.
5. `git diff --stat d78c39e..HEAD` touches exactly:
   `src/tolcad/iso286.py`, `tests/test_iso286.py`,
   `src/tolcad/gen/features.py`, `tests/gen/test_features.py`. No other file
   changed.

## Concerns

None. All three fixes are additive/corrective to documentation and test
coverage; no production value, threshold, or checker-core logic changed.
Task 3 (re-measuring the layout floors) remains outstanding per the ledger
and was correctly left untouched — out of scope for this fix round.
