import pandas as pd


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Convert NAV/OData and Excel column names into consistent snake_case."""

    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.replace("@odata.etag", "odata_etag", regex=False)
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
        .str.replace(".", "_", regex=False)
        .str.replace("/", "_", regex=False)
        .str.lower()
    )
    return df


def merge_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge duplicate column names by taking the first non-empty value per row.

    Happens when two NAV fields map to the same target, e.g.
    person_responsible / project_manager -> project_manager_resource_no.
    """

    df = df.copy()
    duplicated_names = df.columns[df.columns.duplicated()].unique()

    for name in duplicated_names:
        merged = df.loc[:, df.columns == name].bfill(axis=1).iloc[:, 0]
        df = df.drop(columns=name)
        df[name] = merged

    return df


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip text columns; empty strings become None."""

    df = df.copy()
    for column in df.columns:
        if df[column].dtype == "object":
            df[column] = df[column].map(
                lambda v: None if pd.isna(v) or str(v).strip() == "" else str(v).strip()
            )
    return df


def to_date(series: pd.Series) -> pd.Series:
    """Convert a Series to Python date values (invalid -> NaT)."""

    try:
        return pd.to_datetime(series, errors="coerce", format="mixed").dt.date
    except TypeError:
        return pd.to_datetime(
            series.astype(str).str[:10], errors="coerce", format="%Y-%m-%d"
        ).dt.date


def to_numeric(series: pd.Series) -> pd.Series:
    """Convert a Series to numeric values (invalid -> NaN)."""

    return pd.to_numeric(series, errors="coerce")


def to_boolean(series: pd.Series) -> pd.Series:
    """Convert NAV boolean-like values to real Python booleans."""

    if series is None:
        return series

    return series.map(
        lambda v: None
        if pd.isna(v)
        else str(v).strip().lower() in {"true", "1", "yes", "ja", "y"}
    )


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Ensure all target columns exist (missing -> None, duplicates merged)."""

    df = merge_duplicate_columns(df.copy())
    for column in columns:
        if column not in df.columns:
            df[column] = None
    return df[columns]


def transform_gl_ledger_entries(df: pd.DataFrame) -> pd.DataFrame:
    """Transform NAV Sachposten into staging.stg_gl_ledger_entries."""

    df = normalize_column_names(df)

    rename_map = {
        "g_l_account_no": "gl_account_no",
        "g_l_account_name": "gl_account_name",
    }
    df = df.rename(columns=rename_map)

    target_columns = [
        "entry_no",
        "posting_date",
        "document_no",
        "document_type",
        "gl_account_no",
        "gl_account_name",
        "description",
        "amount",
        "job_no",
        "global_dimension_1_code",
        "global_dimension_2_code",
        "dimension_set_id",
        "source_code",
        "reason_code",
        "gen_posting_type",
        "gen_bus_posting_group",
        "gen_prod_posting_group",
        "external_document_no",
        "user_id",
        "reversed",
        "reversed_by_entry_no",
        "reversed_entry_no",
    ]
    df = ensure_columns(df, target_columns)
    df = clean_text_columns(df)

    df["posting_date"] = to_date(df["posting_date"])
    df["amount"] = to_numeric(df["amount"])
    df["entry_no"] = to_numeric(df["entry_no"])
    df["dimension_set_id"] = to_numeric(df["dimension_set_id"])
    df["reversed_by_entry_no"] = to_numeric(df["reversed_by_entry_no"])
    df["reversed_entry_no"] = to_numeric(df["reversed_entry_no"])
    df["reversed"] = to_boolean(df["reversed"])

    return df


def transform_vendor_ledger_entries(df: pd.DataFrame) -> pd.DataFrame:
    """Transform NAV Kreditorenposten into staging.stg_vendor_ledger_entries."""

    df = normalize_column_names(df)

    rename_map = {"remaining_amt_lcy": "remaining_amount_lcy"}
    df = df.rename(columns=rename_map)

    target_columns = [
        "entry_no",
        "vendor_no",
        "vendor_name",
        "posting_date",
        "document_no",
        "external_document_no",
        "description",
        "amount",
        "amount_lcy",
        "remaining_amount",
        "remaining_amount_lcy",
        "global_dimension_1_code",
        "global_dimension_2_code",
        "dimension_set_id",
        "document_type",
        "currency_code",
        "due_date",
        "open",
    ]
    df = ensure_columns(df, target_columns)
    df = clean_text_columns(df)

    df["posting_date"] = to_date(df["posting_date"])
    df["due_date"] = to_date(df["due_date"])
    df["entry_no"] = to_numeric(df["entry_no"])
    df["dimension_set_id"] = to_numeric(df["dimension_set_id"])
    df["amount"] = to_numeric(df["amount"])
    df["amount_lcy"] = to_numeric(df["amount_lcy"])
    df["remaining_amount"] = to_numeric(df["remaining_amount"])
    df["remaining_amount_lcy"] = to_numeric(df["remaining_amount_lcy"])
    df["open"] = to_boolean(df["open"])

    return df


