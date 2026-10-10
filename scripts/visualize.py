
from pathlib import Path
from getpass import getpass

import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Project folders
ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

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

try:
    # Get trip counts for each pickup hour
    query = """
        SELECT
            HOUR(pickup_datetime) AS pickup_hour,
            COUNT(*) AS total_trips
        FROM trips_full
        GROUP BY HOUR(pickup_datetime)
        ORDER BY pickup_hour;
    """

    df = pd.read_sql_query(query, engine)

    # Create hourly demand chart
    plt.figure(figsize=(12, 6))
    plt.bar(df["pickup_hour"], df["total_trips"])

    plt.title("NYC Taxi Trips by Pickup Hour")
    plt.xlabel("Pickup Hour (24-hour format)")
    plt.ylabel("Number of Trips")
    plt.xticks(range(24))
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    chart_path = OUTPUT_DIR / "hourly_trip_demand.png"
    plt.savefig(chart_path, dpi=300)
    plt.show()

    print(f"Chart saved to: {chart_path}")

finally:
    engine.dispose()