SELECT month, payment_type, trip_count, priced_trip_count
FROM {{ ref('monthly_payment_metrics') }}
WHERE trip_count <= 0
   OR priced_trip_count < 0
   OR priced_trip_count > trip_count
   OR (priced_trip_count > 0 AND trip_total_usd IS NULL)
