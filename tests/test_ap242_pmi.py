import hashlib
import importlib.util
import pathlib

import pytest

# The OCP gate is per-test rather than module-level so the fixture INTEGRITY
# check below still runs on a clone without the [gen] extra. That check is the
# only thing defending the byte-exactness claim in NIST-PROVENANCE.md, and a
# guard that can be switched off by a missing optional dependency is not a
# guard. Everything that actually reads PMI is marked `needs_ocp`.
#
# The gate asks whether OCP is INSTALLED rather than wrapping the import in
# `except ImportError`. A bare except cannot tell "the optional extra is absent"
# from "validation/ap242_pmi.py is broken": renaming PmiCounts turned four
# oracle tests into silent skips reporting "requires the [gen] extra" on a
# machine that had the extra all along. Asking find_spec the narrow question and
# leaving the import unguarded means a broken module raises at collection, which
# is what a broken module should do.
_HAVE_OCP = importlib.util.find_spec("OCP") is not None

if _HAVE_OCP:
    from validation.ap242_pmi import PmiCounts, read_pmi_counts

needs_ocp = pytest.mark.skipif(not _HAVE_OCP, reason="requires the [gen] extra")

NIST_DIR = pathlib.Path(__file__).parent.parent / "data" / "nist_pmi"
FTC06 = NIST_DIR / "nist_ftc_06_asme1_ap242-e2.stp"

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "nist_ctc_01_asme1_ap242-e1.stp"

# Identity of the NIST original, recorded in tests/fixtures/NIST-PROVENANCE.md.
# Byte count ALONE is not enough and the hash ALONE is not enough to read: the
# count is what the provenance note states in prose, the hash is what makes the
# statement falsifiable.
FIXTURE_BYTES = 396_445
FIXTURE_SHA256 = "85a5752da05f53c456ca3a9e038c90358e1d5a3141d1f0d6e5f0970f2356e821"


def assert_is_the_nist_original(path: pathlib.Path) -> None:
    """Fail unless `path` is byte-for-byte the redistributed NIST file.

    WHY THIS EXISTS. This repo has core.autocrlf=true. Committing the fixture
    without a `.gitattributes` binary rule stored a CRLF->LF-normalised
    391,739-byte blob in place of the 396,445-byte original (see commit
    d312ad6, fixed in 7ba4e87). CONTROLLER-VERIFIED: the PMI reader returns the
    SAME counts (21/6/11) from the mangled file, so the positive control below
    passed against a corrupted fixture. Nothing could fail.

    `.gitattributes` is last-match-wins, so appending `* text=auto` would
    silently re-arm that bug. This function is what notices.
    """
    data = path.read_bytes()
    assert len(data) == FIXTURE_BYTES, (
        f"{path.name} is {len(data)} bytes, not the {FIXTURE_BYTES} bytes "
        f"NIST-PROVENANCE.md claims. A 391,739-byte file is the known "
        f"CRLF->LF corruption: check that .gitattributes still marks *.stp "
        f"binary and that no later rule overrides it."
    )
    digest = hashlib.sha256(data).hexdigest()
    assert digest == FIXTURE_SHA256, (
        f"{path.name} hashes to {digest}, not the {FIXTURE_SHA256} recorded in "
        f"NIST-PROVENANCE.md. The file is not the NIST original."
    )


def test_the_committed_fixture_is_byte_identical_to_the_nist_original():
    """The integrity claim NIST-PROVENANCE.md makes, as an assertion.

    A byte count stated in prose that no test reads is not an integrity claim.
    Runs with or without the [gen] extra, because the claim is about the repo,
    not about the CAD toolkit.
    """
    assert FIXTURE.is_file(), (
        "the AP242 fixture must be committed, not fetched -- that is the whole "
        "point of it"
    )
    assert_is_the_nist_original(FIXTURE)


@needs_ocp
def test_reads_semantic_pmi_from_nist_ftc06():
    """Verified by execution 2026-08-01: 47 dimensions, 27 geotols, 59 datums.

    These are exact expected values, not bounds. If OCCT's extraction changes,
    this must fail loudly rather than silently reporting fewer tolerances.
    """
    if not FTC06.is_file():
        pytest.skip("NIST suite not fetched; run scripts/fetch_nist_pmi.py")
    counts = read_pmi_counts(FTC06)
    assert counts == PmiCounts(dimensions=47, geometric_tolerances=27, datums=59)


@needs_ocp
def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        read_pmi_counts(NIST_DIR / "does_not_exist.stp")


@needs_ocp
def test_reads_nonzero_pmi_from_the_committed_fixture():
    """Positive control that runs on a FRESH CLONE, with no fetch step.

    Without this, the only oracle assertions a fresh clone exercises are
    zero-counts and a FileNotFoundError -- so a read_pmi_counts stubbed to
    `return PmiCounts(0, 0, 0)` would pass the whole suite, and the
    zero-PMI contrast in test_end_to_end.py would prove nothing. Design spec
    line 252 makes the fresh-clone path an explicit success criterion.

    The counts are checked against the file's IDENTITY first: the reader gives
    21/6/11 for the CRLF-mangled copy too, so counts alone would not notice a
    corrupted fixture.

    Exact counts, verified by execution 2026-08-01, not bounds.
    """
    assert FIXTURE.is_file(), (
        "the AP242 fixture must be committed, not fetched -- that is the whole "
        "point of it"
    )
    assert_is_the_nist_original(FIXTURE)
    counts = read_pmi_counts(FIXTURE)
    assert counts == PmiCounts(dimensions=21, geometric_tolerances=6, datums=11)


@needs_ocp
def test_the_fixture_and_the_fetched_suite_disagree_about_counts():
    """Guards a reader that returns a constant regardless of its input.

    Skips without the fetched suite, but on a developer machine it proves the
    two files are distinguished. The fixture test above is the fresh-clone
    guarantee; this one is the stronger check when both are available.
    """
    if not FTC06.is_file():
        pytest.skip("NIST suite not fetched; run scripts/fetch_nist_pmi.py")
    assert read_pmi_counts(FIXTURE) != read_pmi_counts(FTC06)
