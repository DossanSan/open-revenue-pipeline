# First API findings

Generated from the validated public API snapshot; these are descriptive source checks.
The final dashboard must use the tested dbt mart.

Period: [2024-01-01, 2026-01-01).
Extracted: 2026-09-17T07:41:05.329808+00:00.
Grain: calendar month x payment_type. Aggregate rows: 172.
Records SHA-256: `ddefd25017c811ff66d3076113745f37871c381e3844dc71ac6e052a2e736bc6`.

| Year | Months | Reported trips | Priced trips | Recorded trip value USD | Average priced trip USD | Amount coverage |
| --- | --- | --- | --- | --- | --- | --- |
| 2024 | 12 | 6,480,350 | 6,462,516 | 184,242,023.96 | 28.51 | 99.72% |
| 2025 | 12 | 6,825,838 | 6,814,201 | 184,317,971.69 | 27.05 | 99.83% |

2025 vs 2024: recorded trip value +0.04%; reported trips +5.33%.

Caveats: incomplete reporting, generally unrecorded cash tips, and payment categories
including Dispute/No Charge. These amounts are not settled or net revenue.
Do not infer customer churn, acquisition efficiency or causes from these aggregates.

Source: https://data.cityofchicago.org/Transportation/Taxi-Trips-2024-/ajtu-isnz
