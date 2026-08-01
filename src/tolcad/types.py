"""Core domain types. All dimensions in millimetres."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

EPS = 1e-9


class FeatureType(Enum):
    """Whether a feature of size removes or adds material."""

    INTERNAL = "internal"  # hole, slot, bore
    EXTERNAL = "external"  # pin, shaft, boss


@dataclass(frozen=True)
class FeatureOfSize:
    """A toleranced feature of size, per ASME Y14.5.

    Deviations are signed offsets from nominal, in mm.
    A Ø8.5 +0.2/-0.0 hole is FeatureOfSize(8.5, 0.0, 0.2, INTERNAL).
    """

    nominal: float
    lower_dev: float
    upper_dev: float
    feature_type: FeatureType
    position_tol: float = 0.0

    def __post_init__(self) -> None:
        if self.upper_dev < self.lower_dev:
            raise ValueError(
                f"upper_dev {self.upper_dev} below lower_dev {self.lower_dev}"
            )
        if self.position_tol < 0.0:
            raise ValueError(f"position_tol must be non-negative, got {self.position_tol}")

    @property
    def max_size(self) -> float:
        return self.nominal + self.upper_dev

    @property
    def min_size(self) -> float:
        return self.nominal + self.lower_dev

    @property
    def mmc(self) -> float:
        """Maximum material condition: most material present."""
        if self.feature_type is FeatureType.INTERNAL:
            return self.min_size
        return self.max_size

    @property
    def lmc(self) -> float:
        """Least material condition: least material present."""
        if self.feature_type is FeatureType.INTERNAL:
            return self.max_size
        return self.min_size


@dataclass(frozen=True)
class Verdict:
    """Result of a functional check.

    margin's unit depends on the tier that produced it:
    - Tier 1 (virtual_condition, floating_fastener, fixed_fastener): margin is
      in mm of slack. margin > 0 means assembly is guaranteed exactly.
    - Tier 2 (iso_fit / Monte Carlo): margin is a clearance YIELD in [0, 1],
      the fraction of sampled part pairs that clear. It is NOT millimetres.
      assembles is True only when margin == 1.0 (full yield).
    These two units are not comparable; code that consumes `margin` across
    tiers (e.g. thresholding against an epsilon in mm) must not mix them.
    """

    assembles: bool
    margin: float
    method: str
    detail: dict = field(default_factory=dict)
