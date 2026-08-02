# Task 2 Report: MateSpec and AssemblySpec

## Summary
Successfully implemented Task 2 of Phase 3: created the spec dataclasses that form the contract between assembly generation and checking. Both `MateSpec` and `AssemblySpec` classes are frozen dataclasses with full validation and lossless JSON serialization.

## Implementation Details

### Files Created

#### `src/tolcad/gen/spec.py`
- **MateSpec (frozen dataclass)**
  - Fields: `kind`, `nominal_mm`, `hole_a`, `hole_b`, `fastener`, `designation`, `position_tol_a`, `position_tol_b`
  - Validation in `__post_init__`:
    - Rejects unknown `kind` values (must be one of: `virtual_condition`, `floating_fastener`, `fixed_fastener`, `iso_fit`)
    - Requires `designation` for `iso_fit` mates
    - Requires `fastener` for all Tier 1 mates
  - `to_check_dict()` method returns exactly the dict shape accepted by `tolcad.checker.check()`:
    - For `iso_fit`: returns `{"type": "iso_fit", "nominal": nominal_mm, "designation": designation}`
    - For `virtual_condition`: returns `{"type": "virtual_condition", "pin": fastener, "hole": hole_a}`
    - For Tier 1 (floating/fixed): returns `{"type": kind, "hole_a": hole_a, "hole_b": hole_b, "fastener": fastener}`

- **AssemblySpec (frozen dataclass)**
  - Fields: `seed`, `difficulty`, `mates` (list[MateSpec]), `plate_size_mm`, `plate_thickness_mm`
  - Default values: `plate_size_mm=40.0`, `plate_thickness_mm=8.0`, `mates=[]`
  - Validation in `__post_init__`: rejects empty mate lists (must have at least one mate)
  - `to_json() -> str`: returns JSON representation with sorted keys and 2-space indentation
  - `from_json(text: str) -> AssemblySpec`: classmethod for lossless deserialization

#### `tests/gen/test_spec.py`
Five comprehensive tests:
1. `test_mate_spec_emits_a_dict_the_checker_accepts` - Validates that floating_fastener MateSpec produces correct checker dict and yields expected margin
2. `test_iso_fit_mate_emits_a_checker_dict` - Validates iso_fit mate dict format and that checker accepts it
3. `test_assembly_spec_json_round_trip_is_lossless` - Ensures AssemblySpec serialization is lossless via JSON round-trip
4. `test_unknown_mate_kind_rejected` - Validates error handling for invalid kind
5. `test_assembly_spec_rejects_empty_mate_list` - Validates error handling for empty mate list

### Design Decisions

1. **No CAD Libraries**: `spec.py` imports only standard library (`json`, `dataclasses`) - no CadQuery or other CAD dependencies. This keeps the module fast to test and maintains the architectural separation.

2. **Direct Interface to Checker**: `MateSpec.to_check_dict()` returns exactly the dict format that `tolcad.checker.check()` already accepts. There is no translation layer - the two components meet at an existing, tested interface. This reduces the chance of bugs and makes the data flow transparent.

3. **Frozen Dataclasses**: Both classes are frozen (immutable) for safety and hashability. The specifications should be treated as immutable once created.

4. **Validation in `__post_init__`**: All validation happens in the constructor, failing fast and explicitly.

## Testing Results

### Step 1: Failing Test (Deliberately)
```
ModuleNotFoundError: No module named 'tolcad.gen.spec'
```
✓ Confirmed test fails as expected before implementation

### Step 2: Tests After Implementation
```
tests/gen/test_spec.py::test_mate_spec_emits_a_dict_the_checker_accepts PASSED
tests/gen/test_spec.py::test_iso_fit_mate_emits_a_checker_dict PASSED
tests/gen/test_spec.py::test_assembly_spec_json_round_trip_is_lossless PASSED
tests/gen/test_spec.py::test_unknown_mate_kind_rejected PASSED
tests/gen/test_spec.py::test_assembly_spec_rejects_empty_mate_list PASSED
```
✓ All 5 new tests pass

### Step 3: Full Test Suite
```
============================ 116 passed in 14.70s ================================
```
✓ All 116 tests pass (111 original + 5 new)
✓ No regressions

### Step 4: Gate A Script
```
Gate A: NOT CLEARED
Exit code: 1
```
✓ Gate A script continues to exit with code 1 as expected (status SKIP due to missing export files is normal)

