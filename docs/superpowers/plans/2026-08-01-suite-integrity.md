# Suite Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make "this test cannot fail" a condition the repository detects mechanically, before it reaches a published number.

**Architecture:** Three layers, each owning a defect class the others structurally cannot reach. Branch coverage catches unreachable code. A cosmic-ray mutation score catches tautological and insensitive production tests. A declared-mutation registry covers what mutation tools cannot touch at all — test-code constants, data files and scanned text — and runs inside every `pytest` invocation. A dormant CI workflow makes the first two actually enforce.

**Tech Stack:** Python 3.13, pytest 9.0.2, pytest-cov, cosmic-ray. No CadQuery in any task here.

**Design spec:** `docs/superpowers/specs/2026-08-01-suite-integrity-design.md`

## Verified environment facts (spiked 2026-08-01, do not re-litigate)

- **`mutmut` 3.7.0 refuses to run natively on Windows**, exiting with a message directing to WSL. Unusable. **cosmic-ray is the tool** — it installs, imports and exposes a `cosmic-ray` CLI natively here.
- cosmic-ray workflow is three commands: `cosmic-ray init <cfg.toml> <session.sqlite>`, `cosmic-ray exec <cfg.toml> <session.sqlite>`, then `cr-report <session.sqlite>`. The report's last lines read `total jobs: N`, `complete: N (100.00%)`, `surviving mutants: M (P%)`.
- **The test-command in the config must run the WHOLE core subset, not the one matching test file.** Spiked both ways on `types.py`: per-file gave 12 survivors of 66 (18.2%); the full core subset gave **5 of 66 (7.58%)**. A per-file command inflates survivors and makes the score meaningless.
- `types.py` (80 lines) yields 66 mutants and takes **28 s** against the full core subset. Core is 827 lines, so expect roughly 600–700 mutants and **~5 minutes** for the whole core. Practical for a pre-merge gate, too slow for every `pytest`.
- The core test subset runs in **0.14 s** for 128 tests.
- `cosmic-ray` emits `TestOutcome.INCOMPETENT` for mutants that fail to execute (e.g. `RemoveDecorator` on a dataclass). These are neither killed nor surviving and must not be counted as either.
- **The repo has `core.autocrlf=true`, so tracked files are CRLF on disk.** Any patch anchor containing a newline will not match naively. The runner normalises `\r\n` → `\n` before matching text targets, and restores from the original bytes.
- There is no CI and **no git remote**.

## Global Constraints

- **This is not a research gate.** `CLAUDE.md` freezes Gate A/B/C/D thresholds. Nothing here is folded into `scripts/gate_a.py`, which must remain untouched and still report 6 PASS / 3 SKIP, exit 1.
- **All dimensions in millimetres, float.** ISO 286-1 unit conversion happens only at the `iso286.py` table boundary.
- **Do NOT modify any checker-core module** — `types`, `y14_5`, `iso286`, `montecarlo`, `checker`, `reliability` — except transiently inside a declared mutation, which must restore byte-identically.
- **Do NOT change any value** in `_IT_MICRONS`, `_DEVIATION_MICRONS`, `_SIZE_BANDS`, `_CLEARANCE_HOLE_MM`, `TAPPING_DRILL_MM`, `_TOL_FRACTION_RANGE`, `_MIN_WALL_MM`, `_EDGE_MARGIN_MM`.
- **Do NOT generate a research corpus.** Spec §12 puts pre-registration first.
- Thresholds for layers 1 and 2 are **measured, then pinned** — never an aspirational round number.
- The full suite must still pass, and the Tier 1 ladder must stay at **d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%** over seeds 0-199.

## File structure

| File | Change | Responsibility |
|---|---|---|
| `tests/mutation_registry.py` | Create | `DeclaredMutation` dataclass, `REGISTRY`, and the runner that performs the experiment |
| `tests/test_declared_mutations.py` | Create | Executes every registry entry; asserts registry coverage |
| `scripts/check_suite_integrity.py` | Create | Layers 1 and 2; gate-A-style report; nonzero exit on failure |
| `cosmic-ray.toml` | Create | cosmic-ray config for the six core modules |
| `.github/workflows/ci.yml` | Create | Clean-clone run of the suite plus the integrity script |
| `pyproject.toml` | Modify | Add the `mutation` marker and cosmic-ray to the dev extra |
| `.gitignore` | Modify | Ignore cosmic-ray session databases and coverage artifacts |

---

### Task 1: The declared-mutation runner and its anti-vacuity contract

**Files:**
- Create: `tests/mutation_registry.py`
- Create: `tests/test_declared_mutations.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `DeclaredMutation(name, target, find, replace, test, expect, why, binary=False)` — frozen dataclass
  - `REGISTRY: tuple[DeclaredMutation, ...]`
  - `run_declared_mutation(m: DeclaredMutation) -> None` — raises `AssertionError` with a diagnostic message on any failure

This task builds the mechanism and proves it on two entries. Task 2 fills in the rest.

**The contract, and why each clause exists.** A guard that claims "I would catch X" is worthless unless someone has watched it catch X. The runner performs the whole experiment:

1. the anchor occurs **exactly once** — an ambiguous or absent anchor silently patches nothing, or the wrong thing
2. the target test **passes before** mutation — proving an outcome change from a broken baseline proves nothing
3. apply, run, assert the **declared outcome**
4. restore, and assert the file is **byte-identical**

Clauses 1, 2 and 4 exist because *the anti-vacuity mechanism must not itself become vacuous*. That would be a twelfth instance of the defect this repository is trying to eliminate, and the most embarrassing one available.

- [ ] **Step 1: Write the failing test**

Create `tests/test_declared_mutations.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_declared_mutations.py -v`
Expected: FAIL at collection with `ModuleNotFoundError: No module named 'tests.mutation_registry'`.

Note `tests/` needs to be importable as a package for `from tests.mutation_registry import ...` to work. `pythonpath = ["src", "."]` is already set in `pyproject.toml`, so add an empty `tests/__init__.py` **only if** the import fails without it — check before adding, and say which you did.

- [ ] **Step 3: Write the runner**

Create `tests/mutation_registry.py`:

```python
"""Declared mutations: guards that have been watched failing.

WHY THIS EXISTS. This project's dominant failure mode is the test that cannot
fail -- eleven documented instances. Mutation tools (Layer 2) mutate src/ only,
so they cannot reach four of them: self-referential test constants, a corrupted
data fixture, a case-sensitive text guard, and a stale literal floor. Those live
in test code, in binary data, and in scanned prose.

What did catch all four was a manual ritual -- corrupt something, watch the
specific guard fail, revert -- performed in a shell and lost when it closed.
This module makes that ritual executable and permanent.

THE RUNNER'S OWN ANTI-VACUITY. A registry that silently patched nothing would be
a twelfth instance of the very defect it exists to catch. So the runner asserts
the anchor matches exactly once, asserts the target test PASSES before the
mutation, and asserts the file is restored byte-identically afterwards.
"""

from __future__ import annotations

import dataclasses
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_VALID_EXPECTATIONS = ("fail", "pass")


@dataclasses.dataclass(frozen=True)
class DeclaredMutation:
    """One experiment: corrupt `target`, and require `test` to react as declared.

    expect="fail" -- the guard must NOTICE this corruption. Covers insensitive,
        tautological and drifted guards.
    expect="pass" -- the result must NOT depend on this incidental choice. Covers
        seed fishing: a conclusion that held only for one lucky draw fails here.
        Asserting a test *can* fail says nothing about whether it passes for the
        right reason, which is why both directions are needed.
    """

    name: str
    target: str
    find: str
    replace: str
    test: str
    expect: str
    why: str
    binary: bool = False

    def __post_init__(self) -> None:
        if self.expect not in _VALID_EXPECTATIONS:
            raise ValueError(
                f"{self.name}: expect must be one of {_VALID_EXPECTATIONS}, "
                f"got {self.expect!r}"
            )
        if self.find == self.replace:
            raise ValueError(f"{self.name}: a no-op mutation proves nothing")


