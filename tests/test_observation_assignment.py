"""The stopping criterion is only usable if its worked table is committed.

The observation-assignment table is what makes R2 -- "a control needs its own
control ONLY IF its failure is a silent false green AND none of O-A..O-D
reveals it" -- a rule a reader can APPLY rather than merely read. Until this
task it existed only in an agent transcript: the *Unencoded* shape from the
design spec's own taxonomy ("the verification happened but left no guard"),
identical in kind to a 39-cell IT table check run once in a shell and never
committed.

These tests do not merely assert the file exists. They assert the table can
still do the job: every listed control carries a verdict, and every verdict
names the observation that decides it. A table whose "needs its own control?"
column said "yes"/"no" with no observation named would be decoration, and
would pass a bare existence check.
"""

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOC = (
    REPO_ROOT / "docs" / "superpowers" / "specs"
    / "2026-08-01-observation-assignment.md"
)
# The ledger reconciliation must live in a TRACKED file. `.superpowers/sdd/`
# carries its own `.gitignore` containing `*`, so every SDD progress ledger is
# deliberately untracked; a canonical value recorded only there would satisfy
# nothing Gate D can audit from a clone.
RECONCILIATION = (
    REPO_ROOT / "docs" / "superpowers" / "specs"
    / "2026-08-01-ledger-reconciliation.md"
)

# One key per quantity the ledgers contradict themselves on.
CONTESTED = (
    "pre-fix d4",
    "Tier 1 ladder",
    "untriaged survivors",
    "branch coverage",
    "mutation score",
    "reliability mean",
    "instance count",
)

OBSERVATIONS = ("O-A", "O-B", "O-C", "O-D")
RULES = ("R1", "R2", "R3", "R4", "R5", "R6")

# One key per control the close-out plan requires an assignment for. Each must
# match the FIRST cell of exactly one row of the worked table.
CONTROL_KEYS = (
    "run_declared_mutation",
    "test_the_registry_still_covers_every_critical_guard",
    "B2",
    "B3",
    "re-run-and-compare",
    "B10",
    "B9",
    "ladder pin",
    "mate[8]",
    "mutual exclusion",
)


def _doc_text() -> str:
    assert DOC.is_file(), (
        f"{DOC} does not exist. The observation-assignment table exists only "
        f"in an agent transcript -- the Unencoded shape from the design "
        f"spec's own taxonomy, one session expiry from gone."
    )
    return DOC.read_text(encoding="utf-8")


def _worked_rows() -> list[list[str]]:
    """Every 4-cell body row of the worked assignment table.

    Header and separator rows are dropped by requiring a first cell that is
    neither empty nor made only of dashes/colons.
    """
    rows = []
    for line in _doc_text().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 4:
            continue
        if not cells[0] or set(cells[0]) <= set("-: "):
            continue
        if cells[0].lower().startswith("control"):
            continue
        rows.append(cells)
    return rows


def test_the_observation_table_is_committed():
    assert DOC.is_file(), (
        "the observation-assignment table exists only in a transcript. That is "
        "the Unencoded shape from the design spec's own taxonomy."
    )


def test_every_observation_and_rule_is_defined():
    text = _doc_text()
    for obs in OBSERVATIONS:
        assert obs in text, f"{obs} is not defined"
    for rule in RULES:
        assert rule in text, f"{rule} is not stated"
    assert "silent false green" in text.lower(), (
        "R2's trigger condition is the phrase the whole table turns on"
    )


@pytest.mark.parametrize("key", CONTROL_KEYS)
def test_every_named_control_has_exactly_one_assignment_row(key):
    matches = [r for r in _worked_rows() if key in r[0]]
    assert len(matches) == 1, (
        f"no unique observation assignment for {key!r}: matched "
        f"{len(matches)} rows of the worked table"
    )


def test_every_row_names_the_observation_that_decides_it():
    """R2 is only checkable if each verdict cites an observation.

    A verdict of bare "no" is unfalsifiable: it does not say WHICH observation
    would have caught the defect, so a reader cannot audit it and a proposer of
    a new control cannot be held to naming the observation that fails.
    """
    rows = _worked_rows()
    assert rows, "the worked table has no body rows"
    for control, _failure, revealed, verdict in rows:
        assert any(o in revealed for o in OBSERVATIONS) or "none" in revealed.lower(), (
            f"row {control!r}: the 'revealed by' cell names no observation and "
            f"does not say 'none'"
        )
        assert verdict.lower().startswith(("yes", "no")), (
            f"row {control!r}: verdict {verdict!r} must start Yes or No"
        )
        assert any(o in verdict for o in OBSERVATIONS), (
            f"row {control!r}: verdict {verdict!r} names no observation. R2 "
            f"requires naming the observation that reveals the defect (No) or "
            f"the fact that none does (Yes)."
        )


