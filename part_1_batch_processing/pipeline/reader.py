
# ==========================================
# STAGE 1: READER
# ==========================================
import logging
import os
import pandas as pd
from pipeline.config import Config

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def reader(file_path: str = Config.INPUT_FILE) -> pd.DataFrame:
    logging.info(f"\n{'='*50}\nSTAGE: READER INGESTION\n{'='*50}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    try:
        df = pd.read_parquet(file_path, engine='pyarrow')
    except Exception as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}") from e

    if df.empty:
        raise ValueError(f"Input file contains no data: {file_path}")

    logging.info(f"Total Raw Rows Loaded: {len(df):,}")
    logging.info(f"Columns: {list(df.columns)}")
    return df
