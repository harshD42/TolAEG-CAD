# Functional Checker Implementation Plan (Phases 0 & 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an open, GD&T-aware functional checker that decides whether toleranced CAD parts will assemble, and clear blocking Gate A.

**Architecture:** Two tiers. Tier 1 evaluates closed-form ASME Y14.5 conditions (virtual condition, floating/fixed fastener) — exact arithmetic, zero checker error. Tier 2 runs Monte Carlo stack-up over ISO 286 fits. A thin `checker.py` dispatches on mate type. An optional `validation/` package cross-checks against SolidWorks TolAnalyst and is never imported by core code.

**Tech Stack:** Python 3.11+, pytest, NumPy, `dataclasses`. CadQuery/OCC arrive in Phase 3, not here.

## Global Constraints

- **All dimensions in millimetres, stored as `float`.** ISO 286 table values are published in µm and MUST be converted at the table boundary, never later.
- **No core module may import from `validation/`.** Enforced by a test in Task 9.
- **Every headline path runs with no SolidWorks license.** `validation/` is optional and import-guarded.
- **No internal or proprietary company data. No SolidWorks implementation details.** TolAnalyst is a black-box oracle — record its verdicts, never its mechanism.
- **Tier 1 must be exact.** No floating-point tolerance slop in Tier 1 comparisons beyond an explicit `EPS = 1e-9`.
- **Pre-registered Gate A thresholds are fixed** (spec §7) and MUST NOT be edited by any task in this plan.

---

### Task 1: Repository scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/tolcad/__init__.py`
- Create: `tests/test_smoke.py`
- Create: `CLAUDE.md`
- Create: `.gitignore`

**Interfaces:**
- Consumes: nothing
- Produces: importable package `tolcad`; `pytest` runnable from repo root

- [ ] **Step 1: Write the failing test**

```python
# tests/test_smoke.py
def test_package_imports():
    import tolcad
    assert tolcad.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad'`

- [ ] **Step 3: Create the package files**

```toml
# pyproject.toml
[project]
name = "tolcad"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["numpy>=1.26"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov>=5.0"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

```python
# src/tolcad/__init__.py
"""Open GD&T-aware functional checker for toleranced CAD assemblies."""

__version__ = "0.1.0"
```

```
# .gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
*.egg-info/
build/
dist/
.venv/
results/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pip install -e ".[dev]" && pytest tests/test_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Write CLAUDE.md**

```markdown
# tolcad

Open, GD&T-aware functional checker for toleranced CAD assemblies.
Supports the paper: *Nominally Correct, Functionally Wrong*.
Design spec: `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`

## Conventions

- **All dimensions are millimetres (float).** ISO 286 tables publish micrometres;
  convert at the table boundary and nowhere else.
- **Tier 1 is exact.** Closed-form ASME Y14.5. Compare with `EPS = 1e-9`, no looser.
- **Tier 2 is statistical.** Monte Carlo. Always report a seed.
- **`validation/` is optional and one-directional.** It may import core; core may never
  import it. Enforced by `tests/test_architecture.py`.
- **No SolidWorks required for any headline result.** TolAnalyst is a black-box oracle.

## Commands

    pytest                      # all tests
    pytest -m "not slow"        # skip Monte Carlo convergence
    python scripts/gate_a.py    # Gate A report

## Do not edit

Pre-registered Gate A/B/C/D thresholds in the design spec §7 are frozen.
Changing one after seeing data invalidates the result.
```

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src tests CLAUDE.md .gitignore
git commit -m "feat: repository scaffold and project conventions"
```

---

### Task 2: Core domain types

**Files:**
- Create: `src/tolcad/types.py`
- Test: `tests/test_types.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `FeatureType` enum: `INTERNAL`, `EXTERNAL`
  - `FeatureOfSize(nominal: float, lower_dev: float, upper_dev: float, feature_type: FeatureType, position_tol: float = 0.0)` with properties `mmc -> float`, `lmc -> float`
  - `Verdict(assembles: bool, margin: float, method: str, detail: dict)`

`mmc` is the maximum-material condition: the **largest** size for an external feature, the **smallest** for an internal one. `margin` is positive when assembly is guaranteed, in mm.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_types.py
import pytest
from tolcad.types import FeatureOfSize, FeatureType, Verdict


def test_internal_feature_mmc_is_smallest_size():
    # Ø8.5 +0.2/-0.0 hole
    hole = FeatureOfSize(8.5, 0.0, 0.2, FeatureType.INTERNAL)
    assert hole.mmc == pytest.approx(8.5)
    assert hole.lmc == pytest.approx(8.7)


def test_external_feature_mmc_is_largest_size():
    # Ø8.0 +0.0/-0.1 pin
    pin = FeatureOfSize(8.0, -0.1, 0.0, FeatureType.EXTERNAL)
    assert pin.mmc == pytest.approx(8.0)
    assert pin.lmc == pytest.approx(7.9)


def test_verdict_is_immutable():
    v = Verdict(assembles=True, margin=0.5, method="floating_fastener", detail={})
    with pytest.raises(AttributeError):
        v.assembles = False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_types.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.types'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/types.py
