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

    # C4: these two rows must TRACK their source markers rather than being
    # hardcoded either way. Both citations were verified against the primary
    # standards on 2026-08-01, so both markers are gone and both rows now read
    # PASS. If a marker is ever reintroduced the row must revert to SKIP.
    y14_src = (REPO / "src" / "tolcad" / "y14_5.py").read_text(encoding="utf-8")
    iso_src = (REPO / "src" / "tolcad" / "iso286.py").read_text(encoding="utf-8")
    lines = {ln.strip() for ln in result.stdout.splitlines()}

    def _row(prefix: str) -> str:
        matches = [ln for ln in lines if ln.startswith(prefix)]
        assert len(matches) == 1, f"expected exactly one {prefix!r} row, got {matches}"
        return matches[0]

    y14_expected = "SKIP" if "CITATION PENDING" in y14_src else "PASS"
    iso_expected = "SKIP" if "replace this line" in iso_src else "PASS"
    assert y14_expected in _row("Y14.5 citation verified")
    assert iso_expected in _row("ISO 286 transcription verified")

    # I6: the fresh-clone criterion cannot be checked in-process and must stay SKIP.
    assert "SKIP" in _row("Fresh clone pipeline")
