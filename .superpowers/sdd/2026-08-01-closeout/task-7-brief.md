### Task 7: CI that exercises the corruption mode

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `tests/test_gitattributes_clone.py`
- Test: same

**Interfaces:**
- Consumes: nothing
- Produces: two CI jobs, `suite` and `integrity`

Two corrections to the obvious design. `.gitattributes` is testable **without** CI — a `git clone --no-local` with `core.autocrlf=true` proves it in seconds. And `ubuntu-latest` defaults to `autocrlf=false`, so a Linux-only CI exercises the *safe* direction and proves nothing about the corruption mode. Layer 2 takes ~25 minutes and must not sit on the per-push path: a gate people route around is worse than no gate.

- [ ] **Step 1: Write the failing test**

Create `tests/test_gitattributes_clone.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

The test passes against the current `.gitattributes`, so passing proves nothing. Demonstrate it can fail: temporarily comment out the `*.stp binary` line in `.gitattributes`, commit to a scratch branch, run the test, confirm the `autocrlf=true` case FAILS with a byte count of 391,739, then discard the scratch commit. Paste both results.

- [ ] **Step 3: Write the workflow**

Create `.github/workflows/ci.yml` with two jobs:

- **`suite`** — matrix `[ubuntu-latest, windows-latest]`. The Windows leg runs `git config --global core.autocrlf true` **before** checkout, because that is the configuration under which the corruption occurs. Steps: checkout, setup-python 3.13, `pip install -e ".[dev,gen]"`, `python -m pytest -q`. The tree-cleanliness fixture from Task 1 runs automatically.
- **`integrity`** — `workflow_dispatch` and a weekly `schedule` **only**. Runs `python scripts/check_suite_integrity.py`. Never on push: ~25 minutes.

Claim precisely what CI adds, in a comment: the code path already works in a fresh clone (verified locally), but a local clone reuses an ambient interpreter. CI's actual contribution is proving `pip install -e ".[dev,gen]"` works from nothing.

- [ ] **Step 4: Run and push**

Run: `python -m pytest tests/test_gitattributes_clone.py -v`, then the full suite. Push and confirm both jobs appear in Actions and `suite` goes green on both platforms.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml tests/test_gitattributes_clone.py
git commit -m "feat: CI exercising the CRLF corruption mode, integrity layer off the push path"
```

---

