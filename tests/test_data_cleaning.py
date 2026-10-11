"""
Unit Tests for SalesIQ Data Cleaning & Quality Audit.
"""
import pandas as pd
import pytest
from src.data_cleaner import DataCleaner
from src.data_loader import validate_schema


def test_schema_validation():
    valid_df = pd.DataFrame({
        "Order ID": ["CA-1"],
        "Order Date": ["2023-01-01"],
        "Ship Date": ["2023-01-03"],
        "Customer ID": ["C-1"],
        "Customer Name": ["Alice"],
        "Segment": ["Consumer"],
        "Country": ["United States"],
        "State": ["California"],
        "City": ["Los Angeles"],
        "Region": ["West"],
        "Product ID": ["P-1"],
        "Category": ["Technology"],
        "Sub-Category": ["Phones"],
        "Product Name": ["iPhone"],
        "Sales": [100.0],
        "Quantity": [1],
        "Discount": [0.1],
        "Profit": [20.0],
    })
    is_valid, missing, _ = validate_schema(valid_df)
    assert is_valid is True
    assert len(missing) == 0

    # Incomplete schema
    invalid_df = pd.DataFrame({"Order ID": ["CA-1"], "Sales": [100.0]})
    is_valid, missing, _ = validate_schema(invalid_df)
    assert is_valid is False
    assert "Customer ID" in missing
    assert "Profit" in missing


def test_duplicate_removal():
    df = pd.DataFrame({
        "Order ID": ["CA-1", "CA-1", "CA-2"],
        "Order Date": ["2023-01-01", "2023-01-01", "2023-01-02"],
        "Ship Date": ["2023-01-03", "2023-01-03", "2023-01-04"],
        "Customer ID": ["C-1", "C-1", "C-2"],
        "Customer Name": ["Alice", "Alice", "Bob"],
        "Segment": ["Consumer", "Consumer", "Corporate"],
        "Country": ["USA", "USA", "USA"],
        "State": ["CA", "CA", "NY"],
        "City": ["LA", "LA", "NYC"],
        "Region": ["West", "West", "East"],
        "Product ID": ["P-1", "P-1", "P-2"],
        "Category": ["Tech", "Tech", "Office"],
        "Sub-Category": ["Phones", "Phones", "Paper"],
        "Product Name": ["Phone", "Phone", "Paper"],
        "Sales": [100.0, 100.0, 50.0],
        "Quantity": [1, 1, 2],
        "Discount": [0.0, 0.0, 0.1],
        "Profit": [20.0, 20.0, 10.0]
    })
    cleaner = DataCleaner(df)
    clean_df, audit = cleaner.clean()

    assert len(clean_df) == 2
    assert audit.original_metrics.duplicate_records == 1
    assert audit.cleaned_metrics.duplicate_records == 0


def test_inconsistent_dates_and_negative_sales():
    df = pd.DataFrame({
        "Order ID": ["CA-1"],
        "Order Date": ["2023-05-10"],
        "Ship Date": ["2023-05-01"],  # Inconsistent: earlier than order date
        "Customer ID": ["C-1"],
        "Customer Name": ["Alice"],
        "Segment": ["Consumer"],
        "Country": ["USA"],
        "State": ["CA"],
        "City": ["LA"],
        "Region": ["West"],
        "Product ID": ["P-1"],
        "Category": ["Tech"],
        "Sub-Category": ["Phones"],
        "Product Name": ["Phone"],
        "Sales": [-250.0],  # Negative sales entry error
        "Quantity": [1],
        "Discount": [1.5],  # Out-of-bounds discount
        "Profit": [-50.0]
    })
    cleaner = DataCleaner(df)
    clean_df, audit = cleaner.clean()

    # Ship date corrected to order date
    assert clean_df.loc[0, "Ship Date"] == pd.Timestamp("2023-05-10")
    # Sales sanitized to positive
    assert clean_df.loc[0, "Sales"] == 250.0
    # Discount clamped to 1.0
    assert clean_df.loc[0, "Discount"] == 1.0


def test_empty_dataframe_cleaning():
    df = pd.DataFrame(columns=["Order ID", "Sales", "Profit"])
    cleaner = DataCleaner(df)
    clean_df, audit = cleaner.clean()
    assert len(clean_df) == 0
    assert audit.cleaned_metrics.total_records == 0
