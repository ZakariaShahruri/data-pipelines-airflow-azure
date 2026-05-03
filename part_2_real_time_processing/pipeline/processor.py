import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("--- PROCESSOR START: Enhancing Data Quality & Insights ---")

    # 1. Remove Duplicates
    initial_rows = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=['Transaction_ID'])
    logging.info(f"Requirement 1: Removed {initial_rows - len(df)} duplicate records.")

    # 2. New column: Vat_Amount (21% standard VAT)
    df['Vat_Amount'] = (df['Total Spent'] * 0.21).round(2)
    logging.info("Requirement 2: Added 'Vat_Amount' (21%).")

    # 3. New column: Is_Bulk_Order (flag orders with 10+ items)
    df['Is_Bulk_Order'] = df['Quantity'] >= 10
    logging.info("Requirement 3: Added 'Is_Bulk_Order' flag.")

    # 4. New column: Customer_Segment (spending tiers)
    df['Customer_Segment'] = df['Total Spent'].apply(
        lambda x: 'Premium' if x > 200 else ('Mid-Tier' if x > 100 else 'Standard')
    )
    logging.info("Requirement 4: Added 'Customer_Segment' (Premium/Mid-Tier/Standard).")

    # 5. New column: Estimated_Delivery (transaction date + 3 days)
    df['Estimated_Delivery'] = df['Transaction Date'] + pd.Timedelta(days=3)
    logging.info("Requirement 5: Added 'Estimated_Delivery' (T+3 days).")

    # 6. New column: Order_Reference (unique lookup key)
    df['Order_Reference'] = df['Customer ID'] + "-" + df['Location'].str.upper()
    logging.info("Requirement 6: Created 'Order_Reference' lookup key.")

    logging.info(f"SUCCESS: Processing complete. Total columns now: {len(df.columns)}")
    return df
