"""
SalesIQ — Data Quality & Ingestion Audit Page.
"""
import streamlit as st
from src.state_manager import initialize_app_state, load_sample_dataset
from src.data_cleaner import export_to_csv_bytes, export_to_excel_bytes
from src.ui_components import load_custom_css
from src.formatters import format_indian_number

load_custom_css()
initialize_app_state()

if not st.session_state.get("dataset_active"):
    st.warning("⚠️ No dataset is currently loaded. Please visit the Home / Executive Overview page to upload your file.")
    if st.button("🚀 Load Sample Dataset for Demo", type="primary"):
        load_sample_dataset()
        st.rerun()
    st.stop()

st.markdown("## 🧹 Data Quality, Validation & Ingestion Audit")
audit = st.session_state.get("audit")
cleaned_df = st.session_state.get("cleaned_df")

if audit:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📥 Raw Ingestion Health")
        st.metric("Total Raw Records", f"{format_indian_number(audit.original_metrics.total_records)}")
        st.metric("Duplicate Rows", f"{format_indian_number(audit.original_metrics.duplicate_records)}")
        st.metric("Missing Cells", f"{format_indian_number(audit.original_metrics.missing_cells)}")
        st.metric("Inconsistent Date Pairs", f"{format_indian_number(audit.original_metrics.inconsistent_dates_count)}")
    with c2:
        st.markdown("### ✨ Cleaned Dataset Health")
        st.metric("Clean Records Retained", f"{format_indian_number(audit.cleaned_metrics.total_records)}")
        st.metric("Duplicate Rows Remaining", f"{format_indian_number(audit.cleaned_metrics.duplicate_records)}")
        st.metric("Missing Cells Remaining", f"{format_indian_number(audit.cleaned_metrics.missing_cells)}")
        st.metric("Inconsistent Dates Remaining", f"{format_indian_number(audit.cleaned_metrics.inconsistent_dates_count)}")

    st.divider()
    st.markdown("### 📝 Cleaning Actions Taken")
    for a in audit.actions_taken:
        st.markdown(f"- ✅ **{a}**")

st.divider()
st.markdown("### 👁️ Cleaned Data Preview")
st.dataframe(cleaned_df.head(20), use_container_width=True)

st.divider()
st.markdown("### 💾 Export Clean Data")
c_e1, c_e2 = st.columns(2)
with c_e1:
    st.download_button("📥 Download Clean CSV", export_to_csv_bytes(cleaned_df), "cleaned_sales.csv", "text/csv", use_container_width=True)
with c_e2:
    st.download_button("📥 Download Clean Excel (.xlsx)", export_to_excel_bytes(cleaned_df), "cleaned_sales.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
