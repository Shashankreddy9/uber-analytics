
from pathlib import Path
from getpass import getpass

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "yellow_tripdata_2025-01.parquet"

if not DATA_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

columns = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "trip_distance",
    "fare_amount",
    "total_amount",
]

password = getpass("Enter your MySQL password: ")

url = URL.create(
    "mysql+pymysql",
    username="root",
    password=password,
    host="localhost",
    port=3306,
    database="uber_analytics",
)

engine = create_engine(url)

try:
    print("Reading full dataset...")
    df = pd.read_parquet(DATA_FILE, columns=columns)

    df["tpep_pickup_datetime"] = pd.to_datetime(
        df["tpep_pickup_datetime"], errors="coerce"
    )
    df["tpep_dropoff_datetime"] = pd.to_datetime(
        df["tpep_dropoff_datetime"], errors="coerce"
    )

    df = df.dropna(subset=[
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "PULocationID",
        "DOLocationID",
        "trip_distance",
    ])

    df["trip_duration_min"] = (
        df["tpep_dropoff_datetime"]
        - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60

    df = df[
        (df["trip_duration_min"] > 0)
        & (df["trip_duration_min"] <= 240)
        & (df["trip_distance"] > 0)
        & (df["tpep_pickup_datetime"] >= "2025-01-01")
        & (df["tpep_pickup_datetime"] < "2025-02-01")
    ].copy()

    df = df.rename(columns={
        "tpep_pickup_datetime": "pickup_datetime",
        "tpep_dropoff_datetime": "dropoff_datetime",
        "PULocationID": "pickup_location_id",
        "DOLocationID": "dropoff_location_id",
    })

    df["pickup_location_id"] = df["pickup_location_id"].astype(int)
    df["dropoff_location_id"] = df["dropoff_location_id"].astype(int)

    print(f"Clean January rows ready to load: {len(df):,}")

    # Replace only the separate full-data table.
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE trips_full"))

        df.to_sql(
            "trips_full",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=1000,
        )

        total = connection.execute(
            text("SELECT COUNT(*) FROM trips_full")
        ).scalar_one()

    print(f"Rows loaded into trips_full: {total:,}")

finally:
    engine.dispose()