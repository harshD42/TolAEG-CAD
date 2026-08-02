### Task 4: Pin all four ladder counts, reproducibly

**Files:**
- Create: `scripts/measure_ladder.py`
- Create: `tests/gen/test_ladder_pin.py`
- Modify: `pyproject.toml`
- Modify: `tests/mutation_registry.py`

**Interfaces:**
- Consumes: `tolcad.gen.sampler.sample_assembly`, `tolcad.checker.check`
- Produces: `measure_ladder() -> dict[int, tuple[int, int]]` mapping difficulty to `(failures, total)`; `corpus_digest() -> str`

The four numbers going into pre-registration — d1 19.5%, d2 32.9%, d3 52.9%, d4 69.1% — are **pinned by nothing executable**. The only guard bands `rates[0]` and `rates[-1]` over 80 seeds, not 200. QA demonstrated d2 and d3 can move up to **19.3 percentage points** with every guard green, and the `flat-difficulty-ladder` registry entry targets d4 only.

- [ ] **Step 1: Write the failing test**

Create `tests/gen/test_ladder_pin.py`:

```python
"""The four numbers pre-registration will freeze, pinned as exact counts.

O-C. Rates alone are insufficient: a rate is a ratio and hides a change in the
denominator. The counts are what a third party reproduces.
"""

import numpy as np
import pytest

from scripts.measure_ladder import LADDER_RECIPE, corpus_digest, measure_ladder

# Measured 2026-08-01 on numpy 2.4.1 over seeds 0-199. See D-C: the numpy
# version is pinned because Generator's stream is NOT covered by NEP 19.
EXPECTED_COUNTS = {1: (31, 159), 2: (99, 301), 3: (239, 452), 4: (421, 609)}
EXPECTED_DIGEST = None  # filled in Step 3 from the measured value


@pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
def test_each_ladder_level_matches_its_exact_pinned_counts(difficulty):
    failures, total = measure_ladder()[difficulty]
    exp_f, exp_t = EXPECTED_COUNTS[difficulty]
    assert (failures, total) == (exp_f, exp_t), (
        f"d{difficulty} measured {failures}/{total}, pinned {exp_f}/{exp_t}. "
        f"numpy=={np.__version__} (pinned 2.4.1; Generator's stream is not "
        f"guaranteed across releases). If this is an intended change, re-measure "
        f"ALL FOUR levels and re-pin -- and note the pre-registration freezes them."
    )


def test_the_corpus_digest_is_reproducible():
    assert corpus_digest() == EXPECTED_DIGEST, (
        f"the corpus changed. Recipe: {LADDER_RECIPE}"
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/gen/test_ladder_pin.py -v`
Expected: FAIL — `scripts.measure_ladder` does not exist.

- [ ] **Step 3: Implement, measure, and pin**

Create `scripts/measure_ladder.py`:

```python
#!/usr/bin/env python
"""Reproduce the pre-registered difficulty ladder and the corpus digest.

WHY THIS EXISTS. The four ladder rates appeared in five ledgers and would have
gone into the pre-registration, but no script produced them and no test pinned
them. A pre-registered number that no executable artifact reproduces is
unverifiable, which is the purest form of this project's dominant failure mode.

Usage: python scripts/measure_ladder.py
"""

from __future__ import annotations

import hashlib
import json

from tolcad.checker import check
from tolcad.gen.sampler import sample_assembly

# The recipe, written down so the digest means something. Changing any element
# changes the digest by design.
LADDER_RECIPE = {
    "seeds": "range(0, 200)",
    "difficulties": [1, 2, 3, 4],
    "counted": "Tier 1 mates only (kind != 'iso_fit')",
    "statistic": "check(mate.to_check_dict()).assembles is False",
}


def measure_ladder() -> dict[int, tuple[int, int]]:
    """Return {difficulty: (tier1_failures, tier1_total)} over seeds 0-199."""
    out: dict[int, tuple[int, int]] = {}
    for difficulty in LADDER_RECIPE["difficulties"]:
        failures = total = 0
        for seed in range(200):
            for mate in sample_assembly(seed, difficulty).mates:
                if mate.kind == "iso_fit":
                    continue
                total += 1
                if not check(mate.to_check_dict()).assembles:
                    failures += 1
        out[difficulty] = (failures, total)
    return out


def corpus_digest() -> str:
    """SHA-256 over every sampled spec, in a defined order."""
    hasher = hashlib.sha256()
    for difficulty in LADDER_RECIPE["difficulties"]:
        for seed in range(200):
            hasher.update(sample_assembly(seed, difficulty).to_json().encode("utf-8"))
    return hasher.hexdigest()


def main() -> int:
    counts = measure_ladder()
    for difficulty, (failures, total) in sorted(counts.items()):
        print(f"  d{difficulty}: {failures}/{total} = {100 * failures / total:.2f}% fail")
    print(f"  corpus digest: {corpus_digest()}")
    print(f"  recipe: {json.dumps(LADDER_RECIPE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Run `python scripts/measure_ladder.py`, confirm the counts are 31/159, 99/301, 239/452, 421/609, and paste the printed digest into `EXPECTED_DIGEST`.

Pin numpy in `pyproject.toml` (D-C):

```toml
dependencies = ["numpy==2.4.1"]
```

Add a middle-row declared mutation to `tests/mutation_registry.py` — the existing `flat-difficulty-ladder` entry targets d4 and misses the d2/d3 hole:

```python
    DeclaredMutation(
        name="ladder-d2-row-shifted",
        target="src/tolcad/gen/sampler.py",
        find="    2: (0.65, 1.16),",
        replace="    2: (0.70, 1.24),",
        test="tests/gen/test_ladder_pin.py::test_each_ladder_level_matches_its_exact_pinned_counts",
        expect="fail",
        why=(
            "The monotonicity guard bands only d1 and d4. QA demonstrated d2 and "
            "d3 can move up to 19.3 percentage points with every guard green, and "
            "flat-difficulty-ladder targets the d4 row only. These four counts go "
            "into the pre-registration."
        ),
    ),
```

Add `"ladder-d2-row-shifted"` to `_CRITICAL_GUARDS` in `tests/test_declared_mutations.py`.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/gen/test_ladder_pin.py tests/test_declared_mutations.py -v`, then the full suite.
Expected: PASS. The new registry entry proves the pin can fail — the runner mutates d2 and requires the pin to notice.

- [ ] **Step 5: Commit**

```bash
git add scripts/measure_ladder.py tests/gen/test_ladder_pin.py pyproject.toml tests/mutation_registry.py tests/test_declared_mutations.py
git commit -m "feat: pin all four ladder counts and the corpus digest, on a pinned numpy"
```

---

