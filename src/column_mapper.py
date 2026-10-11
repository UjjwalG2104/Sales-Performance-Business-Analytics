"""
SalesIQ — Intelligent Column Mapping & Schema Adaptation Engine.
Detects column aliases with case-, whitespace-, and punctuation-insensitive matching.
Enables custom dataset ingestion across diverse retail and ecommerce schemas.
"""
import re
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd

# Canonical field definitions and priority aliases
CANONICAL_ALIASES: Dict[str, List[str]] = {
    "Sales": [
        "sales", "revenue", "total sales", "amount", "net sales", "total amount",
        "sales amount", "turnover", "total", "order value", "extended price",
        "price total", "line total", "sale amount", "gross sales"
    ],
    "Order Date": [
        "order date", "order_date", "date", "invoice date", "invoicedate",
        "transaction date", "transaction_date", "orderdate", "sale date",
        "trans date", "trans_date", "purchase date", "timestamp"
    ],
    "Order ID": [
        "order id", "order_id", "invoice no", "invoiceno", "invoice number",
        "transaction id", "transaction_id", "order no", "order_no", "orderid",
        "trans id", "trans_id", "receipt no", "document no"
    ],
    "Profit": [
        "profit", "net profit", "earnings", "margin", "total profit",
        "operating profit", "net margin", "income", "gain"
    ],
    "Quantity": [
        "quantity", "qty", "units sold", "units", "number of items",
        "item count", "count", "volume", "order qty", "item qty"
    ],
    "Discount": [
        "discount", "discount rate", "markdown", "discount_pct", "disc",
        "discount pct", "rebate", "discount percentage", "discount amount"
    ],
    "Product Name": [
        "product name", "product", "item", "item name", "product_name",
        "description", "sku", "goods", "title", "product title", "merchandise"
    ],
    "Product ID": [
        "product id", "product_id", "productid", "item id", "item_id",
        "sku code", "product code", "item code", "asin"
    ],
    "Category": [
        "category", "product category", "department", "item category",
        "category name", "sector", "class", "product line", "division"
    ],
    "Sub-Category": [
        "sub-category", "sub_category", "subcategory", "sub category",
        "product subcategory", "family", "sub department", "type"
    ],
    "Customer Name": [
        "customer name", "customer_name", "customername", "customer", "client",
        "client name", "buyer", "account name", "contact name", "full name"
    ],
    "Customer ID": [
        "customer id", "customer_id", "customerid", "client id", "client_id",
        "account id", "cust id", "cust_id", "member id"
    ],
    "Segment": [
        "segment", "customer segment", "tier", "market segment", "channel",
        "customer type", "client type", "group"
    ],
    "Region": [
        "region", "zone", "territory", "area", "geographic region", "district"
    ],
    "State": [
        "state", "province", "region/state", "state/province"
    ],
    "City": [
        "city", "town", "municipality", "location"
    ],
    "Postal Code": [
        "postal code", "postal_code", "zip code", "zipcode", "zip", "pincode", "pin code"
    ],
    "Ship Date": [
        "ship date", "ship_date", "shipping date", "shipdate", "dispatch date", "delivery date"
    ],
    "Shipping Cost": [
        "shipping cost", "shipping_cost", "freight", "shipping fee", "shipping", "delivery fee"
    ]
}


def normalize_string(s: str) -> str:
    """Normalizes a column name by removing special characters, underscores, and extra spaces."""
    s = str(s).lower().strip()
    s = re.sub(r"[_\-\.]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def detect_column_mapping(df_columns: List[str]) -> Dict[str, Optional[str]]:
    """
    Intelligently maps raw dataframe column names to canonical schema fields.
    Guarantees no raw column is assigned to more than one canonical field.
    """
    normalized_raw = {col: normalize_string(col) for col in df_columns}
    assigned_raw_cols: Set[str] = set()
    mapping: Dict[str, Optional[str]] = {}

    # Exact normalized match first
    for canonical, aliases in CANONICAL_ALIASES.items():
        matched_raw = None
        for raw_col, norm_col in normalized_raw.items():
            if raw_col in assigned_raw_cols:
                continue
            if norm_col in [normalize_string(a) for a in aliases]:
                matched_raw = raw_col
                break

        if matched_raw:
            mapping[canonical] = matched_raw
            assigned_raw_cols.add(matched_raw)

    # Substring / partial match for remaining unmapped canonical fields
    for canonical, aliases in CANONICAL_ALIASES.items():
        if canonical in mapping:
            continue

        matched_raw = None
        for raw_col, norm_col in normalized_raw.items():
            if raw_col in assigned_raw_cols:
                continue

            for alias in aliases:
                norm_alias = normalize_string(alias)
                # Word boundary match
                pattern = r"\b" + re.escape(norm_alias) + r"\b"
                if re.search(pattern, norm_col):
                    matched_raw = raw_col
                    break
            if matched_raw:
                break

        if matched_raw:
            mapping[canonical] = matched_raw
            assigned_raw_cols.add(matched_raw)
        else:
            mapping[canonical] = None

    return mapping


def apply_column_mapping(
    df: pd.DataFrame,
    mapping: Dict[str, Optional[str]]
) -> pd.DataFrame:
    """
    Renames columns in df based on confirmed mapping.
    Canonical fields without a mapping will not exist in the output dataframe.
    """
    rename_dict = {}
    for canonical, raw_col in mapping.items():
        if raw_col and raw_col in df.columns:
            rename_dict[raw_col] = canonical

    mapped_df = df.rename(columns=rename_dict).copy()
    return mapped_df


def validate_mapping(
    mapping: Dict[str, Optional[str]],
    df: pd.DataFrame
) -> Tuple[bool, List[str], List[str]]:
    """
    Validates mapped schema against minimum analytical requirements:
    - Minimum requirement: 'Sales' column must be mapped and convertible to numeric.
    - Generates informational warnings for missing optional fields.
    """
    errors: List[str] = []
    warnings: List[str] = []

    sales_col = mapping.get("Sales")
    if not sales_col:
        errors.append("Mandatory field 'Sales' (Revenue / Amount) is not mapped. Sales analytics requires a numeric sales column.")
    elif sales_col not in df.columns:
        errors.append(f"Mapped Sales column '{sales_col}' does not exist in the uploaded file.")
    else:
        # Check if sales can be parsed as numeric
        sample_sales = df[sales_col].dropna().head(100)
        numeric_test = pd.to_numeric(sample_sales, errors="coerce")
        if numeric_test.isna().all() and len(sample_sales) > 0:
            errors.append(f"Column '{sales_col}' mapped to 'Sales' cannot be parsed as numeric values.")

    # Informational warnings for missing optional fields
    if not mapping.get("Profit"):
        warnings.append("Profit column is absent: Profit metrics, margins, and loss analytics will be hidden.")
    if not mapping.get("Order Date"):
        warnings.append("Order Date column is absent: Time-series trends, monthly growth, and forecasting will be disabled.")
    if not mapping.get("Order ID"):
        warnings.append("Order ID column is absent: Unique order counts and Average Order Value (AOV) will be based on line items.")
    if not mapping.get("Customer Name") and not mapping.get("Customer ID"):
        warnings.append("Customer columns are absent: Customer analytics will be hidden.")
    if not mapping.get("Category") and not mapping.get("Product Name"):
        warnings.append("Product/Category columns are absent: Product portfolio analytics will be hidden.")
    if not mapping.get("Region") and not mapping.get("State"):
        warnings.append("Region/State columns are absent: Geographic territory maps will be hidden.")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings
