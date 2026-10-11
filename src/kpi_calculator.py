"""
SalesIQ — KPI Calculator Engine.
Computes dynamic business metrics with safe zero handling, distinct order semantics,
and rigorous period-over-period comparison algorithms.
Adapts safely to partial schemas when optional columns are absent.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class KPISnapshot:
    total_revenue: float = 0.0
    total_profit: Optional[float] = None
    profit_margin_pct: Optional[float] = None
    total_orders: int = 0
    units_sold: Optional[int] = None
    average_order_value: Optional[float] = None
    revenue_growth_pct: Optional[float] = None
    profit_growth_pct: Optional[float] = None
    avg_discount_pct: Optional[float] = None
    loss_making_orders_pct: Optional[float] = None
    has_profit: bool = True
    has_orders: bool = True
    has_quantity: bool = True
    has_dates: bool = True


class KPICalculator:
    """
    Computes financial and operational KPIs from the active filtered sales dataset.
    """

    @staticmethod
    def calculate_kpis(df: pd.DataFrame, prior_df: Optional[pd.DataFrame] = None) -> KPISnapshot:
        """
        Calculates all core KPIs from the active dataset.
        If prior_df is provided, calculates period-over-period growth for revenue and profit.
        Gracefully handles missing optional columns (Profit, Quantity, Order ID, Discount).
        """
        if df is None or df.empty:
            return KPISnapshot(
                total_revenue=0.0,
                total_profit=0.0,
                profit_margin_pct=0.0,
                total_orders=0,
                units_sold=0,
                average_order_value=0.0,
                has_profit=False,
                has_orders=False,
                has_quantity=False,
                has_dates=False
            )

        # Core Revenue (Mandatory)
        total_revenue = float(df["Sales"].sum()) if "Sales" in df.columns else 0.0

        # Presence Flags
        has_profit = "Profit" in df.columns
        has_orders = "Order ID" in df.columns
        has_quantity = "Quantity" in df.columns
        has_dates = "Order Date" in df.columns

        # Profit & Margin
        if has_profit:
            total_profit = round(float(df["Profit"].sum()), 2)
            profit_margin_pct = (
                round((total_profit / total_revenue) * 100.0, 2)
                if total_revenue > 0
                else 0.0
            )
        else:
            total_profit = None
            profit_margin_pct = None

        # Distinct Orders & AOV
        if has_orders:
            total_orders = int(df["Order ID"].nunique())
            aov = (
                round(total_revenue / total_orders, 2)
                if total_orders > 0
                else 0.0
            )
        else:
            total_orders = len(df)
            aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

        # Units Sold
        units_sold = int(df["Quantity"].sum()) if has_quantity else None

        # Average Discount
        avg_discount = (
            round(float(df["Discount"].mean()) * 100.0, 2)
            if "Discount" in df.columns
            else None
        )

        # Loss-making order share
        loss_pct = None
        if has_profit and has_orders:
            order_profits = df.groupby("Order ID")["Profit"].sum()
            loss_orders = (order_profits < 0).sum()
            loss_pct = round((loss_orders / total_orders) * 100.0, 1) if total_orders > 0 else 0.0
        elif has_profit:
            loss_orders = (df["Profit"] < 0).sum()
            loss_pct = round((loss_orders / len(df)) * 100.0, 1) if len(df) > 0 else 0.0

        # Period-over-period Growth Calculations
        rev_growth = None
        prof_growth = None

        if prior_df is not None and not prior_df.empty:
            prior_rev = float(prior_df["Sales"].sum()) if "Sales" in prior_df.columns else 0.0
            if prior_rev > 0:
                rev_growth = round(((total_revenue - prior_rev) / prior_rev) * 100.0, 2)
            elif prior_rev == 0 and total_revenue > 0:
                rev_growth = 100.0

            if has_profit and "Profit" in prior_df.columns and total_profit is not None:
                prior_prof = float(prior_df["Profit"].sum())
                if prior_prof != 0:
                    prof_growth = round(((total_profit - prior_prof) / abs(prior_prof)) * 100.0, 2)
                elif prior_prof == 0 and total_profit > 0:
                    prof_growth = 100.0

        return KPISnapshot(
            total_revenue=round(total_revenue, 2),
            total_profit=total_profit,
            profit_margin_pct=profit_margin_pct,
            total_orders=total_orders,
            units_sold=units_sold,
            average_order_value=aov,
            revenue_growth_pct=rev_growth,
            profit_growth_pct=prof_growth,
            avg_discount_pct=avg_discount,
            loss_making_orders_pct=loss_pct,
            has_profit=has_profit,
            has_orders=has_orders,
            has_quantity=has_quantity,
            has_dates=has_dates
        )

    @staticmethod
    def get_period_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Splits dataset chronologically into current vs prior equivalent periods
        for growth comparison.
        """
        if df is None or df.empty or "Order Date" not in df.columns:
            return pd.DataFrame(), pd.DataFrame()

        sorted_df = df.sort_values("Order Date")
        min_date = sorted_df["Order Date"].min()
        max_date = sorted_df["Order Date"].max()

        if pd.isna(min_date) or pd.isna(max_date):
            return df, pd.DataFrame()

        total_days = (max_date - min_date).days
        if total_days < 2:
            return df, pd.DataFrame()

        half_point = min_date + pd.Timedelta(days=total_days // 2)
        prior_period = sorted_df[sorted_df["Order Date"] < half_point]
        current_period = sorted_df[sorted_df["Order Date"] >= half_point]

        return current_period, prior_period
