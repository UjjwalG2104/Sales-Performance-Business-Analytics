"""
SalesIQ — Data Cleaning, Validation, and Quality Audit Module.
Performs deterministic data cleaning, type conversions, anomaly flagging,
and computes comprehensive Before-and-After Data Quality metrics.
"""
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class QualityMetrics:
    total_records: int = 0
    duplicate_records: int = 0
    missing_cells: int = 0
    missing_by_column: Dict[str, int] = field(default_factory=dict)
    invalid_dates_count: int = 0
    negative_sales_count: int = 0
    anomalous_discount_count: int = 0
    inconsistent_dates_count: int = 0  # ship_date < order_date
    memory_usage_kb: float = 0.0


@dataclass
class CleaningAudit:
    original_metrics: QualityMetrics
    cleaned_metrics: QualityMetrics
    actions_taken: List[str] = field(default_factory=list)
    flagged_records_count: int = 0


class DataCleaner:
    """
    Standardized, reproducible Data Cleaning pipeline for Sales Performance data.
    Preserves original data while producing a clean, typed, analytical-ready dataset.
    """

    def __init__(self, df: pd.DataFrame, exchange_rate: float = 1.0):
        self.raw_df = df.copy()
        self.cleaned_df = df.copy()
        self.exchange_rate = float(exchange_rate)
        self.audit_log: List[str] = []

    def compute_quality_metrics(self, df: pd.DataFrame) -> QualityMetrics:
        """Calculates comprehensive data health metrics on a given dataframe."""
        metrics = QualityMetrics()
        metrics.total_records = len(df)
        metrics.duplicate_records = int(df.duplicated().sum())
        metrics.missing_cells = int(df.isna().sum().sum())
        metrics.missing_by_column = {col: int(cnt) for col, cnt in df.isna().sum().items() if cnt > 0}
        metrics.memory_usage_kb = round(df.memory_usage(deep=True).sum() / 1024.0, 2)

        # Check domain-specific anomalies if columns exist
        if "Sales" in df.columns:
            numeric_sales = pd.to_numeric(df["Sales"], errors="coerce")
            metrics.negative_sales_count = int((numeric_sales < 0).sum())

        if "Discount" in df.columns:
            numeric_discount = pd.to_numeric(df["Discount"], errors="coerce")
            metrics.anomalous_discount_count = int(((numeric_discount < 0) | (numeric_discount > 1)).sum())

        if "Order Date" in df.columns and "Ship Date" in df.columns:
            o_dates = pd.to_datetime(df["Order Date"], errors="coerce")
            s_dates = pd.to_datetime(df["Ship Date"], errors="coerce")
            metrics.invalid_dates_count = int(o_dates.isna().sum() + s_dates.isna().sum())
            valid_mask = o_dates.notna() & s_dates.notna()
            metrics.inconsistent_dates_count = int((s_dates[valid_mask] < o_dates[valid_mask]).sum())

        return metrics

    def clean(self) -> Tuple[pd.DataFrame, CleaningAudit]:
        """
        Executes end-to-end cleaning workflow:
        1. Strips leading/trailing whitespaces in column names and string columns.
        2. Detects and removes exact duplicate records.
        3. Parses and validates Order Date and Ship Date.
        4. Corrects inconsistent Ship Dates (sets Ship Date = Order Date if prior).
        5. Casts numeric columns (Sales, Profit, Quantity, Discount, Shipping Cost).
        6. Converts currencies with explicit exchange rate if configured.
        7. Imputes or safely handles missing values without fabricating business totals.
        8. Adds analytical helper columns: Year, Month, YearMonth, Quarter, Profit Margin.
        """
        df = self.raw_df.copy()
        initial_metrics = self.compute_quality_metrics(df)
        actions = []

        # 1. Clean Column Names
        original_cols = list(df.columns)
        df.columns = [str(c).strip() for c in df.columns]
        if list(df.columns) != original_cols:
            actions.append("Trimmed whitespace from dataframe column headers.")

        # 2. Handle Duplicates
        num_dupes = int(df.duplicated().sum())
        if num_dupes > 0:
            df = df.drop_duplicates().reset_index(drop=True)
            actions.append(f"Removed {num_dupes} duplicate transaction rows.")

        # 3. Clean String Columns
        string_cols = df.select_dtypes(include=["object", "string"]).columns
        for col in string_cols:
            if col not in ["Order Date", "Ship Date"]:
                df[col] = df[col].astype(str).str.strip()

        # 4. Standardize Dates
        if "Order Date" in df.columns:
            orig_missing = df["Order Date"].isna().sum()
            df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
            new_missing = df["Order Date"].isna().sum() - orig_missing
            if new_missing > 0:
                actions.append(f"Flagged and coerced {new_missing} unparseable Order Dates to NaT.")
            # Drop records with completely missing Order Date (fundamental transaction anchor)
            if df["Order Date"].isna().sum() > 0:
                dropped = df["Order Date"].isna().sum()
                df = df.dropna(subset=["Order Date"]).reset_index(drop=True)
                actions.append(f"Dropped {dropped} records with unrecoverable missing Order Date.")

        if "Ship Date" in df.columns:
            df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")
            # If Ship Date is missing, default to Order Date (0-day fulfillment)
            missing_ship = df["Ship Date"].isna().sum()
            if missing_ship > 0:
                df["Ship Date"] = df["Ship Date"].fillna(df["Order Date"])
                actions.append(f"Imputed {missing_ship} missing Ship Dates using Order Date.")

            # Correct inconsistent dates (Ship Date < Order Date)
            inconsistent_mask = df["Ship Date"] < df["Order Date"]
            num_inconsistent = inconsistent_mask.sum()
            if num_inconsistent > 0:
                df.loc[inconsistent_mask, "Ship Date"] = df.loc[inconsistent_mask, "Order Date"]
                actions.append(f"Corrected {num_inconsistent} records where Ship Date was earlier than Order Date.")

        # 5. Type Casting and Cleaning Numeric Fields
        numeric_specs = {
            "Sales": (float, 0.0),
            "Profit": (float, 0.0),
            "Quantity": (int, 1),
            "Discount": (float, 0.0),
            "Shipping Cost": (float, 0.0),
        }

        for col, (target_type, default_val) in numeric_specs.items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default_val)
                if target_type == int:
                    df[col] = df[col].round().astype(int)
                else:
                    df[col] = df[col].round(2)

        # 5b. Explicit Exchange Rate Currency Scaling
        if self.exchange_rate != 1.0:
            monetary_fields = ["Sales", "Profit", "Shipping Cost"]
            converted_cols = []
            for m_col in monetary_fields:
                if m_col in df.columns:
                    df[m_col] = (df[m_col] * self.exchange_rate).round(2)
                    converted_cols.append(m_col)
            if converted_cols:
                actions.append(f"Applied currency conversion rate of {self.exchange_rate} to columns: {', '.join(converted_cols)}.")

        # 6. Flag & Sanitize Anomalous Business Values
        if "Sales" in df.columns:
            neg_sales = (df["Sales"] < 0).sum()
            if neg_sales > 0:
                # In retail POS, negative sales without return flags are data entry errors
                df["Sales"] = df["Sales"].apply(lambda x: abs(x) if x < 0 else x)
                actions.append(f"Sanitized {neg_sales} negative sales amounts to absolute values.")

        if "Discount" in df.columns:
            bad_discounts = ((df["Discount"] < 0) | (df["Discount"] > 1.0)).sum()
            if bad_discounts > 0:
                df["Discount"] = df["Discount"].clip(lower=0.0, upper=1.0)
                actions.append(f"Normalized {bad_discounts} discount rates to allowable range [0.0, 1.0].")

        # 7. Impute Missing Identifiers or Categoricals Safely
        categorical_defaults = {
            "Customer ID": "CUST-UNKNOWN",
            "Customer Name": "Anonymous Customer",
            "Segment": "Consumer",
            "Country": "United States",
            "Region": "East",
            "State": "Unknown State",
            "City": "Unknown City",
            "Category": "Office Supplies",
            "Sub-Category": "Binders",
            "Product Name": "General Merchandise",
        }
        for col, default_val in categorical_defaults.items():
            if col in df.columns and df[col].isna().sum() > 0:
                fill_count = df[col].isna().sum()
                df[col] = df[col].fillna(default_val)
                actions.append(f"Filled {fill_count} blank entries in '{col}' with '{default_val}'.")

        # 8. Add Business Analytics Derived Columns
        if "Order Date" in df.columns:
            df["Order_Year"] = df["Order Date"].dt.year
            df["Order_Month"] = df["Order Date"].dt.month
            df["Order_YearMonth"] = df["Order Date"].dt.strftime("%Y-%m")
            df["Order_Quarter"] = "Q" + df["Order Date"].dt.quarter.astype(str)
            df["Order_DayOfWeek"] = df["Order Date"].dt.day_name()

        if "Sales" in df.columns and "Profit" in df.columns:
            # Profit Margin = Profit / Sales (safely handling 0 sales)
            df["Profit_Margin_Pct"] = np.where(
                df["Sales"] > 0,
                np.round((df["Profit"] / df["Sales"]) * 100.0, 2),
                0.0
            )

        if "Order Date" in df.columns and "Ship Date" in df.columns:
            df["Shipping_Days"] = (df["Ship Date"] - df["Order Date"]).dt.days

        self.cleaned_df = df
        final_metrics = self.compute_quality_metrics(df)
        audit = CleaningAudit(
            original_metrics=initial_metrics,
            cleaned_metrics=final_metrics,
            actions_taken=actions,
            flagged_records_count=num_dupes + (new_missing if "new_missing" in locals() else 0)
        )
        return df, audit


def export_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Exports cleaned dataframe to CSV format in-memory bytes."""
    return df.to_csv(index=False).encode("utf-8")


def export_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Exports cleaned dataframe to Excel (.xlsx) format in-memory bytes."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Convert datetime columns to strings for universal Excel compatibility
        export_df = df.copy()
        for col in export_df.select_dtypes(include=["datetime64[ns]", "datetime64"]).columns:
            export_df[col] = export_df[col].dt.strftime("%Y-%m-%d")
        export_df.to_excel(writer, index=False, sheet_name="Cleaned_Sales_Data")
    return output.getvalue()
