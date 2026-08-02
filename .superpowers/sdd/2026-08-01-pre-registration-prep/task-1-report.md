# Task 1 Report: Drop line-to-line H7/h6, pin the Tier 2 structural fact

Status: **DONE**

Branch: `feat/pre-registration-prep`
Base HEAD before this task: `7ac01ed`
Commit created: `422c21f124ed22866ba8e4fd367806b06247bd87`

## Step 2: initial run (verify red/green shape)

Command: `python -m pytest tests/gen/test_features.py -v -k "line_to_line or verdict_classes or shaft_letter or yield_does_vary"`

```
collected 13 items / 9 deselected / 4 selected

tests/gen/test_features.py::test_no_supported_fit_is_line_to_line FAILED [ 25%]
tests/gen/test_features.py::test_supported_fits_still_contain_both_verdict_classes PASSED [ 50%]
tests/gen/test_features.py::test_iso_fit_verdict_is_fixed_by_the_shaft_letter_at_every_size PASSED [ 75%]
tests/gen/test_features.py::test_iso_fit_yield_does_vary_with_size PASSED [100%]

================================== FAILURES ===================================
____________________ test_no_supported_fit_is_line_to_line ____________________
    ...
>           assert hole.min_size != shaft.max_size, (
                f"{designation} is line-to-line at 20 mm (hole min == shaft max == "
                f"{hole.min_size}); its verdict is decided by sampling noise"
            )
E           AssertionError: H7/h6 is line-to-line at 20 mm (hole min == shaft max == 20.0); its verdict is decided by sampling noise
E           assert 20.0 != 20.0
E            +  where 20.0 = FeatureOfSize(nominal=20.0, lower_dev=0.0, upper_dev=0.021, feature_type=<FeatureType.INTERNAL: 'internal'>, position_tol=0.0).min_size
E            +  and   20.0 = FeatureOfSize(nominal=20.0, lower_dev=-0.013, upper_dev=0.0, feature_type=<FeatureType.EXTERNAL: 'external'>, position_tol=0.0).max_size

=========================== short test summary info ===========================
FAILED tests/gen/test_features.py::test_no_supported_fit_is_line_to_line - As...
================== 1 failed, 3 passed, 9 deselected in 0.19s ==================
```

Exactly the expected shape: 1 FAIL naming `H7/h6` (hole min == shaft max == 20.0), 3 PASS as regression pins. In particular `test_iso_fit_verdict_is_fixed_by_the_shaft_letter_at_every_size` **PASSED**, so the hard-stop condition was not triggered — the structural argument holds and it was safe to proceed.

## Step 3: the change

`SUPPORTED_FITS` in `src/tolcad/gen/features.py` changed from
`("H7/g6", "H7/h6", "H7/k6", "H7/p6")` to `("H7/g6", "H7/k6", "H7/p6")`,
with the full explanatory comment from the brief applied verbatim above the assignment.

## Step 4: post-change run

`python -m pytest tests/gen/test_features.py -v` → **13 passed** (all four new tests plus the existing nine).

Full suite: `python -m pytest -q -m "not slow"` →

```
190 passed, 2 deselected in 23.77s
```

This is consistent with the baseline of 188 passed / 2 deselected: `188 + 4 new tests = 192` total collected, `190 passed + 2 deselected = 192`. Confirmed via `--collect-only`: `190/192 tests collected (2 deselected)`. No regressions.

## Step 4 (mandatory measurement): failure-rate table

Command run verbatim from the brief:

