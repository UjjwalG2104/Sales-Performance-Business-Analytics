"""
SalesIQ — Application State Manager.
Centralizes session state initialization and cached dataset loading
across both app.py and individual page scripts.
Ensures custom dataset upload is the default, and never automatically loads the sample.
"""
from typing import Any, Dict, Optional
import pandas as pd
import streamlit as st

from config.settings import DEFAULT_CURRENCY_CODE, DEFAULT_CURRENCY_SYMBOL
from src.data_cleaner import DataCleaner
from src.data_loader import ensure_sample_dataset_exists, load_file
from src.database import DatabaseManager


def initialize_app_state():
    """
    Initializes global session state variables if not already initialized.
    Does NOT automatically load the Superstore sample dataset.
    """
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()

    if "currency_code" not in st.session_state:
        st.session_state.currency_code = DEFAULT_CURRENCY_CODE
    if "currency_symbol" not in st.session_state:
        st.session_state.currency_symbol = DEFAULT_CURRENCY_SYMBOL
    if "source_currency" not in st.session_state:
        st.session_state.source_currency = "INR"
    if "exchange_rate" not in st.session_state:
        st.session_state.exchange_rate = 1.0

    if "dataset_active" not in st.session_state:
        st.session_state.dataset_active = False
    if "raw_df" not in st.session_state:
        st.session_state.raw_df = None
    if "cleaned_df" not in st.session_state:
        st.session_state.cleaned_df = None
    if "audit" not in st.session_state:
        st.session_state.audit = None
    if "data_source_label" not in st.session_state:
        st.session_state.data_source_label = None
    if "column_mapping" not in st.session_state:
        st.session_state.column_mapping = None
    if "pending_upload" not in st.session_state:
        st.session_state.pending_upload = None


def set_active_dataset(
    raw_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    audit: Any,
    source_label: str,
    column_mapping: Optional[Dict[str, Optional[str]]] = None
):
    """Activates a dataset and updates the relational database."""
    st.session_state.raw_df = raw_df
    st.session_state.cleaned_df = cleaned_df
    st.session_state.audit = audit
    st.session_state.data_source_label = source_label
    st.session_state.column_mapping = column_mapping
    st.session_state.dataset_active = True
    st.session_state.pending_upload = None

    # Sync to SQLite database
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    st.session_state.db_manager.load_cleaned_data_to_db(cleaned_df)


def clear_active_dataset():
    """Clears the currently active dataset from session state and the database."""
    st.session_state.raw_df = None
    st.session_state.cleaned_df = None
    st.session_state.audit = None
    st.session_state.data_source_label = None
    st.session_state.column_mapping = None
    st.session_state.dataset_active = False
    st.session_state.pending_upload = None

    if "db_manager" in st.session_state:
        st.session_state.db_manager.clear_all_tables()


def load_sample_dataset():
    """Loads the Superstore sample dataset on explicit user request."""
    sample_path = ensure_sample_dataset_exists()
    raw, _ = load_file(sample_path)
    cleaner = DataCleaner(raw, exchange_rate=st.session_state.get("exchange_rate", 1.0))
    clean_df, audit = cleaner.clean()
    set_active_dataset(
        raw_df=raw,
        cleaned_df=clean_df,
        audit=audit,
        source_label="Superstore Sample Dataset"
    )
