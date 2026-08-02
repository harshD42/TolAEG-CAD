# Task 4 fix report: findings F-1 .. F-9

Branch `feat/suite-integrity`, starting HEAD `7b1f807`.

Cosmic-ray was **not** run in this round. F-1 was reconcilable entirely from the
run-2 diagnostic artefacts, which still exist in the scratchpad
(`cr_survivors/survivors_run.log` plus the six per-module `.sqlite` sessions and
`survivors_*.txt` diffs). Mutant verification was done in an isolated copy of
`src/` + `tests/`, never in the working tree.

---

## 1. F-1 — the survivor arithmetic, reconciled

**The survey was complete. The denominator label was wrong.**

Per-module figures, read verbatim from run 2's `cr-report` output:

| Module | Total jobs | INCOMPETENT | Viable | Surviving |
|---|---|---|---|---|
| types | 66 | 42 | 24 | 5 |
| y14_5 | 339 | 149 | 190 | 40 |
| iso286 | 515 | 226 | 289 | 169 |
| montecarlo | 97 | 11 | 86 | 44 |
| checker | 24 | 0 | 24 | 8 |
| reliability | 77 | 40 | 37 | 9 |
| **Total** | **1,118** | **468** | **650** | **275** |

    killed = 650 - 275 = 375
    375 / 650 = 57.6923%   <- exactly the 57.69% run 2 printed

The `surviving mutants:` counts sum to **275**, which is precisely the set that
was triaged. **No survivors were missed.** The claimed contradiction came from
one mislabelled number: **1,118 is TOTAL JOBS, not viable mutants.** Section 4
of the task-4 report compounded it — "1,118 = 1,586 total jobs − 468
INCOMPETENT" is an addition (1,118 + 468 = 1,586) where a subtraction belonged.
There is no 1,586-job run; that figure never existed.

So the reviewer's third arithmetic line is the one that resolves it:
93.85% of **650** (not 1,118) implies **610 killed, 40 surviving**, and
610/650 = 93.8462% displays as exactly 93.85%. The denominator is stable across
runs because both totals and INCOMPETENT are determined by the source AST, which
the triage never touched (only `tests/` changed).

### What IS unaccounted for, stated plainly

Run 3 left **40 survivors** against **23 documented equivalents**, so
**~17 mutants were neither killed nor documented.** Four of those 17 are now
identified and killed (F-3, F-4, and the third `is` mutant found here); the
`%` mutant of F-6 was a 41st that had been miscounted as killed. That still
leaves roughly a dozen **UNTRIAGED**. They are reported as untriaged in
`check_suite_integrity.py`'s pin comment and in the corrected task-4 report —
not folded into the equivalent count, not re-framed away. Identifying them
requires another cosmic-ray run, which this round's budget forbids; it should
be the first action of any future round that is allowed one.

### Triage verdicts that were wrong (found by applying the mutants)

| Recorded | Reality | Now |
|---|---|---|
| `y14_5` `condition is "fixed"` (governing_part) — equivalent | live, raises `TypeError` via `check()` | killed |
| `y14_5` `condition is "floating"` (hole_b MMC guard) — equivalent | live, **deletes a safety guard** | killed |
| `y14_5` `condition is "floating"` (hole_b type guard) — equivalent | live (not in the review; found here) | killed |
| `y14_5` `condition >= "fixed"` — equivalent | real behaviour change, killed by other tests | reclassified |
| `y14_5` `hole.mmc % fastener.mmc` — killed | survived | killed |
| `checker` `kind is "virtual_condition"` — killed | survived | killed |
| `checker` `kind is "iso_fit"` — killed | survived | killed |
| `montecarlo` `distribution is "uniform"` — killed | survived | killed |
| `montecarlo` `distribution is "normal"` — killed | survived | killed |

Corrected totals for the 275: **256 killed, 19 equivalent** (was 252 / 23).
For `y14_5` alone: **28 killed, 12 equivalent** (was 24 / 16).

---

## 2. The `"".join([x])` no-op — a defect the review did not name

Four of the nine wrong verdicts above share one root cause, worth stating
separately because it was a *test that could not fail*, shipped inside the layer
built to catch tests that cannot fail.

`test_checker.py` and `test_montecarlo.py` defeated CPython literal interning
with `"".join(["virtual_condition"])`. That does nothing: `str.join` has a
single-element fast path that returns the item itself, so the result **is** the
interned literal.

```
>>> "".join(["floating"]) is "floating"          True    (no-op)
>>> "".join(["float", "ing"]) is "floating"      False   (works)
>>> "floating_fastener".replace("_fastener","") is "floating"   False  (production)
```

Replaced by a `_uninterned()` helper that splits into two pieces and **asserts
its own postcondition** (`built is not text`), so it fails loudly rather than
silently reverting to a no-op if CPython ever changes.

---

## 3. Mutant verification, before and after

Isolated copy of `src/` + `tests/`, `PYTHONDONTWRITEBYTECODE=1`, `__pycache__`
cleared between runs, test command = the same six-file core subset cosmic-ray
uses. (The bytecode precaution matters: `-` → `%` preserves file size, so a
same-second rewrite can be served from a stale `.pyc`. A first pass without it
produced a false "killed" for the F-6 mutant.)

