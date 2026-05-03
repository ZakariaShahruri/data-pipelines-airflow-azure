"""
Part 1 — Batch Processing DAG
NYC Yellow Taxi January 2025

Pipeline stages run as separate Airflow tasks so each step is visible,
retryable, and logged independently in the Airflow UI.

Intermediate DataFrames are persisted as Parquet files between tasks so
large datasets (3.4 M+ rows) never pass through XCom.

TODO: set DEFENSE_DATE to your actual defence date before the exam.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

# ── Project path setup ────────────────────────────────────────────────────────
PROJECT_DIR = Path(os.getenv("PROJECT_DIR", "/opt/airflow"))
BATCH_DIR = PROJECT_DIR / "part_1_batch_processing"
sys.path.insert(0, str(BATCH_DIR))

from dotenv import load_dotenv
load_dotenv(BATCH_DIR / ".env")

# ── Defence date — change this to your actual exam date ──────────────────────
DEFENSE_DATE = datetime(2026, 5, 5)

# ── Temp staging files shared between tasks ───────────────────────────────────
TEMP = BATCH_DIR / "output" / "airflow_temp"

default_args = {
    "owner": "salina",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# ── Task callables ────────────────────────────────────────────────────────────

def task_read(**ctx) -> None:
    os.chdir(BATCH_DIR)
    from pipeline.reader import reader
    from pipeline.config import Config

    raw_df = reader(str(BATCH_DIR / Config.INPUT_FILE))

    TEMP.mkdir(parents=True, exist_ok=True)
    out = str(TEMP / "raw.parquet")
    raw_df.to_parquet(out, engine="pyarrow", index=False)
    ctx["ti"].xcom_push(key="raw_path", value=out)
    print(f"[Reader] {len(raw_df):,} rows saved to {out}")


def task_validate(**ctx) -> None:
    os.chdir(BATCH_DIR)
    from pipeline.validator import validator

    raw_path = ctx["ti"].xcom_pull(task_ids="read_data", key="raw_path")
    raw_df = pd.read_parquet(raw_path, engine="pyarrow")

    valid_df, rejected_df = validator(raw_df)

    valid_out = str(TEMP / "validated.parquet")
    rejected_out = str(TEMP / "rejected_primary.parquet")
    valid_df.to_parquet(valid_out, engine="pyarrow", index=False)
    if not rejected_df.empty:
        rejected_df.to_parquet(rejected_out, engine="pyarrow", index=False)

    ctx["ti"].xcom_push(key="validated_path", value=valid_out)
    ctx["ti"].xcom_push(key="rejected_primary_path", value=rejected_out)
    print(f"[Validator] valid={len(valid_df):,}  rejected={len(rejected_df):,}")


def task_process(**ctx) -> None:
    os.chdir(BATCH_DIR)
    from pipeline.processor import processor

    validated_path = ctx["ti"].xcom_pull(task_ids="validate_data", key="validated_path")
    validated_df = pd.read_parquet(validated_path, engine="pyarrow")

    processed_df = processor(validated_df)

    out = str(TEMP / "processed.parquet")
    processed_df.to_parquet(out, engine="pyarrow", index=False)
    ctx["ti"].xcom_push(key="processed_path", value=out)
    print(f"[Processor] {len(processed_df):,} rows with engineered features")


def task_backup_validate(**ctx) -> None:
    os.chdir(BATCH_DIR)
    from pipeline.backup_validator import backup_validator

    processed_path = ctx["ti"].xcom_pull(task_ids="process_data", key="processed_path")
    processed_df = pd.read_parquet(processed_path, engine="pyarrow")

    final_df, rejected_df = backup_validator(processed_df)

    final_out = str(TEMP / "final.parquet")
    rejected_out = str(TEMP / "rejected_backup.parquet")
    final_df.to_parquet(final_out, engine="pyarrow", index=False)
    if not rejected_df.empty:
        rejected_df.to_parquet(rejected_out, engine="pyarrow", index=False)

    ctx["ti"].xcom_push(key="final_path", value=final_out)
    ctx["ti"].xcom_push(key="rejected_backup_path", value=rejected_out)
    print(f"[Back-up Validator] final={len(final_df):,}  rejected={len(rejected_df):,}")


def task_write(**ctx) -> None:
    os.chdir(BATCH_DIR)
    from pipeline.writer import writer

    final_path = ctx["ti"].xcom_pull(task_ids="backup_validate", key="final_path")
    rejected_primary_path = ctx["ti"].xcom_pull(task_ids="validate_data", key="rejected_primary_path")
    rejected_backup_path = ctx["ti"].xcom_pull(task_ids="backup_validate", key="rejected_backup_path")

    final_df = pd.read_parquet(final_path, engine="pyarrow")

    parts = []
    for path in [rejected_primary_path, rejected_backup_path]:
        p = Path(path) if path else None
        if p and p.exists():
            parts.append(pd.read_parquet(p, engine="pyarrow"))
    all_rejected = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

    result = writer(final_df, invalid_df=all_rejected if not all_rejected.empty else None)
    print(f"[Writer] local={result.get('local_valid')}  azure={result.get('azure_url', 'N/A')}")

    # Print final quality report
    total_input = len(pd.read_parquet(ctx["ti"].xcom_pull(task_ids="read_data", key="raw_path")))
    print(f"\n{'*'*50}\nFINAL QUALITY REPORT\n{'*'*50}")
    print(f"  Raw Input:    {total_input:,}")
    print(f"  Final Gold:   {len(final_df):,}")
    print(f"  Data Loss:    {((total_input - len(final_df)) / total_input * 100):.2f}%")
    print("*"*50)


# ── DAG definition ────────────────────────────────────────────────────────────

with DAG(
    dag_id="part1_batch_taxi_pipeline",
    description="NYC Yellow Taxi Jan 2025 — Read → Validate → Process → Write",
    start_date=DEFENSE_DATE,
    schedule="@once",          # Runs exactly once on the defence date
    default_args=default_args,
    catchup=False,
    tags=["batch", "taxi", "part1"],
) as dag:

    read_data = PythonOperator(
        task_id="read_data",
        python_callable=task_read,
    )

    validate_data = PythonOperator(
        task_id="validate_data",
        python_callable=task_validate,
    )

    process_data = PythonOperator(
        task_id="process_data",
        python_callable=task_process,
    )

    backup_validate = PythonOperator(
        task_id="backup_validate",
        python_callable=task_backup_validate,
    )

    write_data = PythonOperator(
        task_id="write_data",
        python_callable=task_write,
    )

    # ── Linear dependency chain ───────────────────────────────────────────────
    read_data >> validate_data >> process_data >> backup_validate >> write_data
