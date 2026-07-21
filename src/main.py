from pathlib import Path

from sqlalchemy import text

from config import Config
from db import get_engine
from extract_excel import (
    extract_financial_statement_layout_from_excel,
    extract_plan_values_from_excel,
)
from extract_nav import (
    extract_cost_centers_from_nav,
    extract_customer_ledger_entries_from_nav,
    extract_customers_from_nav,
    extract_gl_ledger_entries_from_nav,
    extract_projects_from_nav,
    extract_vendor_ledger_entries_from_nav,
    extract_vendors_from_nav,
    get_transaction_start_date,
)
from load import build_mart_tables, load_staging_tables
from transform import (
    transform_cost_centers,
    transform_customer_ledger_entries,
    transform_customers,
    transform_financial_statement_layout,
    transform_gl_ledger_entries,
    transform_plan_values,
    transform_projects,
    transform_vendor_ledger_entries,
    transform_vendors,
)


def execute_sql_file(file_path: Path) -> None:
    """Execute a complete SQL file against PostgreSQL."""

    with open(file_path, "r", encoding="utf-8") as file:
        sql = file.read()

    with get_engine().begin() as conn:
        conn.execute(text(sql))

    print(f"Executed SQL file: {file_path}")


def setup_database() -> None:
    """
    Rebuild schemas, staging tables, mart tables and views.

    Runs only when RUN_DB_SETUP=true, because SQL 01-04 contain DROP statements.
    """

    print("Setting up database...")
    for file_name in (
        "01_create_schemas.sql",
        "02_create_staging_tables.sql",
        "03_create_mart_tables.sql",
        "04_create_views.sql",
    ):
        execute_sql_file(Config.SQL_DIR / file_name)
    print("Database setup completed.")


def refresh_reporting_views() -> None:
    """Recreate only the reporting views (staging/mart tables are kept)."""

    print("Refreshing reporting views...")
    execute_sql_file(Config.SQL_DIR / "04_create_views.sql")
    print("Reporting views refreshed.")


def test_database_connection() -> None:
    """Check that PostgreSQL can be reached."""

    print("Testing database connection...")
    with get_engine().connect() as conn:
        version = conn.execute(text("SELECT version();")).scalar()
    print(version)


def run_etl() -> None:
    """
    Run the complete ETL process: validate config, connect, optionally rebuild
    the database, extract NAV/Excel, transform, load staging, build mart, refresh
    views.
    """

    Config.validate()
    test_database_connection()

    if Config.RUN_DB_SETUP:
        setup_database()
    else:
        print("Database setup skipped. Existing staging and mart tables are preserved.")

    transaction_start_date = get_transaction_start_date()
    print("Running ETL process...")
    print(f"RUN_DB_SETUP: {Config.RUN_DB_SETUP}")
    print(f"NAV_FULL_REFRESH: {Config.NAV_FULL_REFRESH}")
    print(f"Transaction start date: {transaction_start_date}")

    # Extract NAV
    print("Extracting NAV data...")
    gl_df = extract_gl_ledger_entries_from_nav()
    vendor_ledger_df = extract_vendor_ledger_entries_from_nav()
    customer_ledger_df = extract_customer_ledger_entries_from_nav()
    vendors_df = extract_vendors_from_nav()
    customers_df = extract_customers_from_nav()
    projects_df = extract_projects_from_nav()
    cost_centers_df = extract_cost_centers_from_nav()

    # Extract Excel
    print("Extracting Excel data...")
    financial_statement_layout_df = extract_financial_statement_layout_from_excel()
    plan_source_df = extract_plan_values_from_excel()

    # Transform
    print("Transforming data...")
    gl_entries = transform_gl_ledger_entries(gl_df)
    vendor_entries = transform_vendor_ledger_entries(vendor_ledger_df)
    customer_entries = transform_customer_ledger_entries(customer_ledger_df)
    vendors = transform_vendors(vendors_df)
    customers = transform_customers(customers_df)
    projects = transform_projects(projects_df)
    cost_centers = transform_cost_centers(cost_centers_df)
    financial_statement_layout = transform_financial_statement_layout(
        financial_statement_layout_df
    )
    plan_values = transform_plan_values(plan_source_df)

    print(f"G/L entries: {len(gl_entries)}")
    print(f"Vendor ledger entries: {len(vendor_entries)}")
    print(f"Customer ledger entries: {len(customer_entries)}")
    print(f"Vendors: {len(vendors)}")
    print(f"Customers: {len(customers)}")
    print(f"Projects: {len(projects)}")
    print(f"Cost centers: {len(cost_centers)}")
    print(f"Financial statement layout rows: {len(financial_statement_layout)}")
    print(f"Plan value rows: {len(plan_values)}")

    # Load staging
    print("Loading data into staging tables...")
    load_staging_tables(
        gl_df=gl_entries,
        vendor_ledger_df=vendor_entries,
        customer_ledger_df=customer_entries,
        vendors_df=vendors,
        customers_df=customers,
        projects_df=projects,
        cost_centers_df=cost_centers,
        financial_statement_layout_df=financial_statement_layout,
        plan_df=plan_values,
        full_refresh=Config.NAV_FULL_REFRESH,
        incremental_start_date=transaction_start_date,
    )

    # Build mart and refresh views
    print("Building mart tables...")
    build_mart_tables()
    refresh_reporting_views()

    print("=" * 70)
    print("ETL process finished successfully.")


if __name__ == "__main__":
    run_etl()
