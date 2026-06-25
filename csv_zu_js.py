#!/usr/bin/env python3
"""
Steueraufkommen Dashboard – Datenkonverter
==========================================
Konvertiert daten_1.csv → daten_1.js

Verwendung:
    python csv_zu_js.py                        # Standard: daten_1.csv → daten_1.js
    python csv_zu_js.py pfad/zur/datei.csv     # Benutzerdefinierter Eingabepfad
    python csv_zu_js.py eingabe.csv ausgabe.js # Benutzerdefinierte Ein- und Ausgabe

Anforderungen: Python 3.8+, pandas (pip install pandas)
"""

import re
import json
import sys
import os
from datetime import datetime

import pandas as pd


# ── Konfiguration ──────────────────────────────────────────────────────────────
IDS_GEM  = ['119','120','121','122','123','5614','124']
IDS_174  = ['138','147','140','142','127','139','141','761','143','760','5609',
            '144','145','146','148','149']
IDS_175  = ['130','131','132','129','133','128','261']


# ── CSV einlesen ───────────────────────────────────────────────────────────────
def parse_num(s):
    s = str(s).strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_line(line):
    """Parst eine Zeile des BMF-CSV-Formats (Komma als Dezimal- und Feldtrenner)."""
    if line.startswith('"') and line.endswith('"'):
        line = line[1:-1]
    # Zahlen mit Dezimalkomma sind in "" eingeschlossen → Komma zu Punkt
    line = re.sub(r'""([^"]+)""', lambda m: m.group(1).replace(',', '.'), line)
    parts = line.split(',')
    # Erste rein numerische Spalte = GN_ID
    gn_idx = next((i for i, p in enumerate(parts) if re.match(r'^\s*\d+\s*$', p)), None)
    if gn_idx is None:
        return None
    aggregat = ','.join(parts[:gn_idx]).strip()
    rest = parts[gn_idx:]
    if len(rest) < 8:
        return None
    try:
        return {
            'Aggregat':        aggregat,
            'GN_ID':           rest[0].strip(),
            'Jahr':            int(rest[1].strip()),
            'Monat':           int(rest[2].strip()),
            'Einnahmen':       parse_num(rest[4]) if len(rest) > 4 else 0.0,
            'Anteil Bund':     parse_num(rest[5]) if len(rest) > 5 else 0.0,
            'Anteil Länder':   parse_num(rest[6]) if len(rest) > 6 else 0.0,
            'Anteil Gemeinden':parse_num(rest[7]) if len(rest) > 7 else 0.0,
            'Anteil EU':       parse_num(rest[8]) if len(rest) > 8 else 0.0,
        }
    except Exception:
        return None


def load_csv(path):
    with open(path, 'rb') as f:
        content = f.read().decode('latin-1')
    lines = content.strip().split('\r\n')
    records = []
    errors  = 0
    for line in lines[1:]:
        if not line.strip():
            continue
        r = parse_line(line)
        if r:
            records.append(r)
        else:
            errors += 1
    print(f'  Eingelesen: {len(records)} Datensätze, {errors} Fehler ignoriert')
    return pd.DataFrame(records)


