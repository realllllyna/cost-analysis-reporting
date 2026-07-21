-- ============================================================
-- BESTEHENDE VIEWS ENTFERNEN
-- ============================================================

DROP VIEW IF EXISTS mart.v_plan_actual_vendor CASCADE;
DROP VIEW IF EXISTS mart.v_customer_ledger_entries CASCADE;
DROP VIEW IF EXISTS mart.v_vendor_ledger_entries CASCADE;
DROP VIEW IF EXISTS mart.v_gl_entries CASCADE;


-- ============================================================
-- VIEW 1: SACHPOSTEN  (Power-BI-Seite 1: GuV)
-- ============================================================

CREATE VIEW mart.v_gl_entries AS
SELECT
    -- Buchungsdatum
    d.date_value AS posting_date,
    d.year AS posting_year,
    d.quarter AS posting_quarter,
    d.month AS posting_month,
    d.month_name AS posting_month_name,

    -- Sachkonto
    ga.gl_account_no,
    ga.gl_account_name,

    -- GuV-Struktur
    ps.pnl_level_00,
    ps.pnl_level_0,
    ps.pnl_level_1,
    ps.pnl_level_2,
    ps.pnl_level_3,

    -- Kreditor
    v.vendor_no,
    v.vendor_name,

    -- Debitor
    cu.customer_no,
    cu.customer_name,

    -- Projekt
    p.project_no,
    p.project_name,
    p.status AS project_status,
    p.project_manager_name,
    p.starting_date AS project_starting_date,
    p.ending_date AS project_ending_date,

    -- Kostenstelle
    cc.cost_center_code,
    cc.cost_center_name,

    -- Belegdaten
    f.document_no,
    f.external_document_no,
    f.document_type,
    f.description,

    -- Kennzahl
    f.amount

FROM mart.fact_gl_entries f
LEFT JOIN mart.dim_date d           ON d.date_id = f.posting_date_id
LEFT JOIN mart.dim_gl_account ga    ON ga.gl_account_id = f.gl_account_id
LEFT JOIN mart.dim_pnl_structure ps ON ps.pnl_structure_id = f.pnl_structure_id
LEFT JOIN mart.dim_vendor v         ON v.vendor_id = f.vendor_id
LEFT JOIN mart.dim_customer cu      ON cu.customer_id = f.customer_id
LEFT JOIN mart.dim_project p        ON p.project_id = f.project_id
LEFT JOIN mart.dim_cost_center cc   ON cc.cost_center_id = f.cost_center_id;


-- ============================================================
-- VIEW 2: KREDITORENPOSTEN  (Power-BI-Seite 3: Rechnungen & Zahlstatus)
-- ============================================================

CREATE VIEW mart.v_vendor_ledger_entries AS
SELECT
    -- Buchungsdatum
    pd.date_value AS posting_date,
    pd.year AS posting_year,
    pd.quarter AS posting_quarter,
    pd.month AS posting_month,
    pd.month_name AS posting_month_name,

    -- Fälligkeitsdatum
    dd.date_value AS due_date,

    -- Kreditor
    v.vendor_no,
    v.vendor_name,

    -- Projekt
    p.project_no,
    p.project_name,
    p.status AS project_status,

    -- Kostenstelle
    cc.cost_center_code,
    cc.cost_center_name,

    -- Belegdaten
    f.document_no,
    f.external_document_no,
    f.document_type,
    f.description,

    -- Währungsinformation
    f.currency_code,

    -- Kennzahlen
    f.amount,
    f.amount_lcy,
    f.remaining_amount,
    f.remaining_amount_lcy,
    f.open,
    CASE
        WHEN f.open IS TRUE THEN 'Open'
        WHEN f.open IS FALSE THEN 'Closed'
        ELSE 'Unknown'
    END AS open_status

FROM mart.fact_vendor_ledger_entries f
LEFT JOIN mart.dim_date pd         ON pd.date_id = f.posting_date_id
LEFT JOIN mart.dim_date dd         ON dd.date_id = f.due_date_id
LEFT JOIN mart.dim_vendor v        ON v.vendor_id = f.vendor_id
LEFT JOIN mart.dim_project p       ON p.project_id = f.project_id
LEFT JOIN mart.dim_cost_center cc  ON cc.cost_center_id = f.cost_center_id;


-- ============================================================
-- VIEW 3: DEBITORENPOSTEN  (Reserve / künftige Cashflow-Seite)
-- ============================================================

CREATE VIEW mart.v_customer_ledger_entries AS
SELECT
    f.customer_ledger_entry_id,

    -- Buchungsdatum
    pd.date_id AS posting_date_id,
    pd.date_value AS posting_date,
    pd.year AS posting_year,
    pd.quarter AS posting_quarter,
    pd.month AS posting_month,
    pd.month_name AS posting_month_name,
    pd.year_month AS posting_year_month,

    -- Fälligkeitsdatum
    dd.date_id AS due_date_id,
    dd.date_value AS due_date,
    dd.year AS due_year,
    dd.month AS due_month,
    dd.month_name AS due_month_name,
    dd.year_month AS due_year_month,

    -- Debitor
    cu.customer_id,
    cu.customer_no,
    cu.customer_name,
    cu.phone_no AS customer_phone_no,

    -- Projekt
    p.project_id,
    p.project_no,
    p.project_name,
    p.status AS project_status,

    -- Kostenstelle
    cc.cost_center_id,
    cc.cost_center_code,
    cc.cost_center_name,

    -- Belegdaten
    f.source_entry_no,
    f.document_no,
    f.external_document_no,
    f.document_type,
    f.description,

    -- Währungsinformation
    f.currency_code,

    -- Kennzahlen
    f.amount,
    f.amount_lcy,
    f.remaining_amount,
    f.remaining_amount_lcy,
    f.sales_lcy,
    f.open,

    CASE
        WHEN f.open IS TRUE THEN 'Open'
        WHEN f.open IS FALSE THEN 'Closed'
        ELSE 'Unknown'
    END AS open_status,

    f.loaded_at

