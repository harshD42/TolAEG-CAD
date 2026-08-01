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
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_VALID_EXPECTATIONS = ("fail", "pass")

# Bounded retry around the mutate/restore writes. See _write_bytes_resiliently.
_WRITE_ATTEMPTS = 5
_WRITE_BACKOFF_S = 0.05


def _write_bytes_resiliently(path: pathlib.Path, data: bytes) -> None:
    """Write `data` to `path`, retrying transient OS-level write failures.

    OBSERVED, NOT HYPOTHETICAL. On Windows, 2026-08-01, two registry entries
    targeting the SAME file back to back raised
    `OSError: [Errno 22] Invalid argument` on the RESTORE write and left
    src/tolcad/reliability.py mutated in the working tree. The write that had
    just succeeded milliseconds earlier is the likely trigger (virus scanner or
    write-back still holding the freshly written file). It reproduced once in
    roughly a dozen runs.

    A one-shot write is therefore not good enough for a mechanism whose worst
    outcome is a corrupted working tree. Retries are bounded; a persistent
    failure is re-raised for the caller to convert into a loud, named error.
    """
    for attempt in range(_WRITE_ATTEMPTS):
        try:
            path.write_bytes(data)
            return
        except OSError:
            if attempt == _WRITE_ATTEMPTS - 1:
                raise
            time.sleep(_WRITE_BACKOFF_S * (attempt + 1))


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
        _write_bytes_resiliently(path, mutated)
        passed_under_mutation = _target_test_passes(m.test)
    finally:
        try:
            _write_bytes_resiliently(path, original)
        except OSError as exc:
            # Deliberately raised from `finally`, masking any in-flight error:
            # a mutated file left on disk is strictly the worse outcome and
            # must be the message the operator sees first.
            raise AssertionError(
                f"{m.name}: could NOT restore {m.target} after "
                f"{_WRITE_ATTEMPTS} attempts. THE FILE IS LEFT MUTATED. Run "
                f"`git checkout -- {m.target}` before doing anything else, "
                f"then re-run. Underlying error: {exc!r}"
            ) from exc

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
        name="reliability-perturbation-neutered",
        target="src/tolcad/reliability.py",
        find='_PERTURBABLE = ("nominal", "lower_dev", "upper_dev", "position_tol")',
        replace="_PERTURBABLE = ()",
        test="tests/test_reliability.py::test_positive_control_detects_instability",
        expect="fail",
        why=(
            "HISTORICAL INSTANCE 2: a reliability metric MATHEMATICALLY "
            "INCAPABLE of returning below 1.0. With _PERTURBABLE empty, "
            "_perturb returns an unmodified deepcopy, check() is deterministic, "
            "so every verdict trivially survives and verdict_stability can only "
            "ever return 1.0 -- while still reporting a healthy tested count, "
            "which is what made the original so hard to see. The positive "
            "control is the only guard that asserts the metric CAN report "
            "instability. Note what does NOT catch this: Gate A's reliability "
            "criterion reads 1.0000 under this mutation and happily passes, "
            "which is why this entry and reliability-perturbation-tripled are "
            "separate experiments rather than one."
        ),
    ),
    DeclaredMutation(
        name="reliability-perturbation-tripled",
        target="src/tolcad/reliability.py",
        find="rng.uniform(-epsilon, epsilon)",
        replace="rng.uniform(-3.0 * epsilon, 3.0 * epsilon)",
        test=(
            "tests/test_gate_a.py::"
            "test_gate_a_reliability_criterion_holds_for_the_real_measurement"
        ),
        expect="fail",
        why=(
            "HISTORICAL INSTANCE 4: a Gate A measurement with 1000x headroom -- "
            "a criterion so far from its threshold that no degradation could "
            "move it. This is the headroom probe the design spec's seed table "
            "calls for: perturb the measured quantity by an amount that ought "
            "to matter and require Gate A's reliability criterion to notice. "
            "Tripling the perturbation while leaving the exclusion band at "
            "epsilon takes the mean over the 200 pre-registered seeds from "
            "0.9982 to 0.9068, below the 0.95 threshold. The bound is honest "
            "and narrow: 2x measures 0.9518 and is NOT caught. So the headroom "
            "is roughly 2-3x, which is documented in the target test's "
            "docstring and must be re-measured if the mate set or epsilon "
            "changes. The unit positive control does NOT catch this mutation "
            "(more flips still means value < 1.0), so neither this entry nor "
            "reliability-perturbation-neutered subsumes the other."
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
            "A NARROW TRIPWIRE, NOT A GENERAL SEED-ROBUSTNESS CHECK. Stated "
            "precisely because the earlier wording overstated it. The mutation "
            "IS load-bearing -- reseeding moves the H7/k6 Monte Carlo margin "
            "from 0.68925 to 0.68617 -- but the guarded assertion is on the "
            "BOOLEANS, and for every fit currently in SUPPORTED_FITS "
            "assembles == (es <= 0), which is seed-invariant by construction "
            "(see test_iso_fit_verdict_is_fixed_by_the_shaft_letter). So this "
            "entry cannot presently fail for a seed-fishing reason. Its "
            "reachable failure mode is a line-to-line fit such as H7/h6 "
            "re-entering SUPPORTED_FITS -- exactly the Phase 3.5a "
            "reintroduction path -- where the verdict stops being determined "
            "by the shaft letter and starts depending on the draw. Kept "
            "because it is cheap and that path is live, not because it "
            "certifies the control against seed choice in general."
        ),
    ),
)
