### Task 4: A committed AP242 fixture, so the oracle has a positive control on a fresh clone

**Files:**
- Create: `tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp` (copied from `data/nist_pmi/`, 396,445 bytes)
- Create: `tests/fixtures/NIST-PROVENANCE.md`
- Modify: `tests/test_ap242_pmi.py`

**Interfaces:**
- Consumes: `validation.ap242_pmi.read_pmi_counts`, `PmiCounts`
- Produces: no new API

On a fresh clone, `data/nist_pmi/` does not exist, so the 47/27/59 assertion skips. What remains exercised is a `FileNotFoundError` check and `tests/gen/test_end_to_end.py`'s assertion that our *own* exports have **zero** PMI. A `read_pmi_counts` stubbed to `return PmiCounts(0, 0, 0)` passes that entire fresh-clone suite. Design spec line 252 makes "fresh clone, no licence, runs end-to-end" an explicit success criterion, so this is precisely the configuration where the licence-free oracle's read path has no positive coverage at all.

Committing one small AP242 file fixes it. `nist_ctc_01_asme1_ap242-e1.stp` is the smallest NIST AP242 file with non-trivial PMI: **396,445 bytes**, reading as **21 dimensions, 6 geometric tolerances, 11 datums** — verified by execution, and it parses with no OCCT warnings. NIST states its files "can be used without any restrictions", so redistributing one in the repo is permitted.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ap242_pmi.py`:

```python
FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "nist_ctc_01_asme1_ap242-e1.stp"


def test_reads_nonzero_pmi_from_the_committed_fixture():
    """Positive control that runs on a FRESH CLONE, with no fetch step.

    Without this, the only oracle assertions a fresh clone exercises are
    zero-counts and a FileNotFoundError -- so a read_pmi_counts stubbed to
    `return PmiCounts(0, 0, 0)` would pass the whole suite, and the
    zero-PMI contrast in test_end_to_end.py would prove nothing. Design spec
    line 252 makes the fresh-clone path an explicit success criterion.

    Exact counts, verified by execution 2026-08-01, not bounds.
    """
    assert FIXTURE.is_file(), (
        "the AP242 fixture must be committed, not fetched -- that is the whole "
        "point of it"
    )
    counts = read_pmi_counts(FIXTURE)
    assert counts == PmiCounts(dimensions=21, geometric_tolerances=6, datums=11)


def test_the_fixture_and_the_fetched_suite_disagree_about_counts():
    """Guards a reader that returns a constant regardless of its input.

    Skips without the fetched suite, but on a developer machine it proves the
    two files are distinguished. The fixture test above is the fresh-clone
    guarantee; this one is the stronger check when both are available.
    """
    if not FTC06.is_file():
        pytest.skip("NIST suite not fetched; run scripts/fetch_nist_pmi.py")
    assert read_pmi_counts(FIXTURE) != read_pmi_counts(FTC06)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_ap242_pmi.py -v`
Expected: FAIL on `test_reads_nonzero_pmi_from_the_committed_fixture` — the fixture file does not exist yet, so the `FIXTURE.is_file()` assertion fires.

- [ ] **Step 3: Commit the fixture and its provenance**

```bash
mkdir -p tests/fixtures
cp data/nist_pmi/nist_ctc_01_asme1_ap242-e1.stp tests/fixtures/
```

Create `tests/fixtures/NIST-PROVENANCE.md`:

```markdown
# NIST AP242 test fixture

`nist_ctc_01_asme1_ap242-e1.stp` (396,445 bytes) is one file from the NIST MBE
PMI Validation and Conformance Test Suite, redistributed here unmodified.

- Source archive: https://www.nist.gov/system/files/documents/noindex/2024/06/19/NIST-PMI-STEP-Files.zip
  (reached from https://www.nist.gov/document/nist-pmi-step-files)
- Fetcher for the full suite: `scripts/fetch_nist_pmi.py`
- Terms: NIST states the test cases, CAD models and STEP files "can be used
  without any restrictions", and asks for acknowledgement.

## Why this one is committed when the rest of the suite is gitignored

The full ~14 MB suite stays out of git and is reproducible via the fetcher. This
single file is committed because it is the ONLY positive control the semantic-PMI
read path has on a fresh clone. Without it, every oracle assertion a fresh clone
runs is either a zero-count or a FileNotFoundError, and a `read_pmi_counts`
stubbed to return zeros would pass the entire suite. Design spec line 252 makes
"fresh clone, no licence, runs end-to-end" an explicit success criterion.

It is the smallest AP242 file in the suite carrying non-trivial PMI: 21
dimensions, 6 geometric tolerances, 11 datums.
```

Confirm `.gitignore`'s `data/nist_pmi/` entry does not also match `tests/fixtures/`:

```bash
git check-ignore -v tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp || echo "NOT ignored - good"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_ap242_pmi.py -v`
Expected: PASS, 4 tests.

Prove the fresh-clone claim rather than asserting it — temporarily move the fetched suite aside and confirm the fixture test still runs:

```bash
mv data/nist_pmi data/nist_pmi.bak
python -m pytest tests/test_ap242_pmi.py -v
mv data/nist_pmi.bak data/nist_pmi
```

Expected in the middle run: the fixture test **PASSES** (it does not depend on the fetched data), while the 47/27/59 test and the disagreement test skip. Paste that output. Restore the directory and re-confirm all four pass.

Then the full suite: `python -m pytest -q -m "not slow"`.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/ tests/test_ap242_pmi.py
git commit -m "test: commit one AP242 fixture as the oracle's fresh-clone positive control"
```

---

