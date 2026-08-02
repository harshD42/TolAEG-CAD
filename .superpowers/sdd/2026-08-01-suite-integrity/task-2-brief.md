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

