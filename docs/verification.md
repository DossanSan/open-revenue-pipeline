# Verification record

Checked on 2026-09-17.

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

## Not yet verified

- PostgreSQL load transaction and idempotent rerun against a running database.
- dbt compile/build/tests against PostgreSQL.
- Airflow runtime execution, Docker build/Compose startup and n8n workflow import.
- GitHub Actions execution and public Streamlit deployment.

Docker/PostgreSQL are unavailable in the authoring environment. The manual GitHub
workflow is prepared to validate PostgreSQL/dbt using a disposable service container.
Configuration presence is not evidence of an executed full-stack pipeline.

The dashboard currently identifies its data as an API preview. It switches to the
dbt export only when `public/dashboard.json` exists. No Power BI report was created.
