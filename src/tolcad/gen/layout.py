"""Where features sit on a generated plate, and how big the plate must be.

No CAD dependency, deliberately: `sampler.py` uses it to size the plate it
records on the spec, and `build.py` uses it to place the features it drills.
Both derive from the same arithmetic, so the exported STEP and its sidecar can
never disagree about the layout.

Everything here is in millimetres, stored as float.

WHY THIS EXISTS. The first version hardcoded a 12 mm pitch and a 40 mm plate.
The largest clearance hole in `features.py` is Ø14.5 (M12 loose, radius 7.25),
so two adjacent loose M12 features merged into one slot and the outermost one
ran off the plate edge. Sizing is now derived from the sampled radii, so it
cannot be outgrown by a change to the feature tables.

MARGINS AND WHY THESE VALUES. The sampler's largest allowable position
tolerance is (14.5 - 12.0) = 2.5 mm diametral, and the difficulty ladder
applies at most 1.34x of it (sampler._TOL_FRACTION_RANGE[4] hi), so the applied
tolerance tops out at 2.5 * 1.34 = 3.35 mm diametral and a feature's axis can
sit up to 3.35 / 2 = 1.675 mm off nominal in any direction. Hole size can also
grow by upper_dev -- the clearance hole's own ISO 273 series grade at its own
diameter (via iso286.py), which for the widest case, Ø14.5 M12 loose, is IT14
in the >10-18 mm band: +0.43 mm diameter, +0.215 mm radius. One feature's edge
can therefore reach 1.675 + 0.215 = 1.890 mm past where nominal geometry puts
it.

Headroom below is quoted as excess over the REQUIREMENT, (constant - required)
/ required, for both margins. (Excess over the constant is a different, smaller
number -- 5.5% for the wall -- and mixing the two is how the figure in this
docstring was wrong before.)

  _MIN_WALL_MM = 4.0   Two neighbours leaning toward each other consume at
                       worst 1.675 + 1.675 + 0.215 + 0.215 = 3.78 mm, so 4.0 mm
                       of nominal material between them still leaves a
                       ligament: (4.0 - 3.78) / 3.78 = 5.8% headroom.
  _EDGE_MARGIN_MM = 5.0  A single feature leaning at an edge consumes at worst
                       1.675 + 0.215 = 1.890 mm, so 5.0 mm gives
                       (5.0 - 1.890) / 1.890 = 165% headroom.

Ø14.5 (M12 loose) IS NOT THE WIDEST FEATURE, and that is fine. An iso_fit mate
is laid out at its own nominal, which the sampler draws up to Ø25, so Ø25 is
the widest thing on a plate. It does not enter the derivation above because it
carries position_tol 0.0 and an IT7-class band (~0.021 mm at 25 mm, ~0.01 mm on
the radius), three orders below the clearance-hole case. The binding case for
margin sizing is the widest feature that carries a POSITION TOLERANCE, and that
is the M12 loose clearance hole.

Both are nominal-geometry margins: the reference STEP is drilled at nominal
positions and nominal sizes. The tolerance zones above are what the margins are
sized to survive, not what the geometry models.

tests/gen/test_layout.py re-derives the 3.78 / 1.890 requirement from
features.clearance_hole_for (ISO 273 series grade included) and
sampler._TOL_FRACTION_RANGE at test time, so raising the ladder or widening the
clearance table cannot leave these two constants quietly too small. A second,
cruder pair of literal floors in that file (_LITERAL_WALL_FLOOR_MM = 3.8,
_LITERAL_EDGE_FLOOR_MM = 1.9 -- the derived 3.78 / 1.890 rounded UP, so they
stay conservative rather than merely equal) is checked against the same
derivation, BOTH of them, so neither can drift stale the way the wall one did
when clearance holes moved onto ISO 273.
"""

from __future__ import annotations

from collections.abc import Sequence

_MIN_WALL_MM = 4.0
_EDGE_MARGIN_MM = 5.0

# Floors, so that a one-feature Ø3.2 assembly is still a recognisable plate
# rather than a chip. 12.0 mm was the original hardcoded pitch; 40.0 mm was the
# original hardcoded plate. Keeping them as lower bounds means this change can
# only ever make geometry roomier, never tighter.
_MIN_PITCH_MM = 12.0
_MIN_PLATE_SIZE_MM = 40.0

# Plate sizes and pitches are rounded so the sidecar JSON carries tidy numbers.
# 4 dp = 0.1 um, five orders of magnitude below the smallest margin above.
_ROUND_DP = 4


def feature_radii_mm(mates: Sequence) -> list[float]:
    """Radius of the largest feature each mate contributes, one entry per mate.

    build.py drills hole_a into part_a and hole_b into part_b at the same x, so
    the layout has to make room for whichever is bigger. An iso_fit mate is a
    single blind bore at its nominal diameter.
    """
    radii: list[float] = []
    for mate in mates:
        if mate.kind == "iso_fit":
            radii.append(mate.nominal_mm / 2.0)
            continue
        diameters = [
            hole["nominal"] for hole in (mate.hole_a, mate.hole_b) if hole is not None
        ]
        if not diameters:
            raise ValueError(f"{mate.kind} mate has no hole to lay out")
        radii.append(max(diameters) / 2.0)
    return radii


def feature_pitch_mm(radii: Sequence[float]) -> float:
    """Centre-to-centre spacing that keeps at least _MIN_WALL_MM between neighbours."""
    if len(radii) < 2:
        return _MIN_PITCH_MM
    widest_pair = max(radii[i] + radii[i + 1] for i in range(len(radii) - 1))
    return round(max(widest_pair + _MIN_WALL_MM, _MIN_PITCH_MM), _ROUND_DP)


def feature_positions_mm(radii: Sequence[float]) -> list[float]:
    """Feature x positions, evenly pitched and centred on the plate origin."""
    pitch = feature_pitch_mm(radii)
    span = pitch * (len(radii) - 1)
    return [round(-span / 2.0 + i * pitch, _ROUND_DP) for i in range(len(radii))]


def minimum_plate_size_mm(radii: Sequence[float]) -> float:
    """Smallest square plate that holds every feature with _EDGE_MARGIN_MM to spare."""
    positions = feature_positions_mm(radii)
    reach = max(abs(x) + r for x, r in zip(positions, radii))
    return round(max(2.0 * (reach + _EDGE_MARGIN_MM), _MIN_PLATE_SIZE_MM), _ROUND_DP)


def plate_size_for_mates(mates: Sequence) -> float:
    """Convenience wrapper: the plate size an assembly of these mates needs."""
    return minimum_plate_size_mm(feature_radii_mm(mates))
