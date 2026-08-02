# Final fix wave — C1, I3, C2(a), C2(b), I1

Branch: `feat/procedural-generator`
Base of this wave: `b6f89b7`
Head after this wave: `1098ca1`
Commit range: `b6f89b7..1098ca1` (three commits)

| SHA | Findings | Subject |
|---|---|---|
| `9d198a8` | C1, I3 | drill features at absolute positions on a plate sized to hold them |
| `a6412fa` | C2(a), C2(b) | every difficulty straddles the allowable, and the guard test can see it |
| `1098ca1` | I1 | iso_fit mates carry an explicit Monte Carlo seed and sample count |

Status: **all five findings addressed.** Out-of-scope items (I2, I4, I5, the seven
minors) untouched.

---

## 1. Verification

| Check | At `b6f89b7` | At `1098ca1` |
|---|---|---|
| `python -m pytest -q -m "not slow"` | 155 passed, 2 deselected | **186 passed, 2 deselected** |
| `python -m pytest -q` (incl. slow) | — | **188 passed** |
| `python scripts/gate_a.py` | exit 1, 6 PASS / 3 SKIP | **exit 1, 6 PASS / 3 SKIP — unchanged** |
| `data/nist_pmi/nist_ftc_06_asme1_ap242-e2.stp` | present | **present, 1 971 192 bytes, untouched** |
| Payload staged? | no | **no; `git status` clean, `data/nist_pmi/` still gitignored** |

Gate A output is byte-identical to the baseline: the same six PASS lines
(Y14.5 self-consistency, Monte Carlo convergence, checker reliability 0.9982,
validation isolation, Y14.5 citation, ISO 286 transcription) and the same three
SKIP lines (NIST PMI conformance, TolAnalyst agreement, fresh-clone pipeline).
NOT CLEARED, correct by design at this phase.

Net test delta +31: +15 in `tests/gen/test_build.py`, +7 new
`tests/gen/test_layout.py`, +6 in `tests/gen/test_sampler.py`, +3 in
`tests/gen/test_spec.py`.

### Global constraints re-checked

- All dimensions millimetres, float. `layout.py` does no unit conversion;
  ISO 286 µm→mm still happens only at the table boundary in `iso286.py`.
- Checker core still CAD-free: `tests/test_architecture.py` passes unmodified.
  `layout.py` lives in `tolcad.gen`, is imported by `sampler.py` and `build.py`,
  and imports nothing but `collections.abc`. `spec.py`, `features.py`,
  `sampler.py` and the new `layout.py` are all CAD-free.
- `validation/` untouched; core still never imports it.
- Tier 1 still exact: no rounding was added to any margin path. The 4-dp
  rounding in the sampler is on the *input* position tolerance, as before, and
  `layout.py` rounds only plate/pitch geometry.
- Spec §7 thresholds and `scripts/gate_a.py` untouched.
- No corpus generated. The largest batch inside a test is 50 seeds × 4
  difficulties built in memory (`test_features_are_contained_and_disjoint_...`),
  nothing written to disk.

### One pre-existing test changed, and why

`tests/gen/test_build.py::test_drilling_holes_removes_material` compared the
*total* volume of a d4 assembly against a d1 assembly. That only ever expressed
"drilling removes material" because the plate was a fixed 40 mm. With I3 the
plate is sized per assembly, so a four-mate plate is physically bigger than a
one-mate plate and its total volume is legitimately larger — the old assertion
became false for a reason that has nothing to do with the property it was
guarding. It now compares volume *removed* from each assembly's own undrilled
plates, and additionally asserts the one-mate case removed anything at all.
That is strictly stronger than the original, not weaker.

---

## 2. C1 — holes landed at cumulative, not absolute, positions

`src/tolcad/gen/build.py`.

Reproduced independently before touching anything:

```
OLD .faces('>Z').workplane().center(x,0):
  requested x: [-12.0, 0.0, 12.0]
  actual cylindrical-face centres: [-12.0, 0.0]
NEW pushPoints + CenterOfBoundBox:
  actual cylindrical-face centres: [-12.0, 0.0, 12.0]
```

