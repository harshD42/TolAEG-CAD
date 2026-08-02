# Final fix wave — whole-branch review of `feat/pre-registration-prep`

Base of this wave: `5d04d6f`. Tip: `cb48af4`. Five commits, one logical unit each.
All work landed in a single wave; no second round was needed.

    bcc92e6  test: the fixture's byte-exactness claim is an assertion, not prose      (I-1, M-4)
    f7b28b0  feat: an assembly cannot under-project the zone B-4 assumes              (I-2)
    f7b9599  test: derive the layout floors from the tables they came from            (M-1, M-2)
    bf90b14  test: the ISO-fit disclosure asserts its mechanism, not just its consequence  (M-5)
    cb48af4  docs: note that H7/h6 is still supported but no longer sampled           (P35-1)

## Verification

| Check | Result |
|---|---|
| `python -m pytest -q` (no filter, includes slow) | **220 passed** (was 213 at 5d04d6f; +7) |
| `python scripts/gate_a.py`, exit code captured without a pipe | **exit 1**, `Gate A: NOT CLEARED` |
| Gate A tally | **6 PASS / 3 SKIP** (unchanged) |
| Working tree before each commit | clean |
| Files touched | 9; **no checker-core module** (`types`, `y14_5`, `iso286`, `montecarlo`, `checker`, `reliability`) appears in the diff |
| Deletions in `src/` this wave | 7 lines, all docstring/comment text being rewritten plus one literal replaced by a named constant. No behaviour removed. |

Gate A rows: Y14.5 self-consistency PASS, Monte Carlo convergence PASS, Checker
reliability PASS (mean 0.9982 over 200 pre-registered seeds, 95% bootstrap CI
[0.9964, 0.9995]), Validation isolation PASS, Y14.5 citation verified PASS,
ISO 286 transcription verified PASS; NIST PMI conformance SKIP, TolAnalyst
agreement SKIP, Fresh clone pipeline SKIP.

### Tier 1 failure rate, seeds 0-199

    d1: 19.5%  (n=159)
    d2: 32.9%  (n=301)
    d3: 52.9%  (n=452)
    d4: 69.1%  (n=609)

Bit-identical to the reference (19.5 / 32.9 / 52.9 / 69.1). Nothing in this wave
moved it, as expected. The corpus itself is byte-identical too: SHA-256 over the
concatenated sidecar JSON for seeds 0-199 x d1-4 is `f88582e12117a947…`, which is
the check that matters after `_ISO_FIT_NOMINALS_MM` replaced an inline tuple in
`rng.choice` (same tuple, same RNG stream).

### Fixture integrity

    tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp   396445 bytes  85a5752da05f53c4…
    data/nist_pmi/nist_ctc_01_asme1_ap242-e1.stp    396445 bytes  85a5752da05f53c4…
    git cat-file -s HEAD:tests/fixtures/…            396445

Both present, both unmodified, committed blob still correct. The ~14 MB NIST
suite stays gitignored; still exactly one fixture committed.

---

## I-1 — the fixture's byte-exactness claim now has something that can fail

`tests/test_ap242_pmi.py` gains `assert_is_the_nist_original(path)`, which asserts
the exact size `396_445` **and** the SHA-256
`85a5752da05f53c456ca3a9e038c90358e1d5a3141d1f0d6e5f0970f2356e821`. It is called
from a dedicated integrity test and from the positive control itself, so the
counts are never read from a file that has not first been shown to be the NIST
original. The hash is recorded in `NIST-PROVENANCE.md` beside the byte count,
with a note that the reader returns the same 21/6/11 counts from the mangled
copy and therefore cannot detect corruption on its own.

One structural change beyond the letter of the finding: the OCP gate moved from
a module-level `pytest.importorskip` to a per-test `needs_ocp` marker. The
integrity claim is about the repository, not about the CAD toolkit, and a guard
that a missing optional dependency silently switches off is the same defect
class the finding is about. The four PMI-reading tests are unchanged in
substance; each carries `@needs_ocp`.

### Mutation demonstration (verbatim)

