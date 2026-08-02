"""Executes every declared mutation. See tests/mutation_registry.py.

Each entry is an experiment: corrupt something specific, and require a specific
test to notice (or, for expect="pass", to be unmoved). This is the automation of
a practice that was previously manual and evaporated with the shell session.
"""

import pathlib
import subprocess
import sys

import pytest

from tests import mutation_registry
from tests.mutation_registry import (
    MUTATION_LOCK,
    REGISTRY,
    REPO_ROOT,
    DeclaredMutation,
    _write_bytes_resiliently,
    mutation_lock,
    run_declared_mutation,
)


@pytest.mark.mutation
@pytest.mark.parametrize("declared", REGISTRY, ids=lambda m: m.name)
def test_declared_mutation_behaves_as_declared(declared: DeclaredMutation):
    run_declared_mutation(declared)


def test_a_no_op_patch_is_rejected():
    """An anchor that does not appear patches nothing and proves nothing."""
    bogus = DeclaredMutation(
        name="bogus-anchor",
        target="src/tolcad/types.py",
        find="THIS STRING DOES NOT APPEAR ANYWHERE IN THE FILE",
        replace="neither does this",
        test="tests/test_types.py",
        expect="fail",
        why="fixture for the runner's own guard",
    )
    with pytest.raises(AssertionError, match="occurs 0 times"):
        run_declared_mutation(bogus)


def test_an_ambiguous_patch_is_rejected():
    """A repeated anchor would patch every occurrence -- not the declared one.

    'EPS' appears many times in types.py. This is not hypothetical: the first
    anchor tried for _MIN_WALL_MM matched twice, once in a docstring.
    """
    ambiguous = DeclaredMutation(
        name="ambiguous-anchor",
        target="src/tolcad/types.py",
        find="float",
        replace="int",
        test="tests/test_types.py",
        expect="fail",
        why="fixture for the runner's own guard",
    )
    with pytest.raises(AssertionError, match=r"occurs \d+ times"):
        run_declared_mutation(ambiguous)


def test_a_transient_write_failure_is_retried_then_succeeds(tmp_path, monkeypatch):
    """The restore write must survive a transient OSError, not give up on it.

    This is not hypothetical: a single `OSError: [Errno 22] Invalid argument`
    on the restore write left src/tolcad/reliability.py mutated in the working
    tree on 2026-08-01.
    """
    monkeypatch.setattr(mutation_registry, "_WRITE_BACKOFF_S", 0.0)
    target = tmp_path / "f.bin"
    real_write = pathlib.Path.write_bytes
    calls = {"n": 0}

    def flaky(self, data):
        calls["n"] += 1
        if calls["n"] < 3:
            raise OSError(22, "Invalid argument")
        return real_write(self, data)

    monkeypatch.setattr(pathlib.Path, "write_bytes", flaky)
    _write_bytes_resiliently(target, b"restored")
    monkeypatch.undo()

    assert calls["n"] == 3
    assert target.read_bytes() == b"restored"


def test_a_persistent_write_failure_is_raised_not_swallowed(tmp_path, monkeypatch):
    """A tree left mutated must be loud. Silently returning would be the worst
    outcome this whole module exists to prevent."""
    monkeypatch.setattr(mutation_registry, "_WRITE_BACKOFF_S", 0.0)

    def always_fails(self, data):
        raise OSError(22, "Invalid argument")

    monkeypatch.setattr(pathlib.Path, "write_bytes", always_fails)
    with pytest.raises(OSError):
        _write_bytes_resiliently(tmp_path / "f.bin", b"x")


def test_an_invalid_expectation_is_rejected():
    with pytest.raises(ValueError, match="expect"):
        DeclaredMutation(
            name="bad-expect", target="src/tolcad/types.py", find="a",
            replace="b", test="tests/test_types.py", expect="maybe", why="x",
        )


def test_a_mutation_that_changes_nothing_is_rejected():
    with pytest.raises(ValueError, match="no-op"):
        DeclaredMutation(
            name="no-op", target="src/tolcad/types.py", find="same",
            replace="same", test="tests/test_types.py", expect="fail", why="x",
        )


# Guards that protect a number reaching the paper. An entry may be edited, but
# deleting one must not be a quiet way to make a failure go away.
_CRITICAL_GUARDS = frozenset({
    "it7-row-transposed",
    "it-grade-set-widened",
    "flat-difficulty-ladder",
    "ladder-d2-row-shifted",
    "zeroed-wall-margin",
    "stale-literal-wall-floor",
    "crlf-corrupted-nist-fixture",
    "m12-clearance-diameter",
    "fastener-upper-dev-nonzero",
    "mc-seed-base-shifted",
    # Instances 2 and 4. The design spec's Layer 3 seed table named a
    # `reliability` entry; the plan silently substituted another and left both
    # instances covered by nothing until this was caught in review.
    "reliability-perturbation-neutered",
    "reliability-perturbation-tripled",
    "tapped-hole-upper-dev-nonzero",
    "case-sensitive-guard-uppercased",
    # 2026-08-01g. Spec section 7's criterion 1 is a Gate A verdict and
    # therefore a published number under R1. It had no guard at all while the
    # harness reported "Y14.5 self-consistency" in its place.
    "y14-5-worked-example-boundary-shifted",
})


