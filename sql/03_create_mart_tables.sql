-- ============================================================
-- FAKTENTABELLEN ENTFERNEN
-- ============================================================

DROP TABLE IF EXISTS mart.fact_gl_entries CASCADE;
DROP TABLE IF EXISTS mart.fact_vendor_ledger_entries CASCADE;
DROP TABLE IF EXISTS mart.fact_customer_ledger_entries CASCADE;
DROP TABLE IF EXISTS mart.fact_plan_costs CASCADE;


-- ============================================================
-- DIMENSIONSTABELLEN ENTFERNEN
-- ============================================================

DROP TABLE IF EXISTS mart.dim_date CASCADE;
DROP TABLE IF EXISTS mart.dim_pnl_structure CASCADE;
DROP TABLE IF EXISTS mart.dim_gl_account CASCADE;
DROP TABLE IF EXISTS mart.dim_vendor CASCADE;
DROP TABLE IF EXISTS mart.dim_customer CASCADE;
DROP TABLE IF EXISTS mart.dim_project CASCADE;
DROP TABLE IF EXISTS mart.dim_cost_center CASCADE;


-- ============================================================
-- DIMENSION: DATUM
-- ============================================================

CREATE TABLE mart.dim_date (
    date_id INTEGER PRIMARY KEY,
    date_value DATE UNIQUE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day INTEGER NOT NULL,
    year_month TEXT NOT NULL
);


-- ============================================================
-- DIMENSION: GUV-STRUKTUR
-- ============================================================

CREATE TABLE mart.dim_pnl_structure (
    pnl_structure_id SERIAL PRIMARY KEY,
    pnl_level_00 TEXT,
    pnl_level_0 TEXT,
    pnl_level_1 TEXT,
    pnl_level_2 TEXT,
    pnl_level_3 TEXT
);


-- ============================================================
-- DIMENSION: SACHKONTO
-- ============================================================

CREATE TABLE mart.dim_gl_account (
    gl_account_id SERIAL PRIMARY KEY,
    gl_account_no TEXT UNIQUE NOT NULL,
    gl_account_name TEXT,
    pnl_structure_id INTEGER
        REFERENCES mart.dim_pnl_structure(pnl_structure_id)
);


-- ============================================================
-- DIMENSION: KREDITOR
-- ============================================================

CREATE TABLE mart.dim_vendor (
    vendor_id SERIAL PRIMARY KEY,

    vendor_no TEXT NOT NULL UNIQUE,
    vendor_name TEXT,
    search_name TEXT,
    post_code TEXT,
    country_region_code TEXT,
    phone_no TEXT,
    blocked BOOLEAN
);


-- ============================================================
-- DIMENSION: DEBITOR
-- ============================================================

CREATE TABLE mart.dim_customer (
    customer_id SERIAL PRIMARY KEY,

    customer_no TEXT NOT NULL UNIQUE,
    customer_name TEXT,
    phone_no TEXT
);


-- ============================================================
-- DIMENSION: PROJEKT
-- ============================================================

CREATE TABLE mart.dim_project (
    project_id SERIAL PRIMARY KEY,

    project_no TEXT NOT NULL UNIQUE,
    project_name TEXT,
    status TEXT,
    project_manager_resource_no TEXT,
    project_manager_name TEXT,
    customer_no TEXT,
    starting_date DATE,
    ending_date DATE
);


-- ============================================================
-- DIMENSION: KOSTENSTELLE
-- ============================================================

CREATE TABLE mart.dim_cost_center (
    cost_center_id SERIAL PRIMARY KEY,

    cost_center_code TEXT NOT NULL UNIQUE,
    cost_center_name TEXT
);


-- ============================================================
-- FAKT: SACHPOSTEN
-- ============================================================

CREATE TABLE mart.fact_gl_entries (
    gl_entry_id BIGSERIAL PRIMARY KEY,

    posting_date_id INTEGER
        REFERENCES mart.dim_date(date_id),

    pnl_structure_id INTEGER
        REFERENCES mart.dim_pnl_structure(pnl_structure_id),

    gl_account_id INTEGER
        REFERENCES mart.dim_gl_account(gl_account_id),

    vendor_id INTEGER
        REFERENCES mart.dim_vendor(vendor_id),

    customer_id INTEGER
        REFERENCES mart.dim_customer(customer_id),

    project_id INTEGER
        REFERENCES mart.dim_project(project_id),

    cost_center_id INTEGER
        REFERENCES mart.dim_cost_center(cost_center_id),

    source_entry_no BIGINT NOT NULL,
    document_no TEXT,
    external_document_no TEXT,
    document_type TEXT,
    description TEXT,

    source_code TEXT,

    amount NUMERIC(18, 2),

    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (source_entry_no)
);


-- ============================================================
-- FAKT: KREDITORENPOSTEN
-- ============================================================

CREATE TABLE mart.fact_vendor_ledger_entries (
    vendor_ledger_entry_id BIGSERIAL PRIMARY KEY,

    posting_date_id INTEGER
        REFERENCES mart.dim_date(date_id),

    due_date_id INTEGER
        REFERENCES mart.dim_date(date_id),

    vendor_id INTEGER
        REFERENCES mart.dim_vendor(vendor_id),

    project_id INTEGER
        REFERENCES mart.dim_project(project_id),

    cost_center_id INTEGER
        REFERENCES mart.dim_cost_center(cost_center_id),

    source_entry_no BIGINT NOT NULL,

    document_no TEXT,
    external_document_no TEXT,
    document_type TEXT,
    description TEXT,

    currency_code TEXT,

    amount NUMERIC(18, 2),
    amount_lcy NUMERIC(18, 2),
    remaining_amount NUMERIC(18, 2),
    remaining_amount_lcy NUMERIC(18, 2),

    open BOOLEAN,

    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (source_entry_no)
);


-- ============================================================
-- FAKT: DEBITORENPOSTEN
-- ============================================================

CREATE TABLE mart.fact_customer_ledger_entries (
    customer_ledger_entry_id BIGSERIAL PRIMARY KEY,

    posting_date_id INTEGER
        REFERENCES mart.dim_date(date_id),

    due_date_id INTEGER
        REFERENCES mart.dim_date(date_id),

    customer_id INTEGER
        REFERENCES mart.dim_customer(customer_id),

    project_id INTEGER
        REFERENCES mart.dim_project(project_id),

    cost_center_id INTEGER
        REFERENCES mart.dim_cost_center(cost_center_id),

    source_entry_no BIGINT NOT NULL,

    document_no TEXT,
    external_document_no TEXT,
    document_type TEXT,
    description TEXT,

    currency_code TEXT,

    amount NUMERIC(18, 2),
    amount_lcy NUMERIC(18, 2),
    remaining_amount NUMERIC(18, 2),
    remaining_amount_lcy NUMERIC(18, 2),
    sales_lcy NUMERIC(18, 2),

    open BOOLEAN,

    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (source_entry_no)
);


-- ============================================================
-- FAKT: PLANWERTE
-- ============================================================

CREATE TABLE mart.fact_plan_costs (
    plan_cost_id BIGSERIAL PRIMARY KEY,

    plan_date_id INTEGER
        REFERENCES mart.dim_date(date_id),

    pnl_structure_id INTEGER
        REFERENCES mart.dim_pnl_structure(pnl_structure_id),

    vendor_id INTEGER
        REFERENCES mart.dim_vendor(vendor_id),

    frequency TEXT,
    plan_amount NUMERIC(18, 2),

    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- INDIZES: DIMENSIONEN
-- ============================================================

CREATE INDEX idx_dim_gl_account_pnl_structure
    ON mart.dim_gl_account(pnl_structure_id);


-- ============================================================
-- INDIZES: SACHPOSTEN
-- ============================================================

CREATE INDEX idx_fact_gl_entries_posting_date
    ON mart.fact_gl_entries(posting_date_id);

CREATE INDEX idx_fact_gl_entries_gl_account
    ON mart.fact_gl_entries(gl_account_id);

CREATE INDEX idx_fact_gl_entries_pnl_structure
    ON mart.fact_gl_entries(pnl_structure_id);

CREATE INDEX idx_fact_gl_entries_vendor
    ON mart.fact_gl_entries(vendor_id);

CREATE INDEX idx_fact_gl_entries_customer
    ON mart.fact_gl_entries(customer_id);

CREATE INDEX idx_fact_gl_entries_project
    ON mart.fact_gl_entries(project_id);

CREATE INDEX idx_fact_gl_entries_cost_center
    ON mart.fact_gl_entries(cost_center_id);

CREATE INDEX idx_fact_gl_entries_document
    ON mart.fact_gl_entries(document_no);


-- ============================================================
-- INDIZES: KREDITORENPOSTEN
-- ============================================================

CREATE INDEX idx_fact_vendor_entries_posting_date
    ON mart.fact_vendor_ledger_entries(posting_date_id);

CREATE INDEX idx_fact_vendor_entries_due_date
    ON mart.fact_vendor_ledger_entries(due_date_id);

CREATE INDEX idx_fact_vendor_entries_vendor
    ON mart.fact_vendor_ledger_entries(vendor_id);

CREATE INDEX idx_fact_vendor_entries_document
    ON mart.fact_vendor_ledger_entries(document_no);

CREATE INDEX idx_fact_vendor_entries_document_type
    ON mart.fact_vendor_ledger_entries(document_type);

CREATE INDEX idx_fact_vendor_entries_open
    ON mart.fact_vendor_ledger_entries(open);


-- ============================================================
-- INDIZES: DEBITORENPOSTEN
-- ============================================================

CREATE INDEX idx_fact_customer_entries_posting_date
    ON mart.fact_customer_ledger_entries(posting_date_id);

CREATE INDEX idx_fact_customer_entries_due_date
    ON mart.fact_customer_ledger_entries(due_date_id);

CREATE INDEX idx_fact_customer_entries_customer
    ON mart.fact_customer_ledger_entries(customer_id);

CREATE INDEX idx_fact_customer_entries_document
    ON mart.fact_customer_ledger_entries(document_no);

CREATE INDEX idx_fact_customer_entries_document_type
    ON mart.fact_customer_ledger_entries(document_type);

CREATE INDEX idx_fact_customer_entries_open
    ON mart.fact_customer_ledger_entries(open);


-- ============================================================
-- INDIZES: PLANWERTE
-- ============================================================

CREATE INDEX idx_fact_plan_costs_plan_date
    ON mart.fact_plan_costs(plan_date_id);

CREATE INDEX idx_fact_plan_costs_pnl_structure
    ON mart.fact_plan_costs(pnl_structure_id);

CREATE INDEX idx_fact_plan_costs_vendor
    ON mart.fact_plan_costs(vendor_id);