```
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

Result:

| difficulty | fail/total | fail % | reference @ 2c8a8f0 |
|---|---|---|---|
| d1 | 31/159 | 19.5% | 19.5% |
| d2 | 99/301 | 32.9% | 32.9% |
| d3 | 239/452 | 52.9% | 52.9% |
| d4 | 421/609 | 69.1% | 69.1% |

**The table is bit-identical to the reference.** This was checked, not assumed: I confirmed `SUPPORTED_FITS` really is the reduced 3-tuple in the running interpreter (`('H7/g6', 'H7/k6', 'H7/p6')`) before treating the identical numbers as meaningful rather than stale.

Explanation for why no shift occurred despite `rng.choice` now drawing from 3 options instead of 4: in `sampler.py`, `_iso_fit_mate` calls `rng.choice(SUPPORTED_FITS)` (a plain, non-weighted, single-draw choice over a tiny array). NumPy's `Generator.choice` implements this as one bounded-integer draw (Lemire's algorithm) from the underlying PCG64 bit stream; for tiny `n` like 3 or 4 the rejection probability is astronomically small, so the call consumes the same number of raw 64-bit words from the generator with overwhelming probability regardless of whether `n` is 3 or 4. That leaves the RNG state — and therefore every subsequent draw in the same assembly, including the Tier 1 (`floating_fastener`/`fixed_fastener`) mates counted here — bit-for-bit unaffected. The measured identical table across all 200 seeds x 4 difficulties is consistent with this, not a coincidence from a small sample.

Both ladder guard tests in `tests/gen/test_sampler.py` still pass (verified directly, not just inferred from the table match):

```
tests/gen/test_sampler.py::test_tier1_corpus_contains_both_passing_and_failing_mates[1] PASSED
tests/gen/test_sampler.py::test_tier1_corpus_contains_both_passing_and_failing_mates[2] PASSED
tests/gen/test_sampler.py::test_tier1_corpus_contains_both_passing_and_failing_mates[3] PASSED
tests/gen/test_sampler.py::test_tier1_corpus_contains_both_passing_and_failing_mates[4] PASSED
tests/gen/test_sampler.py::test_tier1_failure_rate_rises_monotonically_with_difficulty PASSED
```
(12 passed total in that file.)

No band-widening was needed or performed.

## Step 6: `h6` grep

`grep -rn "h6" tests/ src/` (excluding `__pycache__`) turned up:

- `src/tolcad/gen/features.py:37` — the new explanatory comment (intentional, this task's own text).
- `tests/gen/test_features.py:56` — docstring of the new `test_no_supported_fit_is_line_to_line` (intentional).
- `tests/gen/test_sampler.py:99` and `tests/gen/test_spec.py:41,46,60,77` — construct `MateSpec` directly with `designation="H7/h6"` as an illustrative example of a line-to-line fit, and test sidecar/JSON round-trip and Monte Carlo seed plumbing. These do **not** go through `SUPPORTED_FITS` or `features.iso_fit_mate_features` at all — `MateSpec` and `tolcad.checker.check` never validate `designation` against the generator's supported set, only `features.iso_fit_mate_features` does. These tests already passed in the post-change full-suite run, and the "H7/h6 flips label across seeds" claim in their comments remains true (`iso286.fit_from_designation` still supports the designation; it's simply no longer in the generator's sampled set).
- `tests/test_iso286.py:63,65,147` — test `iso286.fit_from_designation` directly against the ISO 286 standard tables. Entirely independent of `SUPPORTED_FITS`; unaffected by this change.

Nothing was stranded or broken. No fixes were required.

## Commit

```
422c21f124ed22866ba8e4fd367806b06247bd87 fix: drop line-to-line H7/h6, whose label was sampling noise

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

Files changed: `src/tolcad/gen/features.py` (+15/-1), `tests/gen/test_features.py` (+75).

## Self-review

- Diff matches the brief verbatim: the four test functions were appended byte-for-byte as specified, and `SUPPORTED_FITS` plus its comment block match the brief's Step 3 text exactly.
- Scope respected: only `src/tolcad/gen/features.py` and `tests/gen/test_features.py` touched. `y14_5.py`, `montecarlo.py`, `checker.py`, `scripts/gate_a.py`, and design-spec §7 thresholds untouched.
- `features.py` remains CAD-free — no new imports beyond the existing `from tolcad.iso286 import fit_from_designation`.
- Hard stop was correctly evaluated and not triggered (`test_iso_fit_verdict_is_fixed_by_the_shaft_letter_at_every_size` passed both before and after the change).
- Full suite green (190 passed, 2 deselected), count reconciles exactly with baseline + 4 new tests.
- Mandatory measurement step performed and reported honestly, including a mechanistic explanation for why the table came out identical rather than shifted, rather than treating an unexpected non-shift as an error to paper over.
- No band-widening, no threshold edits, no core-module edits.

## Concerns

None. The one item worth flagging for future readers (not a defect): the failure-rate table did not shift as the brief's framing anticipated ("A shift is expected here and must be checked, not assumed away"). I did check it — confirmed the reduced tuple was actually live, re-ran the exact commands, and traced the mechanism (bounded-integer draw over a tiny array consumes a constant number of bit-generator words with overwhelming probability, so removing one entry from a 4-element choice set doesn't perturb the shared RNG stream for downstream draws in the same assembly). This is worth keeping in mind for Task 2 (P35-2) or later tasks that also touch `rng.choice` calls in `sampler.py`: don't assume shrinking/growing a choice tuple will change the sampled corpus just because it consumes a call — it usually won't, for small n.