def test_the_registry_still_covers_every_critical_guard():
    """An entry must not be deletable to silence a failure.

    KNOWN LIMIT -- READ THIS BEFORE RELYING ON IT. This is a PAPER-TRAIL
    mechanism, not a technical guarantee. It catches deleting an entry from
    REGISTRY alone; it is defeated by a single commit that removes the entry
    AND its name from _CRITICAL_GUARDS above. Nothing here can prevent that,
    because _CRITICAL_GUARDS lives in the same file and the same review.
    What it buys is that the deletion has to be explicit and shows up in the
    diff next to this comment, so it cannot happen by accident or by silence.
    This is design spec section 9's open question, stated plainly rather than
    left for a future reader to rediscover as a surprise.

    Related and equally uncovered: nothing forces a NEW guard to be
    registered, so a future test protecting a new published number could be
    added with no entry and no layer would notice.
    """
    present = {m.name for m in REGISTRY}
    missing = _CRITICAL_GUARDS - present
    assert not missing, (
        f"declared mutations were removed: {sorted(missing)}. If a guard is "
        f"genuinely obsolete, remove it from _CRITICAL_GUARDS in the same "
        f"commit and say why."
    )


def test_both_expectation_directions_are_exercised():
    """expect="pass" is what catches seed fishing; losing it loses that class."""
    directions = {m.expect for m in REGISTRY}
    assert directions == {"fail", "pass"}, (
        f"registry only exercises {directions}. Asserting a guard CAN fail says "
        f"nothing about whether a passing result passes for the right reason."
    )


def test_every_registry_name_is_unique():
    names = [m.name for m in REGISTRY]
    assert len(names) == len(set(names))


def test_every_registry_entry_names_a_single_test():
    """A whole-file selector can pass because some unrelated test failed."""
    for m in REGISTRY:
        assert "::" in m.test, (
            f"{m.name} targets '{m.test}', a whole file. Name the specific test, "
            f"or the entry can be satisfied by an unrelated failure."
        )


def test_text_targets_have_a_known_safe_suffix():
    """A line-ending-sensitive target declared as text fails for the wrong reason.

    _count_and_apply normalises CRLF->LF across the whole file for text targets.
    That is harmless for Python and Markdown; it is not harmless in general.
    """
    safe = {".py", ".md", ".toml", ".yml", ".yaml", ".cfg"}
    for m in REGISTRY:
        if m.binary:
            continue
        suffix = pathlib.Path(m.target).suffix
        assert suffix in safe, (
            f"{m.name} targets {m.target} as TEXT, but {suffix} is not in the "
            f"known-safe set {sorted(safe)}. Declare it binary=True."
        )


# --- mutual exclusion between this layer and readers of src/ ----------------
#
# The two scripts guarded here. check_suite_integrity.py is invoked with
# --self-test-failure DELIBERATELY: the guard is the first statement in main(),
# before the argv branch, so the same code path is exercised -- but if the guard
# were absent or misplaced, the plain invocation would spend ~25 minutes running
# cosmic-ray before this test could fail. The self-test path returns in under a
# second, so a broken guard shows up as a wrong exit code, not as a hung suite.
_READERS = (
    ("scripts/gate_a.py", ("scripts/gate_a.py",)),
    (
        "scripts/check_suite_integrity.py",
        ("scripts/check_suite_integrity.py", "--self-test-failure"),
    ),
)

# Distinct from both scripts' meaningful codes (0 = cleared/OK, 1 = a criterion
# or a pin failed). A refusal must not be mistakable for a measured failure.
_LOCK_HELD_EXIT = 2


def _run_reader(argv: tuple[str, ...]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *argv],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=600,
    )