def _target_test_passes(test_selector: str) -> bool:
    """Run one test selector in a subprocess. True if it passed."""
    proc = subprocess.run(
        [
            sys.executable, "-m", "pytest", test_selector,
            "-x", "-q", "--no-header", "-p", "no:cacheprovider",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _count_and_apply(original: bytes, m: DeclaredMutation) -> tuple[int, bytes]:
    """Return (occurrences, mutated bytes).

    Text targets are matched against newline-normalised content: this repo has
    core.autocrlf=true, so tracked files are CRLF on disk and an anchor written
    with \\n would never match. The mutated file is written with LF, which is
    harmless because it exists only for the duration of one subprocess run and
    the restore is from the original bytes regardless.
    """
    if m.binary:
        find = m.find.encode("latin-1")
        replace = m.replace.encode("latin-1")
        return original.count(find), original.replace(find, replace)

    text = original.decode("utf-8").replace("\r\n", "\n")
    return text.count(m.find), text.replace(m.find, m.replace).encode("utf-8")


def run_declared_mutation(m: DeclaredMutation) -> None:
    """Perform the experiment. Raise AssertionError with a diagnosis on failure."""
    path = REPO_ROOT / m.target
    assert path.is_file(), f"{m.name}: target {m.target} does not exist"

    original = path.read_bytes()
    occurrences, mutated = _count_and_apply(original, m)

    if occurrences != 1:
        raise AssertionError(
            f"{m.name}: the patch anchor occurs {occurrences} times in "
            f"{m.target}, expected exactly 1. An anchor that matches zero times "
            f"patches nothing; one that matches many patches the wrong thing. "
            f"Either way this check would be vacuous."
        )

    if not _target_test_passes(m.test):
        raise AssertionError(
            f"{m.name}: {m.test} FAILS before any mutation is applied. "
            f"Demonstrating an outcome change from a broken baseline proves "
            f"nothing -- fix the test first."
        )

    try:
        path.write_bytes(mutated)
        passed_under_mutation = _target_test_passes(m.test)
    finally:
        path.write_bytes(original)

    if path.read_bytes() != original:
        raise AssertionError(
            f"{m.name}: {m.target} was NOT restored byte-identically. The "
            f"working tree may be corrupt -- check it before doing anything else."
        )

    if m.expect == "fail" and passed_under_mutation:
        raise AssertionError(
            f"{m.name}: {m.test} still PASSED with {m.target} corrupted. "
            f"That guard cannot detect what it exists to detect. {m.why}"
        )
    if m.expect == "pass" and not passed_under_mutation:
        raise AssertionError(
            f"{m.name}: {m.test} FAILED under a mutation it should survive. "
            f"The result depends on an incidental choice. {m.why}"
        )


REGISTRY: tuple[DeclaredMutation, ...] = (
    DeclaredMutation(
        name="it7-row-transposed",
        target="src/tolcad/iso286.py",
        find="    7: [10, 12, 15, 18, 21, 25, 30, 35, 40, 46, 52, 57, 63],",
        replace="    7: [10, 12, 15, 18, 21, 30, 25, 35, 40, 46, 52, 57, 63],",
        test="tests/test_iso286.py::test_all_52_it5_to_it8_cells_match_iso286_table_1",
        expect="fail",
        why=(
            "IT7 feeds the Tier 2 iso_fit yields through fit_from_designation, "
            "so a corrupted cell moves published numbers, not documentation."
        ),
    ),
    DeclaredMutation(
        name="zeroed-wall-margin",
        target="src/tolcad/gen/layout.py",
        find="\n_MIN_WALL_MM = 4.0",
        replace="\n_MIN_WALL_MM = 0.0",
        test="tests/gen/test_layout.py::test_the_margin_constants_are_actually_large_enough",
        expect="fail",
        why=(
            "A zero wall makes adjacent holes exactly tangent. The containment "
            "test cannot see it either, because tangency has zero intersection "
            "volume, so this is the only guard standing between a zeroed "
            "constant and a degenerate B-rep in the reference geometry."
        ),
    ),
)
```

Add the marker to `pyproject.toml` under `[tool.pytest.ini_options]`, alongside the existing `slow` marker:

```toml
markers = [
    "slow: Monte Carlo convergence checks (deselect with -m 'not slow')",
    "mutation: declared-mutation experiments; each spawns a pytest subprocess",
]
```

Do **not** deselect `mutation` by default. These run in every invocation on purpose — the sharpest layer must never be opt-in.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_declared_mutations.py -v`
Expected: PASS — 2 registry entries plus 4 runner-guard tests.

The `\n_MIN_WALL_MM = 4.0` anchor is the one that motivated newline normalisation: `_MIN_WALL_MM = 4.0` alone matches **twice** in `layout.py`, once in the docstring at line 32 and once as the assignment at line 67. If your run reports "occurs 2 times", the normalisation is not working — fix it rather than changing the anchor.

Then the full suite: `python -m pytest -q`. Baseline is **280 passed**. Report the new count and the added wall-clock time.

- [ ] **Step 5: Commit**

```bash
git add tests/mutation_registry.py tests/test_declared_mutations.py pyproject.toml
git commit -m "feat: declared-mutation runner, with its own anti-vacuity contract"
```

---

### Task 2: The full seed registry

**Files:**
- Modify: `tests/mutation_registry.py`
- Modify: `tests/test_declared_mutations.py`

**Interfaces:**
- Consumes: `DeclaredMutation`, `REGISTRY`, `run_declared_mutation` from Task 1
- Produces: a `REGISTRY` covering every guard that protects a published number

Every anchor below was verified to occur exactly once (after newline normalisation) on 2026-08-01, and every test node ID was verified to exist via `pytest --collect-only`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_declared_mutations.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_declared_mutations.py -v -k "critical_guard or both_expectation"`
Expected: FAIL — `test_the_registry_still_covers_every_critical_guard` reports seven missing names, and `test_both_expectation_directions_are_exercised` reports `{'fail'}` only.

- [ ] **Step 3: Add the remaining entries**

Append these to the `REGISTRY` tuple in `tests/mutation_registry.py`, after the two from Task 1:

```python
    DeclaredMutation(
        name="it-grade-set-widened",
        target="src/tolcad/iso286.py",
        find="    12: [100,",
        replace=(
            "    9: [25, 30, 36, 43, 52, 62, 74, 87, 100, 115, 130, 140, 155],\n"
            "    12: [100,"
        ),
        test="tests/test_iso286.py::test_the_tabulated_grade_set_is_declared_not_emergent",
        expect="fail",
        why=(
            "fit_from_designation accepts any tabulated grade for the "
            "unrestricted shaft letters, so adding a grade silently widens a "
            "checker-core public API. That already happened once when IT12-IT14 "
            "landed and H12/g12 went from raising to accepted, undocumented."
        ),
    ),
    DeclaredMutation(
        name="flat-difficulty-ladder",
        target="src/tolcad/gen/sampler.py",
        find="    4: (0.72, 1.34),",
        replace="    4: (0.20, 0.50),",
        test="tests/gen/test_sampler.py::test_tier1_failure_rate_rises_monotonically_with_difficulty",
        expect="fail",
        why=(
            "The original anti-degeneracy guard passed under every ladder "
            "mutation including a completely flat one, because iso_fit mates "
            "satisfied it alone. The ladder is pre-registered; it must be guarded."
        ),
    ),
    DeclaredMutation(
        name="stale-literal-wall-floor",
        target="tests/gen/test_layout.py",
        find="_LITERAL_WALL_FLOOR_MM = 3.8",
        replace="_LITERAL_WALL_FLOOR_MM = 3.7",
        test="tests/gen/test_layout.py::test_the_literal_floors_are_not_below_the_derived_ones",
        expect="fail",
        why=(
            "This target is TEST code, which Layer 2 cannot reach at all. The "
            "literal floor once silently stopped being a floor when the derived "
            "requirement moved past it, and no test noticed."
        ),
    ),
    DeclaredMutation(
        name="crlf-corrupted-nist-fixture",
        target="tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp",
        find="HEADER;\r\n",
        replace="HEADER;\n",
        test="tests/test_ap242_pmi.py::test_the_committed_fixture_is_byte_identical_to_the_nist_original",
        expect="fail",
        binary=True,
        why=(
            "core.autocrlf once stored a CRLF-normalised blob for this fixture, "
            "and the PMI reader returns identical counts (21/6/11) from the "
            "mangled copy -- so the positive control passed against the exact "
            "corruption it existed to detect. Only size and hash catch it. "
            "'ISO-10303-21;' is NOT a usable anchor: it appears twice, in the "
            "header and in END-ISO-10303-21;."
        ),
    ),
    DeclaredMutation(
        name="m12-clearance-diameter",
        target="src/tolcad/gen/features.py",
        find="    12.0: (13.0, 13.5, 14.5),",
        replace="    12.0: (13.0, 13.5, 18.5),",
        test="tests/gen/test_features.py::test_clearance_hole_upper_dev_comes_from_the_series_grade",
        expect="fail",
        why=(
            "M12 loose is the widest feature and sets the layout margins. 18.5 "
            "crosses out of the >10-18 ISO 286 band, so the derived tolerance "
            "moves from IT14 0.43 to 0.52. A within-band typo would NOT be "
            "caught here -- that is what the ISO 273 diameter pin is for."
        ),
    ),
    DeclaredMutation(
        name="fastener-upper-dev-nonzero",
        target="src/tolcad/gen/sampler.py",
        find="_FASTENER_UPPER_DEV_MM = 0.0",
        replace="_FASTENER_UPPER_DEV_MM = 0.05",
        test="tests/gen/test_sampler.py::test_the_fastener_tolerance_is_inert_because_its_mmc_is_the_nominal",
        expect="fail",
        why=(
            "The fastener's -0.1 lower deviation is untraced to any standard and "
            "is published in the sidecar. It is safe only because external MMC "
            "is nominal + upper_dev and upper_dev is zero. That is the whole "
            "argument, so it needs a guard."
        ),
    ),
    DeclaredMutation(
        name="mc-seed-base-shifted",
        target="tests/gen/test_features.py",
        find='"seed": 12345, "n": 100_000}).assembles',
        replace='"seed": 24680, "n": 100_000}).assembles',
        test="tests/gen/test_features.py::test_supported_fits_still_contain_both_verdict_classes",
        expect="pass",
        why=(
            "THE SEED-FISHING GUARD, and the only expect='pass' entry. This "
            "control asserts the surviving ISO fit set still spans both verdict "
            "classes. If that conclusion held only for seed 12345 it would be a "
            "fished positive control -- one of the eleven historical instances. "
            "Requiring it to survive an arbitrary reseed is what makes it honest."
        ),
    ),
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_declared_mutations.py -v`
Expected: PASS — 9 registry entries plus the meta-tests.

**If any entry reports "occurs 0 times" or "occurs N times"**, the anchor is wrong; find a unique one rather than deleting the entry. **If any entry with `expect="fail"` reports that the test still passed, STOP and report it** — that is a live instance of the defect, and it is a finding, not a bug in this plan.

Then: `python -m pytest -q` (baseline 280 + Task 1's additions) and `python scripts/gate_a.py > /dev/null 2>&1; echo $?` (expect 1). Capture the exit code without a pipe. Re-measure the ladder over seeds 0-199 and confirm 19.5 / 32.9 / 52.9 / 69.1.

- [ ] **Step 5: Commit**

```bash
git add tests/mutation_registry.py tests/test_declared_mutations.py
git commit -m "feat: declare the mutations that must break each published-number guard"
```

---

### Task 3: The integrity script and branch coverage

**Files:**
- Create: `scripts/check_suite_integrity.py`
- Modify: `.gitignore`
- Test: `tests/test_suite_integrity_script.py`

**Interfaces:**
- Consumes: nothing from earlier tasks
- Produces: `scripts/check_suite_integrity.py` as a CLI exiting 0 on pass, 1 on failure; `CORE_MODULES` and `COVERAGE_FLOOR` as module constants

Layer 1 catches the *unreachable* class: a branch no test enters cannot fail. The fetcher's mismatch → `exit 1` guard sat uncovered for a whole phase.

- [ ] **Step 1: Write the failing test**

Create `tests/test_suite_integrity_script.py`:

```python
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "check_suite_integrity.py"


def test_the_script_exists():
    assert SCRIPT.is_file()


def test_it_names_the_six_core_modules():
    """Layer 1 and 2 scope. gen/ is deliberately excluded -- CadQuery mutants
    are slow and frequently geometrically meaningless."""
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert set(mod.CORE_MODULES) == {
        "types", "y14_5", "iso286", "montecarlo", "checker", "reliability",
    }


def test_the_coverage_floor_is_a_measured_value_not_a_round_number():
    """A floor pinned at an aspirational round number is not a measurement.

    The project's drift class is exactly this: a threshold that stops tracking
    what it is supposed to bound. Whatever the measured baseline is, it is
    almost certainly not 80 or 90.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert mod.COVERAGE_FLOOR not in (0, 50, 60, 70, 75, 80, 85, 90, 95, 100), (
        f"COVERAGE_FLOOR {mod.COVERAGE_FLOOR} looks aspirational rather than "
        f"measured. Run the script, read the number, pin that."
    )


def test_the_script_reports_and_exits_nonzero_when_a_layer_fails(tmp_path):
    """Exercised via --self-test, which forces one layer to report failure."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--self-test-failure"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert proc.returncode == 1, "a failing layer must exit nonzero"
    assert "FAIL" in proc.stdout
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_suite_integrity_script.py -v`
Expected: FAIL — the script does not exist.

- [ ] **Step 3: Write the script's Layer 1**

Create `scripts/check_suite_integrity.py`:

```python
#!/usr/bin/env python
"""Suite integrity: detect tests that cannot fail.

NOT a research gate. CLAUDE.md freezes Gate A/B/C/D; this is separate and
scripts/gate_a.py is untouched. See
docs/superpowers/specs/2026-08-01-suite-integrity-design.md

Layer 1 (here): branch coverage over the checker core -- a branch no test
enters cannot fail. Layer 2 (added in the next task): mutation score.
Layer 3 lives in tests/ and runs in every pytest invocation.

Usage: python scripts/check_suite_integrity.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CORE_MODULES = ("types", "y14_5", "iso286", "montecarlo", "checker", "reliability")

CORE_TEST_SUBSET = [f"tests/test_{name}.py" for name in CORE_MODULES]

# MEASURED, not chosen. Set from an actual run on 2026-08-01 -- see Step 4.
# A floor pinned at a round number is not a measurement, and this project's
# drift class is precisely a threshold that stops tracking what it bounds.
COVERAGE_FLOOR = 0.0  # replaced in Step 4 with the measured value


def run_coverage() -> tuple[float, bool]:
    """Branch coverage over the six core modules. Returns (measured, ok)."""
    proc = subprocess.run(
        [
            sys.executable, "-m", "pytest", *CORE_TEST_SUBSET,
            "-q", "--no-header", "-p", "no:cacheprovider", "-m", "not slow",
            "--cov=src/tolcad", "--cov-branch", "--cov-report=term",
        ],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    match = re.search(r"^TOTAL\s+.*?(\d+(?:\.\d+)?)%", proc.stdout, re.MULTILINE)
    if match is None:
        raise RuntimeError(
            "could not parse coverage output; refusing to report a number "
            f"that was not measured.\n{proc.stdout[-2000:]}"
        )
    measured = float(match.group(1))
    return measured, measured >= COVERAGE_FLOOR


def _print_report(rows: list[tuple[str, str, str, bool]]) -> None:
    print("Suite integrity - tests that cannot fail (non-blocking for Gate A)")
    print()
    for name, measured, threshold, ok in rows:
        status = "PASS" if ok else "FAIL"
        print(f"  {name:<34} {status:<6} {measured} (floor {threshold})")
    print()


def main(argv: list[str]) -> int:
    rows: list[tuple[str, str, str, bool]] = []

    if "--self-test-failure" in argv:
        # Covers this script's own nonzero-exit path. Without it that branch
        # would be untested -- the exact defect Layer 1 exists to catch.
        rows.append(("Self-test (synthetic failure)", "n/a", "n/a", False))
    else:
        measured, ok = run_coverage()
        rows.append(
            ("Core branch coverage", f"{measured:.2f}%", f"{COVERAGE_FLOOR:.2f}%", ok)
        )

    _print_report(rows)
    failed = [name for name, _, _, ok in rows if not ok]
    if failed:
        print(f"Suite integrity: FAILED ({', '.join(failed)})")
        return 1
    print("Suite integrity: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

The output shape deliberately mirrors `scripts/gate_a.py` so the two read alike.

- [ ] **Step 4: Measure the baseline and pin it**

Run: `python scripts/check_suite_integrity.py`

Read the measured branch coverage. **Set `COVERAGE_FLOOR` to that measured value**, not to a round number above or below it. Record the measurement in a comment beside the constant, with the date.

Re-run: the script must now report PASS for Layer 1 and exit 0.

Then `python -m pytest tests/test_suite_integrity_script.py -v` — all pass.

**If the measured coverage is below 90%**, report the uncovered branches rather than pinning a low floor silently: uncovered core branches are themselves findings, and the human should see them before the number is frozen.

- [ ] **Step 5: Commit**

Add to `.gitignore`:

```
# Suite-integrity artifacts: regenerable, not tracked.
.coverage
htmlcov/
*.sqlite
```

```bash
git add scripts/check_suite_integrity.py tests/test_suite_integrity_script.py .gitignore
git commit -m "feat: suite-integrity script with a measured branch-coverage floor"
```

---

### Task 4: The mutation-score layer

**Files:**
- Create: `cosmic-ray.toml`
- Modify: `scripts/check_suite_integrity.py`
- Modify: `pyproject.toml`
- Test: `tests/test_suite_integrity_script.py`

**Interfaces:**
- Consumes: `scripts/check_suite_integrity.py` from Task 3
- Produces: `MUTATION_FLOOR` module constant; `run_mutation_score() -> tuple[float, bool]`

Layer 2 catches the *tautological* and *insensitive* classes in production code. A surviving mutant is the question "could this fail?" asked mechanically, once per mutable expression.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_suite_integrity_script.py`:

```python
def test_the_cosmic_ray_config_runs_the_whole_core_subset():
    """A per-file test command inflates survivors and makes the score meaningless.

    Spiked 2026-08-01 on types.py: scoping the command to tests/test_types.py
    alone gave 12 survivors of 66 (18.2%); the full core subset gave 5 of 66
    (7.58%). checker.py and y14_5.py tests exercise types.py heavily.
    """
    import tomllib

    cfg = tomllib.loads((REPO / "cosmic-ray.toml").read_text(encoding="utf-8"))
    command = cfg["cosmic-ray"]["test-command"]
    for module in ("types", "y14_5", "iso286", "montecarlo", "checker", "reliability"):
        assert f"tests/test_{module}.py" in command, (
            f"cosmic-ray's test-command omits tests/test_{module}.py; the "
            f"resulting mutation score would be inflated and meaningless"
        )


def test_the_mutation_floor_is_measured_not_aspirational():
    sys.path.insert(0, str(REPO / "scripts"))
    import check_suite_integrity as mod

    assert mod.MUTATION_FLOOR not in (0, 50, 60, 70, 75, 80, 85, 90, 95, 100), (
        f"MUTATION_FLOOR {mod.MUTATION_FLOOR} looks aspirational rather than "
        f"measured. Run the layer, read the number, pin that."
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_suite_integrity_script.py -v -k "cosmic_ray or mutation_floor"`
Expected: FAIL — `cosmic-ray.toml` does not exist and `MUTATION_FLOOR` is undefined.

- [ ] **Step 3: Add the config and the layer**

Create `cosmic-ray.toml`:

```toml
# Layer 2 of the suite-integrity gate. See
# docs/superpowers/specs/2026-08-01-suite-integrity-design.md
#
# module-path is set per-run by scripts/check_suite_integrity.py, which iterates
# the six core modules -- cosmic-ray takes one module path per session.
#
# THE TEST COMMAND MUST BE THE WHOLE CORE SUBSET. Spiked 2026-08-01: scoping it
# to the single matching test file gave 12 survivors of 66 on types.py (18.2%),
# against 5 of 66 (7.58%) for the full subset, because checker.py and y14_5.py
# tests exercise types.py heavily. A per-file command measures nothing useful.
[cosmic-ray]
module-path = "src/tolcad/types.py"
timeout = 30.0
excluded-modules = []
test-command = "python -m pytest tests/test_types.py tests/test_y14_5.py tests/test_iso286.py tests/test_montecarlo.py tests/test_checker.py tests/test_reliability.py -x -q --no-header -p no:cacheprovider -m 'not slow'"

[cosmic-ray.distributor]
name = "local"
```

Add `"cosmic-ray>=8.3"` to the `dev` extra in `pyproject.toml`.

Add to `scripts/check_suite_integrity.py`:

```python
import shutil
import tempfile
import tomllib

# MEASURED, not chosen. Set from an actual run -- see Step 4.
MUTATION_FLOOR = 0.0  # replaced in Step 4 with the measured value

_CONFIG = REPO_ROOT / "cosmic-ray.toml"


def _mutate_one_module(module: str, workdir: Path) -> tuple[int, int, int]:
    """Run cosmic-ray over one core module. Returns (total, survived, incompetent)."""
    config = tomllib.loads(_CONFIG.read_text(encoding="utf-8"))
    config["cosmic-ray"]["module-path"] = f"src/tolcad/{module}.py"

    cfg_path = workdir / f"cr-{module}.toml"
    # Re-emit the config with only the field we changed; cosmic-ray reads TOML.
    cfg_path.write_text(
        "[cosmic-ray]\n"
        f'module-path = "src/tolcad/{module}.py"\n'
        f"timeout = {config['cosmic-ray']['timeout']}\n"
        "excluded-modules = []\n"
        f"test-command = \"{config['cosmic-ray']['test-command']}\"\n"
        "\n[cosmic-ray.distributor]\n"
        'name = "local"\n',
        encoding="utf-8",
    )
    session = workdir / f"{module}.sqlite"

    subprocess.run(["cosmic-ray", "init", str(cfg_path), str(session)],
                   cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    subprocess.run(["cosmic-ray", "exec", str(cfg_path), str(session)],
                   cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    report = subprocess.run(["cr-report", str(session)],
                            cwd=REPO_ROOT, capture_output=True, text=True).stdout

    total = int(re.search(r"total jobs:\s*(\d+)", report).group(1))
    survived = int(re.search(r"surviving mutants:\s*(\d+)", report).group(1))
    # INCOMPETENT mutants fail to execute at all (RemoveDecorator on a
    # dataclass, for instance). They are neither killed nor surviving, so
    # counting them either way distorts the score.
    incompetent = report.count("TestOutcome.INCOMPETENT")
    return total, survived, incompetent


def run_mutation_score() -> tuple[float, bool]:
    """Aggregate killed / (total - incompetent) across the six core modules."""
    if shutil.which("cosmic-ray") is None:
        # Unavailable is a FAILURE, never a skip. A silently skipped integrity
        # layer is the exact failure mode this whole exercise exists to remove.
        raise RuntimeError(
            "cosmic-ray is not installed; install the [dev] extra. This layer "
            "does not skip."
        )

    totals = survived_all = incompetent_all = 0
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        for module in CORE_MODULES:
            total, survived, incompetent = _mutate_one_module(module, workdir)
            totals += total
            survived_all += survived
            incompetent_all += incompetent

    denominator = totals - incompetent_all
    if denominator <= 0:
        raise RuntimeError("no viable mutants were generated; the config is wrong")
    killed = denominator - survived_all
    score = 100.0 * killed / denominator
    return score, score >= MUTATION_FLOOR
```

Wire it into `main()` as a second row, guarded so `--self-test-failure` skips the slow path. Session databases live in a `TemporaryDirectory`, never in the repo.

Add `"cosmic-ray>=8.3"` to the `dev` extra in `pyproject.toml`.

- [ ] **Step 4: Measure the baseline and pin it**

Run: `python scripts/check_suite_integrity.py`

This takes roughly **5 minutes** — 827 core lines at about 0.8 mutants per line, ~0.42 s each. That is expected, not a hang.

Set `MUTATION_FLOOR` to the measured aggregate, with a dated comment. Then **triage every survivor**: for each, either write a test that kills it, or record it in a comment as an equivalent mutant with the reason it cannot change behaviour. An unexamined survivor is not acceptable; an equivalent mutant is.

The `types.py` spike found 5 survivors of 66, including `if upper_dev < lower_dev` → `<=` surviving, which means **no test constructs a zero-width tolerance band** (`upper_dev == lower_dev`) — a legitimate case, a basic dimension with no tolerance. Report the full survivor list to the human with your triage.

- [ ] **Step 5: Commit**

```bash
git add cosmic-ray.toml scripts/check_suite_integrity.py tests/test_suite_integrity_script.py pyproject.toml
git commit -m "feat: mutation-score layer over the checker core"
```

---

### Task 5: CI, and proof that all eleven instances are caught

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `docs/superpowers/specs/2026-08-01-suite-integrity-instance-map.md`
- Test: `tests/test_suite_integrity_script.py`

**Interfaces:**
- Consumes: everything above
- Produces: no new API — this is the closing gate

The spec's success criterion is that **all eleven historical instances are caught by at least one layer, verified rather than asserted.** A success criterion that merely claims coverage would itself be the defect.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_suite_integrity_script.py`:

```python
def test_the_instance_map_accounts_for_all_eleven():
    """The spec claims every historical instance is caught. Check the claim."""
    doc = (
        REPO / "docs" / "superpowers" / "specs"
        / "2026-08-01-suite-integrity-instance-map.md"
    ).read_text(encoding="utf-8")

    for n in range(1, 12):
        assert f"| {n} |" in doc, f"instance {n} is missing from the map"
    assert "not caught" not in doc.lower(), (
        "an instance is recorded as uncaught; either add a layer that catches "
        "it or change the spec's success criterion -- do not leave the claim "
        "standing while the map contradicts it"
    )


def test_ci_runs_the_integrity_script_not_just_the_suite():
    """A green suite with an unrun gate is the failure mode being fixed."""
    ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "check_suite_integrity.py" in ci
    assert "pytest" in ci
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_suite_integrity_script.py -v -k "instance_map or ci_runs"`
Expected: FAIL — neither file exists.

- [ ] **Step 3: Write the CI workflow and the instance map**

Create `.github/workflows/ci.yml`: checkout, set up Python 3.13, `pip install -e ".[dev,gen]"`, run `python -m pytest -q`, then `python scripts/check_suite_integrity.py`. Do not fetch the NIST suite in CI — the committed fixture is what makes the oracle path testable on a clean clone, and that is deliberate.

Note in a comment that the workflow is **dormant until a git remote exists**, and that it closes Gate A's third SKIP ("Fresh clone pipeline") once it runs — it is also the only mechanism that can validate the `.gitattributes` binary-fixture rule, since CRLF normalisation is only observable across a fresh clone.

Create the instance map as a table with columns *# · instance · shape · caught by · evidence*, one row per historical instance, numbered 1 to 11:

1. tautological test · 2. reliability metric incapable of <1.0 · 3. seed-fished positive control · 4. Gate A 1000× headroom · 5. unconditionally-skipped test · 6. untested fetcher exit-1 branch · 7. anti-degeneracy guard blind to its own degeneracy · 8. self-referential margin constants · 9. positive control passing against the CRLF corruption it detects · 10. case-sensitive text guard defeated by capitalisation · 11. literal floor that silently stopped being a floor

For each, name the layer and the concrete evidence — a registry entry name, a covered branch, or a killed mutant. Where an instance is caught by a layer only in principle rather than by a specific artifact, **say so plainly** rather than claiming a clean catch.

- [ ] **Step 4: Run the full suite and the gates**

Run, in order:

```bash
python -m pytest -q
python scripts/check_suite_integrity.py > /dev/null 2>&1; echo "integrity exit: $?"
python scripts/gate_a.py > /dev/null 2>&1; echo "gate_a exit: $?"
```

Expected: suite passes; integrity exits 0; Gate A exits **1** with 6 PASS / 3 SKIP, unchanged. Capture exit codes without a pipe — piping to `tail` reports tail's status.

Re-measure the Tier 1 ladder over seeds 0-199 and confirm **d1 19.5% / d2 32.9% / d3 52.9% / d4 69.1%**.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml docs/superpowers/specs/2026-08-01-suite-integrity-instance-map.md tests/test_suite_integrity_script.py
git commit -m "feat: CI harness and the historical-instance coverage map"
```

---

## Plan completion state

At the end of Task 5:

- Declared mutations run in every `pytest` invocation, covering test code, binary fixtures and scanned text — the classes mutation tools cannot reach
- Branch coverage and mutation score have measured, pinned floors and a script that fails on regression
- Both expectation directions are exercised, so seed fishing is detectable
- All eleven historical instances are mapped to a catching layer, with the map checked by a test
- Gate A is untouched and still reports 6 PASS / 3 SKIP
- A CI workflow is ready to activate and will close Gate A's third SKIP

**Deliberately NOT done here:**
- Mutation testing over `gen/`. CadQuery mutants are slow and often geometrically meaningless. `gen/` is covered by Layer 3, which is where its historical instances actually lived.
- Folding any of this into Gate A. Those thresholds are frozen.
- Raising coverage or mutation score beyond the measured baseline. The floors exist to detect regression, not to be maximised.

## Open question for the human

The registry protects *named* guards. Nothing forces a **new** guard to be registered, so a future test protecting a new published number could be added with no entry and no layer would notice. The pre-registration freeze bounds how much new surface can appear before the corpus is generated, which is why this is acceptable now rather than in general. If Phase 4 adds new published numbers, the registry needs entries for them, and that obligation currently lives only in this sentence.

---

## Staleness note, appended 2026-08-01 (APPEND-ONLY)

This plan is an **executed** implementation plan. Its task bodies, acceptance criteria and
"verified environment facts" are a contemporaneous record of what was true and what was
required at the time, so they are annotated here rather than edited. Four figures in it are
superseded:

- **`6 PASS / 3 SKIP`** (lines ~26, ~989, ~1010). Gate A now reports **7 PASS (5 measured,
  2 attested) / 0 FAIL / 3 SKIP**, exit 1. Line 26's stronger form — *"`scripts/gate_a.py`
  … must remain untouched"* — was a correct constraint **on this branch** and was later
  deliberately overridden by design-spec amendment `2026-08-01g`, which added a criterion
  and labelled two attestation rows as attestations. Nothing was weakened or removed.
- **`eleven` historical instances** (lines ~161, ~523, ~921, ~932, ~939, ~1009). The count
  is **twelve**; the suite-integrity design spec's §1 table is the enumeration of record and
  the missing one is the **Unencoded** row. Task 5's `test_the_instance_map_accounts_for_all_eleven`
  is named after the wrong count. Refer to instances **by name, not by number** — the base
  was wrong by one, so every later ordinal is unreliable.
- **`There is no CI and no git remote`** (line 22), and **"dormant until a git remote
  exists"** (line ~971). Both discharged: `origin` is
  `https://github.com/harshD42/TolAEG-CAD` and `.github/workflows/ci.yml` is live and green
  on `ubuntu-latest` and `windows-latest`.
- **The `280 passed` baseline** (line ~346). The suite is now **428 passed**.

Not superseded, and deliberately left: the **18.2%** `types.py` spike (lines ~17, ~767,
~808). It is presented there as a *rejected methodology* — the reason the test command must
run the whole core subset — not as a score for Layer 2, and it is correct in that role.

Canonical values: `docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`.
Design-spec amendments: §10 of `docs/superpowers/specs/2026-08-01-suite-integrity-design.md`.
