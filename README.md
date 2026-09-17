# Strommarkt-Dashboard & BESS Day-Ahead Arbitrage (Deutschland)

Dieses Projekt kombiniert ein interaktives **Strommarkt-Dashboard** mit einer **Ex-post-Simulation der arbitragebasierten Vermarktung eines Großbatteriespeichers (BESS)** am deutschen Day-Ahead-Strommarkt.

Die Anwendung wurde mit **Python & Streamlit** umgesetzt und ist für die explorative Datenanalyse für meine BA-Thesis konzipiert.

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

### Strommix / Erzeugung
CSV-Datei mit folgenden Spalten:

```text
Zeitstempel, Biomasse_MWh, Wasserkraft_MWh, Wind_Offshore_MWh, Wind_Onshore_MWh, Photovoltaik_MWh, Sonstige_Erneuerbare_MWh, Kernenergie_MWh, Braunkohle_MWh, Steinkohle_MWh,
Erdgas_MWh, Pumpspeicher_MWh, Sonstige_MWh

### Strompreise 
CSV-Datei mit folgenden Spalten:

```text
Zeitstempel, Strompreis

