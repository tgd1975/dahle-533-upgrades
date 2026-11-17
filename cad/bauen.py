# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery>=2.5,<2.8"]
# ///
"""Anschlagschieber für die Dahle 533 – erzeugt STL/STEP aus cad/masse.toml.

Aufruf (im Repo-Wurzelverzeichnis):  uv run cad/bauen.py 2>&1 | cat

Koordinaten im Gebrauch: x entlang der Winkelanlage, y = 0 an deren Innenkante
(Papieranlage), y < 0 auf dem Tisch, y > 0 über der Schiene, z = 0 Tischfläche.
Die STL-Dateien liegen bereits in Drucklage (Oberseite auf dem Druckbett).
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "modelle"
BILDER = ROOT / "docs" / "bilder"


def lade_masse() -> dict:
    with open(ROOT / "cad" / "masse.toml", "rb") as f:
        return tomllib.load(f)


def quader(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def pruefe(m: dict) -> list[str]:
    """Maßkette prüfen – gibt Fehler zurück, statt ein unbrauchbares Teil zu bauen."""
    w, s, sp = m["winkelanlage"], m["schieber"], m["spiel"]
    fehler = []
    zunge_b = w["nut_b"] - 2 * sp["nut_seitlich"]
    zunge_h = w["nut_t"] - sp["nut_grund"]
    kopf_d = s["hoehe"] - (w["innensteg_h"] + sp["ueber_steg"])
    dach = s["hoehe"] - (s["magnet_h"] + sp["magnet_versatz"])
    if zunge_b < 2.0:
        fehler.append(f"Zunge nur {zunge_b:.2f} mm dick (< 2,0) – Nut zu schmal für eine gedruckte Zunge")
    if zunge_h < 1.5:
        fehler.append(f"Zunge greift nur {zunge_h:.2f} mm in die Nut (< 1,5)")
    if kopf_d < 4.0:
        fehler.append(f"Kopf über dem Steg nur {kopf_d:.2f} mm dick (< 4,0) – [schieber] hoehe vergrößern")
    if dach < 2.0:
        fehler.append(f"Decke über den Magneten nur {dach:.2f} mm (< 2,0)")
    if s["breite"] < s["magnet_d"] + 2 * 4:
        fehler.append("Balken zu schmal für die Magnettaschen")
    return fehler


def schieber(m: dict, nur_probe: bool = False) -> cq.Workplane:
    w, s, sp = m["winkelanlage"], m["schieber"], m["spiel"]
    h = s["hoehe"]
    b2 = s["breite"] / 2
    k2 = (12.0 if nur_probe else s["kopf_breite"]) / 2
    laenge = 22.0 if nur_probe else s["laenge"]
    if nur_probe:
        b2 = k2

    z_steg = w["innensteg_h"] + sp["ueber_steg"]          # Unterseite des Kopfs
    y_zi = w["innensteg_b"] + sp["nut_seitlich"]          # Zunge, Flanke zum inneren Steg
    y_za = w["innensteg_b"] + w["nut_b"] - sp["nut_seitlich"]  # Zunge, äußere Flanke = Kopfende
    z_zunge = w["innensteg_h"] - w["nut_t"] + sp["nut_grund"]  # Unterkante der Zunge

    balken = quader(-b2, b2, -laenge, 0, 0, h)
    kopf = quader(-k2, k2, 0, y_za, z_steg, h)
    # Zunge an beiden Enden 2 mm kürzer als der Kopf und unten rundum angefast:
    # findet die Nut beim Aufsetzen von selbst und hakt beim Schieben nicht ein.
    zunge = quader(-k2 + 2, k2 - 2, y_zi, y_za, z_zunge, z_steg).faces("<Z").edges().chamfer(0.6)

    if not nur_probe:
        # Ecken gerundet (Optik und Griff): hinteres Balkenende und Kopf außen
        balken = balken.edges(cq.selectors.BoxSelector((-b2 - 1, -laenge - 1, -1), (b2 + 1, -laenge + 1, h + 1))).edges("|Z").fillet(3.0)
        kopf = kopf.edges(cq.selectors.BoxSelector((-k2 - 1, y_za - 1, z_steg - 1), (k2 + 1, y_za + 1, h + 1))).edges("|Z").fillet(2.0)
    teil = balken.union(kopf).union(zunge)

    if not nur_probe:
        # Oberseite (liegt beim Druck auf dem Bett) rundum anfasen
        teil = teil.faces(">Z").edges().chamfer(1.0)

        # Magnettaschen von unten, gleichmäßig über den Balken verteilt
        n = int(s["magnete"])
        rand = 16.0
        teilung = (laenge - 2 * rand) / (n - 1) if n > 1 else 0.0
        punkte = [(0.0, -rand - i * teilung) for i in range(n)]
        d = s["magnet_d"] + sp["magnet_d"]
        t = s["magnet_h"] + sp["magnet_versatz"]
        taschen = cq.Workplane("XY").pushPoints(punkte).circle(d / 2).extrude(t)
        teil = teil.cut(taschen)
        # Entlüftung/Ausdrückloch: Magnet lässt sich von oben wieder herausdrücken
        loecher = cq.Workplane("XY").pushPoints(punkte).circle(1.0).extrude(h)
        teil = teil.cut(loecher)
        # Ablesemarke: feine Kerbe oben in Balkenmitte ist NICHT nötig – abgelesen wird
        # direkt an der Anschlagfläche, die auf dem Tisch über die mm-Skala läuft.
    return teil


E_PETG = 2000.0  # N/mm², gedrucktes PETG in Schichtrichtung (Richtwert)


def pruefe_asym(m: dict) -> list[str]:
    w, a, sp = m["winkelanlage"], m["asym"], m["spiel"]
    fehler = []
    zunge_b = w["nut_b"] - a["luft_nut"]
    schlitz = a["feder_vorspannung"] + 0.5
    steg = zunge_b - a["feder_dicke"] - schlitz  # durchgehende Bezugsflanke hinter den Federn
    nase_halb = 7.0
    if a["schiene"] not in ("vorne", "hinten"):
        fehler.append('[asym] schiene muss "vorne" oder "hinten" sein')
    if zunge_b < 2.5:
        fehler.append(f"[asym] starre Zunge nur {zunge_b:.2f} mm dick (< 2,5)")
    if a["luft_anlage"] < a["luft_nut"] + 0.1:
        fehler.append("[asym] luft_anlage muss größer sein als luft_nut, sonst liegt die Balkenstirn statt der Zunge an")
    if a["federn"] and steg < 1.2:
        fehler.append(f"[asym] Zunge hinter den Federn nur {steg:.2f} mm dick (< 1,2) – feder_dicke oder feder_vorspannung verkleinern")
    enden = [x + a["feder_laenge"] + nase_halb + 1.2 for x in a["federn"]]
    if enden and max(enden) > a["fuehrung"] - 4:
        fehler.append("[asym] letzte Feder reicht über das Ende der Führung hinaus")
    for e, x in zip(enden, sorted(a["federn"])[1:]):
        if x < e + 5:
            fehler.append("[asym] Federn überlappen – Einspannstellen weiter auseinander legen")
    if a["hoehe"] - (w["innensteg_h"] + sp["ueber_steg"]) < 4.0:
        fehler.append("[asym] Kopf über dem Steg dünner als 4,0 mm – hoehe vergrößern")
    if a["hoehe"] - (a["magnet_h"] + sp["magnet_versatz"]) < 2.0:
        fehler.append("[asym] Decke über den Magneten dünner als 2,0 mm – hoehe vergrößern")
    if a["breite"] < a["magnet_d"] + a["magnet_luft_d"] + 2 * 4:
        fehler.append("[asym] Balken zu schmal für die Magnettaschen")
    return fehler


def federkraft(m: dict) -> float:
    """Kraft einer einseitig eingespannten Federzunge bei Nennvorspannung, in N."""
    w, a, sp = m["winkelanlage"], m["asym"], m["spiel"]
    b = a["hoehe"] - (w["innensteg_h"] - w["nut_t"] + sp["nut_grund"])
    traegheit = b * a["feder_dicke"] ** 3 / 12
    return 3 * E_PETG * traegheit * a["feder_vorspannung"] / a["feder_laenge"] ** 3


def schieber_asym(m: dict, nur_probe: bool = False) -> cq.Workplane:
    """Asymmetrischer Schieber mit Magneten im Balken und langer Führung in der Nut.

    x = 0 ist die Anschlagfläche (Messerseite, bündig), die Führung läuft nach +x
    (vom Messer weg). Die starre Zunge läuft durch und führt mit leichtem Spiel;
    ihre Flanke am inneren Steg ist der Bezug. Die Federzungen liegen außen in der
    Zunge, ihre Nasen drücken gegen die äußere Nutwand – jeder Nase liegt die
    starre Flanke direkt gegenüber, sie kann den Schieber also nicht verdrehen.
    """
    w, a, sp = m["winkelanlage"], m["asym"], m["spiel"]
    h, b, lg, laenge = a["hoehe"], a["breite"], a["fuehrung"], a["laenge"]
    box = cq.selectors.BoxSelector

    z_steg = w["innensteg_h"] + sp["ueber_steg"]               # Unterseite des Kopfs
    z_zunge = w["innensteg_h"] - w["nut_t"] + sp["nut_grund"]  # Unterkante der Zunge
    y_zi = w["innensteg_b"] + a["luft_anlage"]                 # Bezugsflanke (am inneren Steg)
    y_za = y_zi + w["nut_b"] - a["luft_nut"]                   # starre Außenflanke = Kopfende
    y_wand = y_zi + w["nut_b"]                                 # äußere Nutwand, wenn die Bezugsflanke anliegt
    y_fi = y_za - a["feder_dicke"]                             # Innenseite der Federzungen
    schlitz = a["feder_vorspannung"] + 0.5                     # Federweg + Reserve
    y_nase = y_wand + a["feder_vorspannung"]
    nase_halb, spalt = 7.0, 1.2

    balken = quader(0, b, -laenge, 0, 0, h)
    balken = balken.edges(box((-1, -laenge - 1, -1), (b + 1, -laenge + 1, h + 1))).edges("|Z").fillet(3.0)
    kopf = quader(0, lg, 0, y_za, z_steg, h)
    kopf = kopf.edges(box((lg - 1, y_za - 1, z_steg - 1), (lg + 1, y_za + 1, h + 1))).edges("|Z").fillet(2.0)
    zunge = quader(1, lg - 2, y_zi, y_za, z_zunge, z_steg).faces("<Z").edges().chamfer(0.6)
    teil = balken.union(kopf).union(zunge)

    # Oberseite (Druckbett) anfasen. Mit Federn bleibt die Kopfkante über ihnen ausgenommen, damit
    # die dünnen Federzungen schon in der ersten Schicht voll gedruckt werden; die Fase läuft über
    # tangentiale Kanten weiter, deshalb bleibt dann auch das gerundete Kopfende ausgenommen.
    if a["federn"]:
        teil = teil.faces(">Z").edges(box((-1, -laenge - 1, h - 1), (lg - 1, y_za - 2.5, h + 1))).chamfer(1.0)
    else:
        teil = teil.faces(">Z").edges().chamfer(1.0)

    for x_ein in a["federn"]:
        x_nase = x_ein + a["feder_laenge"]
        x_ende = x_nase + nase_halb
        # Schlitz hinter der Federzunge (an der Einspannung gerundet) und Trennspalt am freien Ende,
        # beide durch Kopf und Zunge -> frei stehende, einseitig eingespannte Zunge
        l_schlitz = x_ende + spalt - x_ein
        teil = teil.cut(
            cq.Workplane("XY").center(x_ein + l_schlitz / 2, y_fi - schlitz / 2).slot2D(l_schlitz, schlitz).extrude(h + 1)
        )
        teil = teil.cut(quader(x_ende, x_ende + spalt, y_fi - schlitz / 2, y_za + 1, -1, h + 1))
        # Nase am freien Ende, steht um die Vorspannung über die Nutwand; unten angefast, damit sie
        # sich beim Aufsetzen selbst eindrückt (sie beginnt 0,7 mm in der Zunge und füllt deren Fase)
        nase = (
            cq.Workplane("XY")
            .polyline([(x_nase - 6.5, y_za - 0.7), (x_nase - 1.5, y_nase), (x_nase + 1.5, y_nase), (x_nase + 6.5, y_za - 0.7)])
            .close()
            .extrude(h - z_zunge)
            .translate((0, 0, z_zunge))
        )
        nase = nase.faces("<Z").edges(">Y").chamfer(min(1.0, y_nase - y_za))
        teil = teil.union(nase)

    # Magnettaschen von unten, gleichmäßig über den Balken verteilt; 2-mm-Loch zum Ausdrücken
    n = int(a["magnete"])
    rand = 16.0
    teilung = (laenge - 2 * rand) / (n - 1) if n > 1 else 0.0
    punkte = [(b / 2, -rand - i * teilung) for i in range(n)]
    if n > 0:
        tasche_d = a["magnet_d"] + a["magnet_luft_d"]
        tasche_t = a["magnet_h"] + sp["magnet_versatz"]
        teil = teil.cut(cq.Workplane("XY").pushPoints(punkte).circle(tasche_d / 2).extrude(tasche_t))
        teil = teil.cut(cq.Workplane("XY").pushPoints(punkte).circle(1.0).extrude(h))

    if nur_probe:  # ganze Führung und ein Stück Balken mit der ersten Magnettasche – prüft das Spiel der Zunge (und die Federn, falls vorhanden)
        teil = teil.intersect(quader(-1, lg + 1, -(rand + 9), y_nase + 1, -1, h + 1))
    if a["schiene"] == "hinten":
        teil = teil.mirror("YZ")
    return teil


def drucklage(teil: cq.Workplane, hoehe: float) -> cq.Workplane:
    """Oberseite nach unten aufs Druckbett: keine Stützen, Zunge und Taschen zeigen nach oben."""
    return teil.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, hoehe))


def main() -> int:
    m = lade_masse()
    fehler = pruefe(m) + pruefe_asym(m)
    if fehler:
        print("FEHLER in cad/masse.toml:")
        for f in fehler:
            print("  -", f)
        return 1

    OUT.mkdir(exist_ok=True)
    BILDER.mkdir(parents=True, exist_ok=True)
    teile = {
        "anschlagschieber": (schieber(m), m["schieber"]["hoehe"]),
        "passprobe": (schieber(m, nur_probe=True), m["schieber"]["hoehe"]),
        "anschlagschieber_asym": (schieber_asym(m), m["asym"]["hoehe"]),
        "passprobe_asym": (schieber_asym(m, nur_probe=True), m["asym"]["hoehe"]),
    }
    for name, (teil, h) in teile.items():
        gedreht = drucklage(teil, h)
        cq.exporters.export(gedreht, str(OUT / f"{name}.stl"), tolerance=0.01, angularTolerance=0.1)
        cq.exporters.export(teil, str(OUT / f"{name}.step"))
        for ansicht, richtung in {"oben": (1.0, -1.2, 0.9), "unten": (1.0, 1.2, -0.9)}.items():
            cq.exporters.export(
                teil,
                str(BILDER / f"{name}_{ansicht}.svg"),
                opt={"width": 900, "height": 600, "marginLeft": 20, "marginTop": 20, "showAxes": False,
                     "projectionDir": richtung, "strokeWidth": 0.35, "strokeColor": (40, 40, 40),
                     "hiddenColor": (170, 170, 170), "showHidden": False},
            )
            # weißer Hintergrund: die dunklen Linien wären im dunklen Theme sonst unsichtbar
            bild = BILDER / f"{name}_{ansicht}.svg"
            svg = bild.read_text(encoding="utf-8")
            bild.write_text(svg.replace("\n>\n", '\n>\n    <rect width="100%" height="100%" fill="white"/>\n', 1), encoding="utf-8")
        bb = teil.val().BoundingBox()
        vol = teil.val().Volume() / 1000
        print(f"{name}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, {vol:.1f} cm³, gültig={teil.val().isValid()}")

    w, sp = m["winkelanlage"], m["spiel"]
    print(f"Zunge: {w['nut_b'] - 2 * sp['nut_seitlich']:.2f} mm dick, greift {w['nut_t'] - sp['nut_grund']:.2f} mm in die Nut")
    print(f"Lichte Weite über dem inneren Steg: {w['innensteg_b'] + sp['nut_seitlich']:.2f} mm breit, {w['innensteg_h'] + sp['ueber_steg']:.2f} mm hoch")
    a = m["asym"]
    print(f"Asymmetrisch: starre Zunge {w['nut_b'] - a['luft_nut']:.2f} mm dick (Spiel {a['luft_nut']:.1f} mm auf {a['fuehrung'] - 3:.0f} mm Länge "
          f"= höchstens {a['luft_nut'] / (a['fuehrung'] - 3) * a['laenge']:.2f} mm am Balkenende), "
          + (f"{len(a['federn'])} Federzungen {a['feder_dicke']:.1f} x {a['feder_laenge']:.0f} mm mit je etwa {federkraft(m):.1f} N; "
             if a["federn"] else "ohne Federn; ")
          +           f"{int(a['magnete'])} Magnettaschen Ø{a['magnet_d'] + a['magnet_luft_d']:.1f} x {a['magnet_h'] + sp['magnet_versatz']:.1f} tief")
    if not w.get("gemessen", False):
        print("HINWEIS: Schienenmaße sind noch GESCHÄTZT (winkelanlage.gemessen = false) – erst die Passprobe drucken.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
