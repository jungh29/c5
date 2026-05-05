# openbim-bcf-viewer

## Projektziel
Ein schlanker OpenBIM-Notebook-Prototyp: IFC-Modell im Notebook anzeigen, BCF laden, Topic auswählen und referenzierte IFC-Elemente hervorheben.

## aktueller V1-Funktionsumfang
- IFC laden und IfcProduct-Index aufbauen.
- BCF (ZIP/XML) laden und Topics/Viewpoints extrahieren.
- Mapping von BCF-referenzierten GUIDs gegen IFC-GlobalIds.
- Notebook-PoC für Viewer + Topic-Auswahl.
- Tabellen/DataFrames nur für Diagnose.

## Wichtiger Hinweis zu IFC + BCF
- Eine BCF-Datei enthält normalerweise **nicht** das komplette IFC-Modell.
- Für sinnvolle Treffer müssen IFC und BCF inhaltlich zusammengehören (gleiche Modellbasis/GlobalIds).
- Wenn eine beliebige BCF mit einer unpassenden IFC kombiniert wird, bleiben GUID-Treffer typischerweise leer oder sehr gering.

## Installation mit `python -m venv`
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Installation mit `uv`
```bash
uv venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
uv pip install -r requirements.txt
```

## JupyterLab starten
```bash
jupyter lab
```

## Erwartete Beispieldateien
Lege für die manuellen Tests folgende Dateien ab:
- `data/sample.ifc`
- `data/sample.bcfzip`

## Test A: Nur IFC-Viewer
1. `data/sample.ifc` ablegen.
2. `notebooks/01_ifc_viewer_poc.ipynb` öffnen.
3. Alle Zellen von oben nach unten ausführen.

Erwartetes Ergebnis:
- IFC-Modell ist sichtbar.
- Eine Beispiel-GlobalId wird hervorgehoben.

## Test B: IFC + BCF (Hauptprototyp)
1. `data/sample.ifc` und `data/sample.bcfzip` ablegen.
2. `notebooks/03_ifc_bcf_viewer.ipynb` öffnen.
3. `Load IFC` klicken.
4. `Load BCF` klicken.
5. Ein Topic im Dropdown auswählen.

Erwartetes Ergebnis:
- Topic-Informationen sind sichtbar.
- Referenzierte IFC-Elemente werden hervorgehoben.

## Test C: CLI-Diagnose
```bash
python -m openbim_viewer.cli inspect --ifc data/sample.ifc --bcf data/sample.bcfzip
```

Erwartetes Ergebnis:
- Konsole zeigt eine Summary (IFC-Produkte, Topics, Viewpoints, GUID-Treffer).
- Datei `exports/bcf_ifc_mapping.csv` wird erzeugt.
- Optional: `exports/bcf_ifc_mapping.xlsx` bei verfügbarem `openpyxl`.

## CLI-Diagnose
Für schnellen Headless-Check (ohne Notebook/Viewer-UI):

```bash
python -m openbim_viewer.cli inspect --ifc data/sample.ifc --bcf data/sample.bcfzip
```

Die CLI lädt IFC/BCF, erstellt das Mapping und schreibt:
- `exports/bcf_ifc_mapping.csv`
- optional `exports/bcf_ifc_mapping.xlsx` (wenn `openpyxl` verfügbar ist)

## Typische Fehlerbilder und Hinweise
- **Datei nicht gefunden**
  - Pfade prüfen (`data/sample.ifc`, `data/sample.bcfzip`).
- **BCF passt nicht zur IFC**
  - GUID-Mapping bleibt leer oder Trefferzahl ist sehr niedrig.
- **Keine GUIDs in BCF gefunden**
  - BCF kann valide sein, aber keine/andere referenzierte GUID-Felder enthalten.
- **Viewer kann IFC-Geometrie nicht extrahieren**
  - Einzelne Elemente können übersprungen werden; ggf. anderes Testmodell probieren.
- **Notebook-Kernel nutzt falsche Python-Umgebung**
  - Sicherstellen, dass Kernel zur Umgebung mit installierten `requirements.txt`-Paketen gehört.

## Tests
Parser/Mapping-Hilfsfunktionen werden automatisiert mit `pytest` geprüft.
Viewer-Verhalten wird weiterhin manuell in den Notebooks getestet.

```bash
pytest -q
```

## bekannte Einschränkungen der V1
- Fokus auf PoC/Notebook-Workflow, keine vollständige Produktreife.
- Viewer-Fähigkeiten hängen vom verfügbaren Backend ab.
- BCF-Parsing robust, aber nicht auf vollständige Tool-spezifische Sonderfälle ausgelegt.
- Keine vollständige BCF-Kamera-Rekonstruktion in V1.
