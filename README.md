# Kostenanalyse Reporting

ETL-Strecke für ein Power-BI-Kostenanalyse-Reporting.

Die Ist-Daten kommen aus **Microsoft Business Central**, die Plandaten aus
**Excel-Dateien**. **Python** bereitet alles in **PostgreSQL** zu einem Sternschema
auf. **Power BI** wertet daraus flache Reporting-Views aus.

---

## Architektur

```
Microsoft Business Central (NAV)  ─┐
                                   ├─►  Python ETL  ─►  PostgreSQL  ─►  Power BI
Lokale Excel-Dateien (data/)      ─┘   (extract/         (staging       (Reporting)
                                        transform/        + mart)
                                        load)
```

| Schicht | Rolle |
|---|---|
| **Business Central (NAV)** | Ist-Daten: Sach-, Kreditoren-, Debitorenposten, Stammdaten |
| **Excel (`data/`)** | Plandaten und GuV-Struktur |
| **PostgreSQL** | Schema `staging` (Rohdaten) und `mart` (Sternschema + Reporting-Views) |
| **Power BI** | Auswertung über die flachen Views des `mart`-Schemas |

---

## Projektstruktur

```
sql/    01–04: Schemas, Staging-, Mart-Tabellen (Sternschema), Views
src/    ETL: extract_nav, extract_excel, transform, load, main
data/   Excel-Quelldateien (Plan, GuV-Struktur)
docs/   Architektur, ETL-Prozess, Datenmodell
```

---

## Wichtige Einstellungen (`.env`)

| Variable | Erster Lauf | Danach | Bedeutung |
|---|---|---|---|
| `RUN_DB_SETUP` | `true` | **`false`** | `true` legt alle Tabellen neu an (mit `DROP`!) |
| `NAV_START_DATE` | `2024-01-01` | – | Startdatum der Voll-Last |

> ⚠️ Nach dem ersten erfolgreichen Lauf `RUN_DB_SETUP=false` setzen – sonst werden
> bei jedem Lauf alle Tabellen gelöscht und neu aufgebaut.

---

## Power BI

Power BI lädt die **flachen Reporting-Views** aus dem Schema `mart` – je
Berichtsseite genau eine View:

- `v_gl_entries` – GuV (Seite 1)
- `v_plan_actual_vendor` – Plan-Ist-Vergleich (Seite 2)
- `v_vendor_ledger_entries` – Kreditorenposten (Seite 3)

Das **Sternschema** (Dimensionen + Fakten) liegt in PostgreSQL. Die Views liefern
daraus je Seite eine fertige Tabelle. So braucht Power BI kein Beziehungsmodell und
keine mehrdeutigen Join-Pfade – das Modell bleibt einfach und die Auswertung schnell.

Details siehe [`docs/powerbi_guide.md`](docs/powerbi_guide.md).

---

## Code- und Datendokumentation

Dokumentation gemäß den FDM-Vorgaben der HTW Berlin - ausführlich im
[Datenmanagementplan](docs/datenmanagementplan.md).

- **Was:** ETL- und Reporting-Lösung (NAV & Excel → PostgreSQL-Sternschema → Power BI).
- **Wer/Wann:** Thi Chuc An Phan, Bachelorarbeit HTW Berlin, SoSe 2026.
- **Werkzeuge:** Python 3.11+, pandas 2.3.3, SQLAlchemy 2.0.51, pg8000 1.31.5,
  openpyxl 3.1.5, requests 2.32.5, PostgreSQL 16, Power BI Desktop.
- **Datenschutz:** vertrauliche Geschäftsdaten der ETC Solutions GmbH –
  **nicht veröffentlicht**, Zugriff nur für Prüfer auf Anfrage. `.env`, `.pbix` und
  Quelldaten sind per [`.gitignore`](.gitignore) ausgeschlossen.
- **Lizenz:** Code unter **MIT** ([`LICENSE`](LICENSE)) - Daten nicht Teil der Lizenz.

---

## Weitere Dokumentation

- [`docs/architecture.md`](docs/architecture.md) – Architektur & Datenfluss
- [`docs/etl_process.md`](docs/etl_process.md) – kompletter ETL-Prozess
- [`docs/data_model.md`](docs/data_model.md) – Staging- und Mart-Tabellen
- [`docs/datenmanagementplan.md`](docs/datenmanagementplan.md) – Datenmanagementplan (DMP)