## Commit Information
```
commit c4e99a1
Author: Claude Code <noreply@anthropic.com>
Date:   2026-08-01

    feat: AssemblySpec and MateSpec, checker-compatible by construction
    
    - Created src/tolcad/gen/spec.py with two frozen dataclasses
    - MateSpec validates kind and emits checker-compatible dict
    - AssemblySpec provides lossless JSON serialization
    - Added comprehensive tests in tests/gen/test_spec.py
```

## Key Implementation Characteristics for Tasks 3-6

### MateSpec Characteristics
- Immutable once created (frozen dataclass)
- Validates all inputs at construction time
- `to_check_dict()` is the conversion point to checker format
- All dimensional values are in millimetres as floats
- `position_tol_a` and `position_tol_b` are optional but stored (not defaulted to 0.0)

### AssemblySpec Characteristics
- Immutable once created (frozen dataclass)
- Contains one or more MateSpec objects (required, non-empty)
- `seed` and `difficulty` are integers (used for reproducible generation)
- `plate_size_mm` and `plate_thickness_mm` define the base geometry
- JSON serialization uses `asdict()` which recursively serializes nested MateSpec objects
- Deserialization manually reconstructs MateSpec objects from JSON

### Interface Consistency
- The bridge between generation (`AssemblySpec`) and checking (`to_check_dict()`) is established and tested
- No translation layer needed - the dicts returned by `to_check_dict()` are directly passable to `tolcad.checker.check()`
- This keeps Tasks 3-6 focused on geometry and generation logic, not format conversion

### Module Architecture
- `src/tolcad/gen/spec.py` is pure Python, CAD-free
- `src/tolcad/gen/__init__.py` documents that the entire `gen` package may import CadQuery
- The architecture lint in `tests/test_architecture.py` already enforces that core modules never import `gen` or CadQuery
- Tasks 3-5 (mating-feature library, sampler, CadQuery geometry) can freely import CadQuery
- Task 6 (STEP export) will import CadQuery for geometry manipulation

## Verification Checklist
- [x] MateSpec frozen dataclass created with all required fields
- [x] MateSpec.__post_init__ validates kind and required fields
- [x] MateSpec.to_check_dict() returns checker-compatible format for all kinds
- [x] AssemblySpec frozen dataclass created with required and optional fields
- [x] AssemblySpec.__post_init__ validates non-empty mate list
- [x] AssemblySpec.to_json() and from_json() provide lossless round-trip
- [x] All 5 tests pass
- [x] Full test suite (116 tests) passes with no regressions
- [x] Gate A script still exits with code 1
- [x] Code uses no CAD libraries
- [x] Commit created successfully

---

## Fix Report: Critical Issues Found in Review

### Finding 1: position_tol Fields Were Dead (Silent Divergence Footgun)

**Problem:** MateSpec declared `position_tol_a` and `position_tol_b` fields, but `to_check_dict()` never read them. Instead, `tolcad.checker._feature` pulled `position_tol` from INSIDE the hole/fastener dicts with a default of 0.0. The original tests passed only because the fixtures duplicated the value into both places. A generator that set `position_tol_a=0.3` but forgot to embed `"position_tol": 0.3` in `hole_a` would silently get wrong margins with no error.

**Root Cause:** The dedicated fields existed but were not wired into the conversion function.

**Fix:**
- Modified `to_check_dict()` to inject `position_tol` from `position_tol_a` and `position_tol_b` INTO the hole and fastener dicts before returning them to the checker
- Added helper function `inject_position_tol()` that creates a new dict with the position_tol injected, overriding any conflicting value already in the input dict
- The dedicated fields are now the SINGLE SOURCE OF TRUTH; divergence is structurally impossible

**Tests Added:**
- `test_position_tol_a_injected_when_hole_a_has_no_position_tol` — verifies that position_tol is injected even when the input dict lacks the key
- `test_position_tol_a_overrides_conflicting_value_in_hole_a` — verifies that position_tol_a overrides conflicting position_tol in the input dict

### Finding 2: __post_init__ Allowed Malformed Specs (Opaque Failures)

**Problem:** `__post_init__` validated `kind` and that `fastener` was non-None for non-iso_fit kinds, but it allowed:
- A `floating_fastener` with `hole_b=None`
- A `fixed_fastener` with `hole_a=None` or `hole_b=None`
- A `virtual_condition` with `hole_a=None`

These would construct cleanly and then fail in the checker with opaque `TypeError: 'NoneType' object is not subscriptable`, not a clear `ValueError` from the spec module.

