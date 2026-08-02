# Task 3 report — repair the reliability instrument, correct the false frozen statement

Branch `main`, base 062316e. Files changed: `scripts/gate_a.py`,
`tests/test_gate_a.py`, `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`.
**Zero `src/` delta.**

---

## 1. Deviation from the brief, declared up front

The brief's two test snippets are not runnable as written, in three ways. All
three are adaptations of binding, not of intent; the assertions are the brief's.

| Brief | Reality | What I did |
|---|---|---|
| `mod.BOUNDARY_BAND` | lives in `tolcad.reliability`, not `scripts.gate_a` | see below |
| `mod.RELIABILITY_EPSILON` | the module attribute is `_RELIABILITY_EPSILON` | used the real name |
| `mod._aggregate_reliability()` | takes 4 required args `(mates, epsilon, seeds, threshold)` | passed them |

The third adaptation is the substantive one. The brief computes

```python
band = mod.BOUNDARY_BAND * mod.RELIABILITY_EPSILON   # = 2.0 * 1e-4 = 2e-4
```

and then predicts the test will report mate[8] with "2 binding parts (`0.0` and
`3.5e-4`, **both inside the band**)". Those two statements contradict each other:
`3.5e-4 > 2e-4`, so with that band the intended binding part is *outside* it.
`BOUNDARY_BAND * epsilon` is the **bottom** of the regime-2 sensitive band — the
exclusion threshold — not its top. The band the construction rule governs is
`[2e-4, 5e-4]`, documented as such in `gate_a.py` itself.

Consequences of using the brief's literal 2e-4, both of which I verified:

- **It would not have caught mate[9] at all.** mate[9]'s parts were
  `(0.0, -3.5e-4)`; only `0.0` is within 2e-4, so it would have counted *one*
  binding part and passed — reproducing precisely the failure the brief says
  both earlier proposed repairs made.
- It would have **falsely failed mates [2] and [3]**, the regime-1
  far-from-boundary floating-fastener mates, whose parts are `(0.45, 0.40)` and
  `(-0.40, -0.45)`. Zero parts inside any band, so `len(binding) == 1` is false.

