"""
Configuration Settings for SalesIQ — Sales Performance & Business Analytics System.
"""
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
DATABASE_DIR = BASE_DIR / "database"
SQL_DIR = BASE_DIR / "sql"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure runtime directories exist
for path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, SAMPLE_DATA_DIR, DATABASE_DIR, SQL_DIR, ASSETS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = DATABASE_DIR / "salesiq.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
SQL_QUERIES_PATH = SQL_DIR / "business_queries.sql"

# Sample Data File
DEFAULT_SAMPLE_CSV = SAMPLE_DATA_DIR / "superstore_sales.csv"

# Currency Configuration
DEFAULT_CURRENCY_CODE = "INR"
DEFAULT_CURRENCY_SYMBOL = "₹"
SUPPORTED_SOURCE_CURRENCIES = ["INR", "USD", "EUR", "GBP", "AED", "SGD", "CAD", "AUD"]
DEFAULT_EXCHANGE_RATES = {
    "INR": 1.0,
    "USD": 86.50,
    "EUR": 91.20,
    "GBP": 109.50,
    "AED": 23.55,
    "SGD": 64.20,
    "CAD": 61.30,
    "AUD": 54.80,
}

# Required Schema Fields for SalesIQ dataset
REQUIRED_COLUMNS = [
    "Order ID",
    "Order Date",
    "Ship Date",
    "Customer ID",
    "Customer Name",
    "Segment",
    "Country",
    "State",
    "City",
    "Region",
    "Product ID",
    "Category",
    "Sub-Category",
    "Product Name",
    "Sales",
    "Quantity",
    "Discount",
    "Profit",
]

OPTIONAL_COLUMNS = [
    "Shipping Cost",
    "Postal Code",
]

# Color Palette (Enterprise BI Theme)
PALETTE = {
    "primary": "#1E3A8A",      # Deep Navy
    "secondary": "#2563EB",    # Royal Blue
    "accent": "#0D9488",       # Teal
    "success": "#059669",      # Emerald Green
    "warning": "#D97706",      # Amber
    "danger": "#DC2626",       # Crimson Red
    "background": "#F8FAFC",   # Slate 50
    "card_bg": "#FFFFFF",      # Pure White
    "border": "#E2E8F0",       # Slate 200
    "text_dark": "#0F172A",    # Slate 900
    "text_muted": "#64748B",   # Slate 500
}

CHART_COLORWAY = [
    "#1E3A8A", "#2563EB", "#0D9488", "#10B981",
    "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899",
    "#06B6D4", "#64748B"
]
