# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Macht aus einem Bambu-Studio-Projekt (3MF) die Druckdatei: je Objekt eine Platte, ohne G-Code.

Die Kommandozeile von Bambu Studio legt alle geladenen Modelle auf Platte 1. Für
„Passprobe und Schieber in einer Datei, aber einzeln druckbar“ wird hier jedes Objekt
mittig auf eine eigene Platte gesetzt; die Reihenfolge der Platten folgt den Namen.

Gesliced wird in Bambu Studio. Die Projekteinstellungen der Datei sind die unveränderten
Systemprofile (druck/profile_bauen.py) – ohne sie lädt Bambu Studio nur die Geometrie
(„von einer alten Version erzeugt“) und verwirft Platten und Objekteinstellungen. Was zum
Teil gehört, steht als Objekteinstellung in der Datei (EINSTELLUNGEN) und gilt über jedem
Prozessprofil.

Aufruf:  uv run druck/platten.py <ein.3mf> <aus.3mf> <name platte 1> <name platte 2> ...
"""

from __future__ import annotations

import json
import re
import sys
import zipfile

BETT = 256.0            # P1P: 256 x 256 mm
RASTER = BETT * 1.2     # Abstand der Platten in Bambu Studio (Platte + 1/5 Lücke)

# Objekteinstellungen der Teile (in Bambu Studio: Objektliste -> Objekt -> Prozess-Einstellungen)
EINSTELLUNGEN = {
    "wall_loops": "3",                  # steife, maßhaltige Anschlagflächen
    "top_shell_layers": "5",
    "bottom_shell_layers": "4",
    "sparse_infill_density": "20%",
    "sparse_infill_pattern": "gyroid",
    "enable_support": "0",              # Teile sind stützfrei konstruiert
    "brim_type": "outer_only",          # gegen Warping: lange, schmale Teile, flach auf dem Bett
    "brim_width": "5",
}

# Plattentyp je Platte. Den globalen Plattentyp nimmt Bambu Studio nicht aus dem Projekt, sondern aus
# seiner gemerkten Einstellung für den Drucker (zuletzt benutzte Platte) – nur der Eintrag je Platte
# kommt mit der Datei an. Schreibweise wie in der Auswahlliste; "eng_plate" lehnt Bambu Studio ab.
PLATTENTYP = "Engineering Plate"


def spalten(anzahl: int) -> int:
    """Spaltenzahl des Plattenrasters wie in Bambu Studio (kleinstes Quadrat, das alle fasst)."""
    n = 1
    while n * n < anzahl:
        n += 1
    return n


def main() -> int:
    ein, aus, *namen = sys.argv[1:]
    with zipfile.ZipFile(ein) as z:
        dateien = {n: z.read(n) for n in z.namelist()}

    modell = dateien["3D/3dmodel.model"].decode("utf-8")
    einstellungen = dateien["Metadata/model_settings.config"].decode("utf-8")

    # Objekt-ID -> Name
    name_zu_id = {}
    for objekt in re.finditer(r'<object id="(\d+)">\s*<metadata key="name" value="([^"]*)"', einstellungen):
        name_zu_id[objekt.group(2).removesuffix(".stl")] = objekt.group(1)
    fehlend = [n for n in namen if n not in name_zu_id]
    if fehlend or len(namen) != len(name_zu_id):
        print(f"FEHLER: erwartet {namen}, im Projekt sind {sorted(name_zu_id)}")
        return 1

    # Objekt-ID -> Hüllquader im Objektsystem (Netz + Verschiebung der Komponente)
    huelle = {}
    for objekt in re.finditer(r'<object id="(\d+)"[^>]*type="model">\s*<components>\s*<component p:path="([^"]+)"[^>]*transform="([^"]+)"', modell):
        oid, pfad, trafo = objekt.groups()
        t = [float(v) for v in trafo.split()]
        if t[:9] != [1, 0, 0, 0, 1, 0, 0, 0, 1]:
            print(f"FEHLER: Komponente von Objekt {oid} ist gedreht – nicht unterstützt")
            return 1
        netz = dateien[pfad.lstrip("/")].decode("utf-8")
        punkte = [(float(x), float(y), float(zz)) for x, y, zz in re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', netz)]
        huelle[oid] = [(min(p[i] for p in punkte) + t[9 + i], max(p[i] for p in punkte) + t[9 + i]) for i in range(3)]

    # jedes Objekt mittig auf seine Platte, ungedreht, Unterseite auf z = 0
    n_spalten = spalten(len(namen))
    for nr, name in enumerate(namen):
        oid = name_zu_id[name]
        (x0, x1), (y0, y1), (z0, _) = huelle[oid]
        if x1 - x0 > BETT - 20 or y1 - y0 > BETT - 20:
            print(f"FEHLER: {name} ist zu groß für das Druckbett")
            return 1
        mx = (nr % n_spalten) * RASTER + BETT / 2
        my = -(nr // n_spalten) * RASTER + BETT / 2
        trafo = f"1 0 0 0 1 0 0 0 1 {mx - (x0 + x1) / 2:.5f} {my - (y0 + y1) / 2:.5f} {-z0:.5f}"
        modell, anzahl = re.subn(rf'(<item objectid="{oid}"[^>]*transform=")[^"]*(")', rf"\g<1>{trafo}\g<2>", modell)
        if anzahl != 1:
            print(f"FEHLER: Objekt {oid} ({name}) nicht im Bauraum gefunden")
            return 1

    # Objekteinstellungen hinter die Extruder-Zeile jedes Objekts
    zeilen = "".join(f'\n    <metadata key="{k}" value="{v}"/>' for k, v in EINSTELLUNGEN.items())
    einstellungen, anzahl = re.subn(r'(<object id="\d+">\s*<metadata key="name"[^>]*/>\s*<metadata key="extruder"[^>]*/>)', rf"\g<1>{zeilen}", einstellungen)
    if anzahl != len(namen):
        print("FEHLER: Objekteinstellungen nicht eingetragen")
        return 1

    # Platten neu schreiben: je Platte ein Objekt
    instanzen = dict(re.findall(r'<model_instance>\s*<metadata key="object_id" value="(\d+)"/>(.*?)</model_instance>', einstellungen, flags=re.S))
    platten = ""
    for nr, name in enumerate(namen, start=1):
        oid = name_zu_id[name]
        platten += (
            "  <plate>\n"
            f'    <metadata key="plater_id" value="{nr}"/>\n'
            f'    <metadata key="plater_name" value="{name}"/>\n'
            '    <metadata key="locked" value="false"/>\n'
            f'    <metadata key="bed_type" value="{PLATTENTYP}"/>\n'
            '    <metadata key="filament_map_mode" value="Auto For Flush"/>\n'
            '    <metadata key="gcode_file" value=""/>\n'
            "    <model_instance>\n"
            f'      <metadata key="object_id" value="{oid}"/>{instanzen[oid]}</model_instance>\n'
            "  </plate>\n"
        )
    einstellungen, anzahl = re.subn(r"  <plate>.*</plate>\n", platten, einstellungen, flags=re.S)
    if anzahl != 1:
        print("FEHLER: Plattenabschnitt nicht gefunden")
        return 1

    dateien["3D/3dmodel.model"] = modell.encode("utf-8")
    dateien["Metadata/model_settings.config"] = einstellungen.encode("utf-8")
    leer = {"nozzle_sequence": [], "optimal_assignment": [], "sequence": []}
    dateien["Metadata/filament_sequence.json"] = json.dumps({f"plate_{i}": leer for i in range(1, len(namen) + 1)}).encode()

    for name in [n for n in dateien if n.endswith((".gcode", ".gcode.md5"))]:
        print(f"FEHLER: {ein} enthält G-Code ({name})")
        return 1
    # Verweise auf Vorschaubilder, die es in der Datei nicht gibt, entfernen
    rels = dateien["_rels/.rels"].decode("utf-8")
    rels = "".join(z for z in rels.splitlines(keepends=True)
                   if not (m := re.search(r'Target="/([^"]+)"', z)) or m.group(1) in dateien)
    dateien["_rels/.rels"] = rels.encode("utf-8")

    with zipfile.ZipFile(aus, "w", zipfile.ZIP_DEFLATED) as z:
        for name, inhalt in dateien.items():
            z.writestr(name, inhalt)
    print(f"{aus}: {len(namen)} Platten – " + ", ".join(f"{i}: {n}" for i, n in enumerate(namen, start=1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
