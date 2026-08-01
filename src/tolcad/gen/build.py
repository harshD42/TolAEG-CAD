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
