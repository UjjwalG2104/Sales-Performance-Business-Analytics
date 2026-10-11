"""
SalesIQ — Regional & Geographic Performance Page.
"""
import streamlit as st
from src.state_manager import initialize_app_state, load_sample_dataset
from src.regional_analysis import (
    create_regional_comparison_chart,
    create_us_state_choropleth,
    get_regional_summary,
    get_state_performance,
)
from src.ui_components import apply_sidebar_filters, load_custom_css
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
st.markdown("## 🗺️ Regional & Geographic Performance")
filtered_df = apply_sidebar_filters(st.session_state.cleaned_df)

has_loc = "Region" in filtered_df.columns or "State" in filtered_df.columns or "City" in filtered_df.columns
if not has_loc:
    st.info("ℹ️ Regional analytics are hidden because no geographic columns were mapped in the dataset.")
else:
    reg_summary = get_regional_summary(filtered_df)
    state_summary = get_state_performance(filtered_df)

    if not reg_summary.empty:
        st.plotly_chart(create_regional_comparison_chart(reg_summary, currency_symbol=curr_sym), use_container_width=True)
    st.divider()

    if not state_summary.empty:
        metric_choices = ["Total_Sales"]
        if "Total_Profit" in state_summary.columns:
            metric_choices.append("Total_Profit")
        metric_choice = st.radio("Metric:", metric_choices, horizontal=True)
        st.plotly_chart(create_us_state_choropleth(state_summary, metric=metric_choice, currency_symbol=curr_sym), use_container_width=True)
        st.divider()

        st.markdown("### 📊 Territory Breakdown")
        disp_cols = [c for c in ["State", "Region", "Total_Sales", "Total_Profit", "Profit_Margin_Pct", "Total_Orders"] if c in state_summary.columns]
        format_map = {"Total_Sales": lambda x: format_inr(x, symbol=curr_sym)}
        if "Total_Profit" in state_summary.columns:
            format_map["Total_Profit"] = lambda x: format_inr(x, symbol=curr_sym)
            format_map["Profit_Margin_Pct"] = "{:.1f}%"
        st.dataframe(state_summary[disp_cols].style.format(format_map), use_container_width=True, hide_index=True)
