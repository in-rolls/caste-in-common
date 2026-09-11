# Extending the existing IHDS work

Audit date: 2026-09-10. Source: the existing ICPSR 36151 DS0002 R release under
`../land/data/ihds2/ICPSR_36151/`. Raw data remain local and ignored by Git.

## What `../land` already did

`../land/scripts/97_ihds_ingest.ipynb` ingests the household and individual
files for land acquisition and titling; `98_ihds_titling.ipynb` analyzes those
outcomes. It uses pyreadr, parses ICPSR factor codes rather than interpreting
factor positions, preserves zero-padded household identifiers, and uses `WT`.
Religion is `ID11`; `ID14` is the main income source. The full PSU identifier is
`IDPSU`, not the within-district serial `PSUID`. These conventions are retained.

The previous extract retains `COPC`, household size, social groups, and geography,
but not `INCOME`, `INCOMEPC`, `ID12ANM`, or `ID12BNM`. It therefore cannot answer
the new income and detailed-label questions by itself. No previous land files
were changed.

The new extract was joined one-to-one to
`ihds2_allindia_household.csv.gz` on all 42,152 household identifiers. All common
weights, sizes, caste/religion codes, states, rural/urban codes, consumption
values, and complete PSU identifiers reconciled. The source SHA-256 and sample
counts are in `output/ihds_provenance.json`.

## Added variables and definitions

| Variable | Treatment |
|---|---|
| `INCOME` | Released annual household net income; retain negative and zero values |
| `INCOMEPC` | Check against `INCOME / NPERSONS`, allowing source rounding |
| `income_monthly_pc` | `INCOME / NPERSONS / 12`; an annual average, not a monthly observation |
| `ID12ANM` | Reported jati-name response; strip whitespace, uppercase, collapse repeated spaces |
| `ID12BNM` | Reported sub-jati response; same normalization, retained locally for future harmonization |
| `ID13` | 1 Brahmin; 2 Forward/General except Brahmin; 3 OBC; 4 SC; 5 ST; 6 Others |
| `WT` | Household weights; person-weight sensitivity uses `WT * NPERSONS` |
| `COPC` | Released monthly per-capita consumption; retained to reconcile with prior work |

The source contains 452 negative and 166 zero total-income observations. They are
not converted to missing, truncated to zero, or logged. The IHDS-II user guide,
printed pp. 22–23, describes net farm/business income and annual wage totals,
including in-kind compensation. Asset sales are excluded from its income
construction. This is household income, not an individual's earnings.
[IHDS-II user guide](https://s3.amazonaws.com/drupal-base-s3-drupalshareds3-1qwpjwcnqwwsr/ihds/s3fs-public/ihds2usersguide01.pdf).

## Detailed-label limitations

There are 8,312 normalized responses including blank, and 576 blanks. Some
responses are religious or broad social categories. Many look like spelling
variants, but typography normalization is not identity harmonization. Broad
category, religion, jati, and sub-jati fields must be reviewed together to build
an explicit, state-specific crosswalk. No identities are inferred from names.

Descriptive cells require 100 households, 20 PSUs, and Kish weight ESS of 50.
These are reporting thresholds, not a guarantee of precise ranks. Prediction
eligibility is independently determined inside each training fold. Neither
infrequent labels nor missing labels are dropped from prediction evaluation.

A credible next harmonization step is a versioned crosswalk with original label,
state, religion/broad-group context, proposed identity, evidence, ambiguity, and
review status. Preserve unresolved labels. Compare conservative merges with
unmerged results; report both population coverage and sensitivity. A weak result
from the unmerged spelling field cannot show that actual jati has little signal.

## Independent design review incorporated

An independent model reviewed the design and identified these material points:
IHDS Others differs from NSS Others; conditional information differs from total
information; raw spelling fragmentation can attenuate results; complete PSUs
must be held out before filtering; repeated split variation is not sampling
uncertainty; Kish ESS ignores clustering; prior strength needs sensitivity;
nominal cutoffs and annual averages do not establish current poverty or monthly
volatility. The implementation and interpretation reflect these findings.

Independent code review found that person-weighted threshold rows initially
reported the household-weight Kish ESS. This diagnostic was corrected to use the
selected weights and regression-tested. Point estimates were unaffected. No
consequential defect was found in fold assignment, training eligibility, AUC
direction, hierarchical fallback, or tail denominators.
