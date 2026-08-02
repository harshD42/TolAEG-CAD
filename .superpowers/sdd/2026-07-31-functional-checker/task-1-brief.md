### Task 1: Repository scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/tolcad/__init__.py`
- Create: `tests/test_smoke.py`
- Create: `CLAUDE.md`
- Create: `.gitignore`

**Interfaces:**
- Consumes: nothing
- Produces: importable package `tolcad`; `pytest` runnable from repo root

- [ ] **Step 1: Write the failing test**

```python
# tests/test_smoke.py
def test_package_imports():
    import tolcad
    assert tolcad.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tolcad'`

- [ ] **Step 3: Create the package files**

```toml
# pyproject.toml
[project]
name = "tolcad"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["numpy>=1.26"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov>=5.0"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

```python
# src/tolcad/__init__.py
"""Open GD&T-aware functional checker for toleranced CAD assemblies."""

__version__ = "0.1.0"
```

```
# .gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
*.egg-info/
build/
dist/
.venv/
results/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pip install -e ".[dev]" && pytest tests/test_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Write CLAUDE.md**

```markdown
# tolcad

Open, GD&T-aware functional checker for toleranced CAD assemblies.
Supports the paper: *Nominally Correct, Functionally Wrong*.
Design spec: `docs/superpowers/specs/2026-07-31-tolerance-aware-cad-eval-design.md`

## Conventions

- **All dimensions are millimetres (float).** ISO 286 tables publish micrometres;
  convert at the table boundary and nowhere else.
- **Tier 1 is exact.** Closed-form ASME Y14.5. Compare with `EPS = 1e-9`, no looser.
- **Tier 2 is statistical.** Monte Carlo. Always report a seed.
- **`validation/` is optional and one-directional.** It may import core; core may never
  import it. Enforced by `tests/test_architecture.py`.
- **No SolidWorks required for any headline result.** TolAnalyst is a black-box oracle.

## Commands

    pytest                      # all tests
    pytest -m "not slow"        # skip Monte Carlo convergence
    python scripts/gate_a.py    # Gate A report

## Do not edit

Pre-registered Gate A/B/C/D thresholds in the design spec §7 are frozen.
Changing one after seeing data invalidates the result.
```

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src tests CLAUDE.md .gitignore
git commit -m "feat: repository scaffold and project conventions"
```

---

