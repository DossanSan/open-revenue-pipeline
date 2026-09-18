# Verification record

Core pipeline checked on 2026-09-17. Public dashboard deployed on 2026-09-18.

## Passed locally

- Live API extraction and independent monthly control totals for all 24 months in
  [2024-01-01, 2026-01-01): 172 aggregate rows, 13,306,188 reported trips.
- Snapshot checksum and count/amount reconciliation validated by `pipeline.summarize`.
- Nine unit tests: date boundaries, duplicates, missing months, null preservation,
  non-finite amounts, source mismatches, pagination, stable rerun hash and atomic
  preservation of the previous file on extraction failure.
- Python syntax compilation for pipeline and DAG files.
- YAML syntax parse for Compose, dbt and initial CI files; JSON parse for n8n.
- Streamlit AppTest: all three pages, total trip KPI, 2025 filter and empty selection.
- Local browser: Overview renders real KPI cards and time-series charts.

## Passed in GitHub Actions

- PostgreSQL load and idempotent rerun against PostgreSQL 16.6.
- dbt build and all configured tests against PostgreSQL.
- Export of `public/dashboard.json` and publication of the complete source tree.
- Local Streamlit AppTest repeated against the actual dbt export: passed.

Evidence: https://github.com/DossanSan/open-revenue-pipeline/actions/runs/35224315837

## Not yet verified

- Airflow runtime execution, Docker build/Compose startup and n8n workflow import.

## Public dashboard

https://dossansan-open-revenue.streamlit.app/

Deployed with Python 3.12. Verified rendered KPI cards (13,306,188 trips and
$368.56m recorded trip value), charts and payment mix page. The footer confirms
the PostgreSQL/dbt export is in use. Local AppTest also passes with that export.

Docker/PostgreSQL are unavailable in the authoring environment. The manual GitHub
workflow validated PostgreSQL/dbt using a disposable service container.
Configuration presence is not evidence of an executed full-stack pipeline.

The dashboard now reads the actual dbt export in `public/dashboard.json`. An explicitly
labelled API-preview fallback remains for extraction-only exploration. No Power BI
report was created; Streamlit is the primary delivery target.
