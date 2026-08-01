"""Cross-check tolcad verdicts against the NIST MBE PMI Conformance Test Suite.

Public, authoritative, licence-free — this is the oracle that lets Gate A be cleared
without any commercial CAD licence.

Parsing the suite's STEP AP242 semantic PMI requires OCCT XCAF and happens in Phase 3.
This module only compares verdicts already extracted to CSV: part_id,assembles
"""

from __future__ import annotations

import csv
import pathlib


def load_expected(path: str | pathlib.Path) -> dict[str, bool]:
    """Read expected assembly verdicts keyed by NIST part id (e.g. FTC-06)."""
    out: dict[str, bool] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[row["part_id"]] = row["assembles"].strip().lower() == "true"
    return out


def agreement(ours: dict[str, bool], expected: dict[str, bool]) -> float:
    """Fraction of shared part ids where our verdict matches the expected one."""
    shared = set(ours) & set(expected)
    if not shared:
        raise ValueError("no overlapping part ids between the two verdict sets")
    return sum(1 for k in shared if ours[k] == expected[k]) / len(shared)


def disagreements(ours: dict[str, bool], expected: dict[str, bool]) -> list[str]:
    """Part ids where verdicts differ. Gate A requires each to be root-caused."""
    shared = set(ours) & set(expected)
    return sorted(k for k in shared if ours[k] != expected[k])
