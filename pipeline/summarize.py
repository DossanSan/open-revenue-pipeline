"""Reproducible descriptive check of a validated API snapshot (not a dbt replacement)."""
import argparse
from collections import defaultdict
from decimal import Decimal
import json
from pathlib import Path

from pipeline.extract import digest, normalize, reconcile


def summarize(snapshot_path, output):
    snapshot = json.loads(Path(snapshot_path).read_text())
    manifest = snapshot["manifest"]
    records = normalize(snapshot["records"], manifest["start"], manifest["end_exclusive"])
    if digest(records) != manifest["records_sha256"]:
        raise ValueError("Checksum mismatch")
    reconcile(records, manifest["source_control_totals"])
    years = defaultdict(lambda: {"trips": 0, "priced": 0, "value": Decimal(0), "months": set()})
    for row in records:
        stats = years[row["month"][:4]]
        stats["trips"] += row["trip_count"]
        stats["priced"] += row["priced_trip_count"]
        stats["value"] += Decimal(row["trip_total_usd"] or "0")
        stats["months"].add(row["month"])
    lines = ["# First API findings", "", "Generated from the validated public API snapshot; these are descriptive source checks.",
             "The final dashboard must use the tested dbt mart.", "",
             f"Period: [{manifest['start']}, {manifest['end_exclusive']}).",
             f"Extracted: {manifest['extracted_at_utc']}.",
             f"Grain: {manifest['grain']}. Aggregate rows: {len(records)}.",
             f"Records SHA-256: `{manifest['records_sha256']}`.", "",
             "| Year | Months | Reported trips | Priced trips | Recorded trip value USD | Average priced trip USD | Amount coverage |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for year, stats in sorted(years.items()):
        average = stats['value'] / stats['priced'] if stats['priced'] else Decimal(0)
        coverage = Decimal(stats['priced']) / stats['trips']
        lines.append(f"| {year} | {len(stats['months'])} | {stats['trips']:,} | {stats['priced']:,} | {stats['value']:,.2f} | {average:,.2f} | {coverage:.2%} |")
    if all(year in years and len(years[year]['months']) == 12 for year in ('2024', '2025')):
        previous, current = years['2024'], years['2025']
        value_change = current['value'] / previous['value'] - 1
        trip_change = Decimal(current['trips']) / previous['trips'] - 1
        lines += ["", f"2025 vs 2024: recorded trip value {value_change:+.2%}; reported trips {trip_change:+.2%}."]
    lines += ["", "Caveats: incomplete reporting, generally unrecorded cash tips, and payment categories",
              "including Dispute/No Charge. These amounts are not settled or net revenue.",
              "Do not infer customer churn, acquisition efficiency or causes from these aggregates.", "",
              "Source: https://data.cityofchicago.org/Transportation/Taxi-Trips-2024-/ajtu-isnz", ""]
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", default="data/snapshot.json")
    parser.add_argument("--output", default="docs/first_findings.md")
    args = parser.parse_args()
    summarize(args.snapshot, args.output)
