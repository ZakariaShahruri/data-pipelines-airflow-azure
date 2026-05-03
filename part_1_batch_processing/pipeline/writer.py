import io
import logging
import os
from pathlib import Path

import pandas as pd
from azure.storage.blob import BlobServiceClient
from pipeline.config import Config

logger = logging.getLogger(__name__)


def writer(valid_df: pd.DataFrame, invalid_df: pd.DataFrame = None) -> dict:
    """
    Write valid and (optionally) invalid DataFrames to local disk and Azure.

    Returns:
        dict with keys: 'local_valid', 'local_invalid' (if provided), 'azure_url' (if uploaded)
    """
    print(f"\n{'='*50}\nSTAGE: PERSISTENCE (LOCAL & CLOUD)\n{'='*50}")

    output_dir = Path(Config.LOCAL_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {}

    # ── 1. Local: valid rows ──────────────────────────────────────────────────
    local_path = output_dir / Config.OUTPUT_FILE
    valid_df.to_parquet(local_path, engine="pyarrow", index=False)
    result["local_valid"] = local_path
    print(f"  >> Local Save (valid):   {local_path}  ({len(valid_df):,} rows)")

    # ── 2. Local: rejected rows ───────────────────────────────────────────────
    if invalid_df is not None and not invalid_df.empty:
        rejected_path = output_dir / "rejected_rows.parquet"
        invalid_df.to_parquet(rejected_path, engine="pyarrow", index=False)
        result["local_invalid"] = rejected_path
        print(f"  >> Local Save (invalid): {rejected_path}  ({len(invalid_df):,} rows)")

    # ── 3. Azure upload ───────────────────────────────────────────────────────
    conn_str     = Config.AZURE_CONN_STRING
    account_name = Config.AZURE_ACCOUNT_NAME
    account_key  = Config.AZURE_ACCOUNT_KEY

    if not conn_str and not (account_name and account_key):
        print("  >> Azure Upload: SKIPPED (no credentials in environment)")
        return result

    try:
        if conn_str:
            service = BlobServiceClient.from_connection_string(conn_str)
        else:
            service = BlobServiceClient(
                account_url=f"https://{account_name}.blob.core.windows.net",
                credential=account_key,
            )

        container_client = service.get_container_client(Config.AZURE_CONTAINER)
        try:
            container_client.create_container()
        except Exception:
            pass  # Container already exists — safe to ignore

        # Serialize to memory and upload (no second disk read needed)
        buffer = io.BytesIO()
        valid_df.to_parquet(buffer, engine="pyarrow", index=False)
        buffer.seek(0)

        blob_client = container_client.get_blob_client(Config.OUTPUT_FILE)
        blob_client.upload_blob(buffer, overwrite=True)

        result["azure_url"] = blob_client.url
        print(f"  >> Azure Upload: SUCCESS → {blob_client.url}")

    except Exception as e:
        print(f"  >> Azure Upload: FAILED ({e})")
        logger.error(f"Azure upload failed: {e}")

    return result