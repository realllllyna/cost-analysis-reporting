# ETL-Prozess

Dieses Dokument beschreibt den kompletten ETL-Prozess (Extract, Transform, Load)
von den Quellsystemen bis zum fertigen Power-BI-Datenmodell.

---

## Überblick

```
Microsoft Business Central         Lokale Excel-Dateien (data/)
        │  OData v4                          │  openpyxl
        ▼                                    ▼
   ┌─────────────────────────────────────────────────┐
   │  1. EXTRACT   (src/extract_nav.py,              │
   │                src/extract_excel.py)            │
   └─────────────────────────────────────────────────┘
        │  rohe Tabellen (pandas DataFrames)
        ▼
   ┌─────────────────────────────────────────────────┐
   │  2. TRANSFORM (src/transform.py)                │
   │     Spalten umbenennen, bereinigen, typisieren  │
   └─────────────────────────────────────────────────┘
        │  einheitliche DataFrames
        ▼
   ┌─────────────────────────────────────────────────┐
   │  3. LOAD → STAGING (src/load.py)                │
   │     schema "staging" (stg_*)                    │
   └─────────────────────────────────────────────────┘
        │
        ▼
   ┌─────────────────────────────────────────────────┐
   │  4. BUILD MART (src/load.py)                    │
   │     Dimensionen + Faktentabellen (Sternschema)  │
   └─────────────────────────────────────────────────┘
        │
        ▼
   ┌─────────────────────────────────────────────────┐
   │  5. VIEWS (sql/04_create_views.sql)             │
   └─────────────────────────────────────────────────┘
        │
        ▼
      Power BI  (lädt die flachen Reporting-Views aus dem Schema "mart")
```

---

## Datenquellen

### Microsoft Business Central (Ist-Daten)

Zugriff per OData v4. Jeder Service ist eine veröffentlichte Web-Service-Seite in
NAV. Die Namen stehen in der `.env` und können dort angepasst werden.

| Staging-Tabelle | NAV-Service | Inhalt |
|---|---|---|
| `stg_gl_ledger_entries` | `Sachposten` | Sachposten (Hauptbuch) – Kosten & Erlöse |
| `stg_vendor_ledger_entries` | `Kreditorenposten` | Kreditorenposten (Verbindlichkeiten) |
| `stg_customer_ledger_entries` | `Debitorenposten` | Debitorenposten (Forderungen) |
| `stg_vendors` | `Kreditoren` | Kreditoren-Stammdaten |
| `stg_customers` | `Debitor` | Debitoren-Stammdaten |
| `stg_projects` | `Projekte` | Projekt-Stammdaten |
| `stg_cost_centers` | `Kostenstellenplan` | Kostenstellen-Stammdaten |

### Lokale Excel-Dateien (Plan- und Strukturdaten)

| Staging-Tabelle | Datei (`data/`) | Inhalt |
|---|---|---|
| `stg_financial_statement_layout` | `financial_statement_layout.xlsx` | GuV-Struktur: Zuordnung Sachkonto → GuV-Ebenen |
| `stg_plan_values` | `vendor_cost_plan_2026.xlsx` | Kostenplan je Kreditor & GuV-Ebene |

---

## 1. Extract

- **NAV** (`extract_nav.py`): Für jeden Service wird die OData-URL
  `.../Company('ETC Solutions GmbH')/<Service>` aufgerufen und seitenweise
  (`odata.maxpagesize`) ausgelesen. Für die Transaktionstabellen (Sach-,
  Kreditoren-, Debitorenposten) wird ein Filter `Posting_Date ge <Startdatum>`
  gesetzt (siehe Refresh-Modus).
- **Excel** (`extract_excel.py`): Die beiden Dateien werden mit `pandas`/`openpyxl`
  gelesen.

Ergebnis jedes Schritts ist ein roher pandas-DataFrame.

---

## 2. Transform

`transform.py` bringt jede Quelle in die Form der Staging-Tabelle:

1. **Spaltennamen normalisieren** – Leerzeichen/Punkte/Schrägstriche → `_`,
   Kleinschreibung (`normalize_column_names`).
2. **Umbenennen** – NAV-Feldnamen werden über eine `rename_map` auf die
   Staging-Spalten gemappt (z. B. `G_L_Account_No` → `gl_account_no`,
   `KVSPSA_Starting_Date` → `starting_date`).
3. **Zielspalten sicherstellen** (`ensure_columns`) – fehlende Spalten werden als
   `NULL` ergänzt, doppelte zusammengeführt, überzählige entfernt. Damit passt der
   DataFrame **exakt** zur Staging-Tabelle.
4. **Bereinigen & typisieren**:
   - leere Texte → `NULL`
   - Datumswerte vereinheitlichen (ungültige/`0001-01-01` → `NULL`)
   - Beträge numerisch
   - Boolesche Felder (`open`, `blocked`, `reversed` …). Hinweis: das
     NAV-`Blocked`-Feld der Kreditoren ist ein Auswahlfeld – leer = nicht
     gesperrt, jeder Wert = gesperrt.

Wichtige abgeleitete Felder:

- **Betrag in EUR (`amount_lcy`)** – NAV liefert `Amount_LCY` in Hauswährung (EUR).
  Bei Sachposten ist `Amount` bereits EUR.
