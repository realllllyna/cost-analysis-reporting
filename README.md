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
| `NAV_FULL_REFRESH` | `true` | `true` / `false` | Voll-Last vs. inkrementell (letzte `NAV_INCREMENTAL_DAYS` Tage) |
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

## Code- und Datendokumentation (FDM)

Dokumentation von Code und Daten gemäß den Vorgaben zum Forschungsdatenmanagement
(FDM) der HTW Berlin.

**Was? (Softwarepaket)**
ETL-Pipeline und Reporting-Lösung zur Umsatz- und Kostenanalyse: Extraktion aus
Microsoft Dynamics NAV (OData) und Excel, Transformation und Aufbereitung zu einem
Sternschema in PostgreSQL sowie Auswertung in Power BI. Sprache: Python; Kommentare
und Dokumentation überwiegend Deutsch. Methodik: dimensionale Modellierung (Kimball),
ETL, Kennzahlen- und Plan-Ist-Analyse.

**Wer? (Datenursprung, Autor, Lizenz)**
Autorin: Thi Chuc An Phan (Bachelorarbeit, HTW Berlin, Wirtschaftsinformatik). Die
Ist-Daten wurden dem produktiven ERP-System (Business Central) der ETC Solutions GmbH
entnommen, die Plandaten stammen aus internen Excel-Dateien. **Code:** MIT-Lizenz
(siehe [`LICENSE`](LICENSE)). **Daten:** vertraulich, nicht veröffentlicht.

**Wann? (Zeitraum)**
Entwicklung im Rahmen der Bachelorarbeit, Sommersemester 2026 (Bearbeitungszeitraum
29.05.2026 – 07.08.2026).

**Welche Formate / wie viel? (Daten)**
OData-JSON (NAV, flüchtig), Excel `.xlsx` (Plan, GuV-Struktur), PostgreSQL-Datenbank
(`staging` + `mart`), Power-BI-Bericht `.pbix` (Import-Modus). Größenordnung: einige
zehntausend Buchungszeilen; die `.pbix` enthält die importierten Daten und wird nicht
veröffentlicht.

**Werkzeuge (mit Versionen)**

| Werkzeug | Version | Zweck |
|---|---|---|
| Python | 3.11+ | ETL-Sprache |
| pandas | 2.3.3 | Datenaufbereitung |
| SQLAlchemy | 2.0.51 | DB-Zugriff |
| pg8000 | 1.31.5 | PostgreSQL-Treiber |
| python-dotenv | 1.2.2 | Konfiguration (`.env`) |
| openpyxl | 3.1.5 | Excel-Import |
| requests | 2.32.5 | NAV-OData-Aufrufe |
| PostgreSQL | 16 (Docker) | Data Warehouse |
| Power BI Desktop | aktuell | Reporting |

**Qualitätssicherung**
Validierung der Datenkonsistenz (Summe aller Sachposten = 0 gemäß doppelter
Buchführung; Reconciliation der Kennzahlen gegen die Views), inkrementelle vs.
Voll-Last, Typisierung und Bereinigung in der Transform-Schicht.

**Datenschutz**
Die verarbeiteten Geschäftsdaten sind vertraulich (Finanzdaten der ETC Solutions
GmbH). Sie werden **nicht veröffentlicht**; Zugriff nur für die Prüfer auf Anfrage
(eingeschränkter Zugriff). `.env` (Zugangsdaten) und `.pbix`/Quelldaten sind per
[`.gitignore`](.gitignore) vom Repository ausgeschlossen.

**Ablageort**
Quellcode: dieses öffentliche GitHub-Repository. Vertrauliche Daten und der
Power-BI-Bericht: lokal bzw. auf Anfrage; nicht im Repository.

---

## Lizenz

Quellcode unter der **MIT-Lizenz** – siehe [`LICENSE`](LICENSE). Die verarbeiteten
Geschäftsdaten sind vertraulich und nicht Bestandteil dieser Lizenz.

---

## Weitere Dokumentation

- [`docs/architecture.md`](docs/architecture.md) – Architektur & Datenfluss
- [`docs/etl_process.md`](docs/etl_process.md) – kompletter ETL-Prozess
- [`docs/data_model.md`](docs/data_model.md) – Staging- und Mart-Tabellen
- [`docs/datenmanagementplan.md`](docs/datenmanagementplan.md) – Datenmanagementplan (DMP)
