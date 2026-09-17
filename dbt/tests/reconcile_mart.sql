WITH source_totals AS (
    SELECT SUM(trip_count) AS trips, SUM(trip_total_usd) AS value
    FROM {{ source('chicago', 'taxi_monthly') }}
), mart_totals AS (
    SELECT SUM(trip_count) AS trips, SUM(trip_total_usd) AS value
    FROM {{ ref('monthly_overview') }}
)
SELECT s.trips AS source_trips, m.trips AS mart_trips,
       s.value AS source_value, m.value AS mart_value
FROM source_totals AS s CROSS JOIN mart_totals AS m
WHERE s.trips IS DISTINCT FROM m.trips OR s.value IS DISTINCT FROM m.value
