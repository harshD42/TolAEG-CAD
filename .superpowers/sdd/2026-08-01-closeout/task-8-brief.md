### Task 8: Commit the stopping criterion and reconcile the ledgers

**Files:**
- Create: `docs/superpowers/specs/2026-08-01-observation-assignment.md`
- Modify: `.superpowers/sdd/*/progress.md` (reconciliation notes)
- Modify: `.gitignore`
- Test: `tests/test_observation_assignment.py`

**Interfaces:**
- Consumes: nothing
- Produces: the committed worked observation table

The observation-assignment table — the artifact that makes the stopping criterion checkable — **exists only in an agent transcript**. That is the *Unencoded* shape from the project's own taxonomy, and the same defect as a 39-cell verification run once in a shell. Separately, the ledgers contradict themselves on nearly every quantity, and Gate D requires every claim traceable to a logged run.

- [ ] **Step 1: Write the failing test**

Create `tests/test_observation_assignment.py`:

```python
"""The stopping criterion is only usable if its worked table is committed."""

import pathlib

DOC = (
    pathlib.Path(__file__).parent.parent
    / "docs" / "superpowers" / "specs" / "2026-08-01-observation-assignment.md"
)


def test_the_observation_table_is_committed():
    assert DOC.is_file(), (
        "the observation-assignment table exists only in a transcript. That is "
        "the Unencoded shape from the design spec's own taxonomy."
    )


def test_every_observation_is_defined_and_every_control_assigned():
    text = DOC.read_text(encoding="utf-8")
    for obs in ("O-A", "O-B", "O-C", "O-D"):
        assert obs in text, f"{obs} is not defined"
    for control in (
        "declared-mutation runner", "B2", "B3", "B10", "B9",
        "mate[8]", "mutual exclusion",
    ):
        assert control in text, f"no observation assignment for {control}"
    assert "silent false green" in text.lower()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_observation_assignment.py -v`
Expected: FAIL — the document does not exist.

- [ ] **Step 3: Write the document and reconcile the ledgers**

Create the spec containing: the four observations; rules R1–R6 as stated in this plan's header; and the worked table with one row per control — *control · failure mode · revealed by · needs its own control?* Include at minimum the declared-mutation runner, `test_the_registry_still_covers_every_critical_guard`, B2, B3, the re-run-and-compare control, B10, B9, the ladder pin, mate[8]'s partial degeneracy, and the mutual-exclusion control from Task 9.

Then reconcile the ledgers: for each contested quantity (the pre-fix d4 rate recorded as both 69.1% and 478/609; the untriaged survivor count recorded as ~12, ~17 and ~27; four coverage values; seven mutation-score values; and the instance numbering, which drifts because the design spec's §1 table enumerates **twelve** shapes against eleven claimed instances) record one canonical value with its provenance and mark the superseded ones as superseded.

Remove `.superpowers/` from being untracked-and-unignored: commit it, so the defect history Gate D's traceability requirement depends on is not one `rm -rf` from gone.

- [ ] **Step 4: Run**

Run: `python -m pytest -q`.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-08-01-observation-assignment.md tests/test_observation_assignment.py .superpowers/
git commit -m "docs: commit the observation-assignment table and reconcile the ledgers"
```

---

