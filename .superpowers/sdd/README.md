# SDD ledgers — contemporaneous records, NOT a source of numbers

These are the subagent-driven-development ledgers: one directory per plan, each holding a
`progress.md` written hour by hour while the plan executed, plus the per-task briefs and
implementer/reviewer reports beside it.

## Read this before you quote anything from here

**Every figure in these files was true of the tree as it stood that hour.** Many have since been
superseded — the same quantity appears with different values in different ledgers, and the ledgers
do not know about each other. That is not corruption; it is what a contemporaneous log is.

> **The canonical value for any contested quantity is in
> [`docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`](../../docs/superpowers/specs/2026-08-01-ledger-reconciliation.md).**
> That file names one live value per quantity with its provenance and marks every other recorded
> figure SUPERSEDED with the reason.

A concrete example of the hazard: roughly a dozen ledgers here still carry the reliability figure
`mean 0.9982 / tested=11`. It is wrong — it was measured against a defective mate set. The live
value is `0.9975 / tested=12`. The wrong figure **outnumbers the right one in a grep**, which is
exactly why the reconciliation exists and why the standing rule is that **the pre-registration
quotes the spec, never a ledger.**

## What these are good for

- **Why** something is the way it is — the reasoning, the rejected alternatives, the human rulings.
- **What was already tried**, so a later session does not repeat a dead end.
- **Provenance.** The reconciliation doc cites these files by `path:line`. Those citations only
  resolve if these files are in the clone.

## Why they are tracked now

They were deliberately untracked until 2026-08-01, on the reasoning that Gate D's traceability
requirement needs the *adjudicated* value and its executable pin, not the raw hour-by-hour log —
and that committing ~100 mutually contradictory files would make the wrong figures part of the
record.

That reasoning was sound for the question it answered. It does not answer a different one:
**the work has to resume from a clone on another machine.** Untracked ledgers do not clone. Neither
do the reconciliation document's own `path:line` provenance citations, which would dangle.

Resolved by tracking them behind this warning rather than by dumping them unlabelled. The `*.diff`
review artifacts stay ignored — every commit they span is in history, so `git diff <a>..<b>`
reconstructs any of them exactly.

## Index

| Plan | Ledger |
|---|---|
| Functional checker (Phase 1–2) | `2026-07-31-functional-checker/` |
| Procedural generator (Phase 3) | `2026-08-01-procedural-generator/` |
| Pre-registration prep (3.5a) | `2026-08-01-pre-registration-prep/` |
| ISO 273 traceability (3.5b) | `2026-08-01-iso273-traceability/` |
| Suite integrity | `2026-08-01-suite-integrity/` |
| Close-out (nine tasks) | `2026-08-01-closeout/` |

Start instead at [`docs/START-HERE.md`](../../docs/START-HERE.md) unless you specifically need
the narrative of how a decision was reached.
