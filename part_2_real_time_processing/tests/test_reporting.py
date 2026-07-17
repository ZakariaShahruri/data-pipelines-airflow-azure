import pandas as pd
import pytest

from pipeline.reporting import compute_metrics, generate_report, render_html


def _gold_row(**overrides):
    row = {
        "Total Spent": 100.0,
        "Vat_Amount": 21.0,
        "Is_Bulk_Order": False,
        "Discount Applied": False,
        "Customer_Segment": "Standard",
        "Category": "Electronics",
        "Payment Method": "Credit Card",
    }
    row.update(overrides)
    return row


def test_compute_metrics_totals(make_df):
    df = make_df([_gold_row(), _gold_row(**{"Total Spent": 200.0})])
    metrics = compute_metrics(df)
    assert metrics["total_transactions"] == 2
    assert metrics["total_revenue"] == 300.0
    assert metrics["avg_order_value"] == 150.0


def test_compute_metrics_vat_collected(make_df):
    df = make_df([_gold_row(Vat_Amount=10.0), _gold_row(Vat_Amount=15.0)])
    metrics = compute_metrics(df)
    assert metrics["total_vat_collected"] == 25.0


def test_compute_metrics_bulk_and_discount_percentages(make_df):
    df = make_df([
        _gold_row(**{"Is_Bulk_Order": True, "Discount Applied": True}),
        _gold_row(**{"Is_Bulk_Order": False, "Discount Applied": False}),
    ])
    metrics = compute_metrics(df)
    assert metrics["bulk_order_pct"] == 50.0
    assert metrics["discount_usage_pct"] == 50.0


def test_compute_metrics_revenue_by_segment(make_df):
    df = make_df([
        _gold_row(Customer_Segment="Premium", **{"Total Spent": 300.0}),
        _gold_row(Customer_Segment="Standard", **{"Total Spent": 50.0}),
    ])
    metrics = compute_metrics(df)
    assert metrics["revenue_by_segment"] == {"Premium": 300.0, "Mid-Tier": 0.0, "Standard": 50.0}


def test_compute_metrics_revenue_by_category(make_df):
    df = make_df([
        _gold_row(Category="Food", **{"Total Spent": 40.0}),
        _gold_row(Category="Food", **{"Total Spent": 10.0}),
        _gold_row(Category="Electronics", **{"Total Spent": 500.0}),
    ])
    metrics = compute_metrics(df)
    assert metrics["revenue_by_category"]["Electronics"] == 500.0
    assert metrics["revenue_by_category"]["Food"] == 50.0


def test_compute_metrics_handles_empty_dataframe():
    df = pd.DataFrame({
        "Total Spent": pd.Series(dtype=float),
        "Vat_Amount": pd.Series(dtype=float),
        "Is_Bulk_Order": pd.Series(dtype=bool),
        "Discount Applied": pd.Series(dtype=bool),
        "Customer_Segment": pd.Series(dtype=object),
        "Category": pd.Series(dtype=object),
        "Payment Method": pd.Series(dtype=object),
    })
    metrics = compute_metrics(df)
    assert metrics["total_transactions"] == 0
    assert metrics["avg_order_value"] == 0.0
    assert metrics["revenue_by_category"] == {}


def test_render_html_includes_key_metrics(make_df):
    df = make_df([_gold_row()])
    html = render_html(compute_metrics(df))
    assert "<html>" in html
    assert "Total Transactions" in html


def test_generate_report_writes_file(make_df, tmp_path):
    df = make_df([_gold_row()])
    output_path = generate_report(df, tmp_path / "report.html")
    assert output_path.exists()
    assert "Total Transactions" in output_path.read_text(encoding="utf-8")
