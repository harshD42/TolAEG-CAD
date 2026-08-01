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


def test_the_coverage_floor_is_a_measured_value_not_a_round_number():
    """A floor pinned at an aspirational round number is not a measurement.

    The project's drift class is exactly this: a threshold that stops tracking
    what it is supposed to bound. Whatever the measured baseline is, it is
    almost certainly not 80 or 90.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert mod.COVERAGE_FLOOR not in (0, 50, 60, 70, 75, 80, 85, 90, 95, 100), (
        f"COVERAGE_FLOOR {mod.COVERAGE_FLOOR} looks aspirational rather than "
        f"measured. Run the script, read the number, pin that."
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


def test_the_mutation_floor_is_measured_not_aspirational():
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert mod.MUTATION_FLOOR not in (0, 50, 60, 70, 75, 80, 85, 90, 95, 100), (
        f"MUTATION_FLOOR {mod.MUTATION_FLOOR} looks aspirational rather than "
        f"measured. Run the layer, read the number, pin that."
    )
