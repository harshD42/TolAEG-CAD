"""Executes every declared mutation. See tests/mutation_registry.py.

Each entry is an experiment: corrupt something specific, and require a specific
test to notice (or, for expect="pass", to be unmoved). This is the automation of
a practice that was previously manual and evaporated with the shell session.
"""

import pytest

from tests.mutation_registry import REGISTRY, DeclaredMutation, run_declared_mutation


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
    "zeroed-wall-margin",
    "stale-literal-wall-floor",
    "crlf-corrupted-nist-fixture",
    "m12-clearance-diameter",
    "fastener-upper-dev-nonzero",
    "mc-seed-base-shifted",
})


def test_the_registry_still_covers_every_critical_guard():
    """An entry must not be deletable to silence a failure."""
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
