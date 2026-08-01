"""The binary fixture must survive a clone under Windows' autocrlf default.

core.autocrlf=true once stored a CRLF-normalised blob for this fixture, and the
PMI reader returns IDENTICAL counts from the mangled copy -- so the positive
control passed against the exact corruption it existed to detect. Only size and
hash catch it, and only a fresh clone exercises the normalisation.
"""

import hashlib
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
FIXTURE_REL = "tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp"
FIXTURE_BYTES = 396_445
FIXTURE_SHA256 = "85a5752da05f53c456ca3a9e038c90358e1d5a3141d1f0d6e5f0970f2356e821"


@pytest.mark.parametrize("autocrlf", ["true", "input", "false"])
def test_the_fixture_survives_a_clone_under_every_autocrlf_setting(tmp_path, autocrlf):
    dest = tmp_path / f"clone-{autocrlf}"
    subprocess.run(
        ["git", "-c", f"core.autocrlf={autocrlf}", "clone", "--no-local",
         "--quiet", str(REPO), str(dest)],
        check=True, capture_output=True,
    )
    data = (dest / FIXTURE_REL).read_bytes()
    assert len(data) == FIXTURE_BYTES, (
        f"autocrlf={autocrlf} produced {len(data)} bytes, not {FIXTURE_BYTES}. "
        f"The .gitattributes 'binary' rule is not protecting this fixture."
    )
    assert hashlib.sha256(data).hexdigest() == FIXTURE_SHA256
