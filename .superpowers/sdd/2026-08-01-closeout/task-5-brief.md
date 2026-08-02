### Task 5: Close the three guard gaps review found

**Files:**
- Modify: `tests/mutation_registry.py`
- Modify: `tests/test_declared_mutations.py`
- Test: same

**Interfaces:**
- Consumes: `DeclaredMutation`, `REGISTRY`
- Produces: registry entries `tapped-hole-upper-dev-nonzero` and `case-sensitive-guard-uppercased`; selector and suffix meta-guards

Three gaps: `_TAPPED_HOLE_UPPER_DEV_MM` is unguarded while its twin has both a test and a registry entry (the pre-registration names them as equals); historical **instance 10** — the case-sensitive text guard — has no registry entry despite the design spec listing it among Layer 3's seven; and nothing enforces function-level test selectors.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_declared_mutations.py`:

```python
def test_every_registry_entry_names_a_single_test():
    """A whole-file selector can pass because some unrelated test failed."""
    for m in REGISTRY:
        assert "::" in m.test, (
            f"{m.name} targets '{m.test}', a whole file. Name the specific test, "
            f"or the entry can be satisfied by an unrelated failure."
        )


def test_text_targets_have_a_known_safe_suffix():
    """A line-ending-sensitive target declared as text fails for the wrong reason.

    _count_and_apply normalises CRLF->LF across the whole file for text targets.
    That is harmless for Python and Markdown; it is not harmless in general.
    """
    safe = {".py", ".md", ".toml", ".yml", ".yaml", ".cfg"}
    for m in REGISTRY:
        if m.binary:
            continue
        suffix = pathlib.Path(m.target).suffix
        assert suffix in safe, (
            f"{m.name} targets {m.target} as TEXT, but {suffix} is not in the "
            f"known-safe set {sorted(safe)}. Declare it binary=True."
        )
```

Add `"tapped-hole-upper-dev-nonzero"` and `"case-sensitive-guard-uppercased"` to `_CRITICAL_GUARDS`, and add `import pathlib` to the test module.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_declared_mutations.py -v`
Expected: FAIL — the two new `_CRITICAL_GUARDS` names are missing from `REGISTRY`.

- [ ] **Step 3: Add the two entries**

```python
    DeclaredMutation(
        name="tapped-hole-upper-dev-nonzero",
        target="src/tolcad/gen/features.py",
        find="_TAPPED_HOLE_UPPER_DEV_MM = 0.2",
        replace="_TAPPED_HOLE_UPPER_DEV_MM = 0.9",
        test="tests/gen/test_features.py::test_tapped_hole_is_always_smaller_than_its_fastener",
        expect="fail",
        why=(
            "The pre-registration names this and _FASTENER_LOWER_DEV_MM as the two "
            "declared-inert untraced numbers. Its twin has an executed guard and "
            "this did not, so we would be publishing two claims of which only one "
            "was watched failing. 0.9 pushes the M3 tapped hole (2.5 + 0.9 = 3.4) "
            "past the M3 fastener at 3.0."
        ),
    ),
    DeclaredMutation(
        name="case-sensitive-guard-uppercased",
        target="src/tolcad/gen/features.py",
        find="were checked against the primary standard",
        replace="were NOT been checked against the primary standard",
        test="tests/gen/test_features.py::test_features_module_cites_its_primary_sources",
        expect="fail",
        why=(
            "Historical instance 10. The original guard was case-sensitive and a "
            "stale caveat written 'NOT' slipped past it. The guard now lowercases "
            "before matching; this entry is what proves that, and the design spec "
            "listed instance 10 among Layer 3's seven while no entry existed."
        ),
    ),
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_declared_mutations.py -v`, then the full suite.
Expected: PASS, 13 registry entries. If either new entry reports the target test still passed, STOP and report it — that is a live instance, not a plan bug.

- [ ] **Step 5: Commit**

```bash
git add tests/mutation_registry.py tests/test_declared_mutations.py
git commit -m "feat: guard the tapped-hole constant, instance 10, and selector granularity"
```

---

