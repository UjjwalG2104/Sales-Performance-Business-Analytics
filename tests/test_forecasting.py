"""
Unit Tests for SalesIQ Sales Forecasting Engine.
"""
import pandas as pd
import pytest
from src.forecasting import SalesForecaster


def test_insufficient_data_handling():
    # Only 4 months of data
    df = pd.DataFrame({
        "Order Date": ["2023-01-15", "2023-02-15", "2023-03-15", "2023-04-15"],
        "Sales": [100.0, 150.0, 200.0, 180.0]
    })
    res = SalesForecaster.run_forecast(df)
    assert res.is_sufficient_data is False
    assert "at least 12 months" in res.message


def test_forecast_execution_with_sufficient_data():
    dates = pd.date_range("2021-01-01", "2023-12-31", freq="ME")
    sales = [1000 + i * 50 + (200 if i % 12 == 11 else 0) for i in range(len(dates))]
    df = pd.DataFrame({"Order Date": dates, "Sales": sales})

    res = SalesForecaster.run_forecast(df, test_periods=4, forecast_horizon=4)
    assert res.is_sufficient_data is True
    assert "MAE" in res.metrics
    assert "RMSE" in res.metrics
    assert len(res.forecast_df) == 4
    assert res.metrics["MAE"] >= 0.0