Fix: features are collected into `(x, diameter, depth)` operations, grouped by
`(diameter, depth)`, and cut with
`.faces(">Z").workplane(centerOption="CenterOfBoundBox").pushPoints(points)`.
`pushPoints` takes absolute coordinates on that workplane, and
`CenterOfBoundBox` pins the workplane origin to the plate centre instead of
inheriting the previous feature's origin. Applied to `part_a`, `part_b` and the
`iso_fit` blind-bore path, which all now go through the same `_drill` helper.
Grouping is insertion-ordered, so the build stays deterministic.

Three new assertions, as required:

1. `test_features_land_at_the_absolute_positions_the_layout_specifies` — the
   sorted set of cylindrical-face centre x-coordinates, rounded to 6 dp, equals
   `feature_positions_mm(...)` restricted to the tier-1 subset for `part_a` and
   to all mates for `part_b`.
2. `test_every_feature_that_should_be_drilled_exists` — cylindrical-face count
   equals the number of tier-1 mates (`part_a`) and the number of mates
   (`part_b`).
3. `test_features_are_contained_and_disjoint_across_the_seed_sweep` — over
   seeds 0-49 at every difficulty, the volume removed from each plate equals
   `Σ π r² depth` exactly. Overhang clips a cylinder, overlap double-counts
   shared material, and a dropped feature removes nothing; all three make the
   measured removal strictly *less* than the ideal sum. Equality is therefore
   containment and disjointness in one number, and it is one-sided so it cannot
   be satisfied by accident.

Plus `test_a_plate_too_small_for_its_features_is_rejected`: `build_assembly`
now raises rather than exporting a clipped hole, because
`AssemblySpec.plate_size_mm` still has a 40.0 default that a caller could take.

### C1 mutation demonstration

`_drill` reverted to the original relative-workplane chain
(`part.faces(">Z").workplane().center(x, 0.0)` per feature), everything else
left at the fixed state. Verbatim:

```
E       assert [-24.0, -18.0, 0.0] == [-18.0, -6.0, 6.0, 18.0]
E
E         At index 0 diff: -24.0 != -18.0
E         Right contains one more item: 18.0
E         Use -v to get more diff

tests\gen\test_build.py:110: AssertionError
```

```
E           AssertionError: seed 0 d4: part_a features clipped, merged or missing
E           assert 411.4229739141192 == 556.1875633915371 ± 5.6e-07
E
E             comparison failed
E             Obtained: 411.4229739141192
E             Expected: 556.1875633915371 ± 5.6e-07
```

```
=========================== short test summary info ===========================
FAILED tests/gen/test_build.py::test_features_land_at_the_absolute_positions_the_layout_specifies[0-4]
FAILED tests/gen/test_build.py::test_features_land_at_the_absolute_positions_the_layout_specifies[1-3]
FAILED tests/gen/test_build.py::test_features_land_at_the_absolute_positions_the_layout_specifies[2-4]
FAILED tests/gen/test_build.py::test_features_land_at_the_absolute_positions_the_layout_specifies[7-2]
FAILED tests/gen/test_build.py::test_features_land_at_the_absolute_positions_the_layout_specifies[13-4]
FAILED tests/gen/test_build.py::test_every_feature_that_should_be_drilled_exists[0-4]
FAILED tests/gen/test_build.py::test_every_feature_that_should_be_drilled_exists[1-3]
FAILED tests/gen/test_build.py::test_features_are_contained_and_disjoint_across_the_seed_sweep[2]
FAILED tests/gen/test_build.py::test_features_are_contained_and_disjoint_across_the_seed_sweep[3]
FAILED tests/gen/test_build.py::test_features_are_contained_and_disjoint_across_the_seed_sweep[4]
10 failed, 9 passed in 3.16s
```

Fix restored, `tests/gen/test_build.py` back to `19 passed`.

---

## 3. I3 — plate and pitch derived from the sampled radii

New CAD-free module `src/tolcad/gen/layout.py`, shared by `sampler.py` (which
records the derived plate size on the spec) and `build.py` (which drills at the
derived positions). One source of arithmetic, so the STEP and its sidecar
cannot disagree about the layout.

- `feature_radii_mm(mates)` — per mate, the radius of the largest thing drilled
  at that station: `max(hole_a, hole_b)/2` for Tier 1, `nominal/2` for
  `iso_fit`.
- `feature_pitch_mm(radii)` — `max over adjacent pairs (r_i + r_{i+1}) +
  _MIN_WALL_MM`, floored at the historical 12.0 mm.
- `minimum_plate_size_mm(radii)` — `2 × (max(|x_i| + r_i) + _EDGE_MARGIN_MM)`,
  floored at the historical 40.0 mm.

