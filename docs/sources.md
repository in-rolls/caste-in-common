# Source inventory and audit

Inspected 10 September 2026. Local paths assume this repo is next to `land` and
`ration`. Raw inputs remain in their original locations.

| Source | Available evidence | Use | Constraint |
|---|---|---|---|
| NSS 77, schedule 33.1 | Local raw converted blocks, DDI XML, and earlier derived extracts in `../land/data/nss77_sch331` | First pilot: land and consumption by reported ST/SC/OBC/Others | Rural households; consumption is not income; broad groups |
| Bihar land records | `../land/data/account.csv.gz`, land-type parquet and caste coding files; distribution notebooks | Fine account-level distributions, subject to label audit | Register accounts are not unique people/households; omits landless households |
| IHDS-II | Full ICPSR 36151 R bundle and derived land extracts in `../land/data/ihds2` | Next: direct household income, consumption, land and assets | Audit raw variables; broad groups and detailed jati have different availability; no first-pilot income results |
| SHRUG | Official metadata checked; `../land/shrug-scratch` also exists | Geography, contextual comparisons; possibly bounds where compatible marginals exist | Published geographic aggregates are not caste-by-household microdata |
| Ration-card database | Two compressed parts and gzip index in `../ration`; uncompressed size in index manifest is about 56.7 GB | Possible administrative deprivation comparison | Top-level schema lacks an explicit caste column; detail payloads and coverage not yet audited |
| AIDIS | Official NSS documentation describes schedule 18.2; no local household asset file identified in this inspection | Monetary gross assets and net wealth | Obtain/audit data and weights; separate from schedule 33.1 |

## NSS definitions and corrections

The pilot reads the three original converted visit-1 CSV blocks and records their
SHA-256 hashes in `output/provenance.json`. The local DDI at
`../land/data/nss77_sch331/raw/ddi.xml` identifies files F28, F33 and F35 and states
final weight = MLT/100. No extra division by NSC is applied to these converted data.

Official source: [MoSPI survey catalog](https://microdata.gov.in/NADA/index.php/catalog/157).
The [field instructions](https://www.mospi.gov.in/sites/default/files/NSS7733/77th_V_I_Final.pdf)
provide the definitions used here, in sections 3.4.5.6 and 3.5.11. The catalog's
[related materials](https://microdata.gov.in/NADA/index.php/catalog/157/related-materials)
include the estimation procedure; two download endpoints returned gateway errors
when checked. Full design-based variance validation remains a follow-up.

Two inherited definitions must not be propagated:

- `scripts/90_nss_ingest_bihar.ipynb` in `land` renames `b4q9` to
  `mpce_monthly`, but the raw field is **household** usual monthly consumption.
  Divide by `b4q1` household size for per-person monthly consumption.
- That notebook calculates land owned as total land minus leased-in area. The
  total also includes otherwise-possessed categories. Reconstruct ownership from
  `b5q3` for categories 01 + 05 + 06: owned-and-possessed other land,
  owned other land leased out, and owned-and-possessed homestead. Exclude leased-in
  categories 02/03/07/08 and otherwise-possessed categories 04/09.

All 57,978 present land blocks reconcile exactly up to floating-point precision:
sum(categories 01–09) equals category 10. The other 62 of 58,040 households have no
land block. Their missing land outcomes remain missing. These findings are
recorded here; this project does not modify the sibling land analysis.

The field instructions distinguish land in acres, rounded to two decimal places,
from land value. Reported zero includes sufficiently small positive holdings.

## SHRUG

The official [SECC metadata](https://docs.devdatalab.org/SHRUG-Metadata/Socio-Economic%20and%20Caste%20Census%20(2012)/secc-metadata/)
and [consumption metadata](https://docs.devdatalab.org/SHRUG-Metadata/SECC%20consumption/secc-cons-metadata/)
describe geographic aggregates and predicted consumption. A village caste share
and village poverty rate do not identify which households are poor. Weighting
village means by caste shares gives a distribution of village environments, not
household resources conditional on caste. Compatible same-unit marginals can
bound a joint share, but cannot recover it without assumptions. Population caste
shares and household poverty shares do not even have the same denominator.

SECC highest-earner income bands concern the highest-earning household member;
they are not household total earnings or per-person income. Access to actual
joint microdata could change the source's usefulness and should be checked
separately from access to SHRUG aggregates.

## IHDS

See the official [constructed variables](https://ihds.umd.edu/data/constructed-variables)
and [social-group documentation](https://ihds.umd.edu/node/191).
The latter page describes the older wave; variable IDs must be checked against
the wave-II questionnaire and codebook before reuse. The existing `land` ingest
uses wave-II ID13 for caste and ID11 for religion. Its derived extract has no
income field, but the full household R file is locally available.

## Ration schema

A read-only inspection of the decompressed database header found these top-level
tables: ration_card_details, family_members_tables, district, town, village,
fps, tahsil and panchayat. The card table includes card_type and references to
family details, with no explicit caste column. `family_members_tables.sub_table`
could hold richer serialized content; that content was not decoded in this pilot.
No names, card numbers, phone numbers or household records are included in this
repository. This header inspection establishes schema, not state coverage or
whether caste is absent everywhere.