"""Core domain types. All dimensions in millimetres."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

EPS = 1e-9


class FeatureType(Enum):
    """Whether a feature of size removes or adds material."""

    INTERNAL = "internal"  # hole, slot, bore
    EXTERNAL = "external"  # pin, shaft, boss


@dataclass(frozen=True)
class FeatureOfSize:
    """A toleranced feature of size, per ASME Y14.5.

    Deviations are signed offsets from nominal, in mm.
    A Ø8.5 +0.2/-0.0 hole is FeatureOfSize(8.5, 0.0, 0.2, INTERNAL).
    """

    nominal: float
    lower_dev: float
    upper_dev: float
    feature_type: FeatureType
    position_tol: float = 0.0

    def __post_init__(self) -> None:
        if self.upper_dev < self.lower_dev:
            raise ValueError(
                f"upper_dev {self.upper_dev} below lower_dev {self.lower_dev}"
            )
        if self.position_tol < 0.0:
            raise ValueError(f"position_tol must be non-negative, got {self.position_tol}")

    @property
    def max_size(self) -> float:
        return self.nominal + self.upper_dev

    @property
    def min_size(self) -> float:
        return self.nominal + self.lower_dev

    @property
    def mmc(self) -> float:
        """Maximum material condition: most material present."""
        if self.feature_type is FeatureType.INTERNAL:
            return self.min_size
        return self.max_size

    @property
    def lmc(self) -> float:
        """Least material condition: least material present."""
        if self.feature_type is FeatureType.INTERNAL:
            return self.max_size
        return self.min_size


@dataclass(frozen=True)
class Verdict:
    """Result of a functional check.

    margin > 0 means assembly is guaranteed, in mm of slack.
    """

    assembles: bool
    margin: float
    method: str
    detail: dict = field(default_factory=dict)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_types.py -v`
Expected: PASS, 3 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/types.py tests/test_types.py
git commit -m "feat: core domain types for toleranced features"
```

---

### Task 3: Virtual condition (Tier 1)

**Files:**
- Create: `src/tolcad/y14_5.py`
- Test: `tests/test_y14_5.py`

**Interfaces:**
- Consumes: `FeatureOfSize`, `FeatureType`, `Verdict`, `EPS` from `tolcad.types`
- Produces:
  - `virtual_condition(feature: FeatureOfSize) -> float`
  - `vc_assembles(pin: FeatureOfSize, hole: FeatureOfSize) -> Verdict`

Virtual condition is the worst-case boundary a feature can occupy:
external `VC = MMC + position_tol`, internal `VC = MMC - position_tol`.
Assembly is guaranteed iff `VC_pin <= VC_hole`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_y14_5.py
import pytest
from tolcad.types import FeatureOfSize, FeatureType
from tolcad.y14_5 import virtual_condition, vc_assembles

INTERNAL = FeatureType.INTERNAL
EXTERNAL = FeatureType.EXTERNAL


def test_virtual_condition_external_adds_position_tolerance():
    # Ø8.0 pin at MMC with 0.1 position tolerance -> VC 8.1
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.1)
    assert virtual_condition(pin) == pytest.approx(8.1)


def test_virtual_condition_internal_subtracts_position_tolerance():
    # Ø8.5 hole at MMC with 0.5 position tolerance -> VC 8.0
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    assert virtual_condition(hole) == pytest.approx(8.0)


def test_assembly_guaranteed_when_pin_vc_fits_hole_vc():
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.0)
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.2)
    verdict = vc_assembles(pin, hole)
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.3)  # 8.3 - 8.0


def test_assembly_fails_when_pin_vc_exceeds_hole_vc():
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.4)
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    verdict = vc_assembles(pin, hole)
    assert verdict.assembles is False
    assert verdict.margin == pytest.approx(-0.4)  # 8.0 - 8.4


def test_exact_boundary_case_assembles():
    """VC_pin == VC_hole is the guaranteed-fit boundary and must pass."""
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL, position_tol=0.0)
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    verdict = vc_assembles(pin, hole)
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.0, abs=1e-9)


def test_rejects_swapped_feature_types():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    with pytest.raises(ValueError, match="external"):
        vc_assembles(hole, hole)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_y14_5.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.y14_5'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/y14_5.py
"""Tier 1: closed-form ASME Y14.5 assembly conditions.