**Margins chosen, and why.** `_MIN_WALL_MM = 4.0`, `_EDGE_MARGIN_MM = 5.0`.
The sampler's largest allowable position tolerance is
(14.5 − 12.0) = 2.5 mm diametral, and the new ladder applies at most ~1.34× of
it, so a feature's axis can sit up to ~1.7 mm off nominal in any direction; the
hole can also grow by `upper_dev` (+0.2 mm diameter, +0.1 mm radius). Two
neighbours leaning toward each other therefore consume at worst
1.7 + 1.7 + 0.1 + 0.1 ≈ 3.7 mm, so 4.0 mm of nominal material still leaves a
ligament. A single feature leaning at an edge consumes at worst ≈1.85 mm, so
5.0 mm leaves about 2.7× headroom. Both floors mean this change can only ever
make geometry roomier than before, never tighter. Resulting plate sizes over
seeds 0-49 × d1-4 range from 40.0 mm to 108.5 mm.

`plate_size_mm` and `plate_thickness_mm` remain `AssemblySpec` fields with
defaults and are still serialised; the sampler now sets `plate_size_mm`
per assembly. `plate_thickness_mm` is unchanged at 8.0.

The proof that this works is C1's containment/non-intersection test, which
**passes for all seeds 0-49 × difficulty 1-4** (not a sample), plus
`test_sampler_records_a_plate_big_enough_for_its_own_features` over the same
sweep and the derivation tests in `tests/gen/test_layout.py`.

Note the two findings are genuinely coupled: with C1 fixed and I3 not, the
containment test fails at d2, d3 and d4 (the reviewer measured 195/200 d4 seeds
overhanging). With I3 fixed and C1 not, it fails too. Both are needed.

---

## 4. C2(a) — the guard test now looks at Tier 1

`test_corpus_contains_both_passing_and_failing_mates` ran at a single
difficulty and pooled both tiers, so both of its assertions were satisfied
entirely by `iso_fit` mates. It was orthogonal to the Tier 1 sampler it named
in its docstring.

Replaced by two tests in `tests/gen/test_sampler.py`:

- `test_tier1_corpus_contains_both_passing_and_failing_mates`, parametrised
  over difficulties 1-4, filtering `m.kind != "iso_fit"`, asserting the Tier 1
  subset is non-empty and contains both classes **at every level**, not merely
  in the corpus as a whole.
- `test_tier1_failure_rate_rises_monotonically_with_difficulty`, asserting the
  rate is *strictly* increasing, plus band checks on the two ends
  (0.10 ≤ d1 ≤ 0.30, 0.60 ≤ d4 ≤ 0.80) so the monotonicity cannot be satisfied
  by a degenerate 0.1% → 0.2% ramp. Nothing on this branch previously asserted
  that difficulty affected tolerance tightness at all.

---

## 5. C2(b) — the ladder

`_TOL_FRACTION_RANGE` capped the applied fraction at 1.0 for difficulties 1-3.
The Y14.5 margin reduces to `allowable × (1 − f)` floating and
`allowable × (1 − mean(f_a, f_b))` fixed, so `f ≤ 1` made the margin
non-negative *identically* — zero Tier 1 failures at three of four levels, and
a model that always answers "assembles" scoring 100% on Tier 1 at those levels.

Committed ranges, tuned against measurement rather than adopted from the
suggestion:

```python
_TOL_FRACTION_RANGE = {
    1: (0.60, 1.09),
    2: (0.65, 1.16),
    3: (0.70, 1.25),
    4: (0.72, 1.34),
}
```

### Measured Tier 1 failure rate, seeds 0-199, committed ladder

| Difficulty | Tier 1 failures / Tier 1 mates | Failure rate |
|---|---|---|
| 1 | 31 / 159 | **19.5%** |
| 2 | 99 / 301 | **32.9%** |
| 3 | 239 / 452 | **52.9%** |
| 4 | 421 / 609 | **69.1%** |

Monotonically increasing, 19.5% → 69.1%, i.e. the requested ~20% → ~70% shape.
Before this change the same measurement was 0% / 0% / 0% / 69.1%.

