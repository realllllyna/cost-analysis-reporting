from pathlib import Path

import pandas as pd

from config import Config


def _read_excel_file(file_path) -> pd.DataFrame:
    if not file_path:
        raise ValueError("Excel file path is missing in .env")

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Excel file not found: {path}. "
            "Please place the file in data/ or update the path in .env."
        )

    print(f"Reading Excel file: {path}")
    return pd.read_excel(path, engine="openpyxl")


def extract_financial_statement_layout_from_excel() -> pd.DataFrame:
    """Read financial_statement_layout.xlsx (GL account -> P&L levels)."""

    return _read_excel_file(Config.EXCEL_FINANCIAL_STATEMENT_LAYOUT_PATH)


def extract_plan_values_from_excel() -> pd.DataFrame:
    """Read vendor_cost_plan_2026.xlsx (cost plan per vendor and P&L level)."""

    return _read_excel_file(Config.EXCEL_PLAN_VALUES_PATH)
