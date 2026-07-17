import numpy as np
import pandas as pd
import pytest

from pipeline.backup_validator import backup_validator


def _processed_row(**overrides):
    row = {
        "trip_duration_minutes": 20.0,
        "average_speed_mph": 15.0,
        "revenue_per_mile": 4.0,
        "trip_distance": 5.0,
    }
    row.update(overrides)
    return row


def test_removes_infinite_values(make_df):
    df = make_df([_processed_row(average_speed_mph=np.inf), _processed_row()])
    valid, rejected = backup_validator(df)
    assert len(valid) == 1
    assert len(rejected) == 1


def test_removes_rows_over_100_mph(make_df):
    df = make_df([_processed_row(average_speed_mph=101), _processed_row(average_speed_mph=100)])
    valid, rejected = backup_validator(df)
    assert len(valid) == 1
    assert valid.iloc[0]["average_speed_mph"] == 100


def test_removes_rows_with_nonpositive_duration(make_df):
    df = make_df([_processed_row(trip_duration_minutes=0), _processed_row()])
    valid, rejected = backup_validator(df)
    assert len(valid) == 1
    assert len(rejected) == 1


def test_rejected_rows_are_persisted_to_csv(make_df, tmp_path, monkeypatch):
    from pipeline.config import Config
    monkeypatch.setattr(Config, "LOCAL_OUTPUT_DIR", str(tmp_path))

    df = make_df([_processed_row(average_speed_mph=200), _processed_row()])
    backup_validator(df)

    assert (tmp_path / "rejected_backup.csv").exists()
