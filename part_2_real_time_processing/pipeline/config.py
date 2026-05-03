import os
from pathlib import Path

_PART2_DIR = Path(__file__).resolve().parent.parent


class Config:
    INPUT_DIR = _PART2_DIR / "input_zone"
    OUTPUT_DIR = _PART2_DIR / "output_zone"
    SUPPORTED_EXTENSIONS = ('.csv', '.xlsx', '.xls')

    AZURE_CONTAINER = "inventory-output"
    AZURE_CONN_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    VALIDATION_RULES = {
        "Transaction_ID":   "Mandatory: Must be unique — duplicate IDs are dropped.",
        "Customer ID":      "Mandatory: Rows with null Customer ID are removed.",
        "Category":         "Mandatory: Standardised to Title Case; nulls → 'General'.",
        "Item":             "Non-mandatory: Nulls filled with 'Miscellaneous Item'.",
        "Price Per Unit":   "Mandatory: Coerced to positive float; unparseable → 0.0.",
        "Quantity":         "Mandatory: Coerced to integer; minimum value is 1.",
        "Total Spent":      "Mandatory: Coerced to numeric; unparseable → 0.0.",
        "Payment Method":   "Non-mandatory: Whitespace stripped; nulls → 'Other'.",
        "Location":         "Non-mandatory: Nulls filled with 'Unknown'.",
        "Transaction Date": "Mandatory: Parsed to datetime; rows with invalid dates removed.",
        "Discount Applied": "Mandatory: Normalised to boolean True/False.",
    }
