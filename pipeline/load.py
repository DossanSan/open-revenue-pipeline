"""Preview first; --apply atomically replaces only the validated source interval."""
import argparse
import json
import logging
from pathlib import Path

from pipeline.extract import MONEY, digest, normalize, reconcile


def load(path, apply=False):
    import psycopg

    snapshot = json.loads(Path(path).read_text())
    manifest, records = snapshot["manifest"], snapshot["records"]
    start, end = manifest["start"], manifest["end_exclusive"]
    records = normalize(records, start, end)
    if digest(records) != manifest["records_sha256"]:
        raise ValueError("Snapshot checksum mismatch")
    reconcile(records, manifest["source_control_totals"])
    # libpq reads PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD from the environment.
    with psycopg.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('raw.taxi_monthly')")
            exists = cursor.fetchone()[0] is not None
            if exists:
                cursor.execute("SELECT COUNT(*), SUM(trip_count) FROM raw.taxi_monthly WHERE month >= %s AND month < %s", (start, end))
                logging.info("SELECT preview existing rows/trips: %s", cursor.fetchone())
            else:
                logging.info("SELECT preview: target does not exist yet")
            logging.info("Incoming validated rows=%s period=[%s,%s)", len(records), start, end)
            if not apply:
                return
            # Serialize overlapping loads. DDL, delete and insert share one transaction.
            cursor.execute("SELECT pg_advisory_xact_lock(78234421)")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS raw")
            cursor.execute("""CREATE TABLE IF NOT EXISTS raw.taxi_monthly (
                month date NOT NULL, payment_type text NOT NULL,
                trip_count bigint NOT NULL CHECK (trip_count > 0),
                priced_trip_count bigint NOT NULL CHECK (priced_trip_count BETWEEN 0 AND trip_count),
                trip_total_usd numeric, fare_usd numeric, tips_usd numeric,
                tolls_usd numeric, extras_usd numeric,
                extracted_at_utc timestamptz NOT NULL, snapshot_sha256 text NOT NULL,
                PRIMARY KEY (month, payment_type))""")
            cursor.execute("DELETE FROM raw.taxi_monthly WHERE month >= %s AND month < %s", (start, end))
            cursor.executemany("""INSERT INTO raw.taxi_monthly
                (month,payment_type,trip_count,priced_trip_count,trip_total_usd,fare_usd,
                 tips_usd,tolls_usd,extras_usd,extracted_at_utc,snapshot_sha256)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                [(r["month"], r["payment_type"], r["trip_count"], r["priced_trip_count"],
                  *(r[field] for field in MONEY), manifest["extracted_at_utc"],
                  manifest["records_sha256"]) for r in records])
            cursor.execute("SELECT COUNT(*), SUM(trip_count) FROM raw.taxi_monthly WHERE month >= %s AND month < %s", (start, end))
            actual = cursor.fetchone()
            if actual != (len(records), sum(r["trip_count"] for r in records)):
                raise ValueError("Post-load reconciliation failed; transaction rolled back")
    logging.info("Committed validated interval replacement")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default="data/snapshot.json")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        load(args.snapshot, args.apply)
    except Exception as error:
        logging.error("Load failed: %s", type(error).__name__)
        raise SystemExit(1) from error
