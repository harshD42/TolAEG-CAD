"""Cross-check tolcad verdicts against SolidWorks TolAnalyst.

TolAnalyst is treated strictly as a black-box oracle: this module ingests a CSV of
verdicts produced by a separate manual export and compares them to ours. It does not
wrap, automate, or document any SolidWorks internals.

CSV format: assembly_id,assembles
"""

from __future__ import annotations

import csv
import pathlib


def load_verdicts(path: str | pathlib.Path) -> dict[str, bool]:
    """Read exported TolAnalyst verdicts keyed by assembly id."""
    out: dict[str, bool] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[row["assembly_id"]] = row["assembles"].strip().lower() == "true"
    return out


def agreement(ours: dict[str, bool], theirs: dict[str, bool]) -> float:
    """Fraction of shared assembly ids where the two verdicts match."""
    shared = set(ours) & set(theirs)
    if not shared:
        raise ValueError("no overlapping assembly ids between the two verdict sets")
    matches = sum(1 for k in shared if ours[k] == theirs[k])
    return matches / len(shared)


def disagreements(ours: dict[str, bool], theirs: dict[str, bool]) -> list[str]:
    """Assembly ids where verdicts differ. Gate A requires each to be root-caused."""
    shared = set(ours) & set(theirs)
    return sorted(k for k in shared if ours[k] != theirs[k])
