DROP TABLE IF EXISTS staging.stg_gl_ledger_entries CASCADE;
DROP TABLE IF EXISTS staging.stg_vendor_ledger_entries CASCADE;
DROP TABLE IF EXISTS staging.stg_customer_ledger_entries CASCADE;
DROP TABLE IF EXISTS staging.stg_vendors CASCADE;
DROP TABLE IF EXISTS staging.stg_customers CASCADE;
DROP TABLE IF EXISTS staging.stg_projects CASCADE;
DROP TABLE IF EXISTS staging.stg_cost_centers CASCADE;
DROP TABLE IF EXISTS staging.stg_financial_statement_layout CASCADE;
DROP TABLE IF EXISTS staging.stg_plan_values CASCADE;


CREATE TABLE staging.stg_gl_ledger_entries (
    entry_no INTEGER,
    posting_date DATE,
    document_no TEXT,
    document_type TEXT,
    gl_account_no TEXT,
    gl_account_name TEXT,
    description TEXT,
    amount NUMERIC(18, 2),
    job_no TEXT,
    global_dimension_1_code TEXT,
    global_dimension_2_code TEXT,
    dimension_set_id INTEGER,
    source_code TEXT,
    reason_code TEXT,
    gen_posting_type TEXT,
    gen_bus_posting_group TEXT,
    gen_prod_posting_group TEXT,
    external_document_no TEXT,
    user_id TEXT,
    reversed BOOLEAN,
    reversed_by_entry_no INTEGER,
    reversed_entry_no INTEGER,
    source_system TEXT DEFAULT 'NAV',
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE staging.stg_vendor_ledger_entries (
    entry_no INTEGER,
    vendor_no TEXT,
    vendor_name TEXT,
    posting_date DATE,
    document_no TEXT,
    external_document_no TEXT,
    description TEXT,
    amount NUMERIC(18, 2),
    amount_lcy NUMERIC(18, 2),
    remaining_amount NUMERIC(18, 2),
    remaining_amount_lcy NUMERIC(18, 2),
    global_dimension_1_code TEXT,
    global_dimension_2_code TEXT,
    dimension_set_id INTEGER,
    document_type TEXT,
    currency_code TEXT,
    due_date DATE,
    open BOOLEAN,
    source_system TEXT DEFAULT 'NAV',
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE staging.stg_customer_ledger_entries (
    entry_no INTEGER,
    customer_no TEXT,
    customer_name TEXT,
    posting_date DATE,
    document_no TEXT,
    external_document_no TEXT,
    description TEXT,
    amount NUMERIC(18, 2),
    amount_lcy NUMERIC(18, 2),
    remaining_amount NUMERIC(18, 2),
    remaining_amount_lcy NUMERIC(18, 2),
    sales_lcy NUMERIC(18, 2),
    global_dimension_1_code TEXT,
    global_dimension_2_code TEXT,
    dimension_set_id INTEGER,
    document_type TEXT,
    currency_code TEXT,
    due_date DATE,
    open BOOLEAN,
    source_system TEXT DEFAULT 'NAV',
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE staging.stg_vendors (
    vendor_no TEXT,
    vendor_name TEXT,
    search_name TEXT,
    post_code TEXT,
    country_region_code TEXT,
    phone_no TEXT,
    blocked BOOLEAN,
    source_system TEXT DEFAULT 'NAV',
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE staging.stg_customers (
    customer_no TEXT,
    customer_name TEXT,
    phone_no TEXT,
    source_system TEXT DEFAULT 'NAV',
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE staging.stg_projects (
    project_no TEXT,
    description TEXT,
    status TEXT,
    project_manager_resource_no TEXT,
    project_manager_name TEXT,
    customer_no TEXT,
    starting_date DATE,
    ending_date DATE,
    source_system TEXT DEFAULT 'NAV',
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE staging.stg_cost_centers (
    cost_center_code TEXT,
    cost_center_name TEXT,
    line_type TEXT,
    totaling TEXT,
    sorting_order INTEGER,
    net_change NUMERIC(18, 2),
    balance_at_date NUMERIC(18, 2),
    balance_to_allocate NUMERIC(18, 2),
    cost_subtype TEXT,
    responsible_person TEXT,
    blocked BOOLEAN,
    new_page BOOLEAN,
    blank_line BOOLEAN,
    comment TEXT,
    cost_type_filter TEXT,
    date_filter TEXT,
    source_system TEXT DEFAULT 'NAV',
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE staging.stg_financial_statement_layout (
    source_system TEXT DEFAULT 'EXCEL',
    gl_account_no TEXT,
    gl_account_name TEXT,
    pnl_level_00 TEXT,
    pnl_level_0 TEXT,
    pnl_level_1 TEXT,
    pnl_level_2 TEXT,
    pnl_level_3 TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE staging.stg_plan_values (
    pnl_level_1 TEXT,
    pnl_level_2 TEXT,
    pnl_level_3 TEXT,
    vendor_no TEXT,
    vendor_name TEXT,
    frequency TEXT,
    plan_date DATE,
    plan_year INTEGER,
    plan_month INTEGER,
    plan_amount NUMERIC(18, 2),
    source_system TEXT DEFAULT 'EXCEL',
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);