import logging
import os
import numpy as np
import pandas as pd
from pipeline.config import Config

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def backup_validator(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Back-up validation — runs after the processor on computed columns.
    Checks for physically impossible values introduced during processing.

    Returns:
        (valid_df, rejected_df)
    """
    logging.info(f"\n{'='*50}\nSTAGE: BACK-UP VALIDATION\n{'='*50}")

    os.makedirs(Config.LOCAL_OUTPUT_DIR, exist_ok=True)
    df_before = df.copy()

    # Remove any infinities introduced by division
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=['average_speed_mph', 'revenue_per_mile'])

    # NYC reality checks
    df = df[df['average_speed_mph'] <= 100]   # no taxi goes over 100 mph in NYC
    df = df[df['trip_duration_minutes'] > 0]   # trip must have positive duration

    # Collect rejected rows
    rejected = df_before[~df_before.index.isin(df.index)].copy()

    if not rejected.empty:
        rejected_path = os.path.join(Config.LOCAL_OUTPUT_DIR, "rejected_backup.csv")
        rejected.to_csv(rejected_path, index=False)
        logging.info(f"Audit Trail: {len(rejected):,} invalid rows → {rejected_path}")

    logging.info(f"Back-up validation complete. Retained {len(df):,} valid rows.")
    return df, rejected
