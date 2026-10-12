# SalesIQ — Sales Performance & Business Analytics System

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.42+-red.svg)
![Currency](https://img.shields.io/badge/Currency-INR%20(%E2%82%B9)-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3.0-lightgrey.svg)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-teal.svg)
![Tests](https://img.shields.io/badge/Tests-26%2F26%20Passing-brightgreen.svg)

**SalesIQ** is an end-to-end sales analytics, data engineering, and business intelligence platform built for fresher Data Analysts, BI professionals, and analytics engineers. It transforms raw, imperfect retail transactional records into executive-grade KPI scorecards, interactive multidimensional dashboards, relational SQL data warehouses, automated 4-pillar business insights, and holdout-validated machine learning forecasts—all formatted in **Indian Rupees (₹ INR)** with native Indian number grouping.

Live Dashboard: https://salesiq-analytics.streamlit.app/
---

## 1. Key Highlights & Architectural Features

1. **Custom Dataset Upload by Default:**
   - Launches to a clean onboarding screen without pre-loading fake data or default datasets.
   - Prominent drag-and-drop uploader supporting **CSV**, **XLSX**, and **XLS** files up to 200MB.
   - Optional **"Explore with Sample Superstore Dataset"** button available on-demand for quick demonstration.
   - Persistent dataset state across page navigation with **"Replace Dataset"** and **"Clear Dataset"** actions.

2. **Intelligent Column Mapping Engine (`src/column_mapper.py`):**
   - Automatically detects common header variations and aliases using case- and whitespace-insensitive matching (e.g., `Invoice No`, `Order Date`, `Amount`, `Net Profit`, `Qty`, `Item Name`, `Department`, `Client`, `Territory`, `Markdown`).
   - Interactive column confirmation screen allowing users to confirm or override field associations.
   - Requires only a numeric **Sales/Revenue** column; gracefully adapts all scorecards, charts, and SQL queries if optional fields (like Profit, Dates, or Customers) are absent.

3. **Indian Rupee (₹ INR) Formatting (`src/formatters.py`):**
   - Standard Indian comma grouping (Lakhs and Crores system: `2,2,3` grouping):
     - Example: `₹15,32,068.61`
     - Example: `₹1,70,471.65`
     - Negative numbers: `-₹1,23,456.78`
     - Quantities and order counts: formatted without currency symbols (`12,34,567`).
   - Configurable source currency with optional user-confirmed exchange rate conversion.

4. **Relational Database & SQL Analytics Studio (`src/database.py`):**
   - Dynamic ETL into SQLite star schema (`dim_customers`, `dim_locations`, `dim_products`, `fact_orders`, `v_sales_analytics`).
   - Transactionally refreshed on dataset replacement without duplicate rows.
   - 15 production SQL queries demonstrating CTEs, joins, group by, subqueries, and window functions (`LAG`, `RANK`, `DENSE_RANK`, `NTILE`, `SUM OVER`) with query compatibility checking.

5. **Automated 4-Pillar Executive Insights (`src/insights.py`):**
   - Synthesizes findings into: *1. What Happened?*, *2. Evidence & Data Proof*, *3. Why It Matters (Hypothesis)*, *4. Strategic Recommendation*.

6. **Leak-Free Time-Series Forecasting (`src/forecasting.py`):**
   - Chronological hold-out validation with Ridge regression and harmonic monthly seasonality.
   - Error metrics evaluated on unseen test sets: **MAE**, **RMSE**, and **MAPE**.

---

## 2. Technology Stack

| Layer | Technologies | Role & Implementation |
|---|---|---|
| **Core Language** | Python 3.12 | Object-oriented pipeline architecture, modular packaging |
| **Data Engineering** | Pandas 2.x, NumPy, OpenPyXL | Data cleaning, type coercion, period splitting, Excel/CSV I/O |
| **Database & Warehousing** | SQLite 3 | Normalized dimensional star schema (`dim_*`, `fact_*`, `v_*`), relational indexing |
| **Data Visualization** | Plotly Express, Plotly Graph Objects | Interactive charts, dual-axis trends, hierarchy sunbursts, US state choropleth |
| **Interactive Dashboard** | Streamlit | Enterprise BI user interface with custom CSS design tokens |
| **Formatting Engine** | Custom Indian Numbering Formatter | Native Lakhs/Crores digit grouping and ₹ INR formatting |
| **Predictive Analytics** | Scikit-Learn | Ridge regression time-series baseline, calendar harmonic seasonality, MAE/RMSE/MAPE |
| **Automated Testing** | Pytest | 26 automated unit and integration tests |

---

## 3. Project Structure

```
SalesIQ-Sales Performance & Business Analytics/
├── app.py                      # Main Streamlit application & interactive routing hub
├── requirements.txt            # Project dependencies
├── README.md                   # Comprehensive documentation & portfolio guide
├── .gitignore                  # Git exclusion rules
├── pytest.ini                  # Pytest configuration
├── assets/
│   └── style.css               # Enterprise BI CSS design system & typography tokens
├── config/
│   └── settings.py             # Global directory paths, color palettes, currency configs
├── data/
│   ├── raw/                    # Raw uploaded files
│   ├── processed/              # Cleaned analytical datasets
│   └── sample/
│       └── superstore_sales.csv# 4-year retail transaction dataset (3,500 rows)
├── database/
│   ├── schema.sql              # Relational DDL (dim_*, fact_orders, v_sales_analytics)
│   └── salesiq.db              # SQLite database file
├── sql/
│   └── business_queries.sql    # 15 production SQL analytics queries with explanations
├── src/
│   ├── __init__.py
│   ├── column_mapper.py        # Intelligent column alias detection & schema mapping
│   ├── formatters.py           # Indian Rupee (₹) & Lakhs/Crores number formatters
│   ├── data_loader.py          # CSV/Excel ingestion & synthetic Superstore generator
│   ├── data_cleaner.py         # Data validation, duplicate detection & quality auditing
│   ├── database.py             # SQLite connection manager, dimensional ETL & query runner
│   ├── kpi_calculator.py       # Financial KPI formulas & period comparison engine
│   ├── sales_analysis.py       # Time-series trends, discount elasticity & sunburst
│   ├── customer_analysis.py    # Segment economics, top customer ranks & repeat cohorts
│   ├── product_analysis.py     # Quadrant matrices, loss leaders & margin diluters
│   ├── regional_analysis.py    # Territory performance & US State choropleth maps
│   ├── insights.py             # Automated 4-pillar business insight generation engine
│   ├── forecasting.py          # Chronological hold-out time series forecasting
│   ├── state_manager.py        # Centralized Streamlit session state management
│   └── ui_components.py        # Enterprise KPI metric cards, filters & CSS injector
├── pages/
│   ├── sales_analysis.py       # Sales & Revenue subpage
│   ├── product_analysis.py     # Product portfolio diagnostics subpage
│   ├── customer_analysis.py    # Customer analytics subpage
│   ├── regional_analysis.py    # Regional performance subpage
│   ├── sql_analytics.py        # SQL studio subpage
│   ├── data_quality.py         # Data quality & audit subpage
│   └── forecasting.py          # Forecasting subpage
└── tests/
    ├── __init__.py
    ├── test_column_mapper.py   # Unit tests for alias detection and column mapping
    ├── test_custom_upload_workflow.py # Integration tests for custom uploads, FX, and DB refresh
    ├── test_data_cleaning.py   # Unit tests for data cleaning & validation
    ├── test_forecasting.py     # Tests for time-series forecasting & data requirements
    ├── test_inr_formatters.py  # Tests for Indian Rupee and comma grouping
    ├── test_kpis.py            # Unit tests for financial formulas & zero denominators
    └── test_sql.py             # Integration tests for database schema & 15 SQL queries
```

---

## 4. Installation & Quick Start

### 1. Environment Setup
```powershell
# Create virtual environment with Python 3.12
py -3.12 -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Automated Test Suite
```powershell
pytest -v
```
*(All 26 unit and integration tests will execute and pass).*

### 3. Launch Application
```powershell
python -m streamlit run app.py
```
Open your browser to `http://localhost:8501`.

---

## 5. How to Upload & Analyze Custom Data

1. **Launch the application:** The welcome screen displays a clean 3-step guide with an empty upload area.
2. **Select your file:** Drag and drop any `.csv`, `.xlsx`, or `.xls` file.
3. **Review Mappings:** The intelligent mapping screen automatically matches your headers (e.g., `Invoice No`, `Order Date`, `Gross Sales`, `Net Profit`, `Qty`). Adjust any dropdown if desired.
4. **Currency Settings:** Confirm the source currency (`INR`, `USD`, `EUR`, `GBP`, etc.). If uploading foreign currency, check the conversion box and provide an exchange rate if you wish to convert to INR.
5. **Confirm & Launch:** Click **"Confirm Mapping & Launch Dashboard"**. The full executive dashboard, scorecards, charts, SQL tables, and forecasts will immediately populate.
6. **Replace or Clear:** Use the sidebar **"🔄 Replace"** or **"🗑️ Clear"** buttons at any time to switch or unload datasets.

---

## 6. Testing & Quality Assurance

Run the test suite with:
```powershell
pytest tests/ -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: E:\SalesIQ-Sales Performance & Business Analytics
configfile: pytest.ini
collected 26 items

tests/test_column_mapper.py::test_normalize_string PASSED                [  3%]
tests/test_column_mapper.py::test_alias_detection_ecommerce_variant PASSED [  7%]
tests/test_column_mapper.py::test_validate_mapping_missing_sales PASSED  [ 11%]
tests/test_column_mapper.py::test_validate_mapping_with_optional_fields_missing PASSED [ 15%]
tests/test_column_mapper.py::test_apply_column_mapping PASSED            [ 19%]
tests/test_custom_upload_workflow.py::test_cleaner_with_exchange_rate PASSED [ 23%]
tests/test_custom_upload_workflow.py::test_partial_dataset_kpis_no_profit_no_date PASSED [ 26%]
tests/test_custom_upload_workflow.py::test_sql_refresh_without_duplicates PASSED [ 30%]
tests/test_custom_upload_workflow.py::test_query_compatibility_checks PASSED [ 34%]
tests/test_data_cleaning.py::test_schema_validation PASSED               [ 38%]
tests/test_data_cleaning.py::test_duplicate_removal PASSED               [ 42%]
tests/test_data_cleaning.py::test_inconsistent_dates_and_negative_sales PASSED [ 46%]
tests/test_data_cleaning.py::test_empty_dataframe_cleaning PASSED        [ 50%]
tests/test_forecasting.py::test_insufficient_data_handling PASSED        [ 53%]
tests/test_forecasting.py::test_forecast_execution_with_sufficient_data PASSED [ 57%]
tests/test_inr_formatters.py::test_inr_currency_formatting PASSED        [ 61%]
tests/test_inr_formatters.py::test_negative_inr_currency_formatting PASSED [ 65%]
tests/test_inr_formatters.py::test_indian_number_grouping PASSED         [ 69%]
tests/test_inr_formatters.py::test_edge_cases_and_missing_values PASSED  [ 73%]
tests/test_inr_formatters.py::test_inr_compact_notation PASSED           [ 76%]
tests/test_kpis.py::test_standard_kpi_calculations PASSED                [ 80%]
tests/test_kpis.py::test_zero_denominator_safe_handling PASSED           [ 84%]
tests/test_kpis.py::test_period_growth_calculation PASSED                [ 88%]
tests/test_sql.py::test_schema_and_predefined_queries_exist PASSED       [ 92%]
tests/test_sql.py::test_execute_all_15_business_queries PASSED           [ 96%]
tests/test_sql.py::test_kpi_consistency_python_vs_sql PASSED             [100%]

============================= 26 passed in 3.50s ==============================
```
