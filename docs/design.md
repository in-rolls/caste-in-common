# Caste in Common: research design

How much do economic distributions overlap across caste groups, and how large
are their gaps? Both are empirical questions. Neither answer is fixed in advance.

This is a descriptive study. The first estimand is the survey-weighted share of
rural households in each reported NSS social group with outcome Y below a common
threshold t, in NSS 77 visit 1. Land refers to July–December 2018; usual monthly
consumption is reported at the survey. Each outcome retains its own universe,
time reference and units. These are households, not individual earners.

## What the reader should see

1. **Common-threshold tables:** out of 100 households in each group, how many
   own less than 1 acre, or consume less than Rs 2,000 per person per month?
   Show several thresholds and the complete ECDF, so the answer does not depend
   on a single selected cutoff. Include both strict and inclusive inequalities.
2. **Pooled-rank tables:** what share of each group lies below the pooled 25th,
   50th and 75th percentiles? These compare everyone to the same reference
   distribution. Within-group quartiles would contain the same fractions by
   construction and would not answer this question. Report ties at thresholds.
3. **Pairwise comparisons:** independently draw one household from each of two
   groups. Report the probability the first has less, the same, or more of the
   resource. Also provide P(A<B)+0.5P(A=B), with the tie convention explicit.
   A score of 0.5 does not prove the two distributions are identical.
4. **Overlap in common bins:** sum the smaller of the two groups' probability
   masses in each bin. This is a resolution-dependent descriptive statistic,
   not a percentage of economically identical people. Report the edges. Coarser
   bins can inflate it; do not use it as the headline or compare across
   incompatible bins. A smooth-density overlap integral would need bandwidth
   sensitivity and separate treatment of atoms such as zero land.
5. **Gaps alongside overlap:** retain group medians, tails, and differences in
   below-threshold shares. Overlap does not negate a mean gap, unequal access,
   discrimination, or a policy rationale. A gap does not imply complete economic
   separation of groups.

## First pilot and data exposure

The initial scope is rural India and rural Bihar, using NSS 77 visit 1. The raw
blocks and existing land notebooks were inspected before this document was
written. This is an exploratory design record, not a blinded preregistration.

The pilot uses self-reported ST, SC, OBC and Others categories, with religion kept
as a separate source field. These are broad administrative social groups, not
individual jatis. Others must not be relabelled upper caste, and religion is not
itself a caste category. The pilot makes no causal claims and does not infer caste
from surnames.

Fixed land thresholds: 0, 0.1, 0.5, 1, 2 and 5 acres. Consumption thresholds:
Rs 500, 1,000, 1,500, 2,000, 3,000 and 5,000 per person per month. These are
illustrative, historical nominal benchmarks, not official poverty lines.
Pooled quartiles are calculated separately within each geographic universe.
The ECDF plots zoom to 5 acres / Rs 5,000 without trimming or renormalizing the
sample; the CSVs retain the full curves. No winsorization is used.

## Denominators and missingness

Household weights are primary. A future person-weighted estimate should use
household weight multiplied by household size and be labelled separately. Never
call a household share a share of people. Do not pool administrative accounts,
cardholders, survey households and village means into one distribution.

The entire household frame is retained in the local analysis file. Missing land
blocks are excluded from land estimates; threshold outputs give their weighted
share and worst-case bounds if every missing household is below versus above the
threshold. Sparse category rows become zeros only within a present, fully
reconciled land block. Recorded 0.00 acres can include amounts below 0.005 acre.
No area cutoff is treated as proof a household owns only a homestead.

## Uncertainty and diagnostics

Threshold estimates and their pairwise percentage-point differences have
approximate 95% pointwise percentile intervals from 999 bootstrap resamples of
PSUs within states, seed 20260910, retaining the released household weights.
Resample PSUs on the entire regional frame before evaluating group domains.
Use the same draws for differences; comparing two marginal intervals is not a
confidence interval for their difference.

This pilot bootstrap preserves clustering and state composition but not the
full NSS substratification, second-stage design or finite-population corrections.
It is not the official NSS variance estimator, and no claim is made that it is
conservative. There are no significance tests, simultaneous bands, or formal
stochastic-dominance conclusions. Pairwise ranking and pooled-rank summaries are
explicitly descriptive point estimates in this pilot. The weight-only effective
sample size in diagnostics is not a cluster-adjusted effective sample size.

Checks implemented: unique household keys, exact demographic universe, land-to-
household cardinality, category duplicates, missing values, valid weights and
codes, component/total reconciliation, file hashes, Parquet round trip, explicit
ties, brute-force verification of pairwise probabilities, missing-outcome bounds,
and local lint/tests. Every curve retains its full denominator.

## Extensions that could change the interpretation

- **Geography:** show within-state and rural/urban comparisons before presenting
  nationally pooled overlap as overlap among comparable neighbours. Then
  standardize each group's CDF to common geographic weights on common support;
  report dropped places and their population weights. State or district fixed
  effects alone do not produce a distributional comparison.
- **Direct income:** use IHDS household income, with total/per-person units and
  annual/monthly conversion stated. Retain legitimate zero and negative net
  incomes. Assess the survey's income imputation and nonresponse before use.
- **Wealth:** use AIDIS asset values and debts to distinguish gross assets from
  net wealth. Acres and asset-count indices are not rupee wealth. Keep survey
  years separate or apply documented deflators with a fixed reference year.
- **Jati:** use recorded, validated jati labels in Bihar land records to examine
  finer categories among accounts. Audit how labels were assigned. Include
  owners-only and all-household results separately; do not manufacture the
  missing landless population from an owner register.
- **Ration cards:** first establish whether caste is recorded and who enters the
  register. Cardholder composition P(caste | card type) is different from the
  caste-specific coverage rate P(card type | caste). The latter needs a full
  caste-specific denominator. BPL/AAY/PHH are administrative statuses rather
  than interchangeable measures of income poverty.
- **Full inference:** implement the official NSS design using its estimation
  documentation, resolve singleton substrata, validate against published
  estimates, and propagate uncertainty into ranks and overlap coefficients
  before turning the pilot into a paper.

Release of a substantive paper should follow an independent empirical review.
No independent model review has been conducted for this initial pilot.

Five Rajasthan households have zero released weight. They are preserved in the
local data file and excluded from weighted analyses and reported analytical
sample counts. The analytical India sample has 58,035 households.
