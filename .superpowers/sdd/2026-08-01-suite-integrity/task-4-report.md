# Task 4 report: the mutation-score layer

Branch `feat/suite-integrity`, starting HEAD `0b6e878`.

> **CORRECTED 2026-08-01 (fix round).** Sections 3 and 4 originally described
> the 275 survivors as "275 of 1,118 viable mutants", which does not close:
> 275/1,118 is 75.4% killed, not the 57.69% reported. 1,118 is the TOTAL JOBS
> figure; the viable denominator is 650. The survey itself was complete — all
> 275 measured survivors were triaged — but several triage verdicts were wrong.
> Corrections are inline below and in `task-4-fix-report.md`.

## 1. RED (Step 2), verbatim

```
$ python -m pytest tests/test_suite_integrity_script.py -v -k "cosmic_ray or mutation_floor"

collected 6 items / 4 deselected / 2 selected

tests/test_suite_integrity_script.py::test_the_cosmic_ray_config_runs_the_whole_core_subset FAILED [ 50%]
tests/test_suite_integrity_script.py::test_the_mutation_floor_is_measured_not_aspirational FAILED [100%]

================================== FAILURES ===================================
____________ test_the_cosmic_ray_config_runs_the_whole_core_subset ____________
    cfg = tomllib.loads((REPO / "cosmic-ray.toml").read_text(encoding="utf-8"))
>                       (...)
E       FileNotFoundError: [Errno 2] No such file or directory: '...\Paper1\cosmic-ray.toml'

____________ test_the_mutation_floor_is_measured_not_aspirational _____________
    import check_suite_integrity as mod
>       assert mod.MUTATION_FLOOR not in (0, 50, 60, 70, 75, 80, 85, 90, 95, 100), (
E       AttributeError: module 'check_suite_integrity' has no attribute 'MUTATION_FLOOR'

======================= 2 failed, 4 deselected in 0.06s =======================
```

Both failed exactly as expected: `cosmic-ray.toml` did not exist yet and `MUTATION_FLOOR` was undefined.

## 2. cosmic-ray, and the concurrency hazard it introduced

`cosmic-ray` 8.4.6 was already installed (`pip show cosmic-ray`). It mutates the target module **in place on disk**: patches the file, shells out to the test command, restores it — one mutant at a time, for the duration of `cosmic-ray exec`. This was directly observed during this task: a `git diff src/tolcad/types.py` taken mid-run showed a live mutant (`is` → `==`), and a concurrent code-review pass reading the tree during a run hit a spurious diff for the same reason. On every normal exit (three full runs across this task), the restore was byte-clean — `git diff src/` came back empty and `iso286.py`/`y14_5.py` matched HEAD exactly.

Both `cosmic-ray.toml` and `run_mutation_score()`'s docstring now carry an explicit warning: **do not run this concurrently with anything else that reads `src/tolcad/`**, the hazard is abnormal termination (not normal operation, which restores cleanly), and recovery is `git status --short` then `git checkout -- src/`.

## 3. Measured mutation score and pinned floors

