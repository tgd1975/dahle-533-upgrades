#!/usr/bin/env bash
# Baut aus den Modellen in modelle/ je Variante EINE Projektdatei druck/dahle533_<variante>.3mf
# mit zwei Platten: Platte 1 = Passprobe, Platte 2 = Schieber.
# Die Dateien enthalten KEINEN G-Code – gesliced wird in Bambu Studio. Als Projekteinstellungen
# stehen die unveränderten Systemprofile drin (P1P 0,4 mm, 0.20mm Standard, Generic PETG,
# Engineering Plate); Wände, Füllung und Brim sind Objekteinstellungen (druck/platten.py).
# Zur Kontrolle wird jede Datei einmal probeweise gesliced; der G-Code wird verworfen, nur Zeit
# und Gewicht werden gemeldet.
# Aufruf im Repo-Wurzelverzeichnis:  druck/projekt.sh
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
# Vollständig ausgeschriebene Systemprofile (druck/profile_bauen.py)
MASCHINE="$ROOT/druck/profil/machine.json"
PROZESS="$ROOT/druck/profil/process.json"
FILAMENT="$ROOT/druck/profil/filament.json"
TMP="$ROOT/druck/.tmp"   # im Home-Verzeichnis, weil die Flatpak-Sandbox /tmp nicht sieht
rm -rf "$TMP"
mkdir -p "$TMP"

bs() { flatpak run com.bambulab.BambuStudio --debug 1 "$@"; }

variante() { # name, passprobe, schieber
  local name="$1" probe="$2" schieber="$3"
  echo "== $name"
  # 1) Projekt aus beiden Modellen (Bambu Studio legt alles auf Platte 1)
  bs --load-settings "$MASCHINE;$PROZESS" --load-filaments "$FILAMENT" --arrange 1 \
     --outputdir "$TMP" --export-3mf "roh.3mf" "$ROOT/modelle/$probe.stl" "$ROOT/modelle/$schieber.stl"
  # 2) jedes Modell auf eine eigene Platte, Objekteinstellungen eintragen
  uv run "$ROOT/druck/platten.py" "$TMP/roh.3mf" "$ROOT/druck/$name.3mf" "$probe" "$schieber" 2>&1 | cat
  # 3) Kontrolle: Probeslice der fertigen Datei in den Zwischenordner, G-Code wird verworfen
  bs --slice 0 --outputdir "$TMP" --export-3mf "probeslice.3mf" "$ROOT/druck/$name.3mf"
  uv run "$ROOT/druck/probeslice.py" "$TMP/probeslice.3mf" 2 2>&1 | cat
  if unzip -l "$ROOT/druck/$name.3mf" | grep -q -i gcode; then echo "FEHLER: $name.3mf enthält G-Code"; exit 1; fi
}

variante dahle533_symmetrisch  passprobe      anschlagschieber
variante dahle533_asymmetrisch passprobe_asym anschlagschieber_asym
rm -rf "$TMP"
