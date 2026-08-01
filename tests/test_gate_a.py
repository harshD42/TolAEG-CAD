import subprocess
import sys
import pathlib

REPO = pathlib.Path(__file__).parent.parent

sys.path.insert(0, str(REPO))
from scripts.gate_a import _format_margin_band  # noqa: E402
from tolcad.reliability import StabilityResult  # noqa: E402


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


def test_gate_a_reports_tested_margin_band():
    """The reliability row's note is what makes the measurement auditable:
    it must show the actual |margin| range that was tested, not just the
    pass/fail value. The live mate set (_RELIABILITY_MATES) spans both a
    far-from-boundary regime and a sensitive band with margins ~3.5e-4, so
    the normal (tested > 0) path is exercised on every real gate_a.py run.
    """
    result = subprocess.run(
        [sys.executable, "scripts/gate_a.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    lines = {ln.strip() for ln in result.stdout.splitlines()}
    reliability_line = next(ln for ln in lines if ln.startswith("Checker reliability"))
    assert "|margin| in [" in reliability_line
    assert "tested=" in reliability_line
    assert "excluded=" in reliability_line


def test_format_margin_band_normal_case():
    """Direct unit test of the band-formatting helper for tested > 0: it
    must render both the min and max tested |margin| in scientific notation.
    """
    stability = StabilityResult(
        value=1.0, tested=3, excluded=1,
        min_abs_margin=3.5e-4, max_abs_margin=9.0e-1,
    )
    band = _format_margin_band(stability)
    assert band == "|margin| in [3.50e-04, 9.00e-01]"


def test_format_margin_band_tested_zero_case():
    """When every mate is excluded (tested == 0), min/max_abs_margin are
    None; the helper must fall back to a sensible, non-numeric string
    rather than trying to format None (which would raise or print
    "None").
    """
    stability = StabilityResult(
        value=1.0, tested=0, excluded=4,
        min_abs_margin=None, max_abs_margin=None,
    )
    band = _format_margin_band(stability)
    assert band == "no mates outside the exclusion band"
    assert "None" not in band