def test_the_mutual_exclusion_row_is_justified_by_O_B_being_blind():
    """The one case the criterion demanded of its own author.

    Task 9's control is justified precisely because O-B cannot see it: the tree
    is clean AFTER the run, while the corruption exists only DURING it. If the
    table cannot reproduce that reasoning it does not work.
    """
    rows = [r for r in _worked_rows() if "mutual exclusion" in r[0]]
    assert len(rows) == 1
    _control, failure, revealed, verdict = rows[0]
    assert verdict.lower().startswith("yes"), (
        "the mutual-exclusion control is the case R2 forces; the table must "
        "say so"
    )
    assert "O-B" in (failure + revealed + verdict), (
        "the justification is specifically that O-B is structurally blind here"
    )
    assert "none" in (revealed + verdict).lower(), (
        "R2 admits a new control only when NONE of O-A..O-D reveals the defect"
    )


# --- the ledger reconciliation ----------------------------------------------


def _reconciliation_text() -> str:
    assert RECONCILIATION.is_file(), (
        f"{RECONCILIATION} does not exist. Gate D requires every claim "
        f"traceable to a logged run, and the SDD ledgers disagree with "
        f"themselves on nearly every quantity. They are also gitignored, so "
        f"the canonical values must be recorded somewhere a clone can see."
    )
    return RECONCILIATION.read_text(encoding="utf-8")


@pytest.mark.parametrize("quantity", CONTESTED)
def test_each_contested_quantity_has_exactly_one_canonical_value(quantity):
    """Two canonical values is the defect, not the fix.

    The reconciliation records one CANONICAL line per contested quantity and
    marks every other recorded figure SUPERSEDED. A second CANONICAL line for
    the same quantity would recreate the contradiction in the one file that
    exists to resolve it.
    """
    text = _reconciliation_text()
    blocks = [b for b in text.split("\n### ") if b.startswith(quantity)]
    assert len(blocks) == 1, (
        f"expected exactly one '### {quantity}' section, found {len(blocks)}"
    )
    body = blocks[0]
    canonical = [
        ln for ln in body.splitlines()
        if ln.strip().startswith("- **CANONICAL")
    ]
    assert len(canonical) == 1, (
        f"{quantity!r} has {len(canonical)} CANONICAL lines; exactly one is "
        f"the whole point"
    )
    assert "SUPERSEDED" in body or "no other value" in body, (
        f"{quantity!r} records a canonical value but does not say what it "
        f"supersedes; the contradictory figures stay live in a grep"
    )


def test_the_reconciliation_does_not_claim_the_ledgers_were_rewritten():
    """The ledgers are frozen contemporaneous records; their value IS that.

    Reconciliation is additive. If this document ever describes editing the
    original lines, the provenance it exists to protect is gone.
    """
    text = _reconciliation_text().lower()
    assert "not rewritten" in text or "append-only" in text, (
        "the reconciliation must state that the original ledger lines stand"
    )


def _bullets(text: str) -> list[str]:
    """Split markdown list items, keeping wrapped continuation lines together."""
    items: list[str] = []
    for line in text.splitlines():
        if line.startswith("- ") or line.startswith("#"):
            items.append(line)
        elif items and line.startswith("  "):
            items[-1] += " " + line.strip()
        else:
            items.append(line)
    return items


def test_every_canonical_value_cites_its_provenance():
    """A canonical value with no source is an assertion, not a reconciliation."""
    bullets = [
        b for b in _bullets(_reconciliation_text())
        if b.strip().startswith("- **CANONICAL")
    ]
    assert len(bullets) == len(CONTESTED), (
        f"found {len(bullets)} canonical bullets for {len(CONTESTED)} "
        f"contested quantities"
    )
    for bullet in bullets:
        assert "provenance:" in bullet.lower(), (
            f"canonical entry cites no provenance: {bullet!r}"
        )

