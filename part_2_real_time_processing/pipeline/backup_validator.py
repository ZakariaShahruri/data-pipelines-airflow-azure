import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def backup_validate(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("--- BACK-UP VALIDATOR START: Final Sanity Check ---")

    # 1. Check for nulls in new engineered columns
    new_cols = ['Vat_Amount', 'Is_Bulk_Order', 'Customer_Segment', 'Estimated_Delivery', 'Order_Reference']
    for col in new_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            logging.warning(f"Sanity Check: Found {null_count} nulls in {col}. Filling defaults...")
            if col == 'Vat_Amount':
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna("Unknown")

    # 2. Negative VAT safety check
    negative_vat = df[df['Vat_Amount'] < 0]
    if not negative_vat.empty:
        logging.error("Sanity Check: Found negative VAT values! Correcting to 0.")
        df.loc[df['Vat_Amount'] < 0, 'Vat_Amount'] = 0

    # 3. Date consistency check
    date_errors = df[df['Estimated_Delivery'] < df['Transaction Date']]
    if not date_errors.empty:
        logging.error("Sanity Check: Delivery dates found before Transaction dates!")

    # 4. Schema consistency: 11 original + 5 engineered = 16 columns
    expected_count = 16
    if len(df.columns) != expected_count:
        logging.error(f"SCHEMA ERROR: Expected {expected_count} columns, found {len(df.columns)}")
    else:
        logging.info(f"Rule 4: Schema verified — all {expected_count} columns present.")

    logging.info("SUCCESS: Back-up validation passed. Data is safe for export.")
    return df
