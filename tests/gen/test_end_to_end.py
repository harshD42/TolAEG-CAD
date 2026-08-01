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
