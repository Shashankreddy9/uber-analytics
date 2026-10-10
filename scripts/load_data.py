
from pathlib import Path
from getpass import getpass

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Find the project folder and dataset
ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "yellow_tripdata_2025-01.parquet"

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_FILE}\n"
        "Check that the Parquet file is inside the data folder."
    )

print("Reading dataset...")

# Load a sample of 100,000 rows
columns = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "trip_distance",
    "fare_amount",
    "total_amount",
]

df = pd.read_parquet(DATA_FILE, columns=columns).head(100_000)

# Clean the data
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
    df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
).dt.total_seconds() / 60

df = df[
    (df["trip_duration_min"] > 0)
    & (df["trip_duration_min"] <= 240)
    & (df["trip_distance"] > 0)
].copy()

df = df.rename(columns={
    "tpep_pickup_datetime": "pickup_datetime",
    "tpep_dropoff_datetime": "dropoff_datetime",
    "PULocationID": "pickup_location_id",
    "DOLocationID": "dropoff_location_id",
})

df["pickup_location_id"] = df["pickup_location_id"].astype(int)
df["dropoff_location_id"] = df["dropoff_location_id"].astype(int)

print(f"Clean rows ready to load: {len(df):,}")

# Connect to MySQL
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

# Append rows to the existing trips table
try:
    with engine.begin() as connection:
        df.to_sql(
            "trips",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=1000,
        )

        total = connection.execute(
            text("SELECT COUNT(*) FROM trips")
        
        ).scalar_one()

    print(f"Rows loaded: {len(df):,}")
    print(f"Total rows in MySQL: {total:,}")

finally:
    engine.dispose()