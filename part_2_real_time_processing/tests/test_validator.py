import pandas as pd
import pytest

from pipeline.validator import validate_data


def test_first_column_is_renamed_to_transaction_id(make_df):
    df = make_df([{"Unnamed: 0": "T001", "Customer ID": "C001", "Category": "Food",
                    "Item": "Bread", "Price Per Unit": 2.0, "Quantity": 1,
                    "Total Spent": 2.0, "Payment Method": "Cash", "Location": "Ghent",
                    "Transaction Date": "2025-01-01", "Discount Applied": "FALSE"}])
    out = validate_data(df)
    assert "Transaction_ID" in out.columns
    assert out.iloc[0]["Transaction_ID"] == "T001"


def test_duplicate_transaction_ids_are_dropped(make_df, row_factory):
    df = make_df([row_factory(Transaction_ID="T001"), row_factory(Transaction_ID="T001")])
    out = validate_data(df)
    assert len(out) == 1


def test_rows_missing_customer_id_are_dropped(make_df, row_factory):
    df = make_df([row_factory(**{"Customer ID": None}), row_factory(Transaction_ID="T002")])
    out = validate_data(df)
    assert len(out) == 1


def test_category_is_title_cased_and_nulls_become_general(make_df, row_factory):
    df = make_df([
        row_factory(Transaction_ID="T001", Category="ELECTRONICS"),
        row_factory(Transaction_ID="T002", Category=None),
    ])
    out = validate_data(df)
    categories = set(out["Category"])
    assert "Electronics" in categories
    assert "General" in categories


def test_item_null_filled_with_miscellaneous(make_df, row_factory):
    df = make_df([row_factory(Item=None)])
    out = validate_data(df)
    assert out.iloc[0]["Item"] == "Miscellaneous Item"


def test_price_per_unit_coerced_to_positive_float(make_df, row_factory):
    df = make_df([
        row_factory(Transaction_ID="T001", **{"Price Per Unit": -5.0}),
        row_factory(Transaction_ID="T002", **{"Price Per Unit": "not-a-number"}),
    ])
    out = validate_data(df)
    assert out[out["Transaction_ID"] == "T001"].iloc[0]["Price Per Unit"] == 5.0
    assert out[out["Transaction_ID"] == "T002"].iloc[0]["Price Per Unit"] == 0.0


def test_quantity_coerced_to_int_with_minimum_of_one(make_df, row_factory):
    df = make_df([
        row_factory(Transaction_ID="T001", Quantity="not-a-number"),
        row_factory(Transaction_ID="T002", Quantity=0),
    ])
    out = validate_data(df)
    assert out[out["Transaction_ID"] == "T001"].iloc[0]["Quantity"] == 1
    assert out[out["Transaction_ID"] == "T002"].iloc[0]["Quantity"] == 0


def test_total_spent_coerced_to_numeric(make_df, row_factory):
    df = make_df([row_factory(**{"Total Spent": "garbage"})])
    out = validate_data(df)
    assert out.iloc[0]["Total Spent"] == 0.0


def test_payment_method_stripped_and_nulls_become_other(make_df, row_factory):
    df = make_df([
        row_factory(Transaction_ID="T001", **{"Payment Method": "  Cash  "}),
        row_factory(Transaction_ID="T002", **{"Payment Method": None}),
    ])
    out = validate_data(df)
    assert out[out["Transaction_ID"] == "T001"].iloc[0]["Payment Method"] == "Cash"
    assert out[out["Transaction_ID"] == "T002"].iloc[0]["Payment Method"] == "Other"


def test_location_null_filled_with_unknown(make_df, row_factory):
    df = make_df([row_factory(Location=None)])
    out = validate_data(df)
    assert out.iloc[0]["Location"] == "Unknown"


def test_invalid_transaction_dates_are_dropped(make_df, row_factory):
    df = make_df([
        row_factory(Transaction_ID="T001", **{"Transaction Date": "2025-01-15"}),
        row_factory(Transaction_ID="T002", **{"Transaction Date": "not-a-date"}),
    ])
    out = validate_data(df)
    assert len(out) == 1
    assert out.iloc[0]["Transaction_ID"] == "T001"


@pytest.mark.parametrize("raw,expected", [
    ("TRUE", True), ("false", False), (True, True), (False, False),
])
def test_discount_applied_normalized_to_boolean(make_df, row_factory, raw, expected):
    df = make_df([row_factory(**{"Discount Applied": raw})])
    out = validate_data(df)
    assert out.iloc[0]["Discount Applied"] == expected


def test_discount_applied_defaults_to_false_when_unparseable(make_df, row_factory):
    df = make_df([row_factory(**{"Discount Applied": "maybe"})])
    out = validate_data(df)
    assert out.iloc[0]["Discount Applied"] == False
