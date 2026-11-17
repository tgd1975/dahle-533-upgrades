# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Liest einen Probeslice (3MF mit G-Code) und meldet je Platte Zeit, Gewicht und ob die Objekteinstellungen greifen.

Der Probeslice entsteht in druck/projekt.sh nur zur Kontrolle und wird danach gelöscht.

Aufruf:  uv run druck/probeslice.py <probeslice.3mf> <erwartete Plattenzahl>
"""

from __future__ import annotations

import re
import sys
import zipfile


def main() -> int:
    datei, erwartet = sys.argv[1], int(sys.argv[2])
    with zipfile.ZipFile(datei) as z:
        platten = sorted(n for n in z.namelist() if re.fullmatch(r"Metadata/plate_\d+\.gcode", n))
        if len(platten) != erwartet:
            print(f"FEHLER: {len(platten)} Platten gesliced, erwartet {erwartet}")
            return 1
        fehler = 0
        for name in platten:
            g = z.read(name).decode("utf-8", "replace")
            zeit = re.search(r"total estimated time: ([^\n;]+)", g)
            gewicht = re.search(r"total filament weight \[g\] : ([\d.]+)", g)
            brim, stuetzen = "; FEATURE: Brim" in g, "; FEATURE: Support" in g
            nr = re.search(r"plate_(\d+)", name).group(1)
            print(f"  Platte {nr}: {zeit.group(1).strip() if zeit else '?'}, {gewicht.group(1) if gewicht else '?'} g, "
                  f"Brim {'ja' if brim else 'NEIN'}, Stützen {'JA' if stuetzen else 'nein'}")
            if not brim or stuetzen:
                fehler += 1
        if fehler:
            print("FEHLER: Objekteinstellungen (Brim, keine Stützen) greifen nicht")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
