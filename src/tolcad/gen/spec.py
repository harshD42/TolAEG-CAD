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

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> AssemblySpec:
        raw = json.loads(text)
        mates = [MateSpec(**m) for m in raw.pop("mates")]
        return cls(mates=mates, **raw)
