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
  transiently writes to `src/tolcad/{iso286,reliability}.py`,
  `src/tolcad/gen/{sampler,layout,features}.py` and one tracked fixture, then
  restores them. **Never run `pytest` concurrently with `scripts/gate_a.py`,
  `scripts/check_suite_integrity.py`, or anything else that reads
  `src/tolcad/`** — `gate_a.py` shells out to a fresh interpreter that reads the
  checker from disk, so an overlapping run can report a Gate A number measured
  against a mutated checker. `tests/conftest.py` fails the run if the tree is
  left dirty; it cannot detect corruption that existed only *during* the run.

## Commands

    pytest                      # all tests
    pytest -m "not slow"        # skip Monte Carlo convergence
    python scripts/gate_a.py    # Gate A report

## Do not edit

Pre-registered Gate A/B/C/D thresholds in the design spec §7 are frozen.
Changing one after seeing data invalidates the result.
