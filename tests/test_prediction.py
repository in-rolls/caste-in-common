import numpy as np
import pandas as pd
import pytest

from caste_in_common.prediction import assign_folds, fit_predict
from caste_in_common.stats import binned_overlap, binned_superiority_bounds, pairwise


def fixture():
    return pd.DataFrame(
        {
            "psu": np.repeat(np.arange(20).astype(str), 5),
            "state": [10] * 100,
            "urban": [0] * 100,
            "group": ["OBC"] * 100,
            "jati_label": ["X"] * 100,
            "weight": [1.0] * 100,
            "income_monthly_pc": np.tile([0, 500, 1500, 3000, 15000], 20),
        }
    )


def test_psu_folds_preserve_cluster_and_repeatability():
    d = fixture()
    f = assign_folds(d, 42)
    assert (d.assign(fold=f).groupby("psu").fold.nunique() == 1).all()
    assert np.array_equal(f, assign_folds(d, 42))
    assert set(f) == set(range(5))


def test_no_test_outcome_leakage_unseen_fallback_and_probabilities():
    train = fixture()
    test = train.iloc[:2].copy()
    test["jati_label"] = ["UNSEEN", "X"]
    p, coverage = fit_predict(train, test)
    test["income_monthly_pc"] = [-999999, 9999999]
    q, _ = fit_predict(train, test)
    for name in p:
        assert np.allclose(p[name], q[name])
        assert np.allclose(p[name].sum(axis=1), 1)
        assert (p[name] > 0).all()
    assert coverage["geography_broad_label"].tolist() == [False, True]
    assert np.allclose(p["geography_broad_label"][0], p["geography_broad"][0])


def test_label_support_uses_training_not_test_and_weight_scale_invariance():
    train = fixture()
    train.loc[:24, "jati_label"] = "SMALL"
    test = train.iloc[:1].copy()
    p, coverage = fit_predict(train, test)
    assert not coverage["geography_broad_label"][0]
    train.weight *= 1000
    q, _ = fit_predict(train, test)
    for name in p:
        assert np.allclose(p[name], q[name])


def test_auc_half_does_not_imply_overlap():
    less, ties, greater, auc = pairwise([0, 2], [1, 1], [1], [1])
    assert (less, ties, greater, auc) == (0.5, 0, 0.5, 0.5)
    assert binned_overlap([0, 2], [1, 1], [1], [1], [-np.inf, 0.5, 1.5, np.inf]) == 0


def test_bin_bounds_do_not_invent_ties():
    assert binned_superiority_bounds([1, 0], [1, 0]) == (0, 1)
    assert binned_superiority_bounds([0, 1], [1, 0]) == (1, 1)
    assert binned_superiority_bounds([0.5, 0.5], [0.5, 0.5]) == (0.25, 0.75)
    with pytest.raises(ValueError):
        binned_superiority_bounds([-1, 2], [1, 1])