These are exact arithmetic identities from the standard, not simulations.
A failure here is unambiguously a failure of the input geometry.
"""

from __future__ import annotations

from tolcad.types import EPS, FeatureOfSize, FeatureType, Verdict


def virtual_condition(feature: FeatureOfSize) -> float:
    """Worst-case boundary of a feature, per ASME Y14.5.

    External: MMC + position tolerance (effectively the largest it can be).
    Internal: MMC - position tolerance (effectively the smallest it can be).
    """
    if feature.feature_type is FeatureType.EXTERNAL:
        return feature.mmc + feature.position_tol
    return feature.mmc - feature.position_tol


def vc_assembles(pin: FeatureOfSize, hole: FeatureOfSize) -> Verdict:
    """Check a single pin-in-hole pair by virtual condition.

    Assembly is guaranteed iff VC_pin <= VC_hole.
    """
    if pin.feature_type is not FeatureType.EXTERNAL:
        raise ValueError("pin must be an external feature")
    if hole.feature_type is not FeatureType.INTERNAL:
        raise ValueError("hole must be an internal feature")

    vc_pin = virtual_condition(pin)
    vc_hole = virtual_condition(hole)
    margin = vc_hole - vc_pin

    return Verdict(
        assembles=margin >= -EPS,
        margin=margin,
        method="virtual_condition",
        detail={"vc_pin": vc_pin, "vc_hole": vc_hole},
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_y14_5.py -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/y14_5.py tests/test_y14_5.py
git commit -m "feat: virtual condition check (Tier 1)"
```

---

### Task 4: Floating and fixed fastener conditions (Tier 1)

**Files:**
- Modify: `src/tolcad/y14_5.py` (append)
- Modify: `tests/test_y14_5.py` (append)

**Interfaces:**
- Consumes: `FeatureOfSize`, `FeatureType`, `Verdict`, `EPS`
- Produces:
  - `floating_fastener_tolerance(hole: FeatureOfSize, fastener: FeatureOfSize) -> float`
  - `fixed_fastener_tolerance(hole: FeatureOfSize, fastener: FeatureOfSize) -> float`
  - `fastener_assembles(hole_a, hole_b, fastener, condition: str) -> Verdict`

Floating fastener (bolt through clearance holes in both parts, nut on the back):
`T = H - F`, available to **each** part.
Fixed fastener (one part threaded or with a pressed pin): `T = (H - F) / 2`.
`H` = hole MMC, `F` = fastener MMC.

**Citation requirement:** before implementing, confirm both formulas and at least
two worked numeric examples against a citable source — ASME Y14.5-2018, or
Meadows / Krulikowski. Record the source and page in a docstring. The examples
below are canonical but MUST be verified against print, not accepted from this plan.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_y14_5.py  (append)
from tolcad.y14_5 import (
    fastener_assembles,
    fixed_fastener_tolerance,
    floating_fastener_tolerance,
)

# Canonical worked example: M8 bolt (Ø8.0 max) through Ø8.5 min clearance holes.
M8_BOLT = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL)
CLEARANCE_HOLE = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)


def test_floating_fastener_tolerance_is_hole_mmc_minus_fastener_mmc():
    # T = H - F = 8.5 - 8.0 = 0.5 per part
    assert floating_fastener_tolerance(CLEARANCE_HOLE, M8_BOLT) == pytest.approx(0.5)


def test_fixed_fastener_tolerance_is_half_the_floating_value():
    # T = (H - F) / 2 = 0.25 per part
    assert fixed_fastener_tolerance(CLEARANCE_HOLE, M8_BOLT) == pytest.approx(0.25)


def test_floating_fastener_assembles_at_allowable_tolerance():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="floating")
    assert verdict.assembles is True


def test_floating_fastener_fails_above_allowable_tolerance():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    verdict = fastener_assembles(hole, hole, M8_BOLT, condition="floating")
    assert verdict.assembles is False
    assert verdict.margin == pytest.approx(-0.1)


def test_fixed_fastener_is_stricter_than_floating():
    """Same geometry: a tolerance that passes floating must fail fixed at 0.5."""
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.5)
    assert fastener_assembles(hole, hole, M8_BOLT, condition="floating").assembles
    assert not fastener_assembles(hole, hole, M8_BOLT, condition="fixed").assembles


def test_asymmetric_holes_use_the_worse_one():
    tight = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.6)
    loose = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    verdict = fastener_assembles(tight, loose, M8_BOLT, condition="floating")
    assert verdict.assembles is False


def test_unknown_condition_rejected():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL, position_tol=0.1)
    with pytest.raises(ValueError, match="condition"):
        fastener_assembles(hole, hole, M8_BOLT, condition="press")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_y14_5.py -v`
Expected: FAIL with `ImportError: cannot import name 'floating_fastener_tolerance'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/y14_5.py  (append)

def _check_fastener_pair(hole: FeatureOfSize, fastener: FeatureOfSize) -> None:
    if hole.feature_type is not FeatureType.INTERNAL:
        raise ValueError("hole must be an internal feature")
    if fastener.feature_type is not FeatureType.EXTERNAL:
        raise ValueError("fastener must be an external feature")


def floating_fastener_tolerance(
    hole: FeatureOfSize, fastener: FeatureOfSize
) -> float:
    """Position tolerance available to each part, floating fastener condition.

    T = H - F, where H is hole MMC and F is fastener MMC.
    Source: ASME Y14.5 floating fastener formula. Verify citation before use.
    """
    _check_fastener_pair(hole, fastener)
    return hole.mmc - fastener.mmc


def fixed_fastener_tolerance(hole: FeatureOfSize, fastener: FeatureOfSize) -> float:
    """Position tolerance available to each part, fixed fastener condition.

    T = (H - F) / 2. The available clearance is split between the two parts
    because the fastener cannot shift in the part that constrains it.
    Assumes a projected tolerance zone.
    """
    _check_fastener_pair(hole, fastener)
    return (hole.mmc - fastener.mmc) / 2.0


def fastener_assembles(
    hole_a: FeatureOfSize,
    hole_b: FeatureOfSize,
    fastener: FeatureOfSize,
    condition: str,
) -> Verdict:
    """Check a two-part fastened joint against the Y14.5 allowable tolerance."""
    if condition == "floating":
        allowable = floating_fastener_tolerance(hole_a, fastener)
    elif condition == "fixed":
        allowable = fixed_fastener_tolerance(hole_a, fastener)
    else:
        raise ValueError(f"condition must be 'floating' or 'fixed', got {condition!r}")

    worst = max(hole_a.position_tol, hole_b.position_tol)
    margin = allowable - worst

    return Verdict(
        assembles=margin >= -EPS,
        margin=margin,
        method=f"{condition}_fastener",
        detail={
            "allowable_tol": allowable,
            "worst_applied_tol": worst,
            "hole_mmc": hole_a.mmc,
            "fastener_mmc": fastener.mmc,
        },
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_y14_5.py -v`
Expected: PASS, 13 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/y14_5.py tests/test_y14_5.py
git commit -m "feat: floating and fixed fastener conditions (Tier 1)"
```

---

### Task 5: Bonus tolerance under the MMC modifier

**Files:**
- Modify: `src/tolcad/y14_5.py` (append)
- Modify: `tests/test_y14_5.py` (append)

**Interfaces:**
- Consumes: `FeatureOfSize`, `FeatureType`
- Produces: `bonus_tolerance(feature: FeatureOfSize, actual_size: float) -> float`

Under the MMC modifier, a feature departing from MMC toward LMC earns extra
position tolerance equal to that departure. This matters because it is exactly the
mechanism that makes "nominally correct" parts assemble in practice — omitting it
would make the checker pessimistic and overstate the paper's finding.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_y14_5.py  (append)
from tolcad.y14_5 import bonus_tolerance


def test_no_bonus_at_mmc():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    assert bonus_tolerance(hole, 8.5) == pytest.approx(0.0)


def test_full_bonus_at_lmc_for_internal_feature():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    assert bonus_tolerance(hole, 8.7) == pytest.approx(0.2)


def test_full_bonus_at_lmc_for_external_feature():
    pin = FeatureOfSize(8.0, -0.1, 0.0, EXTERNAL)
    assert bonus_tolerance(pin, 7.9) == pytest.approx(0.1)


def test_partial_bonus_mid_range():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    assert bonus_tolerance(hole, 8.6) == pytest.approx(0.1)


def test_actual_size_outside_limits_rejected():
    hole = FeatureOfSize(8.5, 0.0, 0.2, INTERNAL)
    with pytest.raises(ValueError, match="outside"):
        bonus_tolerance(hole, 8.9)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_y14_5.py -v`
Expected: FAIL with `ImportError: cannot import name 'bonus_tolerance'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/y14_5.py  (append)

def bonus_tolerance(feature: FeatureOfSize, actual_size: float) -> float:
    """Extra position tolerance earned by departing from MMC, under the MMC modifier.

    Bonus equals the departure from MMC toward LMC. Zero at MMC, maximal at LMC.
    """
    if not (feature.min_size - EPS <= actual_size <= feature.max_size + EPS):
        raise ValueError(
            f"actual_size {actual_size} outside limits "
            f"[{feature.min_size}, {feature.max_size}]"
        )
    return abs(actual_size - feature.mmc)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_y14_5.py -v`
Expected: PASS, 18 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/y14_5.py tests/test_y14_5.py
git commit -m "feat: bonus tolerance under MMC modifier"
```

---

### Task 6: ISO 286 tolerance tables

**Files:**
- Create: `src/tolcad/iso286.py`
- Test: `tests/test_iso286.py`

**Interfaces:**
- Consumes: `FeatureOfSize`, `FeatureType`
- Produces:
  - `it_grade(nominal_mm: float, grade: int) -> float` — IT tolerance in **mm**
  - `fundamental_deviation(nominal_mm: float, letter: str) -> float` — in **mm**
  - `fit_from_designation(nominal_mm: float, designation: str) -> tuple[FeatureOfSize, FeatureOfSize]` — e.g. `"H7/g6"` → (hole, shaft)

**Citation requirement:** all table values MUST be transcribed from ISO 286-1 or an
equivalent published table and the source recorded in the module docstring.
Values below are correct for the ranges given but MUST be verified against print.

Verification anchor for Ø20 H7/g6: hole `+0.021/0`, shaft `-0.007/-0.020`.
Minimum clearance 0.007 mm, maximum 0.041 mm.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_iso286.py
import pytest
from tolcad.types import FeatureType
from tolcad.iso286 import fit_from_designation, fundamental_deviation, it_grade


def test_it7_at_20mm_is_21_microns():
    assert it_grade(20.0, 7) == pytest.approx(0.021)


def test_it6_at_20mm_is_13_microns():
    assert it_grade(20.0, 6) == pytest.approx(0.013)


def test_it_grade_respects_size_band_boundaries():
    # 18 falls in the 10-18 band (upper bound inclusive), 18.1 in 18-30
    assert it_grade(18.0, 7) == pytest.approx(0.018)
    assert it_grade(18.1, 7) == pytest.approx(0.021)


def test_h_hole_has_zero_fundamental_deviation():
    assert fundamental_deviation(20.0, "H") == pytest.approx(0.0)


def test_g_shaft_deviation_at_20mm_is_minus_7_microns():
    assert fundamental_deviation(20.0, "g") == pytest.approx(-0.007)


def test_h7g6_at_20mm_matches_published_limits():
    hole, shaft = fit_from_designation(20.0, "H7/g6")
    assert hole.feature_type is FeatureType.INTERNAL
    assert shaft.feature_type is FeatureType.EXTERNAL
    assert hole.min_size == pytest.approx(20.000)
    assert hole.max_size == pytest.approx(20.021)
    assert shaft.max_size == pytest.approx(19.993)
    assert shaft.min_size == pytest.approx(19.980)


def test_h7g6_is_a_clearance_fit():
    """Minimum clearance must be strictly positive for a sliding fit."""
    hole, shaft = fit_from_designation(20.0, "H7/g6")
    min_clearance = hole.min_size - shaft.max_size
    assert min_clearance == pytest.approx(0.007)
    assert min_clearance > 0


def test_h7p6_is_an_interference_fit():
    """Maximum clearance must be negative for a press fit."""
    hole, shaft = fit_from_designation(20.0, "H7/p6")
    max_clearance = hole.max_size - shaft.min_size
    assert max_clearance < 0


def test_unsupported_size_rejected():
    with pytest.raises(ValueError, match="outside supported range"):
        it_grade(900.0, 7)


def test_malformed_designation_rejected():
    with pytest.raises(ValueError, match="designation"):
        fit_from_designation(20.0, "H7g6")


@pytest.mark.xfail(
    reason="Fails until table values are verified against print. Do not delete.",
    strict=False,
)
def test_transcription_source_recorded():
    """Gate A guard: table values must cite a real published source."""
    import tolcad.iso286 as mod

    doc = mod.__doc__ or ""
    assert "replace this line" not in doc, (
        "ISO 286 tables are still unverified — record the edition and table number"
    )
    assert "ISO 286" in doc
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_iso286.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.iso286'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/iso286.py
"""ISO 286 limits and fits, hole-basis system.

