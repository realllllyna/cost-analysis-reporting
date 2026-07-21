"""Load transformed data into PostgreSQL staging and mart schemas.

This module supports:
- full or date-based incremental staging refreshes,
- loading master data and Excel data into staging,
- rebuilding all mart dimensions and facts,
- G/L entries with their original positive or negative sign,
- vendor and customer ledger facts,
- plan-cost facts.

The SQL in ``build_mart_tables`` is aligned with the supplied
``03_create_mart_tables.sql`` schema.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection

from config import Config
from db import get_engine


CHUNK_SIZE = 500

INTEGER_COLUMNS = {
    "entry_no",
    "source_entry_no",
    "dimension_set_id",
    "reversed_by_entry_no",
    "reversed_entry_no",
    "sorting_order",
    "plan_year",
    "plan_month",
}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def _quote_identifier(identifier: str) -> str:
    """Return a safely quoted PostgreSQL identifier."""

    if not identifier:
        raise ValueError("Database identifier must not be empty.")
    return '"' + identifier.replace('"', '""') + '"'



def _qualified_table(schema_name: str, table_name: str) -> str:
    """Return a quoted schema-qualified table name."""

    return f"{_quote_identifier(schema_name)}.{_quote_identifier(table_name)}"



def _to_python_value(value: Any, column_name: str | None = None) -> Any:
    """Convert pandas/NumPy scalar values to DB-driver-compatible values."""

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if column_name in INTEGER_COLUMNS:
        try:
            # Handles values such as 2026.0 without sending "2026.0" to INTEGER.
            return int(float(value))
        except (TypeError, ValueError, OverflowError):
            return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if isinstance(value, (date, datetime, Decimal, str, bool, int, float)):
        return value

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value



def _prepare_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame into SQLAlchemy executemany records."""

    records: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        records.append(
            {
                column: _to_python_value(value, column)
                for column, value in row.items()
            }
        )
    return records



def load_dataframe(
    df: pd.DataFrame | None,
    table_name: str,
    schema_name: str,
) -> None:
    """Append a transformed DataFrame to an existing PostgreSQL table."""

    if df is None:
        print(f"No DataFrame supplied for {schema_name}.{table_name}")
        return

    if df.empty:
        print(f"No rows to load into {schema_name}.{table_name}")
        return

    engine = get_engine()
    clean_df = df.copy().astype(object)
    clean_df = clean_df.where(pd.notnull(clean_df), None)

    columns = list(clean_df.columns)
    quoted_columns = ", ".join(_quote_identifier(column) for column in columns)
    parameters = ", ".join(f":{column}" for column in columns)
    target = _qualified_table(schema_name, table_name)

    insert_sql = text(
        f"""
        INSERT INTO {target} ({quoted_columns})
        VALUES ({parameters});
        """
    )

    records = _prepare_records(clean_df)
    total_loaded = 0

    try:
        with engine.begin() as conn:
            for start in range(0, len(records), CHUNK_SIZE):
                chunk = records[start : start + CHUNK_SIZE]
                conn.execute(insert_sql, chunk)
                total_loaded += len(chunk)

        print(f"Loaded {total_loaded} rows into {schema_name}.{table_name}")

    except Exception:
        print(f"Error while loading {schema_name}.{table_name}")
        print("Columns:", columns)
        print("Data types:")
        print(clean_df.dtypes)
        print("First rows:")
        print(clean_df.head(5))
        print("First record:")
        print(records[0] if records else None)
        raise



def truncate_table(
    schema_name: str,
    table_name: str,
    *,
    cascade: bool = False,
) -> None:
    """Truncate a table and restart identity columns."""

    engine = get_engine()
    target = _qualified_table(schema_name, table_name)
    cascade_sql = " CASCADE" if cascade else ""

    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {target} RESTART IDENTITY{cascade_sql};"))

    print(f"Truncated {schema_name}.{table_name}")



def delete_from_date(
    schema_name: str,
    table_name: str,
    date_column: str,
    start_date: str,
) -> None:
    """Delete staging rows whose date is on or after ``start_date``."""

    engine = get_engine()
    target = _qualified_table(schema_name, table_name)
    quoted_date_column = _quote_identifier(date_column)

    with engine.begin() as conn:
        result = conn.execute(
            text(
                f"""
                DELETE FROM {target}
                WHERE {quoted_date_column} >= :start_date;
                """
            ),
            {"start_date": start_date},
        )

    print(
        f"Deleted {result.rowcount} rows from {schema_name}.{table_name} "
        f"where {date_column} >= {start_date}"
    )



