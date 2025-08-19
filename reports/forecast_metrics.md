# Forecast Model Evaluation Metrics

This report will summarize the evaluation of short-horizon traffic forecasting models.

## Metrics
- **MAE (Mean Absolute Error)** and **MAPE (Mean Absolute Percentage Error)** for flow/volume
- **RMSE (Root Mean Squared Error)** for speed
- **Mean delay per vehicle** (proxy)
- **Rolling origin cross-validation** for robust time series evaluation

## Baselines
- Last value
- Seasonal naive

## ML Models
- XGBoost/LightGBM with lagged features
- (Optional) LSTM/TFT for deep time series

## Results
Results and plots will be added after model training and evaluation.

## XGBoost Results

```
No output was printed by the script. Please ensure the script prints or saves results for reporting.
```

## Next Steps
- Update the model script to print or save MAE/RMSE results
- Add baseline results
- Visualize predictions vs actuals

## XGBoost Results
No valid samples for training after dropping missing values.

## XGBoost Results
Fold 1: MAE=0.000, RMSE=0.000

## XGBoost Results
Test MAE=0.000, RMSE=0.000
