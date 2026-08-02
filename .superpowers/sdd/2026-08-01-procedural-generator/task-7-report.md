# Task 7 report: Read semantic PMI from AP242

## Summary

Implemented `validation/ap242_pmi.py` and `tests/test_ap242_pmi.py` exactly per
the brief, following TDD. The module is complementary to `validation/nist_pmi.py`
(not modified) and lives entirely in `validation/`, which stays one-directional
with respect to core (`src/tolcad/`).

**Important caveat, stated plainly:** `data/nist_pmi/nist_ftc_06_asme1_ap242-e2.stp`
has not been downloaded (Task 8, pending human approval). Therefore
`test_reads_semantic_pmi_from_nist_ftc06` has **not actually been exercised
against real data**. It SKIPPED via the module's `pytestmark` skipif, exactly as
expected. The `47 / 27 / 59` counts asserted in that test are unverified in this
run — they were verified by execution against real OCCT/NIST data prior to this
task (per the brief), but not by me, in this session, right now.

## Step 2 — RED (verbatim)

Command: `python -m pytest tests/test_ap242_pmi.py -v`

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\harsh\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\harsh\Downloads\Projects\Paper1
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 0 items / 1 error

=================================== ERRORS ====================================
__________________ ERROR collecting tests/test_ap242_pmi.py ___________________
ImportError while importing test module 'C:\Users\harsh\Downloads\Projects\Paper1\tests\test_ap242_pmi.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_ap242_pmi.py:6: in <module>
    from validation.ap242_pmi import PmiCounts, read_pmi_counts
E   ModuleNotFoundError: No module named 'validation.ap242_pmi'
=========================== short test summary info ===========================
ERROR tests/test_ap242_pmi.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.49s ===============================
```

This matches the expected RED per the brief: `ModuleNotFoundError` at collection,
before the skipif can take effect.

## Step 4 — post-implementation result

Command: `python -m pytest tests/test_ap242_pmi.py -v`

```
collecting ... collected 2 items

tests/test_ap242_pmi.py::test_reads_semantic_pmi_from_nist_ftc06 SKIPPED [ 50%]
tests/test_ap242_pmi.py::test_missing_file_raises SKIPPED (NIST suit...) [100%]

