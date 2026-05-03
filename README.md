# Data Engineering Project — Batch & Real-time Pipelines

**Student:** Salina Giri | **Course:** Data Engineering, Year 2 Semester 2

---

## Overview

Two independent data pipelines orchestrated by **Apache Airflow** and writing to **Azure Blob Storage**.

| | Part 1 — Batch | Part 2 — Real-time |
|---|---|---|
| Dataset | NYC Yellow Taxi, Jan 2025 (~3.4M rows) | Retail Inventory (149 rows, 11 columns) |
| Input | `.parquet` | `.csv` / `.xlsx` |
| Trigger | Scheduled — 5 May 2026 | File drop into `input_zone/` |
| Output | Local `.parquet` + Azure Blob | Local `.csv` + Azure Blob |

Both pipelines follow the same pattern:
```
Reader → Validator → Processor → Back-up Validator → Writer
```

See `VALIDATION_RULES.md` for full validation logic. See `DEFENCE.md` for a defence walkthrough and Q&A.

---

## Structure

```
taxi_project/
├── docker-compose.yaml
├── dags/
│   ├── batch_pipeline_dag.py       ← Part 1 DAG (runs once, 5 May 2026)
│   └── realtime_pipeline_dag.py    ← Part 2 DAG (every 5 minutes)
├── part_1_batch_processing/
│   ├── main.py
│   ├── input/                      ← Raw parquet file
│   ├── output/                     ← processed_taxi_data.parquet + rejected CSVs
│   └── pipeline/
└── part_2_real_time_processing/
    ├── main.py
    ├── watcher.py                  ← Instant file-system trigger
    ├── input_zone/                 ← Drop files here
    ├── output_zone/                ← Processed CSV output
    └── pipeline/
```

---

## Running

### Standalone

```bash
# Part 1
cd part_1_batch_processing && pip install -r requirements.txt && python3 main.py

# Part 2 — leave terminal open, then drop a file into input_zone/
cd part_2_real_time_processing && pip install -r requirements.txt && python watcher.py
```

### Airflow (Docker)

```bash
docker compose up airflow-init   # first time only
docker compose up -d
# http://localhost:8080  (admin / admin)
```

- **`part1_batch_taxi_pipeline`** — toggle ON, trigger manually or wait for 5 May 2026
- **`part2_realtime_inventory_pipeline`** — polls `input_zone/` every 5 minutes; skips cleanly if empty

---

## Azure

Credentials are read from `.env` files at runtime (`AZURE_STORAGE_CONNECTION_STRING`). Never hardcoded.

| Pipeline | Container |
|---|---|
| Part 1 | `taxiproject` |
| Part 2 | `inventory-output` |
