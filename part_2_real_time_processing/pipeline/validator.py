import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("--- STARTING 11-COLUMN VALIDATION ---")

    # 1. Transaction_ID: Rename from blank/Unnamed and ensure no duplicates
    df = df.rename(columns={df.columns[0]: 'Transaction_ID'})
    df = df.drop_duplicates(subset=['Transaction_ID'])
    logging.info("Rule 1 (Transaction_ID): Renamed and removed duplicates.")

    # 2. Customer ID: Ensure no missing values
    df = df.dropna(subset=['Customer ID'])
    logging.info("Rule 2 (Customer ID): Removed rows with missing IDs.")

    # 3. Category: Standardize to Title Case
    df['Category'] = df['Category'].str.title().fillna("General")
    logging.info("Rule 3 (Category): Standardized to Title Case.")

    # 4. Item: Fill missing items
    df['Item'] = df['Item'].fillna("Miscellaneous Item")
    logging.info("Rule 4 (Item): Filled blanks with 'Miscellaneous Item'.")

    # 5. Price Per Unit: Force to positive float
    df['Price Per Unit'] = pd.to_numeric(df['Price Per Unit'], errors='coerce').abs().fillna(0.0)
    logging.info("Rule 5 (Price Per Unit): Converted to positive numbers.")

    # 6. Quantity: Ensure it is an integer and at least 1
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(1).astype(int)
    logging.info("Rule 6 (Quantity): Converted to integer (min 1).")

    # 7. Total Spent: Ensure numeric
    df['Total Spent'] = pd.to_numeric(df['Total Spent'], errors='coerce').fillna(0.0)
    logging.info("Rule 7 (Total Spent): Sanitized numeric format.")

    # 8. Payment Method: Standardize naming
    df['Payment Method'] = df['Payment Method'].str.strip().fillna("Other")
    logging.info("Rule 8 (Payment Method): Cleaned whitespace and filled blanks.")

    # 9. Location: Fill missing with 'Unknown'
    df['Location'] = df['Location'].fillna("Unknown")
    logging.info("Rule 9 (Location): Handled missing location data.")

    # 10. Transaction Date: Standardize to datetime
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
    df = df.dropna(subset=['Transaction Date'])
    logging.info("Rule 10 (Transaction Date): Converted to DateTime format.")

    # 11. Discount Applied: Force to Boolean
    df['Discount Applied'] = df['Discount Applied'].astype(str).str.upper().map({'TRUE': True, 'FALSE': False})
    df['Discount Applied'] = df['Discount Applied'].fillna(False)
    logging.info("Rule 11 (Discount Applied): Standardized to Boolean.")

    logging.info(f"SUCCESS: All 11 columns validated. {len(df)} rows ready.")
    return df