============================= 2 skipped in 0.42s ==============================
```

**Skip reason (stated plainly):** both tests are gated by module-level
`pytestmark = pytest.mark.skipif(not FTC06.is_file(), reason="NIST suite not
fetched; run scripts/fetch_nist_pmi.py")`. `data/nist_pmi/` does not exist in
this environment, so `FTC06.is_file()` is `False` and both tests skip
unconditionally — including `test_missing_file_raises`, which does not itself
depend on the NIST fixture but is skipped anyway because the skipif is applied
module-wide via `pytestmark`. Neither assertion — including the FileNotFoundError
one — has been exercised through pytest in this run; it was however exercised
directly at the Python REPL in the sanity check below, outside pytest.

This is 2 SKIPPED, not 2 PASSED. This is the expected/correct outcome for this
task per the brief; Task 8 (fetching the NIST suite) is required before this
test can actually run and validate the 47/27/59 counts.

## Full-suite result

Command: `python -m pytest -q -m "not slow"`

```
....................................ss.................................. [ 48%]
........................................................................ [ 97%]
...                                                                      [100%]
145 passed, 2 skipped, 2 deselected in 16.07s
```

No regressions. The 2 skipped are the new `test_ap242_pmi.py` tests; 2 deselected
are pre-existing slow/Monte-Carlo tests excluded by `-m "not slow"`.

Also ran `tests/test_architecture.py` directly as an extra check (not required by
the brief, but relevant to the core/validation boundary constraint):

```
tests/test_architecture.py::test_bare_relative_import_of_validation_is_caught PASSED
tests/test_architecture.py::test_dynamic_import_of_validation_is_caught PASSED
tests/test_architecture.py::test_bare_name_import_module_call_is_caught PASSED
tests/test_architecture.py::test_dunder_import_as_attribute_is_caught PASSED
tests/test_architecture.py::test_exec_with_validation_import_is_caught PASSED
tests/test_architecture.py::test_eval_with_validation_import_is_caught PASSED
tests/test_architecture.py::test_innocent_exec_call_is_not_flagged PASSED
tests/test_architecture.py::test_no_core_module_imports_validation PASSED
tests/test_architecture.py::test_core_imports_without_numpy_optional_deps_beyond_declared PASSED
tests/test_architecture.py::test_checker_core_does_not_import_cad_libraries PASSED

10 passed in 0.07s
```

Confirms no core module imports `validation` (or `validation.ap242_pmi`
specifically) and the checker core remains free of CAD libraries.

## Sanity checks

1. Module import and dataclass construction:

```
$ python -c "from validation.ap242_pmi import read_pmi_counts, PmiCounts; print(PmiCounts(1,2,3))"
PmiCounts(dimensions=1, geometric_tolerances=2, datums=3)
```

Confirms the module imports cleanly and all OCP submodule imports
(`OCP.IFSelect`, `OCP.STEPCAFControl`, `OCP.TCollection`, `OCP.TDF`,
`OCP.TDocStd`, `OCP.XCAFDoc`) resolve without error in this environment.

2. FileNotFoundError on nonexistent path:

```
$ python -c "from validation.ap242_pmi import read_pmi_counts; read_pmi_counts('nope.stp')"
Traceback (most recent call last):
  ...
  File "C:\Users\harsh\Downloads\Projects\Paper1\validation\ap242_pmi.py", line 39, in read_pmi_counts
    raise FileNotFoundError(f"no such STEP file: {step_path}")
FileNotFoundError: no such STEP file: nope.stp
```

Confirms `read_pmi_counts` raises `FileNotFoundError` for a missing path, exactly
as required — this assertion does not depend on NIST data and is genuinely
exercised (both here at the REPL, though not yet through pytest since the whole
module is skipped when the fixture directory is absent).

## Commit

SHA: `a09ee2fd09196772dc44ccc20d7c0e8b1f505e18`

Message:
```
feat: read semantic PMI from STEP AP242

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

Files changed: `validation/ap242_pmi.py` (new), `tests/test_ap242_pmi.py` (new).
2 files changed, 93 insertions(+), 0 deletions.

## Self-review of the diff

- Confirmed `git status` showed only these two files as untracked before staging
  — no accidental inclusion of other changes.
- Confirmed the code in both files matches the brief's exact call sequence and
  test bodies verbatim; no restructuring, no added extraction of tolerance
  values or datum names, no extra OCP calls beyond `SetGDTMode`, `SetNameMode`,
  `SetColorMode`, `ReadFile`, `Transfer`, and the three `DimTolTool_s` label
  getters.
- Confirmed `validation/nist_pmi.py` and `validation/tolanalyst.py` were not
  touched, and `validation/__init__.py` did not need changes (no re-export
  required by the brief).
- Confirmed `tests/test_architecture.py` was not modified and still passes,
  verifying the core-never-imports-validation constraint holds with the new
  module present.
- Confirmed the docstring in `ap242_pmi.py` matches the brief's rationale for
  living in `validation/` and for semantic-only (not graphical) PMI.
- Git emitted a line-ending warning (LF -> CRLF) on both new files consistent
  with existing repo `.gitattributes`/Windows checkout behavior; this is
  environmental, not a content issue, and matches how other files in the repo
  are handled.

## Concerns

- The headline test (`test_reads_semantic_pmi_from_nist_ftc06`) remains
  unverified against real data in this environment. It will need to be re-run
  once Task 8 fetches `data/nist_pmi/nist_ftc_06_asme1_ap242-e2.stp`, and only
  then can the 47/27/59 counts be confirmed to still hold with the OCP version
  installed here.
- No other concerns; implementation matches the brief exactly, no regressions,
  architecture boundary intact.

---

## Fix round 1 — scope the NIST-fixture skipif to the one test that needs it

### Finding addressed (Important, plan-mandated, human-approved: FIX)

`tests/test_ap242_pmi.py` used a module-level `pytestmark = pytest.mark.skipif(...)`
that skipped both tests whenever `data/nist_pmi/nist_ftc_06_asme1_ap242-e2.stp`
was absent. That is correct for `test_reads_semantic_pmi_from_nist_ftc06`, which
needs the fixture, but wrong for `test_missing_file_raises`, which asserts only
that a nonexistent path raises `FileNotFoundError` and has zero dependency on
NIST data. It was being skipped under a reason ("NIST suite not fetched") that
wasn't true of it, discarding real, currently-runnable coverage on any machine
without the fetched data — an instance of "the metric that cannot fail."

### Fix applied

Covering test file: `tests/test_ap242_pmi.py` (only file touched).

Removed the module-level `pytestmark` and applied the same `pytest.mark.skipif`
(same condition, same reason string, unchanged) as a decorator directly on
`test_reads_semantic_pmi_from_nist_ftc06` only. `test_missing_file_raises` is
now gated solely by the existing module-level `pytest.importorskip("OCP", ...)`.
Nothing else was changed: `validation/ap242_pmi.py` untouched, expected counts
untouched, OCP call sequence untouched.

Diff:
```diff
 NIST_DIR = pathlib.Path(__file__).parent.parent / "data" / "nist_pmi"
 FTC06 = NIST_DIR / "nist_ftc_06_asme1_ap242-e2.stp"
 
-pytestmark = pytest.mark.skipif(
+
+@pytest.mark.skipif(
     not FTC06.is_file(),
     reason="NIST suite not fetched; run scripts/fetch_nist_pmi.py",
 )
-
-
 def test_reads_semantic_pmi_from_nist_ftc06():
     """Verified by execution 2026-08-01: 47 dimensions, 27 geotols, 59 datums.
```

### Context change since the original implementation

Task 8 has since run: `data/nist_pmi/` now exists with the full fetched NIST
suite, confirmed present via `ls data/nist_pmi/` (33 files, including
`nist_ftc_06_asme1_ap242-e2.stp`). The exact counts (47/27/59) hold against the
real file with the OCP version installed in this environment.

### Verification commands and verbatim output

**Step 1 — run with fixture present, expect 2 passed:**

Command: `python -m pytest tests/test_ap242_pmi.py -v`

```
collecting ... collected 2 items

tests/test_ap242_pmi.py::test_reads_semantic_pmi_from_nist_ftc06 PASSED  [ 50%]
tests/test_ap242_pmi.py::test_missing_file_raises PASSED                 [100%]

============================== 2 passed in 0.59s ==============================
```

This is the first time the headline assertion (47 dimensions / 27 geometric
tolerances / 59 datums against the real NIST FTC06 file) has actually been
exercised and confirmed in this environment — resolving the "unverified"
concern noted in the original report above.

**Step 2 — simulate a fresh clone by temporarily renaming the fixture, expect
1 passed (test_missing_file_raises) / 1 skipped (the NIST one). This is the
load-bearing evidence that the fix works — before the fix this would have
been 2 skipped:**

Commands:
```
mv data/nist_pmi/nist_ftc_06_asme1_ap242-e2.stp data/nist_pmi/nist_ftc_06_asme1_ap242-e2.stp.bak
python -m pytest tests/test_ap242_pmi.py -v
```

Verbatim output:
```
collecting ... collected 2 items

tests/test_ap242_pmi.py::test_reads_semantic_pmi_from_nist_ftc06 SKIPPED [ 50%]
tests/test_ap242_pmi.py::test_missing_file_raises PASSED                 [100%]

======================== 1 passed, 1 skipped in 0.43s =========================
```

Confirmed: `test_missing_file_raises` now genuinely runs and passes with the
NIST fixture absent, proving its coverage no longer depends on data that has
nothing to do with what it asserts.

**Step 3 — restore the fixture and re-confirm 2 passed:**

Commands:
```
mv data/nist_pmi/nist_ftc_06_asme1_ap242-e2.stp.bak data/nist_pmi/nist_ftc_06_asme1_ap242-e2.stp
python -m pytest tests/test_ap242_pmi.py -v
```

Verbatim output:
```
collecting ... collected 2 items

tests/test_ap242_pmi.py::test_reads_semantic_pmi_from_nist_ftc06 PASSED  [ 50%]
tests/test_ap242_pmi.py::test_missing_file_raises PASSED                 [100%]

============================== 2 passed in 0.56s ==============================
```

File restored to its original name and location; verified present via
`ls data/nist_pmi/ | grep ftc_06` showing `nist_ftc_06_asme1_ap242-e2.stp`
(the `.bak` name no longer present). It remains gitignored data, unaffected by
version control either way, and is intact for Task 9.

**Step 4 — full suite, confirm no regressions:**

Command: `python -m pytest -q -m "not slow"`

```
........................................................................ [ 48%]
........................................................................ [ 96%]
......                                                                   [100%]
150 passed, 2 deselected in 16.52s
```

Matches the expected 150 passed, 2 deselected (up from 145 passed / 2 skipped
in the original report, now that both `test_ap242_pmi.py` tests genuinely run
and pass with Task 8's data present).

### Self-review of the fix diff

- `git diff tests/test_ap242_pmi.py` before committing showed exactly the
  intended change: `pytestmark` removed, same `pytest.mark.skipif(...)` object
  (identical condition, identical reason string) moved to decorate only
  `test_reads_semantic_pmi_from_nist_ftc06`. No other lines touched.
- `git status` before staging showed only `tests/test_ap242_pmi.py` as
  modified — `validation/ap242_pmi.py` untouched, no stray changes from the
  rename/restore of the fixture file (it's gitignored, confirmed absent from
  `git status` output throughout).
- Confirmed the expected counts (`PmiCounts(dimensions=47,
  geometric_tolerances=27, datums=59)`) and the OCP call sequence in
  `validation/ap242_pmi.py` were not modified in this round.

### Commit

SHA: `211633ca2d05db85934e0a22ca8d69c7b50887d3`

Message:
```
fix: scope NIST-fixture skipif to the one test that needs it

test_missing_file_raises has zero dependency on the NIST data, but the
module-level pytestmark skipif discarded its coverage on any machine
that hasn't fetched the fixture, under a reason string that wasn't true
of it. Move the skipif to a per-test decorator on
test_reads_semantic_pmi_from_nist_ftc06 only.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

Files changed: `tests/test_ap242_pmi.py`. 1 file changed, 2 insertions(+), 3
deletions(-).

### Concerns

None. The fix is minimal, scoped exactly to the finding, verified both in the
data-present state (2 passed) and the simulated-fresh-clone state (1 passed, 1
skipped), and the full suite shows no regressions. The previously open concern
(headline NIST counts unverified) is now resolved — they hold in this
environment.
