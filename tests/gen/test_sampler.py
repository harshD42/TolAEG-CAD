import pytest
from tolcad.checker import check
from tolcad.gen.sampler import MAX_DIFFICULTY, _mc_seed_for, sample_assembly

_GUARD_SEEDS = 80
_DIFFICULTIES = tuple(range(1, MAX_DIFFICULTY + 1))


def _tier1_verdicts(difficulty: int, seeds: int = _GUARD_SEEDS) -> list[bool]:
    """assembles verdicts for the TIER 1 mates only.

    Filtering out iso_fit is the whole point. The previous version of the guard
    below pooled both tiers, and its two assertions were satisfied entirely by
    iso_fit mates -- so it passed against a Tier 1 sampler that produced zero
    failures at three of the four difficulty levels, and passed just as happily
    when the ladder was mutated to a flat range or to constants of 0.0 and 5.0.
    """
    return [
        check(m.to_check_dict()).assembles
        for seed in range(seeds)
        for m in sample_assembly(seed, difficulty).mates
        if m.kind != "iso_fit"
    ]


def test_same_seed_gives_identical_spec():
    assert sample_assembly(7, 2) == sample_assembly(7, 2)


def test_different_seeds_give_different_specs():
    specs = {sample_assembly(s, 2).to_json() for s in range(20)}
    assert len(specs) > 1, "sampler is ignoring the seed"


def test_difficulty_controls_mate_count_and_is_capped_at_four():
    for difficulty in _DIFFICULTIES:
        spec = sample_assembly(0, difficulty)
        assert len(spec.mates) == difficulty
    # spec section 4.1 caps the tolerance loop at 4 contributors
    with pytest.raises(ValueError, match="difficulty"):
        sample_assembly(0, 5)


def test_every_generated_mate_is_checkable():
    """The generator must never emit a mate the checker rejects."""
    for seed in range(50):
        for difficulty in _DIFFICULTIES:
            for mate in sample_assembly(seed, difficulty).mates:
                verdict = check(mate.to_check_dict())
                assert isinstance(verdict.assembles, bool)


@pytest.mark.parametrize("difficulty", _DIFFICULTIES)
def test_tier1_corpus_contains_both_passing_and_failing_mates(difficulty):
    """A difficulty level whose Tier 1 mates all assemble measures nothing.

    At such a level "always answer assembles" scores 100% on Tier 1, which is
    exactly the degeneracy this project keeps producing. EVERY level has to
    exercise both branches, not just the corpus as a whole, and it has to do so
    with Tier 1 mates -- iso_fit is Tier 2 and is graded by a different module.
    """
    verdicts = _tier1_verdicts(difficulty)
    assert verdicts, f"d{difficulty} produced no Tier 1 mates at all"
    assert any(verdicts), f"d{difficulty}: no assemblable Tier 1 mates"
    assert not all(verdicts), f"d{difficulty}: no non-assemblable Tier 1 mates"


def test_tier1_failure_rate_rises_monotonically_with_difficulty():
    """Difficulty must actually mean something. Nothing else asserts that.

    The applied position tolerance is allowable * f, so the Y14.5 margin is
    allowable * (1 - f) floating and allowable * (1 - mean(f_a, f_b)) fixed.
    A ladder capped at f <= 1 makes every margin non-negative by construction;
    a flat ladder makes every level identical. Both are ruled out here.
    """
    rates = []
    for difficulty in _DIFFICULTIES:
        verdicts = _tier1_verdicts(difficulty)
        rates.append(1.0 - sum(verdicts) / len(verdicts))

    assert all(later > earlier for earlier, later in zip(rates, rates[1:])), (
        f"Tier 1 failure rate is not strictly increasing in difficulty: {rates}"
    )
    # Pin the ends of the ladder too, so a future edit cannot satisfy the
    # monotonicity above with a degenerate 0.1% -> 0.2% ramp.
    assert 0.10 <= rates[0] <= 0.30, f"d1 failure rate {rates[0]:.3f} off the ladder"
    assert 0.60 <= rates[-1] <= 0.80, f"d4 failure rate {rates[-1]:.3f} off the ladder"


def test_seed_and_difficulty_are_recorded_in_the_spec():
    spec = sample_assembly(13, 3)
    assert spec.seed == 13
    assert spec.difficulty == 3


def test_iso_fit_mates_carry_an_explicit_reproducible_monte_carlo_seed():
    """Tier 2 labels ride on the sampling seed, so the seed must be in the spec.

    Without this the checker silently fell back to seed=0 and every H7/h6 mate
    in the corpus took whichever label seed 0 happened to produce.
    """
    seen = 0
    for seed in range(40):
        for difficulty in _DIFFICULTIES:
            spec = sample_assembly(seed, difficulty)
            for index, mate in enumerate(spec.mates):
                if mate.kind != "iso_fit":
                    continue
                seen += 1
                assert mate.mc_seed == _mc_seed_for(seed, index)
                assert mate.mc_seed != 0, "0 is the checker's fallback, not a choice"
                assert mate.mc_n > 0
                # The seed must reach the Monte Carlo, not just sit in the spec.
                assert check(mate.to_check_dict()).detail["seed"] == mate.mc_seed
    assert seen > 0, "no iso_fit mates sampled; this guard checked nothing"


def test_monte_carlo_seeds_are_unique_within_an_assembly():
    for seed in range(40):
        spec = sample_assembly(seed, MAX_DIFFICULTY)
        iso_seeds = [m.mc_seed for m in spec.mates if m.kind == "iso_fit"]
        assert len(iso_seeds) == len(set(iso_seeds))


def test_fixed_fasteners_get_a_tapped_hole_b_and_floating_ones_do_not():
    """Guards I4: identical geometry for two kinds with different formulas.

    Before this, hole_a and hole_b carried the same clearance diameter for
    both kinds, so the exported STEP could not express which formula applied.
    """
    seen_fixed = seen_floating = 0
    for seed in range(60):
        for difficulty in (1, 2, 3, 4):
            for mate in sample_assembly(seed, difficulty).mates:
                if mate.kind == "fixed_fastener":
                    seen_fixed += 1
                    assert mate.hole_b["nominal"] < mate.nominal_mm, (
                        "a fixed fastener's hole_b must be tapped, i.e. smaller "
                        "than the fastener"
                    )
                elif mate.kind == "floating_fastener":
                    seen_floating += 1
                    assert mate.hole_b["nominal"] > mate.nominal_mm, (
                        "a floating fastener's hole_b must be a clearance hole"
                    )
    assert seen_fixed > 0 and seen_floating > 0, "corpus lacks one of the kinds"


def test_a_fixed_mate_is_structurally_not_a_floating_mate():
    """The geometry itself now encodes which formula applies.

    A tapped hole_b cannot pass the fastener, so submitting a fixed mate as
    floating raises. That is the invariant making the two kinds learnable.
    """
    fixed = next(
        m for seed in range(60)
        for m in sample_assembly(seed, 4).mates
        if m.kind == "fixed_fastener"
    )
    as_floating = dict(fixed.to_check_dict(), type="floating_fastener")
    with pytest.raises(ValueError, match="hole_b MMC"):
        check(as_floating)
