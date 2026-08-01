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
