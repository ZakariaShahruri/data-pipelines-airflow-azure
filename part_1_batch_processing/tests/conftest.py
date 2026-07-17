import sys
from pathlib import Path

import pandas as pd
import pytest

PART_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PART_DIR))


def make_row(**overrides) -> dict:
    """A single valid, in-spec taxi trip row. Override fields per test."""
    row = {
        "VendorID": 1,
        "tpep_pickup_datetime": pd.Timestamp("2025-01-15 08:00:00"),
        "tpep_dropoff_datetime": pd.Timestamp("2025-01-15 08:20:00"),
        "passenger_count": 1,
        "trip_distance": 5.0,
        "RatecodeID": 1,
        "store_and_fwd_flag": "N",
        "PULocationID": 100,
        "DOLocationID": 200,
        "payment_type": 1,
        "fare_amount": 15.0,
        "tip_amount": 2.0,
        "tolls_amount": 0.0,
        "extra": 0.5,
        "airport_fee": 0.0,
        "congestion_surcharge": 2.5,
        "cbd_congestion_fee": 0.0,
        "total_amount": 20.0,
    }
    row.update(overrides)
    return row


@pytest.fixture
def make_df():
    def _make_df(rows):
        return pd.DataFrame(rows)
    return _make_df


@pytest.fixture
def row_factory():
    return make_row
