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
