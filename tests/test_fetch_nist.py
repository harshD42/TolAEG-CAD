# tests/test_fetch_nist.py
import importlib.util
import pathlib
import zipfile

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


def _load_fetch_module():
    """Load scripts/fetch_nist_pmi.py by path (scripts/ has no __init__.py)."""
    spec = importlib.util.spec_from_file_location("fetch_nist_pmi", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_fake_archive(dest: pathlib.Path, ap242_count: int) -> None:
    """Write a real ZIP named like the real one, with `ap242_count` fake
    AP242 .stp members, so main() finds the archive already present and
    never touches the network."""
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / "NIST-PMI-STEP-Files.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for i in range(ap242_count):
            zf.writestr(f"nist_ftc_{i:02d}_asme1_ap242-e2.stp", "placeholder STEP text")


def _network_blocked_module(tmp_path, monkeypatch):
    """Load the fetcher, point DEST at tmp_path, and make any attempt to
    reach the network fail loudly rather than silently downloading."""
    module = _load_fetch_module()
    monkeypatch.setattr(module, "DEST", tmp_path)
    monkeypatch.setattr(
        module, "URL", "http://example.invalid/should-not-be-fetched.zip"
    )

    def _boom(*_args, **_kwargs):
        raise AssertionError("network access attempted in a fetcher test")

    monkeypatch.setattr(module.urllib.request, "urlopen", _boom)
    return module


def test_main_returns_1_and_warns_when_ap242_count_mismatches(
    tmp_path, monkeypatch, capsys
):
    module = _network_blocked_module(tmp_path, monkeypatch)
    _build_fake_archive(tmp_path, ap242_count=2)  # wrong: expected 17

    result = module.main()

    assert result == 1
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "expected 17" in captured.err


def test_main_returns_0_when_ap242_count_matches(tmp_path, monkeypatch, capsys):
    module = _network_blocked_module(tmp_path, monkeypatch)
    _build_fake_archive(tmp_path, ap242_count=17)  # matches EXPECTED_AP242_FILES

    result = module.main()

    assert result == 0
    captured = capsys.readouterr()
    assert captured.err == ""
