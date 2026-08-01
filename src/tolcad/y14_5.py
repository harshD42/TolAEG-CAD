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

    CROSS-VERIFIED (secondary sources, 2026-08-01): multiple independent published
    references give the floating fastener formula as H = F + T, attributed to
    ASME Y14.5-1994 Appendix B (section B3) - algebraically identical to T = H - F.
    Source: ASME Y14.5 floating fastener formula. CITATION PENDING HUMAN VERIFICATION.
    (Cross-verification confirms the formula as widely republished; it does not
    confirm it against the standard itself, which is paywalled.)
    """
    _check_fastener_pair(hole, fastener)
    return hole.mmc - fastener.mmc


def fixed_fastener_tolerance(hole: FeatureOfSize, fastener: FeatureOfSize) -> float:
    """Position tolerance available to each part, fixed fastener condition.

    T = (H - F) / 2. The available clearance is split between the two parts
    because the fastener cannot shift in the part that constrains it.

    ASSUMES A PROJECTED TOLERANCE ZONE. This is load-bearing, not a footnote.
    Cross-verified 2026-08-01: published references give the fixed fastener
    condition with unequal tolerances as
        projected zone:      H = F + T1 + T2          <- what this module implements
        NOT projected:       H = F + T1 * (1 + 2P/D)  <- a different, larger formula
    where P is the maximum thickness of the part carrying the clearance hole and D
    the minimum thread depth (or thickness of the part restraining the fastener).
    Those same references note the NON-projected case is the more common one on real
    drawings. Because this project's procedural generator controls the tolerance
    schema, it must emit projected zones explicitly; consuming a real-world drawing
    that lacks one and applying this formula would be OPTIMISTIC (unsafe).

    Source: ASME Y14.5 fixed fastener formula. CITATION PENDING HUMAN VERIFICATION.
    (Cross-verification confirms the formula as widely republished; it does not
    confirm it against the standard itself, which is paywalled.)
    """
    _check_fastener_pair(hole, fastener)
    return (hole.mmc - fastener.mmc) / 2.0


def fastener_assembles(
    hole_a: FeatureOfSize,
    hole_b: FeatureOfSize,
    fastener: FeatureOfSize,
    condition: str,
) -> Verdict:
    """Check a two-part fastened joint by pooling clearance against pooled position error.

    MODEL. Let H_a, H_b be the two holes' MMC diameters, F the fastener's MMC
    diameter, and T_a, T_b the two parts' diametral position tolerances. A
    fastener of diameter F passes through hole i iff its axis lies within
    radius (H_i - F)/2 of that hole's axis. Worst-case separation between the
    two hole axes is T_a/2 + T_b/2.

    - FLOATING (fastener passes clearance holes in BOTH parts and may
      translate freely to accommodate the misalignment): the two permitted
      discs, one per part, must intersect:
          margin = (H_a - F) + (H_b - F) - (T_a + T_b)
      This is symmetric in (H_a, T_a) <-> (H_b, T_b): swapping which part is
      "a" and which is "b" cannot change the verdict.

    - FIXED (the fastener is constrained by one part — a tapped hole or a
      press-fit pin — so it cannot float to split the misalignment). hole_a
      is the CLEARANCE hole the fastener must pass through; hole_b is the
      FIXED FEATURE that locates the fastener and holds it on-axis:
          margin = (H_a - F) - (T_a + T_b)
      H_b does not appear: the fixed feature's own MMC is irrelevant to
      whether the fastener clears hole_a. This is NOT symmetric under a full
      (H_a, T_a) <-> (H_b, T_b) swap (the size term only ever involves H_a),
      but it IS symmetric under swapping T_a <-> T_b alone, since both
      tolerances enter only as a sum.

    Both forms reduce to the classic Y14.5 single-hole formulas in the
    symmetric case (H_a = H_b = H, T_a = T_b = T, i.e. equal parts):
    floating -> T = H - F per part, fixed -> T = (H - F) / 2 per part.
    (Floating: 2(H-F) - 2T = 0 -> T = H - F. Fixed: (H-F) - 2T = 0 ->
    T = (H-F) / 2.)

    Assembles iff margin >= -EPS.

    UNITS: margin is DIAMETRAL (a diameter-of-clearance quantity), matching
    H, F and T above. The physical radial slack between the axes is
    margin / 2; this is also recorded in `detail["radial_slack"]`. Treating
    margin as radial anywhere silently halves (or doubles) the actual slack
    and is exactly the failure class that produced an earlier, wrong version
    of this model — do not do it.

    VALIDATION: hole_a must always be INTERNAL (it is always a clearance
    hole the fastener passes through). For "floating", hole_b must also be
    INTERNAL. For "fixed", hole_b may be INTERNAL (a tapped hole) or
    EXTERNAL (a press-fit locating pin); its feature_type is not otherwise
    constrained because its MMC never enters the fixed formula.

    A hole the fastener must physically pass through cannot be smaller than
    the fastener at MMC: that would make its permitted-axis disc have
    negative radius, and the algebra above does not detect that on its own
    (e.g. H_a=7.9, H_b=9.0, T=0, F=8.0 would otherwise evaluate to margin
    +0.9, "assembles", despite the fastener not fitting hole_a at all). This
    is checked explicitly and raises ValueError: for "floating", both hole_a
    and hole_b must be >= F at MMC; for "fixed", only hole_a must be (hole_b
    is not a clearance hole in the fixed case, so its size is not checked
    here).

    MMC BONUS IS IGNORED, AND THIS IS EXACT, NOT MERELY CONSERVATIVE. Let
    S_a, S_b be the parts' actual (as-produced) sizes, each granting bonus
    tolerance |S_i - H_i| under an MMC modifier. Substituting size-dependent
    clearance (S_i - F) and size-dependent applied tolerance (T_i + |S_i -
    H_i|) into the floating formula:
        (S_a - F) + (S_b - F) - [(T_a + (S_a - H_a)) + (T_b + (S_b - H_b))]
      = (H_a - F) + (H_b - F) - T_a - T_b
    the S_a and S_b terms cancel exactly: the virtual condition H - T is
    size-invariant, so evaluating at MMC (bonus = 0) already gives the exact
    worst case, not merely a safe bound. The one corner where this is
    UNSAFE: if a fixed feature distinct from the fastener shank (e.g. a
    separate locating pin press-fit into hole_b) carried its own MMC
    modifier, its bonus would inflate the applicable T_b with no offsetting
    size term on the hole_a side, and the cancellation above no longer
    holds. This model therefore assumes RFS (no bonus) on the fixed feature
    in the "fixed" condition.

    SCOPE LIMITS (each one makes the computed margin optimistic if violated):
      - The "fixed" formula assumes T_b is a PROJECTED tolerance zone
        (Y14.5 (P) modifier) at least as long as hole_a's part thickness.
        Without that, angular error of the fixed feature over that
        thickness is unmodelled and the fixed margin overstates clearance.
      - Datum shift between the two parts' datum reference frames is
        unmodelled; the derivation assumes the two DRFs coincide exactly.
      - Composite position tolerance, pattern-level (multi-fastener)
        analysis, hole tilt beyond what a projected zone captures, thread
        class, and fastener bending are all out of scope.
    """
    if condition not in ("floating", "fixed"):
        raise ValueError(f"condition must be 'floating' or 'fixed', got {condition!r}")

    if hole_a.feature_type is not FeatureType.INTERNAL:
        raise ValueError("hole_a must be an internal feature")
    if condition == "floating" and hole_b.feature_type is not FeatureType.INTERNAL:
        raise ValueError("hole_b must be an internal feature")
    if fastener.feature_type is not FeatureType.EXTERNAL:
        raise ValueError("fastener must be an external feature")

    if hole_a.mmc < fastener.mmc:
        raise ValueError(
            f"hole_a MMC {hole_a.mmc} is smaller than fastener MMC "
            f"{fastener.mmc}; the fastener cannot pass through hole_a"
        )
    if condition == "floating" and hole_b.mmc < fastener.mmc:
        raise ValueError(
            f"hole_b MMC {hole_b.mmc} is smaller than fastener MMC "
            f"{fastener.mmc}; the fastener cannot pass through hole_b"
        )

    clearance_a = hole_a.mmc - fastener.mmc
    pooled_tol = hole_a.position_tol + hole_b.position_tol
    if condition == "floating":
        clearance_b = hole_b.mmc - fastener.mmc
        margin = clearance_a + clearance_b - pooled_tol
    else:
        clearance_b = None
        margin = clearance_a - pooled_tol

    return Verdict(
        assembles=margin >= -EPS,
        margin=margin,
        method=f"{condition}_fastener",
        detail={
            "margin_unit": "diametral_mm",
            "radial_slack": margin / 2.0,
            "clearance_a": clearance_a,
            "clearance_b": clearance_b,
            "position_tol_a": hole_a.position_tol,
            "position_tol_b": hole_b.position_tol,
            "hole_a_mmc": hole_a.mmc,
            "hole_b_mmc": hole_b.mmc,
            "fastener_mmc": fastener.mmc,
        },
    )


def bonus_tolerance(feature: FeatureOfSize, actual_size: float) -> float:
    """Extra position tolerance earned by departing from MMC, under the MMC modifier.

    Bonus equals the departure from MMC toward LMC. Zero at MMC, maximal at LMC.
    """
    if not (feature.min_size - EPS <= actual_size <= feature.max_size + EPS):
        raise ValueError(
            f"actual_size {actual_size} outside limits "
            f"[{feature.min_size}, {feature.max_size}]"
        )
    return abs(actual_size - feature.mmc)
