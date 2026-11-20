# Sources for Scallop Tally Repair

## Inspired by
Inspired by e-logbook and landing declaration validation, where incomplete or incorrect submissions are caught by automated checks before the data is used (https://assets.publishing.service.gov.uk/media/5f7b247fd3bf7f2d4c18137b/E-log_FAQS.pdf). Moved to a small scallop cooperative whose nightly dashboard shows rows_in that do not equal passed plus failed.

## Concepts tested
- Null semantics in pandas: NaN comparisons evaluate to False and rows silently vanish
- Range and domain checks with precisely defined boundary inclusivity
- Referential integrity against the vessel registry, with unmatched vessels reported rather than dropped by an inner merge
- Structured per-row failure output instead of raising on first error
- Row count reconciliation (in = passed + failed)
- Not mutating the input DataFrame

## Trap
Filters like df[df.weight_kg > max] and df[~(df.weight_kg >= min)] evaluate to False for NaN, so null rows are in neither set and the counts silently drift. The boundary flags in config.py also differ between the weight limit and the season close, so hard-coding < or <= for both fails. A merge on raw vessel ids drops ' mv-014 ' without any error.

## Key concepts found for the topic
- Rule-based validation as explicit, named checks (schema/dtype, null/completeness, range/domain, uniqueness, referential integrity, cross-field consistency) that each return structured results rather than raising on first failure
- Quarantine versus reject versus fail-the-run policy: bad rows are routed to a reject table with a reason code so good data keeps flowing, while thresholds (e.g. reject rate above X%) halt the batch
- Natural-key uniqueness and idempotent loads: duplicate detection must use the true business key (vessel, trip, species, landing date, port) and late or re-sent files must not double-count
- Referential integrity against reference data (species codes, vessel registry, port list, quota allocations) including expired or retired codes and case/whitespace normalisation before comparison
- Unit and plausibility checks: weights in kg vs lb vs tonnes, per-vessel hold capacity, price per kg bands, dates in the future or outside the fishing season, with boundary inclusivity defined precisely
- Null semantics in pandas: NaN vs empty string vs sentinel values (-1, 9999, 'N/A'), dtype coercion with errors='coerce', nullable dtypes, and how comparisons with NaN silently evaluate to False
- Aggregate and reconciliation checks: row counts in versus out, sum of weights per day/species against a control total, freshness and volume anomaly checks against a trailing baseline
- Deterministic, machine-readable output of check results (fixed column names, ordering, rounding, severity levels) so downstream alerting and tests can rely on it

## Searches
- fisheries electronic logbook landing declarations data validation errors catch weight discrepancies audit findings
- NOAA OR EU fisheries catch reporting duplicate landing records species code mismatch quota overcount data quality postmortem
- fishery cooperative quota monitoring data pipeline incorrect landings weight units pounds kilograms conversion error case study

## Pages found
- [Electronic Logbook (E-log) FAQs](https://assets.publishing.service.gov.uk/media/5f7b247fd3bf7f2d4c18137b/E-log_FAQS.pdf)
- [UK Commercial Sea Fisheries Landings by EEZ 2012- ...](https://assets.publishing.service.gov.uk/media/5f760a1a8fa8f55e30433b98/2020-UK_Commercial_Sea_Fisheries_Landings_by_EEZ_2012_-_2019_report.pdf)
- [Technologies for Improving Fisheries Monitoring](https://www.edf.org/sites/default/files/oceans/Technologies_for_Improving_Fisheries_Monitoring.pdf)
- [NMFS Proposes Electronic Reporting Requirement for Commercial Fishing Logbooks – Office of Advocacy](https://advocacy.sba.gov/2026/05/28/nmfs-proposes-electronic-reporting-requirement-for-commercial-fishing-logbooks)
- [European Union Certification Requirements | NOAA Fisheries](https://www.fisheries.noaa.gov/national/seafood-commerce-trade/european-union-certification-requirements)
