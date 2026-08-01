"""AssemblySpec -> CadQuery geometry.

Deliberately simple: two stacked square plates with one feature per mate on a
line. The research question is about tolerances, not shape variety, so the
geometry only has to be a valid B-rep that a CAD reader can consume.

ABSOLUTE PLACEMENT IS LOAD-BEARING. `.faces(">Z").workplane()` defaults to
`centerOption="ProjectedOrigin"`, which inherits the *parent* workplane's
origin, so a following `.center(x, 0)` is a relative offset from the previous
feature rather than an absolute coordinate. Chaining that per feature makes
each hole land at the cumulative sum of the requested offsets: three holes
requested at x = -12, 0, +12 produced cylinders at -12 and 0 only, the third
having drifted off the plate. Every feature is therefore drilled from a
workplane pinned with `centerOption="CenterOfBoundBox"` and positioned with
`pushPoints`, which takes absolute coordinates on that workplane.
"""

from __future__ import annotations

import cadquery as cq

from tolcad.gen.layout import (
    feature_positions_mm, feature_radii_mm, minimum_plate_size_mm,
)
from tolcad.gen.spec import AssemblySpec

# Slack when comparing the spec's plate size against the derived minimum, so
# float round-trips through JSON cannot trip the guard.
_SIZE_EPS_MM = 1e-6


def _drill(part: cq.Workplane, ops: list[tuple[float, float, float | None]]) -> cq.Workplane:
    """Cut holes at absolute x positions on the plate's top face.

    ops entries are (x_mm, diameter_mm, depth_mm | None); None means through.
    Operations are grouped by (diameter, depth) so each distinct feature size
    is a single pushPoints call, and the grouping is insertion-ordered so the
    result stays deterministic for a given spec.
    """
    grouped: dict[tuple[float, float | None], list[tuple[float, float]]] = {}
    for x, diameter, depth in ops:
        grouped.setdefault((diameter, depth), []).append((x, 0.0))

    for (diameter, depth), points in grouped.items():
        plane = (
            part.faces(">Z")
            .workplane(centerOption="CenterOfBoundBox")
            .pushPoints(points)
        )
        part = plane.hole(diameter) if depth is None else plane.hole(diameter, depth=depth)
    return part


def build_assembly(spec: AssemblySpec) -> cq.Assembly:
    """Build a two-plate assembly with one feature per mate."""
    thickness = spec.plate_thickness_mm
    radii = feature_radii_mm(spec.mates)
    xs = feature_positions_mm(radii)

    required = minimum_plate_size_mm(radii)
    if spec.plate_size_mm + _SIZE_EPS_MM < required:
        raise ValueError(
            f"plate_size_mm {spec.plate_size_mm} is too small for these features; "
            f"needs at least {required} mm. Use tolcad.gen.layout."
            f"plate_size_for_mates to size the plate."
        )
    size = spec.plate_size_mm

    ops_a: list[tuple[float, float, float | None]] = []
    ops_b: list[tuple[float, float, float | None]] = []
    for x, mate in zip(xs, spec.mates):
        if mate.kind == "iso_fit":
            # A blind bore in the lower plate; the shaft is not modelled.
            ops_b.append((x, mate.nominal_mm, thickness / 2.0))
            continue
        ops_a.append((x, mate.hole_a["nominal"], None))
        ops_b.append((x, mate.hole_b["nominal"], None))

    part_a = _drill(cq.Workplane("XY").box(size, size, thickness), ops_a)
    part_b = _drill(cq.Workplane("XY").box(size, size, thickness), ops_b)

    asm = cq.Assembly(name=f"assembly_seed{spec.seed}_d{spec.difficulty}")
    asm.add(part_a, name="part_a", loc=cq.Location(cq.Vector(0, 0, thickness)))
    asm.add(part_b, name="part_b", loc=cq.Location(cq.Vector(0, 0, 0)))
    return asm
