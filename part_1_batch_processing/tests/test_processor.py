import pandas as pd
import pytest

from pipeline.processor import processor


def test_removes_unwanted_columns(make_df, row_factory):
    df = make_df([row_factory()])
    out = processor(df)
    assert not {"VendorID", "store_and_fwd_flag", "RatecodeID"} & set(out.columns)


def test_computes_trip_duration_minutes(make_df, row_factory):
    df = make_df([row_factory(
        tpep_pickup_datetime=pd.Timestamp("2025-01-15 08:00:00"),
        tpep_dropoff_datetime=pd.Timestamp("2025-01-15 08:20:00"),
    )])
    out = processor(df)
    assert out.iloc[0]["trip_duration_minutes"] == 20.0


def test_average_speed_computed_from_distance_and_duration(make_df, row_factory):
    df = make_df([row_factory(
        trip_distance=10.0,
        tpep_pickup_datetime=pd.Timestamp("2025-01-15 08:00:00"),
        tpep_dropoff_datetime=pd.Timestamp("2025-01-15 08:30:00"),
    )])
    out = processor(df)
    assert out.iloc[0]["average_speed_mph"] == pytest.approx(20.0)


def test_average_speed_is_zero_when_duration_is_zero(make_df, row_factory):
    same = pd.Timestamp("2025-01-15 08:00:00")
    df = make_df([row_factory(tpep_pickup_datetime=same, tpep_dropoff_datetime=same)])
    out = processor(df)
    assert out.iloc[0]["average_speed_mph"] == 0
    assert out.iloc[0]["trip_duration_minutes"] == 0


def test_revenue_per_mile_computed(make_df, row_factory):
    df = make_df([row_factory(trip_distance=5.0, total_amount=20.0)])
    out = processor(df)
    assert out.iloc[0]["revenue_per_mile"] == pytest.approx(4.0)


def test_pickup_year_and_month_extracted(make_df, row_factory):
    df = make_df([row_factory(tpep_pickup_datetime=pd.Timestamp("2025-03-10 08:00:00"))])
    out = processor(df)
    assert out.iloc[0]["pickup_year"] == 2025
    assert out.iloc[0]["pickup_month"] == 3


@pytest.mark.parametrize("distance,expected", [
    (1.99, "Short"), (2.0, "Medium"), (10.0, "Medium"), (10.01, "Long"),
])
def test_trip_distance_category_boundaries(make_df, row_factory, distance, expected):
    df = make_df([row_factory(trip_distance=distance)])
    out = processor(df)
    assert out.iloc[0]["trip_distance_category"] == expected


@pytest.mark.parametrize("fare,expected", [
    (19.99, "Low"), (20.0, "Medium"), (50.0, "Medium"), (50.01, "High"),
])
def test_fare_category_boundaries(make_df, row_factory, fare, expected):
    df = make_df([row_factory(fare_amount=fare)])
    out = processor(df)
    assert out.iloc[0]["fare_category"] == expected


@pytest.mark.parametrize("hour,expected", [
    (0, "Night"), (5, "Night"), (6, "Night"),
    (7, "Morning"), (12, "Morning"),
    (13, "Afternoon"), (18, "Afternoon"),
    (19, "Evening"), (23, "Evening"),
])
def test_trip_time_of_day_buckets(make_df, row_factory, hour, expected):
    pickup = pd.Timestamp("2025-01-15") + pd.Timedelta(hours=hour)
    df = make_df([row_factory(tpep_pickup_datetime=pickup)])
    out = processor(df)
    assert out.iloc[0]["trip_time_of_day"] == expected