def transform_customer_ledger_entries(df: pd.DataFrame) -> pd.DataFrame:
    """Transform NAV Debitorenposten into staging.stg_customer_ledger_entries."""

    df = normalize_column_names(df)

    rename_map = {
        "remaining_amt": "remaining_amount",
        "remaining_amt_lcy": "remaining_amount_lcy",
    }
    df = df.rename(columns=rename_map)

    target_columns = [
        "entry_no",
        "customer_no",
        "customer_name",
        "posting_date",
        "document_no",
        "external_document_no",
        "description",
        "amount",
        "amount_lcy",
        "remaining_amount",
        "remaining_amount_lcy",
        "sales_lcy",
        "global_dimension_1_code",
        "global_dimension_2_code",
        "dimension_set_id",
        "document_type",
        "currency_code",
        "due_date",
        "open",
    ]
    df = ensure_columns(df, target_columns)
    df = clean_text_columns(df)

    df["posting_date"] = to_date(df["posting_date"])
    df["due_date"] = to_date(df["due_date"])
    df["entry_no"] = to_numeric(df["entry_no"])
    df["dimension_set_id"] = to_numeric(df["dimension_set_id"])
    df["amount"] = to_numeric(df["amount"])
    df["amount_lcy"] = to_numeric(df["amount_lcy"])
    df["remaining_amount"] = to_numeric(df["remaining_amount"])
    df["remaining_amount_lcy"] = to_numeric(df["remaining_amount_lcy"])
    df["sales_lcy"] = to_numeric(df["sales_lcy"])
    df["open"] = to_boolean(df["open"])

    return df


def transform_vendors(df: pd.DataFrame) -> pd.DataFrame:
    """Transform NAV Kreditoren into staging.stg_vendors."""

    df = normalize_column_names(df)

    rename_map = {
        "no": "vendor_no",
        "no_": "vendor_no",
        "number": "vendor_no",
        "name": "vendor_name",
        "phone_no_": "phone_no",
    }
    df = df.rename(columns=rename_map)

    target_columns = [
        "vendor_no",
        "vendor_name",
        "search_name",
        "post_code",
        "country_region_code",
        "phone_no",
        "blocked",
    ]
    df = ensure_columns(df, target_columns)
    df = clean_text_columns(df)

    # NAV "Blocked" is an option field (blank / Payment / All), not a boolean.
    # After clean_text_columns a blank value is None -> not blocked.
    df["blocked"] = df["blocked"].map(lambda v: False if pd.isna(v) else True)

    return df


