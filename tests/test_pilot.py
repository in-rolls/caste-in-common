import numpy as np
import pandas as pd

from caste_in_common.pilot import threshold_table


def test_bootstrap_preserves_constant_outcomes_and_missing_bounds():
    rows = []
    for group in ["ST", "SC", "OBC", "Others"]:
        for row in range(8):
            rows.append(
                {
                    "State": "10",
                    "FSU_Slno": str(row // 2),
                    "group": group,
                    "weight": 1.0,
                    "owned_land_acres": 0 if row % 2 == 0 else np.nan,
                    "consumption_pc_monthly": 1000.0,
                }
            )
    table, contrasts = threshold_table(
        pd.DataFrame(rows), np.random.default_rng(4), n_boot=20
    )
    t = table[table.outcome.eq("owned_land_acres") & table.threshold.eq(1)]
    np.testing.assert_allclose(t.percent, 100)
    np.testing.assert_allclose(t.missing_bound_low, 50)
    np.testing.assert_allclose(t.missing_bound_high, 100)
    np.testing.assert_allclose(t.ci_low, 100)
    np.testing.assert_allclose(contrasts.difference_pp, 0)
