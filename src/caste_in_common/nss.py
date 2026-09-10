"""NSS 77 visit 1: reconstruct outcomes from the official block definitions."""

import hashlib

import numpy as np
import pandas as pd

GROUPS = {"1": "ST", "2": "SC", "3": "OBC", "9": "Others"}


def build_households(directory):
    blocks, manifest = {}, []
    for level in (1, 3, 4):
        paths = list(directory.glob(f"visit1_level_{level:02d}_*.csv.gz"))
        if len(paths) != 1:
            raise ValueError(f"Expected one visit 1 level {level} file: {paths}")
        path = paths[0]
        blocks[level] = pd.read_csv(path, dtype=str)
        manifest.append(
            {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        )
    return assemble(blocks[1], blocks[3], blocks[4]), manifest


def assemble(identification, demographics, land):
    for frame in (identification, demographics, land):
        if frame.HHID.isna().any():
            raise ValueError("Missing household key")
    if not identification.HHID.is_unique or not demographics.HHID.is_unique:
        raise ValueError("Household blocks must have unique HHID")
    if set(identification.HHID) != set(demographics.HHID):
        raise ValueError("Identification and demographic universes differ")
    if not set(land.HHID).issubset(set(identification.HHID)):
        raise ValueError("Land block contains households outside identification")
    if not identification.Sector.eq("1").all():
        raise ValueError("Expected rural households only")
    if not identification.Survey_Code.isin(["1", "2"]).all():
        raise ValueError("Unexpected survey response code")
    fields = ["HHID", "State", "NSS_Region", "Stratum", "SubStratumNo", "FSU_Slno"]
    hh = identification[fields + ["MLT"]].merge(
        demographics[["HHID", "b4q1", "b4q2", "b4q3", "b4q9"]],
        on="HHID",
        validate="one_to_one",
    )
    if hh[fields].isna().any().any():
        raise ValueError("Missing survey design identifiers")
    hh["group"] = hh.b4q3.map(GROUPS)
    if hh.group.isna().any():
        raise ValueError("Unmapped social group")
    hh["weight"] = pd.to_numeric(hh.MLT, errors="raise") / 100
    hh["household_size"] = pd.to_numeric(hh.b4q1, errors="raise")
    hh["consumption_monthly"] = pd.to_numeric(hh.b4q9, errors="raise")
    numeric = hh[["weight", "household_size", "consumption_monthly"]]
    if (
        not np.isfinite(numeric).all().all()
        or (hh.weight < 0).any()
        or (hh[["household_size", "consumption_monthly"]] <= 0).any().any()
    ):
        raise ValueError("Invalid weight, household size, or consumption")
    hh["consumption_pc_monthly"] = hh.consumption_monthly / hh.household_size
    land = land[["HHID", "b5q1", "b5q3"]].copy()
    land["code"] = pd.to_numeric(land.b5q1, errors="raise")
    land["acres"] = pd.to_numeric(land.b5q3, errors="raise")
    if not land.code.isin(range(1, 11)).all():
        raise ValueError("Unexpected land category")
    if not np.isfinite(land.acres).all() or (land.acres < 0).any():
        raise ValueError("Invalid reported land area")
    if land.duplicated(["HHID", "code"]).any():
        raise ValueError("Repeated household/land-category row")
    wide = land.pivot(index="HHID", columns="code", values="acres")
    wide = wide.reindex(columns=range(1, 11))
    if wide[10].isna().any():
        raise ValueError("Present land block lacks total row")
    components = wide.loc[:, 1:9].fillna(0)
    if not np.allclose(components.sum(axis=1), wide[10], rtol=0, atol=0.000001):
        raise ValueError("Land components do not reconcile to total")
    # Sparse category rows imply zero only inside a reconciled land block.
    owned = components[[1, 5, 6]].sum(axis=1).round(2).rename("owned_land_acres")
    hh = hh.merge(owned, on="HHID", how="left", validate="one_to_one")
    hh["land_observed"] = hh.owned_land_acres.notna()
    if len(hh) != len(identification):
        raise ValueError("Household count changed during joins")
    return hh
