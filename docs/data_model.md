# Datenmodell

Das Datenmodell besteht aus einem Staging-Bereich und einem Mart-Bereich.

## Staging

Im Staging-Bereich werden die extrahierten Daten gespeichert.

Tabellen:

- staging.stg_gl_ledger_entries
- staging.stg_vendor_ledger_entries
- staging.stg_customer_ledger_entries
- staging.stg_vendors
- staging.stg_customers
- staging.stg_projects
- staging.stg_cost_centers
- staging.stg_financial_statement_layout
- staging.stg_plan_values

## Mart

Im Mart-Bereich werden die Tabellen für Power BI vorbereitet.

Faktentabellen:

- mart.fact_gl_entries
- mart.fact_vendor_ledger_entries
- mart.fact_customer_ledger_entries
- mart.fact_plan_costs

Dimensionstabellen:

- mart.dim_date
- mart.dim_pnl_structure
- mart.dim_gl_account
- mart.dim_vendor
- mart.dim_customer
- mart.dim_project
- mart.dim_cost_center

## Ziel

Power BI greift nur auf den Mart-Bereich zu. Dadurch werden Transformationen aus Power BI ausgelagert und die Performance verbessert.