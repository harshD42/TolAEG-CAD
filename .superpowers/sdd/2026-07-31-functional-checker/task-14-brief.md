### Task 14: Gate A report — v2 criteria

**Files:**
- Modify: `scripts/gate_a.py` (replace `main`)
- Modify: `tests/test_gate_a.py` (extend)

**Interfaces:**
- Consumes: everything above
- Produces: a Gate A table covering all seven spec v2 §7 criteria

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gate_a.py  (append)
def test_gate_a_reports_v2_criteria():
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    for criterion in [
        "Y14.5 worked examples",
        "NIST PMI conformance",
        "TolAnalyst agreement",
        "Monte Carlo convergence",
        "Checker reliability",
        "Validation isolation",
    ]:
        assert criterion in result.stdout, f"missing criterion: {criterion}"


def test_gate_a_not_cleared_without_oracles():
    """Missing oracles must never count as passes."""
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert "NOT CLEARED" in result.stdout
    assert result.returncode != 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gate_a.py -v`
Expected: FAIL — "NIST PMI conformance" and "Checker reliability" are absent from stdout

- [ ] **Step 3: Replace `main` in `scripts/gate_a.py`**

```python
def main() -> int:
    rows: list[tuple[str, str, str]] = []
    passes: list[bool] = []

    def record(name: str, ok: bool | None, note: str) -> None:
        rows.append((name, {True: "PASS", False: "FAIL", None: "SKIP"}[ok], note))
        passes.append(ok is True)

    record("Y14.5 worked examples", _pytest_passes("tests/test_y14_5.py"),
           "100% required")
    record("Monte Carlo convergence", _pytest_passes("tests/test_convergence.py"),
           "+/-0.5% at N=100k")
    record("Checker reliability", _pytest_passes("tests/test_reliability.py"),
           ">=0.95 verdict stability")
    record("Validation isolation", _pytest_passes("tests/test_architecture.py"),
           "no core imports")

    # Oracles: populated in Phase 3, when generated geometry can feed both engines.
    for name, path, threshold in (
        ("NIST PMI conformance", NIST_EXPECTED, 1.00),
        ("TolAnalyst agreement", TOLANALYST_EXPORT, AGREEMENT_THRESHOLD),
    ):
        if not path.exists():
            record(name, None, f"no export at {path.name}")
            continue
        record(name, False, "harness ready; comparison runs in Phase 3")

    width = max(len(r[0]) for r in rows)
    print("\nGate A - checker correctness (blocking)\n")
    for name, status, note in rows:
        print(f"  {name:<{width}}  {status:<5}  {note}")

    cleared = all(passes)
    print(f"\nGate A: {'CLEARED' if cleared else 'NOT CLEARED'}\n")
    return 0 if cleared else 1
```

Also add near the existing constants:

```python
NIST_EXPECTED = REPO / "data" / "nist_pmi_expected.csv"
```

- [ ] **Step 4: Run the full suite and the gate**

Run: `pytest -v && python scripts/gate_a.py`
Expected: all tests pass; Gate A prints six criteria, four PASS, two SKIP, NOT CLEARED.

- [ ] **Step 5: Commit**

```bash
git add scripts/gate_a.py tests/test_gate_a.py
git commit -m "feat: Gate A report covering spec v2 criteria"
```

---

## Plan completion state

At the end of Task 14:

- Tier 1 closed-form checks: implemented, TDD'd, exact
- Tier 2 Monte Carlo: implemented, seeded, convergence-tested
- Checker reliability: measured under perturbation
- Validation isolation: mechanically enforced
- Both oracle harnesses (NIST, TolAnalyst): built and tested
- Gate A: **4 of 6 criteria passing**; both oracle comparisons blocked on the Phase 3 generator

Gate A is not cleared by this plan and is not expected to be. Clearing it requires generated
geometry to feed both oracles, and reading NIST's STEP AP242 semantic PMI needs OCCT XCAF —
a Phase 3 dependency. The gate script reports missing oracles as SKIP and exits non-zero;
a missing oracle is never counted as a pass.

## Open items carried forward

1. **Citation verification (Tasks 4 and 6).** Y14.5 formulas and ISO 286 table values must be
   confirmed against print before any number derived from them enters the paper. The plan
   states this as a requirement; it is not satisfied by the plan itself.
2. **Phase 1 literature study** runs in parallel and is not covered here.
3. **Phase 3 generator** is the next plan.
