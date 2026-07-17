"""
STAGE 6: REPORTING
Consumes the validated, feature-engineered "gold" dataset and turns it into
business-facing KPIs — this is the reason the pipeline's cleaning and
feature-engineering stages exist, rather than an end in themselves.
"""
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

DISTANCE_CATEGORIES = ["Short", "Medium", "Long"]
FARE_CATEGORIES = ["Low", "Medium", "High"]
TIME_OF_DAY_BUCKETS = ["Night", "Morning", "Afternoon", "Evening"]


def compute_metrics(df: pd.DataFrame) -> dict:
    """Aggregate the gold dataset into the KPIs a dispatcher/analyst would ask for."""
    total_trips = len(df)

    revenue_by_distance_category = {
        cat: round(df.loc[df["trip_distance_category"] == cat, "total_amount"].sum(), 2)
        for cat in DISTANCE_CATEGORIES
    }
    revenue_by_fare_category = {
        cat: round(df.loc[df["fare_category"] == cat, "total_amount"].sum(), 2)
        for cat in FARE_CATEGORIES
    }
    trip_count_by_time_of_day = {
        bucket: int((df["trip_time_of_day"] == bucket).sum())
        for bucket in TIME_OF_DAY_BUCKETS
    }

    top_pickup_locations = (
        df["PULocationID"].value_counts().head(5).to_dict()
    )

    return {
        "total_trips": total_trips,
        "total_revenue": round(df["total_amount"].sum(), 2),
        "avg_fare": round(df["fare_amount"].mean(), 2) if total_trips else 0.0,
        "avg_trip_distance": round(df["trip_distance"].mean(), 2) if total_trips else 0.0,
        "avg_trip_duration_minutes": round(df["trip_duration_minutes"].mean(), 2) if total_trips else 0.0,
        "avg_speed_mph": round(df["average_speed_mph"].mean(), 2) if total_trips else 0.0,
        "revenue_by_distance_category": revenue_by_distance_category,
        "revenue_by_fare_category": revenue_by_fare_category,
        "trip_count_by_time_of_day": trip_count_by_time_of_day,
        "top_pickup_locations": {int(k): int(v) for k, v in top_pickup_locations.items()},
    }


def _bar_rows(data: dict, currency: bool = False) -> str:
    if not data or max(data.values()) == 0:
        return "<p class='empty'>No data</p>"
    max_value = max(data.values())
    rows = []
    for label, value in data.items():
        pct = (value / max_value * 100) if max_value else 0
        formatted = f"${value:,.2f}" if currency else f"{value:,}"
        rows.append(f"""
        <div class="bar-row">
          <span class="bar-label">{label}</span>
          <div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%"></div></div>
          <span class="bar-value">{formatted}</span>
        </div>""")
    return "".join(rows)


def render_html(metrics: dict) -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>NYC Taxi — Gold Data Report</title>
<style>
  body {{ font-family: -apple-system, Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }}
  h1 {{ font-size: 1.5rem; }}
  h2 {{ font-size: 1.1rem; margin-top: 2rem; color: #94a3b8; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin: 1rem 0; }}
  .kpi {{ background: #1e293b; border-radius: 8px; padding: 1rem; }}
  .kpi .value {{ font-size: 1.6rem; font-weight: 700; color: #38bdf8; }}
  .kpi .label {{ font-size: 0.8rem; color: #94a3b8; }}
  .bar-row {{ display: flex; align-items: center; gap: 0.75rem; margin: 0.4rem 0; }}
  .bar-label {{ width: 90px; font-size: 0.85rem; color: #cbd5e1; }}
  .bar-track {{ flex: 1; background: #1e293b; border-radius: 4px; height: 14px; }}
  .bar-fill {{ background: #38bdf8; height: 100%; border-radius: 4px; }}
  .bar-value {{ width: 90px; text-align: right; font-size: 0.85rem; color: #cbd5e1; }}
  .empty {{ color: #64748b; font-style: italic; }}
</style></head>
<body>
  <h1>NYC Yellow Taxi — Gold Data Report</h1>
  <div class="kpi-grid">
    <div class="kpi"><div class="value">{metrics['total_trips']:,}</div><div class="label">Total Trips</div></div>
    <div class="kpi"><div class="value">${metrics['total_revenue']:,.2f}</div><div class="label">Total Revenue</div></div>
    <div class="kpi"><div class="value">${metrics['avg_fare']:,.2f}</div><div class="label">Avg Fare</div></div>
    <div class="kpi"><div class="value">{metrics['avg_trip_distance']} mi</div><div class="label">Avg Trip Distance</div></div>
    <div class="kpi"><div class="value">{metrics['avg_trip_duration_minutes']} min</div><div class="label">Avg Duration</div></div>
    <div class="kpi"><div class="value">{metrics['avg_speed_mph']} mph</div><div class="label">Avg Speed</div></div>
  </div>

  <h2>Revenue by Trip Distance Category</h2>
  {_bar_rows(metrics['revenue_by_distance_category'], currency=True)}

  <h2>Revenue by Fare Category</h2>
  {_bar_rows(metrics['revenue_by_fare_category'], currency=True)}

  <h2>Trip Volume by Time of Day</h2>
  {_bar_rows(metrics['trip_count_by_time_of_day'])}

  <h2>Top 5 Pickup Locations (by trip count)</h2>
  {_bar_rows({f"Zone {k}": v for k, v in metrics['top_pickup_locations'].items()})}
</body></html>
"""


def generate_report(df: pd.DataFrame, output_path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metrics = compute_metrics(df)
    output_path.write_text(render_html(metrics), encoding="utf-8")

    logging.info(f"\n{'='*50}\nSTAGE: REPORTING\n{'='*50}")
    logging.info(f"Report written to {output_path}")
    return output_path
