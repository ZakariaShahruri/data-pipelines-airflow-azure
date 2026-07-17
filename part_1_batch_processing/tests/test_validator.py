import pandas as pd
import pytest

from pipeline.validator import validator


def test_missing_mandatory_column_exits(make_df, row_factory):
    df = make_df([row_factory()])
    df = df.drop(columns=["trip_distance"])
    with pytest.raises(SystemExit):
        validator(df)


def test_dropoff_before_pickup_is_rejected(make_df, row_factory):
    bad = row_factory(
        tpep_pickup_datetime=pd.Timestamp("2025-01-15 08:20:00"),
        tpep_dropoff_datetime=pd.Timestamp("2025-01-15 08:00:00"),
    )
    df = make_df([row_factory(), bad])
    valid, rejected = validator(df)
    assert len(valid) == 1
    assert len(rejected) == 1


@pytest.mark.parametrize("passenger_count,should_pass", [(0, False), (1, True), (9, True), (10, False)])
def test_passenger_count_boundaries(make_df, row_factory, passenger_count, should_pass):
    df = make_df([row_factory(passenger_count=passenger_count)])
    valid, rejected = validator(df)
    assert len(valid) == (1 if should_pass else 0)


@pytest.mark.parametrize("trip_distance,should_pass", [(0, False), (-1, False), (0.1, True)])
def test_trip_distance_must_be_positive(make_df, row_factory, trip_distance, should_pass):
    df = make_df([row_factory(trip_distance=trip_distance)])
    valid, rejected = validator(df)
    assert len(valid) == (1 if should_pass else 0)


@pytest.mark.parametrize("pu,do,should_pass", [(0, 200, False), (100, 0, False), (100, 200, True)])
def test_location_ids_must_be_positive(make_df, row_factory, pu, do, should_pass):
    df = make_df([row_factory(PULocationID=pu, DOLocationID=do)])
    valid, rejected = validator(df)
    assert len(valid) == (1 if should_pass else 0)


@pytest.mark.parametrize("payment_type,should_pass", [(1, True), (6, True), (0, False), (7, False)])
def test_payment_type_must_be_a_known_code(make_df, row_factory, payment_type, should_pass):
    df = make_df([row_factory(payment_type=payment_type)])
    valid, rejected = validator(df)
    assert len(valid) == (1 if should_pass else 0)


@pytest.mark.parametrize("fare_amount,total_amount,should_pass", [
    (0, 20.0, False), (15.0, 0, False), (15.0, 20.0, True),
])
def test_fare_and_total_must_be_positive(make_df, row_factory, fare_amount, total_amount, should_pass):
    df = make_df([row_factory(fare_amount=fare_amount, total_amount=total_amount)])
    valid, rejected = validator(df)
    assert len(valid) == (1 if should_pass else 0)


def test_missing_mandatory_field_row_is_dropped(make_df, row_factory):
    df = make_df([row_factory(), row_factory(trip_distance=None)])
    valid, rejected = validator(df)
    assert len(valid) == 1
    assert len(rejected) == 1


def test_optional_columns_negative_values_are_clamped_to_zero(make_df, row_factory):
    df = make_df([row_factory(tip_amount=-5.0, tolls_amount=-1.0)])
    valid, _ = validator(df)
    assert valid.iloc[0]["tip_amount"] == 0.0
    assert valid.iloc[0]["tolls_amount"] == 0.0


def test_optional_columns_missing_values_are_imputed_with_zero(make_df, row_factory):
    df = make_df([row_factory(extra=None)])
    valid, _ = validator(df)
    assert valid.iloc[0]["extra"] == 0.0


def test_ratecodeid_missing_is_imputed_with_99(make_df, row_factory):
    df = make_df([row_factory(RatecodeID=None)])
    valid, _ = validator(df)
    assert valid.iloc[0]["RatecodeID"] == 99


def test_rejected_rows_are_persisted_to_csv(make_df, row_factory, tmp_path, monkeypatch):
    from pipeline.config import Config
    monkeypatch.setattr(Config, "LOCAL_OUTPUT_DIR", str(tmp_path))

    bad = row_factory(trip_distance=0)
    df = make_df([row_factory(), bad])
    _, rejected = validator(df)

    out_file = tmp_path / "rejected_primary.csv"
    assert out_file.exists()
    assert len(rejected) == 1
