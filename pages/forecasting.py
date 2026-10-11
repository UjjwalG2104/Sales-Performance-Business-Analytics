"""
SalesIQ — Advanced Forecasting & Trend Projection Page.
"""
import streamlit as st
from src.state_manager import initialize_app_state, load_sample_dataset
from src.forecasting import SalesForecaster
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
st.markdown("## 🔮 Advanced Analytics: Sales Forecasting")
filtered_df = apply_sidebar_filters(st.session_state.cleaned_df)

if "Order Date" not in filtered_df.columns:
    st.info("ℹ️ Sales forecasting requires an 'Order Date' column, which is not present in the active dataset.")
else:
    horizon = st.slider("Forecast Horizon (Months):", 3, 12, 6)
    forecast_res = SalesForecaster.run_forecast(filtered_df, test_periods=6, forecast_horizon=horizon, currency_symbol=curr_sym)

    if not forecast_res.is_sufficient_data:
        st.warning(forecast_res.message)
    else:
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Holdout MAE", format_inr(forecast_res.metrics['MAE'], symbol=curr_sym))
        with m2:
            st.metric("Holdout RMSE", format_inr(forecast_res.metrics['RMSE'], symbol=curr_sym))
        with m3:
            st.metric("Holdout MAPE", f"{forecast_res.metrics['MAPE']:.1f}%")

        st.plotly_chart(forecast_res.chart, use_container_width=True)
        st.markdown("#### Projected Monthly Sales")
        st.dataframe(
            forecast_res.forecast_df[["ds", "y_pred", "y_lower", "y_upper"]].rename(columns={
                "ds": "Forecast Month",
                "y_pred": f"Projected Sales ({curr_sym})",
                "y_lower": f"Lower 95% Bound ({curr_sym})",
                "y_upper": f"Upper 95% Bound ({curr_sym})"
            }).style.format({
                f"Projected Sales ({curr_sym})": lambda x: format_inr(x, symbol=curr_sym),
                f"Lower 95% Bound ({curr_sym})": lambda x: format_inr(x, symbol=curr_sym),
                f"Upper 95% Bound ({curr_sym})": lambda x: format_inr(x, symbol=curr_sym)
            }),
            use_container_width=True,
            hide_index=True
        )