A throwaway `tests/test_zz_mutation_demo.py` built the CRLF→LF copy in
`tmp_path` (the real fixture untouched) and pointed the assertions at it. It was
deleted after the run.

    tests/test_zz_mutation_demo.py::test_mangled_copy_is_rejected
    mangled copy is 391739 bytes
    FAILED
    tests/test_zz_mutation_demo.py::test_same_size_byte_flip_is_rejected_by_the_hash
    flipped copy is 396445 bytes (same size)
    FAILED
    tests/test_zz_mutation_demo.py::test_real_fixture_is_accepted PASSED

    E   AssertionError: nist_ctc_01_asme1_ap242-e1.stp is 391739 bytes, not the
        396445 bytes NIST-PROVENANCE.md claims. A 391,739-byte file is the known
        CRLF->LF corruption: check that .gitattributes still marks *.stp binary
        and that no later rule overrides it.
        assert 391739 == 396445

    E   AssertionError: flipped.stp hashes to
        50314ba86d83334c8d4e0541c94174fc7f7f1e282c29ab0ae3909deb074f86f7, not the
        85a5752da05f53c456ca3a9e038c90358e1d5a3141d1f0d6e5f0970f2356e821 recorded
        in NIST-PROVENANCE.md. The file is not the NIST original.

    ========================= 2 failed, 1 passed in 0.49s =========================

The second case is not in the brief; it was added because a size assertion that
runs first can shadow a hash assertion that is never reached. Flipping one bit
in the last-but-one byte keeps the size identical and proves the hash line is
live.

## I-2 — `AssemblySpec` rejects an under-projected zone

`AssemblySpec.__post_init__` now walks the mates and raises for any
`fixed_fastener` whose `projected_zone_mm < plate_thickness_mm`, with an error
that names B-4, the OPTIMISTIC/unsafe wording from `y14_5.py`, and the
unimplemented B-5. The reported construction is now rejected:

    REJECTED: mate 0: projected_zone_mm 8.0 is shorter than plate_thickness_mm
    25.0. ASME Y14.5 B-4 -- the formula y14_5.fastener_assembles applies to a
    fixed fastener -- assumes the zone is projected through the whole part the
    fastener crosses. Under-projected, its margin is OPTIMISTIC (unsafe); the
    non-projected case is B-5, which tolcad does not implement.

Five tests in `tests/gen/test_spec.py`: the rejection; the valid **equal** case
(what the sampler emits, and it also round-trips through JSON); over-projection
allowed, since projecting further than the plate is conservative; the guard not
firing on non-fixed kinds, which carry no zone; and a sweep over seeds 0-24 ×
d1-4 asserting every sampled fixed mate satisfies the precondition. Nothing in
the shipped corpus changed — the sampler already wired both sides from
`_PLATE_THICKNESS_MM`. What changed is the schema being frozen.

## M-1 — the layout floors are tied to the ladder they came from

`test_the_margin_constants_still_cover_the_tables_they_came_from` computes
`_worst_case_radial_excursion_mm()` from `clearance_hole_for` over
`FASTENER_SIZES` (largest hole-MMC-minus-fastener allowable, and the largest
`upper_dev`) and `sampler._TOL_FRACTION_RANGE` (largest `hi`), then compares
`2 ×` it against `_MIN_WALL_MM` and `1 ×` it against `_EDGE_MARGIN_MM`. Today
that is 1.775 mm → 3.55 mm required wall against a 4.0 mm constant.

Still a cross-module comparison — features + sampler vs layout — so it does not
reintroduce the self-reference Task 5 removed. The 3.7 / 1.85 literal assertions
are kept unchanged as a cruder second floor.

### Mutation demonstration (verbatim)

