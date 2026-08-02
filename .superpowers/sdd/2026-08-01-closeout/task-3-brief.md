### Task 3: Repair the reliability instrument and correct the false frozen statement

**Files:**
- Modify: `scripts/gate_a.py`
- Modify: `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`
- Test: `tests/test_gate_a.py`

**Interfaces:**
- Consumes: `tolcad.reliability.verdict_stability`
- Produces: a repaired `_RELIABILITY_MATES` with `tested == 12, excluded == 0`

**The defect.** `scripts/gate_a.py:108` documents mate[8]'s margin as a **sum**: `(8.5-8.0)+(8.5-8.0) - (0.5+0.49965) = +3.5e-4`. But `y14_5.py:228` implements ASME B-3's per-part rule, `margin = min(margin_a, margin_b)` — deliberately, and the module documents at length why a pooled form is *not* Y14.5-conformant. So `min(0.5-0.5, 0.5-0.49965) = 0.0`: the mate sits at exactly zero, lands in the exclusion band, and is silently dropped.

Measured: `tested=11, excluded=1`. Design spec lines 227-228 assert *"at 12 tested mates the only values reachable near the threshold are 1.0000 and 0.9167."* **Both figures are wrong** — eleven mates, reachable values `{0.9091, 1.0}`.

**QA found a second one:** mate[9] also has a part at exactly zero (`margin_a = +0`), and produces the right answer only because `min()` picks the negative branch. Both originally-proposed repairs left it in place, one sign change from the same failure.

**The construction rule (D-D), which determines the number rather than choosing it:**

> Each sensitive-band mate has **exactly one binding part** at ±3.5e-4; every other part in that mate is slack at ≥10× the band.

Applied to mates [8] and [9] (`[8]`: `pt_a` 0.49965 / `pt_b` 0.49650; `[9]`: `pt_a` 0.50035 / `pt_b` 0.49650) this yields **mean 0.9975, CI [0.9954, 0.9992], tested 12, excluded 0**. Record the rule, not just the outcome.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_gate_a.py`:

```python
def test_every_sensitive_mate_has_exactly_one_binding_part():
    """The construction rule, asserted rather than trusted.

    mate[8] was documented as +3.5e-4 using a SUM, but y14_5 implements B-3's
    per-part min(). Its per-part margins were (0.0, +3.5e-4), so min() gave
    exactly 0.0, the exclusion band swallowed it, and tested silently became 11
    while the frozen spec claimed 12. mate[9] had the same zero part and
    survived only because min() picked its negative branch.
    """
    import scripts.gate_a as mod
    from tolcad.checker import check

    band = mod.BOUNDARY_BAND * mod.RELIABILITY_EPSILON
    for i, mate in enumerate(mod._RELIABILITY_MATES):
        detail = check(mate).detail
        parts = [detail.get("margin_a"), detail.get("margin_b")]
        parts = [p for p in parts if p is not None]
        if not parts:
            continue  # single-expression mate; nothing to balance
        binding = [p for p in parts if abs(p) <= band]
        assert len(binding) == 1, (
            f"mate[{i}] has {len(binding)} parts inside the sensitive band "
            f"{band:.2e} (margins {parts}); the construction rule requires "
            f"exactly one binding part, every other slack at >=10x"
        )


def test_reliability_tested_and_excluded_are_pinned_exactly():
    """O-C: an instrument-composition quantity, pinned two-sided.

    `tested > 0` catches TOTAL degeneracy and missed the PARTIAL degeneracy that
    lived underneath it for four ledgers. Pin the exact composition.
    """
    import scripts.gate_a as mod

    aggregate = mod._aggregate_reliability()
    assert aggregate.tested == 12, (
        f"tested={aggregate.tested}, expected 12. A mate has fallen into the "
        f"exclusion band -- check the per-part margins against the construction rule."
    )
    assert aggregate.excluded == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_gate_a.py -v -k "binding_part or pinned_exactly"`
Expected: FAIL — `test_every_sensitive_mate_has_exactly_one_binding_part` reports mate[8] with 2 binding parts (`0.0` and `3.5e-4`, both inside the band), and `tested` is 11 not 12.

- [ ] **Step 3: Apply the repair**

In `scripts/gate_a.py`, fix mate[8] and mate[9] per the construction rule, and replace both contradicted comments. The comments currently show a sum; they must show the per-part form:

```python
    {
        # B-3 is PER PART: margin = min(H_a-F-T_a, H_b-F-T_b), NOT their sum.
        # Construction rule: exactly one binding part at +3.5e-4; the other slack
        # at >=10x the band. hole_a binds; hole_b is slack.
        #   margin_a = (8.5-8.0) - 0.49965 = +3.5e-4   <- binding
        #   margin_b = (8.5-8.0) - 0.49650 = +3.5e-3   <- slack, 10x
        "type": "floating_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.49965},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.49650},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    },
    {
        #   margin_a = (8.5-8.0) - 0.50035 = -3.5e-4   <- binding
        #   margin_b = (8.5-8.0) - 0.49650 = +3.5e-3   <- slack
        "type": "floating_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.50035},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.49650},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    },
```

Also record the rule above `_RELIABILITY_MATES`:

```python
# CONSTRUCTION RULE (frozen 2026-08-01, spec section 7 correction).
# Each sensitive-band mate has EXACTLY ONE binding part at +-3.5e-4; every other
# part in that mate is slack at >=10x the band. Without this rule the repair is
# under-determined -- two reviewers produced 0.9967 and 0.9971 from different
# constructions of the same stated intent. The rule determines the number.
```

- [ ] **Step 4: Measure and file the amendment**

Run: `python scripts/gate_a.py` and record the new mean, CI, fraction, `tested` and `excluded`.

Add to the design spec's correction log — **amendment 1 of 5**:

```markdown
- *2026-08-01f (pre-data):* The Gate A reliability mate set was repaired. Two
  sensitive-band mates were constructed as though the floating-fastener margin
  were the SUM of both parts' slack; y14_5 implements ASME B-3's per-part
  `min()`. One mate therefore sat at exactly 0.0, fell inside the exclusion
  band, and was silently dropped, so the set measured `tested=11, excluded=1`.
  The correction 2026-08-01e text stating "at 12 tested mates the only values
  reachable near the threshold are 1.0000 and 0.9167" was consequently FALSE:
  eleven were tested and the reachable values were {0.9091, 1.0}. Both mates are
  rebuilt under a construction rule -- exactly one binding part per mate at
  +-3.5e-4, all others slack at >=10x -- which determines the result rather than
  leaving it under-specified. Measured after repair: tested=12, excluded=0.
  Found by adversarial review before any data was generated.
```

- [ ] **Step 5: Run and commit**

Run: `python -m pytest -q`, then `python scripts/gate_a.py > /dev/null 2>&1; echo $?` (expect 1, no pipe).

```bash
git add scripts/gate_a.py tests/test_gate_a.py docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md
git commit -m "fix: repair the reliability mate set and correct the false frozen statement"
```

---

