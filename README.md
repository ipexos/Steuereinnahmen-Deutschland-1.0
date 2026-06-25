# Steueraufkommen Deutschland – Dashboard
Verantwortlich: Holger Zemanek

Interaktives Datendashboard zum monatlichen Steueraufkommen der Bundesrepublik Deutschland.  
Datenquelle: Bundesministerium der Finanzen.

## Dateien

| Datei | Beschreibung |
|---|---|
| `index.html` | Dashboard (HTML/JS, keine Server-Abhängigkeiten) |
| `daten_1.js` | Aufbereitete Monatsdaten (generiert aus `daten_1.csv`) |
| `daten_1.csv` | Rohdaten BMF IA5 (nicht im Repository – siehe unten) |
| `csv_zu_js.py` | Konvertierungsskript CSV → JS |

## Lokale Nutzung

Das Dashboard benötigt **keinen Webserver** — es kann direkt im Browser geöffnet werden,
sofern `index.html` und `daten_1.js` im selben Ordner liegen.

> **Hinweis für lokale Nutzung ohne Webserver:** Manche Browser blockieren das Laden
> lokaler JS-Dateien (`file://`-Protokoll). In diesem Fall einen einfachen lokalen Server starten:
> ```bash
> python3 -m http.server 8000
> # Dann im Browser: http://localhost:8000
> ```

## Daten aktualisieren

### 1. Neue CSV-Datei bereitstellen
Neue Datenlieferung von BMF IA5 als `daten_1.csv` in den Projektordner legen.

### 2. Konvertierung ausführen
```bash
pip install pandas          # einmalig, falls nicht installiert
python csv_zu_js.py
```

Das Skript gibt eine Kontrollsumme aus — prüft ob Bund + Länder + EU + Gemeinden = Steuern gesamt:
```
Kontrollsumme (2026/05): Diff = 0.003 Tsd. € ✓
```

### 3. Ergebnis prüfen & veröffentlichen
```bash
git add daten_1.js
git commit -m "Daten aktualisiert: <Monat Jahr>"
git push
```

### Optionale Argumente
```bash
python csv_zu_js.py andere_datei.csv        # Alternativer CSV-Pfad
python csv_zu_js.py eingabe.csv ausgabe.js  # Benutzerdefinierte Pfade
```

## GitHub Pages

Um das Dashboard über GitHub Pages zu veröffentlichen:

1. Repository-Einstellungen → **Pages**
2. Branch: `main`, Ordner: `/ (root)`
3. Dashboard erreichbar unter: `https://<username>.github.io/<repo>/`

## Datenstruktur

`daten_1.js` setzt `window.STEUER_DATA` — ein Array von Monatsobjekten:

```js
{
  "jahr": 2025,
  "monat": 1,
  "t1": {                    // Tabelle 1: Steuerarten (Tsd. Euro)
    "119": 21224.159,        // Lohnsteuer
    "355": 66758.101,        // Steuern insgesamt ohne Gemeindesteuern
    ...
  },
  "t2": {                    // Tabelle 2: Gebietskörperschaften (Tsd. Euro)
    "9003": 28187.868,       // Steuereinnahmen Bund nach BEZ
    "9006": 30967.905,       // Steuereinnahmen Länder nach BEZ
    "256":   2834.145,       // EU-Eigenmittel insgesamt
    "9007":  4768.182,       // Gemeindeanteil gemeinschaftl. Steuern
    ...
  }
}
```

## Systemanforderungen (Konvertierungsskript)

- Python 3.8+
- pandas (`pip install pandas`)
