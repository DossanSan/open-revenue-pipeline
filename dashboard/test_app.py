"""Run after installing dashboard/requirements.txt: python dashboard/test_app.py."""
from pathlib import Path
import json
from streamlit.testing.v1 import AppTest

app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=30).run()
root = Path(__file__).resolve().parents[1]
source = root / "public/dashboard.json"
if not source.exists():
    source = root / "public/api_snapshot.json"
rows = json.loads(source.read_text())["records"]
assert not app.exception, app.exception
assert len(app.metric) == 4
assert app.metric[1].value == f"{sum(row['trip_count'] for row in rows):,}"
for page in ("Payment mix", "Data quality", "Overview"):
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception, app.exception
app.sidebar.multiselect[0].set_value([2025]).run()
assert not app.exception, app.exception
assert app.metric[1].value == f"{sum(row['trip_count'] for row in rows if row['month'].startswith('2025')):,}"
app.sidebar.multiselect[1].set_value([]).run()
assert not app.exception, app.exception
assert len(app.info) > 0
print("Dashboard checks passed: three pages, totals, year filter and empty selection")
