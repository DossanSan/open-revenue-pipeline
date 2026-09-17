# Data contract and metric definitions

- Source: City of Chicago, Taxi Trips (2024-), dataset `ajtu-isnz`.
- Catalog: https://data.cityofchicago.org/Transportation/Taxi-Trips-2024-/ajtu-isnz
- API: https://data.cityofchicago.org/resource/ajtu-isnz.json
- Metadata: https://data.cityofchicago.org/api/views/ajtu-isnz.json
- API guide: https://dev.socrata.com/docs/queries/
- Portal terms: https://www.chicago.gov/city/en/narr/foia/data_disclaimer.html
- Initial period: [2024-01-01, 2026-01-01), source-local calendar months.
- Grain: month x payment type. Currency: USD.
- No keys, taxi IDs, trip IDs, coordinates or customer data are requested or stored.

The source timestamps are local floating timestamps rounded to 15 minutes. They are
not labelled UTC. API aggregation happens before download to keep traffic small.
The `raw` layer therefore means unmodelled API aggregates, not trip-level raw records.

## Definitions

| Field | Definition |
| --- | --- |
| trip_count | Count of all source trips in the cell |
| priced_trip_count | Count of trips with a non-null trip_total |
| trip_total_usd | Sum of recorded total cost, including tips, tolls and extras |
| average recorded trip value | SUM(trip_total_usd) / SUM(priced_trip_count) |
| amount coverage | SUM(priced_trip_count) / SUM(trip_count) |
| component gap | total minus fare, tips, tolls and extras |

Ratios must be recomputed from sums; do not average segment averages. Missing amounts
stay null, not zero. Zero/negative monetary values are retained for inspection rather
than silently removed. Component gaps are diagnostic, not automatically a hard failure.

All payment categories remain visible, including Dispute and No Charge. Accordingly,
the sum is recorded trip value, not a claim about settled payments or net revenue.
Cash tips are generally not reported and the city says not all trips are reported.
Coverage reflects missing amounts in reported trips, not coverage of all taxi activity.

## Quality gates and revisions

1. Whole calendar months only; no partial or future months.
2. Unique month/payment key, expected month coverage, valid counts and finite amounts.
3. Independent API count and monetary control totals per month.
4. Snapshot checksum verified before loading.
5. Transactional interval replacement: reruns do not append duplicate records;
   disappeared categories in a revised month are removed by replacement.
6. Post-load count reconciliation; dbt grain/count/total tests before BI export.

The source offers no snapshot isolation across requests. A revision between grouped
and control queries can fail reconciliation; rerun, do not publish the mismatch.
Monthly schedules currently re-read the fixed 2024–2025 portfolio window to catch
revisions. Extending the end date is explicit; this is not yet a live 2026 report.

## Analysis boundaries

Supported: trend, seasonality, payment mix, amount coverage, volume vs average-value
decomposition. The identity V = priced trips x average recorded value permits a
descriptive bridge, but does not establish causes. Unsupported: customer retention,
churn, MRR/NRR, LTV/CAC, marketing attribution or causal ROI.
