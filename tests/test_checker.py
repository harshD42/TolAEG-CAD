import pytest
from tolcad.checker import check


def test_dispatches_virtual_condition():
    verdict = check({
        "type": "virtual_condition",
        "pin": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0, "position_tol": 0.0},
        "hole": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.2},
    })
    assert verdict.assembles is True
    assert verdict.method == "virtual_condition"


def test_dispatches_floating_fastener():
    hole = {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2, "position_tol": 0.6}
    verdict = check({
        "type": "floating_fastener",
        "hole_a": hole,
        "hole_b": hole,
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    })
    assert verdict.assembles is False


def test_dispatches_iso_fit():
    verdict = check({
        "type": "iso_fit",
        "nominal": 20.0,
        "designation": "H7/g6",
        "n": 10_000,
        "seed": 0,
    })
    assert verdict.margin == pytest.approx(1.0)


def test_unknown_mate_type_rejected():
    with pytest.raises(ValueError, match="unknown mate type"):
        check({"type": "weld"})


def test_missing_type_key_rejected():
    with pytest.raises(ValueError, match="'type'"):
        check({})
