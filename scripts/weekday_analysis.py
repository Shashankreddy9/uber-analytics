
from pathlib import Path
from getpass import getpass

import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

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
    query = """
        SELECT
            DAYOFWEEK(pickup_datetime) AS day_number,
            DAYNAME(pickup_datetime) AS day_name,
            COUNT(*) AS total_trips,
            ROUND(SUM(fare_amount), 2) AS total_fare_revenue,
            ROUND(AVG(fare_amount), 2) AS avg_fare
        FROM trips_full
        GROUP BY
            DAYOFWEEK(pickup_datetime),
            DAYNAME(pickup_datetime)
        ORDER BY day_number;
    """

    df = pd.read_sql_query(query, engine)

    # Print results for your analysis
    print("\nWeekday analysis:")
    print(df.to_string(index=False))

    # Create weekday trip-demand chart
    plt.figure(figsize=(10, 6))
    plt.bar(df["day_name"], df["total_trips"])

    plt.title("NYC Taxi Trip Demand by Day of Week")
    plt.xlabel("Day of Week")
    plt.ylabel("Total Trips")
    plt.xticks(rotation=30)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    chart_path = OUTPUT_DIR / "weekday_trip_demand.png"
    plt.savefig(chart_path, dpi=300)
    plt.show()

    print(f"\nChart saved to: {chart_path}")

finally:
    engine.dispose()