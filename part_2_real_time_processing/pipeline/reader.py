import pandas as pd
import logging
from pipeline.config import Config

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def load_data(file_name: str = "inventory_data.csv") -> pd.DataFrame:
    input_path = Config.INPUT_DIR / file_name
    logging.info(f"--- READER START: Looking for {file_name} ---")

    if not input_path.exists():
        error_msg = f"CRITICAL ERROR: File not found at {input_path}"
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        suffix = input_path.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(input_path)
        elif suffix in (".xlsx", ".xls"):
            df = pd.read_excel(input_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        if df.empty:
            logging.warning("The file was found but it contains no data.")
            return df
        logging.info(f"SUCCESS: Loaded {len(df)} rows from {file_name}.")
        return df
    except Exception as e:
        logging.error(f"FAILED to read file: {str(e)}")
        raise
