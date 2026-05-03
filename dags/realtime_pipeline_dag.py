"""
Part 2 — Real-time Processing DAG
Inventory / Retail Store dataset

The DAG runs every 5 minutes. If it finds a supported file (.csv / .xlsx / .xls)
in input_zone/ it runs the full pipeline; otherwise it skips cleanly via
ShortCircuitOperator (no failed runs, no alerts).

After writing, the processed file is moved to input_zone/archived/ so the same
file is never processed twice.

Standalone alternative: run  python part_2_real_time_processing/watcher.py
which reacts to files the instant they land (watchdog OS events).
Do NOT run both simultaneously — they will race on the same file.
"""
from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator

# ── Project path setup ────────────────────────────────────────────────────────
# Default: two levels up from dags/ (works locally and in Docker when PROJECT_DIR is set).
PROJECT_DIR = Path(os.getenv("PROJECT_DIR", str(Path(__file__).resolve().parent.parent)))
REALTIME_DIR = PROJECT_DIR / "part_2_real_time_processing"
sys.path.insert(0, str(REALTIME_DIR))

from dotenv import load_dotenv
load_dotenv(REALTIME_DIR / ".env")

SUPPORTED_EXTENSIONS = ('.csv', '.xlsx', '.xls')
INPUT_DIR = REALTIME_DIR / "input_zone"
OUTPUT_DIR = REALTIME_DIR / "output_zone"
TEMP = OUTPUT_DIR / "airflow_temp"

default_args = {
    "owner": "salina",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


# ── Task callables ────────────────────────────────────────────────────────────

def check_for_files(**ctx) -> bool:
    """
    ShortCircuitOperator: returns True if a file is waiting, False to skip.
    Pushes the found file path so downstream tasks know which file to process.
    """
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in SUPPORTED_EXTENSIONS:
        files = sorted(INPUT_DIR.glob(f"*{ext}"))
        if files:
            file_path = str(files[0])
            ctx["ti"].xcom_push(key="input_file", value=file_path)
            print(f"[Sensor] Found: {files[0].name}")
            return True
    print("[Sensor] No files in input_zone — skipping this run.")
    return False


def task_read(**ctx) -> None:
    from pipeline.reader import load_data

    input_file = ctx["ti"].xcom_pull(task_ids="check_for_files", key="input_file")
    file_name = Path(input_file).name

    df = load_data(file_name)

    TEMP.mkdir(parents=True, exist_ok=True)
    out = str(TEMP / "raw.parquet")
    df.to_parquet(out, engine="pyarrow", index=False)
    ctx["ti"].xcom_push(key="raw_path", value=out)
    ctx["ti"].xcom_push(key="source_file_name", value=file_name)
    print(f"[Reader] {len(df):,} rows loaded from {file_name}")


def task_validate(**ctx) -> None:
    from pipeline.validator import validate_data

    raw_path = ctx["ti"].xcom_pull(task_ids="read_data", key="raw_path")
    df = pd.read_parquet(raw_path, engine="pyarrow")

    validated_df = validate_data(df)

    out = str(TEMP / "validated.parquet")
    validated_df.to_parquet(out, engine="pyarrow", index=False)
    ctx["ti"].xcom_push(key="validated_path", value=out)
    print(f"[Validator] {len(validated_df):,} rows passed validation")


def task_process(**ctx) -> None:
    from pipeline.processor import process_data

    validated_path = ctx["ti"].xcom_pull(task_ids="validate_data", key="validated_path")
    df = pd.read_parquet(validated_path, engine="pyarrow")

    processed_df = process_data(df)

    out = str(TEMP / "processed.parquet")
    processed_df.to_parquet(out, engine="pyarrow", index=False)
    ctx["ti"].xcom_push(key="processed_path", value=out)
    print(f"[Processor] {len(processed_df):,} rows with {len(processed_df.columns)} columns")


def task_backup_validate(**ctx) -> None:
    from pipeline.backup_validator import backup_validate

    processed_path = ctx["ti"].xcom_pull(task_ids="process_data", key="processed_path")
    df = pd.read_parquet(processed_path, engine="pyarrow")

    final_df = backup_validate(df)

    out = str(TEMP / "final.parquet")
    final_df.to_parquet(out, engine="pyarrow", index=False)
    ctx["ti"].xcom_push(key="final_path", value=out)
    print(f"[Back-up Validator] {len(final_df):,} rows ready for export")


def task_write(**ctx) -> None:
    from pipeline.writer import write_data

    final_path = ctx["ti"].xcom_pull(task_ids="backup_validate", key="final_path")
    source_name = ctx["ti"].xcom_pull(task_ids="read_data", key="source_file_name")

    df = pd.read_parquet(final_path, engine="pyarrow")
    stem = Path(source_name).stem
    output_name = f"{stem}_processed.csv"
    write_data(df, output_name)
    print(f"[Writer] {len(df):,} rows saved as {output_name}")


def task_archive(**ctx) -> None:
    """Move the source file to input_zone/archived/ to prevent reprocessing."""
    input_file = ctx["ti"].xcom_pull(task_ids="check_for_files", key="input_file")
    if not input_file:
        return
    src = Path(input_file)
    if not src.exists():
        print(f"[Archive] Source already moved: {src.name}")
        return
    archive_dir = INPUT_DIR / "archived"
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / src.name
    shutil.move(str(src), str(dest))
    print(f"[Archive] {src.name} → archived/")


# ── DAG definition ────────────────────────────────────────────────────────────

with DAG(
    dag_id="part2_realtime_inventory_pipeline",
    description="Real-time inventory pipeline — polls input_zone/ every 5 min",
    start_date=datetime(2025, 1, 1),
    schedule="*/5 * * * *",
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    tags=["realtime", "inventory", "part2"],
) as dag:

    check_files = ShortCircuitOperator(
        task_id="check_for_files",
        python_callable=check_for_files,
    )

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

    archive_file = PythonOperator(
        task_id="archive_input_file",
        python_callable=task_archive,
    )

    (
        check_files
        >> read_data
        >> validate_data
        >> process_data
        >> backup_validate
        >> write_data
        >> archive_file
    )
