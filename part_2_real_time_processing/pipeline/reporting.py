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

CUSTOMER_SEGMENTS = ["Premium", "Mid-Tier", "Standard"]


def compute_metrics(df: pd.DataFrame) -> dict:
    """Aggregate the gold dataset into the KPIs a store manager would ask for."""
    total_transactions = len(df)

    revenue_by_segment = {
        seg: round(df.loc[df["Customer_Segment"] == seg, "Total Spent"].sum(), 2)
        for seg in CUSTOMER_SEGMENTS
    }

    revenue_by_category = (
        df.groupby("Category")["Total Spent"].sum().sort_values(ascending=False).head(5).round(2).to_dict()
        if total_transactions else {}
    )

    revenue_by_payment_method = (
        df.groupby("Payment Method")["Total Spent"].sum().round(2).to_dict()
        if total_transactions else {}
    )

    return {
        "total_transactions": total_transactions,
        "total_revenue": round(df["Total Spent"].sum(), 2),
        "total_vat_collected": round(df["Vat_Amount"].sum(), 2),
        "avg_order_value": round(df["Total Spent"].mean(), 2) if total_transactions else 0.0,
        "bulk_order_pct": round(df["Is_Bulk_Order"].mean() * 100, 1) if total_transactions else 0.0,
        "discount_usage_pct": round(df["Discount Applied"].mean() * 100, 1) if total_transactions else 0.0,
        "revenue_by_segment": revenue_by_segment,
        "revenue_by_category": revenue_by_category,
        "revenue_by_payment_method": revenue_by_payment_method,
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
<html><head><meta charset="utf-8"><title>Retail Inventory — Gold Data Report</title>
<style>
  body {{ font-family: -apple-system, Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }}
  h1 {{ font-size: 1.5rem; }}
  h2 {{ font-size: 1.1rem; margin-top: 2rem; color: #94a3b8; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin: 1rem 0; }}
  .kpi {{ background: #1e293b; border-radius: 8px; padding: 1rem; }}
  .kpi .value {{ font-size: 1.6rem; font-weight: 700; color: #34d399; }}
  .kpi .label {{ font-size: 0.8rem; color: #94a3b8; }}
  .bar-row {{ display: flex; align-items: center; gap: 0.75rem; margin: 0.4rem 0; }}
  .bar-label {{ width: 110px; font-size: 0.85rem; color: #cbd5e1; }}
  .bar-track {{ flex: 1; background: #1e293b; border-radius: 4px; height: 14px; }}
  .bar-fill {{ background: #34d399; height: 100%; border-radius: 4px; }}
  .bar-value {{ width: 90px; text-align: right; font-size: 0.85rem; color: #cbd5e1; }}
  .empty {{ color: #64748b; font-style: italic; }}
</style></head>
<body>
  <h1>Retail Inventory — Gold Data Report</h1>
  <div class="kpi-grid">
    <div class="kpi"><div class="value">{metrics['total_transactions']:,}</div><div class="label">Total Transactions</div></div>
    <div class="kpi"><div class="value">${metrics['total_revenue']:,.2f}</div><div class="label">Total Revenue</div></div>
    <div class="kpi"><div class="value">${metrics['total_vat_collected']:,.2f}</div><div class="label">VAT Collected</div></div>
    <div class="kpi"><div class="value">${metrics['avg_order_value']:,.2f}</div><div class="label">Avg Order Value</div></div>
    <div class="kpi"><div class="value">{metrics['bulk_order_pct']}%</div><div class="label">Bulk Orders</div></div>
    <div class="kpi"><div class="value">{metrics['discount_usage_pct']}%</div><div class="label">Discount Usage</div></div>
  </div>

  <h2>Revenue by Customer Segment</h2>
  {_bar_rows(metrics['revenue_by_segment'], currency=True)}

  <h2>Top 5 Categories by Revenue</h2>
  {_bar_rows(metrics['revenue_by_category'], currency=True)}

  <h2>Revenue by Payment Method</h2>
  {_bar_rows(metrics['revenue_by_payment_method'], currency=True)}
</body></html>
"""


def generate_report(df: pd.DataFrame, output_path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metrics = compute_metrics(df)
    output_path.write_text(render_html(metrics), encoding="utf-8")

    logging.info("--- REPORTING START: Generating Business KPIs ---")
    logging.info(f"Report written to {output_path}")
    return output_path
