# Task 1 Report: Extend `iso286.py` to IT12–IT14

Branch: `feat/iso273-traceability`. Started at HEAD `e8e4a9f` (clean tree,
baseline `python -m pytest -q -m "not slow"` → 218 passed, 2 deselected = 220
total, confirmed before touching anything).

## Step 1–2: RED

Appended the five tests verbatim to `tests/test_iso286.py` (after
`test_it6_band_boundary_is_not_off_by_one`).

Ran: `python -m pytest tests/test_iso286.py -v -k "it12 or new_rows or thousand or untouched"`

Verbatim result (12 failed, 1 passed):

```
tests/test_iso286.py::test_it12_to_it14_are_tabulated FAILED             [  7%]
tests/test_iso286.py::test_it12_to_it14_match_iso286_table_1[4.0-12-0.12] FAILED [ 15%]
tests/test_iso286.py::test_it12_to_it14_match_iso286_table_1[4.0-13-0.18] FAILED [ 23%]
tests/test_iso286.py::test_it12_to_it14_match_iso286_table_1[4.0-14-0.3] FAILED [ 30%]
tests/test_iso286.py::test_it12_to_it14_match_iso286_table_1[8.0-12-0.15] FAILED [ 38%]
tests/test_iso286.py::test_it12_to_it14_match_iso286_table_1[8.0-13-0.22] FAILED [ 46%]
tests/test_iso286.py::test_it12_to_it14_match_iso286_table_1[8.0-14-0.36] FAILED [ 53%]
tests/test_iso286.py::test_it12_to_it14_match_iso286_table_1[14.0-12-0.18] FAILED [ 61%]
tests/test_iso286.py::test_it12_to_it14_match_iso286_table_1[14.0-13-0.27] FAILED [ 69%]
tests/test_iso286.py::test_it12_to_it14_match_iso286_table_1[14.0-14-0.43] FAILED [ 76%]
tests/test_iso286.py::test_the_new_rows_did_not_land_a_thousand_times_too_small FAILED [ 84%]
tests/test_iso286.py::test_new_rows_span_every_size_band FAILED          [ 92%]
tests/test_iso286.py::test_existing_grades_are_untouched PASSED          [100%]

...
E           ValueError: IT grade 12 not tabulated; have [5, 6, 7, 8]
...
E           KeyError: 12
=========================== short test summary info ===========================
12 failed, 1 passed, 23 deselected in 0.11s
```

Matches the brief's expectation exactly: `ValueError: IT grade 12 not tabulated;
have [5, 6, 7, 8]` on the non-parametrized case, and
`test_existing_grades_are_untouched` PASSED on arrival (deliberate regression
pin, not a TDD violation — confirmed).

## Step 3–4: Implementation

- `src/tolcad/iso286.py`: appended the UNIT TRAP comment block and the three
  new rows (12, 13, 14) to `_IT_MICRONS`, verbatim from the brief. Appended
  the TRANSCRIPTION SOURCE paragraph noting the 2026-08-01 addition and the
  unit change, verbatim from the brief.
- `CLAUDE.md`: replaced the blanket "ISO 286 tables publish micrometres"
  convention line with the corrected version noting the IT01–IT11 vs
  IT12–IT18 split, verbatim from the brief.

## Step 5: GREEN

`python -m pytest tests/test_iso286.py -v` → **36 passed** (all prior 31 +
5 new test functions, one parametrized ×9 = 13 new cases total).

Full suite, no marker filter: `python -m pytest -q` → **233 passed**
(220 baseline + 13 new cases, exactly as expected — nothing outside
`iso286.py` consumes grades 12–14 yet, so no other test moved).

## Step 6: Independent sanity check

```
python -c "from tolcad.iso286 import it_grade; print([(g, it_grade(14.0,g)) for g in (8,12,13,14)])"
[(8, 0.027), (12, 0.18), (13, 0.27), (14, 0.43)]
```

Matches the expected `IT8 0.027, IT12 0.18, IT13 0.27, IT14 0.43` mm exactly —
strictly increasing, and IT12 (0.18) an order of magnitude above IT8 (0.027).
This rules out the 1000× unit-trap failure mode the brief warns about.

## Step 7: Diff confirmation — no existing values changed

`git diff -- src/tolcad/iso286.py` (pre-commit) showed only:
- Two new comment/docstring blocks (UNIT TRAP comment above `_IT_MICRONS`,
  TRANSCRIPTION SOURCE paragraph in the module docstring).
- Three new dict entries (`12:`, `13:`, `14:`) appended after the existing
  `8:` row, plus a two-line comment above them.

No `-` (removal) lines appear anywhere touching the `5:`, `6:`, `7:`, or `8:`
rows of `_IT_MICRONS`. **Explicit confirmation: IT5–IT8 are byte-for-byte
unchanged** — every digit in those four rows is identical to HEAD `e8e4a9f`.
`_DEVIATION_MICRONS` and `_SIZE_BANDS` are untouched (not present in the diff
at all).

## Commit

```
git add src/tolcad/iso286.py tests/test_iso286.py CLAUDE.md
git commit -m "feat: tabulate IT12-IT14, noting ISO 286-1 publishes them in mm

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

SHA: **`13e3b970cd5f790505f12fca41cadeb8d2936627`**

3 files changed, 68 insertions(+), 2 deletions(-) — matches expectations
(iso286.py: +19/-0 net after comment/data additions; test file: +45 new
lines; CLAUDE.md: +6/-2 for the one-paragraph replacement).

## Self-review

- Rows transcribed verbatim from the brief; did not re-derive or re-scale
  them myself, per the brief's explicit instruction not to re-scale the
  already-converted figures.
- `test_new_rows_span_every_size_band` passing confirms each new row has
  exactly 13 entries, parallel to `_SIZE_BANDS` — no silent misalignment.
- `_SHAFT_LETTER_GRADE_RANGE`, `_ES_BASED_SHAFT_LETTERS`,
  `_EI_BASED_SHAFT_LETTERS`, and all deviation-letter logic are untouched;
  this task only ever reads `_IT_MICRONS[grade]`, so `fit_from_designation`
  and `fundamental_deviation` behavior for existing grades is unaffected.
  (Grades 12–14 would also work through `fit_from_designation` for shaft
  letters g/h/p since those aren't grade-restricted, but that's an
  incidental side effect, not something this task needed to build or test —
  left as-is per "strictly additive," no new behavior introduced beyond the
  table.)
- No changes to `y14_5.py`, `montecarlo.py`, `checker.py`, `types.py`, or
  `reliability.py` — confirmed by `git status`/`git show --stat`, only the
  three intended files appear in the commit.
- Full-suite count (233) accounts precisely for the baseline (220) plus the
  13 new test cases; no unrelated test count drift.

## Concerns

None. The unit-trap sanity check, the ordering test, and the diff review all
independently confirm the three new rows are in micrometres and correctly
ordered. `git diff` shows a strictly additive change to `iso286.py` with no
existing digits altered.
