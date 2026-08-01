"""Top-level dispatch over mate types.

Mates arrive as plain dicts so the generator can emit JSON without importing tolcad.
"""

from __future__ import annotations

from tolcad.iso286 import fit_from_designation
from tolcad.montecarlo import clearance_yield
from tolcad.types import FeatureOfSize, FeatureType, Verdict
from tolcad.y14_5 import fastener_assembles, vc_assembles


def _feature(spec: dict, feature_type: FeatureType) -> FeatureOfSize:
    return FeatureOfSize(
        nominal=spec["nominal"],
        lower_dev=spec["lower_dev"],
        upper_dev=spec["upper_dev"],
        feature_type=feature_type,
        position_tol=spec.get("position_tol", 0.0),
    )


def check(mate: dict) -> Verdict:
    """Evaluate a single mate specification."""
    if "type" not in mate:
        raise ValueError("mate specification requires a 'type' key")

    kind = mate["type"]

    if kind == "virtual_condition":
        return vc_assembles(
            _feature(mate["pin"], FeatureType.EXTERNAL),
            _feature(mate["hole"], FeatureType.INTERNAL),
        )

    if kind in ("floating_fastener", "fixed_fastener"):
        return fastener_assembles(
            _feature(mate["hole_a"], FeatureType.INTERNAL),
            _feature(mate["hole_b"], FeatureType.INTERNAL),
            _feature(mate["fastener"], FeatureType.EXTERNAL),
            condition=kind.replace("_fastener", ""),
        )

    if kind == "iso_fit":
        hole, shaft = fit_from_designation(mate["nominal"], mate["designation"])
        return clearance_yield(
            hole,
            shaft,
            n=mate.get("n", 100_000),
            seed=mate.get("seed", 0),
            distribution=mate.get("distribution", "normal"),
        )

    raise ValueError(f"unknown mate type {kind!r}")
