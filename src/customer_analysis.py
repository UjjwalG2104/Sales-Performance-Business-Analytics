"""
SalesIQ — Customer Behavior & Segmentation Analytics Module.
Analyzes customer lifetime value proxies, segment economics, repeat purchase rates,
and provides interactive Plotly customer intelligence charts in INR (₹).
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.settings import PALETTE
from src.formatters import format_indian_number, format_inr


def get_top_customers(df: pd.DataFrame, top_n: int = 10, sort_by: str = "Sales") -> pd.DataFrame:
    """
    Computes top customers ranked by Sales or Profit,
    including order counts and average order value.
    """
    if df.empty or "Sales" not in df.columns:
        return pd.DataFrame()

    has_cust = "Customer ID" in df.columns or "Customer Name" in df.columns
    if not has_cust:
        return pd.DataFrame()

    group_cols = []
    if "Customer ID" in df.columns:
        group_cols.append("Customer ID")
    if "Customer Name" in df.columns:
        group_cols.append("Customer Name")
    if "Segment" in df.columns:
        group_cols.append("Segment")

    agg_dict = {"Total_Sales": ("Sales", "sum")}
    if "Profit" in df.columns:
        agg_dict["Total_Profit"] = ("Profit", "sum")
    if "Order ID" in df.columns:
        agg_dict["Order_Count"] = ("Order ID", "nunique")
    else:
        agg_dict["Order_Count"] = ("Sales", "count")
    if "Quantity" in df.columns:
        agg_dict["Units_Purchased"] = ("Quantity", "sum")

    cust_summary = df.groupby(group_cols).agg(**agg_dict).reset_index()

    if "Total_Profit" in cust_summary.columns:
        cust_summary["Profit_Margin_Pct"] = np.where(
            cust_summary["Total_Sales"] > 0,
            np.round((cust_summary["Total_Profit"] / cust_summary["Total_Sales"]) * 100.0, 2),
            0.0
        )

    cust_summary["AOV"] = np.where(
        cust_summary["Order_Count"] > 0,
        np.round(cust_summary["Total_Sales"] / cust_summary["Order_Count"], 2),
        0.0
    )

    sort_col = "Total_Sales"
    if sort_by.lower() == "profit" and "Total_Profit" in cust_summary.columns:
        sort_col = "Total_Profit"

    return cust_summary.sort_values(sort_col, ascending=False).head(top_n).reset_index(drop=True)


def get_segment_performance(df: pd.DataFrame, currency_symbol: str = "₹") -> Tuple[pd.DataFrame, go.Figure]:
    """Analyzes customer segments by sales volume, profit, margin, and average order value in INR."""
    if df.empty or "Segment" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame(), go.Figure()

    agg_dict = {
        "Total_Sales": ("Sales", "sum"),
        "Total_Orders": ("Order ID", "nunique") if "Order ID" in df.columns else ("Sales", "count")
    }
    if "Profit" in df.columns:
        agg_dict["Total_Profit"] = ("Profit", "sum")
    if "Customer ID" in df.columns:
        agg_dict["Total_Customers"] = ("Customer ID", "nunique")

    seg_df = df.groupby("Segment").agg(**agg_dict).reset_index()

    if "Total_Profit" in seg_df.columns:
        seg_df["Profit_Margin_Pct"] = np.where(
            seg_df["Total_Sales"] > 0,
            np.round((seg_df["Total_Profit"] / seg_df["Total_Sales"]) * 100.0, 2),
            0.0
        )

    seg_df["Average_Order_Value"] = np.where(
        seg_df["Total_Orders"] > 0,
        np.round(seg_df["Total_Sales"] / seg_df["Total_Orders"], 2),
        0.0
    )

    fig = px.bar(
        seg_df,
        x="Segment",
        y="Total_Sales",
        color="Segment",
        color_discrete_sequence=[PALETTE["primary"], PALETTE["secondary"], PALETTE["accent"]],
        title=f"<b>Sales Revenue by Customer Segment ({currency_symbol})</b>"
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(title=f"Revenue ({currency_symbol})", showgrid=True, gridcolor="#F1F5F9"),
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return seg_df, fig


def analyze_customer_repeat_behavior(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluates repeat customer behavior:
    Percentage of repeat vs one-time buyers, revenue share, and average orders per customer.
    """
    cust_col = "Customer ID" if "Customer ID" in df.columns else ("Customer Name" if "Customer Name" in df.columns else None)
    if df.empty or not cust_col or "Sales" not in df.columns:
        return {
            "total_customers": 0,
            "repeat_customers": 0,
            "repeat_rate_pct": 0.0,
            "repeat_revenue_pct": 0.0,
            "one_time_customers": 0,
            "chart": go.Figure()
        }

    order_col = "Order ID" if "Order ID" in df.columns else None
    if order_col:
        orders_per_cust = df.groupby(cust_col).agg(
            Order_Count=(order_col, "nunique"),
            Customer_Sales=("Sales", "sum")
        ).reset_index()
    else:
        orders_per_cust = df.groupby(cust_col).agg(
            Order_Count=("Sales", "count"),
            Customer_Sales=("Sales", "sum")
        ).reset_index()

    total_customers = len(orders_per_cust)
    repeat_mask = orders_per_cust["Order_Count"] > 1
    repeat_count = int(repeat_mask.sum())
    one_time_count = total_customers - repeat_count

    total_sales = df["Sales"].sum()
    repeat_sales = orders_per_cust.loc[repeat_mask, "Customer_Sales"].sum()

    repeat_rate = round((repeat_count / total_customers) * 100.0, 1) if total_customers > 0 else 0.0
    repeat_rev_share = round((repeat_sales / total_sales) * 100.0, 1) if total_sales > 0 else 0.0

    # Donut chart
    fig = go.Figure(data=[go.Pie(
        labels=["Repeat Buyers (2+ Orders)", "One-Time Buyers (1 Order)"],
        values=[repeat_count, one_time_count],
        hole=0.6,
        marker=dict(colors=[PALETTE["secondary"], "#CBD5E1"]),
        textinfo="label+percent",
        hoverinfo="label+value+percent"
    )])
    fig.update_layout(
        title="<b>Customer Retention & Repeat Cohort Breakdown</b>",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=20)
    )

    return {
        "total_customers": total_customers,
        "repeat_customers": repeat_count,
        "repeat_rate_pct": repeat_rate,
        "repeat_revenue_pct": repeat_rev_share,
        "one_time_customers": one_time_count,
        "chart": fig
    }
