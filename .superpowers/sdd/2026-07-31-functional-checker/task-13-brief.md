### Task 13: Checker reliability under perturbation

**Files:**
- Create: `src/tolcad/reliability.py`
- Test: `tests/test_reliability.py`

**Interfaces:**
- Consumes: `check` from `tolcad.checker`, `Verdict`
- Produces: `verdict_stability(mates: list[dict], epsilon: float, seed: int) -> float`

Spec v2 §7 adds a **checker reliability ≥ 0.95** criterion, because correlation is attenuated
by √(reliability) — an unreliable oracle silently shifts Gate B's result across a threshold.

**What reliability means here.** Tier 1 is deterministic, so naive test-retest is trivially
1.0 and measures nothing. The meaningful question is whether a perturbation *small relative to
the decision margin* flips the verdict. Near the boundary a flip is **correct behaviour**, not
unreliability — so cases with `|margin| < 10·epsilon` are excluded from the denominator and
reported separately.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_reliability.py
import pytest
from tolcad.reliability import verdict_stability

HOLE = {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.1}
BOLT = {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0}


def _mate(position_tol: float) -> dict:
    hole = dict(HOLE, position_tol=position_tol)
    return {"type": "floating_fastener", "hole_a": hole, "hole_b": hole,
            "fastener": dict(BOLT)}


def test_far_from_boundary_verdicts_never_flip():
    # Allowable is 0.5; these are all far from it in both directions.
    mates = [_mate(t) for t in (0.05, 0.10, 0.15, 0.90, 0.95)]
    assert verdict_stability(mates, epsilon=1e-6, seed=0) == pytest.approx(1.0)


def test_near_boundary_cases_are_excluded_not_counted_as_failures():
    # position_tol 0.5 sits exactly on the allowable boundary.
    mates = [_mate(0.5)]
    # All cases excluded -> stability is undefined, reported as 1.0 with zero denominator.
    assert verdict_stability(mates, epsilon=1e-3, seed=0) == pytest.approx(1.0)


def test_stability_is_deterministic_for_a_given_seed():
    mates = [_mate(t) for t in (0.05, 0.2, 0.8)]
    a = verdict_stability(mates, epsilon=1e-6, seed=7)
    b = verdict_stability(mates, epsilon=1e-6, seed=7)
    assert a == b


def test_empty_input_rejected():
    with pytest.raises(ValueError, match="at least one mate"):
        verdict_stability([], epsilon=1e-6, seed=0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_reliability.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.reliability'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/reliability.py
"""Gate A: verdict stability under input perturbation.

An unreliable oracle attenuates every downstream correlation by sqrt(reliability),
which can move Gate B's result across a pre-registered threshold. This measures it.
"""

from __future__ import annotations

import copy

import numpy as np

from tolcad.checker import check

# Cases whose margin is within this multiple of epsilon are genuinely ambiguous;
# a flip there is correct behaviour, so they are excluded from the denominator.
BOUNDARY_BAND = 10.0

_PERTURBABLE = ("nominal", "lower_dev", "upper_dev", "position_tol")


def _perturb(mate: dict, epsilon: float, rng: np.random.Generator) -> dict:
    out = copy.deepcopy(mate)
    for value in out.values():
        if isinstance(value, dict):
            for key in _PERTURBABLE:
                if key in value:
                    value[key] += float(rng.uniform(-epsilon, epsilon))
    return out


def verdict_stability(mates: list[dict], epsilon: float, seed: int) -> float:
    """Fraction of non-boundary mates whose verdict survives an epsilon perturbation.

    Returns 1.0 when every case falls inside the boundary band (nothing to test).
    """
    if not mates:
        raise ValueError("need at least one mate to measure stability")

    rng = np.random.default_rng(seed)
    tested = stable = 0

    for mate in mates:
        base = check(mate)
        if abs(base.margin) < BOUNDARY_BAND * epsilon:
            continue  # genuinely ambiguous; a flip here is correct
        tested += 1
        if check(_perturb(mate, epsilon, rng)).assembles == base.assembles:
            stable += 1

    return 1.0 if tested == 0 else stable / tested
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_reliability.py -v`
Expected: PASS, 4 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/reliability.py tests/test_reliability.py
git commit -m "feat: verdict stability under perturbation (Gate A reliability)"
```

---