`_TOL_FRACTION_RANGE[4]` temporarily raised from `(0.72, 1.34)` to `(0.72, 1.70)`:

    .......F.                                                                [100%]
    _______ test_the_margin_constants_still_cover_the_tables_they_came_from _______
    tests\gen\test_layout.py:115: in test_the_margin_constants_still_cover_the_tables_they_came_from
        assert _MIN_WALL_MM >= required_wall - 1e-9, (
    E   AssertionError: _MIN_WALL_MM 4.0 is below the 4.45 mm the clearance table
        and the difficulty ladder now demand between two features leaning toward
        each other
    E   assert 4.0 >= (4.45 - 1e-09)
    1 failed, 8 passed in 0.14s

4.45 mm exactly as the finding predicted, and the eight other layout tests —
including both literal floors — passed, which is the contrast that justifies the
new one.

**One correction to the finding's premise.** It said the 1.7 mutation leaves
"every test in the repo still passing". It does not: with the new test
deselected, the rest of the suite gives

    FAILED tests/gen/test_sampler.py::test_tier1_failure_rate_rises_monotonically_with_difficulty
    1 failed, 216 passed, 3 deselected

`test_sampler.py:87` pins the d4 Tier 1 failure rate to `0.60 <= r <= 0.80` and a
1.7 ceiling pushes it out of the band. So the ladder was not entirely unguarded
— but that guard is about *label balance*, not about *geometry*, and it would not
notice a widened `_CLEARANCE_HOLE_MM`, which reaches the wall by the other term
of the same product. The finding's conclusion stands; only its "every test"
clause was too strong.

The mutation was reverted with `git checkout -- src/tolcad/gen/sampler.py` and
`_TOL_FRACTION_RANGE[4]` re-confirmed as `(0.72, 1.34)` before anything was
committed.

## M-2 — the docstring arithmetic reconciles

Both `layout.py`'s module docstring and the test's now carry the exact chain:
allowable 2.5 mm diametral × 1.34 = 3.35 mm applied, ÷ 2 = **1.675 mm** radial
axis offset, + 0.1 mm radius growth = **1.775 mm** per feature, **3.55 mm** for
two neighbours. `layout.py`'s stale "~1.4x" is now 1.34. The test docstring
states that the 3.7 / 1.85 literals are the original figures computed with the
axis offset rounded up to 1.75, kept *because* they are looser than the exact
3.55 / 1.775.

The false claim "the widest feature is Ø14.5" is replaced in both places by the
true one: `feature_radii_mm` lays an `iso_fit` mate out at `nominal/2` and the
sampler draws up to Ø25, so **Ø25 is the widest feature on a plate**. It does not
enter the derivation because it carries `position_tol` 0.0 and an IT7-class band
(~0.021 mm at 25 mm, ~0.01 mm on the radius). The binding case is the widest
feature that carries a *position tolerance*, which is the M12 loose clearance
hole. No constant changed.

## M-4 — `.gitattributes` scope

Added `*.STP`, `*.step`, `*.STEP` beside the existing `*.stp`, with a comment
noting that patterns are case-sensitive and that `gen/export.py` writes `.step`.

## M-5 — the ISO-fit disclosure tests are exact

(a) `test_iso_fit_verdict_is_fixed_by_the_shaft_letter_at_every_size` now reads
the shaft from `tolcad.iso286.fit_from_designation` at each size and asserts
`assembles == (shaft.upper_dev <= 0.0)`, the mechanism, in addition to the
existing constant-across-diameters assertion. Both branches are live: g6 has
es < 0 at every tested nominal (−0.004 … −0.012), k6 and p6 have es > 0
(+0.009 … +0.059).

(b) The nominals are now `sorted({6.0, 50.0, 120.0} ∪ _ISO_FIT_NOMINALS_MM)` =
(6, 10, 12, 16, 20, 25, 50, 120), with a guard asserting 12 and 16 are present
so the ISO band 10 < d ≤ 18 cannot silently drop out. The sampler's nominal set
became a named constant `_ISO_FIT_NOMINALS_MM` that the test imports, so the two
cannot drift — the same decoupling defect M-1 is about. `rng.choice` receives
the identical tuple, and the corpus digest above confirms the RNG stream is
unperturbed.

## P35-1 — the `mc_seed` rationale is current

The comment keeps H7/h6 as the motivating example (it is still why the field
exists) and gains a clause: H7/h6 left `features.SUPPORTED_FITS` in commit
422c21f, is no longer sampled, but is still supported by
`iso286.fit_from_designation`, so a hand-written spec can name it and the
general point holds for any fit whose worst-case clearance lands near zero.

---

## Concerns

1. **The `.gitattributes` rule itself is still untested, by construction.** The
   integrity assertion is what notices a corrupted blob, and that is the right
   place for it — but the notice arrives at test time on a machine that has
   already cloned. A CI job that clones with `core.autocrlf=true` and runs
   `pytest tests/test_ap242_pmi.py` is the only thing that closes the loop
   before a user hits it. Gate A's "Fresh clone pipeline" row is already SKIP
   with the reason "requires a clean-clone CI run to verify honestly"; this is
   one more thing that row would cover.
2. **`plate_thickness_mm` is a single scalar for both plates.** The B-4
   precondition I-2 enforces is about the thickness of the part the fastener
   *crosses*, which today is `part_a` and today equals `plate_thickness_mm`. If
   the geometry ever grows per-part thicknesses, the guard must follow the
   crossed part, not the assembly-wide scalar. Worth a line in the frozen schema
   documentation.
3. **The M-1 floor is derived from the *floating* worst case.** The fixed case
   halves the allowable, so floating binds — but that is an argument recorded in
   a docstring, not an assertion. If `_tier1_mate` ever stops halving, the
   derived floor silently becomes the wrong one. Low risk; noted rather than
   fixed, because fixing it means the test re-implementing `_tier1_mate`.
4. **Nothing else in this wave is deferred.** All seven items are closed.
