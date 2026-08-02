# tolcad

[![CI](https://github.com/harshD42/TolAEG-CAD/actions/workflows/ci.yml/badge.svg)](https://github.com/harshD42/TolAEG-CAD/actions/workflows/ci.yml)

**An open, GD&T-aware functional checker for toleranced CAD assemblies.**

Supports the paper *Nominally Correct, Functionally Wrong*.

---

## The problem

A generative CAD model can produce a part that looks correct, scores well on Chamfer distance or
IoU, and **will not assemble** once real manufacturing variation is applied. Every hole is a little
off-size and a little off-position; every fastener has its own tolerance. Whether the parts fit is
a question with a determinate answer, and it is not the question the current metrics ask.

`tolcad` answers it, deterministically, from published standards rather than from opinion:

| Standard | What it supplies |
|---|---|
| **ASME Y14.5-2018** App. B | B-3 floating fastener, B-4 fixed fastener (closed-form, exact) |
| **ISO 286-1:2010** Table 1 | IT grades 5–8 and 12–14 across 13 size bands |
| **ISO 273-1979** Table 1 | Clearance holes, fine/medium/coarse = H12/H13/H14 |
| **ISO 2306-1972** Table 1 | Tapping drill diameters, coarse pitch |

Two tiers:

- **Tier 1 is exact.** Closed-form Y14.5 arithmetic, compared at `EPS = 1e-9`. A boolean verdict.
- **Tier 2 is statistical.** Monte Carlo clearance yield over the tolerance ranges. Always seeded.

No SolidWorks licence is required for any headline result.

## Quickstart

```bash
python -m venv .venv && . .venv/Scripts/activate  # Windows; use bin/activate on Linux
pip install -e ".[dev,gen]"
pytest
```

Expect **428 passed**. Full setup, including the two gitignored payloads and the platform traps,
is in [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md).

```bash
python scripts/gate_a.py
```

**Exits 1, and that is correct today** — three of its criteria are SKIP because they need an oracle
that does not yet exist. See [docs/STATE-OF-PLAY.md](docs/STATE-OF-PLAY.md) before concluding
anything is broken. Several commands here exit non-zero by design.

> **Run these one at a time.** `pytest` transiently mutates tracked files under `src/tolcad/` and
> restores them. `scripts/gate_a.py` and `scripts/check_suite_integrity.py` read the checker from
> disk and exit **2** rather than measure a mutated one. See `CLAUDE.md`.

## Where to start

**→ [docs/START-HERE.md](docs/START-HERE.md)** — the entry point, whether you are a person returning
to this after a break or a fresh AI session with no context.

| Document | Answers |
|---|---|
| [STATE-OF-PLAY](docs/STATE-OF-PLAY.md) | What is true today: every verified number with its provenance, gate status, and open items in dependency order |
| [DECISIONS](docs/DECISIONS.md) | Every human ruling, frozen item, and non-obvious rationale — with a "do not re-litigate" table at the top |
| [SPIKES](docs/SPIKES.md) | Every open unknown, its cheapest decisive experiment, what it blocks, and the fallback if the answer is bad |
| [ENVIRONMENT](docs/ENVIRONMENT.md) | Bare machine → green suite, on both platforms, plus every trap |
| [ledger-reconciliation](docs/superpowers/specs/2026-08-01-ledger-reconciliation.md) | **Which number is live**, when the same quantity appears with different values across the logs |

## Layout

```
src/tolcad/          checker core: y14_5, montecarlo, checker, types, iso286, reliability
src/tolcad/gen/      procedural generator: sampler, layout, features, build, spec, export
scripts/             gate_a.py, check_suite_integrity.py, measure_ladder.py, fetchers
tests/               428 tests, incl. the declared-mutation registry (15 entries)
validation/          optional, one-directional: may import core; core may never import it
docs/                specs, plans, and the context documents above
papers/literature/   111-paper survey corpus (index tracked, PDFs fetched)
.superpowers/        planning artifacts and the hour-by-hour SDD ledgers
```

## How this repo defends its own numbers

The project's recurring failure mode has a name: **the test that cannot fail.** Twelve instances
are catalogued — a coverage floor scoped so it could halve without tripping, an interning check
that never defeated interning, a metric that stayed green while its sample size silently fell.

Three layers ratchet against it — branch coverage, mutation score, and a declared-mutation registry
that mutates the checker and asserts each guard notices — plus a mutual-exclusion lock so no reader
can measure a mutated checker.

The honest finding, recorded because it is more useful than the machinery:
**zero of the twelve instances were found by the three layers. Ten were found by an adversarial
reader over a diff.** Layers ratchet; review discovers. Scheduled adversarial review is a
first-class item, not a nicety.

The rules governing when a new control is justified are in
[observation-assignment.md](docs/superpowers/specs/2026-08-01-observation-assignment.md).

## Status

Pre-registration has **not** yet been published. Until it is, the gate thresholds in design spec §7
are frozen but the corpus and baselines are not yet fixed. Current state, and what blocks what, is
in [STATE-OF-PLAY](docs/STATE-OF-PLAY.md).

## Licence

**None yet** — which legally means all rights reserved. This is a known gap, deliberately deferred
rather than overlooked; it must be resolved before the artifact is released, since the paper's first
contribution claims an *open* tool. Tracked in [DECISIONS](docs/DECISIONS.md).