def refresh_transaction_table(
    df: pd.DataFrame | None,
    table_name: str,
    date_column: str,
    full_refresh: bool,
    incremental_start_date: str,
) -> None:
    """Refresh a transaction staging table fully or from a start date."""

    if full_refresh:
        truncate_table("staging", table_name)
    else:
        delete_from_date(
            schema_name="staging",
            table_name=table_name,
            date_column=date_column,
            start_date=incremental_start_date,
        )

    load_dataframe(df, table_name, "staging")


# ---------------------------------------------------------------------------
# Staging load
# ---------------------------------------------------------------------------


def load_staging_tables(
    gl_df: pd.DataFrame,
    vendor_ledger_df: pd.DataFrame,
    customer_ledger_df: pd.DataFrame,
    vendors_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    projects_df: pd.DataFrame,
    cost_centers_df: pd.DataFrame,
    financial_statement_layout_df: pd.DataFrame,
    plan_df: pd.DataFrame,
    full_refresh: bool,
    incremental_start_date: str,
) -> None:
    """Load all transformed NAV and Excel datasets into staging."""

    refresh_transaction_table(
        gl_df,
        "stg_gl_ledger_entries",
        "posting_date",
        full_refresh,
        incremental_start_date,
    )
    refresh_transaction_table(
        vendor_ledger_df,
        "stg_vendor_ledger_entries",
        "posting_date",
        full_refresh,
        incremental_start_date,
    )
    refresh_transaction_table(
        customer_ledger_df,
        "stg_customer_ledger_entries",
        "posting_date",
        full_refresh,
        incremental_start_date,
    )

    master_tables: list[tuple[pd.DataFrame, str]] = [
        (vendors_df, "stg_vendors"),
        (customers_df, "stg_customers"),
        (projects_df, "stg_projects"),
        (cost_centers_df, "stg_cost_centers"),
        (financial_statement_layout_df, "stg_financial_statement_layout"),
        (plan_df, "stg_plan_values"),
    ]

    for _, table_name in master_tables:
        truncate_table("staging", table_name)

    for dataframe, table_name in master_tables:
        load_dataframe(dataframe, table_name, "staging")

    print("Staging tables were loaded successfully.")


# ---------------------------------------------------------------------------
# Mart SQL helpers
# ---------------------------------------------------------------------------


def _execute(conn: Connection, sql: str) -> None:
    """Execute one SQL statement."""

    conn.execute(text(sql))



def _truncate_mart_tables(conn: Connection) -> None:
    """Truncate facts and dimensions in dependency order."""

    for table_name in (
        "fact_gl_entries",
        "fact_vendor_ledger_entries",
        "fact_customer_ledger_entries",
        "fact_plan_costs",
    ):
        _execute(
            conn,
            f"TRUNCATE TABLE mart.{table_name} RESTART IDENTITY CASCADE;",
        )

    for table_name in (
        "dim_vendor",
        "dim_customer",
        "dim_project",
        "dim_cost_center",
        "dim_gl_account",
        "dim_pnl_structure",
        "dim_date",
    ):
        _execute(
            conn,
            f"TRUNCATE TABLE mart.{table_name} RESTART IDENTITY CASCADE;",
        )



