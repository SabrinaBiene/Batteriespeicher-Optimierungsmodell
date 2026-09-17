# Strommarkt-Dashboard & BESS Day-Ahead Arbitrage (Deutschland)
---
## Kurzbeschreibung

Dieses Projekt untersucht das Erlöspotenzial eines Großbatteriespeichers am deutschen Day-Ahead-Strommarkt. Neben der Analyse zentraler Strommarktindikatoren ermöglicht die Anwendung die Simulation einer arbitragebasierten Speicherbewirtschaftung auf Basis historischer Marktdaten.

Es kombiniert ein interaktives **Strommarkt-Dashboard** mit einer **Ex-post-Simulation der arbitragebasierten Vermarktung eines Großbatteriespeichers (BESS)** am deutschen Day-Ahead-Strommarkt.

Die Anwendung wurde mit **Python & Streamlit** umgesetzt und ist für die explorative Datenanalyse konzipiert und im Rahmen einer Bachelorarbeit entwickelt.

---

## Inhalte & Funktionen

Die App besteht aus **zwei Blättern (Pages)**:

### Marktdaten
Analyse zentraler Strommarktindikatoren auf Basis historischer Zeitreihen:

- Day-Ahead-Strompreise (€/MWh)
- Stromerzeugung nach Energieträgern (Strommix)
- Anteil Erneuerbarer Energien (EE-Anteil)
- Negative Preisstunden und Preisstatistiken

---

### BESS Day-Ahead Arbitrage
Simulation der arbitragebasierten Vermarktung eines Großbatteriespeichers:

- Ex-post-Analyse
- Tagesweise Dispatch-Logik (1h Zeitschritt)
- Technische Restriktionen:
  - Energieinhalt (MWh)
  - Lade-/Entladeleistung (MW)
  - Round-Trip-Effizienz (RTE)
- Ergebnisse:
  - Lade-/Entladeleistung
  - State of Charge (SoC)
  - Erlöse, Kosten und Gewinne
  - Kumulierter Gewinn

---

## Methodischer Hintergrund

Die Analyse folgt einem quantitativen, empirischen Ansatz auf Basis von Marktdaten von 01. Jan. 2020 bis 31. Dez. 2025:

- Untersuchung zentraler Marktindikatoren:
  - Preisniveau und Preisvolatilität
  - Negative Preisstunden
  - Anteil Erneuerbarer Energien an der Stromerzeugung
- Ex-post-Simulation einer arbitragebasierten Vermarktung des Stromspeichers
- Bewertung des Erlöspotenzials eines  Großbatteriespeichers
- Sensitivitätsanalyse 

Regulatorische Aspekte (z. B. Netzentgelte, Marktdesign) werden nicht modellbasiert, sondern sind für eine ergänzende qualitative Einordnung vorgesehen.

---

## Datenformate

### Strommix / Strompreise
CSV-Datei mit folgenden Spalten:

```text
für strommix.csv:
Zeitstempel, Biomasse_MWh, Wasserkraft_MWh, Wind_Offshore_MWh, Wind_Onshore_MWh, Photovoltaik_MWh, Sonstige_Erneuerbare_MWh, Kernenergie_MWh, Braunkohle_MWh, Steinkohle_MWh,
Erdgas_MWh, Pumpspeicher_MWh, Sonstige_MWh

für strompreis.csv:
Zeitstempel, Strompreis

```
---

## Projektstruktur | Ordnerstruktur
```text
├── App.py 
├── Battery_Model.py        
├── Daten_Vorbereitung.py
├── data/
  └── strommix.csv
  └── strompreis.csv
└── pages/
  └── 1_Marktdaten.py
  └── 2_Batteriespeicher.py
```
Die Python-Dateien haben dabei folgende Funktion:
App.py
      - Dies ist der Einstiegspunkt der Streamlit-Anwendung & baut die Dashboard-Seite auf
Battery_Model.py
      - Python-Code der Batteriespeicher-Simulation - hier werden die Ergebnisse für die Seite zum Speicher berechnet
Daten_Vorbereitung.py
      - Python-Code der die Daten aufbereitet und die Ergebnisse für die Seite zum Strommarkt liefert
Die beiden Seiten 1. Marktdaten & 2. Batteriespeicher bündeln alle Ergebnisse und stellen diese auf geeignete Weise dar.

Alle Diagramme, die aufbereiteten Datentabellen sowie die Tabelle der Berechnungsergebnisse der Batterispeicher-Simualtion können heruntergeladen werden:
Die Datenreihen Strom über App.py, wo man sich ebenfalls eine Vorschau anzeigen lassen kann.
Die Diagramme haben meist einen Download-Button der sich rechts über dem Diagramm befindet.
Die Ergebnisse der Batterispeicher Simulation finden sich auf der Seite 2. Batteriespeicher in einem seperat beschrifteten Ordner.
---

## Installation | Nutzung des Tools

Die Nutzung des Tools benötigt eine lokale Installation von Python: 
Python (Version 3.10 oder neuer) - Download z.B. über: 
```bash
https://www.python.org/downloads/
```

```text
Wichtig:
Während der Installation die Option "Add Python to PATH" aktivieren.
```

sowie
Git - Download z.B. über: 
```bash
https://git-scm.com/install/windows
```
Dann muss ein Projektordner erstellt werden und im Ordner durch
```text
Rechtsklick > Weitere Optionen anzeigen > Open Git Bash Here
```
ein Terminal geöffnet und die nachfolgenden Eingaben durchlaufen werden.

# 1. Repository klonen:
```bash
git clone https://github.com/SabrinaBiene/Batteriespeicher-Optimierungsmodell.git
```
Dadurch wird das Projekt auf den lokalen Rechner heruntergeladen.

# 2. Virtuelle Python-Umgebung erstellen (empfohlen) und aktivieren:

Windows: 
```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
# 3. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```
Hinweis: Für die reine Nutzung der Anwendung sind keine Änderungen am Quellcode erforderlich. Nach der Installation der Abhängigkeiten genügt der Befehl unter 5. um die Anwendung zu starten.

# 4. Anwendung starten:
```bash
streamlit run App.py
```
Im Terminal erscheint dann typischerweise & die Seite öffnet sich automatisch im Browser:
```text
LOCAL URL: http://localhost:8501
```
Ist das nicht der Fall, kann die Seite manuell im Browser aufgerufen werden: 
```bash
http://localhost:8501
```
