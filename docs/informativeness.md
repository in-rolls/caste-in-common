# How informative is jati about economic position?

Research and design memo, 2026-09-10. The empirical starting point is the
[NSS pilot](../output/first-look.md) and the new
[IHDS income and reported-label pilot](../output/ihds-first-look.md).
The objective is to measure how much an identity narrows the distribution of
economic outcomes, while showing both group differences and individual overlap.

## Use three complementary measures

### 1. Two random draws: probability of superiority

For independent draws from groups A and B, use

`AUC(A,B) = P(Y_A > Y_B) + 0.5 P(Y_A = Y_B)`.

Estimate this with survey weights on both draws. Also show the three raw
probabilities: A has more, B has more, equal. For a public presentation, use
"Out of 100 random pairs, which household has more?" A 60% score means about
40% go the other way; it does not mean the first group is 60% richer. If using
an ROC routine, group A is the positive class and income is the score.

The direction must be fixed explicitly. Our original `stats.pairwise` helper
returns a half-tie score for A being *lower*. The new IHDS tables explicitly
construct and label the opposite, A being *higher*, from the returned components.

AUC measures ordering, not every form of separation. Example: A is equally
likely to have 0 or 2; B always has 1. AUC is 0.5, yet their supports do not
overlap. This example is a regression test. A pairwise matrix may also contain
cycles, so one scalar jati ranking can conceal differences in distribution shape.

For land, ties at zero must remain visible. Report landlessness, unconditional
AUC, and positive-land distributions separately; conditioning on ownership
answers a different question. For wealth, retain debts and negative net worth.

### 2. Shared mass and common-threshold curves

The overlap coefficient is `OVL = integral min(f_A(y), f_B(y)) dy`, with a sum
for discrete outcomes. It equals `1 - total variation distance`. With equal
class priors, optimal classification accuracy from Y alone is `1 - OVL/2`.
Those equal priors are a comparison device, not actual caste population shares.

For finite samples, estimated overlap depends on smoothing or bin width. Publish
fixed-bin overlap at several substantively useful resolutions, alongside weighted
ECDFs. Coarsening bins generally hides separations within bins. Do not report
"the overlap" from one convenient violin bandwidth. Box plots show only a few
quantiles; violins obscure point masses and may invent density below zero.

A strong lead exhibit is an ECDF: x = rupees/person/month, y = percentage below
that amount, one curve per group. Mark ₹2,000 and ₹5,000, retain the full
denominator, and supply the full curve alongside any zoom. A sorted dot-and-range
plot offers a compact companion: median and 10th–90th percentile, with sample and
PSU counts. These ranges show spread, not confidence intervals.

### 3. Predictive information, evaluated on new households

The main question is: how much better can we predict an income distribution once
jati is known? Compare held-out probability forecasts with identical test samples:

1. Population distribution, no identity information.
2. Broad caste category alone.
3. Geography alone (start with state × rural/urban).
4. Geography plus broad caste.
5. Geography plus broad caste plus documented jati.

Use weighted log loss for income bands, plus Brier scores/calibration for each
poverty threshold in a fuller implementation. Continuous outcomes can use
weighted CRPS, quantile loss, and held-out rank prediction. The current code
implements the log-loss pilot, not these further scoring methods.

Ideal expected log-score improvement is conditional mutual information. The
observed improvement from a fitted model is a model-dependent predictive gain;
it can be negative and is not all information available in the identity.
Report gains in nats/bits and relative to the baseline loss, not ordinary
classification accuracy when nearly everyone is below a cutoff.

Hold whole PSUs out before recoding or filtering. Train empirical ranks,
smoothing, crosswalk choices informed by outcomes, and any feature selection
inside training data. A human crosswalk built without income can be frozen
before evaluation. Include rare, missing, and unseen labels through explicit
fallbacks and report weighted coverage. Within-village prediction and prediction
in new villages are different tasks; the first pilot uses the latter.

The implemented hierarchical frequency model uses Kish weight ESS for shrinkage,
30 training households and five training PSUs for eligible cells, and prior
strengths 10/30/100. Three seeds assess split sensitivity, not sampling confidence
intervals. Broad-versus-jati gains need PSU-based uncertainty before strong
conclusions. Harmonized labels and alternative geographic resolutions are
needed before interpreting a small gain as evidence about jati itself.

## A sorted jati version

Publish **two different orders**, labelled clearly:

- A contemporary economic order, learned in training PSUs and evaluated in held-out
  PSUs. Show the matrix of pairwise wins, not just one rank. The current figures
  sort sample medians descriptively and make no out-of-sample rank claim.
