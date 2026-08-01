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
