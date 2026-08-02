# Task 6 report: Export STEP plus a sidecar tolerance schema

## Files touched
- Created `src/tolcad/gen/export.py` (verbatim from brief)
- Created `tests/gen/test_export.py` (verbatim from brief)

## Step 2: RED — failing test output (verbatim)

Command: `python -m pytest tests/gen/test_export.py -v`

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
__________________ ERROR collecting tests/gen/test_export.py __________________
ImportError while importing test module 'C:\Users\harsh\Downloads\Projects\Paper1\tests\gen\test_export.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\gen\test_export.py:6: in <module>
    from tolcad.gen.export import export_assembly
E   ModuleNotFoundError: No module named 'tolcad.gen.export'
=========================== short test summary info ===========================
ERROR tests/gen/test_export.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 1.26s ===============================
```

This matches the brief's expected failure exactly: `ModuleNotFoundError: No module named 'tolcad.gen.export'`. Proceeded to implementation.

## Step 4: GREEN — passing test output

Command: `python -m pytest tests/gen/test_export.py -v`

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0
collecting ... collected 5 items

tests/gen/test_export.py::test_writes_a_step_file_and_a_sidecar_json PASSED [ 20%]
tests/gen/test_export.py::test_step_file_has_a_step_header PASSED        [ 40%]
tests/gen/test_export.py::test_sidecar_round_trips_back_to_the_original_spec PASSED [ 60%]
tests/gen/test_export.py::test_filenames_encode_seed_and_difficulty PASSED [ 80%]
tests/gen/test_export.py::test_export_does_not_emit_a_deprecation_warning PASSED [100%]

============================== 5 passed in 1.36s ==============================
```

All 5 tests pass, including the FutureWarning check confirming `Assembly.export()` (not the deprecated `.save()`) is genuinely warning-free in this environment.

## Full suite result

Command: `python -m pytest -q -m "not slow"`

```
........................................................................ [ 49%]
........................................................................ [ 99%]
.                                                                        [100%]
145 passed, 2 deselected in 16.41s
```

No regressions. Also ran `tests/test_architecture.py` explicitly (10/10 passed), confirming the new `tolcad.gen.export` module does not violate the core/CAD import boundary — it lives in `tolcad.gen`, which is permitted to import CadQuery, and the checker core modules remain untouched.

## Commit

SHA: `a78d5c44f8fba402ef38eef7befbd260a8b95970`

Message:
```
feat: export STEP geometry with a sidecar tolerance schema

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

Diff stat: `src/tolcad/gen/export.py | 35 +++++` and `tests/gen/test_export.py | 47 +++++`, 82 insertions total, 2 files changed. Only the two files named in the brief were staged and committed.

## Self-review

- Implementation is verbatim from the brief: `_stem()` produces `assembly_seed{seed}_d{difficulty}`, `export_assembly()` writes `<stem>.step` via `build_assembly(spec).export(...)` and `<stem>.json` via `spec.to_json()`, returns `(step_path, json_path)`.
- Confirmed `AssemblySpec` has `seed` and `difficulty` as dataclass fields (src/tolcad/gen/spec.py lines 93-94), so `_stem` is well-formed against the real interface, not a guess.
- No extra features added: no CLI entry point, no batch mode, no PMI writing — matches the brief's explicit prohibition.
- `out_dir.mkdir(parents=True, exist_ok=True)` is the only side effect beyond the two file writes; acceptable and matches brief.
- Verified via `git status`/`git diff --stat` before committing that only the two intended files were staged (no accidental inclusion of `__pycache__` or other artifacts).
- Ran the architecture test suite specifically (not just the aggregate "not slow" run) to double check the CAD-free checker core boundary, since that is a project-wide invariant this task could plausibly have threatened. It held.

## Concerns

None. Tests are deterministic (seeded sampler), the RED failure matched the brief's exact prediction, GREEN passed on first attempt with no modifications needed to the brief's implementation, and the full suite plus architecture tests show no regressions.
