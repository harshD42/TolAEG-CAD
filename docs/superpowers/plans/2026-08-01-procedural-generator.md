# Procedural Toleranced-Assembly Generator Implementation Plan (Phase 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn a seed into a toleranced two-part assembly — CadQuery geometry, a JSON tolerance schema the existing checker consumes, a STEP export — and read semantic PMI from NIST AP242 files so the licence-free Gate A oracle can run.

**Architecture:** A pure-Python spec layer (`spec.py`, `features.py`, `sampler.py`) that has no CAD dependency and is fully testable on its own, plus a thin CAD layer (`build.py`, `export.py`) that turns a spec into solids. The tolerance schema is the *same dict shape* `tolcad.checker.check()` already accepts, so the generator and checker meet at an interface that exists and is tested. PMI reading lives in `validation/`, outside the core package.

**Tech Stack:** Python 3.13, CadQuery 2.8.0, OCP (OCCT 7.x bindings), numpy, pytest.

## Verified environment facts (spiked 2026-08-01, do not re-litigate)

These were confirmed by execution on this machine. Trust them.

- `pip install cadquery` succeeds on Windows / Python 3.13; resolves CadQuery **2.8.0** and pulls OCP.
- `cadquery.Assembly.save()` is **deprecated** (emits `FutureWarning`). Use `.export()`, which emits none.
- `Assembly.children` yields objects with `.name` and `.obj`; `.obj` is a `Workplane`, so `child.obj.val()` gives the `Shape` and `.isValid()` / `.Volume()` work on it.
- `Workplane.hole(diameter, depth=...)` accepts the `depth` keyword.
- **pytest 9.0.2 is installed. `pytest.warns(None)` was removed in pytest 8 and raises `TypeError`** — use `warnings.catch_warnings(record=True)`.
- `OCP.STEPCAFControl.STEPCAFControl_Writer` has `SetDimTolMode`, `SetColorMode`, `SetNameMode`, `SetLayerMode`, `SetMaterialMode`.
- `OCP.STEPCAFControl.STEPCAFControl_Reader` has `SetGDTMode`, `SetColorMode`, `SetNameMode`.
- The NIST suite downloads from
  `https://www.nist.gov/system/files/documents/noindex/2024/06/19/NIST-PMI-STEP-Files.zip`
  (~14 MB, 49 entries, 17 AP242 `.stp` files). NIST states the files "can be used without any restrictions."
- Reading `nist_ftc_06_asme1_ap242-e2.stp` with `SetGDTMode(True)` then `Transfer(doc)` yields
  **47 dimensions, 27 geometric tolerances, 59 datums** via `XCAFDoc_DocumentTool.DimTolTool_s`.
  The working call sequence is in Task 7.

## Global Constraints

- **All dimensions in millimetres, stored as `float`.** ISO 286 values are published in µm and converted only at the table boundary in `iso286.py`.
- **No module under `src/tolcad/` may import from `validation/`.** Enforced by `tests/test_architecture.py`.
- **The checker core must stay dependency-light.** `types`, `y14_5`, `iso286`, `montecarlo`, `checker`, `reliability` must NOT import `tolcad.gen` or CadQuery. CadQuery is an optional extra. Task 1 extends the lint to enforce this.
- **Every headline path runs with no SolidWorks licence.** The NIST oracle is the licence-free one.
- **Tier 1 must be exact.** `EPS = 1e-9`, no rounding.
- **Pre-registered thresholds are frozen:** `GATE_A_TOLERANCE = 0.005`, `AGREEMENT_THRESHOLD = 0.95`, `RELIABILITY_THRESHOLD = 0.95`.
- **Scope: Tier 1 and Tier 2 mates only** (spec §4.1). Tolerance loop length ≤ 4. Freeform mates are out.
- **This plan does NOT generate the research corpus.** Spec §12 puts public pre-registration (Phase 3.5) *before* any data generation. The generator must be able to produce assemblies on demand and be tested on small batches, but generating the corpus that produces published numbers happens after pre-registration. Do not add a "generate 10,000 assemblies" step.

---

## File structure

| File | Responsibility |
|---|---|
| `src/tolcad/gen/__init__.py` | Package marker |
| `src/tolcad/gen/spec.py` | `MateSpec`, `AssemblySpec` dataclasses; JSON round-trip; emits checker-ready dicts |
| `src/tolcad/gen/features.py` | Canonical mating-feature library: sizes, fit classes, ISO designations |
| `src/tolcad/gen/sampler.py` | `seed + difficulty -> AssemblySpec`, deterministic |
| `src/tolcad/gen/build.py` | `AssemblySpec -> cadquery.Assembly` |
| `src/tolcad/gen/export.py` | Assembly + spec -> STEP file + sidecar JSON |
| `validation/ap242_pmi.py` | Read semantic PMI counts/values from AP242 (NIST oracle) |
| `scripts/fetch_nist_pmi.py` | Download and verify the NIST suite |

`spec.py`, `features.py` and `sampler.py` import **no CAD libraries** — they are the part that must stay fast and trivially testable.

---

### Task 1: Optional `gen` extra and a lint that keeps the core light

**Files:**
- Modify: `pyproject.toml`
- Create: `src/tolcad/gen/__init__.py`
- Modify: `tests/test_architecture.py`

