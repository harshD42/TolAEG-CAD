"""Declared mutations: guards that have been watched failing.

WHY THIS EXISTS. This project's dominant failure mode is the test that cannot
fail -- eleven documented instances. Mutation tools (Layer 2) mutate src/ only,
so they cannot reach four of them: self-referential test constants, a corrupted
data fixture, a case-sensitive text guard, and a stale literal floor. Those live
in test code, in binary data, and in scanned prose.

What did catch all four was a manual ritual -- corrupt something, watch the
specific guard fail, revert -- performed in a shell and lost when it closed.
This module makes that ritual executable and permanent.

THE RUNNER'S OWN ANTI-VACUITY. A registry that silently patched nothing would be
a twelfth instance of the very defect it exists to catch. So the runner asserts
the anchor matches exactly once, asserts the target test PASSES before the
mutation, and asserts the file is restored byte-identically afterwards.
"""

from __future__ import annotations

import dataclasses
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_VALID_EXPECTATIONS = ("fail", "pass")


@dataclasses.dataclass(frozen=True)
class DeclaredMutation:
    """One experiment: corrupt `target`, and require `test` to react as declared.

    expect="fail" -- the guard must NOTICE this corruption. Covers insensitive,
        tautological and drifted guards.
    expect="pass" -- the result must NOT depend on this incidental choice. Covers
        seed fishing: a conclusion that held only for one lucky draw fails here.
        Asserting a test *can* fail says nothing about whether it passes for the
        right reason, which is why both directions are needed.
    """

    name: str
    target: str
    find: str
    replace: str
    test: str
    expect: str
    why: str
    binary: bool = False

    def __post_init__(self) -> None:
        if self.expect not in _VALID_EXPECTATIONS:
            raise ValueError(
                f"{self.name}: expect must be one of {_VALID_EXPECTATIONS}, "
                f"got {self.expect!r}"
            )
        if self.find == self.replace:
            raise ValueError(f"{self.name}: a no-op mutation proves nothing")


def _target_test_passes(test_selector: str) -> bool:
    """Run one test selector in a subprocess. True if it passed."""
    proc = subprocess.run(
        [
            sys.executable, "-m", "pytest", test_selector,
            "-x", "-q", "--no-header", "-p", "no:cacheprovider",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _count_and_apply(original: bytes, m: DeclaredMutation) -> tuple[int, bytes]:
    """Return (occurrences, mutated bytes).

    Text targets are matched against newline-normalised content: this repo has
    core.autocrlf=true, so tracked files are CRLF on disk and an anchor written
    with \\n would never match. The mutated file is written with LF, which is
    harmless because it exists only for the duration of one subprocess run and
    the restore is from the original bytes regardless.
    """
    if m.binary:
        find = m.find.encode("latin-1")
        replace = m.replace.encode("latin-1")
        return original.count(find), original.replace(find, replace)

    text = original.decode("utf-8").replace("\r\n", "\n")
    return text.count(m.find), text.replace(m.find, m.replace).encode("utf-8")


def run_declared_mutation(m: DeclaredMutation) -> None:
    """Perform the experiment. Raise AssertionError with a diagnosis on failure."""
    path = REPO_ROOT / m.target
    assert path.is_file(), f"{m.name}: target {m.target} does not exist"

    original = path.read_bytes()
    occurrences, mutated = _count_and_apply(original, m)

    if occurrences != 1:
        raise AssertionError(
            f"{m.name}: the patch anchor occurs {occurrences} times in "
            f"{m.target}, expected exactly 1. An anchor that matches zero times "
            f"patches nothing; one that matches many patches the wrong thing. "
            f"Either way this check would be vacuous."
        )

    if not _target_test_passes(m.test):
        raise AssertionError(
            f"{m.name}: {m.test} FAILS before any mutation is applied. "
            f"Demonstrating an outcome change from a broken baseline proves "
            f"nothing -- fix the test first."
        )

    try:
        path.write_bytes(mutated)
        passed_under_mutation = _target_test_passes(m.test)
    finally:
        path.write_bytes(original)

    if path.read_bytes() != original:
        raise AssertionError(
            f"{m.name}: {m.target} was NOT restored byte-identically. The "
            f"working tree may be corrupt -- check it before doing anything else."
        )

    if m.expect == "fail" and passed_under_mutation:
        raise AssertionError(
            f"{m.name}: {m.test} still PASSED with {m.target} corrupted. "
            f"That guard cannot detect what it exists to detect. {m.why}"
        )
    if m.expect == "pass" and not passed_under_mutation:
        raise AssertionError(
            f"{m.name}: {m.test} FAILED under a mutation it should survive. "
            f"The result depends on an incidental choice. {m.why}"
        )


REGISTRY: tuple[DeclaredMutation, ...] = (
    DeclaredMutation(
        name="it7-row-transposed",
        target="src/tolcad/iso286.py",
        find="    7: [10, 12, 15, 18, 21, 25, 30, 35, 40, 46, 52, 57, 63],",
        replace="    7: [10, 12, 15, 18, 21, 30, 25, 35, 40, 46, 52, 57, 63],",
        test="tests/test_iso286.py::test_all_52_it5_to_it8_cells_match_iso286_table_1",
        expect="fail",
        why=(
            "IT7 feeds the Tier 2 iso_fit yields through fit_from_designation, "
            "so a corrupted cell moves published numbers, not documentation."
        ),
    ),
    DeclaredMutation(
        name="zeroed-wall-margin",
        target="src/tolcad/gen/layout.py",
        find="\n_MIN_WALL_MM = 4.0",
        replace="\n_MIN_WALL_MM = 0.0",
        test="tests/gen/test_layout.py::test_the_margin_constants_are_actually_large_enough",
        expect="fail",
        why=(
            "A zero wall makes adjacent holes exactly tangent. The containment "
            "test cannot see it either, because tangency has zero intersection "
            "volume, so this is the only guard standing between a zeroed "
            "constant and a degenerate B-rep in the reference geometry."
        ),
    ),
)