Table values transcribed from ISO 286-1. Published in micrometres; converted to
millimetres at the table boundary so that no downstream code handles microns.

TRANSCRIPTION SOURCE: replace this line with the exact edition and table number the
values below were copied from (e.g. "ISO 286-1:2010, Table 1 and Table 6"). Leaving
this line unedited means the tables are unverified and no derived number may be
published. tests/test_iso286.py::test_transcription_source_recorded enforces this.
"""

from __future__ import annotations

from tolcad.types import FeatureOfSize, FeatureType

# Upper bound (inclusive) of each nominal size band, in mm.
_SIZE_BANDS = [3, 6, 10, 18, 30, 50, 80, 120, 180, 250, 315, 400, 500]

# IT grade tolerance, micrometres, indexed parallel to _SIZE_BANDS.
_IT_MICRONS: dict[int, list[int]] = {
    5: [4, 5, 6, 8, 9, 11, 13, 15, 18, 20, 23, 25, 27],
    6: [6, 8, 9, 11, 13, 16, 19, 22, 25, 29, 32, 36, 40],
    7: [10, 12, 15, 18, 21, 25, 30, 35, 40, 46, 52, 57, 63],
    8: [14, 18, 22, 27, 33, 39, 46, 54, 63, 72, 81, 89, 97],
}

# Fundamental deviation, micrometres. Uppercase = hole (EI), lowercase = shaft (es/ei).
_DEVIATION_MICRONS: dict[str, list[int]] = {
    "H": [0] * 13,
    "g": [-2, -4, -5, -6, -7, -9, -10, -12, -14, -15, -17, -18, -20],
    "h": [0] * 13,
    "k": [0, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4, 5],
    "p": [6, 12, 15, 18, 22, 26, 32, 37, 43, 50, 56, 62, 68],
}


def _band_index(nominal_mm: float) -> int:
    if nominal_mm <= 0 or nominal_mm > _SIZE_BANDS[-1]:
        raise ValueError(
            f"nominal size {nominal_mm} outside supported range (0, {_SIZE_BANDS[-1]}]"
        )
    for i, upper in enumerate(_SIZE_BANDS):
        if nominal_mm <= upper:
            return i
    raise AssertionError("unreachable")


def it_grade(nominal_mm: float, grade: int) -> float:
    """IT tolerance width in mm for a nominal size and grade."""
    if grade not in _IT_MICRONS:
        raise ValueError(f"IT grade {grade} not tabulated; have {sorted(_IT_MICRONS)}")
    return _IT_MICRONS[grade][_band_index(nominal_mm)] / 1000.0


def fundamental_deviation(nominal_mm: float, letter: str) -> float:
    """Fundamental deviation in mm. Uppercase for holes, lowercase for shafts."""
    if letter not in _DEVIATION_MICRONS:
        raise ValueError(
            f"deviation letter {letter!r} not tabulated; "
            f"have {sorted(_DEVIATION_MICRONS)}"
        )
    return _DEVIATION_MICRONS[letter][_band_index(nominal_mm)] / 1000.0


def _parse(designation: str) -> tuple[str, int, str, int]:
    if "/" not in designation:
        raise ValueError(
            f"designation {designation!r} must be of the form 'H7/g6'"
        )
    hole_part, shaft_part = designation.split("/", 1)
    try:
        return hole_part[0], int(hole_part[1:]), shaft_part[0], int(shaft_part[1:])
    except (ValueError, IndexError) as exc:
        raise ValueError(f"malformed designation {designation!r}") from exc


def fit_from_designation(
    nominal_mm: float, designation: str
) -> tuple[FeatureOfSize, FeatureOfSize]:
    """Build (hole, shaft) features from an ISO 286 fit like 'H7/g6'.

    Hole-basis only: the hole letter must be 'H', whose lower deviation is zero.
    """
    hole_letter, hole_grade, shaft_letter, shaft_grade = _parse(designation)

    if hole_letter != "H":
        raise ValueError(f"only hole-basis fits supported, got {hole_letter!r}")

    hole_it = it_grade(nominal_mm, hole_grade)
    hole = FeatureOfSize(nominal_mm, 0.0, hole_it, FeatureType.INTERNAL)

    shaft_it = it_grade(nominal_mm, shaft_grade)
    dev = fundamental_deviation(nominal_mm, shaft_letter)

    if shaft_letter in ("g", "h"):
        # Deviation is the upper limit (es); lower is es - IT.
        shaft = FeatureOfSize(nominal_mm, dev - shaft_it, dev, FeatureType.EXTERNAL)
    else:
        # Deviation is the lower limit (ei); upper is ei + IT.
        shaft = FeatureOfSize(nominal_mm, dev, dev + shaft_it, FeatureType.EXTERNAL)

    return hole, shaft
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_iso286.py -v`
Expected: PASS, 10 tests, plus 1 XFAIL (`test_transcription_source_recorded`). The XFAIL
turns to XPASS once the source line is filled in — that flip is the signal the tables are
verified.

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/iso286.py tests/test_iso286.py
git commit -m "feat: ISO 286 tolerance tables and hole-basis fits"
```

---

### Task 7: Monte Carlo stack-up (Tier 2)

**Files:**
- Create: `src/tolcad/montecarlo.py`
- Test: `tests/test_montecarlo.py`

**Interfaces:**
- Consumes: `FeatureOfSize`, `Verdict`
- Produces:
  - `sample_size(feature: FeatureOfSize, rng, n: int, distribution: str = "normal") -> np.ndarray`
  - `clearance_yield(hole, shaft, n: int, seed: int, distribution: str = "normal") -> Verdict`

`clearance_yield` returns a `Verdict` whose `margin` is the estimated yield in
[0, 1] — the fraction of sampled part pairs achieving positive clearance.
`assembles` is True iff yield is 1.0 within sampling resolution.

The `"normal"` distribution places ±3σ at the tolerance limits and truncates;
`"uniform"` samples the limits uniformly. Both are reported; the choice is an
ablation axis, not a hidden assumption.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_montecarlo.py
import numpy as np
import pytest
from tolcad.iso286 import fit_from_designation
from tolcad.montecarlo import clearance_yield, sample_size
from tolcad.types import FeatureOfSize, FeatureType


def test_samples_stay_within_tolerance_limits():
    hole = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)
    rng = np.random.default_rng(42)
    samples = sample_size(hole, rng, n=10_000)
    assert samples.min() >= hole.min_size
    assert samples.max() <= hole.max_size


def test_uniform_distribution_spans_the_range():
    hole = FeatureOfSize(20.0, 0.0, 0.021, FeatureType.INTERNAL)
    rng = np.random.default_rng(42)
    samples = sample_size(hole, rng, n=10_000, distribution="uniform")
    assert samples.mean() == pytest.approx(20.0105, abs=1e-3)


def test_clearance_fit_yields_fully():
    """H7/g6 has positive minimum clearance, so yield must be exactly 1.0."""
    hole, shaft = fit_from_designation(20.0, "H7/g6")
    verdict = clearance_yield(hole, shaft, n=10_000, seed=0)
    assert verdict.margin == pytest.approx(1.0)
    assert verdict.assembles is True


def test_interference_fit_never_clears():
    """H7/p6 is a press fit; clearance yield must be exactly 0.0."""
    hole, shaft = fit_from_designation(20.0, "H7/p6")
    verdict = clearance_yield(hole, shaft, n=10_000, seed=0)
    assert verdict.margin == pytest.approx(0.0)
    assert verdict.assembles is False


def test_transition_fit_yields_partially():
    """H7/k6 sometimes clears and sometimes interferes."""
    hole, shaft = fit_from_designation(20.0, "H7/k6")
    verdict = clearance_yield(hole, shaft, n=50_000, seed=0, distribution="uniform")
    assert 0.0 < verdict.margin < 1.0


def test_identical_seeds_give_identical_results():
    hole, shaft = fit_from_designation(20.0, "H7/k6")
    a = clearance_yield(hole, shaft, n=10_000, seed=7)
    b = clearance_yield(hole, shaft, n=10_000, seed=7)
    assert a.margin == b.margin


def test_seed_is_recorded_in_detail():
    hole, shaft = fit_from_designation(20.0, "H7/g6")
    verdict = clearance_yield(hole, shaft, n=1_000, seed=99)
    assert verdict.detail["seed"] == 99
    assert verdict.detail["n"] == 1_000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_montecarlo.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.montecarlo'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/montecarlo.py
"""Tier 2: Monte Carlo tolerance stack-up.

