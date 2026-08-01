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
    # Tier 2 (iso_fit) is a Monte Carlo estimate, so its verdict depends on the
    # sampling seed. H7/h6 is line-to-line at MMC and genuinely flips label
    # across seeds, so leaving the seed implicit made the published label an
    # accident of tolcad.checker's fallback default. (H7/h6 is no longer
    # SAMPLED -- it left features.SUPPORTED_FITS in commit 422c21f for exactly
    # that reason -- but iso286.fit_from_designation still supports it, so a
    # hand-written spec can still name it, and the general point holds for any
    # fit whose worst-case clearance lands near zero.) CLAUDE.md requires Tier 2
    # to always report a seed; carrying it here is what puts it in the sidecar
    # JSON a reproducer actually reads, not just in Verdict.detail.
    # Defaults mirror tolcad.checker's fallbacks; the sampler always sets them.
    mc_seed: int = 0
    mc_n: int = 100_000
    # ASME Y14.5 Appendix B-4 -- the formula y14_5.fastener_assembles implements
    # for the fixed case -- is titled "...When Projected Tolerance Zone Is Used"
    # and assumes exactly that. y14_5.py states the precondition outright: apply
    # B-4 without a projected zone and the margin is OPTIMISTIC, i.e. unsafe.
    # B-5 covers the non-projected case with a (1 + 2P/D) multiplier on T2, and
    # tolcad does NOT implement it. Recording the projection here is how the
    # published schema states the condition its verdict is valid under.
    # The projection is the thickness of the part the fastener crosses before
    # reaching the tapped feature. Required and positive for fixed_fastener;
    # None for every other kind, since no other formula has a projection term.
    projected_zone_mm: float | None = None

    def __post_init__(self) -> None:
        if self.mc_n <= 0:
            raise ValueError(f"mc_n must be positive, got {self.mc_n}")
        if self.kind not in VALID_KINDS:
            raise ValueError(
                f"unknown mate kind {self.kind!r}; have {sorted(VALID_KINDS)}"
            )
        if self.kind != "fixed_fastener" and self.projected_zone_mm is not None:
            raise ValueError(
                f"projected_zone_mm applies only to fixed_fastener (Y14.5 B-4); "
                f"{self.kind} carries no projection term, got "
                f"{self.projected_zone_mm}"
            )
        if self.kind == "iso_fit":
            if not self.designation:
                raise ValueError("iso_fit mate requires a designation such as 'H7/g6'")
        elif self.kind == "virtual_condition":
            if self.fastener is None:
                raise ValueError("virtual_condition mate requires a fastener")
            if self.hole_a is None:
                raise ValueError("virtual_condition mate requires hole_a")
        else:  # floating_fastener or fixed_fastener
            if self.fastener is None:
                raise ValueError(f"{self.kind} mate requires a fastener")
            if self.hole_a is None:
                raise ValueError(f"{self.kind} mate requires hole_a")
            if self.hole_b is None:
                raise ValueError(f"{self.kind} mate requires hole_b")
            if self.kind == "fixed_fastener" and not (
                self.projected_zone_mm is not None and self.projected_zone_mm > 0.0
            ):
                raise ValueError(
                    "fixed_fastener requires a positive projected_zone_mm: "
                    "y14_5 implements ASME Y14.5 B-4, which assumes a projected "
                    "tolerance zone, and is optimistic without one. Got "
                    f"{self.projected_zone_mm}"
                )

    def to_check_dict(self) -> dict:
        """Return the dict accepted by tolcad.checker.check.

        Injects position_tol from dedicated fields into the hole/fastener dicts,
        making them the single source of truth and preventing silent divergence.
        """
        if self.kind == "iso_fit":
            return {
                "type": "iso_fit",
                "nominal": self.nominal_mm,
                "designation": self.designation,
                # Explicit, never inherited from the checker's fallback.
                "seed": self.mc_seed,
                "n": self.mc_n,
            }

        # For all Tier 1 mates, inject position_tol into the hole/fastener dicts.
        # position_tol_a and position_tol_b are the single source of truth.
        def inject_position_tol(feature_dict: dict, position_tol: float) -> dict:
            """Create a new dict with position_tol injected."""
            result = dict(feature_dict)
            result["position_tol"] = position_tol
            return result

        if self.kind == "virtual_condition":
            return {
                "type": "virtual_condition",
                "pin": inject_position_tol(self.fastener, self.position_tol_a),
                "hole": inject_position_tol(self.hole_a, self.position_tol_a),
            }

        # floating_fastener or fixed_fastener
        return {
            "type": self.kind,
            "hole_a": inject_position_tol(self.hole_a, self.position_tol_a),
            "hole_b": inject_position_tol(self.hole_b, self.position_tol_b),
            "fastener": inject_position_tol(self.fastener, self.position_tol_a),
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
        # CROSS-OBJECT INVARIANT, and the one that carries the safety meaning.
        # MateSpec can only check that a fixed fastener HAS a projection;
        # whether the projection is long enough is a fact about the plate the
        # fastener crosses, which only the assembly knows.
        #
        # ASME Y14.5 B-4 assumes the tapped hole's tolerance zone is projected
        # through the full thickness of the part the fastener passes through
        # before it reaches the tapped feature. build.py drills part_a to
        # spec.plate_thickness_mm, so a projection shorter than that leaves
        # part of the joint outside the zone -- exactly the under-projected
        # condition y14_5.fixed_fastener_tolerance calls OPTIMISTIC, i.e.
        # unsafe. B-5 is the formula for that case and tolcad does not
        # implement it, so an assembly whose verdict B-4 cannot support must
        # not be constructible at all.
        for index, mate in enumerate(self.mates):
            if mate.kind != "fixed_fastener":
                continue
            if mate.projected_zone_mm < self.plate_thickness_mm:
                raise ValueError(
                    f"mate {index}: projected_zone_mm "
                    f"{mate.projected_zone_mm} is shorter than "
                    f"plate_thickness_mm {self.plate_thickness_mm}. ASME Y14.5 "
                    f"B-4 -- the formula y14_5.fastener_assembles applies to a "
                    f"fixed fastener -- assumes the zone is projected through "
                    f"the whole part the fastener crosses. Under-projected, "
                    f"its margin is OPTIMISTIC (unsafe); the non-projected "
                    f"case is B-5, which tolcad does not implement."
                )

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> AssemblySpec:
        raw = json.loads(text)
        mates = [MateSpec(**m) for m in raw.pop("mates")]
        return cls(mates=mates, **raw)
