import numpy as np
import pandas as pd
import pytest

from pipeline.backup_validator import backup_validate


def _processed_row(**overrides):
    row = {
        "Transaction_ID": "T001",
        "Customer ID": "C001",
        "Category": "Electronics",
        "Item": "Laptop",
        "Price Per Unit": 500.0,
        "Quantity": 2,
        "Total Spent": 1000.0,
        "Payment Method": "Credit Card",
        "Location": "Brussels",
        "Transaction Date": pd.Timestamp("2025-01-15"),
        "Discount Applied": True,
        "Vat_Amount": 210.0,
        "Is_Bulk_Order": False,
        "Customer_Segment": "Premium",
        "Estimated_Delivery": pd.Timestamp("2025-01-18"),
        "Order_Reference": "C001-BRUSSELS",
    }
    row.update(overrides)
    return row


def test_fills_nulls_in_engineered_columns(make_df):
    df = make_df([_processed_row(Customer_Segment=None)])
    out = backup_validate(df)
    assert out.iloc[0]["Customer_Segment"] == "Unknown"


def test_negative_vat_is_corrected_to_zero(make_df):
    df = make_df([_processed_row(Vat_Amount=-10.0)])
    out = backup_validate(df)
    assert out.iloc[0]["Vat_Amount"] == 0


def test_valid_row_passes_through_unchanged(make_df):
    df = make_df([_processed_row()])
    out = backup_validate(df)
    assert len(out) == 1
    assert out.iloc[0]["Vat_Amount"] == 210.0
