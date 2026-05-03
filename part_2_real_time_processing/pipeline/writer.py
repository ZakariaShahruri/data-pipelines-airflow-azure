import io
import logging
import pandas as pd
from azure.storage.blob import BlobServiceClient
from pipeline.config import Config

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def write_data(df: pd.DataFrame, file_name: str = "processed_inventory.csv") -> None:
    logging.info("--- WRITER START: Finalizing Export ---")

    # 1. Local write
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    local_path = Config.OUTPUT_DIR / file_name
    df.to_csv(local_path, index=False)
    logging.info(f"Step 1: Local file saved → {local_path}  ({len(df):,} rows)")

    # 2. Azure cloud upload
    conn_str = Config.AZURE_CONN_STRING
    if not conn_str:
        logging.warning("Azure Upload: SKIPPED (set AZURE_STORAGE_CONNECTION_STRING to enable)")
        return

    try:
        logging.info("Step 2: Connecting to Azure Blob Storage...")
        service = BlobServiceClient.from_connection_string(conn_str)
        container_client = service.get_container_client(Config.AZURE_CONTAINER)
        try:
            container_client.create_container()
        except Exception:
            pass  # Container already exists

        buffer = io.BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)

        blob_client = container_client.get_blob_client(file_name)
        blob_client.upload_blob(buffer, overwrite=True)
        logging.info(f"SUCCESS: Cloud upload complete → {blob_client.url}")

    except Exception as e:
        logging.error(f"Cloud Upload Failed: {e}")
        logging.warning("Note: The local file was still saved successfully.")
