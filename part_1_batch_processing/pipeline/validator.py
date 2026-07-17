# ==========================================
# STAGE 2: VALIDATOR 
# ==========================================
import os
import pandas as pd
from pipeline.config import Config


MANDATORY_COLS = [
    'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'passenger_count',
    'trip_distance', 'PULocationID', 'DOLocationID',
    'payment_type', 'fare_amount', 'total_amount'
]

OPTIONAL_COLS = [
    'tip_amount', 'tolls_amount', 'extra',
    'airport_fee', 'congestion_surcharge', 'cbd_congestion_fee'
]


def validator(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Primary validation — checks mandatory columns and business rules.

    Returns:
        (valid_df, rejected_df)
    """
    print(f"\n{'='*50}\nSTAGE: PRIMARY VALIDATION\n{'='*50}")

    os.makedirs(Config.LOCAL_OUTPUT_DIR, exist_ok=True)
    df_before = df.copy()

    # Column existence check
    missing = [col for col in MANDATORY_COLS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing mandatory columns: {missing}")

    # 1. Mandatory filters
    df = df.dropna(subset=MANDATORY_COLS)
    df = df[df['tpep_dropoff_datetime'] > df['tpep_pickup_datetime']]
    df = df[(df['passenger_count'] >= 1) & (df['passenger_count'] < 10)]
    df = df[df['trip_distance'] > 0]
    df = df[(df['PULocationID'] > 0) & (df['DOLocationID'] > 0)]
    df = df[df['payment_type'].isin([1, 2, 3, 4, 5, 6])]
    df = df[(df['fare_amount'] > 0) & (df['total_amount'] > 0)]

    # 2. Non-mandatory: impute missing/negative values with 0.0
    for col in OPTIONAL_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)
            df.loc[df[col] < 0, col] = 0.0

    # 3. RatecodeID: impute missing with 99 (Unknown)
    if 'RatecodeID' in df.columns:
        df['RatecodeID'] = df['RatecodeID'].fillna(99)

    # Collect rejected rows
    rejected = df_before[~df_before.index.isin(df.index)].copy()

    if not rejected.empty:
        rejected_path = os.path.join(Config.LOCAL_OUTPUT_DIR, "rejected_primary.csv")
        rejected.to_csv(rejected_path, index=False)
        print(f"  >> Audit Trail: {len(rejected):,} invalid rows → {rejected_path}")

    print(f"  >> Primary validation complete. Retained {len(df):,} valid rows.")
    return df, rejected
