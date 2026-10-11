"""
SalesIQ — Data Ingestion and Sample Dataset Generation Module.
Handles CSV and Excel loading, schema validation, and realistic synthetic Superstore data generation.
"""
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from config.settings import DEFAULT_SAMPLE_CSV, REQUIRED_COLUMNS, OPTIONAL_COLUMNS


def generate_sample_superstore_dataset(
    output_path: Optional[Union[str, Path]] = None,
    num_records: int = 3500,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic Superstore retail sales dataset spanning 4 years (2021-2024).
    Contains realistic economics, product hierarchies, regional patterns, discounts, and margins.
    """
    random.seed(seed)
    np.random.seed(seed)

    # Categories and Sub-Categories with base price ranges and margin profiles
    catalog = {
        "Technology": {
            "Phones": [("Apple iPhone 14 Pro", 999.0, 0.28), ("Samsung Galaxy S22", 799.0, 0.25), ("Google Pixel 7", 599.0, 0.22)],
            "Machines": [("Epson EcoTank Pro", 450.0, 0.18), ("HP LaserJet Enterprise", 820.0, 0.15), ("Brother All-in-One Printer", 320.0, 0.12)],
            "Accessories": [("Logitech MX Master 3S", 99.0, 0.35), ("Anker USB-C Docking Station", 149.0, 0.30), ("Apple Magic Keyboard", 119.0, 0.32)],
            "Copiers": [("Canon ImageCLASS Copier", 1200.0, 0.35), ("Sharp Digital Multi-Copier", 1850.0, 0.38), ("Xerox WorkCentre", 950.0, 0.28)],
        },
        "Furniture": {
            "Chairs": [("Herman Miller Aeron Chair", 850.0, 0.20), ("Steelcase Gesture Chair", 750.0, 0.18), ("Hon Mid-Back Mesh Task Chair", 220.0, 0.12)],
            "Tables": [("Bush Somerset L-Shaped Desk", 420.0, -0.05), ("Bavarian Solid Pine Dining Table", 600.0, -0.08), ("Conference Room Modular Table", 980.0, -0.02)],
            "Bookcases": [("Sauder Heritage Hill Bookcase", 260.0, 0.05), ("Bush Mission Oak 4-Shelf Bookcase", 180.0, -0.04), ("Atlantic Heavy Duty Metal Shelving", 210.0, 0.08)],
            "Furnishings": [("Eldon Executive Desk Pad", 35.0, 0.25), ("Howard Miller Wall Clock", 75.0, 0.30), ("Tenex Heavy Duty Floor Mat", 65.0, 0.22)],
        },
        "Office Supplies": {
            "Storage": [("Fellowes Bankers Box 10-Pack", 45.0, 0.22), ("Sterilite Clear Plastic Totes", 30.0, 0.20), ("Tennsco Steel Storage Cabinet", 380.0, 0.16)],
            "Binders": [("Avery Heavy Duty 3-Ring Binder", 12.0, 0.28), ("GBC VeloBind System Covers", 22.0, 0.32), ("Wilson Jones Ring Binder", 15.0, 0.25)],
            "Appliances": [("Krups 12-Cup Coffee Maker", 85.0, 0.20), ("Honeywell HEPA Air Purifier", 160.0, 0.24), ("Bionaire Compact Space Heater", 55.0, 0.15)],
            "Paper": [("Xerox 20lb Multipurpose Paper Ream", 9.5, 0.35), ("Hammermill Premium Color Copy Paper", 14.0, 0.38), ("Southworth 100% Cotton Paper", 24.0, 0.30)],
            "Art": [("Prismacolor Premier Colored Pencils", 38.0, 0.32), ("Bostitch Heavy Duty Stapler", 28.0, 0.25), ("Fiskars Precision Paper Trimmer", 42.0, 0.28)],
            "Envelopes": [("Tyvek Heavy Duty Mailers 100pk", 32.0, 0.30), ("Quality Park Security Envelopes", 18.0, 0.26)],
            "Labels": [("Avery Laser Mailing Labels 500pk", 22.0, 0.34), ("Dymo Thermal Address Labels", 28.0, 0.36)],
            "Supplies": [("Martin Yale High Speed Letter Opener", 125.0, -0.02), ("Fiskars Titanium Scissors", 16.0, 0.25)],
            "Fasteners": [("Acco Heavy Duty Paper Clips Box", 6.5, 0.30), ("Advantus Gem Paper Clips 1000ct", 8.0, 0.32)],
        }
    }

    # Geographic structure
    regions_geo = {
        "East": [
            ("New York", "New York City", "10024"),
            ("New York", "Buffalo", "14201"),
            ("Pennsylvania", "Philadelphia", "19104"),
            ("Massachusetts", "Boston", "02116"),
            ("Ohio", "Columbus", "43215"),
        ],
        "West": [
            ("California", "Los Angeles", "90012"),
            ("California", "San Francisco", "94102"),
            ("California", "San Diego", "92101"),
            ("Washington", "Seattle", "98101"),
            ("Arizona", "Phoenix", "85001"),
            ("Colorado", "Denver", "80202"),
        ],
        "Central": [
            ("Illinois", "Chicago", "60601"),
            ("Texas", "Houston", "77002"),
            ("Texas", "Dallas", "75201"),
            ("Texas", "Austin", "78701"),
            ("Michigan", "Detroit", "48226"),
            ("Minnesota", "Minneapolis", "55401"),
        ],
        "South": [
            ("Florida", "Miami", "33101"),
            ("Florida", "Orlando", "32801"),
            ("Georgia", "Atlanta", "30303"),
            ("North Carolina", "Charlotte", "28202"),
            ("Tennessee", "Nashville", "37201"),
            ("Virginia", "Richmond", "23219"),
        ]
    }

    segments = ["Consumer", "Corporate", "Home Office"]
    segment_weights = [0.52, 0.30, 0.18]

    # Customers pool (to generate repeat purchase behavior)
    num_customers = 250
    first_names = [
        "Emily", "Michael", "Sarah", "James", "Jessica", "David", "Ashley", "John", "Amanda", "Robert",
        "Jennifer", "William", "Elizabeth", "Daniel", "Megan", "Matthew", "Lauren", "Joseph", "Rachel", "Andrew",
        "Stephanie", "Christopher", "Nicole", "Joshua", "Samantha", "Brian", "Katherine", "Kevin", "Hannah", "Thomas"
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
        "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
    ]

    customers = []
    for i in range(1, num_customers + 1):
        c_id = f"CG-{10000 + i}"
        c_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        c_seg = np.random.choice(segments, p=segment_weights)
        c_reg = random.choice(list(regions_geo.keys()))
        c_state, c_city, c_zip = random.choice(regions_geo[c_reg])
        customers.append({
            "Customer ID": c_id,
            "Customer Name": c_name,
            "Segment": c_seg,
            "Region": c_reg,
            "State": c_state,
            "City": c_city,
            "Postal Code": c_zip,
            "Country": "United States"
        })

    # Date range: 2021-01-01 to 2024-12-31 (4 complete calendar years)
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2024, 12, 31)
    total_days = (end_date - start_date).days

    records = []
    order_counter = 10000

    # Build orders with 1-4 items per order
    while len(records) < num_records:
        order_counter += 1
        order_id = f"CA-202{random.randint(1, 4)}-{order_counter}"
        
        # Order Date with realistic Q4 seasonality boost
        day_offset = random.randint(0, total_days)
        o_date = start_date + timedelta(days=day_offset)
        # Seasonal bump towards Nov/Dec holiday rush
        if random.random() < 0.25:
            # Shift towards Q4 of that year
            month_choice = random.choice([10, 11, 12])
            o_date = datetime(o_date.year, month_choice, random.randint(1, 28))

        # Shipping Date (1 to 6 days after order)
        s_date = o_date + timedelta(days=random.randint(1, 6))

        # Pick customer (favoring repeat buyers)
        customer = random.choice(customers)
        
        # Number of line items in this order
        num_items = random.choices([1, 2, 3, 4], weights=[0.55, 0.28, 0.12, 0.05])[0]

        for item_idx in range(num_items):
            if len(records) >= num_records:
                break
                
            category = random.choices(["Technology", "Furniture", "Office Supplies"], weights=[0.35, 0.32, 0.33])[0]
            sub_category = random.choice(list(catalog[category].keys()))
            prod_name, base_price, base_margin = random.choice(catalog[category][sub_category])
            prod_id = f"PRD-{category[:3].upper()}-{sub_category[:3].upper()}-{abs(hash(prod_name)) % 10000:04d}"

            # Quantity purchased (1 to 9 units)
            quantity = random.choices(range(1, 10), weights=[0.35, 0.25, 0.15, 0.10, 0.06, 0.04, 0.02, 0.02, 0.01])[0]

            # Discount policy: standard 0.0, or promotional 0.1 to 0.7
            discount_choice = random.choices(
                [0.0, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7],
                weights=[0.50, 0.15, 0.10, 0.10, 0.07, 0.04, 0.03, 0.01]
            )[0]
            
            # Gross and Net Sales
            unit_price = round(base_price * np.random.uniform(0.95, 1.05), 2)
            gross_sales = unit_price * quantity
            sales = round(gross_sales * (1.0 - discount_choice), 2)

            # Realistic Profit Calculation:
            # Unit Cost = unit_price * (1.0 - base_margin)
            # High discounts erode margin and can cause net losses
            unit_cost = unit_price * (1.0 - base_margin)
            total_cost = unit_cost * quantity
            profit = round(sales - total_cost, 2)

            # Shipping Cost: driven by weight/category and quantity
            ship_rate = {"Technology": 12.0, "Furniture": 25.0, "Office Supplies": 5.0}[category]
            shipping_cost = round((ship_rate * (quantity ** 0.7)) * np.random.uniform(0.85, 1.15), 2)

            records.append({
                "Order ID": order_id,
                "Order Date": o_date.strftime("%Y-%m-%d"),
                "Ship Date": s_date.strftime("%Y-%m-%d"),
                "Customer ID": customer["Customer ID"],
                "Customer Name": customer["Customer Name"],
                "Segment": customer["Segment"],
                "Country": customer["Country"],
                "State": customer["State"],
                "City": customer["City"],
                "Region": customer["Region"],
                "Postal Code": customer["Postal Code"],
                "Product ID": prod_id,
                "Category": category,
                "Sub-Category": sub_category,
                "Product Name": prod_name,
                "Sales": sales,
                "Quantity": int(quantity),
                "Discount": float(discount_choice),
                "Profit": profit,
                "Shipping Cost": shipping_cost,
            })

    df = pd.DataFrame(records)

    # Inject minor realistic edge cases for the data cleaning module to handle and demonstrate:
    # 1. A few duplicate rows
    duplicate_rows = df.sample(n=8, random_state=42)
    # 2. A couple of whitespace/lowercase issues in categorical columns
    df = pd.concat([df, duplicate_rows], ignore_index=True)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_p, index=False)

    return df


def ensure_sample_dataset_exists() -> Path:
    """Ensures the default sample dataset exists on disk; creates it if missing."""
    if not DEFAULT_SAMPLE_CSV.exists():
        DEFAULT_SAMPLE_CSV.parent.mkdir(parents=True, exist_ok=True)
        generate_sample_superstore_dataset(output_path=DEFAULT_SAMPLE_CSV, num_records=3500)
    return DEFAULT_SAMPLE_CSV


def load_file(file_or_path: Union[str, Path, object]) -> Tuple[pd.DataFrame, str]:
    """
    Loads raw sales data from a CSV or Excel file.
    Accepts a filepath (str/Path) or a file-like upload buffer (Streamlit UploadedFile).
    Returns (DataFrame, file_type).
    """
    if hasattr(file_or_path, "name"):
        filename = file_or_path.name.lower()
        if filename.endswith(".csv"):
            df = pd.read_csv(file_or_path)
            return df, "CSV"
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_or_path)
            return df, "Excel"
        else:
            raise ValueError(f"Unsupported file format: {file_or_path.name}. Please upload a .csv or .xlsx file.")
    else:
        path = Path(file_or_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
            return df, "CSV"
        elif path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(path)
            return df, "Excel"
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}. Please provide a .csv or .xlsx file.")


def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
    """
    Validates that the dataframe contains all required columns.
    Returns (is_valid, missing_columns, extra_columns).
    """
    existing_cols = [str(c).strip() for c in df.columns]
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in existing_cols]
    extra_cols = [col for col in existing_cols if col not in REQUIRED_COLUMNS and col not in OPTIONAL_COLUMNS]
    is_valid = len(missing_cols) == 0
    return is_valid, missing_cols, extra_cols
