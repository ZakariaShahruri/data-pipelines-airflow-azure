# Data Engineering Pipelines — Batch & Real-time

[![Tests](https://github.com/ZakariaShahruri/data-pipelines-airflow-azure/actions/workflows/tests.yml/badge.svg)](https://github.com/ZakariaShahruri/data-pipelines-airflow-azure/actions/workflows/tests.yml)

Two independent data pipelines orchestrated by **Apache Airflow** and writing to **Azure Blob Storage**.

| | Part 1 — Batch | Part 2 — Real-time |
|---|---|---|
| Dataset | NYC Yellow Taxi, Jan 2025 (~3.4 M rows) | Retail Inventory (150 rows, 11 columns) |
| Input | `.parquet` file | `.csv` / `.xlsx` dropped into a folder |
| Trigger | Manual | File drop into `input_zone/` |
| Output | Local `.parquet` + Azure Blob | Local `.csv` + Azure Blob |

Both pipelines follow the same pattern:
```
Reader → Validator → Processor → Back-up Validator → Writer
```

See `VALIDATION_RULES.md` for the full validation logic per column.

---

## Project Structure

```
taxi_project/
├── .env.example                        ← Copy to .env and fill in credentials
├── docker-compose.yaml                 ← Airflow + PostgreSQL setup
├── dags/
│   ├── batch_pipeline_dag.py           ← Part 1 DAG (unscheduled, triggered manually)
│   └── realtime_pipeline_dag.py        ← Part 2 DAG (polls every 5 minutes)
├── part_1_batch_processing/
│   ├── main.py                         ← Standalone runner
│   ├── input/                          ← Place downloaded parquet file here
│   ├── output/                         ← Results written here after pipeline runs
│   └── pipeline/                       ← reader, validator, processor, writer
└── part_2_real_time_processing/
    ├── main.py                         ← Standalone runner
    ├── watcher.py                      ← Instant OS-level file trigger
    ├── input_zone/                     ← Drop .csv / .xlsx files here
    ├── output_zone/                    ← Processed output written here
    └── pipeline/                       ← reader, validator, processor, writer
```

---

## Step 1 — Prerequisites

Install the following before anything else:

- **Docker Desktop** — https://www.docker.com/products/docker-desktop  
  Required to run Airflow. After installing, open the Docker Desktop app and make sure it is running (you will see the Docker icon in your taskbar/menu bar).

- **Python 3.10+** — only needed if you want to run the pipelines standalone (without Docker).

---

## Step 2 — Clone the Repository

```bash
git clone https://github.com/ZakariaShahruri/data-pipelines-airflow-azure.git
cd data-pipelines-airflow-azure
```

---

## Step 3 — Download the Dataset (Part 1 only)

The Yellow Taxi parquet file is too large to store in GitHub.

1. Go to: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
2. Download **Yellow Taxi Trip Records — January 2025** (Parquet format)
3. Place the file here: `part_1_batch_processing/input/yellow_tripdata_2025-01.parquet`

Part 2 uses a small inventory CSV included in the repository. It is stored in `input_zone/archived/` to prevent it from being auto-processed on startup. Copy it into `input_zone/` when you want to test:

```bash
cp part_2_real_time_processing/input_zone/archived/inventory_data.csv part_2_real_time_processing/input_zone/
```

---

## Step 4 — Set Up the .env File (Azure Credentials)

The Azure connection string is never stored in the repository — it's a secret, so you provide your own.

```bash
cp .env.example .env
```

Open `.env` and fill in the connection string for your own Azure Storage account (Azure Portal → Storage Account → Access keys → Connection string). The file should look like:

```
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=<your-account>;AccountKey=<key>;EndpointSuffix=core.windows.net
AIRFLOW_UID=50000
```

> Don't have an Azure account handy? That's fine — the pipeline still runs end-to-end and writes output locally; the Azure upload step is simply skipped with a warning if `.env` is missing or the connection string is invalid.
>
> Do not commit the `.env` file — it is already in `.gitignore`.

---

## Option A — Run Standalone (no Docker required)

This runs the pipeline directly in your terminal without Airflow.

### Part 1 — Batch

```bash
cd part_1_batch_processing

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
python3 main.py
```

The pipeline reads `input/yellow_tripdata_2025-01.parquet`, validates and processes it, then writes results to `output/` and uploads to Azure Blob Storage.

### Part 2 — Real-time

```bash
cd part_2_real_time_processing

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
python3 watcher.py
```

Leave the terminal open. Drop any `.csv` or `.xlsx` file into `input_zone/`. The pipeline triggers instantly and writes output to `output_zone/`.

---

## Option B — Run with Airflow (Docker) — Recommended

### First-time setup (run once)

Make sure Docker Desktop is open and running, then:

```bash
docker compose up airflow-init
```

This sets up the database and creates the Airflow admin user. Wait until you see `exited with code 0` before continuing.

### Start Airflow

```bash
docker compose up -d
```

This starts three containers in the background: PostgreSQL, the Airflow scheduler, and the Airflow web server. Wait about 30–60 seconds for everything to be ready.

> **Note:** The first startup installs Python dependencies inside the containers. This can take 2–5 minutes on the first run.

### Open the Airflow UI

Go to: **http://localhost:8080**

Login with:
- **Username:** `admin`
- **Password:** `admin`

### Run Part 1 — Batch Pipeline

1. In the Airflow UI, click **DAGs** in the top menu
2. Find `part1_batch_taxi_pipeline`
3. Toggle the switch on the left from **off (paused) → on (active)**
4. Click the **play button** (▶) on the right → select **Trigger DAG**
5. Click on the DAG name to open the graph view and watch each task turn green

Output is written to `part_1_batch_processing/output/` and uploaded to the `taxiproject` Azure Blob container.

### Run Part 2 — Real-time Pipeline

1. In the Airflow UI, find `part2_realtime_inventory_pipeline`
2. Toggle it **on**
3. Drop a `.csv` file into `part_2_real_time_processing/input_zone/`
4. The DAG checks for files every 5 minutes — or click the **play button** to trigger immediately
5. After processing, the input file moves to `input_zone/archived/` and output appears in `output_zone/`

### Stop Airflow

```bash
docker compose down
```

---

## Azure Blob Storage

| Pipeline | Container name |
|---|---|
| Part 1 | `taxiproject` |
| Part 2 | `inventory-output` |

Credentials are loaded at runtime from the `.env` file. If `.env` is missing or the connection string is wrong, the pipeline still completes and saves output locally — the Azure upload step is skipped with a warning.

---

## Running the Tests

Each pipeline has its own unit + integration test suite (pytest), covering the validation boundary rules, feature-engineering logic, and the writer's local/Azure paths (Azure calls are mocked — no credentials or network access needed).

```bash
cd part_1_batch_processing
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r ../requirements-dev.txt
pytest -v
```

```bash
cd part_2_real_time_processing
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r ../requirements-dev.txt
pytest -v
```

Both suites also run automatically in CI on every push/PR — see `.github/workflows/tests.yml`.
