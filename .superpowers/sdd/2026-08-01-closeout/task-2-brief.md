### Task 2: Make both integrity pins two-sided

**Files:**
- Modify: `scripts/check_suite_integrity.py`
- Test: `tests/test_suite_integrity_script.py`

**Interfaces:**
- Consumes: `COVERAGE_FLOOR`, `MUTATION_MEASURED`, `MUTATION_TOLERANCE` from Task 0's merged state
- Produces: `COVERAGE_MEASURED`, `COVERAGE_TOLERANCE`, `check_two_sided(measured, pinned, tolerance) -> tuple[bool, str]`

Both checks are currently `score >= FLOOR`. A one-sided floor never flags an *improvement*, so the pin silently detaches the moment the next test lands — which is exactly how `MUTATION_MEASURED` drifted 2.04 pp, four times its own tolerance, inside the layer built to catch drift. Re-pinning without making the check two-sided restores the defect.

**Measured values to pin** (architect ran the full layer end-to-end): coverage **94.74%**, mutation **95.89%**.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_suite_integrity_script.py`:

```python
def test_a_measurement_above_the_pin_fails_too():
    """One-sided floors let the pin silently detach. That is how F1 happened.

    MUTATION_MEASURED drifted 2.04pp below the tree -- four times its own
    tolerance -- and the gate stayed green because a floor is a lower bound.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    ok_low, msg_low = mod.check_two_sided(90.0, 95.0, 0.5)
    assert not ok_low and "below" in msg_low.lower()

    ok_high, msg_high = mod.check_two_sided(99.0, 95.0, 0.5)
    assert not ok_high, "an improvement must also fail -- the pin has detached"
    assert "re-pin" in msg_high.lower(), (
        "the upward message must tell the operator to re-pin, not just report"
    )

    ok_mid, _ = mod.check_two_sided(95.2, 95.0, 0.5)
    assert ok_mid


def test_both_pins_are_measured_values_not_round_numbers():
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    for name in ("COVERAGE_MEASURED", "MUTATION_MEASURED"):
        value = getattr(mod, name)
        assert value not in (0, 50, 60, 70, 75, 80, 85, 90, 95, 100), (
            f"{name} = {value} looks aspirational. Run the layer, read the "
            f"number, pin that."
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_suite_integrity_script.py -v -k "two_sided or both_pins"`
Expected: FAIL — `check_two_sided` and `COVERAGE_MEASURED` do not exist.

- [ ] **Step 3: Implement**

In `scripts/check_suite_integrity.py`, replace the two floor constants and add the helper:

```python
# O-C: two-sided pins. A one-sided floor never flags an improvement, so the pin
# silently detaches from the tree the moment the next test lands -- which is
# exactly how the mutation pin drifted 2.04pp, four times its own tolerance,
# inside the layer built to catch drift. Raising a MEASURED value is routine and
# expected; widening a TOLERANCE requires a recorded reason here.
COVERAGE_MEASURED = 94.74   # measured 2026-08-01, gen/ omitted
COVERAGE_TOLERANCE = 0.50
MUTATION_MEASURED = 95.89   # measured 2026-08-01, six core modules
MUTATION_TOLERANCE = 0.50


def check_two_sided(measured: float, pinned: float, tolerance: float) -> tuple[bool, str]:
    """True iff `measured` is within `tolerance` of `pinned`, in either direction."""
    delta = measured - pinned
    if delta < -tolerance:
        return False, f"{measured:.2f} is below the pin {pinned:.2f} by {-delta:.2f}"
    if delta > tolerance:
        return False, (
            f"{measured:.2f} is ABOVE the pin {pinned:.2f} by {delta:.2f} -- the "
            f"tree improved and the pin has detached. Re-pin it and record why."
        )
    return True, f"{measured:.2f} within {tolerance:.2f} of {pinned:.2f}"
```

Wire both layers through `check_two_sided`, and print the returned message.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_suite_integrity_script.py -v`, then `python -m pytest -q`.
Do **not** run `check_suite_integrity.py` itself — it invokes cosmic-ray (~25 min) and must not run concurrently with anything. Task 5 owns that run.

- [ ] **Step 5: Commit**

```bash
git add scripts/check_suite_integrity.py tests/test_suite_integrity_script.py
git commit -m "fix: make both integrity pins two-sided so an improvement cannot detach them"
```

---

