"""
SalesIQ — Customer Analytics & Retention Page.
"""
import streamlit as st
from src.state_manager import initialize_app_state, load_sample_dataset
from src.customer_analysis import (
    analyze_customer_repeat_behavior,
    get_segment_performance,
    get_top_customers,
)
from src.ui_components import apply_sidebar_filters, load_custom_css
from src.formatters import format_indian_number, format_inr

load_custom_css()
initialize_app_state()

if not st.session_state.get("dataset_active"):
    st.warning("⚠️ No dataset is currently loaded. Please visit the Home / Executive Overview page to upload your file.")
    if st.button("🚀 Load Sample Dataset for Demo", type="primary"):
        load_sample_dataset()
        st.rerun()
    st.stop()

curr_sym = st.session_state.get("currency_symbol", "₹")
st.markdown("## 👥 Customer Behavior & Segment Analytics")
filtered_df = apply_sidebar_filters(st.session_state.cleaned_df)

has_cust = "Customer ID" in filtered_df.columns or "Customer Name" in filtered_df.columns
if not has_cust:
    st.info("ℹ️ Customer analytics are hidden because no customer columns are present in the active dataset.")
else:
    seg_df, seg_chart = get_segment_performance(filtered_df, currency_symbol=curr_sym)
    repeat_data = analyze_customer_repeat_behavior(filtered_df)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Customers", f"{format_indian_number(repeat_data['total_customers'])}")
    with m2:
        st.metric("Repeat Buyers", f"{format_indian_number(repeat_data['repeat_customers'])}")
    with m3:
        st.metric("Repeat Rate", f"{repeat_data['repeat_rate_pct']:.1f}%")
    with m4:
        st.metric("Repeat Sales Share", f"{repeat_data['repeat_revenue_pct']:.1f}%")

    st.divider()
    c1, c2 = st.columns([1.2, 1])
    with c1:
        if not seg_df.empty:
            st.plotly_chart(seg_chart, use_container_width=True)
        else:
            st.info("No Segment column present in this dataset.")
    with c2:
        st.plotly_chart(repeat_data["chart"], use_container_width=True)

    st.divider()
    st.markdown("### 🏆 Top High-Value Customers")
    top_cust = get_top_customers(filtered_df, top_n=10)
    if not top_cust.empty:
        disp_cols = [c for c in ["Customer ID", "Customer Name", "Segment", "Total_Sales", "Total_Profit", "Profit_Margin_Pct", "Order_Count", "AOV"] if c in top_cust.columns]
        format_map = {"Total_Sales": lambda x: format_inr(x, symbol=curr_sym), "AOV": lambda x: format_inr(x, symbol=curr_sym)}
        if "Total_Profit" in top_cust.columns:
            format_map["Total_Profit"] = lambda x: format_inr(x, symbol=curr_sym)
            format_map["Profit_Margin_Pct"] = "{:.1f}%"
        st.dataframe(top_cust[disp_cols].style.format(format_map), use_container_width=True, hide_index=True)
