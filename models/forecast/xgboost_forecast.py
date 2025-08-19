"""
XGBoost forecasting for short-horizon traffic KPIs.
"""
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error

def make_lag_features(df, target, lags=[1,2]):
    # Create lag features for the target variable
    df = df.copy()
    for lag in lags:
        df[f'{target}_lag{lag}'] = df[target].shift(lag)
    return df

def train_xgb_forecast(df, target, horizon=5):
    # Use up to 10 lags for the target variable
    df = make_lag_features(df, target, lags=list(range(1, 11)))
    # Drop columns that are entirely empty
    df = df.dropna(axis=1, how='all')
    print(f"DataFrame shape after dropping empty columns: {df.shape}")
    # Fill missing target values with column mean
    if df[target].isnull().any():
        mean_val = df[target].mean()
        df[target] = df[target].fillna(mean_val)
        print(f'Filled missing values in {target} with mean: {mean_val:.3f}')
    # Drop non-numeric columns
    X = df.drop([target], axis=1)
    X = X.select_dtypes(include=['number', 'bool'])
    y = df[target]
    # Split into train/dev/test sets (60/20/20)
    n = len(X)
    train_end = int(n * 0.6)
    dev_end = int(n * 0.8)
    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_dev, y_dev = X.iloc[train_end:dev_end], y.iloc[train_end:dev_end]
    X_test, y_test = X.iloc[dev_end:], y.iloc[dev_end:]
    model = XGBRegressor()
    model.fit(X_train, y_train, eval_set=[(X_dev, y_dev)], verbose=True)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    print('XGBoost Forecast Results:')
    print(f'Test MAE={mae:.3f}, RMSE={rmse:.3f}')
    with open('reports/forecast_metrics.md', 'a') as f:
        f.write('\n## XGBoost Results\n')
        f.write(f'Test MAE={mae:.3f}, RMSE={rmse:.3f}\n')
    return {'mae': mae, 'rmse': rmse}
    # Print and save results
    print('XGBoost Forecast Results:')
    for i, res in enumerate(results):
        print(f'Fold {i+1}: MAE={res["mae"]:.3f}, RMSE={res["rmse"]:.3f}')
    # Save to markdown report
    with open('reports/forecast_metrics.md', 'a') as f:
        f.write('\n## XGBoost Results\n')
        for i, res in enumerate(results):
            f.write(f'Fold {i+1}: MAE={res["mae"]:.3f}, RMSE={res["rmse"]:.3f}\n')
    return results

# Example usage:
if __name__ == "__main__":
    df = pd.read_parquet('data/features.parquet')
    train_xgb_forecast(df, 'queue_length')
