import pathlib
import pytest

pytest.importorskip("OCP", reason="requires the [gen] extra")

from validation.ap242_pmi import PmiCounts, read_pmi_counts

NIST_DIR = pathlib.Path(__file__).parent.parent / "data" / "nist_pmi"
FTC06 = NIST_DIR / "nist_ftc_06_asme1_ap242-e2.stp"


@pytest.mark.skipif(
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


FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "nist_ctc_01_asme1_ap242-e1.stp"


def test_reads_nonzero_pmi_from_the_committed_fixture():
    """Positive control that runs on a FRESH CLONE, with no fetch step.

    Without this, the only oracle assertions a fresh clone exercises are
    zero-counts and a FileNotFoundError -- so a read_pmi_counts stubbed to
    `return PmiCounts(0, 0, 0)` would pass the whole suite, and the
    zero-PMI contrast in test_end_to_end.py would prove nothing. Design spec
    line 252 makes the fresh-clone path an explicit success criterion.

    Exact counts, verified by execution 2026-08-01, not bounds.
    """
    assert FIXTURE.is_file(), (
        "the AP242 fixture must be committed, not fetched -- that is the whole "
        "point of it"
    )
    counts = read_pmi_counts(FIXTURE)
    assert counts == PmiCounts(dimensions=21, geometric_tolerances=6, datums=11)


def test_the_fixture_and_the_fetched_suite_disagree_about_counts():
    """Guards a reader that returns a constant regardless of its input.

    Skips without the fetched suite, but on a developer machine it proves the
    two files are distinguished. The fixture test above is the fresh-clone
    guarantee; this one is the stronger check when both are available.
    """
    if not FTC06.is_file():
        pytest.skip("NIST suite not fetched; run scripts/fetch_nist_pmi.py")
    assert read_pmi_counts(FIXTURE) != read_pmi_counts(FTC06)
