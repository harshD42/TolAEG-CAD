# Task 4 report: committed AP242 fixture as the oracle's fresh-clone positive control

## Baseline

Confirmed at HEAD (164e83a, branch `feat/pre-registration-prep`):

```
208 passed, 2 deselected in 23.07s
```

## Step 1-2: RED

Appended the two tests verbatim to `tests/test_ap242_pmi.py` (`test_reads_nonzero_pmi_from_the_committed_fixture`
and `test_the_fixture_and_the_fetched_suite_disagree_about_counts`), plus the `FIXTURE` path constant.

`python -m pytest tests/test_ap242_pmi.py -v`:

```
tests/test_ap242_pmi.py::test_reads_semantic_pmi_from_nist_ftc06 PASSED  [ 25%]
tests/test_ap242_pmi.py::test_missing_file_raises PASSED                 [ 50%]
tests/test_ap242_pmi.py::test_reads_nonzero_pmi_from_the_committed_fixture FAILED [ 75%]
tests/test_ap242_pmi.py::test_the_fixture_and_the_fetched_suite_disagree_about_counts FAILED [100%]

================================== FAILURES ===================================
______________ test_reads_nonzero_pmi_from_the_committed_fixture ______________
>       assert FIXTURE.is_file(), (
            "the AP242 fixture must be committed, not fetched -- that is the whole "
            "point of it"
        )
E       AssertionError: the AP242 fixture must be committed, not fetched -- that is the whole point of it
E       assert False
E        +  where False = is_file()
E        +    where is_file = WindowsPath('C:/Users/harsh/Downloads/Projects/Paper1/tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp').is_file
________ test_the_fixture_and_the_fetched_suite_disagree_about_counts _________
>       assert read_pmi_counts(FIXTURE) != read_pmi_counts(FTC06)
E       FileNotFoundError: no such STEP file: C:\Users\harsh\Downloads\Projects\Paper1\tests\fixtures\nist_ctc_01_asme1_ap242-e1.stp
========================= 2 failed, 2 passed in 0.62s =========================
```

Failed exactly as expected: fixture not present yet.

## Step 3: Fixture and provenance

- Created `tests/fixtures/`, copied `data/nist_pmi/nist_ctc_01_asme1_ap242-e1.stp` -> `tests/fixtures/`. Confirmed
  396,445 bytes on disk after copy.
- Wrote `tests/fixtures/NIST-PROVENANCE.md` exactly per the brief.
- `.gitignore` confirmation:

```
$ git check-ignore -v tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp || echo "NOT ignored - good"
NOT ignored - good
```

## Step 4: GREEN

`python -m pytest tests/test_ap242_pmi.py -v`:

```
tests/test_ap242_pmi.py::test_reads_semantic_pmi_from_nist_ftc06 PASSED  [ 25%]
tests/test_ap242_pmi.py::test_missing_file_raises PASSED                 [ 50%]
tests/test_ap242_pmi.py::test_reads_nonzero_pmi_from_the_committed_fixture PASSED [ 75%]
tests/test_ap242_pmi.py::test_the_fixture_and_the_fetched_suite_disagree_about_counts PASSED [100%]

============================== 4 passed in 0.81s ==============================
```

## Step 5: Simulated fresh clone

```
$ mv data/nist_pmi data/nist_pmi.bak
$ python -m pytest tests/test_ap242_pmi.py -v
tests/test_ap242_pmi.py::test_reads_semantic_pmi_from_nist_ftc06 SKIPPED [ 25%]
tests/test_ap242_pmi.py::test_missing_file_raises PASSED                 [ 50%]
tests/test_ap242_pmi.py::test_reads_nonzero_pmi_from_the_committed_fixture PASSED [ 75%]
tests/test_ap242_pmi.py::test_the_fixture_and_the_fetched_suite_disagree_about_counts SKIPPED [100%]
======================== 2 passed, 2 skipped in 0.49s =========================
```

The fixture test (`test_reads_nonzero_pmi_from_the_committed_fixture`) PASSED with no fetched suite present;
the 47/27/59 test and the disagreement test SKIPPED as designed. `test_missing_file_raises` also passes
independent of the fetched suite (it only asserts on a nonexistent path), so the net simulated-fresh-clone
result is 2 passed / 2 skipped, with the fixture test being the load-bearing one.

Restored:

```
$ mv data/nist_pmi.bak data/nist_pmi
$ ls data/nist_pmi | wc -l
34
```

Re-confirmed all four pass post-restoration:

```
============================== 4 passed in 0.86s ==============================
```

## Step 6: Full suite

```
python -m pytest -q -m "not slow"
210 passed, 2 deselected in 24.49s
```

(208 baseline + 2 new tests = 210.)

## Step 7-8: Commit

`git status --short` before staging showed exactly:

```
 M tests/test_ap242_pmi.py
?? tests/fixtures/
```

Staged and committed exactly `tests/fixtures/` and `tests/test_ap242_pmi.py`. Commit:

