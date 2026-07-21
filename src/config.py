import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _get_bool_env(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable (true/1/yes/ja/y = True)."""

    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"true", "1", "yes", "ja", "y"}


def _get_int_env(name: str, default: int) -> int:
    """Read an integer environment variable."""

    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable {name} must be an integer, "
            f"but received: {value!r}"
        ) from exc


def _resolve_path(env_name: str, default_relative_path: str) -> Path:
    """Resolve a path from .env; relative paths are based on the project root."""

    path = Path(os.getenv(env_name, default_relative_path))
    if not path.is_absolute():
        path = BASE_DIR / path

    return path.resolve()


class Config:
    BASE_DIR = BASE_DIR

    # Database
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = _get_int_env("DB_PORT", 55432)
    DB_NAME = os.getenv("DB_NAME", "cost_analysis_reporting")
    DB_USER = os.getenv("DB_USER", "cost_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    # Business Central access
    NAV_BASE_URL = os.getenv("NAV_BASE_URL", "")
    NAV_USERNAME = os.getenv("NAV_USERNAME", "")
    NAV_PASSWORD = os.getenv("NAV_PASSWORD", "")
    NAV_COMPANY = os.getenv("NAV_COMPANY", "ETC Solutions GmbH")

    # NAV OData services (published web service pages)
    NAV_GL_ENTRIES_SERVICE = os.getenv("NAV_GL_ENTRIES_SERVICE", "Sachposten")
    NAV_VENDOR_ENTRIES_SERVICE = os.getenv("NAV_VENDOR_ENTRIES_SERVICE", "Kreditorenposten")
    NAV_CUSTOMER_LEDGER_ENTRIES_SERVICE = os.getenv("NAV_CUSTOMER_LEDGER_ENTRIES_SERVICE", "Debitorenposten")
    NAV_VENDORS_SERVICE = os.getenv("NAV_VENDORS_SERVICE", "Kreditoren")
    NAV_CUSTOMERS_SERVICE = os.getenv("NAV_CUSTOMERS_SERVICE", "Debitor")
    NAV_PROJECTS_SERVICE = os.getenv("NAV_PROJECTS_SERVICE", "Projekte")
    NAV_COST_CENTERS_SERVICE = os.getenv("NAV_COST_CENTERS_SERVICE", "Kostenstellenplan")

    # NAV extraction
    NAV_TOP = os.getenv("NAV_TOP")
    NAV_PAGE_SIZE = _get_int_env("NAV_PAGE_SIZE", 1000)
    NAV_TIMEOUT_SECONDS = _get_int_env("NAV_TIMEOUT_SECONDS", 180)
    NAV_START_DATE = os.getenv("NAV_START_DATE", "2024-01-01")
    NAV_FULL_REFRESH = _get_bool_env("NAV_FULL_REFRESH", True)
    NAV_INCREMENTAL_DAYS = _get_int_env("NAV_INCREMENTAL_DAYS", 14)

    # Database setup (runs SQL 01-04 with DROP statements)
    RUN_DB_SETUP = _get_bool_env("RUN_DB_SETUP", False)

    # Excel sources
    EXCEL_FINANCIAL_STATEMENT_LAYOUT_PATH = _resolve_path(
        "EXCEL_FINANCIAL_STATEMENT_LAYOUT_PATH",
        "data/financial_statement_layout.xlsx",
    )
    EXCEL_PLAN_VALUES_PATH = _resolve_path(
        "EXCEL_PLAN_VALUES_PATH",
        "data/vendor_cost_plan_2026.xlsx",
    )

    # SQL scripts
    SQL_DIR = BASE_DIR / "sql"

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values before ETL execution."""

        required_values = {
            "DB_HOST": cls.DB_HOST,
            "DB_NAME": cls.DB_NAME,
            "DB_USER": cls.DB_USER,
            "DB_PASSWORD": cls.DB_PASSWORD,
            "NAV_BASE_URL": cls.NAV_BASE_URL,
            "NAV_USERNAME": cls.NAV_USERNAME,
            "NAV_PASSWORD": cls.NAV_PASSWORD,
            "NAV_COMPANY": cls.NAV_COMPANY,
        }

        missing_values = [
            name
            for name, value in required_values.items()
            if value is None or str(value).strip() == ""
        ]

        if missing_values:
            raise ValueError(
                "Missing required configuration values: " + ", ".join(missing_values)
            )

        if cls.NAV_PAGE_SIZE <= 0:
            raise ValueError("NAV_PAGE_SIZE must be greater than 0.")
        if cls.NAV_TIMEOUT_SECONDS <= 0:
            raise ValueError("NAV_TIMEOUT_SECONDS must be greater than 0.")
        if cls.NAV_INCREMENTAL_DAYS < 0:
            raise ValueError("NAV_INCREMENTAL_DAYS must not be negative.")
