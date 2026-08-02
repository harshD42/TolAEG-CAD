# Task 3 report: Record the projected tolerance zone the B-4 verdict assumes

## Commit
`164e83a638909f19ea55d55cddb676bc67ed25be` — "feat: record the projected tolerance zone B-4 assumes"
(4 files changed, 122 insertions(+))

## Step 1-2: RED

Appended the four tests verbatim to `tests/gen/test_spec.py` and the two tests verbatim to
`tests/gen/test_sampler.py`, then ran:

```
python -m pytest tests/gen/test_spec.py tests/gen/test_sampler.py -v -k "projected"
```

Output (verbatim, trimmed to summary + failure headers):

```
collected 35 items / 29 deselected / 6 selected

tests/gen/test_spec.py::test_fixed_fastener_requires_a_projected_zone FAILED [ 16%]
tests/gen/test_spec.py::test_projected_zone_must_be_positive FAILED      [ 33%]
tests/gen/test_spec.py::test_non_fixed_kinds_must_not_carry_a_projected_zone FAILED [ 50%]
tests/gen/test_spec.py::test_projected_zone_is_not_sent_to_the_checker FAILED [ 66%]
tests/gen/test_sampler.py::test_every_sampled_fixed_fastener_records_its_projected_zone FAILED [ 83%]
tests/gen/test_sampler.py::test_projected_zone_survives_the_sidecar_round_trip PASSED [100%]

FAILURES:
test_fixed_fastener_requires_a_projected_zone
    E       Failed: DID NOT RAISE <class 'ValueError'>

test_projected_zone_must_be_positive
    E           TypeError: MateSpec.__init__() got an unexpected keyword argument 'projected_zone_mm'

test_non_fixed_kinds_must_not_carry_a_projected_zone
    E           TypeError: MateSpec.__init__() got an unexpected keyword argument 'projected_zone_mm'

test_projected_zone_is_not_sent_to_the_checker
    E       TypeError: MateSpec.__init__() got an unexpected keyword argument 'projected_zone_mm'

test_every_sampled_fixed_fastener_records_its_projected_zone
    E                       AttributeError: 'MateSpec' object has no attribute 'projected_zone_mm'

5 failed, 1 passed, 29 deselected in 0.15s
```

Note: `test_projected_zone_survives_the_sidecar_round_trip` passed trivially at this stage — it
only asserts a round trip is lossless, which held vacuously since the field didn't exist yet on
either side of the round trip. This is consistent with the brief's expected failure set (it did
not list this test among the expected failures).

## Step 3: Implementation

Applied exactly what the brief specified, verbatim, no deviation:
- `src/tolcad/gen/spec.py`: added `projected_zone_mm: float | None = None` immediately after
  `mc_n`, with the full explanatory comment from the brief; replaced the `__post_init__` body
  after the `mc_n` check with the brief's validation (kind-not-in-VALID_KINDS check, the
  non-fixed-kind-must-not-carry-a-zone check, then the existing branch structure with the new
  fixed_fastener positive-zone guard added inside the `else` branch).
- `src/tolcad/gen/sampler.py`: added `_PLATE_THICKNESS_MM = 8.0` next to `_MC_SAMPLES`; wired
  `projected_zone_mm=(_PLATE_THICKNESS_MM if kind == "fixed_fastener" else None)` into
  `_tier1_mate`'s returned `MateSpec`; set `plate_thickness_mm=_PLATE_THICKNESS_MM` explicitly in
  the `AssemblySpec(...)` construction at the end of `sample_assembly`.
- `to_check_dict()` in `spec.py` was left untouched — it already only emits `type`,
  `hole_a`/`hole_b`/`fastener` (Tier 1) or `type`/`nominal`/`designation`/`seed`/`n` (iso_fit), so
  `projected_zone_mm` was never at risk of being emitted; the new test
  `test_projected_zone_is_not_sent_to_the_checker` confirms this by construction.
- `src/tolcad/y14_5.py` was not touched.

## Step 4: GREEN

```
python -m pytest tests/gen/test_spec.py tests/gen/test_sampler.py -v
```

All 6 new tests passed. One pre-existing test failed as an expected side effect:

```
tests/gen/test_spec.py::test_fixed_fastener_mate_round_trip FAILED
  E ValueError: fixed_fastener requires a positive projected_zone_mm: y14_5 implements
    ASME Y14.5 B-4, which assumes a projected tolerance zone, and is optimistic without
    one. Got None

1 failed, 34 passed in 0.65s
```

## Step 5: Existing fixtures updated

Ran `grep -rn "fixed_fastener" tests/` (see below). Only two existing `MateSpec(kind=
"fixed_fastener", ...)` constructions needed `projected_zone_mm=8.0` added — both in
`tests/gen/test_spec.py`:

1. `test_fixed_fastener_mate_round_trip` (was failing per above) — added
   `projected_zone_mm=8.0`. This is the fixture the new validation actually broke.
