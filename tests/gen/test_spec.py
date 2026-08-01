import pytest
from tolcad.gen.spec import AssemblySpec, MateSpec
from tolcad.checker import check


def _floating_mate() -> MateSpec:
    return MateSpec(
        kind="floating_fastener",
        nominal_mm=8.0,
        hole_a={"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.3},
        hole_b={"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.3},
        fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
        designation=None,
        position_tol_a=0.3,
        position_tol_b=0.3,
    )


def test_mate_spec_emits_a_dict_the_checker_accepts():
    verdict = check(_floating_mate().to_check_dict())
    # allowable per part = 8.5 - 8.0 = 0.5; applied 0.3 -> margin +0.2
    assert verdict.margin == pytest.approx(0.2)
    assert verdict.assembles is True


def test_iso_fit_mate_emits_a_checker_dict():
    mate = MateSpec(
        kind="iso_fit", nominal_mm=20.0, hole_a=None, hole_b=None,
        fastener=None, designation="H7/g6", position_tol_a=0.0, position_tol_b=0.0,
    )
    d = mate.to_check_dict()
    assert d["type"] == "iso_fit"
    assert d["designation"] == "H7/g6"
    assert check(d).margin == pytest.approx(1.0)  # clearance fit, full yield


def test_iso_fit_check_dict_carries_the_monte_carlo_seed_and_sample_count():
    """CLAUDE.md: Tier 2 always reports a seed. It has to be in the SIDECAR.

    Omitting these let tolcad.checker fall back to seed=0 / n=100_000, so the
    label of a line-to-line fit like H7/h6 -- which genuinely flips across
    sampling seeds -- was decided by a default nobody wrote down.
    """
    mate = MateSpec(
        kind="iso_fit", nominal_mm=20.0, hole_a=None, hole_b=None,
        fastener=None, designation="H7/h6", position_tol_a=0.0, position_tol_b=0.0,
        mc_seed=12345, mc_n=25_000,
    )
    d = mate.to_check_dict()
    assert d["seed"] == 12345
    assert d["n"] == 25_000
    verdict = check(d)
    assert verdict.detail["seed"] == 12345
    assert verdict.detail["n"] == 25_000


def test_monte_carlo_fields_survive_the_sidecar_round_trip():
    mate = MateSpec(
        kind="iso_fit", nominal_mm=16.0, hole_a=None, hole_b=None,
        fastener=None, designation="H7/h6", position_tol_a=0.0, position_tol_b=0.0,
        mc_seed=987, mc_n=50_000,
    )
    original = AssemblySpec(seed=1, difficulty=1, mates=[mate])
    text = original.to_json()
    assert '"mc_seed": 987' in text
    assert '"mc_n": 50000' in text
    restored = AssemblySpec.from_json(text)
    assert restored == original
    assert restored.mates[0].mc_seed == 987
    assert restored.mates[0].mc_n == 50_000


def test_non_positive_monte_carlo_sample_count_rejected():
    with pytest.raises(ValueError, match="mc_n"):
        MateSpec(
            kind="iso_fit", nominal_mm=16.0, hole_a=None, hole_b=None,
            fastener=None, designation="H7/h6", position_tol_a=0.0,
            position_tol_b=0.0, mc_n=0,
        )


def test_assembly_spec_json_round_trip_is_lossless():
    original = AssemblySpec(
        seed=42, difficulty=2, mates=[_floating_mate()],
        plate_size_mm=40.0, plate_thickness_mm=8.0,
    )
    restored = AssemblySpec.from_json(original.to_json())
    assert restored == original


def test_unknown_mate_kind_rejected():
    with pytest.raises(ValueError, match="kind"):
        MateSpec(
            kind="weld", nominal_mm=8.0, hole_a=None, hole_b=None, fastener=None,
            designation=None, position_tol_a=0.0, position_tol_b=0.0,
        )


def test_assembly_spec_rejects_empty_mate_list():
    with pytest.raises(ValueError, match="at least one mate"):
        AssemblySpec(seed=1, difficulty=1, mates=[], plate_size_mm=40.0,
                     plate_thickness_mm=8.0)


def test_position_tol_a_injected_when_hole_a_has_no_position_tol():
    """Verify position_tol_a is injected as the single source of truth."""
    mate = MateSpec(
        kind="floating_fastener",
        nominal_mm=8.0,
        hole_a={"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2},  # no position_tol
        hole_b={"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2},  # no position_tol
        fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
        designation=None,
        position_tol_a=0.3,
        position_tol_b=0.3,
    )
    d = mate.to_check_dict()
    assert d["hole_a"]["position_tol"] == 0.3
    assert d["hole_b"]["position_tol"] == 0.3
    verdict = check(d)
    # Margin should be computed using injected position_tol
    assert verdict.margin == pytest.approx(0.2)
    assert verdict.assembles is True


def test_position_tol_a_overrides_conflicting_value_in_hole_a():
    """Verify position_tol_a overrides conflicting position_tol in hole_a dict."""
    mate = MateSpec(
        kind="floating_fastener",
        nominal_mm=8.0,
        hole_a={"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.5},
        hole_b={"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.5},
        fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
        designation=None,
        position_tol_a=0.3,  # This should override the 0.5 in the dicts
        position_tol_b=0.3,
    )
    d = mate.to_check_dict()
    assert d["hole_a"]["position_tol"] == 0.3
    assert d["hole_b"]["position_tol"] == 0.3
    verdict = check(d)
    # Margin should use 0.3, not 0.5
    assert verdict.margin == pytest.approx(0.2)
    assert verdict.assembles is True


def test_virtual_condition_mate_round_trip():
    """Virtual condition mate through to checker with correct margin."""
    # Ø8.0 pin (external) with 0.3 position tolerance -> VC 8.3
    # Ø8.5 hole (internal) with 0.3 position tolerance -> VC 8.2
    # margin = 8.2 - 8.3 = -0.1
    mate = MateSpec(
        kind="virtual_condition",
        nominal_mm=8.0,
        hole_a={"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2},
        hole_b=None,
        fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
        designation=None,
        position_tol_a=0.3,
        position_tol_b=0.0,
    )
    verdict = check(mate.to_check_dict())
    # VC_hole = 8.5 - 0.3 = 8.2
    # VC_pin = 8.0 + 0.3 = 8.3
    # margin = 8.2 - 8.3 = -0.1
    assert verdict.margin == pytest.approx(-0.1)
    assert verdict.assembles is False


def test_fixed_fastener_mate_round_trip():
    """Fixed fastener mate through to checker with correct margin."""
    # H_a=9.0, H_b=7.9, F=8.0, T_a=0.0, T_b=0.0
    # margin = (9.0 - 8.0) - (0.0 + 0.0) = 1.0
    mate = MateSpec(
        kind="fixed_fastener",
        nominal_mm=8.0,
        hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.0},
        hole_b={"nominal": 7.9, "lower_dev": 0.0, "upper_dev": 0.0},
        fastener={"nominal": 8.0, "lower_dev": 0.0, "upper_dev": 0.0},
        designation=None,
        position_tol_a=0.0,
        position_tol_b=0.0,
        projected_zone_mm=8.0,
    )
    verdict = check(mate.to_check_dict())
    assert verdict.margin == pytest.approx(1.0)
    assert verdict.assembles is True


def test_virtual_condition_rejects_missing_hole_a():
    with pytest.raises(ValueError, match="hole_a"):
        MateSpec(
            kind="virtual_condition",
            nominal_mm=8.0,
            hole_a=None,  # Missing
            hole_b=None,
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None,
            position_tol_a=0.0,
            position_tol_b=0.0,
        )


def test_floating_fastener_rejects_missing_hole_b():
    with pytest.raises(ValueError, match="hole_b"):
        MateSpec(
            kind="floating_fastener",
            nominal_mm=8.0,
            hole_a={"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2},
            hole_b=None,  # Missing
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None,
            position_tol_a=0.3,
            position_tol_b=0.3,
        )


def test_fixed_fastener_rejects_missing_hole_a():
    with pytest.raises(ValueError, match="hole_a"):
        MateSpec(
            kind="fixed_fastener",
            nominal_mm=8.0,
            hole_a=None,  # Missing
            hole_b={"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2},
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None,
            position_tol_a=0.0,
            position_tol_b=0.0,
            projected_zone_mm=8.0,
        )


def test_fixed_fastener_requires_a_projected_zone():
    """y14_5.py names the projected zone a precondition of its B-4 formula.

    Without one, the recorded verdict is optimistic and the schema does not
    say so. Refusing to build such a mate is how that stays true.
    """
    with pytest.raises(ValueError, match="projected_zone_mm"):
        MateSpec(
            kind="fixed_fastener", nominal_mm=8.0,
            hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            hole_b={"nominal": 6.8, "lower_dev": 0.0, "upper_dev": 0.2},
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None, position_tol_a=0.2, position_tol_b=0.2,
        )


def test_projected_zone_must_be_positive():
    with pytest.raises(ValueError, match="projected_zone_mm"):
        MateSpec(
            kind="fixed_fastener", nominal_mm=8.0,
            hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            hole_b={"nominal": 6.8, "lower_dev": 0.0, "upper_dev": 0.2},
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None, position_tol_a=0.2, position_tol_b=0.2,
            projected_zone_mm=0.0,
        )


def test_non_fixed_kinds_must_not_carry_a_projected_zone():
    """B-3 (floating) has no projection term; carrying one would imply it does."""
    with pytest.raises(ValueError, match="projected_zone_mm"):
        MateSpec(
            kind="floating_fastener", nominal_mm=8.0,
            hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            hole_b={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
            fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
            designation=None, position_tol_a=0.2, position_tol_b=0.2,
            projected_zone_mm=8.0,
        )


def test_projected_zone_is_not_sent_to_the_checker():
    """B-4 has no P term -- that is B-5, which tolcad does not implement.

    Emitting it would imply the checker consumes it, which it does not.
    """
    mate = MateSpec(
        kind="fixed_fastener", nominal_mm=8.0,
        hole_a={"nominal": 9.0, "lower_dev": 0.0, "upper_dev": 0.2},
        hole_b={"nominal": 6.8, "lower_dev": 0.0, "upper_dev": 0.2},
        fastener={"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
        designation=None, position_tol_a=0.2, position_tol_b=0.2,
        projected_zone_mm=8.0,
    )
    assert "projected_zone_mm" not in mate.to_check_dict()
    assert check(mate.to_check_dict()).assembles is True
