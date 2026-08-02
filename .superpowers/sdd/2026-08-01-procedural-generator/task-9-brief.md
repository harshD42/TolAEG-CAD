### Task 9: End-to-end generation and a round-trip guard

**Files:**
- Create: `tests/gen/test_end_to_end.py`

**Interfaces:**
- Consumes: everything above
- Produces: no new API — this is the integration gate

The point is to prove the loop closes: a seed produces geometry and a schema, the schema feeds the checker, and the STEP is re-readable by the same OCCT machinery the oracle uses.

- [ ] **Step 1: Write the failing test**

```python
# tests/gen/test_end_to_end.py
import pytest

pytest.importorskip("cadquery", reason="requires the [gen] extra")

from tolcad.checker import check
from tolcad.gen.export import export_assembly
from tolcad.gen.sampler import sample_assembly
from tolcad.gen.spec import AssemblySpec


def test_seed_to_verdict_round_trip(tmp_path):
    """seed -> spec -> STEP + JSON -> reload -> checker verdict."""
    spec = sample_assembly(21, 3)
    step_path, json_path = export_assembly(spec, tmp_path)

    reloaded = AssemblySpec.from_json(json_path.read_text(encoding="utf-8"))
    assert reloaded == spec

    verdicts = [check(m.to_check_dict()) for m in reloaded.mates]
    assert len(verdicts) == 3
    assert all(isinstance(v.assembles, bool) for v in verdicts)
    assert step_path.stat().st_size > 0


def test_exported_step_is_readable_by_the_oracle_machinery(tmp_path):
    """Our own STEP must load in the same reader used for the NIST oracle.

    It carries no semantic PMI (tolerances live in the sidecar), so the counts
    are expected to be zero — the point is that the file parses cleanly.
    """
    pytest.importorskip("OCP", reason="requires the [gen] extra")
    from validation.ap242_pmi import read_pmi_counts

    step_path, _ = export_assembly(sample_assembly(22, 2), tmp_path)
    counts = read_pmi_counts(step_path)
    assert counts.dimensions == 0
    assert counts.geometric_tolerances == 0
    assert counts.datums == 0


def test_a_batch_of_seeds_generates_without_error(tmp_path):
    """Small batch only. The research corpus is generated after Phase 3.5
    pre-registration, not here."""
    for seed in range(5):
        spec = sample_assembly(seed, 2)
        step_path, json_path = export_assembly(spec, tmp_path)
        assert step_path.is_file() and json_path.is_file()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/gen/test_end_to_end.py -v`
Expected: FAIL until Tasks 1–8 are complete; once they are, it should pass

- [ ] **Step 3: No implementation needed**

This task adds no production code. If a test fails, fix the module it exercises rather than weakening the assertion.

- [ ] **Step 4: Run the full suite**

Run: `pytest -q && python scripts/gate_a.py`
Expected: all pass; Gate A still exits 1

- [ ] **Step 5: Commit**

```bash
git add tests/gen/test_end_to_end.py
git commit -m "test: end-to-end seed-to-verdict round trip"
```

---

## Plan completion state

At the end of Task 9:

- A seed deterministically produces a toleranced two-part assembly
- The tolerance schema is the checker's own dict format, validated against it
- STEP geometry exports and re-reads cleanly
- Semantic PMI reads from real NIST AP242 files, pinned to verified counts
- The checker core is still numpy-only, enforced by lint

**Deliberately NOT done here:**
- Generating the research corpus — spec §12 puts pre-registration (Phase 3.5) first
- Writing semantic PMI *into* our own STEP files. `STEPCAFControl_Writer.SetDimTolMode` exists and the spike confirmed it, but nothing in the pipeline needs it: our tolerances live in the sidecar, and the NIST oracle only needs the read path. Add it only if the optional SolidWorks/TolAnalyst oracle turns out to require importable tolerances.
- Wiring the NIST oracle into `scripts/gate_a.py`. That needs the comparison corpus, which follows pre-registration.
- Emitting reference **CadQuery source text** alongside the geometry. Spec §5 lists "CadQuery program" among the generator's outputs, and this plan produces geometry + STEP + schema but not the program text. Deferred deliberately: the baselines *predict* CadQuery code and are scored against reference geometry, so nothing in Phase 4 consumes reference source. Revisit if an experiment ends up needing code-level comparison.

## Open question for the human

Task 3's clearance-hole table (close/normal/loose per fastener size) follows the common metric series. Unlike the Y14.5 formulas and ISO 286 tables, it is not currently traced to a specific standard edition. If these assemblies are meant to look conventional to a mechanical engineer, it is worth confirming the series against ISO 273 or the co-author's house standard. It affects realism, not correctness — every value is pinned by tests either way.