def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Transform NAV Debitor into staging.stg_customers."""

    df = normalize_column_names(df)

    rename_map = {
        "no": "customer_no",
        "no_": "customer_no",
        "number": "customer_no",
        "name": "customer_name",
        "phone_no_": "phone_no",
    }
    df = df.rename(columns=rename_map)

    target_columns = ["customer_no", "customer_name", "phone_no"]
    df = ensure_columns(df, target_columns)
    df = clean_text_columns(df)

    return df


def transform_projects(df: pd.DataFrame) -> pd.DataFrame:
    """Transform NAV Projekte into staging.stg_projects."""

    df = normalize_column_names(df)

    rename_map = {
        "no": "project_no",
        "no_": "project_no",
        "name": "description",
        "person_responsible": "project_manager_resource_no",
        "project_manager": "project_manager_resource_no",
        "kvsresponsible_name": "project_manager_name",
        "kvs_responsible_name": "project_manager_name",
        "bill_to_customer_no": "customer_no",
        "kvspsa_starting_date": "starting_date",
        "kvspsa_ending_date": "ending_date",
    }
    df = df.rename(columns=rename_map)

    target_columns = [
        "project_no",
        "description",
        "status",
        "project_manager_resource_no",
        "project_manager_name",
        "customer_no",
        "starting_date",
        "ending_date",
    ]
    df = ensure_columns(df, target_columns)
    df = clean_text_columns(df)

    df["starting_date"] = to_date(df["starting_date"])
    df["ending_date"] = to_date(df["ending_date"])

    return df


def transform_cost_centers(df: pd.DataFrame) -> pd.DataFrame:
    """Transform NAV Kostenstellenplan into staging.stg_cost_centers."""

    df = normalize_column_names(df)

    rename_map = {
        "code": "cost_center_code",
        "name": "cost_center_name",
        "name_2": "cost_center_name",
    }
    df = df.rename(columns=rename_map)

    target_columns = [
        "cost_center_code",
        "cost_center_name",
        "line_type",
        "totaling",
        "sorting_order",
        "net_change",
        "balance_at_date",
        "balance_to_allocate",
        "cost_subtype",
        "responsible_person",
        "blocked",
        "new_page",
        "blank_line",
        "comment",
        "cost_type_filter",
        "date_filter",
    ]
    df = ensure_columns(df, target_columns)
    df = clean_text_columns(df)

    df["sorting_order"] = to_numeric(df["sorting_order"])
    df["net_change"] = to_numeric(df["net_change"])
    df["balance_at_date"] = to_numeric(df["balance_at_date"])
    df["balance_to_allocate"] = to_numeric(df["balance_to_allocate"])
    df["blocked"] = to_boolean(df["blocked"])
    df["new_page"] = to_boolean(df["new_page"])
    df["blank_line"] = to_boolean(df["blank_line"])

    return df


def transform_financial_statement_layout(df: pd.DataFrame) -> pd.DataFrame:
    """Transform Excel layout into staging.stg_financial_statement_layout."""

    df = normalize_column_names(df)

    rename_map = {
        "sachkonten": "gl_account_no",
        "sachkonto": "gl_account_no",
        "g_l_account_no": "gl_account_no",
        "kontoname": "gl_account_name",
        "name": "gl_account_name",
        "level_00": "pnl_level_00",
        "level_0": "pnl_level_0",
        "level_1": "pnl_level_1",
        "level_2": "pnl_level_2",
        "level_3": "pnl_level_3",
        "guv_level_00": "pnl_level_00",
        "guv_level_0": "pnl_level_0",
        "guv_level_1": "pnl_level_1",
        "guv_level_2": "pnl_level_2",
        "guv_level_3": "pnl_level_3",
    }
    df = df.rename(columns=rename_map)

    target_columns = [
        "source_system",
        "gl_account_no",
        "gl_account_name",
        "pnl_level_00",
        "pnl_level_0",
        "pnl_level_1",
        "pnl_level_2",
        "pnl_level_3",
    ]
    df = ensure_columns(df, target_columns)
    df = clean_text_columns(df)

    df["source_system"] = "EXCEL"

    return df


def transform_plan_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform Excel vendor_cost_plan_2026.xlsx into staging.stg_plan_values.

    plan_year and plan_month are derived from plan_date.
    """

    df = normalize_column_names(df)

    rename_map = {
        "level_1": "pnl_level_1",
        "level_2": "pnl_level_2",
        "level_3": "pnl_level_3",
        "guv_level_1": "pnl_level_1",
        "guv_level_2": "pnl_level_2",
        "guv_level_3": "pnl_level_3",
        "kreditor_nr": "vendor_no",
        "kreditor": "vendor_no",
        "kreditor_name": "vendor_name",
        "frequenz": "frequency",
        "datum": "plan_date",
        "jahr": "plan_year",
        "monat": "plan_month",
        "betrag": "plan_amount",
        "amount": "plan_amount",
    }
    df = df.rename(columns=rename_map)

    target_columns = [
        "pnl_level_1",
        "pnl_level_2",
        "pnl_level_3",
        "vendor_no",
        "vendor_name",
        "frequency",
        "plan_date",
        "plan_year",
        "plan_month",
        "plan_amount",
    ]
    df = ensure_columns(df, target_columns)
    df = clean_text_columns(df)

    df["plan_date"] = to_date(df["plan_date"])
    plan_datetime = pd.to_datetime(df["plan_date"], errors="coerce")
    df["plan_year"] = plan_datetime.dt.year.astype("Int64")
    df["plan_month"] = plan_datetime.dt.month.astype("Int64")
    df["plan_amount"] = to_numeric(df["plan_amount"])

    return df
