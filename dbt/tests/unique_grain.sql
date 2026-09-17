SELECT month, payment_type, COUNT(*) AS row_count
FROM {{ ref('monthly_payment_metrics') }}
GROUP BY month, payment_type
HAVING COUNT(*) > 1
