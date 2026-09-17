# Power BI delivery plan

Status: Power Query and DAX source prepared. A rendered PBIX/PBIP report has NOT yet
been built or validated. No report has been published to Power BI Service.

## Build in Power BI Desktop

1. Use a Windows machine (Desktop has no native macOS version).
2. Complete PostgreSQL load, `dbt build`, and `pipeline.export` first. The final
   report must read the dbt result at `exports/powerbi.json`, not bypass dbt.
   The API snapshot can be used temporarily for exploration, clearly labelled.
3. In Transform data, create a Text parameter `DataFilePath` with the local JSON
   path. Create a blank query and paste `ImportMonthlyPayments.pq` into Advanced Editor.
4. Name the query `MonthlyPayments`; apply changes. Add the measures from
   `measures.dax` one at a time. Create Calendar as a calculated table, mark it as
   the date table and set the relationship documented in that file.
5. Use Calendar month/year fields for axes and filters. Do not show daily analysis:
   the fact grain is a month, not a day. Currency is USD throughout.

## Report pages

### 1. Overview — What changed?
- Cards: Recorded Trip Value USD, Reported Trips, Average Recorded Trip Value USD,
  Amount Coverage. Use explicit USD/percent formatting.
- Monthly line: recorded trip value, with same-period previous-year comparison.
- Monthly columns: reported trips.
- Slicers: calendar year and payment type.
- Subtitle: "Chicago reported taxi trips | 2024–2025 | Public data".
- Footer: refresh timestamp, source link, coverage caveat.

### 2. Payment mix — Where did the change occur?
- Stacked monthly columns by payment type, recorded trip value.
- Matrix: payment type, trips, priced trips, trip value, average value, amount coverage.
- Show Dispute, No Charge and Unknown explicitly. Payment type is NOT a marketing channel.
- Explain that mix shifts are descriptive, not evidence of causal channel performance.

### 3. Data quality — Can the totals be trusted?
- Monthly missing-amount count and amount coverage.
- Component gap: total minus fare/tips/tolls/extras; investigate, do not force to zero.
- Source limitations, source period and extraction timestamp.
- Cash tips are generally absent. Recorded trip value is not verified cash collected,
  company net revenue, MRR, ARR, NRR, CAC or LTV.

## Publish

Power BI Service access is still required. Microsoft requires a supported work/school
account for self-service signup; a personal Gmail account alone is not sufficient.
Do not use a company tenant for a personal portfolio without the appropriate rights.

Publish the validated Import-mode report to an available workspace. For a public
portfolio link, use **Publish to web**, if permitted by the tenant administrator and
license. This exposes the model publicly; this project only uses open aggregates.
Sharing a workspace report and Publish to web are different mechanisms.

The local-file import does NOT create cloud scheduled refresh automatically. Initially
refresh in Desktop and republish. For unattended Service refresh, configure a supported
reachable source/gateway separately; do not claim this is implemented already.

Acceptance: compare all cards to `marts.monthly_overview`, test slicers, null handling,
2024 YoY blanks and 2025 YoY comparisons, then open the public link signed out.
Commit report source as PBIP when available, plus screenshots and the verified URL.

Official references:
- https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop
- https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-signup-purchase-for-power-bi
- https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-publish-to-web
