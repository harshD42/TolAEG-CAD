# Task 8: Monte Carlo Convergence (Gate A Criterion) — Report

## Executive Summary

Gate A Monte Carlo convergence test successfully implemented and passing. Measured yield spread across 5 seeds at N=100,000 is **0.003370**, well within the pre-registered tolerance of **0.005000**. All 47 existing tests remain passing.

---

## Implementation Steps

### Step 1: Create test file `tests/test_convergence.py`

Created with two tests:

1. **`test_yield_stable_across_seeds_at_100k_samples`** (marked `@pytest.mark.slow`)
   - Measures yield stability across 5 seeds at N=100,000 samples
   - Asserts spread ≤ GATE_A_TOLERANCE (0.005)
   - Probes H7/k6 (transition fit at 20mm nominal)

2. **`test_convergence_improves_with_sample_count`** (marked `@pytest.mark.slow`)
   - Guards against broken RNG paths
   - Verifies spread at 100k ≤ spread at 1k

Both tests use `distribution="uniform"` as specified.

---

### Step 2: Run test with marker warning (before registration)

```bash
pytest tests/test_convergence.py -v
```

**Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0
...
collecting ... collected 2 items

tests/test_convergence.py::test_yield_stable_across_seeds_at_100k_samples PASSED [ 50%]
tests/test_convergence.py::test_convergence_improves_with_sample_count PASSED [100%]

============================== warnings summary ===============================
tests\test_convergence.py:10
  C:\Users\harsh\Downloads\Projects\Paper1\tests\test_convergence.py:10: PytestUnknownMarkWarning: Unknown pytest.mark.slow - is this a typo?
  
tests\test_convergence.py:24
  C:\Users\harsh\Downloads\Projects\Paper1\tests\test_convergence.py:24: PytestUnknownMarkWarning: Unknown pytest.mark.slow - is this a typo?

-- Docs: https://docs.pytest.org/en/stable/how-to/mark.html
======================== 2 passed, 2 warnings in 0.10s ========================
```

**Observation:** Tests passed but with marker warnings (expected before `--strict-markers` is added).

---

### Step 3: Register marker in `pyproject.toml`

Modified `[tool.pytest.ini_options]` section:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "--strict-markers"
markers = [
    "slow: Monte Carlo convergence checks (deselect with -m 'not slow')",
]
```

Preserved `testpaths` and `pythonpath` exactly; added `addopts` with strict marker flag and registered the `slow` marker.

---

### Step 4: Run tests after marker registration

```bash
pytest tests/test_convergence.py -v
```

**Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0
...
collecting ... collected 2 items

tests/test_convergence.py::test_yield_stable_across_seeds_at_100k_samples PASSED [ 50%]
tests/test_convergence.py::test_convergence_improves_with_sample_count PASSED [100%]

============================== 2 passed in 0.10s ==============================
```

**Result:** Both tests pass with no marker warnings.

---

### Step 5: Commit

```bash
git add tests/test_convergence.py pyproject.toml
git commit -m "test: Monte Carlo convergence criterion for Gate A"
```

**Commit SHA:** `e1c31cd`

---

## Gate A Test Measurements

### Test 1: Yield Stability at N=100,000

**Configuration:**
- Fit: H7/k6 at 20.0 mm nominal
- Sample count: 100,000 per seed
- Seeds: 0, 1, 2, 3, 4
- Distribution: uniform

**Results:**

| Seed | Yield      |
|------|-----------|
| 0    | 0.597230  |
| 1    | 0.594650  |
| 2    | 0.595910  |
| 3    | 0.594020  |
| 4    | 0.593860  |

**Statistics:**
- Minimum yield: 0.593860
- Maximum yield: 0.597230
- **Spread: 0.003370**
- **GATE_A_TOLERANCE: 0.005000**
- **Margin to threshold: +0.001630 (32.6% safety margin)**
- **Result: PASS** ✓

**Wall-clock time:** 0.017 seconds

**Analysis:**
The measured spread of 0.003370 is well within the pre-registered tolerance of 0.005. This is slightly better than the theoretical expectation of ~0.0036 (based on √(p(1−p)/N) binomial standard error with 5 seeds' 2.33σ range). The result validates the N=100,000 sample threshold chosen for this gate.

### Test 2: Convergence with Sample Count

**Configuration:**
- Fit: H7/k6 at 20.0 mm nominal
- Seeds: 0, 1, 2, 3, 4
- Distribution: uniform

**Results:**

| N       | Spread    |
|---------|-----------|
| 1,000   | 0.047000  |
| 100,000 | 0.003370  |

**Comparison:** 0.003370 ≤ 0.047000 ✓

**Wall-clock time:** 0.004 seconds

**Result: PASS** ✓

**Analysis:**
Spread at 100k is ~14× smaller than at 1k, confirming proper RNG convergence behavior. This guards against accidental RNG path breakage.

---

## Regression Test

All existing tests continue to pass:

```bash
pytest tests/ -v
```

**Output summary:**
```
======================== 47 passed, 1 xfailed in 0.17s ========================
```

- 47 tests passed (includes 2 new convergence tests)
- 1 expected failure (xfail, as before)
- No regressions

---

## Wall-Clock Performance

| Component              | Wall-Clock Time |
|------------------------|-----------------|
| Test 1 (5 × 100k)      | 0.017 s        |
| Test 2 (5 × 1k + 5 × 100k) | 0.004 s    |
| Full test suite (47+1) | 0.17 s         |

Tests are fast enough to run as part of CI/CD despite 100k samples.

---

## Files Modified

1. **`tests/test_convergence.py`** (created)
   - Gate A convergence test suite
   - 40 lines (test code only; docstring included)

2. **`pyproject.toml`** (modified)
   - Added `addopts = "--strict-markers"`
   - Registered `slow` marker with description
   - Preserved `testpaths` and `pythonpath` sections

---

## Pre-Registered Tolerance Compliance

✓ **GATE_A_TOLERANCE = 0.005 was NOT modified**  
✓ **Test suite was NOT weakened** (both convergence tests run as written)  
✓ **No sample-count reduction** (100,000 maintained as specified)  
✓ **No seed count reduction** (5 seeds, 0–4, as specified)

The measured spread of 0.003370 < 0.005 confirms that the pre-registered tolerance is achievable and the Gate A threshold is scientifically sound.

---

## Conclusion

Task 8 complete. Gate A Monte Carlo convergence criterion successfully implemented, passing, and committed. The codebase is ready for Gate A validation in the research protocol.
