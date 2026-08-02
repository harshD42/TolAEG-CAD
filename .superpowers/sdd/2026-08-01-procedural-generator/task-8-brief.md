### Task 8: Fetch and verify the NIST conformance suite

**Files:**
- Create: `scripts/fetch_nist_pmi.py`
- Modify: `.gitignore`
- Test: `tests/test_fetch_nist.py`

**Interfaces:**
- Consumes: nothing
- Produces: `data/nist_pmi/*.stp`; `scripts/fetch_nist_pmi.py` as a CLI

Mirrors the existing `scripts/fetch_literature.sh` convention: the payload is gitignored, the fetcher and its manifest are tracked, so the corpus stays reproducible and auditable.

The archive is ~14 MB with 49 entries, 17 of them AP242 `.stp`. NIST states the files "can be used without any restrictions."

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fetch_nist.py -v`
Expected: FAIL — the script does not exist

- [ ] **Step 3: Write the fetcher**

```python
#!/usr/bin/env python
"""Fetch the NIST MBE PMI Validation and Conformance Test Suite.

Source: https://www.nist.gov/system/files/documents/noindex/2024/06/19/NIST-PMI-STEP-Files.zip
(reached from https://www.nist.gov/document/nist-pmi-step-files)

NIST states the test cases, CAD models and STEP files "can be used without any
restrictions", and asks for acknowledgement. This is the licence-free Gate A
oracle: it is why Gate A can be cleared with no commercial CAD licence.

Payload lands in data/nist_pmi/ and is gitignored; this script is tracked, so
the corpus is reproducible from the repo alone.

Usage: python scripts/fetch_nist_pmi.py
"""

from __future__ import annotations

import pathlib
import sys
import urllib.request
import zipfile

URL = (
    "https://www.nist.gov/system/files/documents/noindex/2024/06/19/"
    "NIST-PMI-STEP-Files.zip"
)
DEST = pathlib.Path(__file__).parent.parent / "data" / "nist_pmi"
EXPECTED_AP242_FILES = 17


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    archive = DEST / "NIST-PMI-STEP-Files.zip"

    if not archive.is_file():
        print(f"downloading {URL}")
        request = urllib.request.Request(
            URL, headers={"User-Agent": "tolcad-research/0.1 (academic use)"}
        )
        with urllib.request.urlopen(request) as response:
            archive.write_bytes(response.read())
    print(f"archive: {archive.stat().st_size} bytes")

    with zipfile.ZipFile(archive) as zf:
        members = [n for n in zf.namelist() if n.lower().endswith(".stp")]
        for name in members:
            target = DEST / pathlib.Path(name).name
            if not target.is_file():
                target.write_bytes(zf.read(name))

    ap242 = sorted(p.name for p in DEST.glob("*ap242*.stp"))
    print(f"extracted {len(list(DEST.glob('*.stp')))} STEP files, "
          f"{len(ap242)} AP242")
    if len(ap242) != EXPECTED_AP242_FILES:
        print(
            f"WARNING: expected {EXPECTED_AP242_FILES} AP242 files, got "
            f"{len(ap242)}. The upstream archive may have changed; verify "
            f"before using these as an oracle.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Append to `.gitignore`:

```
# NIST PMI conformance suite: ~14MB, reproducible via scripts/fetch_nist_pmi.py
data/nist_pmi/
```

- [ ] **Step 4: Run the fetcher and the tests**

Run: `python scripts/fetch_nist_pmi.py && pytest tests/test_fetch_nist.py tests/test_ap242_pmi.py -v`
Expected: fetcher exits 0 reporting 17 AP242 files; both test files pass (Task 7's tests now run rather than skip)

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_nist_pmi.py tests/test_fetch_nist.py .gitignore
git commit -m "feat: fetch and verify the NIST PMI conformance suite"
```

---

