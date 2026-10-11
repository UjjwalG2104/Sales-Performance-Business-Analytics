"""
SalesIQ — Sales & Revenue Analytics Module.
Calculates time series aggregations, discount elasticity, category distributions,
and produces high-resolution Plotly interactive visualizations with INR (₹) formatting.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.settings import CHART_COLORWAY, PALETTE
from src.formatters import format_indian_number, format_inr


def get_monthly_sales_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates sales, profit, quantity, and margins by calendar month."""
    if df.empty or "Order Date" not in df.columns:
        return pd.DataFrame()

    temp = df.copy()
    temp["Order Date"] = pd.to_datetime(temp["Order Date"], errors="coerce")
    temp = temp.dropna(subset=["Order Date"])
    if temp.empty:
        return pd.DataFrame()

    temp["YearMonth"] = temp["Order Date"].dt.to_period("M").dt.to_timestamp()
    
    agg_dict = {"Revenue": ("Sales", "sum")}
    if "Profit" in temp.columns:
        agg_dict["Profit"] = ("Profit", "sum")
    if "Order ID" in temp.columns:
        agg_dict["Orders"] = ("Order ID", "nunique")
    else:
        agg_dict["Orders"] = ("Sales", "count")
    if "Quantity" in temp.columns:
        agg_dict["Units"] = ("Quantity", "sum")

    monthly = temp.groupby("YearMonth").agg(**agg_dict).reset_index()

    if "Profit" in monthly.columns:
        monthly["Profit_Margin_Pct"] = np.where(
            monthly["Revenue"] > 0,
            np.round((monthly["Profit"] / monthly["Revenue"]) * 100.0, 2),
            0.0
        )
        monthly["MoM_Profit_Growth"] = np.round(monthly["Profit"].pct_change() * 100.0, 2)

    monthly["MoM_Revenue_Growth"] = np.round(monthly["Revenue"].pct_change() * 100.0, 2)
    return monthly