```
d312ad64e03714a47fb586cc464419bb8c50e04a
"test: commit one AP242 fixture as the oracle's fresh-clone positive control"

 tests/fixtures/NIST-PROVENANCE.md             |   22 +
 tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp | 4706 +++++++++++++++++++++++++
 tests/test_ap242_pmi.py                       |   34 +
 3 files changed, 4762 insertions(+)
```

`git status --short` after: clean.

## Step 9: Self-review — found and fixed a real bug

While self-reviewing the diff, I checked the committed blob's byte count against the promised 396,445 bytes
(the brief treats this number as load-bearing, and `NIST-PROVENANCE.md` claims the file is "redistributed here
unmodified"):

```
$ git cat-file -s HEAD:tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp
391739
```

That's **391,739 bytes, not 396,445** — a 4,706-byte discrepancy (matching the file's line count). Root cause:
this repo has `core.autocrlf=true`, and the STEP file's ASCII text uses CRLF line endings, so git silently
normalized CRLF -> LF when adding it to the object store. Locally this was invisible: `ls -la` on the working
copy and the test suite both showed/used 396,445 bytes, because `autocrlf=true` re-expands LF -> CRLF on
checkout, round-tripping correctly *on this machine's config*. But a clone with a different `core.autocrlf`
setting (the common Linux/CI default, or `autocrlf=input`) would check out the LF-only 391,739-byte blob —
wrong byte count, different SHA-256, and no longer byte-identical to the NIST original, directly undermining
this task's purpose (a byte-identical, reproducible fresh-clone fixture) and the provenance file's "unmodified"
claim.

Confirmed via hash comparison:

```
original (data/nist_pmi):    85a5752da05f53c456ca3a9e038c90358e1d5a3141d1f0d6e5f0970f2356e821
working copy (tests/fixtures): 85a5752da05f53c456ca3a9e038c90358e1d5a3141d1f0d6e5f0970f2356e821
committed blob (HEAD):          341cea888fb316673ed683e59391c11b4f96cff2542d9387e135f06682dbd7  <- MISMATCH
```

Fix: added `.gitattributes` with `*.stp binary` (no existing `.gitattributes` and no other tracked `.stp` files,
so this is narrowly scoped and touches nothing else), then `git add --renormalize` on the fixture to rewrite the
stored blob byte-identically, and committed the correction separately (did not amend, per repo convention of
preferring new commits):

```
7ba4e878b701ccb5a501c0e87ce23fc60eec1bdc
"fix: mark .stp fixtures binary so they are byte-identical across clones"

 .gitattributes                                |   5 +++++
 tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp | Bin 391739 -> 396445 bytes
 2 files changed, 5 insertions(+)
```

Post-fix verification:

```
$ git cat-file -s HEAD:tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp
396445
$ git cat-file -p HEAD:tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp | sha256sum
85a5752da05f53c456ca3a9e038c90358e1d5a3141d1f0d6e5f0970f2356e821  (matches original exactly)
```

Re-ran everything after the fix:

```
tests/test_ap242_pmi.py -v: 4 passed in 0.82s
python -m pytest -q -m "not slow": 210 passed, 2 deselected in 23.43s
```

`git status --short` is clean; `git log --oneline -3`:

```
7ba4e87 fix: mark .stp fixtures binary so they are byte-identical across clones
d312ad6 test: commit one AP242 fixture as the oracle's fresh-clone positive control
164e83a feat: record the projected tolerance zone B-4 assumes
```

## Committed files (across both commits)

- `tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp` (396,445 bytes, byte-identical to the NIST source)
- `tests/fixtures/NIST-PROVENANCE.md`
- `tests/test_ap242_pmi.py` (modified: two tests + `FIXTURE` constant appended, verbatim per brief)
- `.gitattributes` (new, `*.stp binary` only — a self-review correction, not part of the original brief, but
  required to make the "byte-identical fresh-clone fixture" guarantee actually hold across machines)

No files from `data/nist_pmi/` were staged or committed other than the one copy into `tests/fixtures/`.
`data/nist_pmi/` was fully restored (34 entries) after the simulated-fresh-clone test.

## Concerns / notes for the requester

1. **The `.gitattributes` addition was not in the brief.** It was necessary — without it, the committed fixture
   silently fails to be byte-identical on any clone with a different `core.autocrlf` setting than this machine's
   (`true`), which contradicts both the task's exact-byte-count requirement and the provenance file's
   "redistributed here unmodified" claim. I judged this in-scope for "self-review your diff" and fixed it with a
   second, separate commit rather than amending, but flagging it explicitly in case the two-commit result isn't
   what was wanted (e.g. if a single squashed commit is preferred, or if `.gitattributes` should live elsewhere).
2. Design spec §7 thresholds and `scripts/gate_a.py` were not touched. No core module was modified;
   `validation/` was only read from, not changed, by the new tests.
