# NSS pilot data contract

`data/nss77_households.parquet` is local and git-ignored. One row is one rural
household in NSS 77 visit 1; key `HHID` is a string, preserving leading zeros.
The current source has 58,040 rows. Original converted blocks are read-only.

| Columns | Source / transformation | Type and units | Missingness / validation |
|---|---|---|---|
| HHID | B1; join to B4 and household aggregate of B5 | String household key | Required and unique |
| State, NSS_Region, Stratum, SubStratumNo, FSU_Slno | B1 | String survey identifiers | Required; PSU key is State × FSU_Slno |
| MLT | B1 | String raw multiplier | Parsed to nonnegative numeric weight |
| b4q1 | B4 | Raw household size string | Required, positive |
| b4q2 | B4 | Raw religion code string | Retained; not collapsed to caste |
| b4q3 | B4 | Raw social group string | 1 ST, 2 SC, 3 OBC, 9 Others; fail on unmapped codes |
| b4q9 | B4 | Raw total usual monthly consumption, rupees | Required, positive; not income |
| group | Map b4q3 above | String broad social group | No surname inference; no jati claim |
| weight | MLT / 100 | Nonnegative float household weight | DDI F28/F33 weight note; scaling irrelevant for normalized rates |
| household_size | Numeric b4q1 | Persons | Positive; person-weighting is not applied |
| consumption_monthly | Numeric b4q9 | Rupees per household per month | Source reports whole rupees; no inflation adjustment |
| consumption_pc_monthly | b4q9 / b4q1 | Rupees per person per month | Outcome, still household-weighted |
| owned_land_acres | B5 b5q3, categories 01 + 05 + 06 | Nonnegative float acres per household | 62 missing blocks remain NA; report zero at source precision |
| land_observed | owned_land_acres is nonmissing | Boolean | False for 62 absent land blocks |

The variable definitions are linked in [sources.md](sources.md). Source-specific
missing sentinels are not inferred from plausible values. Numeric parse errors,
nonfinite values and invalid ranges fail the build. No winsorization or
outlier deletion is performed. Diagnostics report counts, extrema, medians,
zero masses and weight concentration by group and outcome. Threshold outputs
report unweighted sample sizes, PSU counts and weighted missingness by group.

## Join contract

- B1 defines the left universe. B1 and B4 must have exactly the same HHID set and
  each must be unique by HHID. Cardinality is one-to-one and row count is conserved.
- B5 is unique by HHID × category. Every B5 HHID must exist in B1. Pivot before
  joining; join the household aggregate one-to-one onto B1 using a left join.
- All present land blocks require category 10. Within each such block, fill
  absent category rows with zero and require that categories 01–09 sum to 10
  within 0.000001 acre. This is justified by the sparse export and its exact
  reconciliation, not by an assumption that arbitrary missing values are zero.
- Absent entire B5 blocks do not become zero. Threshold missingness bounds assign
  all those households to either side of a cutoff. The population interpretation
  of complete-case land rates requires negligible or ignorable nonresponse;
  the bounds show how much this particular missingness can change each rate.
- There is no probabilistic linkage, deduplication by names, or expansion of rows.

## Recode ledger

1. Preserve all IDs as strings on input.
2. Check rural sector and surveyed/substitute status.
3. Map the four observed social-group codes without merging religion into caste.
4. Divide total monthly household consumption by household size.
5. Aggregate only owned land categories; include land leased out and homestead.
6. Retain absent land blocks as missing; use outcome-specific denominators.
7. Use the inverse weighted ECDF for quantiles and explicit strict/inclusive CDFs.
8. Write Parquet and verify an exact dataframe round trip before presentation.

No row-level data are committed. Aggregate outputs carry input-file hashes;
reproduction requires the original local inputs or their authorized equivalents.

Five Rajasthan households have zero released weight. They are preserved in the
local data file and excluded from weighted analyses and reported analytical
sample counts. The analytical India sample has 58,035 households.
