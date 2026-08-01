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


def _check_fastener_pair(hole: FeatureOfSize, fastener: FeatureOfSize) -> None:
    if hole.feature_type is not FeatureType.INTERNAL:
        raise ValueError("hole must be an internal feature")
    if fastener.feature_type is not FeatureType.EXTERNAL:
        raise ValueError("fastener must be an external feature")


def floating_fastener_tolerance(
    hole: FeatureOfSize, fastener: FeatureOfSize
) -> float:
    """Position tolerance available to each part, floating fastener condition.

    T = H - F, where H is hole MMC and F is fastener MMC.
    Source: ASME Y14.5 floating fastener formula. CITATION PENDING HUMAN VERIFICATION.
    """
    _check_fastener_pair(hole, fastener)
    return hole.mmc - fastener.mmc


def fixed_fastener_tolerance(hole: FeatureOfSize, fastener: FeatureOfSize) -> float:
    """Position tolerance available to each part, fixed fastener condition.

    T = (H - F) / 2. The available clearance is split between the two parts
    because the fastener cannot shift in the part that constrains it.
    Assumes a projected tolerance zone.
    Source: ASME Y14.5 fixed fastener formula. CITATION PENDING HUMAN VERIFICATION.
    """
    _check_fastener_pair(hole, fastener)
    return (hole.mmc - fastener.mmc) / 2.0


def fastener_assembles(
    hole_a: FeatureOfSize,
    hole_b: FeatureOfSize,
    fastener: FeatureOfSize,
    condition: str,
) -> Verdict:
    """Check a two-part fastened joint against the Y14.5 allowable tolerance."""
    if hole_b.feature_type is not FeatureType.INTERNAL:
        raise ValueError("hole_b must be an internal feature")
    if condition == "floating":
        allowable = floating_fastener_tolerance(hole_a, fastener)
    elif condition == "fixed":
        allowable = fixed_fastener_tolerance(hole_a, fastener)
    else:
        raise ValueError(f"condition must be 'floating' or 'fixed', got {condition!r}")

    worst = max(hole_a.position_tol, hole_b.position_tol)
    margin = allowable - worst

    return Verdict(
        assembles=margin >= -EPS,
        margin=margin,
        method=f"{condition}_fastener",
        detail={
            "allowable_tol": allowable,
            "worst_applied_tol": worst,
            "hole_mmc": hole_a.mmc,
            "fastener_mmc": fastener.mmc,
        },
    )
