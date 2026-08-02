### Task 1: Optional `gen` extra and a lint that keeps the core light

**Files:**
- Modify: `pyproject.toml`
- Create: `src/tolcad/gen/__init__.py`
- Modify: `tests/test_architecture.py`

**Interfaces:**
- Consumes: nothing
- Produces: installable `tolcad[gen]` extra; importable `tolcad.gen`

The checker currently depends only on numpy, and that is worth protecting — it is why Gate A can run anywhere. CadQuery is heavy, so it goes behind an extra, and the lint gains a rule so nobody quietly imports it into the checker.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_architecture.py  (append)

CORE_LIGHT_MODULES = (
    "types", "y14_5", "iso286", "montecarlo", "checker", "reliability",
)
HEAVY_PACKAGES = {"cadquery", "OCP"}


def test_checker_core_does_not_import_cad_libraries():
    """The checker must stay installable and runnable without CadQuery.

    Gate A's "runs with no commercial licence" guarantee depends on the core
    being light. tolcad.gen may import CadQuery; the six modules below may not,
    and may not import tolcad.gen either.
    """
    offenders = []
    for stem in CORE_LIGHT_MODULES:
        path = CORE / f"{stem}.py"
        assert path.is_file(), f"expected core module missing: {path}"
        imported = _imported_modules(path)
        bad = {m for m in imported if m.split(".")[0] in HEAVY_PACKAGES}
        bad |= {m for m in imported if m.startswith("tolcad.gen")}
        if bad:
            offenders.append(f"{stem}.py imports {sorted(bad)}")
    assert not offenders, (
        "checker core must not depend on CAD libraries: " + "; ".join(offenders)
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_architecture.py::test_checker_core_does_not_import_cad_libraries -v`
Expected: FAIL — `_imported_modules` is defined in the file but `CORE_LIGHT_MODULES` is not yet, so this is a NameError until you append the constants. If it passes immediately, you have not appended the constants; check.

- [ ] **Step 3: Add the extra and the package**

In `pyproject.toml`, add to `[project.optional-dependencies]` alongside the existing `dev`:

```toml
gen = ["cadquery>=2.8"]
```

Create `src/tolcad/gen/__init__.py`:

```python
"""Procedural toleranced-assembly generation.

Imports CadQuery, which the checker core deliberately does not. Install with
`pip install -e ".[gen]"`. tests/test_architecture.py enforces that the six
core checker modules never import this package or CadQuery.
"""
```

- [ ] **Step 4: Run tests**

Run: `pip install -e ".[dev,gen]" && pytest -q`
Expected: all pass, including the new test.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/tolcad/gen/__init__.py tests/test_architecture.py
git commit -m "feat: optional gen extra, lint keeping checker core CAD-free"
```

---