2. `test_fixed_fastener_rejects_missing_hole_a` — added `projected_zone_mm=8.0` for schema
   consistency, even though this test technically still passed either way: the `hole_a is None`
   check in the `else` branch fires before the new positive-zone check, so its
   `pytest.raises(ValueError, match="hole_a")` was satisfied regardless. Updated anyway so the
   fixture reads as a realistic fixed_fastener mate rather than one that happens to fail for two
   independent reasons.

`grep -rn "fixed_fastener" tests/` also matched:
- `tests/test_y14_5.py` (`fixed_fastener_tolerance` function name, `test_fixed_fastener_is_stricter_than_floating`) — these call `y14_5.fixed_fastener_tolerance` directly, not `MateSpec`, so nothing to change.
- `tests/gen/test_sampler.py` — matches are all against `mate.kind == "fixed_fastener"` on
  sampler-produced mates (already carrying the field via the sampler wiring) or are the two new
  tests just added; no fixture edits needed there.

No fixture was switched from `fixed_fastener` to `floating_fastener` to dodge validation — both
touched fixtures remain `fixed_fastener`.

Re-ran `tests/gen/test_spec.py tests/gen/test_sampler.py -v`: **35 passed**.

## Full suite

```
python -m pytest -q -m "not slow"
```

Result: **208 passed, 2 deselected** (baseline at HEAD was 202 passed, 2 deselected; the 6 new
tests account for the delta exactly — no other test count changed).

## Gate A

```
python scripts/gate_a.py
```

Exit code: **1** (expected)

Tally:
```
PASS  Y14.5 self-consistency
PASS  Monte Carlo convergence
PASS  Checker reliability
PASS  Validation isolation
PASS  Y14.5 citation verified
PASS  ISO 286 transcription verified
SKIP  NIST PMI conformance
SKIP  TolAnalyst agreement
SKIP  Fresh clone pipeline
```
6 PASS / 3 SKIP — matches expectation. "Gate A: NOT CLEARED" (by design, due to the SKIPs).

## Tier 1 failure-rate sweep, seeds 0-199

Computed directly (Tier 1 mates only, iso_fit excluded), same method as
`_tier1_verdicts` in `tests/gen/test_sampler.py`:

| difficulty | failure rate | n   |
|-----------:|--------------:|----:|
| d1         | 19.5%         | 159 |
| d2         | 32.9%         | 301 |
| d3         | 52.9%         | 452 |
| d4         | 69.1%         | 609 |

Matches the reference exactly (d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%) — **the table did not
move**. Expected: this task only adds metadata (`projected_zone_mm`) recording an assumption
already true of the generated geometry; it changes no sampling distribution, no tolerance
fraction, and no pass/fail geometry, so the Tier 1 assemble/fail rates are identical to before
this task.

## Self-review

- Diff matches the brief's prescribed code verbatim: field placement (right after `mc_n`,
  defaults follow non-default fields as required by the frozen dataclass), comment text,
  `__post_init__` replacement (kept the `mc_n` check, added the two new checks, preserved the
  existing three-way kind branch structure with one guard added inside the `else` branch),
  sampler constant, `_tier1_mate` wiring, and the explicit `plate_thickness_mm` in
  `sample_assembly`'s `AssemblySpec(...)`.
- Confirmed via `git diff --stat` that `src/tolcad/y14_5.py` and `scripts/gate_a.py` have zero
  changes.
- Confirmed `to_check_dict()` was not modified and does not reference `projected_zone_mm`
  anywhere — `test_projected_zone_is_not_sent_to_the_checker` pins this both by asserting the key
  is absent from the dict and by asserting the checker still returns `assembles is True` for a
  geometrically-valid mate that carries the field only in the spec layer.
- `spec.py` and `sampler.py` remain CAD-free (no new imports were added; `sampler.py`'s only new
  top-level artifact is the `_PLATE_THICKNESS_MM` float constant).
- All dimensions remain float millimetres; no µm conversion was introduced (none needed).
- Fixture audit: exactly 2 existing `MateSpec(kind="fixed_fastener", ...)` call sites needed
  `projected_zone_mm=8.0` added (both in `tests/gen/test_spec.py`); none were converted to
  `floating_fastener`.

## Concerns

- None outstanding. The `test_fixed_fastener_rejects_missing_hole_a` fixture didn't strictly
  *need* the new argument to keep passing (a different `ValueError` fires first), but adding it
  keeps the fixture representative of a realistic fixed_fastener mate rather than one that
  incidentally fails for an unrelated reason — flagged above for transparency rather than left
  silent.
- Gate A's "NOT CLEARED" status and the three SKIPs are pre-existing and out of scope for this
  task (no export files for NIST PMI / TolAnalyst comparisons, and no fresh-clone CI run in this
  session) — unchanged by this task, as expected.
