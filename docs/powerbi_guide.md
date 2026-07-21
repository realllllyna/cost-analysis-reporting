# Power BI Bericht

Der Bericht liest die **flachen Reporting-Views** aus dem Schema `mart`
(PostgreSQL, Import-Modus) und besteht aus **drei Seiten** – je Seite genau eine
View (`v_gl_entries`, `v_plan_actual_vendor`, `v_vendor_ledger_entries`).

**Warum flache Views statt des Sternschemas in Power BI?** Das Sternschema liegt
bereits in PostgreSQL und die Views liefern daraus je Seite eine fertige Tabelle.
So braucht Power BI kein Beziehungsmodell und keine mehrdeutigen Join-Pfade.
Das Modell bleibt einfach und die Auswertung schnell.

> Hinweis zum Vorzeichen: Die Daten liegen im **NAV-Vorzeichen** (Kosten +,
> Erlöse −). Für den betriebswirtschaftlichen Ausweis wird in den Measures
> gedreht (`-SUM(...)`), sodass Erlöse positiv und Kosten negativ erscheinen.

## Seite 1 – GuV (Gewinn- und Verlustrechnung)

**Zweck:** Das operative Ergebnis nach GuV-Struktur zeigen – von der
Gesamtleistung über die Kostenblöcke bis zum EBITDA.

- **Datenbasis:** `v_gl_entries` (Sachposten)
- **Inhalt:** Matrix mit der GuV-Gliederung (A. Gesamtleistung … G. Steuer/Zinsen)
  in den Zeilen, Monaten in den Spalten. Dazu Kennzahlen **EBITDA**,
  **EBITDA-Marge** und Kostenquoten (Personal-, Projekt-, Betriebskosten).
- **Filter:** Debitor, Kreditor, Projekt, Jahr, Monat.

## Seite 2 – Plan-Ist-Vergleich

**Zweck:** Ist-Kosten gegen das geplante Budget stellen und Abweichungen sichtbar
machen – je Monat, GuV-Zeile und Kreditor.

- **Datenbasis:** `v_plan_actual_vendor`
- **Inhalt:** Ist, Plan, Abweichung (absolut und in %) je Kreditor/Kostenart & Status-Kennzeichnung (Plan und Ist / nur Ist / nur Plan).
- **Filter:** Jahr, Monat, GuV-Zeile, Kreditor.

## Seite 3 – Kreditorenposten (Rechnungen & Zahlstatus)

**Zweck:** Offene Posten und Fälligkeiten je Lieferant überwachen.

- **Datenbasis:** `v_vendor_ledger_entries`
- **Inhalt:** Offener Betrag, Anzahl Rechnungen, überfälliger Betrag (fällig +
  noch offen) & Detailliste der Belege mit Buchungs-/Fälligkeitsdatum.
- **Filter:** Kreditor, Projekt, Jahr, Zahlstatus (offen/geschlossen).