- **`plan_year` / `plan_month`** werden aus `plan_date` abgeleitet.

---

## 3. Load → Staging

`load.py` schreibt die DataFrames in das Schema `staging`:

- **Transaktionstabellen** (Sach-/Kreditoren-/Debitorenposten):
  - **Full Refresh**: Tabelle wird geleert (`TRUNCATE`) und neu geladen.
  - **Incremental**: nur Zeilen ab dem Startdatum werden gelöscht und neu geladen
    (`delete_from_date`).
- **Stammdaten & Excel** (Kreditoren, Debitoren, Projekte, Kostenstellen,
  GuV-Struktur, Plan): immer `TRUNCATE` + Voll-Last.

Staging ist die **Rohschicht**: sie hält alle relevanten Quellspalten, auch solche,
die im Mart nicht verwendet werden.

---

## 4. Build Mart (Sternschema)

`build_mart_tables()` baut das Modell in einer Transaktion neu auf – zuerst die
Dimensionen, dann die Fakten.

### Dimensionen

| Dimension | Quelle | Besonderheit |
|---|---|---|
| `dim_date` | aus allen Datumsfeldern der Fakten | lückenloser Tageskalender & deutsche Monatsnamen |
| `dim_pnl_structure` | GuV-Layout (+ Plan-Ebenen, die es nicht gibt) | flache Hierarchie `pnl_level_00…3` |
| `dim_gl_account` | GuV-Layout + Sachposten | Konto → GuV-Struktur |
| `dim_vendor` | Kreditoren-Stamm + Transaktionen/Plan | Stamm gewinnt bei Konflikt |
| `dim_customer` | Debitoren-Stamm + Transaktionen | Stamm gewinnt bei Konflikt |
| `dim_project` | Projekt-Stamm + `job_no`/GD2 aus Transaktionen | |
| `dim_cost_center` | Kostenstellen-Stamm + GD1 aus Transaktionen | |

Prinzip überall: **Stammdaten liefern die Details, Transaktionen ergänzen fehlende
Schlüssel** – so geht kein in den Daten verwendeter Wert verloren.

### Fakten

| Faktentabelle | Körnung (1 Zeile =) | Kennzahlen |
|---|---|---|
| `fact_gl_entries` | ein Sachposten | `amount` (EUR, NAV-Vorzeichen) |
| `fact_vendor_ledger_entries` | ein Kreditorenposten | `amount`, `amount_lcy`, `remaining_amount(_lcy)` |
| `fact_customer_ledger_entries` | ein Debitorenposten | wie oben + `sales_lcy` |
| `fact_plan_costs` | ein Planwert | `plan_amount` |

Auflösung der Verknüpfungen in `fact_gl_entries`:

- **GuV-Struktur** = über das Sachkonto (`dim_gl_account`).
- **Kostenstelle** = eigenes `Global_Dimension_1_Code` der Zeile → sonst über den
  Beleg (Kreditoren-/Debitorenposten mit gleicher `document_no`).
- **Projekt** = `job_no` → eigenes `Global_Dimension_2_Code` → sonst über den Beleg.
- **Kreditor/Debitor** = über den Beleg (`document_no`) aus den Nebenbüchern.

---

## 5. Views

`sql/04_create_views.sql` erstellt flache Sichten (`v_gl_entries`,
`v_vendor_ledger_entries`, `v_customer_ledger_entries`, `v_plan_actual_vendor`).
Sie sind die **Datenquelle für Power BI** – je Berichtsseite eine View. Der
**Plan-Ist-Vergleich** (`v_plan_actual_vendor`) vergleicht
auf **Monatsebene** (`year_month` + GuV-Struktur + Kreditor), da der Plan monatlich,
die Ist-Buchungen aber täglich sind.

---

## Refresh-Modus (`.env`)

| Variable | Bedeutung |
|---|---|
| `NAV_FULL_REFRESH` | `true` = Voll-Last ab `NAV_START_DATE`; `false` = inkrementell |
| `NAV_START_DATE` | Startdatum der Voll-Last (z. B. `2024-01-01`) |
| `NAV_INCREMENTAL_DAYS` | inkrementell: heute minus X Tage werden neu geladen |
| `RUN_DB_SETUP` | `true` = SQL-Dateien `01`–`04` vor dem ETL ausführen (mit `DROP`) |

---

## Ausführung

```bash
# 1. Datenbank starten
docker compose up -d

# 2. Pakete installieren
python -m pip install -r requirements.txt

# 3. ETL starten (führt bei RUN_DB_SETUP=true auch 01–04 aus)
python src/main.py
```

Ablauf in `run_etl()`: Konfiguration prüfen →
Datenbank aufbauen → NAV & Excel extrahieren → transformieren → Staging laden →
Mart bauen → Views aktualisieren.

---

## Power BI

Power BI lädt die **flachen Reporting-Views** aus dem Schema `mart` – je
Berichtsseite genau eine View. Das **Sternschema** liegt in PostgreSQL. Die Views
liefern daraus je Seite eine fertige Tabelle. So braucht Power BI kein
Beziehungsmodell und keine mehrdeutigen Join-Pfade. Das Modell bleibt einfach und
die Auswertung schnell.
