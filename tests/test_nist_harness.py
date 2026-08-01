import pytest
from validation.nist_pmi import agreement, disagreements, load_expected


def test_loads_expected_verdicts(tmp_path):
    csv = tmp_path / "nist.csv"
    csv.write_text("part_id,assembles\nFTC-06,true\nFTC-07,false\n", encoding="utf-8")
    got = load_expected(csv)
    assert got == {"FTC-06": True, "FTC-07": False}


def test_agreement_is_fraction_of_matching_verdicts():
    ours = {"FTC-06": True, "FTC-07": True}
    expected = {"FTC-06": True, "FTC-07": False}
    assert agreement(ours, expected) == pytest.approx(0.5)


def test_disagreements_are_listed_for_root_causing():
    ours = {"FTC-06": True, "FTC-07": True}
    expected = {"FTC-06": True, "FTC-07": False}
    assert disagreements(ours, expected) == ["FTC-07"]


def test_no_overlap_is_an_error_not_a_silent_pass():
    with pytest.raises(ValueError, match="no overlapping"):
        agreement({"A": True}, {"B": True})
