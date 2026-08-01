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
