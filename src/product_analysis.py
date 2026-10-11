"""
SalesIQ — Product Portfolio & Margin Diagnostics Module.
Identifies best sellers, margin diluters, loss leaders,
and category/sub-category profitability matrices with INR (₹) formatting.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.settings import PALETTE
from src.formatters import format_indian_number, format_inr


def get_product_performance_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates sales, profit, quantity, and margins at the product level."""
    if df.empty or "Sales" not in df.columns:
        return pd.DataFrame()

    has_prod = "Product Name" in df.columns or "Product ID" in df.columns
    if not has_prod:
        return pd.DataFrame()

    prod_col = "Product Name" if "Product Name" in df.columns else "Product ID"
    group_cols = [prod_col]
    if "Category" in df.columns:
        group_cols.append("Category")
    if "Sub-Category" in df.columns:
        group_cols.append("Sub-Category")

    agg_dict = {"Total_Sales": ("Sales", "sum")}
    if "Profit" in df.columns:
        agg_dict["Total_Profit"] = ("Profit", "sum")
    if "Quantity" in df.columns:
        agg_dict["Total_Quantity"] = ("Quantity", "sum")
    if "Discount" in df.columns:
        agg_dict["Avg_Discount"] = ("Discount", "mean")
    if "Order ID" in df.columns:
        agg_dict["Order_Count"] = ("Order ID", "nunique")

    prod_summary = df.groupby(group_cols).agg(**agg_dict).reset_index()

    if "Total_Profit" in prod_summary.columns:
        prod_summary["Profit_Margin_Pct"] = np.where(
            prod_summary["Total_Sales"] > 0,
            np.round((prod_summary["Total_Profit"] / prod_summary["Total_Sales"]) * 100.0, 2),
            0.0
        )
    if "Avg_Discount" in prod_summary.columns:
        prod_summary["Avg_Discount_Pct"] = np.round(prod_summary["Avg_Discount"] * 100.0, 1)

    return prod_summary


def get_top_performing_products(df: pd.DataFrame, metric: str = "Sales", top_n: int = 10) -> pd.DataFrame:
    """Returns top N products ranked by Sales or Profit."""
    summary = get_product_performance_summary(df)
    if summary.empty:
        return pd.DataFrame()

    sort_col = "Total_Sales"
    if metric.lower() == "profit" and "Total_Profit" in summary.columns:
        sort_col = "Total_Profit"

    return summary.sort_values(sort_col, ascending=False).head(top_n).reset_index(drop=True)


def get_loss_generating_products(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Identifies products operating at a cumulative net loss."""
    summary = get_product_performance_summary(df)
    if summary.empty or "Total_Profit" not in summary.columns:
        return pd.DataFrame()

    loss_makers = summary[summary["Total_Profit"] < 0].sort_values("Total_Profit", ascending=True)
    return loss_makers.head(top_n).reset_index(drop=True)


def get_high_revenue_low_profit_products(
    df: pd.DataFrame,
    min_sales_percentile: float = 0.70,
    max_margin_pct: float = 5.0
) -> pd.DataFrame:
    """
    Identifies high-revenue products with anemic or negative margins (< 5%).
    """
    summary = get_product_performance_summary(df)
    if summary.empty or "Total_Profit" not in summary.columns or "Profit_Margin_Pct" not in summary.columns:
        return pd.DataFrame()

    sales_threshold = summary["Total_Sales"].quantile(min_sales_percentile)
    diluters = summary[
        (summary["Total_Sales"] >= sales_threshold) &
        (summary["Profit_Margin_Pct"] < max_margin_pct)
    ].sort_values("Total_Sales", ascending=False)

    return diluters.reset_index(drop=True)


def create_product_quadrant_scatter(df: pd.DataFrame, currency_symbol: str = "₹") -> go.Figure:
    """
    Creates a Sales vs Profit quadrant scatter chart highlighting
    Stars, Cash Cows, Question Marks, and Loss Leaders in INR.
    """
    summary = get_product_performance_summary(df)
    if summary.empty:
        fig = go.Figure()
        fig.update_layout(title="Product data not available in the active dataset")
        return fig

    has_profit = "Total_Profit" in summary.columns
    prod_name_col = "Product Name" if "Product Name" in summary.columns else (
        "Product ID" if "Product ID" in summary.columns else summary.columns[0]
    )

    if not has_profit:
        # Fallback to Sales distribution bar or scatter against Quantity
        y_col = "Total_Quantity" if "Total_Quantity" in summary.columns else "Total_Sales"
        fig = px.bar(
            summary.sort_values("Total_Sales", ascending=False).head(20),
            x=prod_name_col,
            y="Total_Sales",
            title=f"<b>Top Products by Sales ({currency_symbol})</b>",
            color_discrete_sequence=[PALETTE["primary"]]
        )
        fig.update_layout(
            xaxis=dict(tickangle=45),
            yaxis=dict(title=f"Total Sales ({currency_symbol})"),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        return fig

    color_col = "Category" if "Category" in summary.columns else None
    size_col = "Total_Quantity" if "Total_Quantity" in summary.columns else None

    hover_data = {"Total_Sales": f":{currency_symbol},.2f", "Total_Profit": f":{currency_symbol},.2f"}
    if "Profit_Margin_Pct" in summary.columns:
        hover_data["Profit_Margin_Pct"] = ":.1f%"

    fig = px.scatter(
        summary,
        x="Total_Sales",
        y="Total_Profit",
        color=color_col,
        size=size_col,
        hover_name=prod_name_col,
        hover_data=hover_data,
        title=f"<b>Product Portfolio Matrix: Sales vs Profitability ({currency_symbol})</b>",
        labels={"Total_Sales": f"Revenue ({currency_symbol})", "Total_Profit": f"Net Profit ({currency_symbol})"}
    )

    fig.add_hline(y=0, line_dash="dash", line_color=PALETTE["danger"], annotation_text="Break-even Profit Line")
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig
