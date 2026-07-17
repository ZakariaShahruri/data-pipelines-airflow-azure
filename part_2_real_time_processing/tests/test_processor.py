import pandas as pd
import pytest

from pipeline.processor import process_data


def _validated_row(**overrides):
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
    }
    row.update(overrides)
    return row


def test_removes_duplicate_transaction_ids(make_df):
    df = make_df([_validated_row(), _validated_row()])
    out = process_data(df)
    assert len(out) == 1


def test_vat_amount_is_21_percent_of_total_spent(make_df):
    df = make_df([_validated_row(**{"Total Spent": 100.0})])
    out = process_data(df)
    assert out.iloc[0]["Vat_Amount"] == 21.0


@pytest.mark.parametrize("quantity,expected", [(9, False), (10, True)])
def test_is_bulk_order_threshold(make_df, quantity, expected):
    df = make_df([_validated_row(Quantity=quantity)])
    out = process_data(df)
    assert bool(out.iloc[0]["Is_Bulk_Order"]) == expected


@pytest.mark.parametrize("total_spent,expected", [
    (100.0, "Standard"), (100.01, "Mid-Tier"), (200.0, "Mid-Tier"), (200.01, "Premium"),
])
def test_customer_segment_tiers(make_df, total_spent, expected):
    df = make_df([_validated_row(**{"Total Spent": total_spent})])
    out = process_data(df)
    assert out.iloc[0]["Customer_Segment"] == expected


def test_estimated_delivery_is_transaction_date_plus_three_days(make_df):
    df = make_df([_validated_row(**{"Transaction Date": pd.Timestamp("2025-01-15")})])
    out = process_data(df)
    assert out.iloc[0]["Estimated_Delivery"] == pd.Timestamp("2025-01-18")


def test_order_reference_combines_customer_id_and_uppercased_location(make_df):
    df = make_df([_validated_row(**{"Customer ID": "C001", "Location": "brussels"})])
    out = process_data(df)
    assert out.iloc[0]["Order_Reference"] == "C001-BRUSSELS"