def test_a_reader_refuses_to_run_while_a_mutation_is_in_flight():
    """O-B cannot see this: the tree is clean AFTER the run, and the corruption
    exists only DURING it.

    gate_a.py shells out to a fresh interpreter that reads the checker core from
    disk, so a run overlapping `reliability-perturbation-tripled` reports a Gate A
    number measured against a mutated checker -- a silent false green. The
    observation-assignment spec's table gives this row "revealed by: none", which
    is what forces a control (R2), and rules out a CLAUDE.md warning as one (R5).

    Written so it cannot pass vacuously: a missing guard leaves gate_a.py exiting
    1 (it exits 1 on the clean tree too, because SKIP rows remain), so the exit
    code is pinned EXACTLY to the refusal code rather than to `!= 0`.
    """
    assert not MUTATION_LOCK.exists(), (
        f"{MUTATION_LOCK} already exists before the lock is taken. Either a run "
        f"was killed mid-mutation or something else creates this file; this test "
        f"cannot distinguish its own lock from a pre-existing one."
    )

    results = {}
    with mutation_lock():
        assert MUTATION_LOCK.exists(), (
            "mutation_lock() did not create the lock file, so the refusals below "
            "would prove nothing about mutual exclusion"
        )
        for name, argv in _READERS:
            results[name] = _run_reader(argv)

    assert not MUTATION_LOCK.exists(), "the lock must clear even on the happy path"

    for name, proc in results.items():
        combined = proc.stdout + proc.stderr
        assert proc.returncode == _LOCK_HELD_EXIT, (
            f"{name} exited {proc.returncode} with the lock held; expected "
            f"{_LOCK_HELD_EXIT}. A reader that merely fails for its usual reason "
            f"is indistinguishable from one that refused.\n{combined}"
        )
        assert "mutation" in combined.lower(), (
            f"{name} refused without saying why:\n{combined}"
        )
        assert "REFUSING TO RUN" in combined, (
            f"{name} did not print the refusal banner:\n{combined}"
        )
        # The refusal must land before any measurement work, not after it.
        assert "Gate A -" not in proc.stdout, f"{name} measured anyway:\n{proc.stdout}"
        assert "Suite integrity -" not in proc.stdout, (
            f"{name} measured anyway:\n{proc.stdout}"
        )
        # A stale lock (a run killed mid-mutation) blocks every later run, so the
        # message has to be a recovery procedure and not just "wait".
        lowered = combined.lower()
        assert "stale" in lowered, (
            f"{name}'s refusal does not mention the stale-lock case. 'Wait for "
            f"the suite to finish' is wrong advice when nothing is "
            f"running:\n{combined}"
        )
        assert "git checkout" in lowered and "git status" in lowered, (
            f"{name}'s refusal does not tell a human how to recover from a stale "
            f"lock (check the tree, restore any leftover mutant, delete the "
            f"lock):\n{combined}"
        )


def test_the_lock_clears_when_the_body_raises():
    """A lock leaked by an exception blocks every later Gate A run.

    `seen` is not decoration: without it this test passes against a
    `mutation_lock` that never creates the file at all, which is the project's
    dominant failure mode (a test that cannot fail) reproduced inside the control
    built to close one.
    """
    seen = {}
    with pytest.raises(RuntimeError, match="boom"):
        with mutation_lock():
            seen["held"] = MUTATION_LOCK.exists()
            raise RuntimeError("boom")

    assert seen["held"], (
        "the lock was never taken, so its absence afterwards proves nothing"
    )
    assert not MUTATION_LOCK.exists(), "a stale lock would block every later run"


def test_the_runner_holds_the_lock_across_mutate_run_and_restore(monkeypatch):
    """A lock taken and dropped before the restore leaves the race wide open.

    Observed from inside the runner rather than read off its source. An earlier
    draft of this test compared the character offsets of `with mutation_lock():`
    and the mutating write in the module text, and it PASSED against a runner
    rewritten as `with mutation_lock(): pass` followed by an unprotected
    mutate/run/restore -- a test that cannot fail, inside the control added to
    close one. Offsets cannot see block structure; sampling the lock at each
    write can.

    Nothing is written and no test is spawned: `_write_bytes_resiliently` and
    `_target_test_passes` are both replaced by recorders, so the probe reads the
    real runner's control flow without touching src/ at all.
    """
    probe = next(m for m in REGISTRY if m.name == "zeroed-wall-margin")
    target = REPO_ROOT / probe.target
    before = target.read_bytes()

    lock_at_write: list[bool] = []
    lock_at_test: list[bool] = []

    def recording_write(path, data):
        lock_at_write.append(MUTATION_LOCK.exists())  # deliberately does not write

    def recording_test(selector):
        lock_at_test.append(MUTATION_LOCK.exists())
        # True for the pre-mutation baseline, False afterwards, so this
        # expect="fail" entry is satisfied and the runner returns normally.
        return len(lock_at_test) == 1

    monkeypatch.setattr(mutation_registry, "_write_bytes_resiliently", recording_write)
    monkeypatch.setattr(mutation_registry, "_target_test_passes", recording_test)

    run_declared_mutation(probe)

    assert lock_at_write == [True, True], (
        f"the lock was not held at both writes (mutate, restore): {lock_at_write}. "
        f"A window in which a src/ file is mutated and the lock is not held is "
        f"exactly the race this control exists to close."
    )
    assert lock_at_test[1:] == [True], (
        f"the lock was not held while the mutated tree was under test: {lock_at_test}"
    )
    assert not MUTATION_LOCK.exists(), "the runner must not leave the lock behind"
    assert target.read_bytes() == before, "the probe must not touch the tree"