| Mutant | Before fixes | After fixes |
|---|---|---|
| `y14_5` governing_part `== "fixed"` → `is` | SURVIVED (192 passed) | KILLED (2 tests) |
| `y14_5` hole_b MMC guard `== "floating"` → `is` | SURVIVED (192 passed) | KILLED |
| `y14_5` hole_b type guard `== "floating"` → `is` | SURVIVED (192 passed) | KILLED |
| `y14_5` governing_part `== "fixed"` → `>=` | KILLED | KILLED (3 tests) |
| `y14_5` governing_part `== "fixed"` → `<=` | SURVIVED | equivalent, documented |
| `y14_5` dispatch `== "floating"` → `>=` | SURVIVED | equivalent, documented |
| `y14_5` `fixed_fastener_tolerance` `-` → `%` | SURVIVED (192 passed) | KILLED |
| `y14_5` `fixed_fastener_tolerance` `-` → `//` | KILLED | KILLED (2 tests) |
| `y14_5` `fixed_fastener_tolerance` `/` → `**` | KILLED | KILLED |
| `checker` `kind == "virtual_condition"` → `is` | SURVIVED (192 passed) | KILLED |
| `checker` `kind == "iso_fit"` → `is` | SURVIVED (192 passed) | KILLED |
| `montecarlo` `distribution == "uniform"` → `is` | SURVIVED (192 passed) | KILLED |
| `montecarlo` `distribution == "normal"` → `is` | SURVIVED (192 passed) | KILLED |
| *control: unmutated* | 192 passed | 196 passed |

---

## 4. Finding-by-finding

**F-1 (Critical).** Reconciled above. Survey complete (275/275); denominator
mislabelled; ~17 run-3 survivors reported as untriaged.

**F-2 (Critical).** `MUTATION_MEASURED = 93.85`, `MUTATION_TOLERANCE = 0.50`,
`MUTATION_FLOOR = 93.35`. This was not hypothetical: run 3's raw score is
610/650 = 93.8462, which is **below** a literal 93.85 floor, so the gate would
have failed deterministically on an unchanged tree. The rationale is recorded at
the constant. `test_the_mutation_floor_is_measured_not_aspirational` now checks
`MUTATION_MEASURED`; a new test asserts `MUTATION_TOLERANCE >= 0.005` (half a
display ulp) and that the floor is the derived value. `timeout` untouched.

**F-3 (Important).** `condition is "fixed"` killed by
`test_governing_part_matches_condition_by_equality_not_identity` (direct call)
and `test_dispatches_fixed_fastener` (production path). Equivalence claim
rewritten.

**F-4 (Important).** `condition is "floating"` on the hole_b MMC guard killed by
`test_hole_b_mmc_guard_matches_condition_by_equality_not_identity`, which asserts
the `ValueError` the mutant deletes. A **third** live one — the same mutation on
the hole_b feature-type guard one line up, not in the review — was found and
killed too.

**F-5 (Important).** Rationale rewritten. The ordering argument is directional:
against `"floating"` only `>=` is equivalent, against `"fixed"` only `<=`.
The comment now tabulates all four comparisons and records that `>= "fixed"` is
a real behaviour change surviving only on luck. The interning half is corrected
to say it holds for source literals and *not* for production's `str.replace`.

**F-6 (Important).** `test_fixed_fastener_tolerance_halves_not_squares_the_clearance`
re-pinned from (9.0, 8.0) to (10.0, 3.0). `9 % 8 == 9 - 8 == 1` was the whole
problem; `10 - 3 = 7`, `10 % 3 = 1`, `10 // 3 = 3`, `7 ** 2 = 49` separate all
four operators.

**F-7 (Important).** `test_dispatches_fixed_fastener` added to `test_checker.py`
— the first `fixed_fastener` mate to reach `checker.check()` in the core subset.
Asserts method, margin, and both `governing_part is None` and
`clearance_b is None`.

**F-8 (Minor).** `_mutate_one_module` now parses through a `_count()` helper that
raises `RuntimeError` with the same "refusing to report a number that was not
measured" wording as `run_coverage`; `cr-report` runs with `check=True`; the
dead `config["cosmic-ray"]["module-path"]` assignment is replaced by a comment
explaining why module-path is supplied per call.

**F-9 (Minor).** Both warnings now say "all THREE normal exits observed during
this layer's development (three full runs)" and cross-reference
`task-4-report.md` §3.

---

## 5. Verification

- Full suite: **376 passed** (371 at HEAD + 5: three `y14_5` identity tests, one
  `checker` fixed-fastener test, one mutation-tolerance test).
- `python scripts/gate_a.py > /dev/null 2>&1; echo $?` → **1** (unchanged;
  `scripts/gate_a.py` untouched).
- Tier 1 ladder, seeds 0–199 via `tests/gen/test_sampler.py::_tier1_verdicts`:
  **d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%** — exact match, unchanged.
- `git status --short` clean before each commit.
- No checker-core *behaviour* changed: the only `src/` edit in this round is
  none at all. All kills are test-side.

## 6. Concerns

- **The ~17 untriaged run-3 survivors are still untriaged.** This is the one
  thing this round could not close within its budget. It is now recorded in
  three places (the pin comment, the corrected task-4 report, this report)
  rather than absorbed. It should be the first item of the next round that is
  permitted a cosmic-ray run.
- **93.85 is a pre-fix measurement, and now more conservatively so.** Nine
  mutants that were not actually being killed at measurement time are killed
  now, so the true score is higher than 93.85. The pin remains a valid lower
  bound; it is further from the truth than it was.
- **The `_uninterned` helper is duplicated across three test files.** Deliberate
  — importing across test modules is fragile and a shared module is a new file —
  but it is duplication, and the three copies must not drift.
- **This class of defect is not systematically excluded.** Nine wrong verdicts
  were found by applying mutants one at a time by hand. Nothing prevents the
  next triage from recording another false kill; only a re-run does. A cheap
  mitigation for a future round: after triage, re-run Layer 2 and require the
  survivor set to have *actually* shrunk by the claimed amount.
