import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "check_suite_integrity.py"


def test_the_script_exists():
    assert SCRIPT.is_file()


def test_it_names_the_six_core_modules():
    """Layer 1 and 2 scope. gen/ is deliberately excluded -- CadQuery mutants
    are slow and frequently geometrically meaningless."""
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert set(mod.CORE_MODULES) == {
        "types", "y14_5", "iso286", "montecarlo", "checker", "reliability",
    }


def test_the_coverage_pin_is_a_measured_value_not_a_round_number():
    """A pin set at an aspirational round number is not a measurement.

    The project's drift class is exactly this: a threshold that stops tracking
    what it is supposed to bound. Whatever the measured baseline is, it is
    almost certainly not 80 or 90.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert mod.COVERAGE_MEASURED not in (0, 50, 60, 70, 75, 80, 85, 90, 95, 100), (
        f"COVERAGE_MEASURED {mod.COVERAGE_MEASURED} looks aspirational rather "
        f"than measured. Run the script, read the number, pin that."
    )


def test_the_script_reports_and_exits_nonzero_when_a_layer_fails(tmp_path):
    """Exercised via --self-test, which forces one layer to report failure."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--self-test-failure"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert proc.returncode == 1, "a failing layer must exit nonzero"
    assert "FAIL" in proc.stdout


def test_the_cosmic_ray_config_runs_the_whole_core_subset():
    """A per-file test command inflates survivors and makes the score meaningless.

    Spiked 2026-08-01 on types.py: scoping the command to tests/test_types.py
    alone gave 12 survivors of 66 (18.2%); the full core subset gave 5 of 66
    (7.58%). checker.py and y14_5.py tests exercise types.py heavily.
    """
    import tomllib

    cfg = tomllib.loads((REPO / "cosmic-ray.toml").read_text(encoding="utf-8"))
    command = cfg["cosmic-ray"]["test-command"]
    for module in ("types", "y14_5", "iso286", "montecarlo", "checker", "reliability"):
        assert f"tests/test_{module}.py" in command, (
            f"cosmic-ray's test-command omits tests/test_{module}.py; the "
            f"resulting mutation score would be inflated and meaningless"
        )


def test_the_mutation_pin_is_measured_not_aspirational():
    """Checks MUTATION_MEASURED directly -- the pin fed to check_two_sided.

    The tolerance is a separate, deliberately-chosen margin (see the test
    below); it is the MEASURED value that has to be real.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert mod.MUTATION_MEASURED not in (0, 50, 60, 70, 75, 80, 85, 90, 95, 100), (
        f"MUTATION_MEASURED {mod.MUTATION_MEASURED} looks aspirational rather "
        f"than measured. Run the layer, read the number, pin that."
    )


def test_the_mutation_tolerance_covers_the_display_rounding_it_is_pinned_from():
    """MUTATION_MEASURED is a 2-decimal DISPLAY rounding; the gate compares the
    RAW score. A one-sided floor set to the displayed value can fail on an
    unchanged tree whenever the raw score rounds up into it -- which is exactly
    what run 3's 610/650 = 93.8462% did against a literal 93.85 floor. The
    tolerance must be at least half a display ulp (0.005) to close that gap; it
    is 0.50pp, which also absorbs cosmic-ray's observed timeout variance.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert mod.MUTATION_TOLERANCE >= 0.005, (
        "MUTATION_TOLERANCE must exceed the 2-decimal display rounding, or an "
        "unchanged tree can fail the gate deterministically"
    )
    # A raw score that only differs from the displayed pin by rounding must
    # still pass the two-sided check, in both directions.
    ok_down, _ = mod.check_two_sided(
        mod.MUTATION_MEASURED - 0.0049, mod.MUTATION_MEASURED, mod.MUTATION_TOLERANCE
    )
    ok_up, _ = mod.check_two_sided(
        mod.MUTATION_MEASURED + 0.0049, mod.MUTATION_MEASURED, mod.MUTATION_TOLERANCE
    )
    assert ok_down and ok_up


def test_a_measurement_above_the_pin_fails_too():
    """One-sided floors let the pin silently detach. That is how F1 happened.

    MUTATION_MEASURED drifted 2.04pp below the tree -- four times its own
    tolerance -- and the gate stayed green because a floor is a lower bound.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    ok_low, msg_low = mod.check_two_sided(90.0, 95.0, 0.5)
    assert not ok_low and "below" in msg_low.lower()

    ok_high, msg_high = mod.check_two_sided(99.0, 95.0, 0.5)
    assert not ok_high, "an improvement must also fail -- the pin has detached"
    assert "re-pin" in msg_high.lower(), (
        "the upward message must tell the operator to re-pin, not just report"
    )

    ok_mid, _ = mod.check_two_sided(95.2, 95.0, 0.5)
    assert ok_mid


def test_both_pins_are_measured_values_not_round_numbers():
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    for name in ("COVERAGE_MEASURED", "MUTATION_MEASURED"):
        value = getattr(mod, name)
        assert value not in (0, 50, 60, 70, 75, 80, 85, 90, 95, 100), (
            f"{name} = {value} looks aspirational. Run the layer, read the "
            f"number, pin that."
        )
