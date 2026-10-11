"""
Integration & Workflow Tests for Custom Dataset Ingestion, Partial Schemas & State Management.
"""
import pandas as pd
import pytest
from src.data_cleaner import DataCleaner
from src.database import DatabaseManager
from src.kpi_calculator import KPICalculator
from src.state_manager import initialize_app_state


def test_cleaner_with_exchange_rate():
    raw_df = pd.DataFrame({
        "Sales": [100.0, 200.0],
        "Profit": [20.0, 40.0],
        "Shipping Cost": [10.0, 15.0]
    })
    # Exchange rate USD -> INR: 86.5
    cleaner = DataCleaner(raw_df, exchange_rate=86.5)
    clean_df, audit = cleaner.clean()

    assert clean_df.loc[0, "Sales"] == 8650.0
    assert clean_df.loc[0, "Profit"] == 1730.0
    assert clean_df.loc[0, "Shipping Cost"] == 865.0
    assert any("Applied currency conversion rate" in a for a in audit.actions_taken)


def test_partial_dataset_kpis_no_profit_no_date():
    partial_df = pd.DataFrame({
        "Sales": [500.0, 1500.0],
        "Product Name": ["Item A", "Item B"]
    })
    cleaner = DataCleaner(partial_df)
    clean_df, _ = cleaner.clean()
    kpi = KPICalculator.calculate_kpis(clean_df)

    assert kpi.total_revenue == 2000.0
    assert kpi.has_profit is False
    assert kpi.total_profit is None
    assert kpi.profit_margin_pct is None
    assert kpi.has_dates is False
    assert kpi.revenue_growth_pct is None
    assert kpi.total_orders == 2  # Fallback to line count


def test_sql_refresh_without_duplicates():
    db = DatabaseManager()
    db.initialize_schema()

    df1 = pd.DataFrame({
        "Order ID": ["CA-1", "CA-2"],
        "Sales": [100.0, 200.0],
        "Profit": [20.0, 30.0]
    })
    count1 = db.load_cleaned_data_to_db(df1, replace=True)
    assert count1 == 2

    # Check row count in database
    res1 = db.execute_query("SELECT COUNT(*) AS cnt FROM fact_orders;")
    assert int(res1.loc[0, "cnt"]) == 2

    # Replace with a new dataset (3 rows)
    df2 = pd.DataFrame({
        "Order ID": ["TX-101", "TX-102", "TX-103"],
        "Sales": [500.0, 600.0, 700.0],
        "Profit": [50.0, 60.0, 70.0]
    })
    count2 = db.load_cleaned_data_to_db(df2, replace=True)
    assert count2 == 3

    # Ensure previous rows were deleted and not duplicated
    res2 = db.execute_query("SELECT COUNT(*) AS cnt FROM fact_orders;")
    assert int(res2.loc[0, "cnt"]) == 3

    # Clear tables
    db.clear_all_tables()
    res3 = db.execute_query("SELECT COUNT(*) AS cnt FROM fact_orders;")
    assert int(res3.loc[0, "cnt"]) == 0


def test_query_compatibility_checks():
    db = DatabaseManager()
    
    # Query referencing profit
    query_profit = "SELECT p.category, SUM(f.profit) FROM fact_orders f JOIN dim_products p ON f.product_id = p.product_id GROUP BY p.category;"
    is_compat, reason = db.check_query_compatibility(query_profit, ["Sales", "Category"])
    assert is_compat is False
    assert "Profit" in reason

    # Query with available columns
    query_sales = "SELECT p.category, SUM(f.sales) FROM fact_orders f JOIN dim_products p ON f.product_id = p.product_id GROUP BY p.category;"
    is_compat2, reason2 = db.check_query_compatibility(query_sales, ["Sales", "Category"])
    assert is_compat2 is True
    assert reason2 is None
