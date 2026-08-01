"""The four numbers pre-registration will freeze, pinned as exact counts.

O-C. Rates alone are insufficient: a rate is a ratio and hides a change in the
denominator. The counts are what a third party reproduces.
"""

import numpy as np
import pytest

from scripts.measure_ladder import LADDER_RECIPE, corpus_digest, measure_ladder

# Measured 2026-08-01 on numpy 2.4.1 over seeds 0-199. See D-C: the numpy
# version is pinned because Generator's stream is NOT covered by NEP 19.
EXPECTED_COUNTS = {1: (31, 159), 2: (99, 301), 3: (239, 452), 4: (421, 609)}
EXPECTED_DIGEST = (
    "c035c2d99d377c1f1c6f912c9c690e47376e012eee37f4283c41de0051336fa3"
)


@pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
def test_each_ladder_level_matches_its_exact_pinned_counts(difficulty):
    failures, total = measure_ladder()[difficulty]
    exp_f, exp_t = EXPECTED_COUNTS[difficulty]
    assert (failures, total) == (exp_f, exp_t), (
        f"d{difficulty} measured {failures}/{total}, pinned {exp_f}/{exp_t}. "
        f"numpy=={np.__version__} (pinned 2.4.1; Generator's stream is not "
        f"guaranteed across releases). If this is an intended change, re-measure "
        f"ALL FOUR levels and re-pin -- and note the pre-registration freezes them."
    )


def test_the_corpus_digest_is_reproducible():
    assert corpus_digest() == EXPECTED_DIGEST, (
        f"the corpus changed. Recipe: {LADDER_RECIPE}"
    )
