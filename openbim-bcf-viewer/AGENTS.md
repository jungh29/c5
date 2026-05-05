# AGENTS.md

## Projektziel
Ein schlanker OpenBIM-Notebook-Prototyp. Hauptziel ist die Anzeige eines IFC-Modells im Notebook und das Hervorheben von IFC-Elementen, die aus einer BCF-Datei referenziert werden.

## Priorität
1. IFC-Modell anzeigen.
2. Einzelne IFC-Elemente anhand ihrer GlobalId hervorheben.
3. BCF-Datei laden.
4. BCF-Topics und Viewpoints auslesen.
5. BCF-IfcGuid-Werte gegen IFC-GlobalIds mappen.
6. Topic-Titel, Status und Kommentare neben dem Viewer anzeigen.
7. Tabellen nur als Diagnose, nicht als Hauptziel.

## Bibliotheken
- ifcopenshell
- pandas
- ipywidgets
- pythreejs
- numpy
- openpyxl nur für Excel-Export
- zipfile, pathlib und xml.etree.ElementTree aus der Standardbibliothek
- optional ifc-viewer-anywidget testen

## Programmierstil
- möglichst schlank
- freie Open-Source-Bibliotheken
- robuste Fehlerbehandlung bei fehlenden BCF-Feldern
- keine harten Annahmen über Solibri, BIMcollab, Revit oder Bonsai
- XML dynamisch scannen und unbekannte Felder als raw_fields erhalten
- keine vollständige Solibri-Funktionalität
- keine vollständige BCF-Kamera-Rekonstruktion in Version 1

## Akzeptanzkriterium
Eine IFC-Datei und eine BCF-Datei können geladen werden. Das IFC-Modell wird im Notebook angezeigt. Bei Auswahl eines BCF-Topics werden die referenzierten IFC-Elemente hervorgehoben und Topic-Informationen daneben angezeigt.
