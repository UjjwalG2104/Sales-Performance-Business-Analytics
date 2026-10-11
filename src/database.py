"""
SalesIQ — SQLite Database and Analytics Engine Module.
Manages relational schema creation, data warehousing ETL, query execution,
and integration with the 15 standard SQL business analytics queries.
Adapts gracefully to custom uploaded schemas.
"""
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import pandas as pd

from config.settings import DB_PATH, SCHEMA_PATH, SQL_QUERIES_PATH


class DatabaseManager:
    """
    Manages SQLite database connections, schema provisioning, ETL ingestion,
    and analytical query execution for SalesIQ.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Returns an active SQLite database connection with row factory enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize_schema(self, schema_file: Optional[Union[str, Path]] = None) -> None:
        """Executes the DDL statements in schema.sql to initialize tables, indexes, and views."""
        schema_p = Path(schema_file) if schema_file else SCHEMA_PATH
        if not schema_p.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_p}")

        sql_script = schema_p.read_text(encoding="utf-8")
        with self.get_connection() as conn:
            conn.executescript(sql_script)

    def clear_all_tables(self) -> None:
        """Transactionally empties all dimensional and fact tables."""
        self.initialize_schema()
        with self.get_connection() as conn:
            conn.execute("DELETE FROM fact_orders;")
            conn.execute("DELETE FROM dim_customers;")
            conn.execute("DELETE FROM dim_locations;")
            conn.execute("DELETE FROM dim_products;")
            conn.commit()

    def load_cleaned_data_to_db(self, df: pd.DataFrame, replace: bool = True) -> int:
        """
        Performs dimensional ETL from the cleaned dataframe into:
        - dim_customers
        - dim_locations
        - dim_products
        - fact_orders
        Dynamically handles partial schemas from custom dataset uploads.
        Returns total number of order rows loaded.
        """
        if df is None or df.empty:
            self.clear_all_tables()
            return 0

        self.initialize_schema()
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if replace:
                cursor.execute("DELETE FROM fact_orders;")
                cursor.execute("DELETE FROM dim_customers;")
                cursor.execute("DELETE FROM dim_locations;")
                cursor.execute("DELETE FROM dim_products;")

            # 1. Populate dim_customers (with fallbacks if columns absent)
            cust_rows = []
            seen_cust: Set[str] = set()
            for idx, row in df.iterrows():
                c_id = str(row.get("Customer ID") or f"CUST-{idx+1}").strip()
                c_name = str(row.get("Customer Name") or "Valued Customer").strip()
                c_seg = str(row.get("Segment") or "General").strip()
                if c_id not in seen_cust:
                    seen_cust.add(c_id)
                    cust_rows.append((c_id, c_name, c_seg))

            cursor.executemany(
                """
                INSERT OR REPLACE INTO dim_customers (customer_id, customer_name, segment)
                VALUES (?, ?, ?);
                """,
                cust_rows
            )

            # 2. Populate dim_locations (with fallbacks)
            loc_rows = []
            seen_loc: Set[Tuple[str, str, str, str, str]] = set()
            for _, row in df.iterrows():
                country = str(row.get("Country") or "India").strip()
                region = str(row.get("Region") or "All Regions").strip()
                state = str(row.get("State") or "National").strip()
                city = str(row.get("City") or "Main Territory").strip()
                zip_val = str(row.get("Postal Code") or "").strip()
                loc_key = (country, region, state, city, zip_val)
                if loc_key not in seen_loc:
                    seen_loc.add(loc_key)
                    loc_rows.append(loc_key)

            cursor.executemany(
                """
                INSERT OR IGNORE INTO dim_locations (country, region, state, city, postal_code)
                VALUES (?, ?, ?, ?, ?);
                """,
                loc_rows
            )

            # Build location lookup map
            cursor.execute("SELECT location_id, country, region, state, city, postal_code FROM dim_locations;")
            loc_lookup = {
                (row["country"], row["region"], row["state"], row["city"], str(row["postal_code"] or "")): row["location_id"]
                for row in cursor.fetchall()
            }

            # 3. Populate dim_products (with fallbacks)
            prod_rows = []
            seen_prod: Set[str] = set()
            for idx, row in df.iterrows():
                p_id = str(row.get("Product ID") or f"PRD-{idx+1}").strip()
                p_name = str(row.get("Product Name") or "General Merchandise").strip()
                cat = str(row.get("Category") or "General").strip()
                subcat = str(row.get("Sub-Category") or "Standard").strip()
                if p_id not in seen_prod:
                    seen_prod.add(p_id)
                    prod_rows.append((p_id, p_name, cat, subcat))

            cursor.executemany(
                """
                INSERT OR REPLACE INTO dim_products (product_id, product_name, category, sub_category)
                VALUES (?, ?, ?, ?);
                """,
                prod_rows
            )

            # 4. Populate fact_orders
            order_rows = []
            for idx, row in df.iterrows():
                order_id = str(row.get("Order ID") or f"ORD-{idx+1}").strip()
                
                # Dates
                if "Order Date" in row and pd.notna(row["Order Date"]):
                    try:
                        o_date = pd.to_datetime(row["Order Date"]).strftime("%Y-%m-%d")
                    except Exception:
                        o_date = datetime.now().strftime("%Y-%m-%d")
                else:
                    o_date = datetime.now().strftime("%Y-%m-%d")

                if "Ship Date" in row and pd.notna(row["Ship Date"]):
                    try:
                        s_date = pd.to_datetime(row["Ship Date"]).strftime("%Y-%m-%d")
                    except Exception:
                        s_date = o_date
                else:
                    s_date = o_date

                c_id = str(row.get("Customer ID") or f"CUST-{idx+1}").strip()
                p_id = str(row.get("Product ID") or f"PRD-{idx+1}").strip()

                country = str(row.get("Country") or "India").strip()
                region = str(row.get("Region") or "All Regions").strip()
                state = str(row.get("State") or "National").strip()
                city = str(row.get("City") or "Main Territory").strip()
                zip_val = str(row.get("Postal Code") or "").strip()
                loc_key = (country, region, state, city, zip_val)
                loc_id = loc_lookup.get(loc_key, 1)

                sales = float(row.get("Sales", 0.0))
                quantity = int(row.get("Quantity", 1))
                discount = float(row.get("Discount", 0.0))
                profit = float(row.get("Profit", 0.0))
                shipping = float(row.get("Shipping Cost", 0.0))

                order_rows.append((
                    order_id,
                    o_date,
                    s_date,
                    c_id,
                    int(loc_id),
                    p_id,
                    sales,
                    quantity,
                    discount,
                    profit,
                    shipping
                ))

            cursor.executemany(
                """
                INSERT INTO fact_orders (
                    order_id, order_date, ship_date, customer_id, location_id,
                    product_id, sales, quantity, discount, profit, shipping_cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                order_rows
            )
            conn.commit()
            return len(order_rows)

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def execute_query(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> pd.DataFrame:
        """Executes a SQL query against the database and returns a Pandas DataFrame."""
        with self.get_connection() as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            return pd.read_sql_query(query, conn)

    def load_predefined_queries(self) -> List[Dict[str, Any]]:
        """
        Parses `sql/business_queries.sql` and extracts the 15 predefined business queries,
        along with query names and descriptions.
        """
        if not SQL_QUERIES_PATH.exists():
            return []

        content = SQL_QUERIES_PATH.read_text(encoding="utf-8")
        blocks = content.split("-- [QUERY ")
        parsed = []

        for block in blocks:
            if not block.strip():
                continue
            lines = block.strip().splitlines()
            header_line = lines[0]
            idx_title = header_line.split("]:", 1)
            query_num = idx_title[0].strip()
            title = idx_title[1].strip() if len(idx_title) > 1 else f"Query {query_num}"

            purpose = ""
            sql_lines = []
            for line in lines[1:]:
                stripped = line.strip()
                if stripped.startswith("-- Purpose:"):
                    purpose = stripped.replace("-- Purpose:", "").strip()
                elif stripped.startswith("--"):
                    continue
                else:
                    sql_lines.append(line)

            sql_code = "\n".join(sql_lines).strip()
            if sql_code:
                parsed.append({
                    "id": int(query_num) if query_num.isdigit() else len(parsed) + 1,
                    "title": title,
                    "purpose": purpose,
                    "sql": sql_code
                })

        return parsed

    def check_query_compatibility(
        self,
        query_sql: str,
        df_columns: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates if a query can run safely against the current dataset's available fields.
        Returns (is_compatible, reason_if_not).
        """
        q_lower = query_sql.lower()
        cols_lower = [c.lower() for c in df_columns]

        if "profit" in q_lower and "profit" not in cols_lower:
            return False, "This query references profitability metrics, but the active dataset does not contain a 'Profit' column."
        if ("strftime" in q_lower or "order_date" in q_lower) and "order date" not in cols_lower and "order_date" not in cols_lower:
            return False, "This query performs temporal analysis, but the active dataset does not contain an 'Order Date' column."
        if "customer" in q_lower and "customer id" not in cols_lower and "customer name" not in cols_lower:
            return False, "This query aggregates by customer, but customer columns are not available in the active dataset."
        if "category" in q_lower and "category" not in cols_lower and "product name" not in cols_lower:
            return False, "This query groups by product category, but product/category columns are absent."
        if "region" in q_lower and "region" not in cols_lower and "state" not in cols_lower:
            return False, "This query evaluates regional territories, but region/location columns are absent."

        return True, None
