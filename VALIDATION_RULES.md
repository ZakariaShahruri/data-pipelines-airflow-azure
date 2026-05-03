# Validation Rules

Both pipelines use a two-pass validation strategy:
- **Primary Validator** — enforces business rules on the raw input data
- **Back-up Validator** — sanity-checks computed columns after processing

---

## Part 1 — NYC Yellow Taxi (Batch)

Source: `part_1_batch_processing/pipeline/validator.py` and `backup_validator.py`

### Primary Validation

| Column | Type | Rule | On Failure |
|---|---|---|---|
| `tpep_pickup_datetime` | Mandatory | Must exist and be strictly before `tpep_dropoff_datetime` | Row rejected |
| `tpep_dropoff_datetime` | Mandatory | Must exist and be strictly after pickup | Row rejected |
| `passenger_count` | Mandatory | Integer between 1 and 9 (inclusive) | Row rejected |
| `trip_distance` | Mandatory | Must be > 0 miles | Row rejected |
| `PULocationID` | Mandatory | Must be a positive integer | Row rejected |
| `DOLocationID` | Mandatory | Must be a positive integer | Row rejected |
| `payment_type` | Mandatory | Must be one of the standard codes: 1, 2, 3, 4, 5, or 6 | Row rejected |
| `fare_amount` | Mandatory | Must be a positive number | Row rejected |
| `total_amount` | Mandatory | Must be a positive number | Row rejected |
| `tip_amount` | Non-mandatory | Any numeric value accepted | Null or negative → imputed with `0.0` |
| `tolls_amount` | Non-mandatory | Any numeric value accepted | Null or negative → imputed with `0.0` |
| `extra` | Non-mandatory | Any numeric value accepted | Null or negative → imputed with `0.0` |
| `airport_fee` | Non-mandatory | Any numeric value accepted | Null or negative → imputed with `0.0` |
| `congestion_surcharge` | Non-mandatory | Any numeric value accepted | Null or negative → imputed with `0.0` |
| `cbd_congestion_fee` | Non-mandatory | Any numeric value accepted | Null or negative → imputed with `0.0` |
| `RatecodeID` | Non-mandatory | Any standard code accepted | Null → imputed with `99` (Unknown) |

**Rejected rows** are written to `output/rejected_primary.csv` for audit.

### Back-up Validation (Post-processing)

Runs after the processor has added computed columns. Checks for physically impossible values.

| Column | Rule | On Failure |
|---|---|---|
| `average_speed_mph` | Must be ≤ 100 mph (NYC physical reality) | Row rejected |
| `trip_duration_minutes` | Must be > 0 | Row rejected |
| `average_speed_mph` / `revenue_per_mile` | No infinite values (division edge case) | Row rejected |

**Rejected rows** are written to `output/rejected_backup.csv` for audit.

---

## Part 2 — Retail Inventory (Real-time)

Source: `part_2_real_time_processing/pipeline/validator.py` and `backup_validator.py`

### Primary Validation (11 Columns)

| # | Column | Type | Rule | On Failure |
|---|---|---|---|---|
| 1 | `Transaction_ID` | Mandatory | Must be unique across the dataset | Duplicate rows are dropped |
| 2 | `Customer ID` | Mandatory | Must not be null | Row removed |
| 3 | `Category` | Mandatory | Any string accepted; standardised to Title Case | Null → filled with `"General"` |
| 4 | `Item` | Non-mandatory | Any string accepted | Null → filled with `"Miscellaneous Item"` |
| 5 | `Price Per Unit` | Mandatory | Must be a positive numeric value | Non-numeric or negative → set to `0.0` |
| 6 | `Quantity` | Mandatory | Must be a positive integer (minimum 1) | Non-numeric → set to `1`; coerced to `int` |
| 7 | `Total Spent` | Mandatory | Must be a numeric value | Non-numeric → set to `0.0` |
| 8 | `Payment Method` | Non-mandatory | Any string accepted; leading/trailing whitespace stripped | Null → filled with `"Other"` |
| 9 | `Location` | Non-mandatory | Any string accepted | Null → filled with `"Unknown"` |
| 10 | `Transaction Date` | Mandatory | Must be parseable as a date/datetime | Unparseable → row removed |
| 11 | `Discount Applied` | Mandatory | Must resolve to `True` or `False` | Neither → filled with `False` |

### Back-up Validation (Post-processing)

Runs after the processor has added 5 engineered columns. Verifies schema and logical consistency.

| Check | Rule | On Failure |
|---|---|---|
| Null check (all 5 new columns) | No nulls allowed in engineered columns | `Vat_Amount` nulls → `0`; others → `"Unknown"` |
| `Vat_Amount` | Must be ≥ 0 | Negative values corrected to `0` |
| `Estimated_Delivery` | Must be after `Transaction Date` | Flagged in logs; row retained |
| Schema count | Exactly 16 columns must be present (11 original + 5 engineered) | Error logged |

---

## Summary

| | Part 1 | Part 2 |
|---|---|---|
| Mandatory columns | 9 | 7 |
| Non-mandatory columns | 7 (imputed) | 4 (imputed) |
| Rows rejected | Saved to CSV audit files | Dropped in-place |
| Back-up checks | 3 (speed, duration, infinities) | 4 (nulls, VAT, dates, schema) |
