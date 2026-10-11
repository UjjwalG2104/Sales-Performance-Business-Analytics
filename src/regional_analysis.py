"""
SalesIQ — Regional & Geographic Performance Analytics Module.
Calculates region and state sales, profitability, margin profiles,
and renders Plotly geographic choropleth maps and regional comparisons in INR (₹).
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.settings import PALETTE
from src.formatters import format_indian_number, format_inr

# US State Name to 2-letter Postal Code Mapping
STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}


def get_regional_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates revenue, profit, orders, and margin across geographic regions."""
    if df.empty or "Sales" not in df.columns:
        return pd.DataFrame()

    loc_col = "Region" if "Region" in df.columns else ("State" if "State" in df.columns else ("City" if "City" in df.columns else None))
    if not loc_col:
        return pd.DataFrame()

    agg_dict = {
        "Total_Sales": ("Sales", "sum"),
        "Total_Orders": ("Order ID", "nunique") if "Order ID" in df.columns else ("Sales", "count")
    }
    if "Profit" in df.columns:
        agg_dict["Total_Profit"] = ("Profit", "sum")
    if "Quantity" in df.columns:
        agg_dict["Total_Quantity"] = ("Quantity", "sum")

    reg_df = df.groupby(loc_col).agg(**agg_dict).reset_index()
    if loc_col != "Region":
        reg_df = reg_df.rename(columns={loc_col: "Region"})

    if "Total_Profit" in reg_df.columns:
        reg_df["Profit_Margin_Pct"] = np.where(
            reg_df["Total_Sales"] > 0,
            np.round((reg_df["Total_Profit"] / reg_df["Total_Sales"]) * 100.0, 2),
            0.0
        )
    reg_df["AOV"] = np.where(
        reg_df["Total_Orders"] > 0,
        np.round(reg_df["Total_Sales"] / reg_df["Total_Orders"], 2),
        0.0
    )

    return reg_df.sort_values("Total_Sales", ascending=False).reset_index(drop=True)


def get_state_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates performance metrics at the individual State level."""
    if df.empty or "Sales" not in df.columns:
        return pd.DataFrame()

    state_col = "State" if "State" in df.columns else ("City" if "City" in df.columns else ("Region" if "Region" in df.columns else None))
    if not state_col:
        return pd.DataFrame()

    group_cols = [state_col]
    if "Region" in df.columns and state_col != "Region":
        group_cols.append("Region")

    agg_dict = {
        "Total_Sales": ("Sales", "sum"),
        "Total_Orders": ("Order ID", "nunique") if "Order ID" in df.columns else ("Sales", "count")
    }
    if "Profit" in df.columns:
        agg_dict["Total_Profit"] = ("Profit", "sum")
    if "Discount" in df.columns:
        agg_dict["Avg_Discount"] = ("Discount", "mean")

    state_df = df.groupby(group_cols).agg(**agg_dict).reset_index()
    if state_col != "State":
        state_df = state_df.rename(columns={state_col: "State"})

    if "Total_Profit" in state_df.columns:
        state_df["Profit_Margin_Pct"] = np.where(
            state_df["Total_Sales"] > 0,
            np.round((state_df["Total_Profit"] / state_df["Total_Sales"]) * 100.0, 2),
            0.0
        )
    state_df["State_Code"] = state_df["State"].map(STATE_ABBR).fillna("")

    return state_df.sort_values("Total_Sales", ascending=False).reset_index(drop=True)


def create_regional_comparison_chart(reg_df: pd.DataFrame, currency_symbol: str = "₹") -> go.Figure:
    """Renders grouped bar chart comparing Regional Revenue and Profit in INR."""
    if reg_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Regional data not available")
        return fig

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=reg_df["Region"],
        y=reg_df["Total_Sales"],
        name=f"Sales Revenue ({currency_symbol})",
        marker_color=PALETTE["secondary"],
        hovertemplate=f"<b>%{{x}}</b><br>Sales: {currency_symbol}%{{y:,.2f}}<extra></extra>"
    ))

    if "Total_Profit" in reg_df.columns:
        fig.add_trace(go.Bar(
            x=reg_df["Region"],
            y=reg_df["Total_Profit"],
            name=f"Net Profit ({currency_symbol})",
            marker_color=PALETTE["accent"],
            hovertemplate=f"<b>%{{x}}</b><br>Profit: {currency_symbol}%{{y:,.2f}}<extra></extra>"
        ))

    fig.update_layout(
        title=f"<b>Geographic Performance: Sales Revenue vs. Net Profit ({currency_symbol})</b>",
        barmode="group",
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(title=f"Amount ({currency_symbol})", showgrid=True, gridcolor="#F1F5F9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def create_us_state_choropleth(state_df: pd.DataFrame, metric: str = "Total_Sales", currency_symbol: str = "₹") -> go.Figure:
    """Renders interactive US State choropleth map, or territorial horizontal bar chart if non-US."""
    if state_df.empty:
        return go.Figure()

    # Check if we have valid US state codes
    has_valid_us_codes = "State_Code" in state_df.columns and (state_df["State_Code"] != "").sum() > 3

    if has_valid_us_codes:
        is_sales = metric == "Total_Sales"
        title_text = f"<b>U.S. State Sales Revenue Distribution ({currency_symbol})</b>" if is_sales else f"<b>U.S. State Net Profit Distribution ({currency_symbol})</b>"
        color_scale = "Blues" if is_sales else "Teal"

        hover_data = {"Total_Sales": f":{currency_symbol},.2f", "State_Code": False}
        if "Total_Profit" in state_df.columns:
            hover_data["Total_Profit"] = f":{currency_symbol},.2f"
        if "Profit_Margin_Pct" in state_df.columns:
            hover_data["Profit_Margin_Pct"] = ":.1f%"

        fig = px.choropleth(
            state_df,
            locations="State_Code",
            locationmode="USA-states",
            color=metric if metric in state_df.columns else "Total_Sales",
            scope="usa",
            hover_name="State",
            hover_data=hover_data,
            color_continuous_scale=color_scale,
            title=title_text
        )
        fig.update_layout(
            geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="#F1F5F9"),
            margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        return fig
    else:
        # Fallback to horizontal ranking bar chart
        top_states = state_df.sort_values(metric if metric in state_df.columns else "Total_Sales", ascending=False).head(15)
        fig = px.bar(
            top_states,
            x=metric if metric in state_df.columns else "Total_Sales",
            y="State",
            orientation="h",
            title=f"<b>Territory Performance: {metric} ({currency_symbol})</b>",
            color_discrete_sequence=[PALETTE["secondary"]]
        )
        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=40, r=40, t=50, b=40)
        )
        return fig
