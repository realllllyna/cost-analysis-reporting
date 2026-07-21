# Architektur

Das Projekt verwendet eine mehrstufige Datenarchitektur.

## Datenquellen

Die Ist-Daten stammen aus Microsoft Business Central.

Die Plan-Daten stammen aus lokalen Excel-Dateien (Ordner `data/`).

## Datenfluss

MS Business Central  
→ Python Extract  
→ Python Transform  
→ PostgreSQL Staging  
→ PostgreSQL Mart  
→ Power BI

Lokale Excel-Datei (`data/`)  
→ Python Extract  
→ Python Transform  
→ PostgreSQL Staging  
→ PostgreSQL Mart  
→ Power BI

## Ziel

Power BI soll nicht direkt mit den Rohdaten arbeiten. Stattdessen werden die Daten vorher in PostgreSQL bereinigt und modelliert.