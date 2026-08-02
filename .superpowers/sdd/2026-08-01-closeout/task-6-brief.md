### Task 6: Make Gate A distinguish measured from attested, and restore criterion 1

**Files:**
- Modify: `scripts/gate_a.py`
- Modify: `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`
- Test: `tests/test_gate_a.py`

**Interfaces:**
- Consumes: nothing new
- Produces: a `kind` field on each row, one of `"measured"` or `"attested"`; a restored `"Y14.5 published worked examples"` row

Two of Gate A's six PASSes are human attestations recorded by *deleting a marker string from source*, and `gate_a.py` silently renamed §7's criterion 1 from "Agreement with published Y14.5 worked examples" to "Y14.5 self-consistency". So "6 PASS / 3 SKIP" reads as six measurements when three are.

**QA initially claimed criterion 1 was measured by nothing and then withdrew it**, having verified the three published ASME worked examples *are* encoded at `tests/test_y14_5.py:339, :361, :381` with the standard's own inputs (F=6.0, H=6.44, T=0.44; T=0.22; T1=0.18/T2=0.26) quoted in the docstrings. So this task *adds* a genuinely measured criterion.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_gate_a.py`:

```python
def test_gate_a_distinguishes_measured_rows_from_attested_ones():
    """Two rows PASS because a marker string is absent from source. That is a
    human attestation, not a measurement, and 6 PASS must not read as six."""
    out = _run_gate_a_stdout()
    assert "PASS(attested)" in out, (
        "attested rows must be labelled; otherwise a reader counts them as "
        "measurements"
    )
    for attested in ("Y14.5 citation verified", "ISO 286 transcription verified"):
        line = _row(attested)
        assert "attested" in line, f"{attested} is an attestation and must say so"


def test_criterion_one_is_restored_as_its_own_measured_row():
    """Spec section 7 criterion 1 is agreement with PUBLISHED worked examples.

    gate_a renamed it to "self-consistency" and noted that is arithmetic derived
    from the same unverified formulas -- so the published-examples criterion was
    reported by nothing. The three examples ARE encoded; point the row at them.
    """
    line = _row("Y14.5 published worked examples")
    assert "PASS" in line and "measured" in line
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_gate_a.py -v -k "measured_rows or criterion_one"`
Expected: FAIL — no `kind` label exists and there is no published-worked-examples row.

- [ ] **Step 3: Implement**

Add a `kind` to each recorded row (`"measured"` or `"attested"`), print it as `PASS(measured)` / `PASS(attested)`, have attested rows print their evidence (who, when, which edition and table), and add the restored row running the three node IDs:

```python
_Y14_5_WORKED_EXAMPLE_TESTS = (
    "tests/test_y14_5.py::test_b3_worked_example_boundary_case_assembles",
    "tests/test_y14_5.py::test_b4_worked_example_boundary_case_assembles",
    "tests/test_y14_5.py::test_b4_worked_example_unequal_split_boundary_case_assembles",
)
```

File **amendment 2 of 5** in the correction log:

```markdown
- *2026-08-01g (pre-data):* Gate A's report now distinguishes measured rows from
  human attestations. Two rows ("Y14.5 citation verified", "ISO 286
  transcription verified") PASS iff a marker string is absent from source, which
  is an attestation; reported inside an undifferentiated "6 PASS" they read as
  measurements. Separately, section 7's criterion 1 -- agreement with published
  Y14.5 worked examples -- had been renamed in the harness to "Y14.5
  self-consistency", whose own note records it is "arithmetic derived from the
  same two unverified formulas the implementation uses", so criterion 1 was
  reported by nothing. The three published ASME Appendix B worked examples are
  encoded as tests and criterion 1 is restored as its own measured row; the
  self-consistency check is retained as informational.
```

- [ ] **Step 4: Run**

Run: `python -m pytest -q`, then `python scripts/gate_a.py` and confirm the report now shows seven criteria with `measured`/`attested` labels, still exiting 1.

- [ ] **Step 5: Commit**

```bash
git add scripts/gate_a.py tests/test_gate_a.py docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md
git commit -m "feat: Gate A separates measured from attested and restores criterion 1"
```

---

