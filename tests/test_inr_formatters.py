"""
Unit Tests for Indian Rupee (INR) & Indian Numbering System Formatters.
"""
import pytest
from src.formatters import (
    format_indian_number,
    format_inr,
    format_inr_compact,
    format_percentage,
)


def test_inr_currency_formatting():
    # Standard positive amounts with Indian comma grouping
    assert format_inr(1532068.61) == "₹15,32,068.61"
    assert format_inr(170471.65) == "₹1,70,471.65"
    assert format_inr(1460.50) == "₹1,460.50"
    assert format_inr(0.0) == "₹0.00"
    assert format_inr(50.0) == "₹50.00"
    assert format_inr(999.99) == "₹999.99"
    assert format_inr(1000.0) == "₹1,000.00"
    assert format_inr(100000.0) == "₹1,00,000.00"
    assert format_inr(10000000.0) == "₹1,00,00,000.00"


def test_negative_inr_currency_formatting():
    # Negative currency amounts should lead with minus sign
    assert format_inr(-123456.78) == "-₹1,23,456.78"
    assert format_inr(-1532068.61) == "-₹15,32,068.61"
    assert format_inr(-50.0) == "-₹50.00"


def test_indian_number_grouping():
    # Quantities and counts without currency symbols
    assert format_indian_number(1234567) == "12,34,567"
    assert format_indian_number(50) == "50"
    assert format_indian_number(999) == "999"
    assert format_indian_number(1000) == "1,000"
    assert format_indian_number(10000) == "10,000"
    assert format_indian_number(100000) == "1,00,000"
    assert format_indian_number(10000000) == "1,00,00,000"
    assert format_indian_number(-54321) == "-54,321"


def test_edge_cases_and_missing_values():
    assert format_inr(None) == "—"
    assert format_inr(float("nan")) == "—"
    assert format_indian_number(None) == "—"
    assert format_indian_number(float("nan")) == "—"
    assert format_percentage(12.5) == "+12.5%"
    assert format_percentage(-4.2) == "-4.2%"
    assert format_percentage(0.0) == "0.0%"


def test_inr_compact_notation():
    assert format_inr_compact(1532068.61) == "₹15.32 L"
    assert format_inr_compact(15000000.0) == "₹1.50 Cr"
    assert format_inr_compact(4500.0) == "₹4.5 K"
    assert format_inr_compact(-250000.0) == "-₹2.50 L"
