# Fix round report — suite integrity, F-1 to F-4

Branch `feat/suite-integrity`. Base 3f26dc8. Commits **28a478b..0b6e878** (three).

## Status

All four findings closed. One additional defect was found and fixed in the same
round. Two items are recorded as still open and deliberately not fixed here.

## Verification

| Check | Result |
|---|---|
| `python -m pytest -q` | **305 passed** (baseline 300 at 3f26dc8, +5) |
| `python scripts/check_suite_integrity.py` | measured **91.64%**, floor **91.64%**, PASS, **exit 0** |
| `python scripts/check_suite_integrity.py --self-test-failure` | **exit 1** |
| `python scripts/gate_a.py` | **exit 1**, **6 PASS / 3 SKIP** |
| Tier 1 ladder, seeds 0–199 | **d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%** (unchanged) |
| `git status --short` before each commit | clean |

The +5 tests are: two new registry entries, two write-restore tests, and one
new Gate A reliability guard.

## F-1 — the coverage floor was itself a metric that cannot fail

`COVERAGE_FLOOR` was 48.0 measured with `--cov=src/tolcad`. That scope includes
`src/tolcad/gen/` (~222 statements) which the core test subset never exercises
**by design**: `gen/` is excluded from Layers 1 and 2 (design spec non-goals,
CadQuery mutants are slow and geometrically noisy) and covered by Layer 3
instead. So 48% was largely measuring an intended, permanent exclusion, and core
coverage could halve without tripping the floor.

Fix: `[tool.coverage.run] omit = ["src/tolcad/gen/*"]` in `pyproject.toml`, with
the reason recorded there at length so the omission is not "fixed" later. Added
`[tool.coverage.report] precision = 2` so the pin is a measurement rather than a
rounded number.

Re-measured: **91.64%** — 233 stmts / 15 miss / 90 branch / 12 partial
(checker 100.00, reliability 98.53, types 91.84, iso286 88.89, y14_5 87.34,
montecarlo 85.19). Pinned at 91.64. Not a round number, so the existing
round-number test is untouched and still passes.

Note the omission is self-detecting: deleting it drops the measurement to ~48%,
far below the floor, and the gate fails loudly rather than quietly stopping.

## F-2 — the registry entry the plan dropped. **Both instances closed.**

The spec's Layer 3 seed table names a `reliability` entry; the plan substituted
`stale-literal-wall-floor` for it and the swap went unnoticed, leaving
instances 2 and 4 covered by nothing.

Closed with **two** entries, because neither subsumes the other — verified, not
assumed.

### `reliability-perturbation-neutered` — instance 2

`src/tolcad/reliability.py`, `_PERTURBABLE = (...)` → `_PERTURBABLE = ()`.
`_perturb` then returns an unmodified deepcopy, `check` is deterministic, so
`verdict_stability` becomes mathematically incapable of returning below 1.0 —
while still reporting a healthy `tested` count, which is what made the original
hard to see.

Guard: `tests/test_reliability.py::test_positive_control_detects_instability`.
Evidence, mutation applied by hand and target test run directly:

```
E  AssertionError: Positive control failed: expected stability < 1.0 but got 1.0 (tested=100)
E  assert 1.0 < 1.0
E   +  where 1.0 = StabilityResult(value=1.0, tested=100, excluded=0, ...).value
1 failed in 0.12s
```

Gate A does **not** catch this mutation: its reliability mean reads 1.0000 and
the row passes. That is why the second entry exists.

### `reliability-perturbation-tripled` — instance 4

`rng.uniform(-epsilon, epsilon)` → `rng.uniform(-3.0 * epsilon, 3.0 * epsilon)`:
the measured quantity perturbed by an amount that ought to matter, with the
exclusion band left at `epsilon`.

Guard: the new
`tests/test_gate_a.py::test_gate_a_reliability_criterion_holds_for_the_real_measurement`,
which asserts the real aggregate mean clears the pre-registered 0.95 and that
`tested > 0`. Evidence:

```
E  AssertionError: Gate A's reliability criterion is no longer met by the real
   measurement: mean 0.9068 over 200 pre-registered seeds, threshold 0.95.
E  assert 0.9068181818181817 >= 0.95
1 failed in 0.19s
```

The unit positive control does **not** catch this mutation (more flips still
means value < 1.0), confirming the two entries are independent.

**Headroom, measured rather than assumed** (200 pre-registered seeds, 11 tested
mates), scaling the perturbation by `k`:

| k | mean | Gate A criterion |
|---|---|---|
| 1 | 0.9982 | PASS (shipped) |
| 2 | 0.9518 | PASS — **not caught**, 0.0018 above threshold |
| 3 | 0.9068 | FAIL — caught |

So the criterion's sensitivity is roughly 2–3×: not the 1000× of the instance it
replaces, and not infinite either. That bound is recorded in the target test's
docstring and must be re-measured if `_RELIABILITY_MATES` or
`_RELIABILITY_EPSILON` changes.

`scripts/gate_a.py` was not modified. The pre-registered 0.95 threshold is
unchanged. Neither entry targets `gate_a.py`.

Registry is now 11 entries; `_CRITICAL_GUARDS` is 11.

## F-3 — overstated claim in `mc-seed-base-shifted`

`why=` rewritten to state the actual scope: the mutation is load-bearing (the
H7/k6 margin moves 0.68925 → 0.68617) but the guarded assertion is on booleans
that are seed-invariant by construction, because `assembles == (es <= 0)` for
every fit currently in `SUPPORTED_FITS`. It is a **tripwire** for a line-to-line
fit such as H7/h6 re-entering `SUPPORTED_FITS` — the Phase 3.5a reintroduction
path — not a general seed-robustness check. Entry kept; it is cheap and that
path is live.

## F-4 — acknowledged gap made explicit

`test_the_registry_still_covers_every_critical_guard`'s docstring now states
that it is a paper-trail mechanism, defeated by one commit that removes an entry
and its name from `_CRITICAL_GUARDS` together, and names the related gap that
nothing forces a *new* guard to be registered. Design spec §9's open question,
stated rather than left to be rediscovered.

## New defect found and fixed in this round

Running two entries that target the **same file** back to back raised
`OSError: [Errno 22] Invalid argument` on the **restore** write and left
`src/tolcad/reliability.py` mutated in the working tree. Reproduced once in
roughly a dozen runs on Windows; the likely trigger is a scanner or write-back
still holding the file written milliseconds earlier. The design's "restore
mismatch must be loud" was satisfied in letter, but what the operator saw was a
`pathlib` traceback, not the named-file message.

`_write_bytes_resiliently` now retries with backoff (5 attempts), and a
persistent failure raises a loud `AssertionError` naming the file and the
`git checkout --` command to run — deliberately from the `finally` block, so it
masks any in-flight error, because a mutated file on disk is the worse outcome.
Two tests cover the retry-then-succeed and the persistent-failure paths. This
upgrades, but does not eliminate, SI-1's "not crash-safe" note.

## Still open — deliberately not fixed here

1. **Gate A itself cannot see a vacuous reliability 1.0.** If every mate were
   excluded, `gate_a.py` would print `tested=0` and the row would still read
   PASS; no gate row asserts `tested > 0`. The new test layer does assert it, so
   the defect is covered by the suite, but the gate script is not fixed —
   `gate_a.py` is out of scope for this round.
2. **The design spec now understates the registry.** §4's seed table lists nine
   entry kinds and §8 distributes eleven instances against them; the registry is
   now eleven entries. SI-5's instance map should be reconciled against the
   registry, not against the table.

## Constraints honoured

No permanent modification to any checker-core module (`reliability.py` is
restored byte-identically; verified after every experiment and by a clean
`git status`). The `mutation` marker remains selected by default. No changes to
`scripts/gate_a.py`, to design spec §7 thresholds, to `_IT_MICRONS`,
`_DEVIATION_MICRONS`, `_SIZE_BANDS`, `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`,
`_TOL_FRACTION_RANGE`, `_MIN_WALL_MM` or `_EDGE_MARGIN_MM`. Layer 2 not
implemented. mm as float; Tier 1 exact at EPS = 1e-9 untouched.
