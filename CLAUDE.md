# tolcad

Open, GD&T-aware functional checker for toleranced CAD assemblies.
Supports the paper: *Nominally Correct, Functionally Wrong*.
Design spec: `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`

## Conventions

- **All dimensions are millimetres (float).** ISO 286-1 Table 1 publishes IT01-IT11
  in micrometres but IT12-IT18 in millimetres; convert at the table boundary in
  `iso286.py` and nowhere else. `_IT_MICRONS` is micrometres throughout, so the
  IT12-IT14 rows were multiplied by 1000 on entry.
- **Tier 1 is exact.** Closed-form ASME Y14.5. Compare with `EPS = 1e-9`, no looser.
- **Tier 2 is statistical.** Monte Carlo. Always report a seed.
- **`validation/` is optional and one-directional.** It may import core; core may never
  import it. Enforced by `tests/test_architecture.py`.
- **No SolidWorks required for any headline result.** TolAnalyst is a black-box oracle.
- **`pytest` mutates and restores tracked files.** The declared-mutation layer
  (15 registry entries) transiently writes to
  `src/tolcad/{iso286,reliability,y14_5}.py`,
  `src/tolcad/gen/{sampler,layout,features}.py`, the tracked NIST fixture
  `tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp`, and two tracked test files
  `tests/gen/{test_layout,test_features}.py` — then restores them.
  **Never run `pytest` concurrently with `scripts/gate_a.py`,
  `scripts/check_suite_integrity.py`, or anything else that reads
  `src/tolcad/`** — `gate_a.py` shells out to a fresh interpreter that reads the
  checker from disk, so an overlapping run can report a Gate A number measured
  against a mutated checker. Note `y14_5.py` in that list: it is the module
  Gate A's criterion 1 is measured against, so the hazard is not hypothetical.
  This is enforced, not merely advised: `run_declared_mutation` holds
  `.mutation-in-progress` at the repo root for the whole mutate-and-restore
  window, and both scripts exit 2 with a recovery procedure rather than
  measuring a mutated checker.
  `tests/conftest.py` fails the run if the tree is left dirty, but **its scope
  is `src/` and `tests/fixtures/` only** — it does not watch the two
  `tests/gen/` targets, and it cannot detect corruption that existed only
  *during* the run. Recover with
  `git checkout -- src/ tests/fixtures/ tests/gen/`.

## Commands

    pytest                                  # all tests (428)
    pytest -m "not slow"                    # skip Monte Carlo convergence
    python scripts/gate_a.py                # Gate A report (exit 1 until the 3 SKIPs clear)
    python scripts/check_suite_integrity.py # Layers 1 and 2; the pre-merge gate

Run these **one at a time** — see the mutation/concurrency rule above.
`gate_a.py` and `check_suite_integrity.py` exit `2`, distinct from their own
`0`/`1`, when a declared mutation is in flight.

## Do not edit

Pre-registered Gate A/B/C/D thresholds in the design spec §7 are frozen.
Changing one after seeing data invalidates the result.

## Where the numbers live

Several quantities have more than one figure recorded across the ledgers. Exactly
one is live for each, with provenance and the reason the others were superseded:
`docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`. Quote the **spec**,
never a ledger — the superseded reliability figure still outnumbers the correct
one in a grep.
