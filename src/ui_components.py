"""
SalesIQ — Shared UI Components and Layout Helpers.
Renders consistent Enterprise BI KPI cards, styled badges, dynamic sidebar filters,
and injects stylesheet tokens with Indian Rupee (INR) formatting.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st

from config.settings import ASSETS_DIR, PALETTE
from src.formatters import format_indian_number, format_inr
from src.kpi_calculator import KPISnapshot


def load_custom_css():
    """Injects custom enterprise CSS into the active Streamlit app."""
    css_file = ASSETS_DIR / "style.css"
    if css_file.exists():
        st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_kpi_metric_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    delta_type: str = "neutral",
    subtext: str = ""
):
    """Renders a single styled KPI card container."""
    delta_html = ""
    if delta:
        css_class = f"kpi-delta-{delta_type}"
        delta_html = f"<div class='{css_class}'>{delta} <span style='font-size:0.75rem; color:#64748B;'>{subtext}</span></div>"

    card_html = f"""
    <div class="kpi-container">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_kpi_dashboard(kpis: KPISnapshot, currency_symbol: str = "₹"):
    """
    Renders the 8 mandatory KPI cards in an organized 4x2 responsive grid
    using Indian Rupee (INR) formatting and handling missing columns gracefully.
    """
    row1_c1, row1_c2, row1_c3, row1_c4 = st.columns(4)

    # 1. Total Revenue
    with row1_c1:
        rev_str = format_inr(kpis.total_revenue, symbol=currency_symbol)
        rev_delta = f"{kpis.revenue_growth_pct:+.1f}%" if kpis.revenue_growth_pct is not None else "Baseline"
        rev_delta_type = "positive" if (kpis.revenue_growth_pct or 0) >= 0 else "negative"
        render_kpi_metric_card("Total Revenue", rev_str, rev_delta, rev_delta_type, "vs prior period" if kpis.has_dates else "active data")

    # 2. Total Profit
    with row1_c2:
        if kpis.has_profit and kpis.total_profit is not None:
            prof_str = format_inr(kpis.total_profit, symbol=currency_symbol)
            prof_delta = f"{kpis.profit_growth_pct:+.1f}%" if kpis.profit_growth_pct is not None else "Baseline"
            prof_delta_type = "positive" if (kpis.profit_growth_pct or 0) >= 0 else "negative"
            render_kpi_metric_card("Total Profit", prof_str, prof_delta, prof_delta_type, "net operating profit")
        else:
            render_kpi_metric_card("Total Profit", "Not Available", "—", "neutral", "profit column absent")

    # 3. Profit Margin
    with row1_c3:
        if kpis.has_profit and kpis.profit_margin_pct is not None:
            margin_str = f"{kpis.profit_margin_pct:.1f}%"
            margin_delta_type = "positive" if kpis.profit_margin_pct >= 12.0 else ("warning" if kpis.profit_margin_pct > 0 else "negative")
            render_kpi_metric_card("Profit Margin", margin_str, "Benchmark: 12%+", margin_delta_type, "net margin")
        else:
            render_kpi_metric_card("Profit Margin", "Not Available", "—", "neutral", "requires profit data")

    # 4. Total Orders
    with row1_c4:
        orders_str = format_indian_number(kpis.total_orders)
        if kpis.has_orders:
            units_subtext = f"{format_indian_number(kpis.units_sold)} items" if kpis.has_quantity and kpis.units_sold is not None else "orders count"
            render_kpi_metric_card("Total Orders", orders_str, units_subtext, "neutral", "distinct purchases")
        else:
            render_kpi_metric_card("Total Orders (Rows)", orders_str, "Line items", "neutral", "no Order ID present")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    row2_c1, row2_c2, row2_c3, row2_c4 = st.columns(4)

    # 5. Units Sold
    with row2_c1:
        if kpis.has_quantity and kpis.units_sold is not None:
            units_str = format_indian_number(kpis.units_sold)
            render_kpi_metric_card("Units Sold", units_str, f"{format_indian_number(kpis.total_orders)} orders", "neutral", "cumulative volume")
        else:
            render_kpi_metric_card("Units Sold", "Not Available", "—", "neutral", "quantity column absent")

    # 6. Average Order Value (AOV)
    with row2_c2:
        if kpis.average_order_value is not None:
            aov_str = format_inr(kpis.average_order_value, symbol=currency_symbol)
            aov_subtext = "per distinct order" if kpis.has_orders else "per transaction row"
            render_kpi_metric_card("Avg Order Value (AOV)", aov_str, "Basket Size", "neutral", aov_subtext)
        else:
            render_kpi_metric_card("Avg Order Value (AOV)", "Not Available", "—", "neutral", "sales absent")

    # 7. Revenue Growth
    with row2_c3:
        if kpis.has_dates and kpis.revenue_growth_pct is not None:
            rev_g_str = f"{kpis.revenue_growth_pct:+.1f}%"
            g_type = "positive" if kpis.revenue_growth_pct >= 0 else "negative"
            render_kpi_metric_card("Revenue Growth", rev_g_str, "Period Comparison", g_type, "half-over-half")
        else:
            render_kpi_metric_card("Revenue Growth", "Not Available", "—", "neutral", "date range required")

    # 8. Profit Growth
    with row2_c4:
        if kpis.has_profit and kpis.has_dates and kpis.profit_growth_pct is not None:
            prof_g_str = f"{kpis.profit_growth_pct:+.1f}%"
            pg_type = "positive" if kpis.profit_growth_pct >= 0 else "negative"
            loss_sub = f"{kpis.loss_making_orders_pct:.1f}% loss orders" if kpis.loss_making_orders_pct is not None else ""
            render_kpi_metric_card("Profit Growth", prof_g_str, loss_sub, pg_type, "half-over-half")
        else:
            render_kpi_metric_card("Profit Growth", "Not Available", "—", "neutral", "profit/dates absent")


