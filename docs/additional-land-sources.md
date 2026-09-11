# Rajasthan and Odisha: what is ready for an economic analysis?

Local audit, 2026-09-10. This was a read-only inspection of source code, Parquet
schemas and aggregate diagnostics. No scraping or source-repository edits were
performed. Counts are snapshots of local files, not completed statewide censuses.

## Rajasthan Record of Rights

Sources: `../rajasthan-ror/src/rajasthan_ror/parse.py`, `plots.py`, README,
`raw/villages.parquet` and `raw/pilot/owners.parquet`.

The location file has 50,109 rows representing the portal's location/sheet frame;
these are not necessarily distinct villages. The pilot owner file has 16,388
owner occurrences across 2,712 distinct `(giscode, plotno)` keys. It retains
`jati`, `area_ha`, ownership `share`, `khata`, `n_owners`, `via`, place and plot
identifiers. In that file, 268 rows have missing jati, 86 missing shares, and
8,598 are `via` rows. These figures describe this pilot, not all raw crawl data.

A consequential trap is in `rows_from_record`: a `via` record obtains the
entire source plot's `data` block. That correctly supplies an owner list linked
through `ownerplots`, but also copies the source `area_ha` and `plotid`. A
linked plot's independent area is therefore not established by its parsed row.
No missing areas in the output does **not** mean complete area measurement.

Before land-amount comparisons:

1. Restrict measurement to directly observed plot areas or obtain each linked
   plot's own area; never add inherited `via` areas as distinct measured plots.
2. Reconcile plot identity and duplicate appearances across sheets. The current
   crawl omits some subdivided/slashed plot numbers, according to its README.
3. Parse and reconcile ownership fractions, retaining unclear shares. A full
   plot area repeated on each co-owner row is not each owner's landholding.
4. Distinguish person, co-owner occurrence, khata, household and plot. Within-name
   aggregation alone is not a defensible household identifier.
5. Build a reviewed state-specific jati crosswalk; the recorded string is not
   an official-category code or an inferred surname label.
6. Report coverage and selection. Landholders are not all households, and
   directly fetched plots are not necessarily a probability sample of plots.

Potential payoff: recorded-jati landholding comparisons and a link between
name information and economic resources, conditional on a validated denominator.
A nonmatch to a land record cannot be counted as landlessness.

## Odisha Record of Rights

Sources: `../odisha-ror/parse_ror.py`, `fetch_ror.py`, README,
`raw/villages.parquet` and `raw/tenants.parquet`.

The village frame has 51,823 rows. The tenant extract has **3,056,090 rows**, each
a tenant occurrence on a khatiyan, rather than a deduplicated individual or
household. It retains `caste_or`, person/relative fields, residence, district,
tahsil, village, khatiyan identifiers, the original tenant text cell and fetch
time. The actual schema contains **no area or ownership-share field**.

The fetcher extracts only text cells containing the caste marker and stores
those cells plus response metadata. It does not retain the full RoR HTML or
plot-area table. Thus the current saved extract cannot yield acreage simply by
changing its tenant parser. A separate retained source or new area collection
would be necessary; neither was undertaken in this audit.

The existing README also distinguishes settlement vintage from fetch time,
notes landholder selection, and describes a crawl order favoring particular
districts. Full local coverage and settlement dates need an audit before
population claims. Village codes must be keyed with their tahsil (and district).

Potential payoff now: direct recorded caste/name/place comparisons, with the
right denominator. Potential payoff after additional data work: jati-specific
land distributions. Present readiness should not be confused with that future
possibility.

## Relationship to the synthesis

The [Passing Glance project](../../passing-glance/README.md) asks what a stranger
can infer from material cues, names and context. These land sources can supply
independently recorded identity and economic context once measurement is
validated. Land wealth is usually not observable on the street; it should not be
silently treated as a visible cue.
