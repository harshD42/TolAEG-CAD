# tests/test_fetch_nist.py
import pathlib

REPO = pathlib.Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "fetch_nist_pmi.py"


def test_fetcher_script_exists():
    assert SCRIPT.is_file()


def test_fetcher_records_the_source_url_and_licence_statement():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "NIST-PMI-STEP-Files.zip" in text
    assert "without any restrictions" in text, (
        "record NIST's usage statement so provenance is auditable"
    )


def test_nist_payload_is_gitignored():
    ignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "data/nist_pmi/" in ignore
