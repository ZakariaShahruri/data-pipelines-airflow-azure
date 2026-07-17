
# ==========================================
# STAGE 1: READER
# ==========================================
import os
import pandas as pd
from pipeline.config import Config


def reader(file_path: str = Config.INPUT_FILE) -> pd.DataFrame:
    print(f"\n{'='*50}\nSTAGE: READER INGESTION\n{'='*50}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    try:
        df = pd.read_parquet(file_path, engine='pyarrow')
    except Exception as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}") from e

    if df.empty:
        raise ValueError(f"Input file contains no data: {file_path}")

    print(f"  >> Total Raw Rows Loaded: {len(df):,}")
    print(f"  >> Columns: {list(df.columns)}")
    return df