def apply_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renders dynamic interactive sidebar filters adapting only to available columns.
    Returns the filtered dataframe.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    st.sidebar.markdown("### 🔍 Global Filters")
    filtered_df = df.copy()

    # 1. Date Range Filter
    if "Order Date" in filtered_df.columns:
        filtered_df["Order Date"] = pd.to_datetime(filtered_df["Order Date"], errors="coerce")
        valid_dates = filtered_df["Order Date"].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            if min_date <= max_date:
                date_selection = st.sidebar.date_input(
                    "Order Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="filter_date_range"
                )
                if isinstance(date_selection, (tuple, list)) and len(date_selection) == 2:
                    start_d, end_d = date_selection
                    filtered_df = filtered_df[
                        (filtered_df["Order Date"].dt.date >= start_d) &
                        (filtered_df["Order Date"].dt.date <= end_d)
                    ]

    # 2. Region Filter
    if "Region" in filtered_df.columns:
        all_regions = sorted([str(r) for r in filtered_df["Region"].dropna().unique().tolist() if str(r).strip()])
        if all_regions:
            selected_regions = st.sidebar.multiselect("Region", options=all_regions, default=all_regions, key="filter_region")
            if selected_regions:
                filtered_df = filtered_df[filtered_df["Region"].isin(selected_regions)]

    # 3. State Filter (Cascaded)
    if "State" in filtered_df.columns:
        available_states = sorted([str(s) for s in filtered_df["State"].dropna().unique().tolist() if str(s).strip()])
        if available_states:
            selected_states = st.sidebar.multiselect("State", options=available_states, default=[], placeholder="All States", key="filter_state")
            if selected_states:
                filtered_df = filtered_df[filtered_df["State"].isin(selected_states)]

    # 4. Category Filter
    if "Category" in filtered_df.columns:
        all_categories = sorted([str(c) for c in filtered_df["Category"].dropna().unique().tolist() if str(c).strip()])
        if all_categories:
            selected_categories = st.sidebar.multiselect("Category", options=all_categories, default=all_categories, key="filter_category")
            if selected_categories:
                filtered_df = filtered_df[filtered_df["Category"].isin(selected_categories)]

    # 5. Sub-Category Filter (Cascaded)
    if "Sub-Category" in filtered_df.columns:
        available_subcats = sorted([str(sc) for sc in filtered_df["Sub-Category"].dropna().unique().tolist() if str(sc).strip()])
        if available_subcats:
            selected_subcats = st.sidebar.multiselect("Sub-Category", options=available_subcats, default=[], placeholder="All Sub-Categories", key="filter_subcat")
            if selected_subcats:
                filtered_df = filtered_df[filtered_df["Sub-Category"].isin(selected_subcats)]

    # 6. Customer Segment Filter
    if "Segment" in filtered_df.columns:
        all_segments = sorted([str(seg) for seg in filtered_df["Segment"].dropna().unique().tolist() if str(seg).strip()])
        if all_segments:
            selected_segments = st.sidebar.multiselect("Customer Segment", options=all_segments, default=all_segments, key="filter_segment")
            if selected_segments:
                filtered_df = filtered_df[filtered_df["Segment"].isin(selected_segments)]

    st.sidebar.markdown(f"**Records Matched:** `{format_indian_number(len(filtered_df))}` / `{format_indian_number(len(df))}`")
    st.sidebar.divider()
    return filtered_df
