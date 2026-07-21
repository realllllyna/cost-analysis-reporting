# Datenmanagementplan

Datenmanagementplan zur Bachelorarbeit gemäß den Vorgaben zum Forschungsdaten­management der HTW Berlin. Der Plan wird während der Bearbeitung fortgeschrieben.

## 1. Allgemeine Angaben

| Feld | Angabe |
|---|---|
| Autorin | Thi Chuc An Phan (Matrikelnr. 592037) |
| Studiengang | B.Sc. Wirtschaftsinformatik, HTW Berlin |
| Erstgutachter | Prof. Dr.-Ing. Ingo Claßen |
| Zweitgutachter | Prof. Dr. Martin Kempa |
| Titel der Arbeit | Konzeption und Implementierung einer BI-Reportinglösung zur Umsatz- und Kostenanalyse |
| Bearbeitungszeitraum | 29.05.2026 – 07.08.2026 (Sommersemester 2026) |

**Was und wie wird untersucht?**
Konzeption und prototypische Umsetzung einer Business-Intelligence-Reportinglösung, die
Ist-Daten aus einem ERP-System (Microsoft Dynamics Business Central) und Plandaten
aus Excel über eine Python-ETL-Strecke in einem PostgreSQL-Data-Warehouse (Sternschema)
zusammenführt und in Power BI zu einer Umsatz- und Kostenanalyse (GuV, Plan-Ist-Vergleich,
offene Posten) aufbereitet.

## 2. Datenerhebung und Regeln

**Datenerhebungsmethode**
- Automatisierte Extraktion aus Business Central über OData-v4-Web-Services.
- Import von Plan- und Strukturdaten aus internen Excel-Dateien.
- Es werden keine personenbezogenen Daten im Sinne von Befragungen oder Interviews erhoben.
  Es handelt sich um betriebswirtschaftliche Buchungs- und Stammdaten eines Unternehmens.

**Anzuwendende Regeln**
- Die Daten sind **vertrauliche Geschäftsdaten** der ETC Solutions GmbH.
- Verarbeitung ausschließlich im Rahmen der Abschlussarbeit - keine Weitergabe an Dritte.
- Zugangsdaten (NAV- und DB-Zugänge) werden nicht im Code oder Repository gespeichert,
  sondern über eine `.env`-Datei außerhalb der Versionsverwaltung gehalten.
- Eine Anonymisierung ist für die Analyse nicht erforderlich, stattdessen erfolgt der
  Schutz über **Nicht-Veröffentlichung** und eingeschränkten Zugriff.

## 3. Art und Umfang der Daten

| Datentyp | Format | Umfang (Größenordnung) |
|---|---|---|
| Sach-, Kreditoren-, Debitorenposten (NAV) | OData-JSON → PostgreSQL | mehrere zehntausend Zeilen |
| Stammdaten (Kreditoren, Debitoren, Projekte, Kostenstellen) | OData-JSON → PostgreSQL | hunderte bis tausende Zeilen |
| Plandaten und GuV-Struktur | Excel `.xlsx` | einige hundert Zeilen |
| Data Warehouse | PostgreSQL 16 (`staging` + `mart`) | < 1 GB |
| Reporting | Power BI `.pbix` (Import-Modus) | Daten eingebettet |

## 4. Ablage, Struktur und Sicherung

**Ablageorte**
- **Quellcode:** öffentliches GitHub-Repository (`realllllyna/cost-analysis-reporting`).
- **Vertrauliche Daten und `.pbix`:** lokal bzw. auf Anfrage - **nicht** im Repository.

**Ordnerstruktur**
```
sql/    Schemas, Staging-, Mart-Tabellen, Views
src/    ETL (extract, transform, load, main)
data/   Excel-Quelldateien (nicht veröffentlicht)
docs/   Architektur, ETL-Prozess, Datenmodell, DMP, Power-BI-Guide
```

**Backup**
- Code: GitHub (remote) + lokale Arbeitskopie.
- Datenbank: reproduzierbar aus den Quellsystemen über den ETL-Lauf (kein separates
  Roh-Backup nötig, da jederzeit neu ladbar).

**Langzeitarchivierung**
- Der Code bleibt öffentlich verfügbar (GitHub), solange sinnvoll.
- Die vertraulichen Daten werden nach Abschluss des Prüfungsverfahrens gelöscht bzw.
  verbleiben ausschließlich beim Unternehmen.

## 5. Veröffentlichung und Lizenz

- **Code:** veröffentlicht unter der **MIT-Lizenz** (siehe `LICENSE`).
- **Daten:** vertraulich, **nicht veröffentlicht** - Zugriff nur für die Prüfer auf
  Anfrage (eingeschränkter Zugriff).
