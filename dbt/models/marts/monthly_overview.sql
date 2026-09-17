SELECT
    month,
    SUM(trip_count) AS trip_count,
    SUM(priced_trip_count) AS priced_trip_count,
    SUM(trip_total_usd) AS trip_total_usd,
    SUM(trip_total_usd) / NULLIF(SUM(priced_trip_count), 0) AS avg_recorded_trip_value_usd,
    SUM(priced_trip_count)::numeric / NULLIF(SUM(trip_count), 0) AS amount_coverage,
    MAX(extracted_at_utc) AS extracted_at_utc
FROM {{ ref('monthly_payment_metrics') }}
GROUP BY month
