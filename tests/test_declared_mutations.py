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
