-- The loader owns the explicit extraction interval; this view retains all loaded history.
SELECT
    month,
    payment_type,
    trip_count,
    priced_trip_count,
    trip_total_usd,
    fare_usd,
    tips_usd,
    tolls_usd,
    extras_usd,
    extracted_at_utc
FROM {{ source('chicago', 'taxi_monthly') }}
