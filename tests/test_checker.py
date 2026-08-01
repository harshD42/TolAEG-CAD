import pytest
from tolcad.checker import check


def _uninterned(text: str) -> str:
    """A string equal to `text` but guaranteed NOT to be the interned literal.

    `"".join([text])` does NOT do this, though an earlier version of these
    tests assumed it did: CPython's str.join has a single-element fast path
    that returns the item itself, so the result IS the interned literal and an
    `is` mutant sails through. Splitting into two pieces forces a real
    concatenation into a fresh object. The asserts make this helper fail loudly
    if CPython ever changes, rather than silently going back to being a no-op.

    This mirrors production, which is the point: checker.py reaches
    fastener_assembles with `kind.replace("_fastener", "")`, and str.replace
    likewise returns a fresh, non-interned object.
    """
    assert len(text) >= 2
    built = "".join([text[:1], text[1:]])
    assert built == text and built is not text, (
        "the interning-defeat helper has stopped defeating interning"
    )
    return built


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


def test_dispatches_fixed_fastener():
    """The whole core test subset had NO fixed_fastener mate going through
    check() -- the only check()-level fastener coverage was the floating mate
    above (and one in test_reliability.py). That gap hid a live mutant.

    check() reaches y14_5 with `condition = kind.replace("_fastener", "")`,
    which str.replace returns as a FRESH, non-interned object. So the
    `condition is "fixed"` mutant in the governing_part expression evaluates
    False here, falls into the floating branch, and compares margin_a <=
    margin_b -- both None in the fixed case -- raising
    `TypeError: '<=' not supported between instances of 'NoneType' and
    'NoneType'`. Nothing in the suite exercised that path, so the mutant was
    filed as an equivalent mutant. It is not one.

    H_a = 8.5, F = 8.0, T_a = T_b = 0.1 -> margin = 0.5 - 0.2 = 0.3.
    """
    verdict = check({
        "type": "fixed_fastener",
        "hole_a": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2,
                   "position_tol": 0.1},
        "hole_b": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2,
                   "position_tol": 0.1},
        "fastener": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
    })
    assert verdict.method == "fixed_fastener"
    assert verdict.assembles is True
    assert verdict.margin == pytest.approx(0.3)
    # None is the fixed case's documented governing_part: H_b never enters the
    # B-4 formula, so no part "governs". Asserting it pins the condition test.
    assert verdict.detail["governing_part"] is None
    assert verdict.detail["clearance_b"] is None


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


def test_unknown_mate_type_before_iso_fit_lexically_is_still_rejected():
    """'weld' (used above) sorts after 'iso_fit' lexically, so it cannot
    distinguish `kind == "iso_fit"` from a `kind <= "iso_fit"` mutant (both
    reject it). 'gizmo' sorts BEFORE 'iso_fit', so a `<=` mutant would
    incorrectly dispatch it into the iso_fit branch instead of raising.
    """
    with pytest.raises(ValueError, match="unknown mate type"):
        check({"type": "gizmo"})


def test_virtual_condition_dispatch_uses_equality_not_identity():
    """CPython interns identifier-shaped string literals, so a literal
    "virtual_condition" here would share identity with the literal in
    checker.py even under an `is` mutant. `_uninterned` builds a genuinely
    distinct object.

    This test previously used `"".join(["virtual_condition"])`, which returns
    the interned literal unchanged -- so it did NOT kill the `kind is
    "virtual_condition"` mutant, despite the triage recording it as killed.
    Verified: the whole core subset stayed green under that mutant.
    """
    kind = _uninterned("virtual_condition")
    verdict = check({
        "type": kind,
        "pin": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
        "hole": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2},
    })
    assert verdict.method == "virtual_condition"


def test_iso_fit_dispatch_uses_equality_not_identity():
    """Same reasoning as above, for the iso_fit branch (and same correction:
    the old `"".join(["iso_fit"])` did not kill the `kind is "iso_fit"` mutant).
    """
    kind = _uninterned("iso_fit")
    verdict = check({
        "type": kind, "nominal": 20.0, "designation": "H7/g6", "n": 100, "seed": 0,
    })
    assert verdict.margin == pytest.approx(1.0)


def test_missing_position_tol_defaults_to_zero():
    """position_tol's default in _feature() must be 0.0. virtual_condition
    is sensitive to it (VC = mmc +/- position_tol), so a wrong default
    silently changes every verdict for a mate that omits the key.

    VC_pin = 8.0 + 0 = 8.0; VC_hole = 8.5 - 0 = 8.5; margin = 0.5.
    """
    verdict = check({
        "type": "virtual_condition",
        "pin": {"nominal": 8.0, "lower_dev": -0.1, "upper_dev": 0.0},
        "hole": {"nominal": 8.5, "lower_dev": 0.0, "upper_dev": 0.2},
    })
    assert verdict.margin == pytest.approx(0.5)


def test_missing_n_and_seed_default_to_documented_values():
    """iso_fit's n and seed defaults (100_000 and 0) must match what the
    docstring/design promise; detail exposes both directly so this does not
    depend on the Monte Carlo yield happening to differ.
    """
    verdict = check({
        "type": "iso_fit", "nominal": 20.0, "designation": "H7/g6",
    })
    assert verdict.detail["n"] == 100_000
    assert verdict.detail["seed"] == 0
