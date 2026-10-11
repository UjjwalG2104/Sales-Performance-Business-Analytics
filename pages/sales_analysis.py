"""
SalesIQ — Sales & Revenue Analysis Page.
"""
import pandas as pd
import streamlit as st
from src.state_manager import initialize_app_state, load_sample_dataset
from src.kpi_calculator import KPICalculator
from src.sales_analysis import (
    analyze_discount_impact,
    create_revenue_profit_trend_chart,
    get_monthly_sales_trend,
    get_yoy_growth_analysis,
)
from src.ui_components import apply_sidebar_filters, load_custom_css, render_kpi_dashboard
from src.formatters import format_inr

load_custom_css()
initialize_app_state()

if not st.session_state.get("dataset_active"):
    st.warning("⚠️ No dataset is currently loaded. Please visit the Home / Executive Overview page to upload your file.")
    if st.button("🚀 Load Sample Dataset for Demo", type="primary"):
        load_sample_dataset()
        st.rerun()
    st.stop()

curr_sym = st.session_state.get("currency_symbol", "₹")
st.markdown("## 💰 In-Depth Sales & Revenue Analysis")
filtered_df = apply_sidebar_filters(st.session_state.cleaned_df)

curr, prior = KPICalculator.get_period_split(filtered_df)
kpis = KPICalculator.calculate_kpis(curr, prior_df=prior)
render_kpi_dashboard(kpis, currency_symbol=curr_sym)
st.divider()

if kpis.has_dates:
    monthly_trend = get_monthly_sales_trend(filtered_df)
    st.plotly_chart(create_revenue_profit_trend_chart(monthly_trend, currency_symbol=curr_sym), use_container_width=True)

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("#### Monthly Growth Breakdown")
        if not monthly_trend.empty:
            display_m = monthly_trend.copy()
            display_m["Month"] = display_m["YearMonth"].dt.strftime("%b %Y")
            display_m["Revenue"] = display_m["Revenue"].apply(lambda x: format_inr(x, symbol=curr_sym))
            if "Profit" in display_m.columns:
                display_m["Profit"] = display_m["Profit"].apply(lambda x: format_inr(x, symbol=curr_sym))
                display_m["Margin"] = display_m["Profit_Margin_Pct"].apply(lambda x: f"{x:.1f}%")
            
            cols = ["Month", "Revenue"]
            if "Profit" in display_m.columns:
                cols += ["Profit", "Margin"]
            cols += ["Orders", "MoM_Revenue_Growth"]
            st.dataframe(display_m[cols].tail(12), use_container_width=True, hide_index=True)
    with c2:
        st.markdown("#### Year-Over-Year (YoY) Sales Comparison")
        yoy_df = get_yoy_growth_analysis(filtered_df)
        if not yoy_df.empty:
            st.dataframe(yoy_df, use_container_width=True, hide_index=True)
        else:
            st.info("Insufficient multi-year records in the active dataset for YoY comparison.")
else:
    st.info("ℹ️ Monthly revenue trends are disabled because no 'Order Date' column exists in this dataset.")

st.divider()
if "Discount" in filtered_df.columns:
    st.markdown("### 🏷️ Discount Impact & Margin Dilution")
    tier_summary, discount_fig = analyze_discount_impact(filtered_df, currency_symbol=curr_sym)
    st.plotly_chart(discount_fig, use_container_width=True)
    if not tier_summary.empty:
        format_dict = {"Total_Sales": lambda x: format_inr(x, symbol=curr_sym)}
        if "Total_Profit" in tier_summary.columns:
            format_dict["Total_Profit"] = lambda x: format_inr(x, symbol=curr_sym)
            format_dict["Overall_Margin_Pct"] = "{:.1f}%"
        st.dataframe(tier_summary.style.format(format_dict), use_container_width=True, hide_index=True)
