# Task 8 report: Fetch and verify the NIST conformance suite

## Status: DONE

## Step 1-2: RED — test written, run, and confirmed failing

`tests/test_fetch_nist.py` was written exactly as given in the brief. Ran
`python -m pytest tests/test_fetch_nist.py -v` before the fetcher existed.
Verbatim output:

```
collecting ... collected 3 items

tests/test_fetch_nist.py::test_fetcher_script_exists FAILED              [ 33%]
tests/test_fetch_nist.py::test_fetcher_records_the_source_url_and_licence_statement FAILED [ 66%]
tests/test_fetch_nist.py::test_nist_payload_is_gitignored FAILED         [100%]

================================== FAILURES ===================================
_________________________ test_fetcher_script_exists __________________________

    def test_fetcher_script_exists():
>       assert SCRIPT.is_file()
E       AssertionError: assert False
E        +  where False = is_file()
E        +    where is_file = WindowsPath('C:/Users/harsh/Downloads/Projects/Paper1/scripts/fetch_nist_pmi.py').is_file

tests\test_fetch_nist.py:9: AssertionError
__________ test_fetcher_records_the_source_url_and_licence_statement __________

    def test_fetcher_records_the_source_url_and_licence_statement():
>       text = SCRIPT.read_text(encoding="utf-8")
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\harsh\\Downloads\\Projects\\Paper1\\scripts\\fetch_nist_pmi.py'

_______________________ test_nist_payload_is_gitignored _______________________

    def test_nist_payload_is_gitignored():
        ignore = (REPO / ".gitignore").read_text(encoding="utf-8")
>       assert "data/nist_pmi/" in ignore
E       AssertionError: assert 'data/nist_pmi/' in '__pycache__/\n*.py[cod]\n.pytest_cache/\n.coverage\n*.egg-info/\nbuild/\ndist/\n.venv/\nresults/\n\n# Literature PDFs: ~617MB, fully reproducible via scripts/fetch_literature.sh.\n# The index and fetch log ARE tracked, so the corpus stays auditable.\npapers/literature/*.pdf\n'

=========================== short test summary info ===========================
FAILED tests/test_fetch_nist.py::test_fetcher_script_exists - AssertionError:...
FAILED tests/test_fetch_nist.py::test_fetcher_records_the_source_url_and_licence_statement
FAILED tests/test_fetch_nist.py::test_nist_payload_is_gitignored - AssertionE...
============================== 3 failed in 0.06s ==============================
```

All 3 failed as expected: the script did not exist, and the `.gitignore` entry
was not yet present.

## Step 3: Fetcher written, one deviation from the brief's literal text

`scripts/fetch_nist_pmi.py` was written per the brief, and the `.gitignore`
entry was appended exactly as given.

**Deviation (required, minimal):** the brief's literal docstring text wraps
across a line break as `"can be used without any\nrestrictions"`. Because the
brief's own test asserts the plain substring `"without any restrictions"`
(single spaces, no embedded newline), the literal text as given in the brief
would fail the brief's own test. I re-wrapped the docstring lines so the
phrase `without any restrictions` appears contiguously on one line (line 8 of
the script), without changing any word or the meaning. No other content,
filenames, URLs, or logic were changed from the brief.

## Step 4: Fetcher run — network download

Ran `python scripts/fetch_nist_pmi.py` (approved one-time network download
from the URL in the brief, nothing else fetched).

Exit code: `0`

stdout:
```
downloading https://www.nist.gov/system/files/documents/noindex/2024/06/19/NIST-PMI-STEP-Files.zip
archive: 13976599 bytes
extracted 33 STEP files, 17 AP242
```

Archive size ~13.3 MiB (13,976,599 bytes), matching the brief's "~14 MB"
estimate. 17 AP242 `.stp` files extracted, matching `EXPECTED_AP242_FILES`.

## Step 5: `tests/test_fetch_nist.py` + `tests/test_ap242_pmi.py`

