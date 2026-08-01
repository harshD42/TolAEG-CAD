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
