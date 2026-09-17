import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline.extract import extract, normalize, reconcile, validate_period


def row(month="2024-01-01", payment="Cash", trips="2", total="10.00"):
    return {"month": month, "payment_type": payment, "trip_count": trips,
            "priced_trip_count": trips, "trip_total_usd": total,
            "fare_usd": total, "tips_usd": "0", "tolls_usd": "0", "extras_usd": "0"}


class ExtractionTests(unittest.TestCase):
    def test_rejects_partial_months(self):
        with self.assertRaises(ValueError):
            validate_period("2024-01-02", "2024-02-01")

    def test_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            normalize([row(), row()], "2024-01-01", "2024-02-01")

    def test_rejects_missing_month(self):
        with self.assertRaises(ValueError):
            normalize([row()], "2024-01-01", "2024-03-01")

    def test_missing_amount_is_not_zero(self):
        source = row(trips="2")
        source["priced_trip_count"] = "0"
        source.pop("trip_total_usd")
        result = normalize([source], "2024-01-01", "2024-02-01")
        self.assertIsNone(result[0]["trip_total_usd"])

    def test_rejects_mismatched_control_totals(self):
        rows = normalize([row()], "2024-01-01", "2024-02-01")
        with self.assertRaises(ValueError):
            reconcile(rows, row(total="11"))

    def test_failed_extract_preserves_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "snapshot.json"
            path.write_text("previous snapshot")
            def fetch(params):
                return [row()] if "$group" in params else [row(total="999")]
            with self.assertRaises(ValueError):
                extract("2024-01-01", "2024-02-01", path, fetch=fetch)
            self.assertEqual(path.read_text(), "previous snapshot")

    def test_rerun_has_same_content_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "snapshot.json"
            fetch = lambda params: [row()]
            first = extract("2024-01-01", "2024-02-01", path, fetch=fetch)
            second = extract("2024-01-01", "2024-02-01", path, fetch=fetch)
            self.assertEqual(first["manifest"]["records_sha256"], second["manifest"]["records_sha256"])
            self.assertEqual(json.loads(path.read_text())["records"], first["records"])

    def test_pagination_keeps_every_group_once(self):
        pages = [row(), row(payment="Credit Card")]
        offsets = []
        def fetch(params):
            if "$group" not in params:
                return [row(trips="4", total="20.00")]
            offsets.append(params["$offset"])
            offset = params["$offset"]
            return pages[offset:offset + 1]
        with tempfile.TemporaryDirectory() as folder, patch("pipeline.extract.PAGE_SIZE", 1):
            result = extract("2024-01-01", "2024-02-01", Path(folder)/"snapshot.json", fetch=fetch)
        self.assertEqual(offsets, [0, 1, 2])
        self.assertEqual(len(result["records"]), 2)

    def test_nonfinite_amount_rejected(self):
        with self.assertRaises(ValueError):
            normalize([row(total="NaN")], "2024-01-01", "2024-02-01")


if __name__ == "__main__":
    unittest.main()
