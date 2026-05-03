
# ==========================================
# STAGE 1: READER
# ==========================================
import os
import sys
import pandas as pd
from pipeline.config import Config


def reader(file_path: str = Config.INPUT_FILE) -> pd.DataFrame:
    print(f"\n{'='*50}\nSTAGE: READER INGESTION\n{'='*50}")

    if not os.path.exists(file_path):
        print(f"  >> CRITICAL: File not found — {file_path}")
        sys.exit(1)

    try:
        df = pd.read_parquet(file_path, engine='pyarrow')
    except Exception as e:
        print(f"  >> CRITICAL: Failed to read file — {e}")
        sys.exit(1)

    if df.empty:
        print("  >> CRITICAL: Input file contains no data.")
        sys.exit(1)

    print(f"  >> Total Raw Rows Loaded: {len(df):,}")
    print(f"  >> Columns: {list(df.columns)}")
    return df
