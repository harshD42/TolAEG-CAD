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
        "Y14.5 self-consistency",
        "TolAnalyst agreement",
        "Monte Carlo convergence",
        "Validation isolation",
    ]:
        assert criterion in result.stdout


def test_gate_a_reports_v2_criteria():
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    for criterion in [
        "Y14.5 self-consistency",
        "NIST PMI conformance",
        "TolAnalyst agreement",
        "Monte Carlo convergence",
        "Checker reliability",
        "Validation isolation",
    ]:
        assert criterion in result.stdout, f"missing criterion: {criterion}"


def test_gate_a_not_cleared_without_oracles():
    """Missing oracles must never count as passes."""
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert "NOT CLEARED" in result.stdout
    assert result.returncode != 0


def test_gate_a_reports_final_wave_criteria():
    """C3/C4/I5/I6: the final fix wave added new rows that must not be lost:
    a measured reliability value, the pending-citation guard rows, and the
    fresh-clone criterion from spec section 7.
    """
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    for criterion in [
        "Y14.5 citation verified",
        "ISO 286 transcription verified",
        "Fresh clone pipeline",
    ]:
        assert criterion in result.stdout, f"missing criterion: {criterion}"

    # C3: the reliability row must show a measured value, not just PASS/FAIL.
    assert "measured" in result.stdout

    # C4: the pending-citation and transcription-placeholder markers are still
    # in source (by design — a human has not verified them yet), so these two
    # rows must read SKIP, never PASS.
    lines = {ln.strip() for ln in result.stdout.splitlines()}
    citation_line = next(ln for ln in lines if ln.startswith("Y14.5 citation verified"))
    iso_line = next(ln for ln in lines if ln.startswith("ISO 286 transcription verified"))
    assert "SKIP" in citation_line
    assert "SKIP" in iso_line