FROM mart.fact_customer_ledger_entries f
LEFT JOIN mart.dim_date pd         ON pd.date_id = f.posting_date_id
LEFT JOIN mart.dim_date dd         ON dd.date_id = f.due_date_id
LEFT JOIN mart.dim_customer cu     ON cu.customer_id = f.customer_id
LEFT JOIN mart.dim_project p       ON p.project_id = f.project_id
LEFT JOIN mart.dim_cost_center cc  ON cc.cost_center_id = f.cost_center_id;


-- ============================================================
-- VIEW 4: PLAN-IST-VERGLEICH NACH KREDITOR  (Power-BI-Seite 2)
-- ============================================================

CREATE VIEW mart.v_plan_actual_vendor AS
-- Plan (monatliches Budget) vs. Ist (tägliche Sachposten) auf MONATS-Ebene,
-- je year_month + GuV-Struktur + Kreditor. Ist-Beträge im NAV-Vorzeichen
-- (Kosten positiv); plan_amount ist ein positives Budget.
WITH actual_values AS (
    SELECT
        d.year_month AS analysis_year_month,
        f.pnl_structure_id,
        f.vendor_id,
        SUM(f.amount) AS actual_amount
    FROM mart.fact_gl_entries f
    JOIN mart.dim_date d
        ON d.date_id = f.posting_date_id
    WHERE f.vendor_id IS NOT NULL
      AND f.pnl_structure_id IS NOT NULL   -- nur echte GuV-Kostenzeilen, keine Bilanz-Gegenbuchungen
    GROUP BY
        d.year_month,
        f.pnl_structure_id,
        f.vendor_id
),

plan_values AS (
    SELECT
        d.year_month AS analysis_year_month,
        f.pnl_structure_id,
        f.vendor_id,
        MAX(f.frequency) AS frequency,
        SUM(f.plan_amount) AS plan_amount
    FROM mart.fact_plan_costs f
    JOIN mart.dim_date d
        ON d.date_id = f.plan_date_id
    GROUP BY
        d.year_month,
        f.pnl_structure_id,
        f.vendor_id
),

combined_values AS (
    SELECT
        COALESCE(a.analysis_year_month, p.analysis_year_month) AS analysis_year_month,
        COALESCE(a.pnl_structure_id, p.pnl_structure_id) AS pnl_structure_id,
        COALESCE(a.vendor_id, p.vendor_id) AS vendor_id,

        p.frequency,

        COALESCE(a.actual_amount, 0::NUMERIC) AS actual_amount,
        COALESCE(p.plan_amount, 0::NUMERIC) AS plan_amount

    FROM actual_values a

    FULL OUTER JOIN plan_values p
        ON p.analysis_year_month = a.analysis_year_month
        AND p.pnl_structure_id IS NOT DISTINCT FROM a.pnl_structure_id
        AND p.vendor_id IS NOT DISTINCT FROM a.vendor_id
)

SELECT
    -- Analysemonat
    LEFT(cv.analysis_year_month, 4)::INTEGER AS analysis_year,
    RIGHT(cv.analysis_year_month, 2)::INTEGER AS analysis_month,
    CASE RIGHT(cv.analysis_year_month, 2)::INTEGER
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
    END AS analysis_month_name,
    ((RIGHT(cv.analysis_year_month, 2)::INTEGER - 1) / 3) + 1 AS analysis_quarter,

    -- GuV-Struktur
    ps.pnl_level_00,
    ps.pnl_level_0,
    ps.pnl_level_1,
    ps.pnl_level_2,
    ps.pnl_level_3,

    -- Kreditor
    v.vendor_no,
    v.vendor_name,

    -- Planungsfrequenz
    cv.frequency,

    -- Kennzahlen
    cv.actual_amount,
    cv.plan_amount,
    cv.actual_amount - cv.plan_amount AS variance_amount,

    CASE
        WHEN cv.plan_amount = 0 THEN NULL
        ELSE
            ROUND(
                (
                    (cv.actual_amount - cv.plan_amount)
                    / NULLIF(ABS(cv.plan_amount), 0)
                ) * 100,
                2
            )
    END AS variance_percent,

    CASE
        WHEN cv.plan_amount = 0 AND cv.actual_amount = 0
            THEN 'No values'
        WHEN cv.plan_amount = 0
            THEN 'Actual without plan'
        WHEN cv.actual_amount = 0
            THEN 'Plan without actual'
        ELSE 'Plan and actual'
    END AS comparison_status

FROM combined_values cv
LEFT JOIN mart.dim_pnl_structure ps ON ps.pnl_structure_id = cv.pnl_structure_id
LEFT JOIN mart.dim_vendor v         ON v.vendor_id = cv.vendor_id;
