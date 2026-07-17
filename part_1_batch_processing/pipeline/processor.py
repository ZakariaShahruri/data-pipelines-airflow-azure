import logging

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

COLS_TO_REMOVE = ['VendorID', 'store_and_fwd_flag', 'RatecodeID']


def processor(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the validated DataFrame:
      - Removes unused columns
      - Adds computed columns
    """
    logging.info(f"\n{'='*50}\nSTAGE: PROCESSOR\n{'='*50}")

    # Remove columns per assignment spec
    cols_to_drop = [col for col in COLS_TO_REMOVE if col in df.columns]
    df = df.drop(columns=cols_to_drop)
    logging.info(f"Removed columns: {cols_to_drop}")

    # Computed columns
    df['trip_duration_minutes'] = (
        df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']
    ).dt.total_seconds() / 60

    df['average_speed_mph'] = np.where(
        df['trip_duration_minutes'] > 0,
        df['trip_distance'] / (df['trip_duration_minutes'] / 60),
        0
    )

    df['revenue_per_mile'] = np.where(
        df['trip_distance'] > 0,
        df['total_amount'] / df['trip_distance'],
        0
    )

    df['pickup_year']  = df['tpep_pickup_datetime'].dt.year
    df['pickup_month'] = df['tpep_pickup_datetime'].dt.month

    # Spec: Short < 2, Medium 2–10, Long > 10  (boundary values belong to upper category)
    df['trip_distance_category'] = np.select(
        [df['trip_distance'] < 2, df['trip_distance'] <= 10],
        ['Short', 'Medium'],
        default='Long'
    )

    # Spec: Low < 20, Medium 20–50, High > 50  (boundary values belong to upper category)
    df['fare_category'] = np.select(
        [df['fare_amount'] < 20, df['fare_amount'] <= 50],
        ['Low', 'Medium'],
        default='High'
    )

    df['trip_time_of_day'] = pd.cut(
        df['tpep_pickup_datetime'].dt.hour,
        bins=[0, 6, 12, 18, 24],
        labels=['Night', 'Morning', 'Afternoon', 'Evening'],
        right=True,
        include_lowest=True  # otherwise an exact-midnight pickup (hour == 0) falls outside every bin -> NaN
    )

    logging.info("Processor complete.")
    logging.info("New columns added: trip_duration_minutes, average_speed_mph, "
                 "revenue_per_mile, pickup_year, pickup_month, "
                 "trip_distance_category, fare_category, trip_time_of_day")
    return df