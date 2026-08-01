import json
import pytest

pytest.importorskip("cadquery", reason="requires the [gen] extra")

from tolcad.gen.export import export_assembly
from tolcad.gen.sampler import sample_assembly
from tolcad.gen.spec import AssemblySpec


def test_writes_a_step_file_and_a_sidecar_json(tmp_path):
    spec = sample_assembly(3, 2)
    step_path, json_path = export_assembly(spec, tmp_path)
    assert step_path.is_file() and step_path.stat().st_size > 0
    assert json_path.is_file() and json_path.stat().st_size > 0


def test_step_file_has_a_step_header(tmp_path):
    step_path, _ = export_assembly(sample_assembly(3, 2), tmp_path)
    assert step_path.read_text(errors="ignore").startswith("ISO-10303-21;")


def test_sidecar_round_trips_back_to_the_original_spec(tmp_path):
    spec = sample_assembly(4, 3)
    _, json_path = export_assembly(spec, tmp_path)
    assert AssemblySpec.from_json(json_path.read_text(encoding="utf-8")) == spec


def test_filenames_encode_seed_and_difficulty(tmp_path):
    step_path, json_path = export_assembly(sample_assembly(11, 2), tmp_path)
    assert "seed11" in step_path.name and "d2" in step_path.name
    assert step_path.stem == json_path.stem


def test_export_does_not_emit_a_deprecation_warning(tmp_path):
    """CadQuery 2.8 deprecated Assembly.save; we must be on .export.

    Note: pytest.warns(None) was REMOVED in pytest 8 and raises TypeError on the
    pytest 9 installed here. Use warnings.catch_warnings instead.
    """
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        export_assembly(sample_assembly(6, 1), tmp_path)
    future = [w for w in caught if issubclass(w.category, FutureWarning)]
    assert not future, f"deprecated CadQuery API in use: {[str(w.message) for w in future]}"
