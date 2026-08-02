### Task 2: `MateSpec` and `AssemblySpec`

**Files:**
- Create: `src/tolcad/gen/spec.py`
- Test: `tests/gen/test_spec.py`

**Interfaces:**
- Consumes: nothing (pure Python, no CAD)
- Produces:
  - `MateSpec(kind, nominal_mm, hole_a, hole_b, fastener, designation, position_tol_a, position_tol_b)` — a frozen dataclass
  - `MateSpec.to_check_dict() -> dict` — the dict `tolcad.checker.check()` accepts
  - `AssemblySpec(seed, difficulty, mates, plate_size_mm, plate_thickness_mm)` with `to_json() -> str` and `AssemblySpec.from_json(str) -> AssemblySpec`

The spec is the contract between generation and checking. It must serialise losslessly, because the sidecar JSON is what a reproducer reads.

- [ ] **Step 1: Write the failing test**

```python
# tests/gen/test_spec.py
import pytest
from tolcad.gen.spec import AssemblySpec, MateSpec
from tolcad.checker import check


def _floating_mate() -> MateSpec:
    return MateSpec(
        kind="floating_fastener",
        nominal_mm=8.0,
        hole_a={"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.3},
        hole_b={"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.3},
        fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
        designation=None,
        position_tol_a=0.3,
        position_tol_b=0.3,
    )


def test_mate_spec_emits_a_dict_the_checker_accepts():
    verdict = check(_floating_mate().to_check_dict())
    # allowable per part = 8.5 - 8.0 = 0.5; applied 0.3 -> margin +0.2
    assert verdict.margin == pytest.approx(0.2)
    assert verdict.assembles is True


def test_iso_fit_mate_emits_a_checker_dict():
    mate = MateSpec(
        kind="iso_fit", nominal_mm=20.0, hole_a=None, hole_b=None,
        fastener=None, designation="H7/g6", position_tol_a=0.0, position_tol_b=0.0,
    )
    d = mate.to_check_dict()
    assert d["type"] == "iso_fit"
    assert d["designation"] == "H7/g6"
    assert check(d).margin == pytest.approx(1.0)  # clearance fit, full yield


def test_assembly_spec_json_round_trip_is_lossless():
    original = AssemblySpec(
        seed=42, difficulty=2, mates=[_floating_mate()],
        plate_size_mm=40.0, plate_thickness_mm=8.0,
    )
    restored = AssemblySpec.from_json(original.to_json())
    assert restored == original


def test_unknown_mate_kind_rejected():
    with pytest.raises(ValueError, match="kind"):
        MateSpec(
            kind="weld", nominal_mm=8.0, hole_a=None, hole_b=None, fastener=None,
            designation=None, position_tol_a=0.0, position_tol_b=0.0,
        )


def test_assembly_spec_rejects_empty_mate_list():
    with pytest.raises(ValueError, match="at least one mate"):
        AssemblySpec(seed=1, difficulty=1, mates=[], plate_size_mm=40.0,
                     plate_thickness_mm=8.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/gen/test_spec.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.gen.spec'`
(create `tests/gen/__init__.py` if pytest needs it for collection)

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/gen/spec.py
"""Specification objects for generated assemblies. No CAD dependency.

The spec is the contract between generation and checking: MateSpec.to_check_dict
returns exactly the dict shape tolcad.checker.check already accepts, so the two
halves meet at an interface that is already implemented and tested.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

VALID_KINDS = frozenset(
    {"virtual_condition", "floating_fastener", "fixed_fastener", "iso_fit"}
)


@dataclass(frozen=True)
class MateSpec:
    """One mate. Tier 1 kinds use the hole/fastener dicts; iso_fit uses designation."""

    kind: str
    nominal_mm: float
    hole_a: dict | None
    hole_b: dict | None
    fastener: dict | None
    designation: str | None
    position_tol_a: float
    position_tol_b: float

    def __post_init__(self) -> None:
        if self.kind not in VALID_KINDS:
            raise ValueError(
                f"unknown mate kind {self.kind!r}; have {sorted(VALID_KINDS)}"
            )
        if self.kind == "iso_fit" and not self.designation:
            raise ValueError("iso_fit mate requires a designation such as 'H7/g6'")
        if self.kind != "iso_fit" and self.fastener is None:
            raise ValueError(f"{self.kind} mate requires a fastener")

    def to_check_dict(self) -> dict:
        """Return the dict accepted by tolcad.checker.check."""
        if self.kind == "iso_fit":
            return {
                "type": "iso_fit",
                "nominal": self.nominal_mm,
                "designation": self.designation,
            }
        if self.kind == "virtual_condition":
            return {"type": "virtual_condition", "pin": self.fastener,
                    "hole": self.hole_a}
        return {
            "type": self.kind,
            "hole_a": self.hole_a,
            "hole_b": self.hole_b,
            "fastener": self.fastener,
        }


@dataclass(frozen=True)
class AssemblySpec:
    """A whole generated assembly: plates plus the mates joining them."""

    seed: int
    difficulty: int
    mates: list[MateSpec] = field(default_factory=list)
    plate_size_mm: float = 40.0
    plate_thickness_mm: float = 8.0

    def __post_init__(self) -> None:
        if not self.mates:
            raise ValueError("an assembly needs at least one mate")

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> AssemblySpec:
        raw = json.loads(text)
        mates = [MateSpec(**m) for m in raw.pop("mates")]
        return cls(mates=mates, **raw)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/gen/test_spec.py -v`
Expected: PASS, 5 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/gen/spec.py tests/gen/
git commit -m "feat: AssemblySpec and MateSpec, checker-compatible by construction"
```

---