Statistical, unlike Tier 1. Every result carries its seed and sample count so
that any reported number is reproducible.
"""

from __future__ import annotations

import numpy as np

from tolcad.types import FeatureOfSize, Verdict


def sample_size(
    feature: FeatureOfSize,
    rng: np.random.Generator,
    n: int,
    distribution: str = "normal",
) -> np.ndarray:
    """Draw n actual sizes for a toleranced feature, clipped to its limits.

    'normal' places +/-3 sigma at the tolerance limits, then truncates.
    'uniform' samples the limits uniformly.
    """
    lo, hi = feature.min_size, feature.max_size

    if distribution == "uniform":
        return rng.uniform(lo, hi, size=n)

    if distribution == "normal":
        mid = (lo + hi) / 2.0
        sigma = (hi - lo) / 6.0
        if sigma == 0.0:
            return np.full(n, mid)
        return np.clip(rng.normal(mid, sigma, size=n), lo, hi)

    raise ValueError(
        f"distribution must be 'normal' or 'uniform', got {distribution!r}"
    )


def clearance_yield(
    hole: FeatureOfSize,
    shaft: FeatureOfSize,
    n: int,
    seed: int,
    distribution: str = "normal",
) -> Verdict:
    """Estimate the fraction of part pairs achieving positive clearance.

    margin is the yield in [0, 1]. assembles is True only at full yield.
    """
    rng = np.random.default_rng(seed)
    holes = sample_size(hole, rng, n, distribution)
    shafts = sample_size(shaft, rng, n, distribution)

    clearances = holes - shafts
    yield_frac = float(np.mean(clearances > 0.0))

    return Verdict(
        assembles=yield_frac >= 1.0,
        margin=yield_frac,
        method="monte_carlo_clearance",
        detail={
            "seed": seed,
            "n": n,
            "distribution": distribution,
            "min_clearance": float(clearances.min()),
            "mean_clearance": float(clearances.mean()),
        },
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_montecarlo.py -v`
Expected: PASS, 7 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/montecarlo.py tests/test_montecarlo.py
git commit -m "feat: Monte Carlo clearance stack-up (Tier 2)"
```

---

### Task 8: Monte Carlo convergence (Gate A criterion)

**Files:**
- Create: `tests/test_convergence.py`
- Modify: `pyproject.toml` (register the `slow` marker)

**Interfaces:**
- Consumes: `clearance_yield`, `fit_from_designation`
- Produces: nothing importable; establishes the Gate A stability criterion

Gate A requires the yield estimate to be stable to **±0.5% range across 5 seeds at N=100,000**.
A transition fit is the right probe: clearance and interference fits are degenerate at
0.0 and 1.0 and would pass trivially.

**Why N=100k and not 10k.** For a transition fit with yield p≈0.6, the binomial standard
error is √(p(1−p)/N). At N=10k that is ≈0.0049, so the expected range across 5 seeds is
≈2.33σ ≈ 0.011 — twice the threshold, and unachievable by correct code. At N=100k,
SE ≈ 0.0016 and expected range ≈ 0.0036. Spec §7 was corrected accordingly, pre-data.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_convergence.py
"""Gate A: Monte Carlo stability. Threshold is pre-registered in spec section 7."""

import pytest
from tolcad.iso286 import fit_from_designation
from tolcad.montecarlo import clearance_yield

GATE_A_TOLERANCE = 0.005  # +/- 0.5%, pre-registered. DO NOT LOOSEN.


@pytest.mark.slow
def test_yield_stable_across_seeds_at_100k_samples():
    hole, shaft = fit_from_designation(20.0, "H7/k6")
    yields = [
        clearance_yield(hole, shaft, n=100_000, seed=s, distribution="uniform").margin
        for s in range(5)
    ]
    spread = max(yields) - min(yields)
    assert spread <= GATE_A_TOLERANCE, (
        f"yield spread {spread:.4f} exceeds Gate A tolerance {GATE_A_TOLERANCE}; "
        f"yields={yields}"
    )


@pytest.mark.slow
def test_convergence_improves_with_sample_count():
    """Spread at 100k must not exceed spread at 1k. Guards against a broken RNG path."""
    hole, shaft = fit_from_designation(20.0, "H7/k6")

    def spread(n: int) -> float:
        ys = [
            clearance_yield(hole, shaft, n=n, seed=s, distribution="uniform").margin
            for s in range(5)
        ]
        return max(ys) - min(ys)

    assert spread(100_000) <= spread(1_000)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_convergence.py -v`
Expected: FAIL with `'slow' not found in markers configuration option` (strict markers not yet registered)

- [ ] **Step 3: Register the marker**

```toml
# pyproject.toml  — replace the [tool.pytest.ini_options] block
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "--strict-markers"
markers = [
    "slow: Monte Carlo convergence checks (deselect with -m 'not slow')",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_convergence.py -v`
Expected: PASS, 2 tests

If `test_yield_stable_across_seeds_at_100k_samples` fails, **do not raise
`GATE_A_TOLERANCE`.** The threshold is pre-registered. Investigate the RNG path or
record the failure as a Gate A deviation in the spec.

- [ ] **Step 5: Commit**

```bash
git add tests/test_convergence.py pyproject.toml
git commit -m "test: Monte Carlo convergence criterion for Gate A"
```

---

### Task 9: Architecture guard — validation isolation

**Files:**
- Create: `validation/__init__.py`
- Create: `validation/tolanalyst.py`
- Create: `tests/test_architecture.py`

**Interfaces:**
- Consumes: `Verdict` (inside `validation/` only)
- Produces: `validation.tolanalyst.load_verdicts(path) -> dict[str, bool]`; `validation.tolanalyst.agreement(ours, theirs) -> float`

Gate A requires that no core module imports `validation/`. This test enforces it
mechanically so the reproducibility guarantee cannot rot.

TolAnalyst is a **black box**. This module reads a CSV of verdicts exported by a
separate manual step. It does not automate, wrap, or describe SolidWorks internals.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_architecture.py
"""Gate A: core must never depend on the optional SolidWorks path."""

import ast
import pathlib

CORE = pathlib.Path(__file__).parent.parent / "src" / "tolcad"


def _imported_modules(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_no_core_module_imports_validation():
    offenders = []
    for path in CORE.rglob("*.py"):
        bad = {m for m in _imported_modules(path) if m.split(".")[0] == "validation"}
        if bad:
            offenders.append(f"{path.name} imports {sorted(bad)}")
    assert not offenders, (
        "core modules must not import validation/: " + "; ".join(offenders)
    )


def test_core_imports_without_numpy_optional_deps_beyond_declared():
    """Core must import cleanly with no SolidWorks tooling present."""
    import tolcad.checker  # noqa: F401
    import tolcad.iso286  # noqa: F401
    import tolcad.montecarlo  # noqa: F401
    import tolcad.y14_5  # noqa: F401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_architecture.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.checker'` (Task 10 creates it)

- [ ] **Step 3: Write the validation package**

```python
# validation/__init__.py
"""Optional SolidWorks cross-validation. Never imported by core tolcad modules."""
```

```python
# validation/tolanalyst.py
"""Cross-check tolcad verdicts against SolidWorks TolAnalyst.

