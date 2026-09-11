"""IHDS-II income extension of land/scripts/97_ihds_ingest.ipynb."""

import re

import numpy as np
import pandas as pd

GROUPS = {
    1: "Brahmin",
    2: "Forward/General",
    3: "OBC",
    4: "SC",
    5: "ST",
    6: "Others",
}


def code(series):
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series)
    text = series.astype("string").str.strip()
    parsed = text.str.extract(r"^\((\d+)\)", expand=False)
    invalid = text.notna() & parsed.isna()
    if invalid.any():
        raise ValueError("Unrecognized ICPSR labelled category")
    return pd.to_numeric(parsed)


def normalize_label(value):
    """Only typography: no inferred caste, synonym merges, or spelling guesses."""
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip().upper())


def prepare(raw):
    d = pd.DataFrame(index=raw.index)
    d["idhh"] = raw.IDHH.astype("string").str.zfill(10)
    if d.idhh.isna().any() or not d.idhh.is_unique:
        raise ValueError("Missing or duplicate household identifiers")
    for dest, source in [
        ("state", "STATEID"),
        ("urban", "URBAN2011"),
        ("caste_code", "ID13"),
        ("religion_code", "ID11"),
    ]:
        d[dest] = code(raw[source])
    d["psu"] = raw.IDPSU.astype("string")
    d["state_name"] = raw.STATEID.astype("string").str.replace(
        r"^\(\d+\)\s*|\s+\d+$", "", regex=True
    )
    d["group"] = d.caste_code.map(GROUPS).fillna("Not reported")
    if not d.caste_code.dropna().isin(GROUPS).all():
        raise ValueError("Unexpected broad caste code")
    d["jati_label"] = raw.ID12ANM.map(normalize_label)
    d["subjati_label"] = raw.ID12BNM.map(normalize_label)
    for dest, source in [
        ("weight", "WT"),
        ("hh_size", "NPERSONS"),
        ("income_annual_hh", "INCOME"),
        ("consumption_monthly_pc", "COPC"),
    ]:
        d[dest] = pd.to_numeric(raw[source], errors="raise")
    required = ["weight", "hh_size", "income_annual_hh", "state", "urban"]
    if not np.isfinite(d[required].to_numpy(float)).all():
        raise ValueError("Missing or nonfinite income, weights, or design variables")
    if (d.weight <= 0).any() or (d.hh_size <= 0).any() or d.psu.isna().any():
        raise ValueError("Invalid sampling weights, household size, or PSU")
    if not d.urban.isin([0, 1]).all():
        raise ValueError("Unexpected urban code")
    if (d.groupby("psu").state.nunique() > 1).any():
        raise ValueError("PSU identifiers reused across states")
    annual_pc = d.income_annual_hh / d.hh_size
    if not np.allclose(annual_pc, raw.INCOMEPC, rtol=1e-6, atol=0.1):
        raise ValueError("Per-capita income does not reconcile with released INCOMEPC")
    d["income_monthly_pc"] = annual_pc / 12
    d["person_weight"] = d.weight * d.hh_size
    return d.reset_index(drop=True)


def read_households(path):
    import pyreadr

    objects = pyreadr.read_r(str(path))
    if len(objects) != 1:
        raise ValueError("Expected one household data frame")
    return prepare(next(iter(objects.values())))
