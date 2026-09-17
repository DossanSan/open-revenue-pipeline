SELECT
    month,
    payment_type,
    trip_count,
    priced_trip_count,
    trip_count - priced_trip_count AS missing_amount_trips,
    trip_total_usd,
    fare_usd,
    tips_usd,
    tolls_usd,
    extras_usd,
    trip_total_usd / NULLIF(priced_trip_count, 0) AS avg_recorded_trip_value_usd,
    priced_trip_count::numeric / NULLIF(trip_count, 0) AS amount_coverage,
    trip_total_usd - (fare_usd + tips_usd + tolls_usd + extras_usd) AS component_gap_usd,
    extracted_at_utc
FROM {{ ref('stg_taxi_monthly') }}