def _load_dim_date(conn: Connection) -> None:
    _execute(
        conn,
        f"""
        WITH all_dates AS (
            SELECT posting_date AS date_value
            FROM staging.stg_gl_ledger_entries
            WHERE posting_date IS NOT NULL

            UNION ALL
            SELECT posting_date
            FROM staging.stg_vendor_ledger_entries
            WHERE posting_date IS NOT NULL

            UNION ALL
            SELECT due_date
            FROM staging.stg_vendor_ledger_entries
            WHERE due_date IS NOT NULL

            UNION ALL
            SELECT posting_date
            FROM staging.stg_customer_ledger_entries
            WHERE posting_date IS NOT NULL

            UNION ALL
            SELECT due_date
            FROM staging.stg_customer_ledger_entries
            WHERE due_date IS NOT NULL

            UNION ALL
            SELECT plan_date
            FROM staging.stg_plan_values
            WHERE plan_date IS NOT NULL
        ),
        limits AS (
            -- Kalender beginnt nie vor NAV_START_DATE (verhindert Ausreißer-Daten)
            SELECT GREATEST(MIN(date_value)::DATE, DATE '{Config.NAV_START_DATE}') AS min_date,
                   MAX(date_value)::DATE AS max_date
            FROM all_dates
        )
        INSERT INTO mart.dim_date (
            date_id,
            date_value,
            year,
            quarter,
            month,
            month_name,
            day,
            year_month
        )
        SELECT
            TO_CHAR(day_value, 'YYYYMMDD')::INTEGER,
            day_value::DATE,
            EXTRACT(YEAR FROM day_value)::INTEGER,
            EXTRACT(QUARTER FROM day_value)::INTEGER,
            EXTRACT(MONTH FROM day_value)::INTEGER,
            CASE EXTRACT(MONTH FROM day_value)::INTEGER
                WHEN 1 THEN 'Januar'
                WHEN 2 THEN 'Februar'
                WHEN 3 THEN 'März'
                WHEN 4 THEN 'April'
                WHEN 5 THEN 'Mai'
                WHEN 6 THEN 'Juni'
                WHEN 7 THEN 'Juli'
                WHEN 8 THEN 'August'
                WHEN 9 THEN 'September'
                WHEN 10 THEN 'Oktober'
                WHEN 11 THEN 'November'
                WHEN 12 THEN 'Dezember'
            END,
            EXTRACT(DAY FROM day_value)::INTEGER,
            TO_CHAR(day_value, 'YYYY-MM')
        FROM limits
        CROSS JOIN LATERAL generate_series(
            limits.min_date,
            limits.max_date,
            INTERVAL '1 day'
        ) AS generated(day_value)
        WHERE limits.min_date IS NOT NULL
          AND limits.max_date IS NOT NULL
        ON CONFLICT (date_id) DO NOTHING;
        """,
    )



def _load_dim_pnl_structure(conn: Connection) -> None:
    _execute(
        conn,
        """
        WITH layout_rows AS (
            SELECT DISTINCT
                NULLIF(TRIM(pnl_level_00::TEXT), '') AS pnl_level_00,
                NULLIF(TRIM(pnl_level_0::TEXT), '') AS pnl_level_0,
                NULLIF(TRIM(pnl_level_1::TEXT), '') AS pnl_level_1,
                NULLIF(TRIM(pnl_level_2::TEXT), '') AS pnl_level_2,
                NULLIF(TRIM(pnl_level_3::TEXT), '') AS pnl_level_3
            FROM staging.stg_financial_statement_layout
        ),
        plan_rows AS (
            -- Only P&L paths that the layout does NOT already define.
            -- Prevents a duplicate (partial) row for a category the
            -- layout already provides in full.
            SELECT DISTINCT
                NULL::TEXT AS pnl_level_00,
                NULL::TEXT AS pnl_level_0,
                NULLIF(TRIM(p.pnl_level_1::TEXT), '') AS pnl_level_1,
                NULLIF(TRIM(p.pnl_level_2::TEXT), '') AS pnl_level_2,
                NULLIF(TRIM(p.pnl_level_3::TEXT), '') AS pnl_level_3
            FROM staging.stg_plan_values p
            WHERE NOT EXISTS (
                SELECT 1
                FROM layout_rows lr
                WHERE COALESCE(lr.pnl_level_1, '') = COALESCE(NULLIF(TRIM(p.pnl_level_1::TEXT), ''), '')
                  AND COALESCE(lr.pnl_level_2, '') = COALESCE(NULLIF(TRIM(p.pnl_level_2::TEXT), ''), '')
                  AND COALESCE(lr.pnl_level_3, '') = COALESCE(NULLIF(TRIM(p.pnl_level_3::TEXT), ''), '')
            )
        ),
        combined AS (
            SELECT * FROM layout_rows
            UNION
            SELECT * FROM plan_rows
        )
        INSERT INTO mart.dim_pnl_structure (
            pnl_level_00,
            pnl_level_0,
            pnl_level_1,
            pnl_level_2,
            pnl_level_3
        )
        SELECT
            pnl_level_00,
            pnl_level_0,
            pnl_level_1,
            pnl_level_2,
            pnl_level_3
        FROM combined
        WHERE pnl_level_00 IS NOT NULL
           OR pnl_level_0 IS NOT NULL
           OR pnl_level_1 IS NOT NULL
           OR pnl_level_2 IS NOT NULL
           OR pnl_level_3 IS NOT NULL;
        """,
    )



