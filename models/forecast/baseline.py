"""
Baseline forecasting models for short-horizon traffic KPIs.
- Last value
- Seasonal naive
"""
import pandas as pd
import numpy as np

def last_value_forecast(series, horizon=5):
    """Forecast next horizon steps using last observed value."""
    return np.repeat(series.iloc[-1], horizon)

def seasonal_naive_forecast(series, season_length=12, horizon=5):
    """Forecast using value from same time last season."""
    return series.iloc[-season_length:][:horizon].values

# Example usage:
# df = pd.read_parquet('data/features.parquet')
# y = df['queue_length']
# preds = last_value_forecast(y, horizon=5)
