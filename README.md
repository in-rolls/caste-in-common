# Caste in Common

**How much do economic distributions overlap across caste groups—and how large
are the gaps?**

Take 100 households from each group. How many own less than an acre? How many
consume less than the same rupee amount? Draw one household from each of two
groups: how often does the one from the poorer group have more?

The project puts those questions next to one another. Broad overlap and large
inequalities can coexist. Neither is assumed away.

Start with the [first land and consumption results](output/first-look.md), built
from local NSS 77 survey data already available in the sibling `land` repository.
They describe rural households, with self-reported ST, SC, OBC and Others labels.
They include reported zero holdings and use household survey weights.

![The same threshold for each group](output/rural_india_thresholds.png)

[Income, jati and overlap methods](docs/informativeness.md) ·
[IHDS income results and sorted label comparisons](output/ihds-first-look.md) ·
[IHDS ingestion audit](docs/ihds-audit.md) ·
[Research design](docs/design.md) · [Source inventory and audit](docs/sources.md) ·
[Data dictionary and join contract](docs/data-dictionary.md)

## Reproduce

```sh
make setup
make ci
make pilot NSS_DIR=../land/data/nss77_sch331/csv
.venv/bin/python -m pip install -e '.[ihds]'
make ihds
```

Python 3.11 or later. `make ci-docker` runs formatting checks, lint and tests in a
standard Python image. No API key is needed for this pilot. The original NSS
microdata require authorized access; they are not included in this repository.
See the source inventory for their official catalog and local provenance.

`make pilot` writes a local, ignored household Parquet file and regenerates the
aggregate CSVs, figures and prose under `output/`. It reads the raw converted
survey blocks rather than the earlier derived household extract. The generated
note is the source of result tables; figures and prose share computed outputs.

## What is measured

- Land thresholds in acres; consumption thresholds in survey-year rupees per
  person per month. Every threshold CSV distinguishes `<` from `<=`.
- Full weighted ECDFs, including zeros; plot limits zoom without dropping tails.
- Shares below common pooled quartiles, with the inverse-ECDF convention.
- Pairwise less/equal/greater probabilities and explicitly labelled half ties.
- Shared mass in fixed bins, with the bin edges recorded. This overlap statistic
  depends on those edges and is not the percentage of identical households.
- Threshold differences and approximate PSU-bootstrap intervals; see the design
  for the approximation's limits and missing-outcome bounds.

The NSS pilot measures land and consumption. The IHDS-II extension measures
annual net household income per person, reported jati-label distributions,
within-state pairwise probabilities, reverse tail composition, and prediction
on held-out PSUs. It extends the ingestion conventions in `../land/scripts/97`
and verifies common fields against that project’s existing household extract.

`make ihds` reads the existing ICPSR R household release, writes an ignored
Parquet extract, and regenerates `output/ihds_*` and `output/ihds-first-look.md`.
Override `IHDS_SOURCE` to use another location. The full prediction run evaluates
three split seeds and three smoothing strengths; no new data download is needed.

Detailed responses are normalized for typography, not harmonized into verified
jatis. Their predictive results are a measurement pilot, not a conclusion about
all information contained in jati. The research memo documents the next sources:
REDS, Bihar/Telangana surveys, HCES, AIDIS, CPHS and VDSA.

These are descriptive comparisons. They do not estimate the causal effect of
caste or settle a policy question. `Others` is a residual category, not a verified upper-caste classification;
its meaning differs between NSS and IHDS. Household shares are not person shares.

The separate [Passing Glance synthesis](../passing-glance/README.md) connects
these economic distributions to the information a stranger can obtain from
names, visible material circumstances and context.