def _load_dim_gl_account(conn: Connection) -> None:
    _execute(
        conn,
        """
        WITH account_source AS (
            SELECT
                TRIM(fsl.gl_account_no::TEXT) AS gl_account_no,
                MAX(NULLIF(TRIM(fsl.gl_account_name::TEXT), '')) AS gl_account_name,
                MIN(dps.pnl_structure_id) AS pnl_structure_id
            FROM staging.stg_financial_statement_layout fsl
            LEFT JOIN mart.dim_pnl_structure dps
              ON COALESCE(dps.pnl_level_00,'') = COALESCE(NULLIF(TRIM(fsl.pnl_level_00::TEXT),''),'')
             AND COALESCE(dps.pnl_level_0,'')  = COALESCE(NULLIF(TRIM(fsl.pnl_level_0::TEXT),''),'')
             AND COALESCE(dps.pnl_level_1,'')  = COALESCE(NULLIF(TRIM(fsl.pnl_level_1::TEXT),''),'')
             AND COALESCE(dps.pnl_level_2,'')  = COALESCE(NULLIF(TRIM(fsl.pnl_level_2::TEXT),''),'')
             AND COALESCE(dps.pnl_level_3,'')  = COALESCE(NULLIF(TRIM(fsl.pnl_level_3::TEXT),''),'')

            WHERE NULLIF(TRIM(fsl.gl_account_no::TEXT),'') IS NOT NULL

            GROUP BY
                TRIM(fsl.gl_account_no::TEXT)
        )

        INSERT INTO mart.dim_gl_account
        (
            gl_account_no,
            gl_account_name,
            pnl_structure_id
        )

        SELECT
            gl_account_no,
            gl_account_name,
            pnl_structure_id
        FROM account_source

        UNION

        SELECT
            TRIM(gle.gl_account_no::TEXT),
            MAX(NULLIF(TRIM(gle.gl_account_name::TEXT),'')),
            NULL::INTEGER
        FROM staging.stg_gl_ledger_entries gle
        WHERE NULLIF(TRIM(gle.gl_account_no::TEXT),'') IS NOT NULL
          AND NOT EXISTS (
                SELECT 1
                FROM account_source s
                WHERE s.gl_account_no =
                      TRIM(gle.gl_account_no::TEXT)
          )
        GROUP BY
            TRIM(gle.gl_account_no::TEXT)

        ON CONFLICT (gl_account_no)
        DO UPDATE
        SET
            gl_account_name =
                COALESCE(EXCLUDED.gl_account_name,
                         mart.dim_gl_account.gl_account_name),

            pnl_structure_id =
                COALESCE(EXCLUDED.pnl_structure_id,
                         mart.dim_gl_account.pnl_structure_id);
        """,
    )