So I used `_SENSITIVE_BAND = 5.0 * _RELIABILITY_EPSILON` (the band's top) and
skipped mates with **no** part in the band as regime-1, which the rule does not
govern. Both changes are commented in the test. With this binding the test
catches mate[8] *and* mate[9], and passes on the repaired set.

I also added the **second half** of the construction rule, which the brief's
snippet asserts nowhere: that every non-binding part is slack at ≥10×. Without
it, "exactly one binding part" is satisfiable by a part parked just outside the
band, which is the same near-degeneracy in a new costume.

---

## 2. RED — verbatim

```
tests/test_gate_a.py::test_every_sensitive_mate_has_exactly_one_binding_part FAILED
tests/test_gate_a.py::test_reliability_tested_and_excluded_are_pinned_exactly FAILED

E  AssertionError: mate[8] has 2 parts inside the sensitive band 5.00e-04
   (margins [0.0, 0.00035000000000001696]); the construction rule requires
   exactly one binding part, every other slack at >=10x
E  assert 2 == 1
E   +  where 2 = len([0.0, 0.00035000000000001696])

E  AssertionError: tested=11, expected 12. A mate has fallen into the exclusion
   band -- check the per-part margins against the construction rule.
E  assert 11 == 12
E   +  where 11 = ReliabilityAggregate(mean=0.9981818181818182,
      ci_low=0.9963636363636362, ci_high=0.9995454545454545,
      fraction_passing=0.98, tested=11, excluded=1,
      min_abs_margin=0.0003499999999991843, max_abs_margin=0.44999999999999996,
      n_seeds=200).tested

====================== 2 failed, 12 deselected in 0.22s =======================
```

Pre-repair per-part margins across the whole set, measured:

```
 0 virtual_condition margin=+2.000000e-01  a=None                  b=None
 1 virtual_condition margin=-1.000000e-01  a=None                  b=None
 2 floating_fastener margin=+4.000000e-01  a=0.45                  b=0.4
 3 floating_fastener margin=-4.500000e-01  a=-0.4                  b=-0.44999999999999996
 4 fixed_fastener    margin=+4.000000e-01  a=None                  b=None
 5 fixed_fastener    margin=-3.000000e-01  a=None                  b=None
 6 virtual_condition margin=+3.500000e-04  a=None                  b=None
 7 virtual_condition margin=-3.500000e-04  a=None                  b=None
 8 floating_fastener margin= 0.000000e+00  a=0.0                   b=+3.5000000000000170e-04   <-- SWALLOWED
 9 floating_fastener margin=-3.500000e-04  a=0.0                   b=-3.4999999999996145e-04   <-- LATENT
10 fixed_fastener    margin=+3.500000e-04  a=None                  b=None
11 fixed_fastener    margin=-3.500000e-04  a=None                  b=None
tested 11  excluded 1  mean 0.9982
```

An intermediate RED is worth recording: after repairing mate[8] alone, the run
went `1 failed, 1 passed` with the failure now on **mate[9]** — the test does
independently catch the latent second defect, it is not merely asserted to.

---

## 3. Repaired per-part margins — every sensitive mate

| # | type | margin_a | margin_b | margin = min | verdict | governing |
|---|---|---|---|---|---|---|
| 6 | virtual_condition | — | — | +3.5000e-04 | assembles | — |
| 7 | virtual_condition | — | — | −3.5000e-04 | fails | — |
| 8 | floating_fastener | **+3.5e-04** (binding) | +3.5e-03 (slack, 10×) | +3.5000e-04 | assembles | hole_a |
| 9 | floating_fastener | **−3.5e-04** (binding) | +3.5e-03 (slack, 10×) | −3.5000e-04 | fails | hole_a |
| 10 | fixed_fastener | — | — | +3.5000e-04 | assembles | — |
| 11 | fixed_fastener | — | — | −3.5000e-04 | fails | — |

Three positive and three negative, the balance the set was designed for and had
lost. Mates [6], [7], [10], [11] are single-expression (virtual-condition and
B-4 fixed-fastener, which sets `margin_a = margin_b = None`); the rule does not
apply and the test skips them. Untouched, as instructed.

Both repaired mates now report `governing_part = hole_a`, so the binding part is
named in the checker's own output rather than inferred.

---

## 4. Measured after repair

```
Checker reliability  PASS  mean 0.9975 over 200 pre-registered seeds
  (95% bootstrap CI [0.9954, 0.9992], 10000 resamples);
  fraction of seeds >= 0.95: 0.9700
  (tested=12, excluded=0, tested |margin| in [3.50e-04, 4.50e-01]);
  threshold 0.95
```

| quantity | value |
|---|---|
| mean | **0.9975** |
| 95% bootstrap CI | **[0.9954, 0.9992]** |
| fraction of seeds ≥ 0.95 | **0.9700** |
| tested / excluded | **12 / 0** |
| tested \|margin\| band | [3.50e-04, 4.50e-01] |

This equals D-D's predicted 0.9975 / [0.9954, 0.9992] / 12 / 0 exactly. It was
measured, not assumed; the agreement is a check on D-D, not a substitute for the
measurement.

**Reachable per-seed values, measured both sides of the repair:**

- pre-repair (11 tested): `{0.9091, 1.0000}`
- post-repair (12 tested): `{0.9167, 1.0000}`

The first confirms the brief's factual claim about what 01e got wrong. The
second means 01e's sentence — "at 12 tested mates the only values reachable near
the threshold are 1.0000 and 0.9167" — is now **true of the instrument it
describes**. The repair did not just remove a false statement; it made the
frozen text correct. That is recorded in the amendment.

---

## 5. Headroom re-measured (not in the brief; its own docstring demanded it)

`test_gate_a_reliability_criterion_holds_for_the_real_measurement` carried a
measured headroom table prefixed "200 pre-registered seeds, **11 tested mates**"
and closing with "*If the mate set or epsilon changes, re-measure these numbers
— do not carry them forward.*" The mate set just changed. I re-measured by
scaling the perturbation inside `reliability._perturb` by k (monkeypatched
in-process; **no `src/` file was edited**):

| k | before (11 mates) | after (12 mates) |
|---|---|---|
| 1 | 0.9982 PASS (shipped) | **0.9975 PASS (shipped)** |
| 2 | 0.9518 **PASS — not caught**, 0.0018 of margin | **0.9392 FAIL — caught** |
| 3 | 0.9068 FAIL | **0.8950 FAIL** |

Restoring the twelfth mate **tightened the criterion's sensitivity from ~3× to
~2×**. The gate got stricter, not looser, which is the right direction for a
repair to a measuring instrument. Docstring updated with the new table and the
old one retained for comparison.

Also corrected in the same file: the monkeypatched `fake_aggregate` in
`test_gate_a_reliability_row_is_fail_when_mean_below_threshold` carried
`tested=11, excluded=1`. Cosmetic (it is a fake driving a FAIL path), but it
mirrors the real instrument and would have quietly re-taught the wrong
composition to the next reader.

---

## 6. Amendment as filed

Appended to the correction log in
`docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`,
**amendment 1 of 5** for this plan, sixth in the log overall:

> - *2026-08-01f (pre-data):* The Gate A reliability mate set was repaired. Two
>   sensitive-band mates were constructed as though the floating-fastener margin
>   were the SUM of both parts' slack; y14_5 implements ASME B-3's per-part
>   `min()`. One mate therefore sat at exactly 0.0, fell inside the exclusion
>   band, and was silently dropped, so the set measured `tested=11, excluded=1`.
>   The correction 2026-08-01e text stating "at 12 tested mates the only values
>   reachable near the threshold are 1.0000 and 0.9167" was consequently FALSE:
>   eleven were tested and the reachable values were {0.9091, 1.0}. Both mates are
>   rebuilt under a construction rule — exactly one binding part per mate at
>   ±3.5e-4, all others slack at ≥10× — which determines the result rather than
>   leaving it under-specified. Measured after repair: `tested=12, excluded=0`,
>   mean **0.9975** over the unchanged 200-seed set (95% bootstrap CI
>   [0.9954, 0.9992]), fraction of seeds ≥ 0.95 = 0.9700, and the reachable
>   per-seed values are once again exactly {0.9167, 1.0000} — so 01e's sentence
>   is now true of the instrument it describes. Neither the 0.95 threshold, the
>   seed set, nor the exclusion band was touched. Found by adversarial review
>   before any data was generated.

Two additions beyond the brief's draft, both factual and both measured: the
post-repair numbers (the brief said to use measured, not predicted, values), and
the observation that 01e is now true. I also changed the sentence that follows
the log from "**All five** predate any experimental data" to "**All six**" — it
is a count of the log's entries and adding a sixth without touching it would
have introduced a new false statement into the same paragraph this task exists
to correct.

The construction rule is recorded above `_RELIABILITY_MATES` in `gate_a.py`,
including the reason it exists (B-3 is per-part) and a pointer to the test that
enforces it.

---

## 7. Verification

| check | result |
|---|---|
| Full suite, `python -m pytest -q` | **382 passed** in 37.47s (380 before + the 2 new) |
| Target tests | `2 passed, 12 deselected` |
| `python scripts/gate_a.py > /dev/null 2>&1; echo $?` (no pipe) | **1** |
| Gate A rows | **6 PASS / 3 SKIP** (unchanged; the 3 SKIPs are the two missing oracle exports and the fresh-clone row) |
| `git status --short` after all runs | clean (empty) |
| Session finalizer | did not fire — no `src/` or `tests/fixtures/` modification |
| `src/` delta | zero |

`git status --short` post-commit and after a further full-suite + Gate A run:

```

```

(empty — no output, both times.)

**Commit `cac4644`**, three files, 140 insertions / 23 deletions:

```
docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md |  21 +++-
scripts/gate_a.py                                                    |  31 ++++--
tests/test_gate_a.py                                                 | 111 +++++++++++---
```

Pushed: `062316e..cac4644  main -> main` to
https://github.com/harshD42/TolAEG-CAD. `origin/main` confirmed at `cac4644`.

This report is not in the commit: `.superpowers/sdd/2026-08-01-closeout/` is
gitignored, as with previous tasks' reports.

---

## 8. Self-review

**Constraints, each checked rather than assumed.**

- `src/` untouched — confirmed by `git status --short` listing only `docs/`,
  `scripts/`, `tests/`. I did not edit `y14_5.py`; the per-part `min()` is
  correct and the defect was entirely in the mate construction, exactly as the
  task stated. The k-scaling re-measurement monkeypatched `_perturb`
  in-process and wrote nothing.
- 0.95 threshold, `RELIABILITY_SEEDS` (0–199), and `BOUNDARY_BAND` (2.0)
  all unchanged — grep-confirmed.
- `_IT_MICRONS`, `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`,
  `_TOL_FRACTION_RANGE`, `_MIN_WALL_MM`, `_EDGE_MARGIN_MM` — untouched; no file
  containing them was opened for edit.
- Only `position_tol` values on mates [8] and [9] changed. No nominal, no
  deviation, no mate added or removed, count still 12.

**One judgement call worth flagging.** The slack assertion compares a ratio, and
the mates are constructed at *exactly* 10× (3.5e-4 → 3.5e-3), which in binary
floating point lands a few ulp under: `3.500000000000003e-3` vs
`10 × 3.5000000000000017e-4 = 3.5000000000000017e-3`. A bare `>=` fails on the
correct construction. I gave it a relative tolerance of 1e-9 with a comment
explaining why. This is not the `EPS = 1e-9` Tier-1 exactness convention being
loosened — that governs checker margins in millimetres; this is a dimensionless
ratio in a test, and the repo has direct precedent (commit e4d372c, "compare the
mutation score against a tolerance, not its own rounding").

**Concerns.**

1. **The drift was seen in 2026-07-31 and rationalised away.** The ledger
   `.superpowers/sdd/2026-07-31-functional-checker/multiseed-reliability.md:68`
   says, in its own words, "`tested=11, excluded=1` here vs. `tested=12,
   excluded=0` previously — this reflects the current, already-verified checker
   implementation, not a change made to reach a target number." The composition
   change was *observed*, *written down*, and explained as benign. Nobody asked
   which mate left or why. That is not a testing gap, it is a reading habit, and
   O-C now has teeth against exactly this shape — but only for `tested` and
   `excluded` on this one instrument. Any other instrument-composition
   denominator in the codebase is still guarded by whatever its author chose.

2. **The brief's own test would have shipped the bug it was written to catch.**
   The band binding it specifies passes mate[9]. Both of the two earlier
   proposed repairs missed [9]; the *test* specified to prevent that recurrence
   also missed it. That is three independent artefacts converging on the same
   blind spot — the arithmetic relating 3.5e-4 to `BOUNDARY_BAND * epsilon` was
   never evaluated by anyone, only asserted. I would treat any other
   literal-code block in these briefs as unexecuted until run.

3. **Stale numbers survive in historical ledgers, deliberately.** Roughly a
   dozen files under `.superpowers/sdd/` quote `mean 0.9982 / tested=11`. Those
   are frozen records of runs that genuinely produced those numbers and I did
   not rewrite them. But they are now the majority of grep hits for the Gate A
   reliability figure, and a future reader grepping for the current value will
   find eleven wrong answers before the right one. Nothing to fix today;
   flagging that the pre-registration must quote the spec, never a ledger.

4. **The 3.5e-4 magnitude remains a free parameter**, as spec §8 already
   discloses ("chosen after the seed was pinned … a smaller value fails more
   often"). The construction rule fixes the *shape* of each mate and thereby
   determines the number; it does not make the band magnitude forced. The
   disclosure at spec lines 237–240 still stands and still needs to reach the
   paper. This task did not change that, and should not be read as having
   settled it.