**Interfaces:**
- Consumes: nothing
- Produces: installable `tolcad[gen]` extra; importable `tolcad.gen`

The checker currently depends only on numpy, and that is worth protecting — it is why Gate A can run anywhere. CadQuery is heavy, so it goes behind an extra, and the lint gains a rule so nobody quietly imports it into the checker.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_architecture.py  (append)

CORE_LIGHT_MODULES = (
    "types", "y14_5", "iso286", "montecarlo", "checker", "reliability",
)
HEAVY_PACKAGES = {"cadquery", "OCP"}


def test_checker_core_does_not_import_cad_libraries():
    """The checker must stay installable and runnable without CadQuery.

    Gate A's "runs with no commercial licence" guarantee depends on the core
    being light. tolcad.gen may import CadQuery; the six modules below may not,
    and may not import tolcad.gen either.
    """
    offenders = []
    for stem in CORE_LIGHT_MODULES:
        path = CORE / f"{stem}.py"
        assert path.is_file(), f"expected core module missing: {path}"
        imported = _imported_modules(path)
        bad = {m for m in imported if m.split(".")[0] in HEAVY_PACKAGES}
        bad |= {m for m in imported if m.startswith("tolcad.gen")}
        if bad:
            offenders.append(f"{stem}.py imports {sorted(bad)}")
    assert not offenders, (
        "checker core must not depend on CAD libraries: " + "; ".join(offenders)
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_architecture.py::test_checker_core_does_not_import_cad_libraries -v`
Expected: FAIL — `_imported_modules` is defined in the file but `CORE_LIGHT_MODULES` is not yet, so this is a NameError until you append the constants. If it passes immediately, you have not appended the constants; check.

- [ ] **Step 3: Add the extra and the package**

In `pyproject.toml`, add to `[project.optional-dependencies]` alongside the existing `dev`:

```toml
gen = ["cadquery>=2.8"]
```

Create `src/tolcad/gen/__init__.py`:

```python
"""Procedural toleranced-assembly generation.

Imports CadQuery, which the checker core deliberately does not. Install with
`pip install -e ".[gen]"`. tests/test_architecture.py enforces that the six
core checker modules never import this package or CadQuery.
"""
```

- [ ] **Step 4: Run tests**

Run: `pip install -e ".[dev,gen]" && pytest -q`
Expected: all pass, including the new test.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/tolcad/gen/__init__.py tests/test_architecture.py
git commit -m "feat: optional gen extra, lint keeping checker core CAD-free"
```

---

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

### Task 3: Canonical mating-feature library

**Files:**
- Create: `src/tolcad/gen/features.py`
- Test: `tests/gen/test_features.py`

**Interfaces:**
- Consumes: `tolcad.iso286.fit_from_designation`
- Produces:
  - `FASTENER_SIZES: tuple[float, ...]` — nominal fastener diameters in mm
  - `clearance_hole_for(fastener_mm: float, grade: str) -> dict` where `grade` is `"close"`, `"normal"` or `"loose"`
  - `SUPPORTED_FITS: tuple[str, ...]` — ISO designations the checker accepts
  - `iso_fit_mate_features(nominal_mm: float, designation: str) -> tuple[dict, dict]`

Clearance-hole sizes follow the common metric series. These are ordinary engineering table values, not standard-restricted formulas, but the same discipline applies: state where they come from and pin them.

- [ ] **Step 1: Write the failing test**

```python
# tests/gen/test_features.py
import pytest
from tolcad.gen.features import (
    FASTENER_SIZES, SUPPORTED_FITS, clearance_hole_for, iso_fit_mate_features,
)


def test_fastener_sizes_are_the_common_metric_series():
    assert FASTENER_SIZES == (3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0)


@pytest.mark.parametrize("grade, expected_nominal", [
    ("close", 8.4), ("normal", 9.0), ("loose", 10.0),
])
def test_clearance_hole_for_m8(grade, expected_nominal):
    hole = clearance_hole_for(8.0, grade)
    assert hole["nominal"] == pytest.approx(expected_nominal)


def test_clearance_hole_is_always_at_least_the_fastener():
    for f in FASTENER_SIZES:
        for grade in ("close", "normal", "loose"):
            hole = clearance_hole_for(f, grade)
            mmc = hole["nominal"] + hole["lower_dev"]
            assert mmc >= f, f"M{f} {grade}: hole MMC {mmc} below fastener {f}"


def test_unknown_grade_rejected():
    with pytest.raises(ValueError, match="grade"):
        clearance_hole_for(8.0, "snug")


def test_unknown_fastener_size_rejected():
    with pytest.raises(ValueError, match="fastener"):
        clearance_hole_for(7.0, "normal")


def test_supported_fits_are_all_accepted_by_the_checker():
    from tolcad.iso286 import fit_from_designation
    for d in SUPPORTED_FITS:
        hole, shaft = fit_from_designation(20.0, d)
        assert hole.min_size < hole.max_size
        assert shaft.min_size < shaft.max_size


def test_iso_fit_mate_features_returns_hole_then_shaft():
    hole, shaft = iso_fit_mate_features(20.0, "H7/g6")
    assert hole["nominal"] == pytest.approx(20.0)
    # g6 shaft at 20 mm is es -7 um, ei -20 um
    assert shaft["upper_dev"] == pytest.approx(-0.007)
    assert shaft["lower_dev"] == pytest.approx(-0.020)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/gen/test_features.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.gen.features'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/gen/features.py
"""Canonical mating features for generated assemblies. No CAD dependency.

Clearance-hole diameters follow the common metric close/normal/loose series
(the ISO 273 style progression reproduced in general engineering references).
They are ordinary table values rather than a standard-restricted formula, but
they are pinned by tests so a silent edit cannot drift them.
"""

from __future__ import annotations

from tolcad.iso286 import fit_from_designation

FASTENER_SIZES: tuple[float, ...] = (3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0)

# fastener nominal -> (close, normal, loose) clearance hole nominal diameter, mm
_CLEARANCE_HOLE_MM: dict[float, tuple[float, float, float]] = {
    3.0: (3.2, 3.4, 3.6),
    4.0: (4.3, 4.5, 4.8),
    5.0: (5.3, 5.5, 5.8),
    6.0: (6.4, 6.6, 7.0),
    8.0: (8.4, 9.0, 10.0),
    10.0: (10.5, 11.0, 12.0),
    12.0: (13.0, 13.5, 14.5),
}
_GRADE_INDEX = {"close": 0, "normal": 1, "loose": 2}

# Hole tolerance applied to a generated clearance hole: H13-ish, +0.2/-0.0 mm.
_HOLE_UPPER_DEV_MM = 0.2

SUPPORTED_FITS: tuple[str, ...] = ("H7/g6", "H7/h6", "H7/k6", "H7/p6")


def clearance_hole_for(fastener_mm: float, grade: str) -> dict:
    """Return a checker-ready hole dict for a fastener at a clearance grade."""
    if fastener_mm not in _CLEARANCE_HOLE_MM:
        raise ValueError(
            f"fastener size {fastener_mm} not tabulated; have {FASTENER_SIZES}"
        )
    if grade not in _GRADE_INDEX:
        raise ValueError(f"grade must be one of {sorted(_GRADE_INDEX)}, got {grade!r}")
    nominal = _CLEARANCE_HOLE_MM[fastener_mm][_GRADE_INDEX[grade]]
    return {
        "nominal": nominal,
        "lower_dev": 0.0,
        "upper_dev": _HOLE_UPPER_DEV_MM,
        "position_tol": 0.0,
    }


def iso_fit_mate_features(nominal_mm: float, designation: str) -> tuple[dict, dict]:
    """Return (hole, shaft) dicts for an ISO 286 fit, in checker dict form."""
    if designation not in SUPPORTED_FITS:
        raise ValueError(
            f"fit {designation!r} not supported; have {SUPPORTED_FITS}"
        )
    hole, shaft = fit_from_designation(nominal_mm, designation)
    return (
        {"nominal": hole.nominal, "lower_dev": hole.lower_dev,
         "upper_dev": hole.upper_dev, "position_tol": 0.0},
        {"nominal": shaft.nominal, "lower_dev": shaft.lower_dev,
         "upper_dev": shaft.upper_dev},
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/gen/test_features.py -v`
Expected: PASS, 10 tests (the parametrised one counts as 3)

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/gen/features.py tests/gen/test_features.py
git commit -m "feat: canonical mating-feature library"
```

---

### Task 4: Deterministic sampler

**Files:**
- Create: `src/tolcad/gen/sampler.py`
- Test: `tests/gen/test_sampler.py`

**Interfaces:**
- Consumes: `AssemblySpec`, `MateSpec`, `features.*`
- Produces: `sample_assembly(seed: int, difficulty: int) -> AssemblySpec`

`difficulty` is an integer 1–4 and controls the number of mates (= tolerance loop length, capped at 4 per spec §4.1) and how tight the position tolerances are relative to the allowable. Determinism matters more than realism here: the corpus must be reproducible from a seed alone.

- [ ] **Step 1: Write the failing test**

```python
# tests/gen/test_sampler.py
import pytest
from tolcad.checker import check
from tolcad.gen.sampler import sample_assembly


def test_same_seed_gives_identical_spec():
    assert sample_assembly(7, 2) == sample_assembly(7, 2)


def test_different_seeds_give_different_specs():
    specs = {sample_assembly(s, 2).to_json() for s in range(20)}
    assert len(specs) > 1, "sampler is ignoring the seed"


def test_difficulty_controls_mate_count_and_is_capped_at_four():
    for difficulty in (1, 2, 3, 4):
        spec = sample_assembly(0, difficulty)
        assert len(spec.mates) == difficulty
    # spec section 4.1 caps the tolerance loop at 4 contributors
    with pytest.raises(ValueError, match="difficulty"):
        sample_assembly(0, 5)


def test_every_generated_mate_is_checkable():
    """The generator must never emit a mate the checker rejects."""
    for seed in range(50):
        for difficulty in (1, 2, 3, 4):
            for mate in sample_assembly(seed, difficulty).mates:
                verdict = check(mate.to_check_dict())
                assert isinstance(verdict.assembles, bool)


def test_corpus_contains_both_passing_and_failing_mates():
    """A generator that only produces assemblable parts measures nothing.

    Guards the failure mode this project has hit repeatedly: a fixture that
    cannot exercise the negative branch.
    """
    verdicts = [
        check(m.to_check_dict()).assembles
        for seed in range(80)
        for m in sample_assembly(seed, 3).mates
    ]
    assert any(verdicts), "no assemblable mates generated"
    assert not all(verdicts), "no non-assemblable mates generated"


def test_seed_and_difficulty_are_recorded_in_the_spec():
    spec = sample_assembly(13, 3)
    assert spec.seed == 13
    assert spec.difficulty == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/gen/test_sampler.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.gen.sampler'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/gen/sampler.py
"""Seed -> AssemblySpec. Deterministic, no CAD dependency.

Difficulty 1-4 sets the number of mates (the tolerance loop length, capped at 4
by spec section 4.1) and how tightly position tolerances crowd the allowable.
Higher difficulty produces more marginal joints, so the corpus contains both
assemblable and non-assemblable cases by construction.
"""

from __future__ import annotations

import numpy as np

from tolcad.gen.features import (
    FASTENER_SIZES, SUPPORTED_FITS, clearance_hole_for, iso_fit_mate_features,
)
from tolcad.gen.spec import AssemblySpec, MateSpec

MAX_DIFFICULTY = 4

# Fraction of the allowable position tolerance actually applied, by difficulty.
# At difficulty 4 the range straddles 1.0, so some joints fail.
_TOL_FRACTION_RANGE = {
    1: (0.20, 0.50),
    2: (0.40, 0.80),
    3: (0.60, 1.00),
    4: (0.80, 1.30),
}

_TIER1_KINDS = ("floating_fastener", "fixed_fastener")


def _tier1_mate(rng: np.random.Generator, difficulty: int) -> MateSpec:
    fastener_mm = float(rng.choice(FASTENER_SIZES))
    grade = str(rng.choice(("close", "normal", "loose")))
    kind = str(rng.choice(_TIER1_KINDS))

    hole = clearance_hole_for(fastener_mm, grade)
    fastener = {"nominal": fastener_mm, "lower_dev": -0.1, "upper_dev": 0.0}

    # Allowable per Y14.5: floating T = H - F; fixed splits H - F across both parts.
    hole_mmc = hole["nominal"] + hole["lower_dev"]
    allowable = hole_mmc - fastener_mm
    if kind == "fixed_fastener":
        allowable /= 2.0

    lo, hi = _TOL_FRACTION_RANGE[difficulty]
    tol_a = round(allowable * float(rng.uniform(lo, hi)), 4)
    tol_b = round(allowable * float(rng.uniform(lo, hi)), 4)

    return MateSpec(
        kind=kind,
        nominal_mm=fastener_mm,
        hole_a=dict(hole, position_tol=tol_a),
        hole_b=dict(hole, position_tol=tol_b),
        fastener=fastener,
        designation=None,
        position_tol_a=tol_a,
        position_tol_b=tol_b,
    )


def _iso_fit_mate(rng: np.random.Generator) -> MateSpec:
    nominal = float(rng.choice((10.0, 12.0, 16.0, 20.0, 25.0)))
    designation = str(rng.choice(SUPPORTED_FITS))
    iso_fit_mate_features(nominal, designation)  # validates the pair
    return MateSpec(
        kind="iso_fit", nominal_mm=nominal, hole_a=None, hole_b=None,
        fastener=None, designation=designation,
        position_tol_a=0.0, position_tol_b=0.0,
    )


def sample_assembly(seed: int, difficulty: int) -> AssemblySpec:
    """Deterministically sample one assembly."""
    if not 1 <= difficulty <= MAX_DIFFICULTY:
        raise ValueError(
            f"difficulty must be 1-{MAX_DIFFICULTY} (spec section 4.1 caps the "
            f"tolerance loop at {MAX_DIFFICULTY} contributors), got {difficulty}"
        )
    rng = np.random.default_rng(seed)
    mates = [
        _iso_fit_mate(rng) if rng.random() < 0.25 else _tier1_mate(rng, difficulty)
        for _ in range(difficulty)
    ]
    return AssemblySpec(seed=seed, difficulty=difficulty, mates=mates)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/gen/test_sampler.py -v`
Expected: PASS, 6 tests. If `test_corpus_contains_both_passing_and_failing_mates` fails, do NOT widen `_TOL_FRACTION_RANGE` blindly — print the verdict distribution first and check the allowable arithmetic matches `y14_5.fastener_assembles`.

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/gen/sampler.py tests/gen/test_sampler.py
git commit -m "feat: deterministic assembly sampler"
```

---

### Task 5: Build CadQuery geometry from a spec

**Files:**
- Create: `src/tolcad/gen/build.py`
- Test: `tests/gen/test_build.py`

**Interfaces:**
- Consumes: `AssemblySpec`
- Produces: `build_assembly(spec: AssemblySpec) -> cadquery.Assembly`

Two square plates, stacked, with one clearance hole per Tier 1 mate arranged on a line. `iso_fit` mates contribute a bore in the lower plate and are not drilled through. Geometry realism is explicitly *not* the goal — reproducibility and a valid B-rep are.

- [ ] **Step 1: Write the failing test**

```python
# tests/gen/test_build.py
import pytest

cq = pytest.importorskip("cadquery", reason="requires the [gen] extra")

from tolcad.gen.build import build_assembly
from tolcad.gen.sampler import sample_assembly


def test_builds_a_two_part_assembly():
    asm = build_assembly(sample_assembly(1, 2))
    names = {child.name for child in asm.children}
    assert names == {"part_a", "part_b"}


def test_geometry_is_a_valid_solid_with_positive_volume():
    asm = build_assembly(sample_assembly(1, 2))
    for child in asm.children:
        solid = child.obj.val()
        assert solid.isValid(), f"{child.name} produced an invalid solid"
        assert solid.Volume() > 0.0


def test_drilling_holes_removes_material():
    """A hole that removed nothing would silently make every part identical."""
    one = build_assembly(sample_assembly(2, 1))
    four = build_assembly(sample_assembly(2, 4))
    vol_one = sum(c.obj.val().Volume() for c in one.children)
    vol_four = sum(c.obj.val().Volume() for c in four.children)
    assert vol_four < vol_one, "more mates did not remove more material"


def test_same_seed_gives_identical_volume():
    a = sum(c.obj.val().Volume() for c in build_assembly(sample_assembly(5, 3)).children)
    b = sum(c.obj.val().Volume() for c in build_assembly(sample_assembly(5, 3)).children)
    assert a == pytest.approx(b)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/gen/test_build.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.gen.build'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/gen/build.py
"""AssemblySpec -> CadQuery geometry.

Deliberately simple: two stacked square plates with one feature per mate on a
line. The research question is about tolerances, not shape variety, so the
geometry only has to be a valid B-rep that a CAD reader can consume.
"""

from __future__ import annotations

import cadquery as cq

from tolcad.gen.spec import AssemblySpec

_FEATURE_PITCH_MM = 12.0


def _feature_positions(count: int) -> list[float]:
    """Evenly spaced x positions, centred on the origin."""
    span = _FEATURE_PITCH_MM * (count - 1)
    return [(-span / 2.0) + i * _FEATURE_PITCH_MM for i in range(count)]


def build_assembly(spec: AssemblySpec) -> cq.Assembly:
    """Build a two-plate assembly with one feature per mate."""
    size = spec.plate_size_mm
    thickness = spec.plate_thickness_mm
    xs = _feature_positions(len(spec.mates))

    part_a = cq.Workplane("XY").box(size, size, thickness)
    part_b = cq.Workplane("XY").box(size, size, thickness)

    for x, mate in zip(xs, spec.mates):
        if mate.kind == "iso_fit":
            # A blind bore in the lower plate; the shaft is not modelled.
            part_b = (
                part_b.faces(">Z").workplane().center(x, 0.0)
                .hole(mate.nominal_mm, depth=thickness / 2.0)
            )
            continue
        dia_a = mate.hole_a["nominal"]
        dia_b = mate.hole_b["nominal"]
        part_a = part_a.faces(">Z").workplane().center(x, 0.0).hole(dia_a)
        part_b = part_b.faces(">Z").workplane().center(x, 0.0).hole(dia_b)

    asm = cq.Assembly(name=f"assembly_seed{spec.seed}_d{spec.difficulty}")
    asm.add(part_a, name="part_a", loc=cq.Location(cq.Vector(0, 0, thickness)))
    asm.add(part_b, name="part_b", loc=cq.Location(cq.Vector(0, 0, 0)))
    return asm
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/gen/test_build.py -v`
Expected: PASS, 4 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/gen/build.py tests/gen/test_build.py
git commit -m "feat: build CadQuery geometry from an assembly spec"
```

---

### Task 6: Export STEP plus a sidecar tolerance schema

**Files:**
- Create: `src/tolcad/gen/export.py`
- Test: `tests/gen/test_export.py`

**Interfaces:**
- Consumes: `AssemblySpec`, `build_assembly`
- Produces: `export_assembly(spec: AssemblySpec, out_dir: Path) -> tuple[Path, Path]` returning `(step_path, json_path)`

The sidecar JSON is the tolerance schema. Per spec §4.2 the schema belongs to the *reference design*: it travels with the reference geometry and is later applied to a model's *predicted* geometry. Keeping it beside the STEP rather than inside it is what makes that separation obvious.

Note: `cq.Assembly.save()` is deprecated in CadQuery 2.8 — use `.export()`.

- [ ] **Step 1: Write the failing test**

```python
# tests/gen/test_export.py
import json
import pytest

pytest.importorskip("cadquery", reason="requires the [gen] extra")

from tolcad.gen.export import export_assembly
from tolcad.gen.sampler import sample_assembly
from tolcad.gen.spec import AssemblySpec


def test_writes_a_step_file_and_a_sidecar_json(tmp_path):
    spec = sample_assembly(3, 2)
    step_path, json_path = export_assembly(spec, tmp_path)
    assert step_path.is_file() and step_path.stat().st_size > 0
    assert json_path.is_file() and json_path.stat().st_size > 0


def test_step_file_has_a_step_header(tmp_path):
    step_path, _ = export_assembly(sample_assembly(3, 2), tmp_path)
    assert step_path.read_text(errors="ignore").startswith("ISO-10303-21;")


def test_sidecar_round_trips_back_to_the_original_spec(tmp_path):
    spec = sample_assembly(4, 3)
    _, json_path = export_assembly(spec, tmp_path)
    assert AssemblySpec.from_json(json_path.read_text(encoding="utf-8")) == spec


def test_filenames_encode_seed_and_difficulty(tmp_path):
    step_path, json_path = export_assembly(sample_assembly(11, 2), tmp_path)
    assert "seed11" in step_path.name and "d2" in step_path.name
    assert step_path.stem == json_path.stem


def test_export_does_not_emit_a_deprecation_warning(tmp_path):
    """CadQuery 2.8 deprecated Assembly.save; we must be on .export.

    Note: pytest.warns(None) was REMOVED in pytest 8 and raises TypeError on the
    pytest 9 installed here. Use warnings.catch_warnings instead.
    """
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        export_assembly(sample_assembly(6, 1), tmp_path)
    future = [w for w in caught if issubclass(w.category, FutureWarning)]
    assert not future, f"deprecated CadQuery API in use: {[str(w.message) for w in future]}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/gen/test_export.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad.gen.export'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tolcad/gen/export.py
"""Write a generated assembly to disk: STEP geometry plus a sidecar schema.

The tolerance schema is kept BESIDE the STEP rather than embedded in it. Per
spec section 4.2 the schema belongs to the reference design and is later applied
to a model's predicted geometry; keeping the two files separate makes that
separation explicit rather than implied.
"""

from __future__ import annotations

import pathlib

from tolcad.gen.build import build_assembly
from tolcad.gen.spec import AssemblySpec


def _stem(spec: AssemblySpec) -> str:
    return f"assembly_seed{spec.seed}_d{spec.difficulty}"


def export_assembly(
    spec: AssemblySpec, out_dir: str | pathlib.Path
) -> tuple[pathlib.Path, pathlib.Path]:
    """Write <stem>.step and <stem>.json into out_dir; return both paths."""
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = _stem(spec)
    step_path = out_dir / f"{stem}.step"
    json_path = out_dir / f"{stem}.json"

    # CadQuery 2.8 deprecated Assembly.save in favour of Assembly.export.
    build_assembly(spec).export(str(step_path))
    json_path.write_text(spec.to_json(), encoding="utf-8")
    return step_path, json_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/gen/test_export.py -v`
Expected: PASS, 5 tests

- [ ] **Step 5: Commit**

```bash
git add src/tolcad/gen/export.py tests/gen/test_export.py
git commit -m "feat: export STEP geometry with a sidecar tolerance schema"
```

---

### Task 7: Read semantic PMI from AP242

**Files:**
- Create: `validation/ap242_pmi.py`
- Test: `tests/test_ap242_pmi.py`

**Interfaces:**
- Consumes: OCP XCAF
- Produces: `read_pmi_counts(step_path) -> PmiCounts` where `PmiCounts` is a frozen dataclass with `dimensions: int`, `geometric_tolerances: int`, `datums: int`

This is the NIST oracle's read path. It lives in `validation/` because it is oracle infrastructure; the core checker must not depend on it.

**The exact call sequence below was verified by execution** against `nist_ftc_06_asme1_ap242-e2.stp`, which yields 47 dimensions, 27 geometric tolerances and 59 datums. Do not restructure it speculatively.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ap242_pmi.py
import pathlib
import pytest

pytest.importorskip("OCP", reason="requires the [gen] extra")

from validation.ap242_pmi import PmiCounts, read_pmi_counts

NIST_DIR = pathlib.Path(__file__).parent.parent / "data" / "nist_pmi"
FTC06 = NIST_DIR / "nist_ftc_06_asme1_ap242-e2.stp"

pytestmark = pytest.mark.skipif(
    not FTC06.is_file(),
    reason="NIST suite not fetched; run scripts/fetch_nist_pmi.py",
)


def test_reads_semantic_pmi_from_nist_ftc06():
    """Verified by execution 2026-08-01: 47 dimensions, 27 geotols, 59 datums.

    These are exact expected values, not bounds. If OCCT's extraction changes,
    this must fail loudly rather than silently reporting fewer tolerances.
    """
    counts = read_pmi_counts(FTC06)
    assert counts == PmiCounts(dimensions=47, geometric_tolerances=27, datums=59)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        read_pmi_counts(NIST_DIR / "does_not_exist.stp")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ap242_pmi.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'validation.ap242_pmi'` (or SKIP if the NIST suite is not yet fetched — Task 8 fetches it; if it skips, come back and re-run after Task 8)

- [ ] **Step 3: Write minimal implementation**

```python
# validation/ap242_pmi.py
"""Read semantic PMI from STEP AP242, for the NIST conformance oracle.

Oracle infrastructure: lives in validation/ so the checker core never depends
on OCP. The call sequence below was verified by execution against
nist_ftc_06_asme1_ap242-e2.stp (47 dimensions, 27 geometric tolerances,
59 datums).

Semantic PMI only. Graphical PMI (the rendered annotation symbols) needs either
OCCT's commercial visualisation component or manual tessellation, and is not
required here: the checker consumes tolerance semantics, not drawing marks.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

from OCP.IFSelect import IFSelect_ReturnStatus
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDF import TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool


@dataclass(frozen=True)
class PmiCounts:
    """How many semantic PMI entities a STEP AP242 file carries."""

    dimensions: int
    geometric_tolerances: int
    datums: int


def read_pmi_counts(step_path: str | pathlib.Path) -> PmiCounts:
    """Count semantic PMI entities in an AP242 file."""
    step_path = pathlib.Path(step_path)
    if not step_path.is_file():
        raise FileNotFoundError(f"no such STEP file: {step_path}")

    doc = TDocStd_Document(TCollection_ExtendedString("tolcad"))
    reader = STEPCAFControl_Reader()
    reader.SetGDTMode(True)
    reader.SetNameMode(True)
    reader.SetColorMode(True)

    status = reader.ReadFile(str(step_path))
    if status != IFSelect_ReturnStatus.IFSelect_RetDone:
        raise ValueError(f"OCCT could not read {step_path.name}: {status}")
    if not reader.Transfer(doc):
        raise ValueError(f"OCCT could not transfer {step_path.name} into a document")

    tool = XCAFDoc_DocumentTool.DimTolTool_s(doc.Main())

    def _count(getter) -> int:
        seq = TDF_LabelSequence()
        getter(seq)
        return seq.Length()

    return PmiCounts(
        dimensions=_count(tool.GetDimensionLabels),
        geometric_tolerances=_count(tool.GetGeomToleranceLabels),
        datums=_count(tool.GetDatumLabels),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ap242_pmi.py -v`
Expected: PASS, 2 tests (run Task 8 first if they skip)

- [ ] **Step 5: Commit**

```bash
git add validation/ap242_pmi.py tests/test_ap242_pmi.py
git commit -m "feat: read semantic PMI from STEP AP242"
```

---

### Task 8: Fetch and verify the NIST conformance suite

**Files:**
- Create: `scripts/fetch_nist_pmi.py`
- Modify: `.gitignore`
- Test: `tests/test_fetch_nist.py`

**Interfaces:**
- Consumes: nothing
- Produces: `data/nist_pmi/*.stp`; `scripts/fetch_nist_pmi.py` as a CLI

Mirrors the existing `scripts/fetch_literature.sh` convention: the payload is gitignored, the fetcher and its manifest are tracked, so the corpus stays reproducible and auditable.

The archive is ~14 MB with 49 entries, 17 of them AP242 `.stp`. NIST states the files "can be used without any restrictions."

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fetch_nist.py
import pathlib

REPO = pathlib.Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "fetch_nist_pmi.py"


def test_fetcher_script_exists():
    assert SCRIPT.is_file()


def test_fetcher_records_the_source_url_and_licence_statement():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "NIST-PMI-STEP-Files.zip" in text
    assert "without any restrictions" in text, (
        "record NIST's usage statement so provenance is auditable"
    )


def test_nist_payload_is_gitignored():
    ignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "data/nist_pmi/" in ignore
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fetch_nist.py -v`
Expected: FAIL — the script does not exist

- [ ] **Step 3: Write the fetcher**

```python
#!/usr/bin/env python
"""Fetch the NIST MBE PMI Validation and Conformance Test Suite.

Source: https://www.nist.gov/system/files/documents/noindex/2024/06/19/NIST-PMI-STEP-Files.zip
(reached from https://www.nist.gov/document/nist-pmi-step-files)

NIST states the test cases, CAD models and STEP files "can be used without any
restrictions", and asks for acknowledgement. This is the licence-free Gate A
oracle: it is why Gate A can be cleared with no commercial CAD licence.

Payload lands in data/nist_pmi/ and is gitignored; this script is tracked, so
the corpus is reproducible from the repo alone.

Usage: python scripts/fetch_nist_pmi.py
"""

from __future__ import annotations

import pathlib
import sys
import urllib.request
import zipfile

URL = (
    "https://www.nist.gov/system/files/documents/noindex/2024/06/19/"
    "NIST-PMI-STEP-Files.zip"
)
DEST = pathlib.Path(__file__).parent.parent / "data" / "nist_pmi"
EXPECTED_AP242_FILES = 17


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    archive = DEST / "NIST-PMI-STEP-Files.zip"

    if not archive.is_file():
        print(f"downloading {URL}")
        request = urllib.request.Request(
            URL, headers={"User-Agent": "tolcad-research/0.1 (academic use)"}
        )
        with urllib.request.urlopen(request) as response:
            archive.write_bytes(response.read())
    print(f"archive: {archive.stat().st_size} bytes")

    with zipfile.ZipFile(archive) as zf:
        members = [n for n in zf.namelist() if n.lower().endswith(".stp")]
        for name in members:
            target = DEST / pathlib.Path(name).name
            if not target.is_file():
                target.write_bytes(zf.read(name))

    ap242 = sorted(p.name for p in DEST.glob("*ap242*.stp"))
    print(f"extracted {len(list(DEST.glob('*.stp')))} STEP files, "
          f"{len(ap242)} AP242")
    if len(ap242) != EXPECTED_AP242_FILES:
        print(
            f"WARNING: expected {EXPECTED_AP242_FILES} AP242 files, got "
            f"{len(ap242)}. The upstream archive may have changed; verify "
            f"before using these as an oracle.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Append to `.gitignore`:

```
# NIST PMI conformance suite: ~14MB, reproducible via scripts/fetch_nist_pmi.py
data/nist_pmi/
```

- [ ] **Step 4: Run the fetcher and the tests**

Run: `python scripts/fetch_nist_pmi.py && pytest tests/test_fetch_nist.py tests/test_ap242_pmi.py -v`
Expected: fetcher exits 0 reporting 17 AP242 files; both test files pass (Task 7's tests now run rather than skip)

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_nist_pmi.py tests/test_fetch_nist.py .gitignore
git commit -m "feat: fetch and verify the NIST PMI conformance suite"
```

---

### Task 9: End-to-end generation and a round-trip guard

**Files:**
- Create: `tests/gen/test_end_to_end.py`

**Interfaces:**
- Consumes: everything above
- Produces: no new API — this is the integration gate

The point is to prove the loop closes: a seed produces geometry and a schema, the schema feeds the checker, and the STEP is re-readable by the same OCCT machinery the oracle uses.

- [ ] **Step 1: Write the failing test**

```python
# tests/gen/test_end_to_end.py
import pytest

pytest.importorskip("cadquery", reason="requires the [gen] extra")

from tolcad.checker import check
from tolcad.gen.export import export_assembly
from tolcad.gen.sampler import sample_assembly
from tolcad.gen.spec import AssemblySpec


def test_seed_to_verdict_round_trip(tmp_path):
    """seed -> spec -> STEP + JSON -> reload -> checker verdict."""
    spec = sample_assembly(21, 3)
    step_path, json_path = export_assembly(spec, tmp_path)

    reloaded = AssemblySpec.from_json(json_path.read_text(encoding="utf-8"))
    assert reloaded == spec

    verdicts = [check(m.to_check_dict()) for m in reloaded.mates]
    assert len(verdicts) == 3
    assert all(isinstance(v.assembles, bool) for v in verdicts)
    assert step_path.stat().st_size > 0


def test_exported_step_is_readable_by_the_oracle_machinery(tmp_path):
    """Our own STEP must load in the same reader used for the NIST oracle.

    It carries no semantic PMI (tolerances live in the sidecar), so the counts
    are expected to be zero — the point is that the file parses cleanly.
    """
    pytest.importorskip("OCP", reason="requires the [gen] extra")
    from validation.ap242_pmi import read_pmi_counts

    step_path, _ = export_assembly(sample_assembly(22, 2), tmp_path)
    counts = read_pmi_counts(step_path)
    assert counts.dimensions == 0
    assert counts.geometric_tolerances == 0
    assert counts.datums == 0


def test_a_batch_of_seeds_generates_without_error(tmp_path):
    """Small batch only. The research corpus is generated after Phase 3.5
    pre-registration, not here."""
    for seed in range(5):
        spec = sample_assembly(seed, 2)
        step_path, json_path = export_assembly(spec, tmp_path)
        assert step_path.is_file() and json_path.is_file()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/gen/test_end_to_end.py -v`
Expected: FAIL until Tasks 1–8 are complete; once they are, it should pass

- [ ] **Step 3: No implementation needed**

This task adds no production code. If a test fails, fix the module it exercises rather than weakening the assertion.

- [ ] **Step 4: Run the full suite**

Run: `pytest -q && python scripts/gate_a.py`
Expected: all pass; Gate A still exits 1

- [ ] **Step 5: Commit**

```bash
git add tests/gen/test_end_to_end.py
git commit -m "test: end-to-end seed-to-verdict round trip"
```

---

## Plan completion state

At the end of Task 9:

- A seed deterministically produces a toleranced two-part assembly
- The tolerance schema is the checker's own dict format, validated against it
- STEP geometry exports and re-reads cleanly
- Semantic PMI reads from real NIST AP242 files, pinned to verified counts
- The checker core is still numpy-only, enforced by lint

**Deliberately NOT done here:**
- Generating the research corpus — spec §12 puts pre-registration (Phase 3.5) first
- Writing semantic PMI *into* our own STEP files. `STEPCAFControl_Writer.SetDimTolMode` exists and the spike confirmed it, but nothing in the pipeline needs it: our tolerances live in the sidecar, and the NIST oracle only needs the read path. Add it only if the optional SolidWorks/TolAnalyst oracle turns out to require importable tolerances.
- Wiring the NIST oracle into `scripts/gate_a.py`. That needs the comparison corpus, which follows pre-registration.
- Emitting reference **CadQuery source text** alongside the geometry. Spec §5 lists "CadQuery program" among the generator's outputs, and this plan produces geometry + STEP + schema but not the program text. Deferred deliberately: the baselines *predict* CadQuery code and are scored against reference geometry, so nothing in Phase 4 consumes reference source. Revisit if an experiment ends up needing code-level comparison.

## Open question for the human

Task 3's clearance-hole table (close/normal/loose per fastener size) follows the common metric series. Unlike the Y14.5 formulas and ISO 286 tables, it is not currently traced to a specific standard edition. If these assemblies are meant to look conventional to a mechanical engineer, it is worth confirming the series against ISO 273 or the co-author's house standard. It affects realism, not correctness — every value is pinned by tests either way.
