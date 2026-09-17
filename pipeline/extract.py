"""Read-only Socrata extraction. No trip identifiers or individual locations."""
import argparse
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
import logging
import os
from pathlib import Path
import ssl
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LOG = logging.getLogger(__name__)
API = "https://data.cityofchicago.org/resource/ajtu-isnz.json"
PAGE_SIZE = 1000
MONEY = ("trip_total_usd", "fare_usd", "tips_usd", "tolls_usd", "extras_usd")
AGGREGATES = (
    "count(*) as trip_count,count(trip_total) as priced_trip_count,"
    "sum(trip_total) as trip_total_usd,sum(fare) as fare_usd,"
    "sum(tips) as tips_usd,sum(tolls) as tolls_usd,sum(extras) as extras_usd"
)


def validate_period(start, end):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first.day != 1 or last.day != 1 or first >= last:
        raise ValueError("Use month boundaries with start < end; end is exclusive")
    if first < date(2024, 1, 1):
        raise ValueError("This API dataset starts in January 2024")
    if last > date.today().replace(day=1):
        raise ValueError("Only completed calendar months are supported")
    return first, last


def request_json(params):
    url = API + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "open-revenue-pipeline/0.1"})
    # Use a configured CA bundle; never disable TLS verification.
    context = ssl.create_default_context(cafile=os.getenv("SSL_CERT_FILE"))
    for attempt in range(4):
        try:
            with urlopen(request, timeout=90, context=context) as response:
                body = json.load(response)
            if not isinstance(body, list):
                raise ValueError("API returned an unexpected response schema")
            return body
        except (HTTPError, URLError, TimeoutError) as error:
            if isinstance(error, HTTPError) and error.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 3:
                raise
            delay = 2 ** attempt
            if isinstance(error, HTTPError):
                retry_after = error.headers.get("Retry-After", "")
                if retry_after.isdigit():
                    delay = min(120, max(delay, int(retry_after)))
            LOG.warning("API request failed (%s); retry in %ss", type(error).__name__, delay)
            time.sleep(delay)
    raise RuntimeError("Unreachable retry state")


def decimal_value(value):
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError("Non-finite amount")
    return number


def normalize(rows, start, end):
    first, last = validate_period(start, end)
    normalized, keys = [], set()
    for row in rows:
        month = date.fromisoformat(row["month"][:10])
        payment_type = row.get("payment_type") or "(Missing)"
        key = (month.isoformat(), payment_type)
        if month.day != 1 or not first <= month < last or key in keys:
            raise ValueError("Invalid month or duplicate month/payment key")
        keys.add(key)
        trip_count, priced = int(row["trip_count"]), int(row["priced_trip_count"])
        if trip_count <= 0 or not 0 <= priced <= trip_count:
            raise ValueError("Invalid trip counts")
        result = dict(month=month.isoformat(), payment_type=payment_type,
                      trip_count=trip_count, priced_trip_count=priced)
        for field in MONEY:
            value = row.get(field)
            result[field] = None if value is None else str(decimal_value(value))
        if priced > 0 and result["trip_total_usd"] is None:
            raise ValueError("Missing total despite priced trips")
        normalized.append(result)
    expected = set()
    cursor = first
    while cursor < last:
        expected.add(cursor.isoformat())
        cursor = date(cursor.year + (cursor.month == 12), cursor.month % 12 + 1, 1)
    if {r["month"] for r in normalized} != expected:
        raise ValueError("Missing months: refusing to publish a partial snapshot")
    return sorted(normalized, key=lambda row: (row["month"], row["payment_type"]))


def reconcile(rows, total):
    for field in ("trip_count", "priced_trip_count"):
        if sum(r[field] for r in rows) != int(total[field]):
            raise ValueError(f"Source reconciliation failed: {field}")
    for field in MONEY:
        actual = sum((decimal_value(r[field]) for r in rows if r[field] is not None), Decimal(0))
        expected = decimal_value(total[field]) if total.get(field) is not None else Decimal(0)
        if actual != expected:
            raise ValueError(f"Source reconciliation failed: {field}; retry if source changed")


def digest(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


def atomic_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         suffix=".tmp", delete=False) as handle:
            temp_name = handle.name
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def extract(start, end, output, fetch=request_json):
    first, last = validate_period(start, end)
    records, control_totals = [], []
    cursor = first
    while cursor < last:
        following = date(cursor.year + (cursor.month == 12), cursor.month % 12 + 1, 1)
        where = f"trip_start_timestamp >= '{cursor}T00:00:00' AND trip_start_timestamp < '{following}T00:00:00'"
        params = {"$select": "date_trunc_ym(trip_start_timestamp) as month,payment_type," + AGGREGATES,
                  "$where": where, "$group": "month,payment_type", "$order": "month,payment_type",
                  "$limit": PAGE_SIZE}
        partition, offset = [], 0
        while True:
            page = fetch({**params, "$offset": offset})
            partition.extend(page)
            if len(page) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        partition = normalize(partition, str(cursor), str(following))
        totals = fetch({"$select": AGGREGATES, "$where": where})
        if len(totals) != 1:
            raise ValueError("Expected one source control-total row")
        reconcile(partition, totals[0])
        records.extend(partition)
        control_totals.append(totals[0])
        LOG.info("Validated month=%s rows=%s trips=%s", cursor, len(partition), totals[0]["trip_count"])
        cursor = following
    records = normalize(records, start, end)
    combined_total = {field: str(sum((decimal_value(t[field]) for t in control_totals
                                    if t.get(field) is not None), Decimal(0)))
                      for field in (*MONEY, "trip_count", "priced_trip_count")}
    reconcile(records, combined_total)
    snapshot = {"manifest": {
        "source_url": API, "dataset_id": "ajtu-isnz", "start": start, "end_exclusive": end,
        "source_time_basis": "Chicago local floating timestamps, rounded to 15 minutes",
        "grain": "calendar month x payment_type", "currency": "USD",
        "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
        "row_count": len(records), "records_sha256": digest(records),
        "reconciliation": "passed", "source_control_totals": combined_total,
    }, "records": records}
    atomic_json(output, snapshot)
    LOG.info("Validated snapshot: rows=%s trips=%s path=%s", len(records), combined_total["trip_count"], output)
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", default="data/snapshot.json")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        extract(args.start, args.end, args.output)
    except Exception as error:
        LOG.error("Extraction failed (%s); previous snapshot retained", type(error).__name__)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