The reviewer's suggested starting point was measured and **rejected**:
`1:(0.60,1.05)`, `2:(0.75,1.15)`, `3:(0.90,1.25)`, `4:(1.00,1.35)` gives
11.3% / 40.2% / 87.2% / **100.0%** — d4 would have contained no assemblable
Tier 1 mate at all, which is the same degeneracy in the opposite direction. A
third candidate, `1:(0.60,1.10) … 4:(0.75,1.35)`, gave 20.8/35.9/53.3/**76.0%**
and was rejected as overshooting d4.

The number of RNG draws is unchanged by this edit (`rng.uniform(lo, hi)` is one
draw either way), so the sampled fastener sizes, grades, kinds and designations
are bit-identical to `b6f89b7`. Only the position-tolerance values moved. The
geometry change in `9d198a8` is therefore fully independent of the ladder
change in `a6412fa`.

### C2 mutation demonstration

Demanded flat ladder `(0.2, 0.5)` at every difficulty:

```
E       AssertionError: d4: no non-assemblable Tier 1 mates
E       assert not True
E        +  where True = all([True, True, True, True, True, True, ...])

tests\gen\test_sampler.py:65: AssertionError
```

```
E       AssertionError: Tier 1 failure rate is not strictly increasing in difficulty: [0.0, 0.0, 0.0, 0.0]
E       assert False

tests\gen\test_sampler.py:81: AssertionError
```

```
=========================== short test summary info ===========================
FAILED tests/gen/test_sampler.py::test_tier1_corpus_contains_both_passing_and_failing_mates[1]
FAILED tests/gen/test_sampler.py::test_tier1_corpus_contains_both_passing_and_failing_mates[2]
FAILED tests/gen/test_sampler.py::test_tier1_corpus_contains_both_passing_and_failing_mates[3]
FAILED tests/gen/test_sampler.py::test_tier1_corpus_contains_both_passing_and_failing_mates[4]
FAILED tests/gen/test_sampler.py::test_tier1_failure_rate_rises_monotonically_with_difficulty
5 failed in 0.17s
```

The other two mutations the reviewer used, plus the ladder actually shipped at
`b6f89b7`, also now fail:

```
--- mutation _TOL_FRACTION_RANGE = (0.0, 0.0) at every difficulty ---
5 failed in 0.17s
    E       AssertionError: d1: no non-assemblable Tier 1 mates
    E       AssertionError: d2: no non-assemblable Tier 1 mates
    E       AssertionError: d3: no non-assemblable Tier 1 mates
    E       AssertionError: d4: no non-assemblable Tier 1 mates
    E       AssertionError: Tier 1 failure rate is not strictly increasing in difficulty: [0.0, 0.0, 0.0, 0.0]
--- mutation _TOL_FRACTION_RANGE = (5.0, 5.0) at every difficulty ---
5 failed in 0.18s
    E       AssertionError: d1: no assemblable Tier 1 mates
    E       AssertionError: d2: no assemblable Tier 1 mates
    E       AssertionError: d3: no assemblable Tier 1 mates
    E       AssertionError: d4: no assemblable Tier 1 mates
    E       AssertionError: Tier 1 failure rate is not strictly increasing in difficulty: [1.0, 1.0, 1.0, 1.0]
--- mutation: the ORIGINAL b6f89b7 ladder (d1-d3 capped at f<=1.0) ---
4 failed, 1 passed in 0.19s
    E       AssertionError: d1: no non-assemblable Tier 1 mates
    E       AssertionError: d2: no non-assemblable Tier 1 mates
    E       AssertionError: d3: no non-assemblable Tier 1 mates
    E       AssertionError: Tier 1 failure rate is not strictly increasing in difficulty: [0.0, 0.0, 0.0, 0.7755102040816326]
```

All four of these **passed** the test that was replaced. Production restored
after each; `tests/gen/test_sampler.py` back to `12 passed`.

---

## 6. I1 — explicit Monte Carlo seed and sample count

`MateSpec` gains `mc_seed: int = 0` and `mc_n: int = 100_000`, placed after the
existing non-default fields, with defaults mirroring `tolcad.checker`'s
fallbacks. `to_check_dict()` emits `"seed"` and `"n"` in the `iso_fit` branch.
`asdict`/`from_json` carry them through the sidecar unchanged, verified by
`test_monte_carlo_fields_survive_the_sidecar_round_trip`. A non-positive `mc_n`
is rejected in `__post_init__`.

The sampler derives the seed as
`_mc_seed_for(seed, index) = 10_000 + seed × MAX_DIFFICULTY + index`, so it is
reproducible from the spec alone, collision-free across (assembly seed, mate
index), and never 0 — the offset means a spec that lost its seed in transit is
visibly different from one that legitimately drew 0.

`test_iso_fit_mates_carry_an_explicit_reproducible_monte_carlo_seed` asserts
not just that the field is set but that
`check(mate.to_check_dict()).detail["seed"] == mate.mc_seed`, i.e. the seed
actually reaches the Monte Carlo rather than sitting inertly in the spec.
Deleting the `seed`/`n` keys from `to_check_dict()` fails it with
`assert 0 == 10006`, and fails the spec-level test with `KeyError: 'seed'`.

### What H7/h6 now resolves to — reported, not decided

Over seeds 0-199 × difficulties 1-4 (108 H7/h6 mates), with per-mate seeds:

| Designation | assembles=True | assembles=False | distinct margins |
|---|---|---|---|
| H7/g6 | 123 | 0 | {1.0} |
| **H7/h6** | **85** | **23** | **{1.0, 0.99999}** |
| H7/k6 | 0 | 122 | 46 distinct values in [0.684, 0.764] |
| H7/p6 | 0 | 126 | {0.0} |

So **the H7/h6 label now varies across mates** — 21.3% False — where before it
was uniformly True because every mate silently used seed 0. The margin is
either exactly 1.0 or 0.99999, i.e. the False cases are a single clearance
failure in 100 000 samples. This is genuine line-to-line behaviour at MMC, not
a bug, but it does mean roughly one H7/h6 mate in five now carries a label that
would flip under a different sample count.

`SUPPORTED_FITS` was **not** changed, per instruction. The other three fits
remain perfectly predictable from the designation letter, which is I2 and
remains the human's call.

---

## 7. Concerns and things the human should know

1. **H7/h6 is now a coin-flip weighted 4:1, and that is a benchmark design
   decision, not a bug fix.** Before this wave every H7/h6 mate was labelled
   True; now 21% are False, and which ones depends on `mc_n = 100_000`. Halving
   or doubling the sample count would relabel a different subset. This
   interacts directly with I2 (label predictability): H7/h6 is now the *only*
   fit whose label a model cannot read off the designation string, and the
   signal it carries is one part in 10⁵ of sampling noise. Pre-registration
   should say explicitly whether a near-boundary Tier 2 label like this is a
   meaningful test item or a coin toss dressed as one. I did not decide it.

2. **I4 is still open and it interacts with the geometry now being frozen.**
   `build.py` still drills an identical through hole in both plates for fixed
   and floating fasteners, so the two kinds remain geometrically
   indistinguishable despite different ground-truth formulas, and
   `y14_5.py:80-81` still states as a load-bearing precondition that "the
   generator must emit projected zones" — which this generator does not. That
   was deferred, but it means the reference geometry about to be pre-registered
   does not encode the distinction its own labels depend on.

3. **The ladder is tuned to the current feature tables.** The failure rates
   above depend on the clearance-hole table in `features.py` and on the 50/50
   floating/fixed split. Any edit to either moves the rates. The band
   assertions on d1 and d4 will catch a large drift; a small one will pass. If
   the clearance table is ever revised against ISO 273 (the open question from
   Task 3), re-measure the ladder before pre-registering.

4. **The plate-size guard in `build_assembly` is new behaviour.** A caller who
   hand-builds an `AssemblySpec` and takes the 40.0 mm default will now get a
   `ValueError` instead of clipped geometry. That is deliberate, but it is a
   breaking change for any code path that constructs specs outside the sampler.

5. **`test_features_are_contained_and_disjoint_across_the_seed_sweep` builds
   400 solids** (50 seeds × 4 difficulties × 2 parts) and adds ~8 s to the
   suite, taking it from 16.6 s to 23.4 s. It is not marked slow because the
   brief required it to run over the full sweep. If the suite becomes a
   bottleneck, mark it rather than shrinking the sweep.

6. **The `_MIN_WALL_MM` / `_EDGE_MARGIN_MM` rationale is calibrated against the
   ladder committed here.** The worst-case displacement arithmetic in
   `layout.py`'s docstring assumes a maximum applied fraction of ~1.34. If the
   ladder is ever pushed higher, revisit the margins as well — the containment
   test checks nominal geometry, which is unaffected by tolerance zones, so it
   would not catch the margins becoming rhetorically stale.