def _load_dim_vendor(conn: Connection) -> None:
    _execute(
        conn,
        """
        INSERT INTO mart.dim_vendor (
            vendor_no,
            vendor_name,
            search_name,
            post_code,
            country_region_code,
            phone_no,
            blocked
        )
        SELECT DISTINCT ON (
            TRIM(sv.vendor_no::TEXT)
        )
            TRIM(sv.vendor_no::TEXT) AS vendor_no,
            NULLIF(TRIM(sv.vendor_name::TEXT), '') AS vendor_name,
            NULLIF(TRIM(sv.search_name::TEXT), '') AS search_name,
            NULLIF(TRIM(sv.post_code::TEXT), '') AS post_code,
            NULLIF(
                TRIM(sv.country_region_code::TEXT),
                ''
            ) AS country_region_code,
            NULLIF(TRIM(sv.phone_no::TEXT), '') AS phone_no,
            sv.blocked
        FROM staging.stg_vendors sv
        WHERE NULLIF(
            TRIM(sv.vendor_no::TEXT),
            ''
        ) IS NOT NULL
        ORDER BY
            TRIM(sv.vendor_no::TEXT),
            CASE
                WHEN NULLIF(
                    TRIM(sv.vendor_name::TEXT),
                    ''
                ) IS NOT NULL
                THEN 0
                ELSE 1
            END,
            NULLIF(TRIM(sv.vendor_name::TEXT), '')
        ON CONFLICT (vendor_no)
        DO UPDATE SET
            vendor_name = COALESCE(
                EXCLUDED.vendor_name,
                mart.dim_vendor.vendor_name
            ),
            search_name = COALESCE(
                EXCLUDED.search_name,
                mart.dim_vendor.search_name
            ),
            post_code = COALESCE(
                EXCLUDED.post_code,
                mart.dim_vendor.post_code
            ),
            country_region_code = COALESCE(
                EXCLUDED.country_region_code,
                mart.dim_vendor.country_region_code
            ),
            phone_no = COALESCE(
                EXCLUDED.phone_no,
                mart.dim_vendor.phone_no
            ),
            blocked = COALESCE(
                EXCLUDED.blocked,
                mart.dim_vendor.blocked
            );

        WITH additional_vendor_source AS (
            SELECT
                NULLIF(
                    TRIM(vendor_no::TEXT),
                    ''
                ) AS vendor_no,
                NULLIF(
                    TRIM(vendor_name::TEXT),
                    ''
                ) AS vendor_name
            FROM staging.stg_vendor_ledger_entries

            UNION ALL

            SELECT
                NULLIF(
                    TRIM(vendor_no::TEXT),
                    ''
                ) AS vendor_no,
                NULLIF(
                    TRIM(vendor_name::TEXT),
                    ''
                ) AS vendor_name
            FROM staging.stg_plan_values
        ),
        deduplicated_vendors AS (
            SELECT
                vendor_no,
                MAX(vendor_name) AS vendor_name
            FROM additional_vendor_source
            WHERE vendor_no IS NOT NULL
            GROUP BY
                vendor_no
        )
        INSERT INTO mart.dim_vendor (
            vendor_no,
            vendor_name
        )
        SELECT
            src.vendor_no,
            src.vendor_name
        FROM deduplicated_vendors src
        ON CONFLICT (vendor_no)
        DO UPDATE SET
            vendor_name = COALESCE(
                mart.dim_vendor.vendor_name,
                EXCLUDED.vendor_name
            );
        """,
    )



def _load_dim_customer(conn: Connection) -> None:
    _execute(
        conn,
        """
        INSERT INTO mart.dim_customer (
            customer_no, customer_name, phone_no
        )
        SELECT DISTINCT ON (TRIM(sc.customer_no::TEXT))
            TRIM(sc.customer_no::TEXT),
            NULLIF(TRIM(sc.customer_name::TEXT), ''),
            NULLIF(TRIM(sc.phone_no::TEXT), '')
        FROM staging.stg_customers sc
        WHERE NULLIF(TRIM(sc.customer_no::TEXT), '') IS NOT NULL
        ORDER BY TRIM(sc.customer_no::TEXT)
        ON CONFLICT (customer_no) DO UPDATE SET
            customer_name = COALESCE(EXCLUDED.customer_name, mart.dim_customer.customer_name),
            phone_no = COALESCE(EXCLUDED.phone_no, mart.dim_customer.phone_no);

        INSERT INTO mart.dim_customer (customer_no, customer_name)
        SELECT DISTINCT
            TRIM(cle.customer_no::TEXT),
            NULLIF(TRIM(cle.customer_name::TEXT), '')
        FROM staging.stg_customer_ledger_entries cle
        WHERE NULLIF(TRIM(cle.customer_no::TEXT), '') IS NOT NULL
        ON CONFLICT (customer_no) DO UPDATE SET
            customer_name = COALESCE(mart.dim_customer.customer_name, EXCLUDED.customer_name);
        """,
    )



def _load_dim_project(conn: Connection) -> None:
    _execute(
        conn,
        """
        INSERT INTO mart.dim_project (
            project_no, project_name, status,
            project_manager_resource_no, project_manager_name,
            customer_no, starting_date, ending_date
        )
        SELECT DISTINCT ON (TRIM(sp.project_no::TEXT))
            TRIM(sp.project_no::TEXT),
            NULLIF(TRIM(sp.description::TEXT), ''),
            NULLIF(TRIM(sp.status::TEXT), ''),
            NULLIF(TRIM(sp.project_manager_resource_no::TEXT), ''),
            NULLIF(TRIM(sp.project_manager_name::TEXT), ''),
            NULLIF(TRIM(sp.customer_no::TEXT), ''),
            sp.starting_date,
            sp.ending_date
        FROM staging.stg_projects sp
        WHERE NULLIF(TRIM(sp.project_no::TEXT), '') IS NOT NULL
        ORDER BY TRIM(sp.project_no::TEXT)
        ON CONFLICT (project_no) DO UPDATE SET
            project_name = COALESCE(EXCLUDED.project_name, mart.dim_project.project_name),
            status = COALESCE(EXCLUDED.status, mart.dim_project.status),
            project_manager_resource_no = COALESCE(EXCLUDED.project_manager_resource_no, mart.dim_project.project_manager_resource_no),
            project_manager_name = COALESCE(EXCLUDED.project_manager_name, mart.dim_project.project_manager_name),
            customer_no = COALESCE(EXCLUDED.customer_no, mart.dim_project.customer_no),
            starting_date = COALESCE(EXCLUDED.starting_date, mart.dim_project.starting_date),
            ending_date = COALESCE(EXCLUDED.ending_date, mart.dim_project.ending_date);

        INSERT INTO mart.dim_project (project_no)
        SELECT DISTINCT TRIM(src.project_no)
        FROM (
            SELECT NULLIF(TRIM(job_no::TEXT), '') AS project_no
            FROM staging.stg_gl_ledger_entries
            UNION ALL
            SELECT NULLIF(TRIM(global_dimension_2_code::TEXT), '')
            FROM staging.stg_gl_ledger_entries
            UNION ALL
            SELECT NULLIF(TRIM(global_dimension_2_code::TEXT), '')
            FROM staging.stg_vendor_ledger_entries
            UNION ALL
            SELECT NULLIF(TRIM(global_dimension_2_code::TEXT), '')
            FROM staging.stg_customer_ledger_entries
        ) src
        WHERE src.project_no IS NOT NULL
        ON CONFLICT (project_no) DO NOTHING;
        """,
    )



def _load_dim_cost_center(conn: Connection) -> None:
    _execute(
        conn,
        """
        INSERT INTO mart.dim_cost_center (
            cost_center_code, cost_center_name
        )
        SELECT DISTINCT ON (TRIM(scc.cost_center_code::TEXT))
            TRIM(scc.cost_center_code::TEXT),
            NULLIF(TRIM(scc.cost_center_name::TEXT), '')
        FROM staging.stg_cost_centers scc
        WHERE NULLIF(TRIM(scc.cost_center_code::TEXT), '') IS NOT NULL
        ORDER BY TRIM(scc.cost_center_code::TEXT)
        ON CONFLICT (cost_center_code) DO UPDATE SET
            cost_center_name = COALESCE(EXCLUDED.cost_center_name, mart.dim_cost_center.cost_center_name);

        INSERT INTO mart.dim_cost_center (cost_center_code)
        SELECT DISTINCT TRIM(src.cost_center_code)
        FROM (
            SELECT NULLIF(TRIM(global_dimension_1_code::TEXT), '') AS cost_center_code
            FROM staging.stg_gl_ledger_entries
            UNION ALL
            SELECT NULLIF(TRIM(global_dimension_1_code::TEXT), '')
            FROM staging.stg_vendor_ledger_entries
            UNION ALL
            SELECT NULLIF(TRIM(global_dimension_1_code::TEXT), '')
            FROM staging.stg_customer_ledger_entries
        ) src
        WHERE src.cost_center_code IS NOT NULL
        ON CONFLICT (cost_center_code) DO NOTHING;
        """,
    )



def _load_fact_gl_entries(conn: Connection) -> None:
    _execute(
        conn,
        """
        WITH vendor_by_document AS (
            SELECT DISTINCT ON (document_no)
                document_no::TEXT,
                NULLIF(TRIM(vendor_no::TEXT), '') AS vendor_no,
                NULLIF(TRIM(global_dimension_1_code::TEXT), '') AS cost_center_code,
                NULLIF(TRIM(global_dimension_2_code::TEXT), '') AS project_no
            FROM staging.stg_vendor_ledger_entries
            WHERE NULLIF(TRIM(document_no::TEXT), '') IS NOT NULL
            ORDER BY document_no, entry_no
        ),
        customer_by_document AS (
            SELECT DISTINCT ON (document_no)
                document_no::TEXT,
                NULLIF(TRIM(customer_no::TEXT), '') AS customer_no,
                NULLIF(TRIM(global_dimension_1_code::TEXT), '') AS cost_center_code,
                NULLIF(TRIM(global_dimension_2_code::TEXT), '') AS project_no
            FROM staging.stg_customer_ledger_entries
            WHERE NULLIF(TRIM(document_no::TEXT), '') IS NOT NULL
            ORDER BY document_no, entry_no
        )
        INSERT INTO mart.fact_gl_entries (
            posting_date_id, pnl_structure_id, gl_account_id,
            vendor_id, customer_id, project_id, cost_center_id,
            source_entry_no, document_no, external_document_no, document_type,
            description, source_code,
            amount
        )
        SELECT
            dd.date_id,
            dga.pnl_structure_id,
            dga.gl_account_id,
            dv.vendor_id,
            dcu.customer_id,
            dp.project_id,
            dcc.cost_center_id,
            gle.entry_no,
            gle.document_no::TEXT,
            gle.external_document_no::TEXT,
            gle.document_type::TEXT,
            gle.description::TEXT,
            gle.source_code::TEXT,
            gle.amount
        FROM staging.stg_gl_ledger_entries gle
        LEFT JOIN mart.dim_date dd
          ON dd.date_value = gle.posting_date
        LEFT JOIN mart.dim_gl_account dga
          ON dga.gl_account_no = TRIM(gle.gl_account_no::TEXT)
        LEFT JOIN vendor_by_document vbd
          ON vbd.document_no = gle.document_no::TEXT
        LEFT JOIN customer_by_document cbd
          ON cbd.document_no = gle.document_no::TEXT
        LEFT JOIN mart.dim_vendor dv
          ON dv.vendor_no = vbd.vendor_no
        LEFT JOIN mart.dim_customer dcu
          ON dcu.customer_no = cbd.customer_no
        LEFT JOIN mart.dim_project dp
          ON dp.project_no = COALESCE(
                NULLIF(TRIM(gle.job_no::TEXT), ''),
                NULLIF(TRIM(gle.global_dimension_2_code::TEXT), ''),
                vbd.project_no,
                cbd.project_no
             )
        LEFT JOIN mart.dim_cost_center dcc
          ON dcc.cost_center_code = COALESCE(
                NULLIF(TRIM(gle.global_dimension_1_code::TEXT), ''),
                vbd.cost_center_code,
                cbd.cost_center_code
             )
        WHERE gle.entry_no IS NOT NULL
        ON CONFLICT (source_entry_no) DO NOTHING;
        """,
    )



def _load_fact_vendor_ledger_entries(conn: Connection) -> None:
    _execute(
        conn,
        """
        INSERT INTO mart.fact_vendor_ledger_entries (
            posting_date_id, due_date_id,
            vendor_id, project_id, cost_center_id, source_entry_no,
            document_no, external_document_no, document_type, description,
            currency_code,
            amount, amount_lcy,
            remaining_amount, remaining_amount_lcy, open
        )
        SELECT
            posting_date.date_id,
            due_date.date_id,
            dv.vendor_id,
            dp.project_id,
            dcc.cost_center_id,
            vle.entry_no,
            vle.document_no::TEXT,
            vle.external_document_no::TEXT,
            vle.document_type::TEXT,
            vle.description::TEXT,
            vle.currency_code::TEXT,
            vle.amount,
            vle.amount_lcy,
            vle.remaining_amount,
            vle.remaining_amount_lcy,
            vle.open
        FROM staging.stg_vendor_ledger_entries vle
        LEFT JOIN mart.dim_date posting_date ON posting_date.date_value = vle.posting_date
        LEFT JOIN mart.dim_date due_date ON due_date.date_value = vle.due_date
        LEFT JOIN mart.dim_vendor dv
          ON dv.vendor_no = NULLIF(TRIM(vle.vendor_no::TEXT), '')
        LEFT JOIN mart.dim_project dp
          ON dp.project_no = NULLIF(TRIM(vle.global_dimension_2_code::TEXT), '')
        LEFT JOIN mart.dim_cost_center dcc
          ON dcc.cost_center_code = NULLIF(TRIM(vle.global_dimension_1_code::TEXT), '')
        WHERE vle.entry_no IS NOT NULL
        ON CONFLICT (source_entry_no) DO NOTHING;
        """,
    )



