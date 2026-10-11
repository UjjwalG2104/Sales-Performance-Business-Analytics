"""
SalesIQ — SQL Analytics Studio Page.
"""
import streamlit as st
from src.state_manager import initialize_app_state, load_sample_dataset
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

st.markdown("## ⚡ SQL Analytics Studio")
db = st.session_state.db_manager
predefined = db.load_predefined_queries()
df_cols = st.session_state.cleaned_df.columns.tolist()

query_labels = [f"Q{q['id']}: {q['title']}" for q in predefined]
choice = st.selectbox("Select SQL Business Query:", range(len(query_labels)), format_func=lambda i: query_labels[i])
selected = predefined[choice]

st.markdown(f"**Business Purpose:** *{selected['purpose']}*")

is_compat, incompat_reason = db.check_query_compatibility(selected["sql"], df_cols)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**SQL Statement:**")
    st.code(selected["sql"], language="sql")
with c2:
    st.markdown("**Result Set:**")
    if not is_compat:
        st.warning(f"⚠️ Query Incompatible with Active Dataset:\n{incompat_reason}")
    else:
        try:
            res = db.execute_query(selected["sql"])
            st.dataframe(res, use_container_width=True)
            st.caption(f"Returned {format_indian_number(len(res))} rows.")
        except Exception as e:
            st.error(f"SQL Execution Error: {str(e)}")

st.divider()
st.markdown("### 💻 Custom SQL Console")
custom_query = st.text_area("Write SQL:", "SELECT category, ROUND(SUM(sales), 2) as total_sales FROM v_sales_analytics GROUP BY category;")
if st.button("Run SQL", type="primary"):
    try:
        out = db.execute_query(custom_query)
        st.dataframe(out, use_container_width=True)
        st.success(f"Returned {format_indian_number(len(out))} rows.")
    except Exception as e:
        st.error(str(e))
