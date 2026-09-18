# Streamlit dashboard

Live report: https://dossansan-open-revenue.streamlit.app/

Primary report destination, replacing Power BI for a Mac-friendly, license-free demo.
Streamlit Community Cloud offers free app hosting linked to GitHub:
https://docs.streamlit.io/deploy/streamlit-community-cloud

Run from the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r dashboard/requirements.txt
.venv/bin/python -m streamlit run dashboard/app.py
```

The app reads `public/dashboard.json` (dbt export) when present. Otherwise it displays
`public/api_snapshot.json` and explicitly labels it an API preview. No API calls or
database credentials are required for a viewer. All included data is public and aggregated.

For the final pipeline output, after the successful dbt build:

```bash
python -m pipeline.export --output public/dashboard.json
```

Commit only the reviewed public aggregate export, never database credentials. The
GitHub refresh workflow can rebuild this export using an ephemeral PostgreSQL service.
Airflow/n8n run locally; the free dashboard host does not run those services.

Deployment: connect the public GitHub repo in Streamlit Community Cloud, choose
`dashboard/app.py`, Python 3.12 and deploy. The requirements file next to the entrypoint
contains dashboard-only dependencies. No paid account is required by Community Cloud;
service quotas and sleep behaviour still apply. Account setup/authorization may require
the owner to complete a browser step.

Validate three pages, year/payment filters and empty selections. Verify KPI totals
against the exported mart, then check the public URL in a signed-out browser.