TolAnalyst is treated strictly as a black-box oracle: this module ingests a CSV of
verdicts produced by a separate manual export and compares them to ours. It does not
wrap, automate, or document any SolidWorks internals.

CSV format: assembly_id,assembles
"""

from __future__ import annotations

import csv
import pathlib


def load_verdicts(path: str | pathlib.Path) -> dict[str, bool]:
    """Read exported TolAnalyst verdicts keyed by assembly id."""
    out: dict[str, bool] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[row["assembly_id"]] = row["assembles"].strip().lower() == "true"
    return out


def agreement(ours: dict[str, bool], theirs: dict[str, bool]) -> float:
    """Fraction of shared assembly ids where the two verdicts match."""
    shared = set(ours) & set(theirs)
    if not shared:
        raise ValueError("no overlapping assembly ids between the two verdict sets")
    matches = sum(1 for k in shared if ours[k] == theirs[k])
    return matches / len(shared)


def disagreements(ours: dict[str, bool], theirs: dict[str, bool]) -> list[str]:
    """Assembly ids where verdicts differ. Gate A requires each to be root-caused."""
    shared = set(ours) & set(theirs)
    return sorted(k for k in shared if ours[k] != theirs[k])
```

- [ ] **Step 4: Run test — one will still fail**

Run: `pytest tests/test_architecture.py::test_no_core_module_imports_validation -v`
Expected: PASS

The second test stays red until Task 10 creates `tolcad.checker`. That is expected.

- [ ] **Step 5: Commit**

```bash
git add validation tests/test_architecture.py
git commit -m "feat: TolAnalyst verdict comparison and architecture guard"
```

---

### Task 10: Top-level checker dispatch

**Files:**
- Create: `src/tolcad/checker.py`
- Test: `tests/test_checker.py`

**Interfaces:**
- Consumes: everything above
- Produces: `check(mate: dict) -> Verdict`

`mate` is a plain dict so the Phase 3 generator can emit JSON without importing tolcad.
Required key `type`, one of `"virtual_condition"`, `"floating_fastener"`,
`"fixed_fastener"`, `"iso_fit"`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_checker.py
import pytest
from tolcad.checker import check


def test_dispatches_virtual_condition():
    verdict = check({
        "type": "virtual_condition",
        "pin": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0, "position_tol": 0.0},
        "hole": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.2},
    })
    assert verdict.assembles is True
    assert verdict.method == "virtual_condition"


def test_dispatches_floating_fastener():
    hole = {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.6}
    verdict = check({
        "type": "floating_fastener",
        "hole_a": hole,
        "hole_b": hole,
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    })
    assert verdict.assembles is False


def test_dispatches_iso_fit():
    verdict = check({
        "type": "iso_fit",
        "nominal": 20.0,
        "designation": "H7/g6",
        "n": 10_000,
        "seed": 0,
    })
    assert verdict.margin == pytest.approx(1.0)


def test_unknown_mate_type_rejected():
    with pytest.raises(ValueError, match="unknown mate type"):
        check({"type": "weld"})


def test_missing_type_key_rejected():
    with pytest.raises(ValueError, match="'type'"):
        check({})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_checker.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.checker'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/checker.py
"""Top-level dispatch over mate types.

