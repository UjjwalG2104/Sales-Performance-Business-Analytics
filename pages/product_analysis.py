"""
SalesIQ — Product Performance & Portfolio Diagnostics Page.
"""
import streamlit as st
from src.state_manager import initialize_app_state, load_sample_dataset
from src.product_analysis import (
    create_product_quadrant_scatter,
    get_high_revenue_low_profit_products,
    get_loss_generating_products,
    get_top_performing_products,
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
st.markdown("## 📦 Product Analytics & Portfolio Diagnostics")
filtered_df = apply_sidebar_filters(st.session_state.cleaned_df)

has_prod = "Product Name" in filtered_df.columns or "Product ID" in filtered_df.columns
if not has_prod:
    st.info("ℹ️ Product analytics are unavailable because neither 'Product Name' nor 'Product ID' columns are present in the active dataset.")
else:
    st.plotly_chart(create_product_quadrant_scatter(filtered_df, currency_symbol=curr_sym), use_container_width=True)
    st.divider()

    tab1, tab2, tab3 = st.tabs(["⭐ Top Products", "🚨 Net Loss Products", "⚠️ Margin Diluters"])
    with tab1:
        top_p = get_top_performing_products(filtered_df, metric="Sales", top_n=10)
        if not top_p.empty:
            disp_cols = [c for c in ["Product ID", "Product Name", "Category", "Sub-Category", "Total_Sales", "Total_Profit", "Profit_Margin_Pct", "Total_Quantity"] if c in top_p.columns]
            format_map = {"Total_Sales": lambda x: format_inr(x, symbol=curr_sym)}
            if "Total_Profit" in top_p.columns:
                format_map["Total_Profit"] = lambda x: format_inr(x, symbol=curr_sym)
                format_map["Profit_Margin_Pct"] = "{:.1f}%"
            st.dataframe(top_p[disp_cols].style.format(format_map), use_container_width=True, hide_index=True)

    with tab2:
        if "Profit" in filtered_df.columns:
            loss_p = get_loss_generating_products(filtered_df, top_n=15)
            if not loss_p.empty:
                disp_cols = [c for c in ["Product ID", "Product Name", "Category", "Sub-Category", "Total_Sales", "Total_Profit", "Profit_Margin_Pct", "Avg_Discount_Pct"] if c in loss_p.columns]
                format_map = {"Total_Sales": lambda x: format_inr(x, symbol=curr_sym), "Total_Profit": lambda x: format_inr(x, symbol=curr_sym)}
                st.dataframe(loss_p[disp_cols].style.format(format_map), use_container_width=True, hide_index=True)
            else:
                st.success("No products generating net operating losses in the filtered dataset.")
        else:
            st.info("ℹ️ Loss detection requires a 'Profit' column.")

    with tab3:
        if "Profit" in filtered_df.columns:
            diluter_p = get_high_revenue_low_profit_products(filtered_df)
            if not diluter_p.empty:
                disp_cols = [c for c in ["Product ID", "Product Name", "Category", "Sub-Category", "Total_Sales", "Total_Profit", "Profit_Margin_Pct"] if c in diluter_p.columns]
                format_map = {"Total_Sales": lambda x: format_inr(x, symbol=curr_sym), "Total_Profit": lambda x: format_inr(x, symbol=curr_sym), "Profit_Margin_Pct": "{:.1f}%"}
                st.dataframe(diluter_p[disp_cols].style.format(format_map), use_container_width=True, hide_index=True)
            else:
                st.info("No margin diluter candidates detected with current thresholds.")
        else:
            st.info("ℹ️ Margin dilution diagnostics require a 'Profit' column.")
