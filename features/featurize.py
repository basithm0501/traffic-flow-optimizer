"""
Fetch hourly weather data from Open-Meteo for intersection locations and join with traffic metrics.
Saves enriched features to data/features.parquet.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import os

# Intersection coordinates (example: Monroe Ave & S Winton Rd, Monroe Ave & Clover St)
INTERSECTIONS = [
    {"name": "Monroe Ave & S Winton Rd", "lat": 43.12708222627869, "lon": -77.5653911674301},
    {"name": "Monroe Ave & Clover St (NY65)", "lat": 43.111108, "lon": -77.547803}
]

# Time range for weather data (last 24 hours)
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=24)

# Open-Meteo API endpoint
API_URL = "https://api.open-meteo.com/v1/forecast"

# Weather parameters to fetch
PARAMS = {
    "hourly": "temperature_2m,precipitation,windspeed_10m",
    "timezone": "UTC"
}

def fetch_weather(lat, lon, start, end):
    params = PARAMS.copy()
    params.update({
        "latitude": lat,
        "longitude": lon,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d")
    })
    resp = requests.get(API_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    # Flatten to DataFrame
    df = pd.DataFrame({
        "time": data["hourly"]["time"],
        "temperature_2m": data["hourly"]["temperature_2m"],
        "precipitation": data["hourly"]["precipitation"],
        "windspeed_10m": data["hourly"]["windspeed_10m"]
    })
    df["lat"] = lat
    df["lon"] = lon
    return df

# Fetch weather for all intersections
weather_dfs = []
for loc in INTERSECTIONS:
    df = fetch_weather(loc["lat"], loc["lon"], start_time, end_time)
    df["intersection"] = loc["name"]
    weather_dfs.append(df)
weather_df = pd.concat(weather_dfs, ignore_index=True)

# Load traffic metrics (assume metrics.parquet exists)
metrics_path = "data/metrics.parquet"
if os.path.exists(metrics_path):
    metrics_df = pd.read_parquet(metrics_path)
    # Merge on intersection name and hour
    metrics_df["hour"] = pd.to_datetime(metrics_df["minute"]).dt.floor("H")
    weather_df["hour"] = pd.to_datetime(weather_df["time"])
    features_df = pd.merge(metrics_df, weather_df, left_on=["camera_id", "hour"], right_on=["intersection", "hour"], how="left")
    # Save enriched features
    features_df.to_parquet("data/features.parquet")
    print("Saved enriched features to data/features.parquet")
else:
    print(f"Metrics file not found: {metrics_path}")