**Root Cause:** Validation was incomplete; hole field validation was missing.

**Fix:**
- Expanded `__post_init__` to validate required hole fields per kind:
  - `virtual_condition` requires `hole_a` and `fastener`
  - `floating_fastener` and `fixed_fastener` require `hole_a`, `hole_b`, and `fastener`
- All violations raise clear `ValueError` with the specific missing field named

**Tests Added:**
- `test_virtual_condition_rejects_missing_hole_a` — validates error when hole_a is None
- `test_floating_fastener_rejects_missing_hole_b` — validates error when hole_b is None
- `test_fixed_fastener_rejects_missing_hole_a` — validates error when hole_a is None

### Additional Coverage

The review also noted that no tests existed for `virtual_condition` or `fixed_fastener` mates through the checker. Added:
- `test_virtual_condition_mate_round_trip` — constructs a virtual_condition MateSpec, converts to checker dict, and verifies the expected margin (-0.1)
- `test_fixed_fastener_mate_round_trip` — constructs a fixed_fastener MateSpec with H_a=9.0, H_b=7.9, F=8.0, T=0, verifies margin = 1.0 per the formula (H_a - F) - (T_a + T_b)

### Testing After Fixes

```
pytest tests/gen/test_spec.py -v

collected 12 items

tests/gen/test_spec.py::test_mate_spec_emits_a_dict_the_checker_accepts PASSED
tests/gen/test_spec.py::test_iso_fit_mate_emits_a_checker_dict PASSED
tests/gen/test_spec.py::test_assembly_spec_json_round_trip_is_lossless PASSED
tests/gen/test_spec.py::test_unknown_mate_kind_rejected PASSED
tests/gen/test_spec.py::test_assembly_spec_rejects_empty_mate_list PASSED
tests/gen/test_spec.py::test_position_tol_a_injected_when_hole_a_has_no_position_tol PASSED
tests/gen/test_spec.py::test_position_tol_a_overrides_conflicting_value_in_hole_a PASSED
tests/gen/test_spec.py::test_virtual_condition_mate_round_trip PASSED
tests/gen/test_spec.py::test_fixed_fastener_mate_round_trip PASSED
tests/gen/test_spec.py::test_virtual_condition_rejects_missing_hole_a PASSED
tests/gen/test_spec.py::test_floating_fastener_rejects_missing_hole_b PASSED
tests/gen/test_spec.py::test_fixed_fastener_rejects_missing_hole_a PASSED

======================== 12 passed in 0.09s ========================
```
✓ All 12 tests pass (5 original + 7 new/fixed)

### Full Test Suite After Fixes

```
pytest -v

======================== 123 passed in 14.18s ========================
```
✓ All 123 tests pass (111 original + 12 new)
✓ No regressions

### Gate A After Fixes

```
Gate A: NOT CLEARED
Exit code: 1
```
✓ Gate A script continues to exit with code 1 as expected

### Commit Information for Fix

```
commit 4ce9dd6
Author: Claude Code <noreply@anthropic.com>
Date:   2026-08-01

    fix: position_tol is single source of truth; validate required fields per kind
    
    - position_tol_a/b now injected INTO hole/fastener dicts in to_check_dict()
    - Dedicated fields are the SINGLE SOURCE OF TRUTH; divergence is impossible
    - __post_init__ now validates all required hole fields per kind
    - Added 7 tests covering injection, override, and validation
    - Verified virtual_condition and fixed_fastener round-trip through checker
```

### Summary of Changes

**src/tolcad/gen/spec.py:**
- Enhanced `__post_init__` to validate all required hole fields per kind
- Refactored `to_check_dict()` with `inject_position_tol()` helper that overwrites position_tol from dedicated fields
- Position_tol_a and position_tol_b are now the single source of truth

**tests/gen/test_spec.py:**
- 5 original tests unchanged
- 7 new tests covering position_tol injection, override, validation, and round-trip checking

### Implications for Tasks 3-6

The fixes strengthen the contract between generation and checking:
1. Generators cannot accidentally create specs with missing hole fields — they will fail at construction with clear errors
2. Generators cannot accidentally diverge position_tol values between the dedicated fields and the dict fields — the dedicated fields are the source, and they are ALWAYS injected into the dicts
3. All four mate kinds (virtual_condition, floating_fastener, fixed_fastener, iso_fit) are now fully tested end-to-end through the checker
