"""Tier 1: closed-form ASME Y14.5 assembly conditions.

These are exact arithmetic identities from the standard, not simulations.
A failure here is unambiguously a failure of the input geometry.
"""

from __future__ import annotations

from tolcad.types import EPS, FeatureOfSize, FeatureType, Verdict


def virtual_condition(feature: FeatureOfSize) -> float:
    """Worst-case boundary of a feature, per ASME Y14.5.

    External: MMC + position tolerance (effectively the largest it can be).
    Internal: MMC - position tolerance (effectively the smallest it can be).
    """
    if feature.feature_type is FeatureType.EXTERNAL:
        return feature.mmc + feature.position_tol
    return feature.mmc - feature.position_tol


def vc_assembles(pin: FeatureOfSize, hole: FeatureOfSize) -> Verdict:
    """Check a single pin-in-hole pair by virtual condition.

    Assembly is guaranteed iff VC_pin <= VC_hole.
    """
    if pin.feature_type is not FeatureType.EXTERNAL:
        raise ValueError("pin must be an external feature")
    if hole.feature_type is not FeatureType.INTERNAL:
        raise ValueError("hole must be an internal feature")

    vc_pin = virtual_condition(pin)
    vc_hole = virtual_condition(hole)
    margin = vc_hole - vc_pin

    return Verdict(
        assembles=margin >= -EPS,
        margin=margin,
        method="virtual_condition",
        detail={"vc_pin": vc_pin, "vc_hole": vc_hole},
    )