def _load_fact_customer_ledger_entries(conn: Connection) -> None:
    _execute(
        conn,
        """
        INSERT INTO mart.fact_customer_ledger_entries (
            posting_date_id, due_date_id,
            customer_id, project_id, cost_center_id, source_entry_no,
            document_no, external_document_no, document_type, description,
            currency_code,
            amount, amount_lcy,
            remaining_amount, remaining_amount_lcy, sales_lcy, open
        )
        SELECT
            posting_date.date_id,
            due_date.date_id,
            dcu.customer_id,
            dp.project_id,
            dcc.cost_center_id,
            cle.entry_no,
            cle.document_no::TEXT,
            cle.external_document_no::TEXT,
            cle.document_type::TEXT,
            cle.description::TEXT,
            cle.currency_code::TEXT,
            cle.amount,
            cle.amount_lcy,
            cle.remaining_amount,
            cle.remaining_amount_lcy,
            cle.sales_lcy,
            cle.open
        FROM staging.stg_customer_ledger_entries cle
        LEFT JOIN mart.dim_date posting_date ON posting_date.date_value = cle.posting_date
        LEFT JOIN mart.dim_date due_date ON due_date.date_value = cle.due_date
        LEFT JOIN mart.dim_customer dcu
          ON dcu.customer_no = NULLIF(TRIM(cle.customer_no::TEXT), '')
        LEFT JOIN mart.dim_project dp
          ON dp.project_no = NULLIF(TRIM(cle.global_dimension_2_code::TEXT), '')
        LEFT JOIN mart.dim_cost_center dcc
          ON dcc.cost_center_code = NULLIF(TRIM(cle.global_dimension_1_code::TEXT), '')
        WHERE cle.entry_no IS NOT NULL
        ON CONFLICT (source_entry_no) DO NOTHING;
        """,
    )



def _load_fact_plan_costs(conn: Connection) -> None:
    _execute(
        conn,
        """
        INSERT INTO mart.fact_plan_costs (
            plan_date_id, pnl_structure_id,
            vendor_id, frequency, plan_amount
        )
        SELECT
            dd.date_id,
            dps.pnl_structure_id,
            dv.vendor_id,
            spv.frequency::TEXT,
            spv.plan_amount
        FROM staging.stg_plan_values spv
        LEFT JOIN mart.dim_date dd
          ON dd.date_value = spv.plan_date
        LEFT JOIN LATERAL (
            SELECT dps.pnl_structure_id
            FROM mart.dim_pnl_structure dps
            WHERE COALESCE(dps.pnl_level_1, '') = COALESCE(NULLIF(TRIM(spv.pnl_level_1::TEXT), ''), '')
              AND COALESCE(dps.pnl_level_2, '') = COALESCE(NULLIF(TRIM(spv.pnl_level_2::TEXT), ''), '')
              AND COALESCE(dps.pnl_level_3, '') = COALESCE(NULLIF(TRIM(spv.pnl_level_3::TEXT), ''), '')
            ORDER BY dps.pnl_structure_id
            LIMIT 1
        ) dps ON TRUE
        LEFT JOIN mart.dim_vendor dv
          ON dv.vendor_no = NULLIF(TRIM(spv.vendor_no::TEXT), '')
        WHERE spv.plan_amount IS NOT NULL;
        """,
    )


# ---------------------------------------------------------------------------
# Public mart build function
# ---------------------------------------------------------------------------


def build_mart_tables() -> None:
    """Rebuild all mart dimensions and facts in one transaction."""

    engine = get_engine()

    with engine.begin() as conn:
        _truncate_mart_tables(conn)

        _load_dim_date(conn)
        _load_dim_pnl_structure(conn)
        _load_dim_gl_account(conn)
        _load_dim_vendor(conn)
        _load_dim_customer(conn)
        _load_dim_project(conn)
        _load_dim_cost_center(conn)

        _load_fact_gl_entries(conn)
        _load_fact_vendor_ledger_entries(conn)
        _load_fact_customer_ledger_entries(conn)
        _load_fact_plan_costs(conn)

    print("Mart tables were built successfully.")