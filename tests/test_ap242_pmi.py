import pathlib
import pytest

pytest.importorskip("OCP", reason="requires the [gen] extra")

from validation.ap242_pmi import PmiCounts, read_pmi_counts

NIST_DIR = pathlib.Path(__file__).parent.parent / "data" / "nist_pmi"
FTC06 = NIST_DIR / "nist_ftc_06_asme1_ap242-e2.stp"

pytestmark = pytest.mark.skipif(
    not FTC06.is_file(),
    reason="NIST suite not fetched; run scripts/fetch_nist_pmi.py",
)


def test_reads_semantic_pmi_from_nist_ftc06():
    """Verified by execution 2026-08-01: 47 dimensions, 27 geotols, 59 datums.

    These are exact expected values, not bounds. If OCCT's extraction changes,
    this must fail loudly rather than silently reporting fewer tolerances.
    """
    counts = read_pmi_counts(FTC06)
    assert counts == PmiCounts(dimensions=47, geometric_tolerances=27, datums=59)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        read_pmi_counts(NIST_DIR / "does_not_exist.stp")
