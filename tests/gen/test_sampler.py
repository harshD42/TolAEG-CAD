import pytest
from tolcad.checker import check
from tolcad.gen.sampler import sample_assembly


def test_same_seed_gives_identical_spec():
    assert sample_assembly(7, 2) == sample_assembly(7, 2)


def test_different_seeds_give_different_specs():
    specs = {sample_assembly(s, 2).to_json() for s in range(20)}
    assert len(specs) > 1, "sampler is ignoring the seed"


def test_difficulty_controls_mate_count_and_is_capped_at_four():
    for difficulty in (1, 2, 3, 4):
        spec = sample_assembly(0, difficulty)
        assert len(spec.mates) == difficulty
    # spec section 4.1 caps the tolerance loop at 4 contributors
    with pytest.raises(ValueError, match="difficulty"):
        sample_assembly(0, 5)


def test_every_generated_mate_is_checkable():
    """The generator must never emit a mate the checker rejects."""
    for seed in range(50):
        for difficulty in (1, 2, 3, 4):
            for mate in sample_assembly(seed, difficulty).mates:
                verdict = check(mate.to_check_dict())
                assert isinstance(verdict.assembles, bool)


def test_corpus_contains_both_passing_and_failing_mates():
    """A generator that only produces assemblable parts measures nothing.

    Guards the failure mode this project has hit repeatedly: a fixture that
    cannot exercise the negative branch.
    """
    verdicts = [
        check(m.to_check_dict()).assembles
        for seed in range(80)
        for m in sample_assembly(seed, 3).mates
    ]
    assert any(verdicts), "no assemblable mates generated"
    assert not all(verdicts), "no non-assemblable mates generated"


def test_seed_and_difficulty_are_recorded_in_the_spec():
    spec = sample_assembly(13, 3)
    assert spec.seed == 13
    assert spec.difficulty == 3
