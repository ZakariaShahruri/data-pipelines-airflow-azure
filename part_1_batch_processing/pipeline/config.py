import os

class Config:
    INPUT_FILE  = 'input/yellow_tripdata_2025-01.parquet'
    OUTPUT_FILE = 'processed_taxi_data.parquet'
    LOCAL_OUTPUT_DIR = "output"
    AZURE_CONTAINER  = "taxiproject"

    # Credentials — set these as environment variables, never hardcode them
    AZURE_CONN_STRING    = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_ACCOUNT_NAME   = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    AZURE_ACCOUNT_KEY    = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

    VALIDATION_RULES = {
        "tpep_pickup_datetime":   "Mandatory: Must exist and occur before dropoff.",
        "passenger_count":        "Mandatory: Must be between 1 and 9.",
        "trip_distance":          "Mandatory: Must be greater than 0 miles.",
        "PULocationID/DOLocationID": "Mandatory: Must be valid positive integers.",
        "payment_type":           "Mandatory: Must be a standard code (1-6).",
        "fare_amount/total_amount": "Mandatory: Must be positive numerical values.",
        "tip_amount/surcharges":  "Non-Mandatory: Missing values imputed with 0.0.",
        "RatecodeID":             "Non-Mandatory: Missing values imputed with 99 (Unknown).",
        "average_speed_mph":      "Back-up: Must be <= 100 mph (NYC reality check).",
        "trip_duration_minutes":  "Back-up: Must be strictly greater than 0.",
    }

