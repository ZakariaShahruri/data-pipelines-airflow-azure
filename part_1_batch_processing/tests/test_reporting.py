import pandas as pd
import pytest

from pipeline.reporting import compute_metrics, generate_report, render_html


def _gold_row(**overrides):
    row = {
        "total_amount": 20.0,
        "fare_amount": 15.0,
        "trip_distance": 5.0,
        "trip_duration_minutes": 20.0,
        "average_speed_mph": 15.0,
        "trip_distance_category": "Medium",
        "fare_category": "Low",
        "trip_time_of_day": "Morning",
        "PULocationID": 100,
    }
    row.update(overrides)
    return row


def test_compute_metrics_totals(make_df):
    df = make_df([_gold_row(), _gold_row(total_amount=30.0, fare_amount=25.0)])
    metrics = compute_metrics(df)
    assert metrics["total_trips"] == 2
    assert metrics["total_revenue"] == 50.0
    assert metrics["avg_fare"] == 20.0


def test_compute_metrics_revenue_by_distance_category(make_df):
    df = make_df([
        _gold_row(trip_distance_category="Short", total_amount=10.0),
        _gold_row(trip_distance_category="Medium", total_amount=20.0),
        _gold_row(trip_distance_category="Long", total_amount=30.0),
    ])
    metrics = compute_metrics(df)
    assert metrics["revenue_by_distance_category"] == {"Short": 10.0, "Medium": 20.0, "Long": 30.0}


def test_compute_metrics_trip_count_by_time_of_day(make_df):
    df = make_df([
        _gold_row(trip_time_of_day="Night"),
        _gold_row(trip_time_of_day="Night"),
        _gold_row(trip_time_of_day="Evening"),
    ])
    metrics = compute_metrics(df)
    assert metrics["trip_count_by_time_of_day"] == {"Night": 2, "Morning": 0, "Afternoon": 0, "Evening": 1}


def test_compute_metrics_top_pickup_locations(make_df):
    df = make_df([
        _gold_row(PULocationID=100), _gold_row(PULocationID=100), _gold_row(PULocationID=200),
    ])
    metrics = compute_metrics(df)
    assert metrics["top_pickup_locations"] == {100: 2, 200: 1}


def test_compute_metrics_handles_empty_dataframe(make_df):
    df = pd.DataFrame({
        "total_amount": pd.Series(dtype=float),
        "fare_amount": pd.Series(dtype=float),
        "trip_distance": pd.Series(dtype=float),
        "trip_duration_minutes": pd.Series(dtype=float),
        "average_speed_mph": pd.Series(dtype=float),
        "trip_distance_category": pd.Series(dtype=object),
        "fare_category": pd.Series(dtype=object),
        "trip_time_of_day": pd.Series(dtype=object),
        "PULocationID": pd.Series(dtype=int),
    })
    metrics = compute_metrics(df)
    assert metrics["total_trips"] == 0
    assert metrics["avg_fare"] == 0.0
    assert metrics["top_pickup_locations"] == {}


def test_render_html_includes_key_metrics(make_df):
    df = make_df([_gold_row()])
    html = render_html(compute_metrics(df))
    assert "<html>" in html
    assert "Total Trips" in html
    assert "Zone 100" in html


def test_generate_report_writes_file(make_df, tmp_path):
    df = make_df([_gold_row()])
    output_path = generate_report(df, tmp_path / "report.html")
    assert output_path.exists()
    assert "Total Trips" in output_path.read_text(encoding="utf-8")
