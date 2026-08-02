### Task 1: Land the branch and make `pytest` safe to run on `main`

**Files:**
- Create: `tests/conftest.py`
- Modify: `CLAUDE.md`
- Test: `tests/test_tree_cleanliness.py`

**Interfaces:**
- Consumes: nothing
- Produces: a session-scoped autouse fixture failing the run if `git status --porcelain src/ tests/fixtures/` is non-empty afterwards

The merge is a clean fast-forward with **zero `src/` delta at rest**. But at *runtime* the declared mutations write to five `src/` files and a tracked fixture, and `mutation_registry.py:38-45` records that a restore has already failed once in roughly a dozen runs on Windows. This control (O-B) must land in the same commit as the merge, because it guards the hazard the merge introduces.

- [ ] **Step 1: Write the failing test**

Create `tests/test_tree_cleanliness.py`:

```python
"""The suite mutates tracked files and restores them. Prove it restored.

O-B in the stopping criterion. Covers B2 (untested error conversion), B10
(SIGKILL mid-write) and any cosmic-ray leftover, by observing the ARTIFACT
rather than guarding each guard.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent


def _dirty_tracked_paths() -> list[str]:
    proc = subprocess.run(
        ["git", "status", "--porcelain", "src/", "tests/fixtures/"],
        cwd=REPO, capture_output=True, text=True, check=True,
    )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def test_the_cleanliness_helper_reports_a_dirty_tree(tmp_path):
    """The finalizer is only as good as its detector. Prove the detector works."""
    victim = REPO / "src" / "tolcad" / "types.py"
    original = victim.read_bytes()
    try:
        victim.write_bytes(original + b"\n# transient\n")
        assert _dirty_tracked_paths(), "detector missed a genuinely dirty tree"
    finally:
        victim.write_bytes(original)
    assert not _dirty_tracked_paths(), "detector did not clear after restore"


def test_the_tree_is_clean_right_now():
    dirty = _dirty_tracked_paths()
    assert not dirty, (
        "tracked files under src/ or tests/fixtures/ are modified. A declared "
        "mutation failed to restore. Recover with: git checkout -- src/ tests/fixtures/\n"
        + "\n".join(dirty)
    )
```

Create `tests/conftest.py`:

```python
"""Session-scoped tree-cleanliness finalizer. See tests/test_tree_cleanliness.py."""

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent


@pytest.fixture(scope="session", autouse=True)
def _fail_if_the_suite_left_the_tree_dirty():
    yield
    proc = subprocess.run(
        ["git", "status", "--porcelain", "src/", "tests/fixtures/"],
        cwd=REPO, capture_output=True, text=True,
    )
    dirty = [line for line in proc.stdout.splitlines() if line.strip()]
    if dirty:
        pytest.fail(
            "THE SUITE LEFT TRACKED FILES MODIFIED. A declared mutation did not "
            "restore. Recover with `git checkout -- src/ tests/fixtures/` and "
            "check mutation_registry.run_declared_mutation.\n" + "\n".join(dirty),
            pytrace=False,
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_tree_cleanliness.py -v`
Expected: FAIL — the files do not exist yet. Create them, then both pass. `test_the_cleanliness_helper_reports_a_dirty_tree` is the important one: it proves the detector detects, by dirtying the tree deliberately and restoring it.

- [ ] **Step 3: Merge, and add the concurrency warning**

```bash
git checkout main
git merge --ff-only feat/suite-integrity
```

Add to `CLAUDE.md` under Conventions:

```markdown
- **`pytest` mutates and restores tracked files.** The declared-mutation layer
  transiently writes to `src/tolcad/{iso286,reliability}.py`,
  `src/tolcad/gen/{sampler,layout,features}.py` and one tracked fixture, then
  restores them. **Never run `pytest` concurrently with `scripts/gate_a.py`,
  `scripts/check_suite_integrity.py`, or anything else that reads
  `src/tolcad/`** — `gate_a.py` shells out to a fresh interpreter that reads the
  checker from disk, so an overlapping run can report a Gate A number measured
  against a mutated checker. `tests/conftest.py` fails the run if the tree is
  left dirty; it cannot detect corruption that existed only *during* the run.
```

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS. Baseline on the branch was 374 passed / 2 skipped; expect +2 from this task.

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py tests/test_tree_cleanliness.py CLAUDE.md
git commit -m "feat: fail the suite if it leaves tracked files mutated"
git push origin main
```

---