# ── Aggregate berechnen ────────────────────────────────────────────────────────
def calc_month(sub):
    def gn(gn_id, col='Einnahmen'):
        r = sub[sub['GN_ID'] == gn_id]
        if len(r) == 0:
            return 0.0
        v = r.iloc[0][col]
        return float(v) if not pd.isna(v) else 0.0

    agg_173   = sum(gn(i) for i in IDS_GEM)
    agg_794   = gn('150') + gn('151')
    agg_174   = sum(gn(i) for i in IDS_174)
    agg_175   = sum(gn(i) for i in IDS_175)
    agg_219   = gn('219')
    agg_355   = agg_173 + agg_794 + agg_174 + agg_175 + agg_219
    agg_256   = gn('219') + gn('210') + gn('211') + gn('5592')
    abzug_eu  = agg_256 - agg_219

    agg_9001  = sum(gn(i, 'Anteil Bund') for i in IDS_GEM)
    agg_174_b = sum(gn(i, 'Anteil Bund') for i in IDS_174)
    agg_9002  = (agg_9001 + agg_174_b + gn('150', 'Anteil Bund') - abzug_eu
                 + gn('677', 'Anteil Bund') + gn('212', 'Anteil Bund')
                 + gn('720', 'Anteil Bund'))
    agg_9003  = agg_9002 + gn('158', 'Anteil Bund')

    agg_9004  = sum(gn(i, 'Anteil Länder') for i in IDS_GEM)
    agg_175_l = sum(gn(i, 'Anteil Länder') for i in IDS_175)
    agg_9005  = (agg_9004 + agg_175_l + gn('150', 'Anteil Länder')
                 + gn('151', 'Anteil Länder') + gn('677', 'Anteil Länder')
                 + gn('720', 'Anteil Länder') + gn('212', 'Anteil Länder'))
    agg_9006  = agg_9005 + gn('158', 'Anteil Länder')
    agg_9007  = sum(gn(i, 'Anteil Gemeinden') for i in ['119','120','122','124'])

    def tsd(v): return round(v / 1000, 6)

    t1 = {i: tsd(gn(i)) for i in IDS_GEM + IDS_174 + IDS_175 + ['125','126','219']}
    t1.update({'173': tsd(agg_173), '794': tsd(agg_794),
               '174': tsd(agg_174), '175': tsd(agg_175), '355': tsd(agg_355)})

    t2 = {
        '9001':    tsd(agg_9001),
        '174b':    tsd(agg_174_b),
        '150b':    tsd(gn('150', 'Anteil Bund')),
        'abzug_eu': tsd(-abzug_eu),
        '677b':    tsd(gn('677', 'Anteil Bund')),
        '212b':    tsd(gn('212', 'Anteil Bund')),
        '720b':    tsd(gn('720', 'Anteil Bund')),
        '9002':    tsd(agg_9002),
        '158b':    tsd(gn('158', 'Anteil Bund')),
        '9003':    tsd(agg_9003),
        '9004':    tsd(agg_9004),
        '175l':    tsd(agg_175_l),
        '150l':    tsd(gn('150', 'Anteil Länder')),
        '151l':    tsd(gn('151', 'Anteil Länder')),
        '677l':    tsd(gn('677', 'Anteil Länder')),
        '720l':    tsd(gn('720', 'Anteil Länder')),
        '212l':    tsd(gn('212', 'Anteil Länder')),
        '9005':    tsd(agg_9005),
        '158l':    tsd(gn('158', 'Anteil Länder')),
        '9006':    tsd(agg_9006),
        '219eu':   tsd(gn('219')),
        '211eu':   tsd(gn('211')),
        '210eu':   tsd(gn('210')),
        '5592eu':  tsd(gn('5592')),
        '256':     tsd(agg_256),
        '9007':    tsd(agg_9007),
    }
    return t1, t2


# ── Hauptprogramm ──────────────────────────────────────────────────────────────
def main():
    # Pfade aus Argumenten oder Standard
    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'daten_1.csv'
    js_path  = sys.argv[2] if len(sys.argv) > 2 else 'daten_1.js'

    if not os.path.exists(csv_path):
        print(f'Fehler: Datei nicht gefunden: {csv_path}')
        sys.exit(1)

    print(f'Lese: {csv_path}')
    df = load_csv(csv_path)

    print('Berechne Aggregate...')
    out = []
    for (jahr, monat), grp in df.groupby(['Jahr', 'Monat']):
        if grp['Einnahmen'].sum() == 0:
            continue
        t1, t2 = calc_month(grp)
        if t1['355'] == 0:
            continue
        out.append({'jahr': int(jahr), 'monat': int(monat), 't1': t1, 't2': t2})

    out.sort(key=lambda r: (r['jahr'], r['monat']))

    if out:
        print(f'  Zeitraum: {out[0]["jahr"]}/{out[0]["monat"]:02d} – '
              f'{out[-1]["jahr"]}/{out[-1]["monat"]:02d}')
        print(f'  Monate mit Daten: {len(out)}')

    # Kontrollsumme letzter verfügbarer Monat
    last = out[-1]
    total = last['t2']['9003'] + last['t2']['9006'] + last['t2']['256'] + last['t2']['9007']
    diff  = abs(total - last['t1']['355'])
    print(f'  Kontrollsumme ({last["jahr"]}/{last["monat"]:02d}): '
          f'Diff = {diff:.3f} Tsd. € {"✓" if diff < 1 else "⚠ PRÜFEN"}')

    js_content = (
        '// Steueraufkommen Deutschland – Monatsdaten (Tsd. Euro)\n'
        '// Quelle: Bundesministerium der Finanzen, IA5\n'
        f'// Generiert: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n'
        f'window.STEUER_DATA = {json.dumps(out, separators=(",", ":"), ensure_ascii=False)};\n'
    )

    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    size_kb = len(js_content) / 1024
    print(f'Gespeichert: {js_path} ({size_kb:.0f} KB)')


if __name__ == '__main__':
    main()
