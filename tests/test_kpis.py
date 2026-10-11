"""
Unit Tests for SalesIQ KPI Calculations & Financial Formulas.
"""
import pandas as pd
import pytest
from src.kpi_calculator import KPICalculator


def test_standard_kpi_calculations():
    df = pd.DataFrame({
        "Order ID": ["ORD-1", "ORD-1", "ORD-2"],  # 2 distinct orders
        "Sales": [100.0, 50.0, 250.0],           # Total 400.0
        "Profit": [20.0, 10.0, 50.0],             # Total 80.0
        "Quantity": [2, 1, 5],                    # Total 8 units
        "Discount": [0.0, 0.1, 0.0]
    })
    kpi = KPICalculator.calculate_kpis(df)

    assert kpi.total_revenue == 400.0
    assert kpi.total_profit == 80.0
    assert kpi.total_orders == 2
    assert kpi.units_sold == 8
    assert kpi.average_order_value == 200.0  # 400.0 / 2 orders
    assert kpi.profit_margin_pct == 20.0     # (80 / 400) * 100


def test_zero_denominator_safe_handling():
    # Zero sales case
    df_zero_sales = pd.DataFrame({
        "Order ID": ["ORD-1"],
        "Sales": [0.0],
        "Profit": [0.0],
        "Quantity": [0]
    })
    kpi = KPICalculator.calculate_kpis(df_zero_sales)
    assert kpi.profit_margin_pct == 0.0
    assert kpi.average_order_value == 0.0

    # Empty DataFrame case
    kpi_empty = KPICalculator.calculate_kpis(pd.DataFrame())
    assert kpi_empty.total_revenue == 0.0
    assert kpi_empty.total_profit == 0.0
    assert kpi_empty.total_orders == 0
    assert kpi_empty.profit_margin_pct == 0.0


def test_period_growth_calculation():
    prior_df = pd.DataFrame({"Sales": [1000.0], "Profit": [200.0], "Order ID": ["A"]})
    current_df = pd.DataFrame({"Sales": [1250.0], "Profit": [300.0], "Order ID": ["B"]})

    kpi = KPICalculator.calculate_kpis(current_df, prior_df=prior_df)
    assert kpi.revenue_growth_pct == 25.0   # ((1250 - 1000) / 1000) * 100
    assert kpi.profit_growth_pct == 50.0    # ((300 - 200) / 200) * 100