- An independently specified historical order within a region, then ask how often
  the historically higher-ranked group has higher contemporary income, assets,
  education, or land. A literacy order is an economic/educational ranking, not a
  timeless ritual ranking.

The [1931 Brahmin comparison](https://www.gojiberries.io/relative-status-of-brahmins-across-india-in-1931/)
provides a useful design: relative literacy rankings differ across provinces.
Archive original census tables, distinguish literacy from English literacy,
verify age and sex denominators, and harmonize historical boundaries before
matching modern jatis. Preserve uncertain crosswalks and calculate alternative
rankings rather than forcing a national ladder. Binary historical literacy also
has many ties: its pairwise half-tie AUC is `0.5 + 0.5(p_A - p_B)`.

More revealing comparisons would include land versus schooling rankings,
within-district versus nationally drawn pairs, rural versus urban rank reversals,
and how much group ranks persist when averaging several years of income.

## Visible poverty is a further measurement problem

The user's clarified question concerns visible living standards: a difference
between ₹2,000 and ₹2,500 per person per month may not yield a difference a
stranger can discern. Perfectly observed income is therefore not the same cue
as ordinary material appearance. Coarsened income bands and self-reported
non-facial material profiles can test part of that channel; observer judgments
need separate evidence. The new [Passing Glance synthesis](../../passing-glance/README.md)
connects this question to names, perception research, changing consumer goods
and income volatility. Economic AUC is one component, not a measure of what a
passer-by can identify.

## Poverty clustering and the reverse question

Large shares below the same low threshold can be substantively striking.
They do not mathematically imply that caste is uninformative: multiplying every
income by 0.01 leaves rank AUC unchanged. A compressed histogram can also conceal
material differences in food security, assets, or income risk within the bottom.

The proposed ₹2,000 and ₹5,000 cutoffs should appear together, with their price
year explicit. ₹5,000 in 2011–12 is not ₹5,000 now. For cross-year exhibits,
choose one purchasing-power base year and deflate with a documented price index;
show state/rural-urban price sensitivity. Treat these as illustrative material
standards unless tied to a specified official poverty definition. Consumption,
net income, earnings, land quantity, and wealth value remain distinct outcomes.

"Only the rich reliably cue status" asks the reverse conditional:

`P(jati=j | income >= t)` versus the population prior `P(jati=j)`.

At each threshold show tail composition, enrichment/lift (posterior/prior),
and recall (share of that jati in the tail). A high lift can coexist with low
posterior probability, and high tail purity can identify only a tiny minority
of a group. Test both tails, report rare-tail sample support, and avoid choosing
thresholds after seeing which one produces the strongest story. The new
`ihds_tails.csv` computes these quantities for broad groups. Detailed-jati
reverse prediction awaits a harmonized crosswalk.

A particularly clear display would put caste composition in the bottom, middle,
and top of the *same* income distribution beside population composition. Do not
infer broad categories from surnames to construct this test: label error could
produce the overlap being investigated.

## Wider data search: priorities and actual readiness

| Source | What it can contribute | Access and limitation established in this audit |
|---|---|---|
| IHDS-II, 2011–12 | Income, consumption, assets, literal jati/sub-jati; national rural and urban sample | Full local file available; new tested pilot done. Existing land extract and conventions reconciled. Detailed-label harmonization remains necessary. [Official access](https://ihds.umd.edu/data/data-download) |
| REDS, 2006 census / 2007–08 detailed household survey | Particularly promising fine-jati, land, occupation, household income, and repeated observations | Original research describes a 99,760-household census of 202 villages across 15 states; caste data absent in Kerala/Gujarat for that analysis. Detailed survey is a smaller sample. Download/access not yet established. [Primary research data description](https://ageconsearch.umn.edu/record/121671/files/cdp1007.pdf) |
| Bihar JEEViKA baseline, 2011 | Detailed jati, consumption and land in a directly relevant existing study | Joshi, Kochhar and Rao use 8,973 households in seven districts, oversampling SC/ST hamlets. Not representative of Bihar as a whole. The separately catalogued 2011 retrospective survey is a different sample; do not conflate them. [Published study](https://academic.oup.com/ooec/article/doi/10.1093/ooec/odab004/6520734), [separate catalog](https://microdata.worldbank.org/catalog/5912) |
| Bihar caste survey, 2023 | Caste-specific household income brackets and economic indicators | Local `../bihar_jati` contains the population release, not the later economic report. Locate and reconcile the economic tables before calculating rates. Household ₹6,000/month bins cannot be converted to per-person thresholds without joint household-size data. [Assembly proceedings, 7 November 2023](https://vidhansabha.bihar.gov.in/pdf/proceeding/17th_10th/07-11-2023.pdf) |
| Telangana SEEEPC, 2024, reports released 2026 | Recent state census of caste and socioeconomic indicators; promising jati-specific income/land distributions | Official PDFs located. Volume IV downloaded and checked: it contains population counts, not caste-by-income tables. Expert-group Volume I contains income-band and land summaries; source wording alternates individual/household denominators, requiring questionnaire/table reconciliation. Expert Volume II is also downloaded and inspected: 242-caste rankings, 56-caste land/assets exhibits and an analysis restricted to low-income respondents. Audit Version/Volume carefully. [Official directory](https://des.telangana.gov.in/publications/SEEEPC/), [expert report](https://des.telangana.gov.in/publications/SEEEPC/SEEEPC-IEWG%20Volume-1%2017-04-26.pdf) |
| HCES 2022–23 and 2023–24 | Recent consumption distributions and common rupee cutoffs by broad social group | Public-use catalog and documentation located. Better temporal anchor than old NSS/IHDS for contemporary consumption; audit social-group fields, weights, and free-item imputation before estimation. [Official 2023–24 catalog](https://microdata.gov.in/nada/index.php/catalog/237/related-materials) |
| AIDIS 2019 | Asset values, debts, net worth, broad social groups | Official microdata/report available; not yet ingested. Separate land acreage from land value and distinguish gross assets from net wealth. [Official catalog](https://microdata.gov.in/NADA/index.php/catalog/156), [official report](https://www.mospi.gov.in/sites/default/files/publication_reports/Report_no588-AIDIS-77R-SeptFinal_0.pdf) |
| SHRUG / SECC | Geography, deprivation and contextual comparisons | Public SHRUG aggregates are not household joint jati–income distributions. Consumption is predicted from other data, including IHDS; it is not an independent direct-income replication. [Official documentation](https://docs.devdatalab.org/), [codebook](https://shrug-assets.s3.amazonaws.com/static/main/assets/other/shrug-codebook.pdf) |
| Local ration cards / BPL | Administrative eligibility, if caste exists in the actual schema or linked records | No explicit caste field established in the top-level local schema; nested payloads not audited. Card categories measure program status, not an observed continuous income distribution. Coverage/exclusion matter. |
| CMIE CPHS | Monthly income histories and annual sums; household panel with caste attributes | Paid data; existing access not established. Fine-jati detail unverified. Audit reported income components and treatment of asset sales. [Provider](https://consumerpyramidsdx.cmie.com/), [identity attributes](https://www.cmie.com/kommon/bin/sr.php?kall=wproducts&portal_code=030020030010000000000000000000000000000000000&prd=poi&tabno=7010) |
| ICRISAT VLS / VDSA | Frequent transactions and annual income, assets, agricultural risk in poor rural communities | Official portal and documentation located; registration/data access needed. Village samples are geographically limited; caste coding must be inspected. [Microdata documentation](https://vdsa.icrisat.org/vdsa-microdoc.aspx), [database](https://vdsa.icrisat.org/vdsa-database.aspx) |
| Tamil Nadu Household Panel Survey | Repeated household outcomes; COVID phone rounds and later baseline | Official project located; detailed-jati fields and public access unverified. Pandemic telephone rounds do not establish ordinary-year volatility. [Project](https://www.tnhps.in/) |

The local [Rajasthan and Odisha audit](additional-land-sources.md) adds two
recorded-jati sources. Rajasthan has area/share fields but linked-plot area
reuse requires correction before summing. Odisha’s existing tenant extract has
no area field. Both select landholders.

The highest-return combination is harmonized IHDS + REDS for detailed jati,
HCES for recent consumption, AIDIS for wealth, and Telangana/Bihar tables for
large-sample state evidence. CPHS/VDSA answer the separate short-run dynamics
question. These sources should form parallel exhibits, not be pooled as if they
measure the same outcome, population, or price year.

## Existing research that should shape the argument

*Fractal inequality in rural India* is close to the proposed project. It finds
substantial within-category and within-jati variation in poor rural Bihar, and
shows why broad caste aggregates can conceal finer differences. Its sample
selection limits extrapolation. It supplies a comparison to replicate, not a
reason to assume the answer. [Joshi, Kochhar and Rao](https://academic.oup.com/ooec/article/doi/10.1093/ooec/odab004/6520734).

For a useful counterweight, *Caste Stratification and Wealth Inequality in India*
uses AIDIS and emphasizes wealth stratification and relatively limited overlap
for forward-caste Hindus. Consumption overlap cannot settle the wealth question.
[Zacharias and Vakulabharanam](https://doi.org/10.1016/j.worlddev.2011.04.026).

Telangana’s expert report supplies a direct rival to the idea that economic
clustering erases status distinctions. Its Volume II, printed pp. 91–96, compares
education, housing, work and other indicators among respondents reporting less
than ₹1 lakh annual income. Those are comparisons of other outcomes among
low-income respondents, not a measure of income overlap or a causal effect of
caste. Its question 27 has twelve income ranges, potentially much more useful
than the three broad income bands in the summary. The microdata or corresponding
jati-by-band counts are still needed. Do not sort jatis on a composite containing
income and then use income to validate that ranking: that would be circular.
[Official expert Volume II](https://des.telangana.gov.in/publications/SEEEPC/SEEEPC-IEWG%20Volume-2.pdf).

## Use interval-censored tables without making up incomes

For a pair of castes with shares `a_k` and `b_k` in identical ordered income
intervals, the mass of definitely greater pairs is

`L = sum_k a_k * sum_(l<k) b_l`.

Same-bin pairs have unresolved order, so a sharp bound on `P(A>B)` is
`[L, L + sum_k a_k*b_k]` when each bin admits multiple values. The same endpoints
bound the half-tie AUC. These are identification bounds, not confidence intervals.
Known exact-value bins (such as a separately recorded zero) need their known ties.
The tested `binned_superiority_bounds` helper implements the interval-bin case.

This makes coarse Bihar/Telangana tables usable without assuming uniform income
within a band. If both groups are mostly in the bottom band, the bounds may be
wide. That is lack of resolution, not demonstrated similarity within that band.
Different bin boundaries, missing-income categories, and rounded published
percentages must be reconciled first.

## Income consistency from year to year

IHDS 2004–05 and 2011–12 identify changes across roughly seven years. They cannot
identify one-year persistence without additional assumptions. Dividing annual
income by twelve does not create a monthly panel.

For CPHS or VDSA, start with complete nonoverlapping annual windows in constant
prices. Report rank correlation, transition matrices, and
`P(Y_(t+1) < threshold | Y_t < threshold)` alongside the overall prevalence.
Add the share poor in every observed year, the share ever poor, and the fraction
of months below the cutoff. Report transitions by baseline income and caste,
with attrition and household splits/migration explicit. Compare income and
consumption persistence. Analyze negative/zero income separately; percentage
changes and coefficients of variation become unstable near zero.

Separate seasonality, transient shocks, longer-lived changes and reporting error.
Compare single-year income with two/three-year averages; check same calendar
months; retain matched and unbalanced-panel diagnostics. A noisy baseline can
create apparent mean reversion. High volatility can coexist with persistent
poverty when fluctuations rarely clear a meaningful standard of living.

A current working paper using monthly CPHS data for 2016–19 models permanent and
transitory income risk and reports substantial income volatility and incomplete
consumption insurance. It supports investigating the hypothesis, but does not
supply our caste-specific annual persistence estimates.
[Chatterjee, Chopra, Neelakantan and Udupa, author research page](https://anandchopra.net/research/).

CPHS bottom-tail coverage is particularly consequential here. Drèze and Somanchi
compare it with other surveys and challenge its representation of poor
households; weighting alone need not repair missing segments.
[Primary analysis](https://www.ideasforindia.in/topics/poverty-inequality/weighty-evidence-poverty-estimation-with-missing-data).

Li, Millimet and Roychowdhury explicitly examine measurement error in IHDS
consumption mobility. Their partial-identification approach is a useful template:
observed transitions should not automatically be interpreted as true changes.
This is consumption over 2005–12, not annual income persistence.
[Published study](https://academic.oup.com/jrsssa/article/186/1/84/7008539).

A further connection joins the jati and volatility questions: jati may predict
access to insurance and transfers even when single-year income distributions
overlap. Mobarak and Rosenzweig use jati-linked survey information on shocks,
loans and transfers to study informal risk sharing alongside an insurance
experiment. Compare income losses with subsequent consumption losses and
transfers across jatis, without interpreting a descriptive difference as causal.
[Primary study](https://ageconsearch.umn.edu/record/121671/files/cdp1007.pdf).
