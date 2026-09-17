"""Airflow 3 DAG. Only file paths, never dataframes, cross task boundaries."""
from datetime import timedelta
import json
import os
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen

import pendulum
from airflow.sdk import dag, task, get_current_context

ROOT = "/opt/project"
PYTHON = "/opt/pipeline-venv/bin/python"
DBT = "/opt/pipeline-venv/bin/dbt"


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


@dag(
    schedule="0 6 5 * *",  # Source may lag; re-read all configured history monthly.
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    params={"start": "2024-01-01", "end": "2026-01-01"},
    tags=["portfolio", "public-data"],
)
def open_revenue_pipeline():
    @task()
    def extract():
        context = get_current_context()
        # Parameterized replay window; current demo revalidates fixed 2024-2025 history.
        run(PYTHON, "-m", "pipeline.extract", "--start", context["params"]["start"],
            "--end", context["params"]["end"], "--output", "data/snapshot.json")

    @task()
    def load():
        run(PYTHON, "-m", "pipeline.load")  # Read-only SELECT preview.
        run(PYTHON, "-m", "pipeline.load", "--apply")

    @task()
    def build():
        run(DBT, "build", "--project-dir", ROOT + "/dbt", "--profiles-dir", ROOT + "/dbt")

    @task()
    def export():
        run(PYTHON, "-m", "pipeline.export")

    @task(retries=0)
    def emit_quality_event():
        # Optional internal n8n event. No email/Slack or other outgoing messages.
        endpoint = os.getenv("N8N_WEBHOOK_URL")
        if not endpoint:
            return "n8n disabled"
        manifest = json.loads(Path(ROOT + "/data/snapshot.json").read_text())["manifest"]
        event = {"pipeline": "open_revenue", "status": "success", "row_count": manifest["row_count"],
                 "end_exclusive": manifest["end_exclusive"], "sha256": manifest["records_sha256"]}
        request = Request(endpoint, data=json.dumps(event).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise ValueError("n8n did not acknowledge quality event")

    extract() >> load() >> build() >> export() >> emit_quality_event()


open_revenue_pipeline()
