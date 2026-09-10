import numpy as np
import pandas as pd
import pytest

from caste_in_common.nss import assemble


def blocks():
    identification = pd.DataFrame(
        {
            "HHID": ["001", "002"],
            "State": ["10"] * 2,
            "NSS_Region": ["101"] * 2,
            "Stratum": ["01"] * 2,
            "SubStratumNo": ["01"] * 2,
            "FSU_Slno": ["001", "002"],
            "MLT": ["100", "200"],
            "Sector": ["1"] * 2,
            "Survey_Code": ["1"] * 2,
        }
    )
    demographics = pd.DataFrame(
        {
            "HHID": ["001", "002"],
            "b4q1": ["4", "2"],
            "b4q2": ["1", "2"],
            "b4q3": ["2", "9"],
            "b4q9": ["8000", "2000"],
        }
    )
    land = pd.DataFrame(
        {
            "HHID": ["001"] * 6,
            "b5q1": ["01", "03", "04", "05", "06", "10"],
            "b5q3": ["1", "2", "3", "4", "0.1", "10.1"],
        }
    )
    return identification, demographics, land


def test_owned_excludes_leased_in_and_otherwise_possessed():
    hh = assemble(*blocks())
    assert hh.loc[0, "owned_land_acres"] == pytest.approx(5.1)
    assert hh.loc[0, "consumption_pc_monthly"] == 2000
    assert hh.loc[1, "consumption_pc_monthly"] == 1000
    assert hh.HHID.tolist() == ["001", "002"]
    assert np.isnan(hh.loc[1, "owned_land_acres"])
    assert hh.group.tolist() == ["SC", "Others"]


def test_bad_total_rejected():
    a, d, land = blocks()
    land.loc[land.b5q1.eq("10"), "b5q3"] = "11"
    with pytest.raises(ValueError, match="reconcile"):
        assemble(a, d, land)


def test_duplicate_category_rejected():
    a, d, land = blocks()
    with pytest.raises(ValueError, match="Repeated"):
        assemble(a, d, pd.concat([land, land.iloc[[0]]]))


def test_demographic_join_cannot_drop_households():
    a, d, land = blocks()
    with pytest.raises(ValueError, match="universes differ"):
        assemble(a, d.iloc[:1], land)


def test_unknown_group_rejected():
    a, d, land = blocks()
    d.loc[0, "b4q3"] = "8"
    with pytest.raises(ValueError, match="Unmapped"):
        assemble(a, d, land)


def test_owned_sum_respects_source_precision_at_threshold():
    a, d, land = blocks()
    land = pd.DataFrame(
        {
            "HHID": ["001"] * 4,
            "b5q1": ["01", "05", "06", "10"],
            "b5q3": ["0.3", "0.6", "0.1", "1.0"],
        }
    )
    hh = assemble(a, d, land)
    assert hh.loc[0, "owned_land_acres"] == 1.0
    assert not hh.loc[0, "owned_land_acres"] < 1.0


def test_zero_source_weight_preserved_for_explicit_exclusion():
    a, d, land = blocks()
    a.loc[0, "MLT"] = "0"
    hh = assemble(a, d, land)
    assert len(hh) == 2
    assert hh.loc[0, "weight"] == 0
