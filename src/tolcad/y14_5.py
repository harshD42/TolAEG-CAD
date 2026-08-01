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

    Source: ASME Y14.5-2018, Nonmandatory Appendix B, section B-3 "Floating Fastener
    Case". Verified against the primary text 2026-08-01. Symbols per B-2.1.
    Reproduces B-3's worked example exactly (F=6, H=6.44 -> T=0.44 per part).
    """
    _check_fastener_pair(hole, fastener)
    return hole.mmc - fastener.mmc


def fixed_fastener_tolerance(hole: FeatureOfSize, fastener: FeatureOfSize) -> float:
    """Position tolerance available to each part, fixed fastener condition.

    T = (H - F) / 2. The available clearance is split between the two parts
    because the fastener cannot shift in the part that constrains it.

    ASSUMES A PROJECTED TOLERANCE ZONE. This is load-bearing, not a footnote.
    B-4 is titled "...When Projected Tolerance Zone Is Used" and warns the formula
    does not give enough clearance when tapped or tight-fitting holes are out of
    square. B-5 covers that case instead:
        H = F + T1 + T2 * (1 + 2P/D)
    with P the maximum projection of the fastener and D the minimum depth of
    engagement. The multiplier applies to T2, the tapped hole's tolerance -- NOT to
    T1. This module implements B-4 only, so applying it to a drawing without a
    projected zone is OPTIMISTIC (unsafe); the generator must emit projected zones.

    Source: ASME Y14.5-2018, Nonmandatory Appendix B, section B-4 "Fixed Fastener
    Case When Projected Tolerance Zone Is Used". Verified against the primary text
    2026-08-01. Reproduces B-4's worked examples exactly (F=6, H=6.44 -> T=0.22 per
    part; and the unequal split 2T=0.44 -> T1=0.18, T2=0.26).
    """
    _check_fastener_pair(hole, fastener)
    return (hole.mmc - fastener.mmc) / 2.0


def fastener_assembles(
    hole_a: FeatureOfSize,
    hole_b: FeatureOfSize,
    fastener: FeatureOfSize,
    condition: str,
) -> Verdict:
    """Check a two-part fastened joint against ASME Y14.5-2018 Nonmandatory Appendix B.

    SOURCE: ASME Y14.5-2018, Nonmandatory Appendix B, "Formulas for Positional
    Tolerancing", sections B-3 (floating) and B-4 (fixed). Symbols follow B-2.1:
    H = minimum diameter of clearance hole (MMC limit); F = maximum diameter of
    fastener (MMC limit); T = positional tolerance diameter.

    - FLOATING (B-3) — fastener passes clearance holes in BOTH parts, e.g. bolt
      and nut. The formula is H = F + T, equivalently T = H - F. For unequal
      parts B-3 is explicit that it is applied PER PART, not pooled: "Any number
      of parts with different hole sizes and positional tolerances may be mated,
      provided the formula H = F + T or T = H - F is applied to each part
      individually." Hence:
          margin = min(H_a - F - T_a,  H_b - F - T_b)
      Symmetric in (H_a, T_a) <-> (H_b, T_b), since min is commutative.

      WHY PER-PART AND NOT A POOLED DISC-INTERSECTION CONDITION. A pooled
      condition, (H_a - F) + (H_b - F) >= T_a + T_b, is the correct answer to a
      different question: whether one specific pair of parts can physically be
      assembled. It is strictly more permissive. Y14.5 governs drawing
      conformance and interchangeability — each part must be acceptable against
      its own drawing without reference to the actual deviations of the mating
      part — so the per-part rule is the standards-conformant one and is what
      this module implements. An earlier version of this code used the pooled
      form and was wrong for that reason, not for a geometric one.

    - FIXED (B-4) — the fastener is restrained by one part (screw in a tapped
      hole, or a stud). hole_a is the CLEARANCE hole; hole_b is the FIXED
      FEATURE. For equal tolerances B-4 gives H = F + 2T, i.e. T = (H - F)/2.
      B-4 then generalises to unequal tolerances explicitly: "The general
      formula for the fixed fastener case where two mating parts have different
      positional tolerances is H = F + T1 + T2." Hence:
          margin = (H_a - F) - (T_a + T_b)
      H_b does not appear: the fixed feature's own MMC is irrelevant to whether
      the fastener clears hole_a. Not symmetric under a full (H_a, T_a) <->
      (H_b, T_b) swap, but symmetric under swapping T_a <-> T_b alone.

    Both reduce to the classic single-hole forms when the parts are equal
    (H_a = H_b = H, T_a = T_b = T): floating -> T = H - F; fixed -> the two
    tolerances sum to H - F, i.e. T = (H - F)/2 each.

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
      - The "fixed" formula is B-4, which is titled "FIXED FASTENER CASE WHEN
        PROJECTED TOLERANCE ZONE IS USED" and assumes exactly that. B-4 warns
        that "The preceding formulas do not provide sufficient clearance ...
        when threaded holes or holes for tight-fitting members, such as dowels,
        are out of square", and B-5 gives the alternative for that case:
            H = F + T1 + T2 * (1 + 2P/D)
        where P is the maximum projection of the fastener and D the minimum
        depth of engagement. Note the multiplier lands on T2, the tapped or
        tight-fitting hole's tolerance — not on T1. This module implements B-4
        only, so applying it to a drawing WITHOUT a projected tolerance zone is
        optimistic (unsafe). The procedural generator must emit projected zones
        explicitly.
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
    if condition == "floating":
        # B-3: "applied to each part individually" — the joint is limited by
        # whichever part has the least slack of its own, never by their sum.
        clearance_b = hole_b.mmc - fastener.mmc
        margin_a = clearance_a - hole_a.position_tol
        margin_b = clearance_b - hole_b.position_tol
        margin = min(margin_a, margin_b)
    else:
        # B-4: H = F + T1 + T2, so both tolerances draw on hole_a's clearance.
        clearance_b = None
        margin_a = margin_b = None
        margin = clearance_a - (hole_a.position_tol + hole_b.position_tol)

    return Verdict(
        assembles=margin >= -EPS,
        margin=margin,
        method=f"{condition}_fastener",
        detail={
            "margin_unit": "diametral_mm",
            "radial_slack": margin / 2.0,
            "clearance_a": clearance_a,
            "clearance_b": clearance_b,
            "margin_a": margin_a,
            "margin_b": margin_b,
            "governing_part": (
                None
                if condition == "fixed"
                else ("hole_a" if margin_a <= margin_b else "hole_b")
            ),
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