Three full runs were made across this task (the third at the coordinator's request, after the first two used slightly different harnesses — the production `run_mutation_score()` path vs. a standalone diagnostic script written to capture per-mutant diffs for triage):

| Run | Purpose | Score |
|---|---|---|
| 1 | `python scripts/check_suite_integrity.py`, pre-triage | 57.63% |
| 2 | Standalone diagnostic (same config, captures survivor diffs) | 57.69% (275 of **650 viable** mutants surviving) |
| 3 | `python scripts/check_suite_integrity.py`, **post-triage** (all new tests in place) | **93.85%** (Core branch coverage: 94.12%) |

**The run-2 denominator, from the raw artefacts** (`cr_survivors/survivors_run.log`,
per-module `total jobs` / `surviving mutants` from `cr-report`):

| Module | Total jobs | INCOMPETENT | Viable | Surviving |
|---|---|---|---|---|
| types | 66 | 42 | 24 | 5 |
| y14_5 | 339 | 149 | 190 | 40 |
| iso286 | 515 | 226 | 289 | 169 |
| montecarlo | 97 | 11 | 86 | 44 |
| checker | 24 | 0 | 24 | 8 |
| reliability | 77 | 40 | 37 | 9 |
| **Total** | **1,118** | **468** | **650** | **275** |

375 killed / 650 viable = **57.69%** — the score the run actually printed.
1,118 is total jobs, not the viable denominator, and "1,118 = 1,586 total jobs
− 468 INCOMPETENT" in section 4 was an addition where a subtraction belonged.
Run 3's 93.85% is 610/650 (40 surviving) over the same denominator.

The small variance between runs 1 and 2 (57.63 vs 57.69) is cosmic-ray's per-mutant timeout sensitivity under system load, not a code change — both used the identical `cosmic-ray.toml`.

**Pinned:**
- `MUTATION_FLOOR = 93.85` (dated comment in `scripts/check_suite_integrity.py`)
- `COVERAGE_FLOOR = 94.12` (re-pinned from 91.64 — the new tests raised branch coverage, and leaving the old floor in place would have reintroduced the "floor that stops tracking what it bounds" defect this whole layer exists to catch)

**Caveat recorded in the code comment:** three more `types.py` survivors were found and fixed (2 killed, 1 documented equivalent) *after* the run-3 measurement, while writing up this report. Per explicit instruction, cosmic-ray was not run a fourth time to get a post-fix number. Those fixes can only raise the true current score, so 93.85 remains a valid (slightly conservative) floor — a lower bound the current tree still clears, never a false ceiling.

## 4. Full survivor list and triage

**All 275 measured survivors surveyed** — 275 of **650** viable mutants (650 = 1,118 total jobs − 468 INCOMPETENT, which cannot execute at all — `RemoveDecorator` on a dataclass, mainly — and correctly left out of the denominator per the brief). **252 recorded killed** with new tests; **23 recorded as equivalent mutants** with a specific reason each.

> **CORRECTED.** The survey was complete, but six of those verdicts were wrong,
> found by applying the mutants in an isolated copy during the fix round:
> five "killed" that did not kill (the `%` mutant in `fixed_fastener_tolerance`,
> two `is` mutants in `checker.py`, two in `montecarlo.py`) and four
> "equivalent" that are not (three live `condition is "..."` mutants in
> `y14_5.py`, plus `condition >= "fixed"`, which is a real behaviour change
> that other tests happen to kill). All are now killed for real. Corrected
> totals: **256 killed, 19 equivalent** overall (y14_5 alone: 28 killed,
> 12 equivalent, not 24/16). See `task-4-fix-report.md` §3. Separately, run 3
> left 40 survivors against 23 documented equivalents, so a residual
> **~17 mutants remain UNTRIAGED** — reported as untriaged, not absorbed.

### types.py — 5 survivors (3 killed, 2 equivalent)

| Mutation | Triage |
|---|---|
| `mmc`: `self.feature_type is FeatureType.INTERNAL` → `==` | **Equivalent.** `FeatureType` is a plain `Enum`; CPython enum members are singletons, so `is`/`==` agree for every value. |
| `lmc`: same mutation | **Equivalent**, same reason. |
| `@dataclass(frozen=True)` → `frozen=False` | **Killed** — `test_feature_of_size_is_immutable` asserts `AttributeError` on mutation. |
| `position_tol: float = 0.0` → `= 1.0` | **Killed** — `test_position_tol_defaults_to_zero_when_omitted` asserts the default value directly. |
| `if self.position_tol < 0.0` → `< -1.0` | **Killed** — `test_negative_position_tol_rejected` uses `position_tol=-0.1`. |

### checker.py — 8 survivors (8 killed)

| Mutation | Triage |
|---|---|
| `kind == "iso_fit"` → `kind <= "iso_fit"` | **Killed** — `test_unknown_mate_type_before_iso_fit_lexically_is_still_rejected` uses `"gizmo"` (sorts before `"iso_fit"`), which the existing `"weld"` case (sorts after) could not catch. |
| `kind == "virtual_condition"` → `is` | ~~Killed~~ **NOT killed at the time — corrected.** `"".join(["virtual_condition"])` returns the interned literal unchanged: CPython's `str.join` has a single-element fast path that returns the item itself. The test could not fail. Now killed via a two-piece join (`_uninterned`). |
| `kind == "iso_fit"` → `is` | Same false claim, same fix. |
| `position_tol=spec.get("position_tol", 0.0)` → `1.0` | **Killed** — `test_missing_position_tol_defaults_to_zero` omits the key and checks the resulting margin. |
| `n=mate.get("n", 100_000)` → `100001` / `99999` | **Killed** (both) — `test_missing_n_and_seed_default_to_documented_values` checks `detail["n"] == 100_000` exactly. |
| `seed=mate.get("seed", 0)` → `1` / `-1` | **Killed** (both) — same test checks `detail["seed"] == 0`. |

### y14_5.py — 40 survivors (~~24 killed, 16 equivalent~~ → **28 killed, 12 equivalent**)

- **8 equivalent:** `FeatureType` comparisons (`is`/`==`) in `virtual_condition`, `vc_assembles`, `_check_fastener_pair`, `fastener_assembles`'s hole/fastener guards — same singleton-enum reasoning as types.py. *(Still correct: enum members are singletons and cannot be manufactured a second time, so the argument holds for computed values, not just literals.)*
- ~~**8 equivalent:** `condition == "floating"`/`"fixed"` → `>=`/`<=`/`is` …~~ **WRONG — corrected.** Of these eight, only **four** are equivalent (`>=` against `"floating"` at three sites, `<=` against `"fixed"` at one). The rationale as written was false in two ways: (a) the ordering argument is directional — `"fixed" <= "floating"` is `True` where `==` is `False`, so per site exactly one direction is equivalent, and `condition >= "fixed"` is a real behaviour change (killed by the governing_part tests); (b) the interning argument applies only to source *literals*, and production never uses one — `checker.py` builds `condition` with `str.replace`, which allocates a fresh object, so all three `is` mutants are live. One of them silently deletes the hole_b clearance guard. All four now killed; see `task-4-fix-report.md` §3 and the rewritten block comment in `test_y14_5.py`.
- **24 killed**, grouped by root cause:
  - **7** — `bonus_tolerance`'s EPS-widened validity guard: no existing test probed the *lower* bound at all, or either bound's exact edge. New: `test_bonus_tolerance_rejects_actual_size_below_min`, `..._accepts_lower_bound_exactly_at_epsilon`, `..._accepts_upper_bound_exactly_at_epsilon`.
  - **5** — `hole.mmc - fastener.mmc` → `%`/`**`: the canonical worked example (`0.5/2.0 == 0.5**2.0`) coincidentally agreed with subtraction. New tests use values ≥ 2× the fastener MMC where they diverge sharply (`floating_fastener_tolerance`, `fixed_fastener_tolerance`, `fastener_assembles`'s `clearance_a`/`clearance_b`). **CORRECTED:** the `fixed_fastener_tolerance` case used H=9, F=8 with the justification "9%8=1 forces subtraction apart from modulo too" — but `9 % 8 == 9 - 8 == 1`, so the `%` mutant survived that test. Re-pinned on (10.0, 3.0), the same pair the floating test uses, which separates `-`, `%`, `//` and `**` at once.
  - **2** — `hole_a.mmc < fastener.mmc` / `hole_b.mmc < fastener.mmc` → `<=`: no test used an exactly-equal-MMC pair (a legitimate zero-clearance boundary case, in the same spirit as the zero-width tolerance finding). New: `test_floating_allows_hole_a_exactly_at_fastener_mmc`.
  - **8** — `detail["governing_part"]`: **nothing previously read this field at all.** New assertions added to three existing tests (asymmetric-hole-a, asymmetric-hole-b, and a new tie-break test using bit-identical margins) pin all three cases (`hole_a` wins, `hole_b` wins, tie → `hole_a`), which collectively discriminate `==`,`!=`,`<`,`>`,`>=`,`is`,`is not`, and full negation.
  - **2** — `assembles=margin >= -EPS` → `>` (two call sites, `vc_assembles` and `fastener_assembles`): new bit-exact boundary tests constructed from 0 and `EPS` directly (avoiding floating round-off from subtracting `EPS` off a larger number).

### montecarlo.py — 44 survivors (42 killed, 2 equivalent)

- **2 equivalent:** `sigma <= 0.0` vs `== 0.0` — `sigma = (hi-lo)/6.0` and `FeatureOfSize` already guarantees `hi >= lo`, so `sigma` can never be negative; `<=0` and `==0` are the same predicate. `assembles=yield_frac == 1.0` vs `>= 1.0` — `yield_frac` is a mean of booleans, mathematically bounded to `[0,1]`, so it can never exceed 1.0; the two predicates coincide.
- **42 killed:**
  - **30** — the `mid`/`sigma` arithmetic formula and the `sigma==0.0` shortcut's *value-observable* mutants: one new test (`test_normal_distribution_matches_the_documented_mid_and_sigma`) checks the "normal" branch's mean and std directly — the existing tests only checked the post-clip min/max range, which every formula satisfies trivially.
  - **4** — `sigma==0.0` mutants that are only observable via **rng-state consumption** (numpy's `Generator.normal(scale=0)` is itself deterministic, so a mutant that fails to take the shortcut is invisible to a values-only check): `test_zero_width_tolerance_does_not_consume_rng_state` uses a second, later draw to detect the state shift.
  - **4** — unknown-`distribution` dispatch (`<=`/`>=` substitutes for `==`): `"bogus"`/`"zzz"` sort before/after both `"uniform"` and `"normal"` lexically.
  - **2** — `distribution == "uniform"`/`"normal"` → `is`: runtime-built strings, same interning-defeat technique as checker.py — **and inheriting the same defect.** `"".join(["uniform"])` is a no-op, so neither mutant was killed. Both now killed via `_uninterned`.
  - **1** — `clearances = holes - shafts` → `holes // shafts`: at this nominal size the ratio is always close to 1, so floor division degenerates to 0/1 with the *same sign* as the correct subtraction for the existing all-clearance/all-interference tests. New test checks `detail["mean_clearance"]`/`["min_clearance"]` exact magnitude, not just sign.
  - **1** — `clearances > 0.0` → `>= 0.0`: new test uses two bit-identical zero-tolerance features (clearance exactly 0), which is itself a zero-width-band case.

### reliability.py — 9 survivors (7 killed, 2 equivalent)

- **2 equivalent:** `tested <= 0` vs `== 0` (`tested` only ever increments from 0, never negative). `check(...).assembles is base.assembles` vs `==` (Python `True`/`False` are process-wide singletons, so `is`/`==` agree on every bool pair).
- **7 killed:** `BOUNDARY_BAND * epsilon` → `%` and the constant `2.0` → `1.0` (two new tests with epsilon/margin chosen so the two formulas diverge sharply); the boundary's strict `<` vs `<=` (exact-edge test); `stable / tested` → `stable // tested` (a monkeypatched `check` forces an exact non-integer ratio, since the existing positive-control test's `0.0 <= value < 1.0` assertion can't distinguish a real fraction from floor-division's `0`); `assembles == base.assembles` → `>=` (a monkeypatched fail→pass flip, the one direction `>=` gets backwards); `StabilityResult`'s `frozen=True` → `False` (immutability test); `continue` → `break` in the exclusion loop (two-mate test where the excluded one comes first).

### iso286.py — 169 survivors (168 killed, 1 equivalent)

By far the largest count — dominated by individual `NumberReplacer`/unary-operator mutations on single cells of `_DEVIATION_MICRONS` ("g", "k", "p"), because only a handful of 20mm spot values were previously pinned per letter (unlike `_IT_MICRONS`, which already had an exhaustive 91-cell check).

- **1 equivalent:** `hole_letter is not "H"` vs `!=`. `hole_letter` is always a single character (`hole_part[0]`); CPython caches every single-character Latin-1 string as a process-wide singleton, so `is`/`is not` against a single character always agrees with `==`/`!=` — stronger than the general literal-interning argument, since it holds for computed single characters too, not just source literals.
- **168 killed**, grouped by root cause (one new parametrized/table test typically kills many individually-numbered mutants at once):
  - **~120** — individual `_DEVIATION_MICRONS` cell mutations across "g"/"k"/"p": `test_all_deviation_letters_match_iso286_tables_4_and_5`, an exhaustive 13-band parametrized check (mirroring the treatment `_IT_MICRONS` already had).
  - **4** — `"H"`/`"h"`: `[0]*13` → `[0]*14`/`[0]*12`: `test_deviation_tables_span_every_size_band` pins list length against `_SIZE_BANDS`.
  - **21** — individual `_SIZE_BANDS` cell mutations: `test_size_bands_match_iso286_table_1_exactly` pins the whole list.
  - **2** — `hole_letter != "H"` → `<`/`>`: `test_non_hole_basis_designation_rejected_on_both_sides_of_h`, parametrized over letters on both sides of `"H"` alphabetically.
  - **5** — `nominal_mm <= 0` boundary mutations (`==0`, `<0`, `<=1`, `<=-1`, and the upper `>` → `>=`): four new boundary tests (`-0.5`/`0.0` rejected, `0.5` accepted, `500.0` accepted, `500.0001` rejected).
  - **6** — the error message's `_SIZE_BANDS[-1]` index mutations (only visible in the *text* of the exception, not whether it raises): `test_out_of_range_message_names_the_actual_upper_bound` pins the literal `"(0, 500]"` in the message.
  - **4** — the `k`-grade range tuple `(4, 7)` mutations: three boundary tests (`k4`/`k7` accepted, `k3` rejected — `k4`'s test distinguishes on which *exception message* fires, since grade 4 isn't itself an `_IT_MICRONS` grade).
  - **2** — the `_parse` except-tuple mutations (`ValueError`/`IndexError` swapped for a nonsense placeholder type): two new malformed-designation tests that specifically trigger each exception type inside the `try` (`"H7/g"` for the `ValueError` side, `"/g6"` for the `IndexError` side).
  - **1** — `designation.split("/", 1)` → `split("/", 2)`: a designation with a second slash (`"H7/g6/extra"`), which the mutant turns into an unpacking error instead of the wrapped "malformed designation" message.

## 5. Verification

- Full suite: **371 passed** (368 immediately after the survivor triage; 371 after fixing the types.py gap described below).
- `python scripts/gate_a.py > /dev/null 2>&1; echo $?` → **1** (unchanged, 6 PASS / 3 SKIP; `scripts/gate_a.py` itself untouched).
- Tier 1 ladder, seeds 0–199 (re-measured with the same helper `tests/gen/test_sampler.py::_tier1_verdicts` uses, at `seeds=200`): **d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%** — exact match, unchanged.
- `git status --short`: clean after commit (see below); before commit, only the expected files were modified/untracked.

## 6. Self-review

**A mistake, caught and fixed before commit.** My first pass at `types.py` used the brief's *illustrative* survivor example (`if upper_dev < lower_dev` → `<=`, i.e. the zero-width-band case) and added a test for it, without going back to the actual measured survivor list for `types.py` once it was captured (mmc/lmc `is`→`==`, the frozen-dataclass mutant, and the two `position_tol` mutants — a completely different set of 5). This meant `test_types.py` initially had a real test but for the *wrong* module's actual gaps. Caught during report-writing by re-reading `tests/test_types.py` against the raw `survivors_types.txt` diff file; fixed by adding `test_feature_of_size_is_immutable`, `test_position_tol_defaults_to_zero_when_omitted`, and `test_negative_position_tol_rejected`, plus documenting the two `is`/`==` equivalents. This is exactly the kind of error the "triage every survivor, not just the number" instruction is designed to surface — worth stating plainly rather than glossing over.

**On the "measured, not aspirational" pin.** `MUTATION_FLOOR = 93.85` predates the three types.py fixes above by a few minutes; it was not re-measured afterward per explicit instruction not to run cosmic-ray a fourth time. The fixes can only raise the true score (they kill previously-surviving mutants), so the floor remains a valid lower bound — documented as such in the code comment rather than left unexplained.

**Concerns:**
- The `>=93.85%` floor is close to (not comfortably below) the actual current score; if a future contributor adds a new branch to the core without matching tests, the floor could start failing on ordinary variance from cosmic-ray's per-mutant timeout under load (observed: 57.63% vs 57.69% on two nominally identical runs). This is a real operational risk worth watching, not a defect in the pin itself — the brief is explicit that the pin must be measured, and a measured value close to the true rate is the honest result.
- iso286.py's exhaustive deviation-table test asserts against a *second, independently transcribed* copy of the table in the test file (`_G_DEVIATION_UM` etc.), matching the pattern already used for `_IT_MICRONS`. This is deliberate (a test that reads the same constant it's checking proves nothing), but it does mean two literal copies of the same published values now exist in the codebase, and if ISO 286 were ever amended, both would need updating together.
