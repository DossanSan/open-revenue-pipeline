"""Atomically export a verified dbt mart for Power BI. Run after dbt build."""
import argparse
from datetime import date, datetime, timezone
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row

from pipeline.extract import atomic_json


def export(output):
    with psycopg.connect(row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT month, payment_type, trip_count, priced_trip_count,
                trip_total_usd, fare_usd, tips_usd, tolls_usd, extras_usd,
                amount_coverage, component_gap_usd, extracted_at_utc
                FROM marts.monthly_payment_metrics ORDER BY month, payment_type""")
            rows = cursor.fetchall()
    if not rows:
        raise ValueError("Refusing empty export")
    normalized = [{k: (v.isoformat() if isinstance(v, (date, datetime)) else
                        str(v) if isinstance(v, Decimal) else v)
                   for k, v in row.items()} for row in rows]
    atomic_json(output, {"manifest": {"exported_at_utc": datetime.now(timezone.utc).isoformat(),
                                      "source": "marts.monthly_payment_metrics", "currency": "USD"},
                         "records": normalized})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="public/dashboard.json")
    args = parser.parse_args()
    export(args.output)
