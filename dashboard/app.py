"""Streamlit portfolio dashboard, real Chicago API aggregates only."""
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
st.set_page_config(page_title="Chicago | Open Revenue", page_icon="🚕", layout="wide")


@st.cache_data
def read_data(path, modified):
    payload = json.loads(Path(path).read_text())
    frame = pd.DataFrame(payload["records"])
    frame["month"] = pd.to_datetime(frame["month"])
    for column in ("trip_count", "priced_trip_count", "trip_total_usd", "fare_usd", "tips_usd", "tolls_usd", "extras_usd"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["year"] = frame["month"].dt.year
    frame["missing_amount_trips"] = frame["trip_count"] - frame["priced_trip_count"]
    return frame, payload["manifest"]


def kpis(frame):
    trips = int(frame["trip_count"].sum())
    priced = int(frame["priced_trip_count"].sum())
    value = frame["trip_total_usd"].sum(min_count=1)
    return trips, priced, value, value / priced if priced else None


source = ROOT / "public" / "dashboard.json"
is_mart = source.exists()
if not is_mart:
    source = ROOT / "public" / "api_snapshot.json"
if not source.exists():
    st.error("No validated dataset available. Run the extraction pipeline first.")
    st.stop()
data, manifest = read_data(str(source), source.stat().st_mtime_ns)

with st.sidebar:
    st.caption("OPEN DATA · REVENUE ANALYTICS")
    st.title("Chicago")
    st.write("Taxi economy, in focus.")
    page = st.radio("Explore", ["Overview", "Payment mix", "Data quality"], label_visibility="collapsed")
    years = st.multiselect("Calendar year", sorted(data["year"].unique()), default=sorted(data["year"].unique()))
    payments = st.multiselect("Payment type", sorted(data["payment_type"].unique()), default=sorted(data["payment_type"].unique()))
    st.divider()
    st.caption("MONTHLY DATA · USD")
    st.caption("Real public data from the City of Chicago. No customer or individual trip records are stored.")
    st.link_button("Explore the source ↗", "https://data.cityofchicago.org/Transportation/Taxi-Trips-2024-/ajtu-isnz")

filtered = data[data["year"].isin(years) & data["payment_type"].isin(payments)]
st.caption("THE OPEN REVENUE PROJECT / CHICAGO TAXIS")
st.title({"Overview": "More trips. A different mix.", "Payment mix": "How payment patterns changed.", "Data quality": "Trust starts with the source."}[page])
st.write("Explore recorded trip value, volume and payment patterns across 2024–2025.")
if filtered.empty:
    st.info("Choose at least one year and one available payment type to explore the data.")
    st.stop()

trips, priced, value, average = kpis(filtered)
columns = st.columns(4)
columns[0].metric("Recorded trip value", f"${value / 1_000_000:,.2f}m")
columns[1].metric("Reported trips", f"{trips:,}")
columns[2].metric("Avg. priced trip", f"${average:,.2f}" if average is not None else "—")
columns[3].metric("Amount coverage", f"{priced / trips:.2%}" if trips else "—")
st.caption("Trip value includes recorded fare, tips and charges; it is not verified collected or net revenue.")
st.divider()

monthly = filtered.groupby("month", as_index=False).agg(
    trip_total_usd=("trip_total_usd", "sum"), trip_count=("trip_count", "sum"),
    priced_trip_count=("priced_trip_count", "sum"), missing_amount_trips=("missing_amount_trips", "sum"))
monthly["average_value"] = monthly["trip_total_usd"] / monthly["priced_trip_count"].replace(0, float("nan"))
monthly["coverage"] = monthly["priced_trip_count"] / monthly["trip_count"]
monthly["year"] = monthly["month"].dt.year.astype(str)
palette = ["#d65a31", "#23766b", "#ba9536", "#486985", "#9683a1", "#777567", "#b07669", "#526342"]

if page == "Overview":
    st.subheader("The value of reported trips")
    chart = alt.Chart(monthly).mark_line(point=True, color=palette[0], strokeWidth=3).encode(
        x=alt.X("month:T", title=None, axis=alt.Axis(format="%b %Y")),
        y=alt.Y("trip_total_usd:Q", title="Recorded trip value · USD", axis=alt.Axis(format="$~s")),
        tooltip=[alt.Tooltip("month:T", title="Month", format="%b %Y"), alt.Tooltip("trip_total_usd:Q", title="USD", format=",.2f")])
    st.altair_chart(chart.properties(height=300), use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.subheader("Reported volume")
        st.altair_chart(alt.Chart(monthly).mark_bar(color=palette[1], cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X("month:T", title=None), y=alt.Y("trip_count:Q", title="Trips", axis=alt.Axis(format="~s")),
            tooltip=["month:T", alt.Tooltip("trip_count:Q", format=",")]).properties(height=220), use_container_width=True)
    with right:
        st.subheader("Average priced trip")
        st.altair_chart(alt.Chart(monthly).mark_line(point=True, color=palette[2]).encode(
            x=alt.X("month:T", title=None), y=alt.Y("average_value:Q", title="USD per priced trip", scale=alt.Scale(zero=False)),
            tooltip=["month:T", alt.Tooltip("average_value:Q", format=".2f")]).properties(height=220), use_container_width=True)
    st.subheader("Read the change carefully")
    if set(years) == {2024, 2025}:
        prior, current = (kpis(filtered[filtered["year"] == year]) for year in (2024, 2025))
        if prior[0] and prior[2] and prior[3] and current[3]:
            st.info(f"For the selected payment types, 2025 trip value changed by {current[2]/prior[2]-1:+.2%}, "
                    f"reported trips by {current[0]/prior[0]-1:+.2%}, and average priced-trip value by {current[3]/prior[3]-1:+.2%}. "
                    "This is a descriptive comparison, not proof of a pricing or customer-behaviour effect.")
    else:
        st.caption("Select both years for a full-year comparison.")

elif page == "Payment mix":
    st.subheader("Recorded value by payment type")
    st.altair_chart(alt.Chart(filtered).mark_bar().encode(
        x=alt.X("month:T", title=None), y=alt.Y("trip_total_usd:Q", title="USD", axis=alt.Axis(format="$~s")),
        color=alt.Color("payment_type:N", title="Payment type", scale=alt.Scale(range=palette)),
        tooltip=["month:T", "payment_type:N", alt.Tooltip("trip_total_usd:Q", format=",.2f")]
    ).properties(height=350), use_container_width=True)
    mix = filtered.groupby("payment_type", as_index=False)[["trip_count", "priced_trip_count", "trip_total_usd"]].sum()
    mix["average_value_usd"] = mix["trip_total_usd"] / mix["priced_trip_count"].replace(0, float("nan"))
    st.dataframe(mix.sort_values("trip_total_usd", ascending=False), hide_index=True, use_container_width=True)
    st.caption("Dispute, No Charge and Unknown remain visible. A payment type is not a marketing channel.")

else:
    left, right = st.columns(2)
    with left:
        st.subheader("Trips without recorded totals")
        st.altair_chart(alt.Chart(monthly).mark_bar(color=palette[0]).encode(
            x=alt.X("month:T", title=None), y=alt.Y("missing_amount_trips:Q", title="Trips"),
            tooltip=["month:T", "missing_amount_trips:Q"]
        ).properties(height=260), use_container_width=True)
    with right:
        st.subheader("Amount coverage")
        st.altair_chart(alt.Chart(monthly).mark_line(point=True, color=palette[1]).encode(
            x=alt.X("month:T", title=None), y=alt.Y("coverage:Q", title="Share of reported trips", axis=alt.Axis(format=".1%"), scale=alt.Scale(domain=[0, 1])),
            tooltip=["month:T", alt.Tooltip("coverage:Q", format=".2%")]
        ).properties(height=260), use_container_width=True)
    st.markdown("""
- **Reporting coverage:** the City says not all trips are reported. Amount coverage here only measures missing totals among reported trips.
- **Cash tips:** generally not recorded, so recorded tip rates are not comparable across payment types.
- **Time:** source-local timestamps are rounded to 15 minutes; this report uses whole calendar months.
- **Accounting:** recorded trip value is not settled revenue or profit. Disputes and no-charge categories are retained.
- **Scope:** no customer-level churn, CAC, LTV or SaaS retention metrics can be inferred.
""")
    st.subheader("Inspect the aggregates")
    st.dataframe(filtered.drop(columns="year"), hide_index=True, use_container_width=True)

st.divider()
stamp = manifest.get("extracted_at_utc") or manifest.get("exported_at_utc", "Unknown")
st.caption(f"Source: City of Chicago · Snapshot: {stamp} · Grain: month × payment type · USD")
if is_mart:
    st.caption("Data path: public API → PostgreSQL → dbt → dashboard export.")
else:
    st.caption("API preview: independently reconciled source snapshot. PostgreSQL/dbt integration has not yet supplied this app's dataset.")
