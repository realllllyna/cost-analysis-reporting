from datetime import date, timedelta

import pandas as pd

from config import Config
from nav_client import NavClient


def _get_top_param(top: int | None = None) -> int | None:
    """Resolve the OData $top limit: argument, then NAV_TOP, then no limit."""

    if top is None and Config.NAV_TOP and str(Config.NAV_TOP).strip():
        top = int(Config.NAV_TOP)

    if top is None:
        return None

    if top <= 0:
        raise ValueError("top must be greater than 0.")

    return top


def get_transaction_start_date() -> str:
    """
    Start date for transaction tables.

    Full refresh: NAV_START_DATE. Incremental: today - NAV_INCREMENTAL_DAYS.
    """

    if Config.NAV_FULL_REFRESH:
        return Config.NAV_START_DATE

    start = date.today() - timedelta(days=Config.NAV_INCREMENTAL_DAYS)
    return start.isoformat()


def _posting_date_filter() -> dict[str, str]:
    """OData filter for transaction tables."""

    return {"$filter": f"Posting_Date ge {get_transaction_start_date()}"}


def _extract_service(
    service_name: str,
    top: int | None = None,
    params: dict | None = None,
) -> pd.DataFrame:
    """Extract one NAV OData service into a DataFrame."""

    if not service_name or not service_name.strip():
        raise ValueError("NAV service name must not be empty.")

    request_params = dict(params) if params else {}

    top_value = _get_top_param(top)
    if top_value is not None:
        request_params["$top"] = top_value

    rows = NavClient().get_odata_values(
        company_name=Config.NAV_COMPANY,
        service_name=service_name,
        params=request_params or None,
    )

    return pd.DataFrame(rows)


def extract_gl_ledger_entries_from_nav(top: int | None = None) -> pd.DataFrame:
    return _extract_service(Config.NAV_GL_ENTRIES_SERVICE, top, _posting_date_filter())


def extract_vendor_ledger_entries_from_nav(top: int | None = None) -> pd.DataFrame:
    return _extract_service(Config.NAV_VENDOR_ENTRIES_SERVICE, top, _posting_date_filter())


def extract_customer_ledger_entries_from_nav(top: int | None = None) -> pd.DataFrame:
    return _extract_service(Config.NAV_CUSTOMER_LEDGER_ENTRIES_SERVICE, top, _posting_date_filter())


def extract_vendors_from_nav(top: int | None = None) -> pd.DataFrame:
    return _extract_service(Config.NAV_VENDORS_SERVICE, top)


def extract_customers_from_nav(top: int | None = None) -> pd.DataFrame:
    return _extract_service(Config.NAV_CUSTOMERS_SERVICE, top)


def extract_projects_from_nav(top: int | None = None) -> pd.DataFrame:
    return _extract_service(Config.NAV_PROJECTS_SERVICE, top)


def extract_cost_centers_from_nav(top: int | None = None) -> pd.DataFrame:
    return _extract_service(Config.NAV_COST_CENTERS_SERVICE, top)
