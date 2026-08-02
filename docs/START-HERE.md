# Start here

You are picking up `tolcad` cold — either a person returning after a break, or an AI session with
no history. This page is the only one you need to read first. Everything else is reachable from it.

**Written 2026-08-01 against `main`. If `git log` shows commits after that, trust the code over
this page and say so.**

---

## Sixty seconds

`tolcad` measures whether a CAD assembly **actually assembles** once real manufacturing variation
is applied — deterministically, from ASME Y14.5 and the ISO tolerance standards. Generative CAD is
currently evaluated on shape similarity, which cannot see this. The paper's claim is that measuring
it changes model rankings.

The checker works. It is not the risk. The risk has always been **whether its numbers can be
trusted**, and most of the effort to date has gone there.

Right now:

- **428 tests pass.** `pytest`.
- **`scripts/gate_a.py` exits 1**, and that is correct — three criteria SKIP for want of an oracle.
- **`scripts/check_suite_integrity.py` exits 1**, and that is correct — a pin fired.
- **Nothing is pre-registered yet.** The gate thresholds are frozen; the corpus and baselines are not.

## Read in this order

| # | Document | Why |
|---|---|---|
| 1 | [STATE-OF-PLAY](STATE-OF-PLAY.md) | What is true today. Every number with its provenance, gate status, open items in dependency order. |
| 2 | [DECISIONS](DECISIONS.md) | 77 decisions. **Read the "do not re-litigate" table at the top before you change anything.** |
| 3 | [SPIKES](SPIKES.md) | 29 open unknowns, each with its cheapest decisive experiment and what breaks if the answer is bad. |
| 4 | [ENVIRONMENT](ENVIRONMENT.md) | Bare machine → green suite. Read before running anything. |

Then the plan for whatever you are actually doing (below).

Do **not** start by reading the `.superpowers/sdd/` ledgers. They are hour-by-hour records full of
superseded figures, kept for narrative and provenance. When two documents disagree on a number,
[ledger-reconciliation.md](superpowers/specs/2026-08-01-ledger-reconciliation.md) says which one is
live.

## What to do next, and in what order

The ordering is not preference. Each item names what it blocks.

**1. The baseline runnability audit → [containerization plan](superpowers/plans/2026-08-02-baseline-containerization.md)**
~10 days, blocked by nothing, **blocks pre-registration irreversibly.** Gate C's frozen criterion
is "effect holds across ≥6 of ≥8 baselines" and the spec names **nine** models — one spare. If
fewer than eight run, the criterion is unmeetable, and after the freeze there is no honest
recovery. Pilot two models first (cadrille, then DeepCAD) so a bad answer arrives on day one while
the model list can still change.

**2. P1.5, the mutation-score repair → [triage plan](superpowers/plans/2026-08-02-mutation-survivor-triage.md)**
The Layer 2 score reads 100.00% and **it is an artefact** — diagnosed 2026-08-01, see below. Needs
`src/` and `tests/` frozen while it runs. The pre-registration plan argues it does *not* block the
freeze; read that argument before reordering.

**3. Pre-registration → [pre-registration plan](superpowers/plans/2026-08-02-pre-registration.md)**
~8.25 days. Gated on item 1 and on a re-measured reliability sweep. Publishes to OSF plus Zenodo;
a signed git tag is navigation only, not immutability.

**4. Phase 4** — corpus, `metrics/`, `harness/`, `analysis/`, the baselines. Not yet planned in detail.

## The one thing to understand about this codebase

Its recurring defect has a name: **the test that cannot fail.** Twelve instances are catalogued —
a coverage floor scoped so core coverage could halve without tripping it; an interning check that
never defeated interning; a reliability metric that stayed green while its sample size silently
fell from twelve to eleven.

Three layers ratchet against it, plus a lock so no reader can measure a mutated checker. But the
honest finding is:

> **Zero of the twelve instances were found by the three layers. Ten were found by an adversarial
> reader over a diff.**

Layers ratchet. Review discovers. Budget the review.

Instances are referred to **by name, never by ordinal** — the canonical count is twelve and the old
numbering is superseded, because only six of the twelve positions are reconstructible and inventing
the rest would be the same defect in a new coat.

Two were found *while assembling this handoff*, which is the point:

- **The O-B finalizer capture — a control disabled another control.** The session finalizer that
  fails the suite if it leaves the tree dirty also fires when *cosmic-ray* dirties the tree, which
  it does for every mutant by construction. Every mutant was recorded killed; Layer 2 has measured
  nothing since that finalizer landed. Proven in a scratch clone: seven tests pass against an
  undetectable edit and the run still exits 1. It caught **13 of the 15** declared mutations too —
  four of which have never once been executed honestly. **The two-sided pin caught it. A one-sided
  floor would have read 100.00 ≥ 93.35 and stayed green forever.**
- **The unfalsifiable k-sweep.** The obvious way to re-measure the reliability headroom scales
  `epsilon` at the call site, which pushes the sensitive mates inside the exclusion band, collapses
  the sample from twelve to six, and reports a perfect 1.0000 at every setting. The bug was rebuilt
  *inside the measurement written to bound an earlier instance of the same bug.*

Before you add a control, check [observation-assignment.md](superpowers/specs/2026-08-01-observation-assignment.md).
It gives the rule for when a new one is justified: name the observation that fails to reveal the
defect. If you cannot, you do not need the control.

## Open questions that need a human

Do not resolve these by inference. They are recorded in [DECISIONS](DECISIONS.md) and
[SPIKES](SPIKES.md) with full context.

1. **`LICENSE` — deliberately deferred.** The repo is public with no licence, which legally means
   all rights reserved. The paper's first contribution claims an *open* tool. Must be settled before
   artifact release.
2. **Is residual R-e discharged?** The same ledger records the CRLF/`.gitattributes` hole as CLOSED
   *and* as "untested by construction." A test exists that post-dates the residual and does real
   nested clones across all three `autocrlf` settings, which probably discharges it — but Gate A's
   fresh-clone row is still SKIP and nobody has ruled.
3. **Should the declared-mutation registry size be executably pinned?** It was recorded as
   "uncontested at 14" while the tree held 15. The figure went stale inside the one document whose
   job is to hold non-stale figures, because nothing pins it.
4. **The observation table does not cover the two `tests/gen/` mutation targets.** Its rows assign
   restore-residue to O-B and are literally accurate — they say "a `src/` file" — but O-B's watch
   set excludes `tests/gen/`. Changing a "revealed by" cell is a control decision, not an edit.

## Working conventions

- **Run one thing at a time.** `pytest` transiently mutates files under `src/tolcad/`; readers of
  `src/` exit **2** rather than measure a mutated checker. `CLAUDE.md` has the rule and the recovery.
- **Quote the spec, never a ledger.** The superseded reliability figure still outnumbers the correct
  one in a grep.
- **Frozen means frozen.** Design spec §7's Gate A–D thresholds do not change. Corrections go in as
  numbered amendments showing the superseded text — see `2026-08-01f` through `k` for the form.
  Correcting a falsehood pre-data is legitimate; reacting to an outcome is not.
- **Plans in this repo have a bad record for code snippets.** Six consecutive tasks found plan code
  that did not run as written — wrong threshold directions, nonexistent symbols, a rationale that
  was exactly backwards. Verify against real source before pasting. Fixing the plan is expected.
- **TDD, and watch the test fail first.** In a project whose signature defect is tests that cannot
  fail, a test never observed failing is not evidence.
