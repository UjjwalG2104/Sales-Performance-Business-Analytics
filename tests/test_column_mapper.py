"""
Unit Tests for Intelligent Column Mapping & Schema Detection.
"""
import pandas as pd
import pytest
from src.column_mapper import (
    apply_column_mapping,
    detect_column_mapping,
    normalize_string,
    validate_mapping,
)


def test_normalize_string():
    assert normalize_string("  Order_ID  ") == "order id"
    assert normalize_string("Invoice-No.") == "invoice no"
    assert normalize_string("NET_SALES_AMOUNT") == "net sales amount"


def test_alias_detection_ecommerce_variant():
    raw_cols = [
        "Invoice No",
        "Invoice Date",
        "Client ID",
        "Client Name",
        "Customer Group",
        "Item Name",
        "Department",
        "Units Sold",
        "Gross Sales",
        "Net Profit",
        "Markdown",
        "Territory",
    ]
    mapping = detect_column_mapping(raw_cols)

    assert mapping["Order ID"] == "Invoice No"
    assert mapping["Order Date"] == "Invoice Date"
    assert mapping["Customer ID"] == "Client ID"
    assert mapping["Customer Name"] == "Client Name"
    assert mapping["Segment"] == "Customer Group"
    assert mapping["Product Name"] == "Item Name"
    assert mapping["Category"] == "Department"
    assert mapping["Quantity"] == "Units Sold"
    assert mapping["Sales"] == "Gross Sales"
    assert mapping["Profit"] == "Net Profit"
    assert mapping["Discount"] == "Markdown"
    assert mapping["Region"] == "Territory"


def test_validate_mapping_missing_sales():
    raw_df = pd.DataFrame({"Order ID": ["ORD-1"], "Profit": [50.0]})
    mapping = {"Sales": None, "Profit": "Profit"}
    is_valid, errors, warnings = validate_mapping(mapping, raw_df)

    assert is_valid is False
    assert any("Mandatory field 'Sales'" in e for e in errors)


def test_validate_mapping_with_optional_fields_missing():
    raw_df = pd.DataFrame({"Amount": [1000.0, 2000.0], "Item": ["Widget A", "Widget B"]})
    mapping = {"Sales": "Amount", "Product Name": "Item", "Profit": None, "Order Date": None}
    is_valid, errors, warnings = validate_mapping(mapping, raw_df)

    assert is_valid is True
    assert len(errors) == 0
    assert any("Profit column is absent" in w for w in warnings)
    assert any("Order Date column is absent" in w for w in warnings)


def test_apply_column_mapping():
    raw_df = pd.DataFrame({
        "Invoice No": ["INV-1001"],
        "Amount": [499.50],
        "Earnings": [85.00]
    })
    mapping = {
        "Order ID": "Invoice No",
        "Sales": "Amount",
        "Profit": "Earnings"
    }
    mapped_df = apply_column_mapping(raw_df, mapping)

    assert "Order ID" in mapped_df.columns
    assert "Sales" in mapped_df.columns
    assert "Profit" in mapped_df.columns
    assert mapped_df.loc[0, "Sales"] == 499.50