Ran `python -m pytest tests/test_fetch_nist.py tests/test_ap242_pmi.py -v`
after the docstring fix and after the fetch succeeded:

```
collecting ... collected 5 items

tests/test_fetch_nist.py::test_fetcher_script_exists PASSED              [ 20%]
tests/test_fetch_nist.py::test_fetcher_records_the_source_url_and_licence_statement PASSED [ 40%]
tests/test_fetch_nist.py::test_nist_payload_is_gitignored PASSED         [ 60%]
tests/test_ap242_pmi.py::test_reads_semantic_pmi_from_nist_ftc06 PASSED  [ 80%]
tests/test_ap242_pmi.py::test_missing_file_raises PASSED                 [100%]

============================== 5 passed in 0.56s ==============================
```

**Exact counts confirmed.** `tests/test_ap242_pmi.py::test_reads_semantic_pmi_from_nist_ftc06`
asserts `PmiCounts(dimensions=47, geometric_tolerances=27, datums=59)` for
`data/nist_pmi/nist_ftc_06_asme1_ap242-e2.stp`, and this test PASSED — meaning
`read_pmi_counts()` produced exactly 47 dimensions, 27 geometric tolerances,
and 59 datums on this run. No discrepancy was observed; the pre-registered
counts from Task 7 hold against the real NIST oracle file now that it exists.

Task 7's tests, previously SKIPPED (no `data/nist_pmi/`), ran for the first
time in this session and both passed.

## Step 6: Full suite, no regressions

Ran `python -m pytest -q -m "not slow"`:

```
........................................................................ [ 48%]
........................................................................ [ 96%]
......                                                                   [100%]
150 passed, 2 deselected in 16.55s
```

150 passed, 2 deselected (slow/Monte Carlo convergence tests, correctly
excluded by the marker). No failures, no regressions.

## Step 7: No payload committed

Before staging:

```
$ git status --short
 M .gitignore
?? scripts/fetch_nist_pmi.py
?? tests/test_fetch_nist.py
```

`data/nist_pmi/` (containing the ~14 MB zip and 33 extracted `.stp` files)
does not appear at all — correctly gitignored, confirming the `.gitignore`
entry takes effect immediately.

After `git add scripts/fetch_nist_pmi.py tests/test_fetch_nist.py .gitignore`:

```
M  .gitignore
A  scripts/fetch_nist_pmi.py
A  tests/test_fetch_nist.py
```

Exactly the three intended files staged. Committed with:

```
feat: fetch and verify the NIST PMI conformance suite

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

Commit SHA: `ae2b3ac837d77322d74693cf4b71cc025990a5a3`

Post-commit `git status --short` is clean (no output). `git show --stat HEAD`
confirms exactly 3 files changed: `.gitignore`, `scripts/fetch_nist_pmi.py`,
`tests/test_fetch_nist.py` — no `data/` payload in the commit.

## Self-review

- Diffed the full commit (`git show HEAD`) against the brief's literal code
  blocks. The only difference is the docstring line-wrap fix described above
  (required for the brief's own test to pass as written); URL, filenames,
  `EXPECTED_AP242_FILES`, gitignore comment/entry, and commit message all
  match the brief verbatim.
- Confirmed no retry logic, checksums, progress bars, or extra CLI flags were
  added beyond what the brief specifies.
- Confirmed `validation/ap242_pmi.py` (Task 7) was not touched — this task
  only added the fetcher, its test, and the gitignore entry.
- Confirmed no module under `src/tolcad/` was touched (this task doesn't
  touch `src/` at all), preserving the core/validation import boundary.
- Confirmed the payload directory (`data/nist_pmi/`) is real on disk (34
  files: the zip + 33 `.stp`, 17 of them AP242) but absent from git tracking
  and from the commit.

## Concerns

None. All exact counts held (47/27/59), the fetcher behaved as specified, and
no regressions were introduced.

---

# Fix round 1: execute `main()` against a synthetic archive

## Finding (Important, plan-mandated — human ruled FIX)

The original three tests in `tests/test_fetch_nist.py` only checked that the
script file exists and grepped two substrings out of its source text and out
of `.gitignore`. `main()` itself — in particular the AP242-count mismatch
guard (`len(ap242) != EXPECTED_AP242_FILES` -> warn to stderr -> `return 1`)
— had zero automated coverage. That branch is the one that would catch NIST
silently changing the archive upstream and corrupting the oracle, and it had
only ever been exercised once, manually, in the case where the count
happened to match.

## Fix

Added two tests to `tests/test_fetch_nist.py` (existing three left
untouched, nothing replaced):

- `test_main_returns_1_and_warns_when_ap242_count_mismatches` — builds a
  real ZIP named `NIST-PMI-STEP-Files.zip` in `tmp_path` with 2 fake
  `*ap242*.stp` members (wrong; expected 17), points the module's `DEST` at
  `tmp_path` via `monkeypatch.setattr`, calls `main()`, and asserts it
  returns `1` and that `"WARNING"` / `"expected 17"` land in `capsys`'s
  captured stderr.
- `test_main_returns_0_when_ap242_count_matches` — the mandatory positive
  control: identical construction but with exactly 17 fake AP242 members,
  asserting `main()` returns `0` and stderr is empty. Without this, the
  negative test alone could not distinguish "correctly detects mismatch"
  from "always returns 1" — a test that cannot fail.

Both tests load `scripts/fetch_nist_pmi.py` by path via
`importlib.util.spec_from_file_location` (no `__init__.py` in `scripts/`,
so it isn't an importable package) using a shared `_load_fetch_module()`
helper, and both route through a shared `_network_blocked_module()` helper
that:

1. Loads a fresh module object.
2. `monkeypatch.setattr(module, "DEST", tmp_path)` — redirects the archive
   location so nothing touches the real `data/nist_pmi/`.
3. `monkeypatch.setattr(module, "URL", "http://example.invalid/...")` — belt
   and suspenders; harmless if unreached since the archive already exists.
4. `monkeypatch.setattr(module.urllib.request, "urlopen", _boom)` where
   `_boom` raises `AssertionError("network access attempted in a fetcher
   test")` — makes any accidental network path fail the test immediately
   rather than silently downloading 14 MB.

`_build_fake_archive(dest, ap242_count)` pre-creates
`dest/"NIST-PMI-STEP-Files.zip"` with `ap242_count` trivial placeholder
`.stp` members before `main()` runs, so `archive.is_file()` is already
`True` when `main()` checks it and the entire download branch (`if not
archive.is_file(): ...`) is structurally never entered — confirmed by the
patched `urlopen` never firing (both tests passed, so `_boom` was never
called).

**No production code was changed.** `scripts/fetch_nist_pmi.py` is
untouched; `monkeypatch.setattr` on `DEST`/`URL`/`urlopen` was sufficient
because `main()` looks up `DEST`/`URL` as module globals at call time, so
patching the loaded module's attributes before invoking `main()` is
enough — no refactor for testability was needed.

## Verification

### 1. `pytest tests/test_fetch_nist.py -v`

```
collecting ... collected 5 items

tests/test_fetch_nist.py::test_fetcher_script_exists PASSED              [ 20%]
tests/test_fetch_nist.py::test_fetcher_records_the_source_url_and_licence_statement PASSED [ 40%]
tests/test_fetch_nist.py::test_nist_payload_is_gitignored PASSED         [ 60%]
tests/test_fetch_nist.py::test_main_returns_1_and_warns_when_ap242_count_mismatches PASSED [ 80%]
tests/test_fetch_nist.py::test_main_returns_0_when_ap242_count_matches PASSED [100%]

============================== 5 passed in 0.06s ==============================
```

All 5 pass, including both new tests. 0.06s total confirms no network
round-trip occurred (a real download would take several seconds at
minimum).

### 2. Deliberate-failure check (is the negative test non-vacuous?)

Temporarily changed the negative test's fake-archive construction from
`ap242_count=2` (wrong) to `ap242_count=17` (matching — i.e. deliberately
violating the test's own premise that the count should mismatch), then ran
just that test:

```
$ python -m pytest tests/test_fetch_nist.py::test_main_returns_1_and_warns_when_ap242_count_mismatches -v

tests/test_fetch_nist.py::test_main_returns_1_and_warns_when_ap242_count_mismatches FAILED [100%]

================================== FAILURES ===================================
__________ test_main_returns_1_and_warns_when_ap242_count_mismatches __________

    def test_main_returns_1_and_warns_when_ap242_count_mismatches(
        tmp_path, monkeypatch, capsys
    ):
        module = _network_blocked_module(tmp_path, monkeypatch)
        _build_fake_archive(tmp_path, ap242_count=17)  # DELIBERATE: should be 2 (wrong)

        result = module.main()

>       assert result == 1
E       assert 0 == 1

tests\test_fetch_nist.py:70: AssertionError
---------------------------- Captured stdout call -----------------------------
archive: 2691 bytes
extracted 17 STEP files, 17 AP242
=========================== short test summary info ===========================
FAILED tests/test_fetch_nist.py::test_main_returns_1_and_warns_when_ap242_count_mismatches
============================== 1 failed in 0.08s ==============================
```

FAILED as expected (`assert 0 == 1`) — proves the test can actually fail,
i.e. it is measuring something real and is not vacuously true. Reverted the
change immediately back to `ap242_count=2`, then re-ran the full file to
confirm all 5 pass again:

```
============================== 5 passed in 0.06s ==============================
```

(full output identical to the block under item 1 above)

### 3. Full suite

```
$ python -m pytest -q -m "not slow"
........................................................................ [ 46%]
........................................................................ [ 92%]
...........                                                              [100%]
155 passed, 2 deselected in 16.73s
```

155 passed (153 baseline as of commit `bbac3dc`, plus the 2 new tests added
here), 2 deselected (slow). No regressions.

### 4. No network access, real NIST data untouched

- Both `_network_blocked_module` calls patch `urlopen` to raise; since all
  5 tests passed, that patched function was never invoked — no network
  call was reachable, let alone made.
- Total runtime for the 5 fetch tests was 0.06s both times, and the full
  155-test suite ran in 16.73s (essentially identical to the 16.55s/150-test
  baseline from the original task run) — consistent with zero network
  latency added.
- `data/nist_pmi/nist_ftc_06_asme1_ap242-e2.stp` verified present after the
  fix, same size (1,971,192 bytes) and timestamp (Aug 1 03:22) as the
  original fetch; `data/nist_pmi/*.stp` still totals 33 files.
- `git status --short` after the fix showed only `tests/test_fetch_nist.py`
  modified — no `data/` payload ever appeared as untracked/staged.

## Commit

Committed the test-only fix on its own:

```
test: execute fetch_nist_pmi.main() against synthetic archives

Add negative and positive coverage for the AP242 mismatch guard: a
non-matching fake archive must return 1 and warn to stderr, a matching
one must return 0. Both load the script by path and monkeypatch DEST
plus urlopen so no test ever touches the network or the real
data/nist_pmi/ fixtures.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

Commit SHA: `b6f89b735bb0df746fcdd8a1a877ef1fad45a8ce`

`git status --short` post-commit is clean. Only `tests/test_fetch_nist.py`
was changed (1 file, 62 insertions) — `scripts/fetch_nist_pmi.py` was not
touched.

## Concerns

None. Both the mismatch test and its mandatory positive control pass, the
negative test was proven non-vacuous by the deliberate-failure check, no
network access occurred, the real NIST fixture is untouched, and the full
suite shows no regressions (155 passed vs. the 153-passed baseline, the
delta being exactly the 2 new tests).
