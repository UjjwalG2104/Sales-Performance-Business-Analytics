"""
SalesIQ — Indian Rupee (INR) & Indian Number Formatting Utilities.
Implements the Indian numbering system (Lakhs & Crores grouping)
with strict adherence to currency standards.
"""
from typing import Optional, Union
import numpy as np
import pandas as pd


def format_indian_number(
    val: Union[int, float, str, None],
    decimals: int = 0
) -> str:
    """
    Formats a numeric value using the Indian numbering system (2,2,3 grouping).
    Example: 1234567 -> 12,34,567
             1234567.89 (decimals=2) -> 12,34,567.89
    """
    if val is None or pd.isna(val):
        return "—"

    try:
        num = float(val)
    except (ValueError, TypeError):
        return str(val)

    if np.isnan(num) or np.isinf(num):
        return "—"

    is_negative = num < 0
    num = abs(num)

    if decimals > 0:
        formatted_float = f"{num:.{decimals}f}"
        int_part, dec_part = formatted_float.split(".")
    else:
        int_part = str(int(round(num)))
        dec_part = ""

    # Indian grouping algorithm
    if len(int_part) <= 3:
        grouped_int = int_part
    else:
        last_three = int_part[-3:]
        remaining = int_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        grouped_int = ",".join(groups) + "," + last_three

    result = f"{grouped_int}.{dec_part}" if dec_part else grouped_int
    return f"-{result}" if is_negative else result


def format_inr(
    val: Union[int, float, str, None],
    decimals: int = 2,
    symbol: str = "₹",
    include_symbol: bool = True
) -> str:
    """
    Formats a numeric value in Indian Rupees (INR) with the ₹ symbol
    and Indian comma grouping.
    Examples:
        123456.78 -> ₹1,23,456.78
        -123456.78 -> -₹1,23,456.78
        0 -> ₹0.00
    """
    if val is None or pd.isna(val):
        return "—"

    try:
        num = float(val)
    except (ValueError, TypeError):
        return str(val)

    if np.isnan(num) or np.isinf(num):
        return "—"

    is_negative = num < 0
    num = abs(num)

    formatted_num = format_indian_number(num, decimals=decimals)
    sym = symbol if include_symbol else ""

    if is_negative:
        return f"-{sym}{formatted_num}"
    return f"{sym}{formatted_num}"


def format_inr_compact(
    val: Union[int, float, None],
    symbol: str = "₹"
) -> str:
    """
    Formats large amounts in Indian compact notation (Lakhs / Crores).
    1 Cr = 1,00,00,000 (10^7)
    1 L  = 1,00,000    (10^5)
    1 K  = 1,000       (10^3)
    """
    if val is None or pd.isna(val):
        return "—"

    try:
        num = float(val)
    except (ValueError, TypeError):
        return str(val)

    is_negative = num < 0
    num = abs(num)

    if num >= 1e7:
        formatted = f"{num / 1e7:.2f} Cr"
    elif num >= 1e5:
        formatted = f"{num / 1e5:.2f} L"
    elif num >= 1e3:
        formatted = f"{num / 1e3:.1f} K"
    else:
        formatted = f"{num:.2f}"

    return f"-{symbol}{formatted}" if is_negative else f"{symbol}{formatted}"


def format_percentage(val: Union[int, float, None], decimals: int = 1) -> str:
    """Formats a percentage value with % sign."""
    if val is None or pd.isna(val):
        return "—"
    try:
        num = float(val)
        return f"{num:+.{decimals}f}%" if num != 0 else f"0.0%"
    except (ValueError, TypeError):
        return "—"
