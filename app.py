"""
SalesIQ — Sales Performance & Business Analytics System
Main Application Entry Point.
Implements custom dataset upload by default, intelligent column mapping,
Indian Rupee (INR) formatting, and dynamic dashboard adaptation.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import streamlit as st

from config.settings import (
    DEFAULT_CURRENCY_CODE,
    DEFAULT_CURRENCY_SYMBOL,
    DEFAULT_EXCHANGE_RATES,
    DEFAULT_SAMPLE_CSV,
    PALETTE,
    SUPPORTED_SOURCE_CURRENCIES,
)
from src.column_mapper import (
    apply_column_mapping,
    detect_column_mapping,
    validate_mapping,
)
from src.data_cleaner import DataCleaner, export_to_csv_bytes, export_to_excel_bytes
from src.data_loader import ensure_sample_dataset_exists, load_file
from src.database import DatabaseManager
from src.formatters import format_indian_number, format_inr
from src.insights import InsightsGenerator
from src.kpi_calculator import KPICalculator
from src.sales_analysis import (
    analyze_discount_impact,
    create_category_sunburst,
    create_revenue_profit_trend_chart,
    get_monthly_sales_trend,
    get_yoy_growth_analysis,
)
from src.product_analysis import (
    create_product_quadrant_scatter,
    get_high_revenue_low_profit_products,
    get_loss_generating_products,
    get_top_performing_products,
)
from src.customer_analysis import (
    analyze_customer_repeat_behavior,
    get_segment_performance,
    get_top_customers,
)
from src.regional_analysis import (
    create_regional_comparison_chart,
    create_us_state_choropleth,
    get_regional_summary,
    get_state_performance,
)
from src.forecasting import SalesForecaster
from src.state_manager import (
    clear_active_dataset,
    initialize_app_state,
    load_sample_dataset,
    set_active_dataset,
)
from src.ui_components import (
    apply_sidebar_filters,
    load_custom_css,
    render_kpi_dashboard,
)

# Page Configuration
st.set_page_config(
    page_title="SalesIQ — Sales Performance & Business Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load Enterprise BI Stylesheet
load_custom_css()

# Initialize Session State
initialize_app_state()


# ==============================================================================
# ONBOARDING / EMPTY STATE & UPLOAD WORKFLOW
# ==============================================================================
if not st.session_state.get("dataset_active"):
    st.markdown("""
    <div style="text-align: center; padding: 30px 10px 20px 10px;">
        <h1 style="font-size: 2.6rem; color: #0F172A; margin-bottom: 8px;">SalesIQ Analytics</h1>
        <p style="font-size: 1.15rem; color: #475569; max-width: 650px; margin: 0 auto;">
            Turn your sales data into actionable business insights with executive scorecards,
            relational SQL intelligence, and predictive trend forecasting.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 3-Step Guided Workflow Banner
    step_col1, step_col2, step_col3 = st.columns(3)
    with step_col1:
        st.markdown("""
        <div class="kpi-container" style="text-align: center; border-top: 4px solid #2563EB;">
            <div style="font-size: 1.5rem; margin-bottom: 6px;">📤</div>
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">Step 1: Upload Data</div>
            <div style="font-size: 0.85rem; color: #64748B;">Drop any retail or ecommerce sales file in CSV, XLSX, or XLS format.</div>
        </div>
        """, unsafe_allow_html=True)
    with step_col2:
        st.markdown("""
        <div class="kpi-container" style="text-align: center; border-top: 4px solid #0D9488;">
            <div style="font-size: 1.5rem; margin-bottom: 6px;">🧭</div>
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">Step 2: Map & Validate</div>
            <div style="font-size: 0.85rem; color: #64748B;">Intelligent alias matching links your column headers to standard analytics fields.</div>
        </div>
        """, unsafe_allow_html=True)
    with step_col3:
        st.markdown("""
        <div class="kpi-container" style="text-align: center; border-top: 4px solid #059669;">
            <div style="font-size: 1.5rem; margin-bottom: 6px;">📈</div>
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">Step 3: Analyze & Forecast</div>
            <div style="font-size: 0.85rem; color: #64748B;">Instant financial scorecards, INR (₹) formatting, SQL queries, and insights.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Prominent File Uploader Card
    upload_card = st.container()
    with upload_card:
        st.markdown("### 📂 Ingest Your Sales Dataset")
        uploaded_file = st.file_uploader(
            "Select CSV, XLSX, or XLS file (Max 200MB):",
            type=["csv", "xlsx", "xls"],
            help="Upload your custom sales transactions table. Only a numeric sales/revenue column is required.",
            key="landing_file_uploader"
        )

        demo_col, info_col = st.columns([1, 2])
        with demo_col:
            if st.button("🚀 Or Explore with Sample Superstore Dataset", type="secondary", use_container_width=True):
                load_sample_dataset()
                st.success("Sample Superstore dataset activated!")
                st.rerun()

        with info_col:
            st.caption("ℹ️ **Privacy & Local Execution:** Data processing occurs locally in memory and in an embedded SQLite database (`salesiq.db`). No data is sent to external servers.")

    # Process Uploaded File
    if uploaded_file is not None:
        try:
            if (
                st.session_state.pending_upload is None
                or st.session_state.pending_upload.get("filename") != uploaded_file.name
            ):
                raw_df, f_type = load_file(uploaded_file)
                detected_map = detect_column_mapping(raw_df.columns.tolist())
                st.session_state.pending_upload = {
                    "filename": uploaded_file.name,
                    "file_type": f_type,
                    "df": raw_df,
                    "mapping": detected_map
                }
        except Exception as e:
            st.error(f"Error parsing uploaded file: {str(e)}")

    # Column Mapping & Review Modal
    if st.session_state.pending_upload is not None:
        p_up = st.session_state.pending_upload
        raw_df = p_up["df"]
        current_map = p_up["mapping"]

        st.divider()
        st.markdown(f"### 🧭 Intelligent Column Mapping: `{p_up['filename']}`")

        # Metadata metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Rows", f"{format_indian_number(len(raw_df))}")
        with m2:
            st.metric("Total Columns", f"{len(raw_df.columns)}")
        with m3:
            st.metric("File Type", p_up["file_type"])
        with m4:
            # Check date range if detected
            date_col = current_map.get("Order Date")
            if date_col and date_col in raw_df.columns:
                parsed_dates = pd.to_datetime(raw_df[date_col], errors="coerce").dropna()
                date_str = f"{parsed_dates.min().strftime('%b %Y')} – {parsed_dates.max().strftime('%b %Y')}" if not parsed_dates.empty else "No dates parsed"
            else:
                date_str = "No Date column"
            st.metric("Date Span", date_str)

        st.markdown("#### Confirm or Override Field Mappings")
        st.caption("Matches were automatically detected using fuzzy alias recognition. Verify or adjust the associations below:")

        raw_col_options = ["(Not Present)"] + raw_df.columns.tolist()

        c_map1, c_map2 = st.columns(2)
        confirmed_mapping: Dict[str, Optional[str]] = {}

        # Primary financial & core fields
        with c_map1:
            st.markdown("**Core Transaction Fields:**")
            
            # Sales (Required)
            default_sales = current_map.get("Sales") if current_map.get("Sales") in raw_df.columns else "(Not Present)"
            sales_idx = raw_col_options.index(default_sales) if default_sales in raw_col_options else 0
            sel_sales = st.selectbox("Sales / Revenue (Required)*", options=raw_col_options, index=sales_idx, key="map_sales")
            confirmed_mapping["Sales"] = sel_sales if sel_sales != "(Not Present)" else None

            # Order Date
            default_date = current_map.get("Order Date") if current_map.get("Order Date") in raw_df.columns else "(Not Present)"
            date_idx = raw_col_options.index(default_date) if default_date in raw_col_options else 0
            sel_date = st.selectbox("Order Date", options=raw_col_options, index=date_idx, key="map_date")
            confirmed_mapping["Order Date"] = sel_date if sel_date != "(Not Present)" else None

            # Order ID
            default_oid = current_map.get("Order ID") if current_map.get("Order ID") in raw_df.columns else "(Not Present)"
            oid_idx = raw_col_options.index(default_oid) if default_oid in raw_col_options else 0
            sel_oid = st.selectbox("Order ID / Transaction No", options=raw_col_options, index=oid_idx, key="map_oid")
            confirmed_mapping["Order ID"] = sel_oid if sel_oid != "(Not Present)" else None

            # Profit
            default_prof = current_map.get("Profit") if current_map.get("Profit") in raw_df.columns else "(Not Present)"
            prof_idx = raw_col_options.index(default_prof) if default_prof in raw_col_options else 0
            sel_prof = st.selectbox("Profit / Net Income", options=raw_col_options, index=prof_idx, key="map_prof")
            confirmed_mapping["Profit"] = sel_prof if sel_prof != "(Not Present)" else None

            # Quantity
            default_qty = current_map.get("Quantity") if current_map.get("Quantity") in raw_df.columns else "(Not Present)"
            qty_idx = raw_col_options.index(default_qty) if default_qty in raw_col_options else 0
            sel_qty = st.selectbox("Quantity / Units Sold", options=raw_col_options, index=qty_idx, key="map_qty")
            confirmed_mapping["Quantity"] = sel_qty if sel_qty != "(Not Present)" else None

            # Discount
            default_disc = current_map.get("Discount") if current_map.get("Discount") in raw_df.columns else "(Not Present)"
            disc_idx = raw_col_options.index(default_disc) if default_disc in raw_col_options else 0
            sel_disc = st.selectbox("Discount Rate", options=raw_col_options, index=disc_idx, key="map_disc")
            confirmed_mapping["Discount"] = sel_disc if sel_disc != "(Not Present)" else None

        # Categorical, customer & location fields
        with c_map2:
            st.markdown("**Catalog, Customer & Territory Fields:**")

            # Product Name
            default_prod = current_map.get("Product Name") if current_map.get("Product Name") in raw_df.columns else "(Not Present)"
            prod_idx = raw_col_options.index(default_prod) if default_prod in raw_col_options else 0
            sel_prod = st.selectbox("Product Name / Description", options=raw_col_options, index=prod_idx, key="map_prod")
            confirmed_mapping["Product Name"] = sel_prod if sel_prod != "(Not Present)" else None

            # Category
            default_cat = current_map.get("Category") if current_map.get("Category") in raw_df.columns else "(Not Present)"
            cat_idx = raw_col_options.index(default_cat) if default_cat in raw_col_options else 0
            sel_cat = st.selectbox("Category / Department", options=raw_col_options, index=cat_idx, key="map_cat")
            confirmed_mapping["Category"] = sel_cat if sel_cat != "(Not Present)" else None

            # Sub-Category
            default_sub = current_map.get("Sub-Category") if current_map.get("Sub-Category") in raw_df.columns else "(Not Present)"
            sub_idx = raw_col_options.index(default_sub) if default_sub in raw_col_options else 0
            sel_sub = st.selectbox("Sub-Category / Family", options=raw_col_options, index=sub_idx, key="map_sub")
            confirmed_mapping["Sub-Category"] = sel_sub if sel_sub != "(Not Present)" else None

            # Customer Name
            default_cust = current_map.get("Customer Name") if current_map.get("Customer Name") in raw_df.columns else "(Not Present)"
            cust_idx = raw_col_options.index(default_cust) if default_cust in raw_col_options else 0
            sel_cust = st.selectbox("Customer Name / Client", options=raw_col_options, index=cust_idx, key="map_cust")
            confirmed_mapping["Customer Name"] = sel_cust if sel_cust != "(Not Present)" else None

            # Region
            default_reg = current_map.get("Region") if current_map.get("Region") in raw_df.columns else "(Not Present)"
            reg_idx = raw_col_options.index(default_reg) if default_reg in raw_col_options else 0
            sel_reg = st.selectbox("Region / Territory", options=raw_col_options, index=reg_idx, key="map_reg")
            confirmed_mapping["Region"] = sel_reg if sel_reg != "(Not Present)" else None

            # State
            default_st = current_map.get("State") if current_map.get("State") in raw_df.columns else "(Not Present)"
            st_idx = raw_col_options.index(default_st) if default_st in raw_col_options else 0
            sel_st = st.selectbox("State / Province", options=raw_col_options, index=st_idx, key="map_st")
            confirmed_mapping["State"] = sel_st if sel_st != "(Not Present)" else None

        # Currency Interpretation & Exchange Rate Settings
        st.divider()
        st.markdown("#### 💱 Currency Interpretation & Exchange Rate")
        st.caption("SalesIQ defaults to Indian Rupees (₹ INR). If your file is recorded in another currency, choose the source currency and whether to convert:")

        cur_c1, cur_c2, cur_c3 = st.columns(3)
        with cur_c1:
            src_cur = st.selectbox(
                "Source File Currency:",
                options=SUPPORTED_SOURCE_CURRENCIES,
                index=0,
                key="source_currency_selector"
            )
        with cur_c2:
            apply_fx = st.checkbox(
                f"Convert {src_cur} to INR (₹)?",
                value=(src_cur != "INR"),
                key="apply_fx_checkbox"
            )
        with cur_c3:
            default_fx = DEFAULT_EXCHANGE_RATES.get(src_cur, 1.0) if apply_fx else 1.0
            custom_fx = st.number_input(
                f"Exchange Rate (1 {src_cur} = ₹ INR):",
                min_value=0.01,
                value=float(default_fx),
                step=0.50,
                disabled=not apply_fx,
                key="custom_fx_input"
            )

        active_fx = custom_fx if apply_fx else 1.0

        # Validate mapping
        is_valid, map_errors, map_warnings = validate_mapping(confirmed_mapping, raw_df)
        if not is_valid:
            for err in map_errors:
                st.error(f"❌ {err}")
        else:
            for warn in map_warnings:
                st.warning(f"⚠️ {warn}")

            if st.button("✅ Confirm Mapping & Launch Dashboard", type="primary", use_container_width=True):
                # Apply column rename
                mapped_df = apply_column_mapping(raw_df, confirmed_mapping)
                # Clean and scale
                cleaner = DataCleaner(mapped_df, exchange_rate=active_fx)
                clean_df, audit = cleaner.clean()

                st.session_state.source_currency = src_cur
                st.session_state.exchange_rate = active_fx
                st.session_state.currency_symbol = DEFAULT_CURRENCY_SYMBOL
                st.session_state.currency_code = DEFAULT_CURRENCY_CODE

                set_active_dataset(
                    raw_df=raw_df,
                    cleaned_df=clean_df,
                    audit=audit,
                    source_label=f"{p_up['filename']} ({p_up['file_type']})",
                    column_mapping=confirmed_mapping
                )
                st.success(f"Successfully activated dataset with {format_indian_number(len(clean_df))} clean rows!")
                st.rerun()

    st.stop()


# ==============================================================================
# ACTIVE DATASET: SIDEBAR & CONTROLS
# ==============================================================================
with st.sidebar:
    st.markdown("## 📊 SalesIQ Analytics")
    st.caption("Enterprise Business Intelligence")
    st.divider()

    # Active dataset card
    ds_label = st.session_state.get("data_source_label", "Custom Dataset")
    st.markdown(f"**Active Dataset:** `{ds_label}`")
    st.caption(f"**Rows:** {format_indian_number(len(st.session_state.cleaned_df))} | **Currency:** {st.session_state.currency_code} ({st.session_state.currency_symbol})")

    # Dataset Replacement & Clearing Actions
    col_act1, col_act2 = st.columns(2)
    with col_act1:
        if st.button("🔄 Replace", help="Upload a new dataset"):
            clear_active_dataset()
            st.rerun()
    with col_act2:
        if st.button("🗑️ Clear", help="Unload dataset and reset"):
            clear_active_dataset()
            st.rerun()

    st.divider()

    # Navigation Menu
    nav_page = st.radio(
        "Navigation",
        [
            "Executive Overview",
            "Sales Analysis",
            "Product Analysis",
            "Customer Analysis",
            "Regional Analysis",
            "SQL Analytics",
            "Data Quality & Audit",
            "Forecasting",
            "About the Project"
        ],
        index=0,
        key="main_navigation"
    )
    st.divider()

# Currency Symbol
curr_sym = st.session_state.get("currency_symbol", "₹")

# Apply Dynamic Filters to Active Cleaned Dataset
cleaned_df = st.session_state.cleaned_df
filtered_df = apply_sidebar_filters(cleaned_df)

# Split for Period-over-Period growth calculation
curr_period, prior_period = KPICalculator.get_period_split(filtered_df)
kpis = KPICalculator.calculate_kpis(curr_period, prior_df=prior_period)


# ==============================================================================
# PAGE 1: EXECUTIVE OVERVIEW
# ==============================================================================
if nav_page == "Executive Overview":
    st.markdown("## 📈 Executive Sales Overview")
    st.markdown("High-level performance summary, financial health indicators, and automated business insights in **Indian Rupees (₹)**.")

    # 1. KPI Cards Grid
    render_kpi_dashboard(kpis, currency_symbol=curr_sym)
    st.divider()

    # 2. Key Visualizations: Monthly Revenue Trend + Category Sunburst
    col_chart1, col_chart2 = st.columns([1.6, 1.4])
    with col_chart1:
        if kpis.has_dates:
            monthly_data = get_monthly_sales_trend(filtered_df)
            trend_fig = create_revenue_profit_trend_chart(monthly_data, currency_symbol=curr_sym)
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.info("ℹ️ Monthly revenue trend is unavailable because no 'Order Date' column was mapped in the active dataset.")

    with col_chart2:
        if "Category" in filtered_df.columns:
            sunburst_fig = create_category_sunburst(filtered_df, currency_symbol=curr_sym)
            st.plotly_chart(sunburst_fig, use_container_width=True)
        else:
            st.info("ℹ️ Category distribution is unavailable because no 'Category' column was mapped in the active dataset.")

    st.divider()

    # 3. Automated Business Insights Engine
    st.markdown("### 💡 Automated Business Insights & Recommendations")
    st.caption("Evidence-backed findings synthesized dynamically from the active filtered transactions.")

    insights = InsightsGenerator.generate_all_insights(filtered_df, currency_symbol=curr_sym)
    if not insights:
        st.info("No notable anomalies detected for the currently selected filters.")
    else:
        for ins in insights:
            badge_icon = "🟢" if ins.severity == "positive" else ("🔴" if ins.severity == "critical" else ("🟡" if ins.severity == "warning" else "🔵"))
            st.markdown(f"""
            <div class="insight-card {ins.severity}">
                <div class="insight-header">{badge_icon} [{ins.category}] {ins.headline}</div>
                <div class="insight-section-title">1. What Happened?</div>
                <div class="insight-body">{ins.what_happened}</div>
                <div class="insight-section-title">2. Evidence & Data Proof</div>
                <div class="insight-body"><b>{ins.evidence}</b></div>
                <div class="insight-section-title">3. Why It Matters (Business Impact & Hypothesis)</div>
                <div class="insight-body"><i>{ins.why_it_matters}</i></div>
                <div class="insight-section-title">4. Strategic Recommendation</div>
                <div class="insight-body">🎯 <b>{ins.recommended_action}</b></div>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# PAGE 2: SALES & REVENUE ANALYSIS
# ==============================================================================
elif nav_page == "Sales Analysis":
    st.markdown("## 💰 In-Depth Sales & Revenue Analysis")
    st.markdown("Examine monthly momentum, year-over-year pacing, and margin sensitivity to discounts in **Indian Rupees (₹)**.")

    render_kpi_dashboard(kpis, currency_symbol=curr_sym)
    st.divider()

    if kpis.has_dates:
        monthly_trend = get_monthly_sales_trend(filtered_df)
        st.plotly_chart(create_revenue_profit_trend_chart(monthly_trend, currency_symbol=curr_sym), use_container_width=True)

        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.markdown("#### Monthly Growth Breakdown")
            if not monthly_trend.empty:
                display_monthly = monthly_trend.copy()
                display_monthly["Month"] = display_monthly["YearMonth"].dt.strftime("%b %Y")
                display_monthly["Revenue"] = display_monthly["Revenue"].apply(lambda x: format_inr(x, symbol=curr_sym))
                if "Profit" in display_monthly.columns:
                    display_monthly["Profit"] = display_monthly["Profit"].apply(lambda x: format_inr(x, symbol=curr_sym))
                    display_monthly["Margin"] = display_monthly["Profit_Margin_Pct"].apply(lambda x: f"{x:.1f}%")
                display_monthly["MoM Rev Growth"] = display_monthly["MoM_Revenue_Growth"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
                
                cols_to_show = ["Month", "Revenue"]
                if "Profit" in display_monthly.columns:
                    cols_to_show += ["Profit", "Margin"]
                cols_to_show += ["Orders", "MoM Rev Growth"]
                st.dataframe(display_monthly[cols_to_show].tail(12), use_container_width=True, hide_index=True)

        with c2:
            st.markdown("#### Year-Over-Year (YoY) Sales Comparison")
            yoy_df = get_yoy_growth_analysis(filtered_df)
            if not yoy_df.empty:
                st.dataframe(yoy_df, use_container_width=True, hide_index=True)
            else:
                st.info("Insufficient multi-year records in the active dataset for YoY comparison.")
    else:
        st.info("ℹ️ Time-based monthly analytics are disabled because no 'Order Date' column exists in this dataset.")

    st.divider()
    # Discount Analysis
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
    else:
        st.info("ℹ️ Discount analysis is hidden because no 'Discount' column is present in the dataset.")


# ==============================================================================
# PAGE 3: PRODUCT ANALYSIS
# ==============================================================================
elif nav_page == "Product Analysis":
    st.markdown("## 📦 Product Analytics & Portfolio Diagnostics")
    st.markdown("Identify top-performing products, negative margin items, and portfolio distribution in **Indian Rupees (₹)**.")

    has_prod = "Product Name" in filtered_df.columns or "Product ID" in filtered_df.columns
    if not has_prod:
        st.info("ℹ️ Product analysis is unavailable because neither 'Product Name' nor 'Product ID' columns are present in the active dataset.")
    else:
        st.plotly_chart(create_product_quadrant_scatter(filtered_df, currency_symbol=curr_sym), use_container_width=True)
        st.divider()

        tab_top, tab_loss, tab_diluters = st.tabs([
            "⭐ Top Products by Revenue",
            "🚨 Net Loss Products",
            "⚠️ High-Revenue, Low-Margin Products"
        ])

        with tab_top:
            st.markdown("#### Top 10 Best Sellers by Revenue")
            top_rev = get_top_performing_products(filtered_df, metric="Sales", top_n=10)
            if not top_rev.empty:
                disp_cols = [c for c in ["Product ID", "Product Name", "Category", "Sub-Category", "Total_Sales", "Total_Profit", "Profit_Margin_Pct", "Total_Quantity"] if c in top_rev.columns]
                format_map = {"Total_Sales": lambda x: format_inr(x, symbol=curr_sym)}
                if "Total_Profit" in top_rev.columns:
                    format_map["Total_Profit"] = lambda x: format_inr(x, symbol=curr_sym)
                    format_map["Profit_Margin_Pct"] = "{:.1f}%"
                st.dataframe(top_rev[disp_cols].style.format(format_map), use_container_width=True, hide_index=True)

        with tab_loss:
            st.markdown("#### Products Generating Negative Operating Profit")
            if kpis.has_profit:
                loss_df = get_loss_generating_products(filtered_df, top_n=15)
                if not loss_df.empty:
                    disp_cols = [c for c in ["Product ID", "Product Name", "Category", "Sub-Category", "Total_Sales", "Total_Profit", "Profit_Margin_Pct", "Avg_Discount_Pct"] if c in loss_df.columns]
                    format_map = {
                        "Total_Sales": lambda x: format_inr(x, symbol=curr_sym),
                        "Total_Profit": lambda x: format_inr(x, symbol=curr_sym),
                        "Profit_Margin_Pct": "{:.1f}%"
                    }
                    st.dataframe(loss_df[disp_cols].style.format(format_map), use_container_width=True, hide_index=True)
                else:
                    st.success("No products generating net operating losses in the filtered dataset.")
            else:
                st.info("ℹ️ Net loss detection is unavailable because no 'Profit' column is present in the dataset.")

        with tab_diluters:
            st.markdown("#### Margin Diluters (Top Volume, but Margin < 5%)")
            if kpis.has_profit:
                diluters_df = get_high_revenue_low_profit_products(filtered_df)
                if not diluters_df.empty:
                    disp_cols = [c for c in ["Product ID", "Product Name", "Category", "Sub-Category", "Total_Sales", "Total_Profit", "Profit_Margin_Pct"] if c in diluters_df.columns]
                    format_map = {
                        "Total_Sales": lambda x: format_inr(x, symbol=curr_sym),
                        "Total_Profit": lambda x: format_inr(x, symbol=curr_sym),
                        "Profit_Margin_Pct": "{:.1f}%"
                    }
                    st.dataframe(diluters_df[disp_cols].style.format(format_map), use_container_width=True, hide_index=True)
                else:
                    st.info("No margin diluters detected with current thresholds.")
            else:
                st.info("ℹ️ Margin dilution diagnostics require a 'Profit' column.")


# ==============================================================================
# PAGE 4: CUSTOMER ANALYSIS
# ==============================================================================
elif nav_page == "Customer Analysis":
    st.markdown("## 👥 Customer Behavior & Segment Analytics")
    st.markdown("Examine customer value, segment economics, and repeat buyer loyalty in **Indian Rupees (₹)**.")

    has_cust = "Customer ID" in filtered_df.columns or "Customer Name" in filtered_df.columns
    if not has_cust:
        st.info("ℹ️ Customer analytics are hidden because no customer identification columns were mapped in the dataset.")
    else:
        seg_summary, seg_chart = get_segment_performance(filtered_df, currency_symbol=curr_sym)
        repeat_data = analyze_customer_repeat_behavior(filtered_df)

        c_rep1, c_rep2, c_rep3, c_rep4 = st.columns(4)
        with c_rep1:
            st.metric("Total Customers", f"{format_indian_number(repeat_data['total_customers'])}")
        with c_rep2:
            st.metric("Repeat Buyers", f"{format_indian_number(repeat_data['repeat_customers'])}")
        with c_rep3:
            st.metric("Repeat Buyer Rate", f"{repeat_data['repeat_rate_pct']:.1f}%")
        with c_rep4:
            st.metric("Repeat Revenue Share", f"{repeat_data['repeat_revenue_pct']:.1f}%")

        st.divider()
        c_c1, c_c2 = st.columns([1.2, 1])
        with c_c1:
            if not seg_summary.empty:
                st.plotly_chart(seg_chart, use_container_width=True)
            else:
                st.info("Customer Segment breakdown is unavailable (no 'Segment' column mapped).")
        with c_c2:
            st.plotly_chart(repeat_data["chart"], use_container_width=True)

        st.divider()
        st.markdown("### 🏆 Top High-Value Customers")
        top_cust = get_top_customers(filtered_df, top_n=10, sort_by="Sales")
        if not top_cust.empty:
            disp_cols = [c for c in ["Customer ID", "Customer Name", "Segment", "Total_Sales", "Total_Profit", "Profit_Margin_Pct", "Order_Count", "AOV"] if c in top_cust.columns]
            format_map = {"Total_Sales": lambda x: format_inr(x, symbol=curr_sym), "AOV": lambda x: format_inr(x, symbol=curr_sym)}
            if "Total_Profit" in top_cust.columns:
                format_map["Total_Profit"] = lambda x: format_inr(x, symbol=curr_sym)
                format_map["Profit_Margin_Pct"] = "{:.1f}%"
            st.dataframe(top_cust[disp_cols].style.format(format_map), use_container_width=True, hide_index=True)


# ==============================================================================
# PAGE 5: REGIONAL ANALYSIS
# ==============================================================================
elif nav_page == "Regional Analysis":
    st.markdown("## 🗺️ Regional & Geographic Performance")
    st.markdown("Assess regional profitability, state-level penetration, and geographic performance in **Indian Rupees (₹)**.")

    has_loc = "Region" in filtered_df.columns or "State" in filtered_df.columns or "City" in filtered_df.columns
    if not has_loc:
        st.info("ℹ️ Regional analytics are hidden because no geographic columns (Region, State, or City) were mapped.")
    else:
        reg_summary = get_regional_summary(filtered_df)
        state_summary = get_state_performance(filtered_df)

        if not reg_summary.empty:
            st.plotly_chart(create_regional_comparison_chart(reg_summary, currency_symbol=curr_sym), use_container_width=True)
        
        st.divider()
        if not state_summary.empty:
            metric_options = ["Total_Sales"]
            if "Total_Profit" in state_summary.columns:
                metric_options.append("Total_Profit")
            map_metric = st.radio("Territory Metric:", metric_options, horizontal=True)
            st.plotly_chart(create_us_state_choropleth(state_summary, metric=map_metric, currency_symbol=curr_sym), use_container_width=True)

            st.divider()
            st.markdown("### 📊 State / Territory Breakdown")
            disp_cols = [c for c in ["State", "Region", "Total_Sales", "Total_Profit", "Profit_Margin_Pct", "Total_Orders"] if c in state_summary.columns]
            format_map = {"Total_Sales": lambda x: format_inr(x, symbol=curr_sym)}
            if "Total_Profit" in state_summary.columns:
                format_map["Total_Profit"] = lambda x: format_inr(x, symbol=curr_sym)
                format_map["Profit_Margin_Pct"] = "{:.1f}%"
            st.dataframe(state_summary[disp_cols].style.format(format_map), use_container_width=True, hide_index=True)


# ==============================================================================
# PAGE 6: SQL ANALYTICS MODULE
# ==============================================================================
elif nav_page == "SQL Analytics":
    st.markdown("## ⚡ SQL Analytics Studio")
    st.markdown("Run real relational SQL queries against the embedded SQLite database (`salesiq.db`) reflecting the active dataset.")

    db = st.session_state.db_manager
    predefined_queries = db.load_predefined_queries()
    df_cols = cleaned_df.columns.tolist()

    st.markdown("### 📋 15 Standard Business Analytics Queries")
    query_options = [f"Q{q['id']}: {q['title']}" for q in predefined_queries]
    selected_idx = st.selectbox("Select Business Query to Execute:", range(len(query_options)), format_func=lambda i: query_options[i])

    selected_q = predefined_queries[selected_idx]
    st.markdown(f"**Business Purpose:** *{selected_q['purpose']}*")

    # Check query compatibility with active fields
    is_compat, incompat_reason = db.check_query_compatibility(selected_q["sql"], df_cols)

    col_q1, col_q2 = st.columns([1, 1])
    with col_q1:
        st.markdown("**SQL Statement:**")
        st.code(selected_q["sql"], language="sql")

    with col_q2:
        st.markdown("**Live Execution Output:**")
        if not is_compat:
            st.warning(f"⚠️ Query Incompatible: {incompat_reason}")
        else:
            try:
                query_res = db.execute_query(selected_q["sql"])
                st.dataframe(query_res, use_container_width=True)
                st.caption(f"Returned {format_indian_number(len(query_res))} rows.")
            except Exception as e:
                st.error(f"SQL execution error: {str(e)}")

    st.divider()
    st.markdown("### 💻 Custom SQL Query Console")
    st.caption("Write SELECT queries against tables: `fact_orders`, `dim_customers`, `dim_products`, `dim_locations`, or view `v_sales_analytics`:")
    custom_sql = st.text_area(
        "Custom SQL Query:",
        value="SELECT p.category, ROUND(SUM(f.sales), 2) AS total_revenue, COUNT(f.order_line_id) AS total_lines FROM fact_orders f JOIN dim_products p ON f.product_id = p.product_id GROUP BY p.category ORDER BY total_revenue DESC;",
        height=100
    )
    if st.button("Execute Custom SQL", type="primary"):
        try:
            custom_res = db.execute_query(custom_sql)
            st.dataframe(custom_res, use_container_width=True)
            st.success(f"Executed successfully! {format_indian_number(len(custom_res))} rows returned.")
        except Exception as e:
            st.error(f"SQL Syntax / Execution Error: {str(e)}")


# ==============================================================================
# PAGE 7: DATA QUALITY & AUDIT
# ==============================================================================
elif nav_page == "Data Quality & Audit":
    st.markdown("## 🧹 Data Quality, Validation & Ingestion Audit")
    st.markdown("Deterministic before-and-after data hygiene inspection, anomaly detection, and clean dataset exports.")

    audit = st.session_state.get("audit")
    if audit:
        c_q1, c_q2 = st.columns(2)
        with c_q1:
            st.markdown("### 📥 Raw Ingestion Health")
            st.metric("Total Raw Records", f"{format_indian_number(audit.original_metrics.total_records)}")
            st.metric("Duplicate Rows Detected", f"{format_indian_number(audit.original_metrics.duplicate_records)}")
            st.metric("Missing Cell Count", f"{format_indian_number(audit.original_metrics.missing_cells)}")
            st.metric("Inconsistent Date Pairs", f"{format_indian_number(audit.original_metrics.inconsistent_dates_count)}")
            st.metric("Memory Footprint", f"{audit.original_metrics.memory_usage_kb:.1f} KB")

        with c_q2:
            st.markdown("### ✨ Cleaned Dataset Health")
            st.metric("Clean Records Retained", f"{format_indian_number(audit.cleaned_metrics.total_records)}")
            st.metric("Duplicate Rows Remaining", f"{format_indian_number(audit.cleaned_metrics.duplicate_records)}")
            st.metric("Missing Cells Remaining", f"{format_indian_number(audit.cleaned_metrics.missing_cells)}")
            st.metric("Inconsistent Dates Remaining", f"{format_indian_number(audit.cleaned_metrics.inconsistent_dates_count)}")
            st.metric("Memory Footprint", f"{audit.cleaned_metrics.memory_usage_kb:.1f} KB")

        st.divider()
        st.markdown("### 📝 Cleaning Decisions & Audit Trail")
        for act in audit.actions_taken:
            st.markdown(f"- ✅ **{act}**")
    else:
        st.info("No active cleaning audit logged for this session.")

    st.divider()
    st.markdown("### 👁️ Cleaned Data Preview")
    st.dataframe(cleaned_df.head(25), use_container_width=True)

    st.divider()
    st.markdown("### 💾 Export Cleaned Dataset")
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        csv_bytes = export_to_csv_bytes(cleaned_df)
        st.download_button(
            label="📥 Download Cleaned CSV",
            data=csv_bytes,
            file_name="cleaned_salesiq_data.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_exp2:
        excel_bytes = export_to_excel_bytes(cleaned_df)
        st.download_button(
            label="📥 Download Cleaned Excel (.xlsx)",
            data=excel_bytes,
            file_name="cleaned_salesiq_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


# ==============================================================================
# PAGE 8: FORECASTING & ADVANCED ANALYTICS
# ==============================================================================
elif nav_page == "Forecasting":
    st.markdown("## 🔮 Advanced Analytics: Sales Forecasting")
    st.markdown("Chronological hold-out validation, baseline time-series modeling, and out-of-sample projection in **Indian Rupees (₹)**.")

    if not kpis.has_dates:
        st.info("ℹ️ Sales forecasting requires an 'Order Date' column, which is not present in the active dataset.")
    else:
        horizon = st.slider("Select Forecast Horizon (Months):", min_value=3, max_value=12, value=6)
        forecast_res = SalesForecaster.run_forecast(filtered_df, test_periods=6, forecast_horizon=horizon, currency_symbol=curr_sym)

        if not forecast_res.is_sufficient_data:
            st.warning(forecast_res.message)
        else:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Holdout MAE", format_inr(forecast_res.metrics['MAE'], symbol=curr_sym), help="Mean Absolute Error on unseen test set")
            with m2:
                st.metric("Holdout RMSE", format_inr(forecast_res.metrics['RMSE'], symbol=curr_sym), help="Root Mean Squared Error on unseen test set")
            with m3:
                st.metric("Holdout MAPE", f"{forecast_res.metrics['MAPE']:.1f}%", help="Mean Absolute Percentage Error")

            st.plotly_chart(forecast_res.chart, use_container_width=True)

            st.markdown("#### Forecast Projections Table")
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

            st.info("ℹ️ **Model Limitations & Statistical Disclaimer:** This baseline incorporates linear trend and harmonic monthly seasonality trained strictly without data leakage. Forecasts assume stationary macroeconomic and promotional conditions.")


# ==============================================================================
# PAGE 9: ABOUT THE PROJECT
# ==============================================================================
elif nav_page == "About the Project":
    st.markdown("## ℹ️ About SalesIQ — Sales Performance & Business Analytics")
    st.markdown("""
    **SalesIQ** is an end-to-end analytics platform engineered to showcase production-grade Data Analyst, Data Engineering, and BI capabilities.

    ### 🎯 Portfolio & Interview Highlights
    - **Adaptive Custom Upload Pipeline:** Ingests any custom retail/ecommerce sales CSV or Excel file with intelligent column alias detection.
    - **Indian Rupee (₹ INR) Formatting:** Native Indian numbering system (Lakhs & Crores grouping) applied uniformly across all KPI scorecards, charts, and tables.
    - **Data Cleaning Integrity:** Explicit before-and-after data quality auditing, duplicate detection, date consistency enforcement, and anomaly clamping without fabricating business numbers.
    - **Relational SQL Analytics:** 15 production business queries demonstrating aggregations, joins, CTEs, and window functions (`LAG`, `RANK`, `DENSE_RANK`, `NTILE`, `SUM OVER`).
    - **Automated 4-Pillar Insights:** Translates raw metrics into structured business recommendations (`What Happened`, `Evidence`, `Why It Matters`, `Action`).
    - **Leak-Free Predictive Modeling:** Time series forecasting with chronological train/test splitting and MAE/RMSE/MAPE error evaluation.

    ### 🛠️ Tech Stack
    - **Core:** Python 3.12, Pandas, NumPy
    - **Visualization:** Plotly, Matplotlib, Seaborn
    - **Database:** SQLite (Relational star schema with foreign keys and indexes)
    - **Dashboard UI:** Streamlit with customized Enterprise BI design tokens
    - **Machine Learning:** Scikit-Learn
    - **Quality Assurance:** Pytest automated test suite
    """)
