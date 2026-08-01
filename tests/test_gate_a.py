import subprocess
import sys
import pathlib

REPO = pathlib.Path(__file__).parent.parent


def test_gate_a_script_runs_without_solidworks_export():
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert "TolAnalyst agreement" in result.stdout
    assert "SKIP" in result.stdout
    # Missing oracle means Gate A is not cleared.
    assert result.returncode != 0


def test_gate_a_reports_every_criterion():
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    for criterion in [
        "Y14.5 worked examples",
        "TolAnalyst agreement",
        "Monte Carlo convergence",
        "Validation isolation",
    ]:
        assert criterion in result.stdout