def create_revenue_profit_trend_chart(monthly_df: pd.DataFrame, currency_symbol: str = "₹") -> go.Figure:
    """Creates a dual-axis interactive trend chart for Monthly Revenue and Profit in INR."""
    if monthly_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No time-series date data available for monthly trends")
        return fig

    fig = go.Figure()

    # Revenue Bar
    fig.add_trace(go.Bar(
        x=monthly_df["YearMonth"],
        y=monthly_df["Revenue"],
        name=f"Revenue ({currency_symbol})",
        marker_color=PALETTE["secondary"],
        opacity=0.85,
        hovertemplate=f"<b>%{{x|%b %Y}}</b><br>Revenue: {currency_symbol}%{{y:,.2f}}<extra></extra>"
    ))

    # Profit Line if available
    if "Profit" in monthly_df.columns:
        fig.add_trace(go.Scatter(
            x=monthly_df["YearMonth"],
            y=monthly_df["Profit"],
            name=f"Profit ({currency_symbol})",
            mode="lines+markers",
            line=dict(color=PALETTE["accent"], width=3),
            marker=dict(size=6, color=PALETTE["primary"]),
            hovertemplate=f"<b>%{{x|%b %Y}}</b><br>Profit: {currency_symbol}%{{y:,.2f}}<extra></extra>"
        ))

    fig.update_layout(
        title="<b>Monthly Revenue vs. Profit Performance</b>",
        title_font=dict(size=16, color=PALETTE["text_dark"]),
        xaxis=dict(title="Month", showgrid=False),
        yaxis=dict(title=f"Amount ({currency_symbol})", showgrid=True, gridcolor="#F1F5F9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def get_yoy_growth_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates Year-Over-Year growth by Month and Quarter."""
    if df.empty or "Order Date" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()

    temp = df.copy()
    temp["Order Date"] = pd.to_datetime(temp["Order Date"], errors="coerce")
    temp = temp.dropna(subset=["Order Date"])
    if temp.empty:
        return pd.DataFrame()

    temp["Year"] = temp["Order Date"].dt.year
    temp["Month_Num"] = temp["Order Date"].dt.month
    temp["Month_Name"] = temp["Order Date"].dt.strftime("%b")

    years = sorted(temp["Year"].unique())
    if len(years) < 2:
        return pd.DataFrame()

    pivot_rev = temp.pivot_table(
        index=["Month_Num", "Month_Name"],
        columns="Year",
        values="Sales",
        aggfunc="sum"
    ).fillna(0)

    pivot_rev.columns = [f"Sales_{y}" for y in pivot_rev.columns]
    pivot_rev = pivot_rev.reset_index().sort_values("Month_Num")
    return pivot_rev


def create_category_sunburst(df: pd.DataFrame, currency_symbol: str = "₹") -> go.Figure:
    """Creates a hierarchical breakdown of Sales across Category and Sub-Category."""
    if df.empty or "Category" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="Category data not present in active dataset")
        return fig

    has_subcat = "Sub-Category" in df.columns
    has_profit = "Profit" in df.columns

    group_cols = ["Category", "Sub-Category"] if has_subcat else ["Category"]
    agg_dict = {"Sales": ("Sales", "sum")}
    if has_profit:
        agg_dict["Profit"] = ("Profit", "sum")

    cat_df = df.groupby(group_cols).agg(**agg_dict).reset_index()

    path_cols = ["Category", "Sub-Category"] if has_subcat else ["Category"]
    color_col = "Profit" if has_profit else "Sales"

    fig = px.sunburst(
        cat_df,
        path=path_cols,
        values="Sales",
        color=color_col,
        color_continuous_scale="Tealgrn" if has_profit else "Blues",
        title="<b>Product Hierarchy: Sales & Profitability Distribution</b>",
    )
    fig.update_layout(
        margin=dict(t=50, l=10, r=10, b=10),
        coloraxis_colorbar=dict(title=f"{color_col} ({currency_symbol})")
    )
    return fig


def analyze_discount_impact(df: pd.DataFrame, currency_symbol: str = "₹") -> Tuple[pd.DataFrame, go.Figure]:
    """
    Groups transactions by discount tiers to evaluate margin erosion
    and toxic discounting patterns.
    """
    if df.empty or "Discount" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame(), go.Figure()

    has_profit = "Profit" in df.columns
    temp = df.copy()
    bins = [-0.01, 0.0, 0.10, 0.20, 0.30, 0.50, 1.0]
    labels = ["0% (No Discount)", "1% - 10%", "11% - 20%", "21% - 30%", "31% - 50%", "> 50% (Deep Discount)"]
    temp["Discount_Tier"] = pd.cut(temp["Discount"], bins=bins, labels=labels)

    agg_dict = {
        "Total_Sales": ("Sales", "sum"),
        "Order_Count": ("Sales", "count")
    }
    if has_profit:
        agg_dict["Total_Profit"] = ("Profit", "sum")
        if "Profit_Margin_Pct" in temp.columns:
            agg_dict["Avg_Profit_Margin"] = ("Profit_Margin_Pct", "mean")

    tier_summary = temp.groupby("Discount_Tier", observed=False).agg(**agg_dict).reset_index()

    if has_profit:
        tier_summary["Overall_Margin_Pct"] = np.where(
            tier_summary["Total_Sales"] > 0,
            np.round((tier_summary["Total_Profit"] / tier_summary["Total_Sales"]) * 100.0, 2),
            0.0
        )

    # Visualization
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=tier_summary["Discount_Tier"],
        y=tier_summary["Total_Sales"],
        name=f"Total Sales ({currency_symbol})",
        marker_color=PALETTE["secondary"],
        yaxis="y"
    ))

    if has_profit:
        fig.add_trace(go.Scatter(
            x=tier_summary["Discount_Tier"],
            y=tier_summary["Overall_Margin_Pct"],
            name="Profit Margin (%)",
            marker=dict(color=PALETTE["danger"], size=8),
            line=dict(color=PALETTE["danger"], width=3),
            yaxis="y2"
        ))
        fig.update_layout(
            yaxis2=dict(
                title="Profit Margin (%)",
                overlaying="y",
                side="right",
                showgrid=False
            )
        )

    fig.update_layout(
        title="<b>Discount Impact on Sales Volume & Profitability</b>",
        title_font=dict(size=16, color=PALETTE["text_dark"]),
        xaxis=dict(title="Discount Bracket"),
        yaxis=dict(title=f"Sales ({currency_symbol})", showgrid=True, gridcolor="#F1F5F9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return tier_summary, fig
