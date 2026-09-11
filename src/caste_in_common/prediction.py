"""Held-out-PSU prediction of income bins using smoothed group frequencies."""

import numpy as np
import pandas as pd

CUTS = np.array([0, 1000, 2000, 5000, 10000], dtype=float)
MODELS = ["pooled", "broad", "geography", "geography_broad", "geography_broad_label"]
LEVELS = {
    "broad": (["group"], "pooled"),
    "geography": (["state", "urban"], "pooled"),
    "geography_broad": (["state", "urban", "group"], "geography"),
    "geography_broad_label": (
        ["state", "urban", "group", "jati_label"],
        "geography_broad",
    ),
}


def assign_folds(d, seed, n_folds=5):
    """All members of a complete PSU stay together, including missing labels."""
    units = d[["psu", "state", "urban"]].drop_duplicates()
    if not units.psu.is_unique:
        raise ValueError("PSU crosses state/urban strata")
    rng = np.random.default_rng(seed)
    mapping = {}
    for _, g in units.groupby(["state", "urban"], sort=True):
        ids = sorted(g.psu)
        rng.shuffle(ids)
        mapping.update({u: i % n_folds for i, u in enumerate(ids)})
    return d.psu.map(mapping).to_numpy(int)


def fit_predict(train, test, prior=30, min_hh=30, min_psu=5):
    """Parent probabilities plus Kish-weight-ESS shrinkage; training data only."""
    if prior <= 0:
        raise ValueError("Prior strength must be positive")
    bins = np.searchsorted(CUTS, train.income_monthly_pc, side="right")
    weights = train.weight.to_numpy(float)
    pooled = np.bincount(bins, weights=weights, minlength=len(CUTS) + 1)
    pooled = (pooled / pooled.sum() + 1e-8) / (1 + (len(CUTS) + 1) * 1e-8)
    fitted = {}
    predictions = {"pooled": np.tile(pooled, (len(test), 1))}
    coverage = {"pooled": np.ones(len(test), dtype=bool)}
    work = train.reset_index(drop=True).copy()
    work["bin"] = bins
    for name, (columns, parent) in LEVELS.items():
        table = {}
        for key, group in work.groupby(columns, sort=False, dropna=False):
            key = key if isinstance(key, tuple) else (key,)
            if name.endswith("label") and key[-1] == "":
                continue
            if len(group) < min_hh or group.psu.nunique() < min_psu:
                continue
            if parent == "pooled":
                base = pooled
            else:
                parent_key = key[: len(LEVELS[parent][0])]
                base = fitted[parent].get(parent_key)
                if base is None:
                    if parent == "geography_broad":
                        base = fitted["geography"].get(key[:2], pooled)
                    else:
                        base = pooled
            w = group.weight.to_numpy(float)
            effective_n = w.sum() ** 2 / (w @ w)
            empirical = np.bincount(group.bin, weights=w, minlength=len(pooled))
            empirical /= w.sum()
            table[key] = (effective_n * empirical + prior * base) / (
                effective_n + prior
            )
        fitted[name] = table
        pred = predictions[parent].copy()
        covered = np.zeros(len(test), dtype=bool)
        for i, key in enumerate(test[columns].itertuples(index=False, name=None)):
            if key in table:
                pred[i] = table[key]
                covered[i] = True
        predictions[name] = pred
        coverage[name] = covered
    return predictions, coverage


def evaluate(d, seeds=(19, 47, 83), priors=(10, 30, 100)):
    """Repeated split sensitivity; output is not a sampling confidence interval."""
    rows = []
    actual = np.searchsorted(CUTS, d.income_monthly_pc, side="right")
    for seed in seeds:
        folds = assign_folds(d, seed)
        for prior in priors:
            loss = {name: np.zeros(len(d)) for name in MODELS}
            used = {name: np.zeros(len(d)) for name in MODELS}
            for fold in np.unique(folds):
                held = np.flatnonzero(folds == fold)
                predictions, coverage = fit_predict(
                    d.loc[folds != fold], d.iloc[held], prior=prior
                )
                for name in MODELS:
                    p = predictions[name]
                    loss[name][held] = -np.log(p[np.arange(len(held)), actual[held]])
                    used[name][held] = coverage[name]
            for name in MODELS:
                rows.append(
                    {
                        "seed": seed,
                        "prior_effective_households": prior,
                        "model": name,
                        "log_loss_nats": np.average(loss[name], weights=d.weight),
                        "own_level_coverage_pct": 100
                        * np.average(used[name], weights=d.weight),
                    }
                )
    return pd.DataFrame(rows)
