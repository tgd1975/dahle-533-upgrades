# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Löst die Vererbung der Bambu-Studio-Systemprofile auf und schreibt vollständige Profile.

Die Profile sind die UNVERÄNDERTEN Systemprofile unter ihren Systemnamen. Die Kommandozeile
in druck/projekt.sh braucht sie, um das Projekt anzulegen; Bambu Studio erkennt sie beim
Öffnen als seine eigenen Profile wieder. Teilespezifische Werte stehen nicht hier, sondern
als Objekteinstellungen in druck/platten.py.

Die Kommandozeile von Bambu Studio folgt den Schlüsseln "inherits" und "include" NICHT – ein
Profil, das nur erbt, bekommt Vorgabewerte (PLA, 35 °C Bett, allgemeiner Start-G-Code).

Aufruf im Repo-Wurzelverzeichnis:  uv run druck/profile_bauen.py 2>&1 | cat
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BBL = Path("/var/lib/flatpak/app/com.bambulab.BambuStudio/current/active/files/share/BambuStudio/profiles/BBL")
ZIEL = Path(__file__).resolve().parent / "profil"

DRUCKER = "Bambu Lab P1P 0.4 nozzle"
PROZESS = "0.20mm Standard @BBL P1P"
FILAMENT = "Generic PETG @BBL P1P"

# Einziger eigener Wert: der Plattentyp des Projekts (kein Profilwert). Ohne Angabe trägt die
# Kommandozeile die Cool Plate ein, die für PETG gesperrt ist. In Bambu Studio umstellbar.
PROZESS_EIGEN = {
    "curr_bed_type": "Engineering Plate",   # Platte des Besitzers für PETG
}


def index(art: str) -> dict[str, Path]:
    gefunden = {}
    for datei in (BBL / art).rglob("*.json"):
        try:
            name = json.loads(datei.read_text(encoding="utf-8")).get("name")
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if name:
            gefunden[name] = datei
    return gefunden


VERWALTUNG = {"name", "type", "from", "instantiation", "inherits", "include", "setting_id", "base_id"}


def aufloesen(name: str, idx: dict[str, Path]) -> dict:
    """Vollständiges Profil: erst das Elternprofil ("inherits"), dann die Bausteine ("include"), dann die eigenen Werte.

    In den Bausteinen stehen beim P1P Start-, End-, Schichtwechsel-, Filamentwechsel- und Zeitraffer-G-Code.
    Ohne sie bleibt der allgemeine Start-G-Code aus fdm_machine_common stehen – ohne die Startroutine des P1P.
    """
    daten = json.loads(idx[name].read_text(encoding="utf-8"))
    eltern = daten.get("inherits")
    basis = aufloesen(eltern, idx) if eltern else {}
    for baustein in daten.get("include", []):
        basis.update({k: v for k, v in aufloesen(baustein, idx).items() if k not in VERWALTUNG})
    basis.update(daten)
    basis.pop("include", None)
    return basis


def schreibe(art: str, name: str, neuer_name: str, eigen: dict, id_schluessel: str) -> Path:
    profil = aufloesen(name, index(art))
    profil.update(eigen)
    profil["inherits"] = ""
    profil["name"] = neuer_name
    profil[id_schluessel] = neuer_name if art != "filament" else [neuer_name]
    profil.pop("setting_id", None)
    profil.pop("base_id", None)
    ZIEL.mkdir(exist_ok=True)
    ziel = ZIEL / f"{art}.json"
    if art == "machine" and "machine: P1P" not in profil["machine_start_gcode"]:
        raise SystemExit("FEHLER: Start-G-Code des P1P fehlt im Druckerprofil – Bausteine (include) nicht aufgelöst?")
    ziel.write_text(json.dumps(profil, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{ziel.name}: {len(profil)} Werte aus „{name}“")
    return ziel


def main() -> int:
    if not BBL.is_dir():
        print(f"FEHLER: Bambu-Studio-Profile nicht gefunden: {BBL}")
        return 1
    schreibe("machine", DRUCKER, DRUCKER, {}, "printer_settings_id")
    schreibe("process", PROZESS, PROZESS, PROZESS_EIGEN, "print_settings_id")
    schreibe("filament", FILAMENT, FILAMENT, {}, "filament_settings_id")
    return 0


if __name__ == "__main__":
    sys.exit(main())
