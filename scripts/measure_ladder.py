#!/usr/bin/env python
"""Reproduce the pre-registered difficulty ladder and the corpus digest.

WHY THIS EXISTS. The four ladder rates appeared in five ledgers and would have
gone into the pre-registration, but no script produced them and no test pinned
them. A pre-registered number that no executable artifact reproduces is
unverifiable, which is the purest form of this project's dominant failure mode.

Usage: python scripts/measure_ladder.py
"""

from __future__ import annotations

import hashlib
import json

from tolcad.checker import check
from tolcad.gen.sampler import sample_assembly

# The recipe, written down so the digest means something. Changing any element
# changes the digest by design.
LADDER_RECIPE = {
    "seeds": "range(0, 200)",
    "difficulties": [1, 2, 3, 4],
    "counted": "Tier 1 mates only (kind != 'iso_fit')",
    "statistic": "check(mate.to_check_dict()).assembles is False",
}


def measure_ladder() -> dict[int, tuple[int, int]]:
    """Return {difficulty: (tier1_failures, tier1_total)} over seeds 0-199."""
    out: dict[int, tuple[int, int]] = {}
    for difficulty in LADDER_RECIPE["difficulties"]:
        failures = total = 0
        for seed in range(200):
            for mate in sample_assembly(seed, difficulty).mates:
                if mate.kind == "iso_fit":
                    continue
                total += 1
                if not check(mate.to_check_dict()).assembles:
                    failures += 1
        out[difficulty] = (failures, total)
    return out


def corpus_digest() -> str:
    """SHA-256 over every sampled spec, in a defined order."""
    hasher = hashlib.sha256()
    for difficulty in LADDER_RECIPE["difficulties"]:
        for seed in range(200):
            hasher.update(sample_assembly(seed, difficulty).to_json().encode("utf-8"))
    return hasher.hexdigest()


def main() -> int:
    counts = measure_ladder()
    for difficulty, (failures, total) in sorted(counts.items()):
        print(f"  d{difficulty}: {failures}/{total} = {100 * failures / total:.2f}% fail")
    print(f"  corpus digest: {corpus_digest()}")
    print(f"  recipe: {json.dumps(LADDER_RECIPE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
