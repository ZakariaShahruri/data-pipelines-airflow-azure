import sys
from pathlib import Path

import pandas as pd
import pytest

PART_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PART_DIR))


def make_row(**overrides) -> dict:
    """A single valid, in-spec inventory transaction row (post-rename column names)."""
    row = {
        "Transaction_ID": "T001",
        "Customer ID": "C001",
        "Category": "electronics",
        "Item": "Laptop",
        "Price Per Unit": 500.0,
        "Quantity": 2,
        "Total Spent": 1000.0,
        "Payment Method": "Credit Card",
        "Location": "Brussels",
        "Transaction Date": "2025-01-15",
        "Discount Applied": "TRUE",
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
