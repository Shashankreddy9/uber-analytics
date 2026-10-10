
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[1]
file = root / "data" / "yellow_tripdata_2025-01.parquet"

print(f"File size: {file.stat().st_size / (1024**2):.1f} MB")

df = pd.read_parquet(
    file,
    columns=["tpep_pickup_datetime"]
)

print(f"Total source rows: {len(df):,}")
print("\nPickup date counts for the entire file:")

dates = pd.to_datetime(df["tpep_pickup_datetime"]).dt.date
print(dates.value_counts().sort_index())

print("\nEarliest pickup:", dates.min())
print("Latest pickup:", dates.max())