Mates arrive as plain dicts so the generator can emit JSON without importing tolcad.
"""

from __future__ import annotations

from tolcad.iso286 import fit_from_designation
from tolcad.montecarlo import clearance_yield
from tolcad.types import FeatureOfSize, FeatureType, Verdict
from tolcad.y14_5 import fastener_assembles, vc_assembles


def _feature(spec: dict, feature_type: FeatureType) -> FeatureOfSize:
    return FeatureOfSize(
        nominal=spec["nominal"],
        lower_dev=spec["lower_dev"],
        upper_dev=spec["upper_dev"],
        feature_type=feature_type,
        position_tol=spec.get("position_tol", 0.0),
    )


def check(mate: dict) -> Verdict:
    """Evaluate a single mate specification."""
    if "type" not in mate:
        raise ValueError("mate specification requires a 'type' key")

    kind = mate["type"]

    if kind == "virtual_condition":
        return vc_assembles(
            _feature(mate["pin"], FeatureType.EXTERNAL),
            _feature(mate["hole"], FeatureType.INTERNAL),
        )

    if kind in ("floating_fastener", "fixed_fastener"):
        return fastener_assembles(
            _feature(mate["hole_a"], FeatureType.INTERNAL),
            _feature(mate["hole_b"], FeatureType.INTERNAL),
            _feature(mate["fastener"], FeatureType.EXTERNAL),
            condition=kind.replace("_fastener", ""),
        )

    if kind == "iso_fit":
        hole, shaft = fit_from_designation(mate["nominal"], mate["designation"])
        return clearance_yield(
            hole,
            shaft,
            n=mate.get("n", 10_000),
            seed=mate.get("seed", 0),
            distribution=mate.get("distribution", "normal"),
        )

    raise ValueError(f"unknown mate type {kind!r}")
```

- [ ] **Step 4: Run all tests**

Run: `pytest -v`
Expected: PASS, all tests including both in `test_architecture.py`

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/checker.py tests/test_checker.py
git commit -m "feat: top-level mate dispatch"
```

---

### Task 11: Gate A report script

**Files:**
- Create: `scripts/gate_a.py`
- Test: `tests/test_gate_a.py`

**Interfaces:**
- Consumes: pytest results, `validation.tolanalyst.agreement`
- Produces: `scripts/gate_a.py` CLI printing a per-criterion pass/fail table and exiting non-zero on any failure

This script is how "did we clear Gate A?" gets answered with evidence rather than
narrative. The TolAnalyst criterion is reported as SKIPPED when no export file is
present, so the script runs without a SolidWorks license — but Gate A is only
**cleared** when it is present and passing.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gate_a.py
import subprocess
import sys
import pathlib

REPO = pathlib.Path(__file__).parent.parent


def test_gate_a_script_runs_without_solidworks_export():
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert "TolAnalyst agreement" in result.stdout
    assert "SKIP" in result.stdout
    # Missing oracle means Gate A is not cleared.
    assert result.returncode != 0


def test_gate_a_reports_every_criterion():
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    for criterion in [
        "Y14.5 worked examples",
        "TolAnalyst agreement",
        "Monte Carlo convergence",
        "Validation isolation",
    ]:
        assert criterion in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gate_a.py -v`
Expected: FAIL — `scripts/gate_a.py` does not exist, stdout is empty

- [ ] **Step 3: Write the script**

```python
#!/usr/bin/env python
"""Gate A report. Thresholds are pre-registered in the design spec, section 7.

