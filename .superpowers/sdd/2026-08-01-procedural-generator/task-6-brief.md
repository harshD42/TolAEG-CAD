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

