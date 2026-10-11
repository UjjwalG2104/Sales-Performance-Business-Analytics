"""
Integration Tests for SalesIQ SQLite Database and 15 SQL Business Queries.
"""
import pandas as pd
import pytest
from src.database import DatabaseManager


@pytest.fixture(scope="module")
def db_instance():
    from src.data_loader import ensure_sample_dataset_exists, load_file
    from src.data_cleaner import DataCleaner
    db = DatabaseManager()
    db.initialize_schema()
    check_df = db.execute_query("SELECT COUNT(*) as cnt FROM fact_orders;")
    if int(check_df.loc[0, "cnt"]) == 0:
        sample_path = ensure_sample_dataset_exists()
        raw, _ = load_file(sample_path)
        cleaner = DataCleaner(raw)
        clean_df, _ = cleaner.clean()
        db.load_cleaned_data_to_db(clean_df, replace=True)
    return db


def test_schema_and_predefined_queries_exist(db_instance):
    queries = db_instance.load_predefined_queries()
    assert len(queries) >= 15, f"Expected at least 15 SQL queries, found {len(queries)}"


def test_execute_all_15_business_queries(db_instance):
    queries = db_instance.load_predefined_queries()
    for q in queries:
        query_id = q["id"]
        title = q["title"]
        sql_text = q["sql"]
        result_df = db_instance.execute_query(sql_text)
        assert isinstance(result_df, pd.DataFrame), f"Query {query_id} ({title}) failed to return DataFrame"
        assert not result_df.empty or len(result_df.columns) > 0, f"Query {query_id} ({title}) returned invalid schema"


def test_kpi_consistency_python_vs_sql(db_instance):
    # Query 1 calculates total sales and total profit
    q1_df = db_instance.execute_query("""
        SELECT 
            ROUND(SUM(sales), 2) AS total_revenue,
            ROUND(SUM(profit), 2) AS total_profit,
            COUNT(DISTINCT order_id) AS total_orders
        FROM fact_orders;
    """)
    assert len(q1_df) == 1
    sql_rev = float(q1_df.loc[0, "total_revenue"])
    sql_orders = int(q1_df.loc[0, "total_orders"])

    raw_orders = db_instance.execute_query("SELECT sales, order_id FROM fact_orders;")
    py_rev = round(float(raw_orders["sales"].sum()), 2)
    py_orders = int(raw_orders["order_id"].nunique())

    assert abs(sql_rev - py_rev) < 0.01, f"Mismatch: SQL Rev {sql_rev} vs Python Rev {py_rev}"
    assert sql_orders == py_orders, f"Mismatch: SQL Orders {sql_orders} vs Python Orders {py_orders}"