Exits 0 only when every criterion passes. A skipped criterion is not a pass.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).parent.parent
TOLANALYST_EXPORT = REPO / "data" / "tolanalyst_verdicts.csv"
AGREEMENT_THRESHOLD = 0.95  # pre-registered, DO NOT LOOSEN


def _pytest_passes(target: str) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q"],
        cwd=REPO, capture_output=True, text=True,
    )
    return result.returncode == 0


def main() -> int:
    rows: list[tuple[str, str, str]] = []

    ok = _pytest_passes("tests/test_y14_5.py")
    rows.append(("Y14.5 worked examples", "PASS" if ok else "FAIL", "100% required"))

    ok_conv = _pytest_passes("tests/test_convergence.py")
    rows.append(
        ("Monte Carlo convergence", "PASS" if ok_conv else "FAIL", "+/-0.5% at N=100k")
    )

    ok_iso = _pytest_passes("tests/test_architecture.py")
    rows.append(("Validation isolation", "PASS" if ok_iso else "FAIL", "no core imports"))

    if TOLANALYST_EXPORT.exists():
        from validation.tolanalyst import agreement, load_verdicts

        theirs = load_verdicts(TOLANALYST_EXPORT)
        # Populated in Phase 3 once the generator can produce matching assemblies.
        ours: dict[str, bool] = {}
        try:
            score = agreement(ours, theirs)
            ok_tol = score >= AGREEMENT_THRESHOLD
            rows.append(
                ("TolAnalyst agreement", "PASS" if ok_tol else "FAIL", f"{score:.1%}")
            )
        except ValueError as exc:
            ok_tol = False
            rows.append(("TolAnalyst agreement", "FAIL", str(exc)))
    else:
        ok_tol = False
        rows.append(
            ("TolAnalyst agreement", "SKIP", f"no export at {TOLANALYST_EXPORT.name}")
        )

    width = max(len(r[0]) for r in rows)
    print("\nGate A — checker correctness (blocking)\n")
    for name, status, note in rows:
        print(f"  {name:<{width}}  {status:<5}  {note}")

    cleared = all([ok, ok_conv, ok_iso, ok_tol])
    print(f"\nGate A: {'CLEARED' if cleared else 'NOT CLEARED'}\n")
    return 0 if cleared else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_gate_a.py -v`
Expected: PASS, 2 tests

- [ ] **Step 5: Run the full suite and the gate**

Run: `pytest -v && python scripts/gate_a.py`
Expected: all tests pass; Gate A reports NOT CLEARED with TolAnalyst SKIP. That is the
correct state at the end of this plan — the oracle comparison needs the Phase 3 generator.

- [ ] **Step 6: Commit**

```bash
git add scripts/gate_a.py tests/test_gate_a.py
git commit -m "feat: Gate A report script"
```

---

### Task 12: NIST conformance oracle harness

**Files:**
- Create: `validation/nist_pmi.py`
- Test: `tests/test_nist_harness.py`

**Interfaces:**
- Consumes: nothing from core
- Produces: `validation.nist_pmi.load_expected(path) -> dict[str, bool]`, `validation.nist_pmi.agreement(ours, expected) -> float`, `validation.nist_pmi.disagreements(ours, expected) -> list[str]`

Spec v2 §7 adds the **NIST MBE PMI Validation and Conformance Test Suite** as a licence-free
Gate A oracle. Reading its STEP AP242 semantic PMI requires OCCT XCAF (`XCAFDoc_DimTolTool`),
which is a Phase 3 dependency — so this task builds the *comparison harness* only, exactly
mirroring the TolAnalyst pattern. The actual comparison runs in Phase 3.

CSV format: `part_id,assembles`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_nist_harness.py
import pytest
from validation.nist_pmi import agreement, disagreements, load_expected


def test_loads_expected_verdicts(tmp_path):
    csv = tmp_path / "nist.csv"
    csv.write_text("part_id,assembles\nFTC-06,true\nFTC-07,false\n", encoding="utf-8")
    got = load_expected(csv)
    assert got == {"FTC-06": True, "FTC-07": False}


def test_agreement_is_fraction_of_matching_verdicts():
    ours = {"FTC-06": True, "FTC-07": True}
    expected = {"FTC-06": True, "FTC-07": False}
    assert agreement(ours, expected) == pytest.approx(0.5)


def test_disagreements_are_listed_for_root_causing():
    ours = {"FTC-06": True, "FTC-07": True}
    expected = {"FTC-06": True, "FTC-07": False}
    assert disagreements(ours, expected) == ["FTC-07"]


def test_no_overlap_is_an_error_not_a_silent_pass():
    with pytest.raises(ValueError, match="no overlapping"):
        agreement({"A": True}, {"B": True})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_nist_harness.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'validation.nist_pmi'`

- [ ] **Step 3: Write minimal implementation**

```python
# validation/nist_pmi.py
"""Cross-check tolcad verdicts against the NIST MBE PMI Conformance Test Suite.

Public, authoritative, licence-free — this is the oracle that lets Gate A be cleared
without any commercial CAD licence.

Parsing the suite's STEP AP242 semantic PMI requires OCCT XCAF and happens in Phase 3.
This module only compares verdicts already extracted to CSV: part_id,assembles
"""

from __future__ import annotations

import csv
import pathlib


def load_expected(path: str | pathlib.Path) -> dict[str, bool]:
    """Read expected assembly verdicts keyed by NIST part id (e.g. FTC-06)."""
    out: dict[str, bool] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[row["part_id"]] = row["assembles"].strip().lower() == "true"
    return out


def agreement(ours: dict[str, bool], expected: dict[str, bool]) -> float:
    """Fraction of shared part ids where our verdict matches the expected one."""
    shared = set(ours) & set(expected)
    if not shared:
        raise ValueError("no overlapping part ids between the two verdict sets")
    return sum(1 for k in shared if ours[k] == expected[k]) / len(shared)


def disagreements(ours: dict[str, bool], expected: dict[str, bool]) -> list[str]:
    """Part ids where verdicts differ. Gate A requires each to be root-caused."""
    shared = set(ours) & set(expected)
    return sorted(k for k in shared if ours[k] != expected[k])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_nist_harness.py -v`
Expected: PASS, 4 tests

- [ ] **Step 5: Commit**

```bash
git add validation/nist_pmi.py tests/test_nist_harness.py
git commit -m "feat: NIST PMI conformance oracle harness"
```

---

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
