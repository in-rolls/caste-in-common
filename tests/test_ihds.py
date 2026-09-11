import numpy as np
import pandas as pd
import pytest

from caste_in_common.ihds import code, normalize_label, prepare
from caste_in_common.ihds_pilot import summarize, tail_composition


def raw_fixture():
    return pd.DataFrame(
        {
            "IDHH": ["1", "2", "3"],
            "STATEID": ["(10) Bihar 10"] * 3,
            "URBAN2011": ["(0) rural 0"] * 3,
            "IDPSU": [1, 2, 3],
            "ID13": ["(2) Forward", "(3) OBC", "(6) Others"],
            "ID11": ["(1) Hindu"] * 3,
            "ID12ANM": [" X ", "Y", "Z"],
            "ID12BNM": ["", "", ""],
            "WT": [1.0, 2.0, 3.0],
            "NPERSONS": [2, 4, 1],
            "INCOME": [-2400, 0, 60000],
            "INCOMEPC": [-1200, 0, 60000],
            "COPC": [1000.0, 1000.0, 1000.0],
        }
    )


def test_income_units_codes_and_nonpositive_retention():
    d = prepare(raw_fixture())
    assert d.income_monthly_pc.tolist() == [-100, 0, 5000]
    assert d.person_weight.tolist() == [2, 8, 3]
    assert d.group.tolist() == ["Forward/General", "OBC", "Others"]
    assert d.idhh.iloc[0] == "0000000001"
    assert d.state_name.tolist() == ["Bihar"] * 3


def test_normalization_does_not_merge_spelling_variants():
    assert normalize_label("  RAJ  PUT ") == "RAJ PUT"
    assert normalize_label("RAJPOOT") != normalize_label("RAJPUT")
    assert normalize_label(pd.NA) == ""
    with pytest.raises(ValueError):
        code(pd.Series(["Hindu"]))


def test_invalid_income_reconciliation_and_duplicates():
    raw = raw_fixture()
    raw.loc[0, "INCOMEPC"] = 500
    with pytest.raises(ValueError, match="reconcile"):
        prepare(raw)
    raw = raw_fixture()
    raw.loc[0, "IDHH"] = "2"
    with pytest.raises(ValueError, match="duplicate"):
        prepare(raw)


def test_threshold_excludes_equality_and_person_denominator():
    d = prepare(raw_fixture())
    thresholds, pairs = summarize(d)
    row = thresholds.query("scope == 'India' and group == 'Others' and cutoff == 5000")
    assert (row.pct == 0).all()
    row = pairs.query("scope == 'India' and a == 'Others' and b == 'OBC'")
    assert (row.a_auc == 1).all()


def test_tail_composition_bayes_identity():
    d = prepare(raw_fixture())
    t = tail_composition(d)
    t = t.query("cutoff == 2000 and side == 'at_or_above'")
    assert t.tail_composition_pct.sum() == pytest.approx(100)
    assert np.allclose(
        t.tail_composition_pct,
        t.population_share_pct * t.group_in_tail_pct / t.all_households_in_tail_pct,
    )


def test_person_weight_ess_uses_person_weights():
    from caste_in_common.ihds_pilot import support

    d = prepare(raw_fixture())
    assert support(d, "person_weight")["weight_ess"] == pytest.approx(13**2 / 77)
    assert support(d)["weight_ess"] == pytest.approx(6**2 / 14)
    d["group"] = "OBC"
    thresholds, _ = summarize(d)
    row = thresholds.query(
        "scope == 'India' and weighting == 'person_weight' and cutoff == 2000"
    ).iloc[0]
    assert row.weight_ess == pytest.approx(13**2 / 77)


def test_within_state_label_pair_direction_and_no_cross_state_pairs():
    from caste_in_common.ihds_pilot import label_pairs

    d = prepare(raw_fixture())
    table = pd.DataFrame(
        {
            "state": ["Bihar"] * 3,
            "reported_label": ["X", "Y", "Z"],
            "median": [-100, 0, 5000],
        }
    )
    pairs = label_pairs(d, table)
    assert len(pairs) == 9
    row = pairs.query("a == 'Z' and b == 'X'").iloc[0]
    assert row.a_auc == 1
    assert row.a_greater_pct == 100
