# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery>=2.5,<2.8"]
# ///
"""Zinkhalter des Lasers aus dem KW-triO 13036 – 3D-Modell und technische Zeichnung aus einem Modell.

Schreibt modelle/kwtrio_halter.step und docs/bilder/kwtrio_halter.svg. Alle Ansichten sind Projektionen
desselben Körpers (verdeckte Kanten gestrichelt), die Maße kommen aus derselben Tabelle HALTER.

Aufruf im Repo-Wurzelverzeichnis:  uv run cad/kwtrio_halter.py 2>&1 | cat

Koordinaten: y entlang der Strahlachse ab Stirnseite des Körpers (Laser bei y = 0, Kabel hinten),
z ab Unterseite nach oben, x quer (Mitte x = 0).
"""

from __future__ import annotations

from pathlib import Path

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_TangentialDeflection
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape

ROOT = Path(__file__).resolve().parent.parent

# Maße in mm. "geschätzt" = aus dem Foto, nicht gemessen.
HALTER = {
    "breite": 15.5,        # quer
    "hoehe": 19.1,         # Unterseite bis Scheitel des Halbbogens
    "laenge": 22.7,        # Körper
    "achse": 11.4,         # Strahlachse über der Unterseite
    "rohr_d": 12.0,        # Drehrohr (hinten gemessen 11,9)
    "rohr_v": 1.2,         # Drehrohr steht vorne vor
    "rohr_frei": 7.0,      # Drehrohr liegt hinten so lang frei
    "modul_d": 9.0,        # Messinghülse des Lasermoduls – geschätzt
    "wand": 1.5,           # Wand der offenen Unterseite
    "tasche": 3.1,         # Tiefe der offenen Unterseite
    "zu_vorn_d": 5.7,      # Zapfen unten vorne: Steckzapfen, sitzt im Blechloch
    "zu_vorn_rand": 3.0,   # ... Abstand zur Vorderkante
    "zu_hint_d": 4.5,      # Zapfen unten hinten: Gewinde für die M3-Schraube mit Feder
    "zu_hint_rand": 2.9,   # ... Abstand zur Hinterkante
    "zu_h": 4.2,           # Zapfen unten stehen unter der Unterseite vor
    "zo_d": 4.5,           # Zapfen oben auf dem Halbbogen, Madenschraube – Ø geschätzt
    "zo_y": 6.0,           # ... Lage ab Stirnseite – geschätzt
    "zo_h": 3.7,           # ... über dem Scheitel
    "hebel_d": 5.0,        # Hebelrohr auf dem Drehrohr – Ø geschätzt
    "hebel_h": 7.8,        # ... über dem Drehrohr
    "bohrung": 2.5,        # Bohrungen in den Zapfen (M3-Kern)
}


def modell() -> tuple[cq.Workplane, cq.Workplane]:
    """Gibt (fester Körper, Drehrohr mit Hebel) zurück."""
    h = HALTER
    b, l, za = h["breite"], h["laenge"], h["achse"]
    ra = h["hoehe"] - za
    rr = h["rohr_d"] / 2
    y_frei = l - h["rohr_frei"]

    def zyl_y(r, y0, y1, z=za):     # Zylinder entlang y
        return cq.Workplane("XZ", origin=(0, y0, 0)).center(0, z).circle(r).extrude(-(y1 - y0))

    def zyl_z(r, y, z0, z1):        # Zylinder senkrecht
        return cq.Workplane("XY", origin=(0, 0, z0)).center(0, y).circle(r).extrude(z1 - z0)

    block = cq.Workplane("XY").box(b, l, za, centered=(True, False, False))
    bogen = zyl_y(ra, 0, y_frei).intersect(
        cq.Workplane("XY", origin=(0, 0, za)).box(b, y_frei, ra, centered=(True, False, False)))
    fest = block.union(bogen)
    fest = fest.cut(zyl_y(rr, -1, l + 1))                                   # Bett des Drehrohrs
    fest = fest.cut(cq.Workplane("XY").box(b - 2 * h["wand"], l - 2 * h["wand"], h["tasche"],
                                           centered=(True, False, False)).translate((0, h["wand"], 0)))
    for d, y in [(h["zu_vorn_d"], h["zu_vorn_rand"] + h["zu_vorn_d"] / 2),
                 (h["zu_hint_d"], l - h["zu_hint_rand"] - h["zu_hint_d"] / 2)]:
        fest = fest.union(zyl_z(d / 2, y, -h["zu_h"], h["tasche"] + 0.01))
        fest = fest.cut(zyl_z(h["bohrung"] / 2, y, -h["zu_h"] - 1, h["tasche"] + 1))
    zo_top = h["hoehe"] + h["zo_h"]
    fest = fest.union(zyl_z(h["zo_d"] / 2, h["zo_y"], za + rr, zo_top))
    fest = fest.cut(zyl_z(h["bohrung"] / 2, h["zo_y"], za, zo_top + 1))

    y_hebel = y_frei + h["rohr_frei"] / 2
    rohr = zyl_y(rr, -h["rohr_v"], l).cut(zyl_y(h["modul_d"] / 2, -h["rohr_v"] - 1, l + 1))
    rohr = rohr.union(zyl_z(h["hebel_d"] / 2, y_hebel, za + rr - 1, za + rr + h["hebel_h"]))
    rohr = rohr.cut(zyl_z(h["bohrung"] / 2, y_hebel, za + rr - 0.5, za + rr + h["hebel_h"] + 1))
    rohr = rohr.cut(zyl_y(h["modul_d"] / 2, -h["rohr_v"] - 1, l + 1))
    return fest, rohr


# ---------------------------------------------------------------- Projektion
def projektion(form: cq.Shape, blick: tuple, rechts: tuple) -> tuple[list, list]:
    """Sichtbare und verdeckte Kanten als Polylinien in Bildkoordinaten (u nach rechts, v nach oben).

    blick: Richtung vom Teil zum Betrachter; rechts: Modellrichtung, die im Bild nach rechts zeigt."""
    algo = HLRBRep_Algo()
    algo.Add(form.wrapped)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*blick), gp_Dir(*rechts))))
    algo.Update()
    algo.Hide()
    hlr = HLRBRep_HLRToShape(algo)

    def linien(*verbunde):
        out = []
        for v in verbunde:
            if v is None or v.IsNull():
                continue
            for kante in cq.Shape.cast(v).Edges():
                kurve = BRepAdaptor_Curve(kante.wrapped)
                teil = GCPnts_TangentialDeflection(kurve, 0.05, 0.01)
                pts = [teil.Value(i) for i in range(1, teil.NbPoints() + 1)]
                out.append([(p.X(), p.Y()) for p in pts])
        return out

    sichtbar = linien(hlr.VCompound(), hlr.OutLineVCompound(), hlr.Rg1LineVCompound())
    verdeckt = linien(hlr.HCompound(), hlr.OutLineHCompound())
    return sichtbar, verdeckt


# ---------------------------------------------------------------- Zeichnung
TEXT, LINIE, MASS, ROT, BLAU = "#222", "#222", "#555", "#d62728", "#1f5fa8"
S = 7.0  # px je mm


def zahl(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


class Ansicht:
    """Eine Ansicht: Bildkoordinaten (u, v) in mm -> SVG-Pixel, Ursprung (ox, oy)."""

    def __init__(self, ox: float, oy: float):
        self.ox, self.oy = ox, oy

    def p(self, u: float, v: float) -> tuple[float, float]:
        return self.ox + u * S, self.oy - v * S


def pfade(ans: Ansicht, linien: list, stil: str) -> str:
    teile = []
    for pl in linien:
        pts = " ".join(f"{ans.p(u, v)[0]:.2f},{ans.p(u, v)[1]:.2f}" for u, v in pl)
        teile.append(f'<polyline points="{pts}" fill="none" {stil}/>')
    return "\n".join(teile)


def pfeil_defs() -> str:
    return (f'<defs><marker id="pe" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
            f'<path d="M0,1 L10,5 L0,9 z" fill="{MASS}"/></marker>'
            f'<marker id="pa" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
            f'<path d="M10,1 L0,5 L10,9 z" fill="{MASS}"/></marker></defs>')


def hilf(a, b) -> str:
    return (f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{MASS}" '
            f'stroke-width="0.7" stroke-dasharray="3,3"/>')


def mass_h(ans: Ansicht, u1: float, u2: float, v: float, text: str, ab: float, ref_v: float | None = None) -> str:
    """Waagerechtes Maß zwischen u1 und u2; Maßlinie ab px unter (ab > 0) bzw. über (ab < 0) der Höhe v."""
    x1, y = ans.p(u1, v)
    x2, _ = ans.p(u2, v)
    ym = y + ab
    out = []
    if ref_v is not None:
        out += [hilf(ans.p(u1, ref_v), (x1, ym + (4 if ab > 0 else -4))),
                hilf(ans.p(u2, ref_v), (x2, ym + (4 if ab > 0 else -4)))]
    out.append(f'<line x1="{x1:.1f}" y1="{ym:.1f}" x2="{x2:.1f}" y2="{ym:.1f}" stroke="{MASS}" '
               f'marker-start="url(#pa)" marker-end="url(#pe)"/>')
    ty = ym + (16 if ab > 0 else -5)
    out.append(f'<text x="{(x1 + x2) / 2:.1f}" y="{ty:.1f}" text-anchor="middle">{text}</text>')
    return "\n".join(out)


def mass_v(ans: Ansicht, v1: float, v2: float, u: float, text: str, ab: float, ref_u: float | None = None) -> str:
    """Senkrechtes Maß zwischen v1 und v2; Maßlinie ab px rechts (ab > 0) bzw. links (ab < 0) von u."""
    x, y1 = ans.p(u, v1)
    _, y2 = ans.p(u, v2)
    xm = x + ab
    out = []
    if ref_u is not None:
        out += [hilf(ans.p(ref_u, v1), (xm + (4 if ab > 0 else -4), y1)),
                hilf(ans.p(ref_u, v2), (xm + (4 if ab > 0 else -4), y2))]
    out.append(f'<line x1="{xm:.1f}" y1="{y1:.1f}" x2="{xm:.1f}" y2="{y2:.1f}" stroke="{MASS}" '
               f'marker-start="url(#pa)" marker-end="url(#pe)"/>')
    tx, anker = (xm + 6, "start") if ab > 0 else (xm - 6, "end")
    out.append(f'<text x="{tx:.1f}" y="{(y1 + y2) / 2 + 5:.1f}" text-anchor="{anker}">{text}</text>')
    return "\n".join(out)


def text(ans: Ansicht, u: float, v: float, t: str, anker: str = "start", gr: int = 12, farbe: str = TEXT,
         dx: float = 0, dy: float = 0) -> str:
    x, y = ans.p(u, v)
    return f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{anker}" font-size="{gr}" fill="{farbe}">{t}</text>'


def mittellinie(ans: Ansicht, a: tuple, b: tuple) -> str:
    p, q = ans.p(*a), ans.p(*b)
    return (f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="{MASS}" '
            f'stroke-width="0.7" stroke-dasharray="10,3,2,3"/>')


def zeichnung(fest: cq.Workplane, rohr: cq.Workplane) -> str:
    h = HALTER
    b, l, za, hh = h["breite"], h["laenge"], h["achse"], h["hoehe"]
    rb, rr = b / 2, h["rohr_d"] / 2
    y_frei = l - h["rohr_frei"]
    yh = y_frei + h["rohr_frei"] / 2
    hebel_top = za + rr + h["hebel_h"]
    yu_v = h["zu_vorn_rand"] + h["zu_vorn_d"] / 2
    yu_h = l - h["zu_hint_rand"] - h["zu_hint_d"] / 2
    ganz = cq.Compound.makeCompound([fest.val(), rohr.val()])

    sicht = f'stroke="{LINIE}" stroke-width="1.4" stroke-linejoin="round"'
    verd = f'stroke="{MASS}" stroke-width="0.7" stroke-dasharray="4,3"'

    # Projektionsmethode 3, Hauptansicht = Seitenansicht (Betrachter bei +x, Laser links)
    # (Name, Blickrichtung zum Betrachter, Bild-rechts, Bild-Ursprung)
    seite = Ansicht(470, 330)       # u = y, v = z
    vorn = Ansicht(250, 330)        # u = x, v = z   (Blick auf den Laser, von -y)
    hinten = Ansicht(850, 330)      # u = -x, v = z  (Blick auf den Hebel, von +y)
    unten = Ansicht(470, 0)         # u = y, v = x   (von -z; +x oben, an der Hauptansicht)
    unten.oy = seite.oy + h["zu_h"] * S + 130 + rb * S
    ansichten = [
        (seite, (1, 0, 0), (0, 1, 0)),
        (vorn, (0, -1, 0), (1, 0, 0)),
        (hinten, (0, 1, 0), (-1, 0, 0)),
        (unten, (0, 0, -1), (0, 1, 0)),
    ]

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="820" viewBox="0 0 1100 820" '
         f'font-family="sans-serif" font-size="14" fill="{TEXT}">',
         "<title>Zinkhalter des KW-triO-Lasers</title>",
         '<rect width="100%" height="100%" fill="white"/>', pfeil_defs(),
         '<text x="20" y="30" font-size="16" font-weight="bold">Zinkhalter des Lasers aus dem KW-triO 13036</text>',
         f'<text x="20" y="52" font-size="13" fill="{MASS}">Maße in mm, Maßstab 7 : 1, Projektionsmethode 3 '
         f'(ISO 5456-2), Hauptansicht = Seitenansicht. Alle Ansichten aus einem 3D-Modell (cad/kwtrio_halter.py).</text>',
         f'<text x="20" y="72" font-size="13" fill="{MASS}">Verdeckte Kanten gestrichelt. „ca.“ = aus dem Foto geschätzt.</text>']
    for ans, blick, rechts in ansichten:
        vis, hid = projektion(ganz, blick, rechts)
        o.append(pfade(ans, hid, verd))
        o.append(pfade(ans, vis, sicht))

    # Titel der Ansichten
    o.append(text(seite, l / 2, hebel_top, "Seitenansicht (Hauptansicht)", "middle", 14, dy=-34))
    o.append(text(vorn, 0, hebel_top, "Ansicht von vorn (Laser)", "middle", 14, dy=-34))
    o.append(text(hinten, 0, hebel_top, "Ansicht von hinten (Hebel)", "middle", 14, dy=-34))
    o.append(text(unten, l / 2, rb, "Untersicht", "middle", 14, dy=-14))

    # Mittellinien
    o.append(mittellinie(seite, (-h["rohr_v"] - 1.5, za), (l + 1.5, za)))
    for ans in (vorn, hinten):
        o.append(mittellinie(ans, (-rb - 1.5, za), (rb + 1.5, za)))
        o.append(mittellinie(ans, (0, -h["zu_h"] - 1.5), (0, hebel_top + 1.5)))
    o.append(mittellinie(unten, (-h["rohr_v"] - 1.5, 0), (l + 1.5, 0)))
    for yy in (yu_v, yu_h):
        o.append(mittellinie(unten, (yy, -3.5), (yy, 3.5)))
        o.append(mittellinie(seite, (yy, -h["zu_h"] - 1), (yy, h["tasche"] + 1)))
    for yy, top in ((h["zo_y"], hh + h["zo_h"]), (yh, hebel_top)):
        o.append(mittellinie(seite, (yy, za + rr - 0.5), (yy, top + 1.2)))

    # Strahl und Beschriftung
    x0, y0 = seite.p(-h["rohr_v"], za)
    o.append(f'<line x1="{x0 - 46:.1f}" y1="{y0:.1f}" x2="{x0 - 6:.1f}" y2="{y0:.1f}" stroke="{ROT}" stroke-width="3"/>')
    o.append(text(seite, -h["rohr_v"], za, "Strahl", "end", 12, ROT, dx=-48, dy=-8))
    o.append(text(seite, l, za, "Kabel", "start", 12, dx=14, dy=-8))
    o.append(text(seite, y_frei / 2, (hh + za) / 2, "Halbbogen", "middle", 11, dy=4))
    o.append(text(seite, y_frei + h["rohr_frei"] / 2, za + rr / 2, "Drehrohr", "middle", 10, BLAU, dy=4))
    o.append(text(vorn, rb, za + 6.5, "Halbbogen (fest)", dx=8))
    o.append(text(vorn, rb, za, f"Drehrohr Ø{zahl(h['rohr_d'])}", dx=8, dy=20, farbe=BLAU))
    o.append(text(hinten, rb, hebel_top, f"Hebelrohr Ø ca. {zahl(h['hebel_d'])}", dx=8, dy=16))
    o.append(text(hinten, rb, za + rr, "Drehrohr Ø11,9", dx=8, dy=4, farbe=BLAU))
    o.append(text(unten, -h["rohr_v"], 0, "Laser", "end", 11, MASS, dx=-12, dy=-6))
    for yy, d, t, dy in [(yu_v, h["zu_vorn_d"], f"Ø{zahl(h['zu_vorn_d'])} Steckzapfen (Blechloch)", 34),
                         (yu_h, h["zu_hint_d"], f"Ø{zahl(h['zu_hint_d'])} M3, Schraube mit Feder", 56)]:
        a, e = unten.p(yy, -d / 2), unten.p(yy, -rb)
        o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{e[0]:.1f}" y2="{e[1] + dy - 12:.1f}" stroke="{MASS}" stroke-width="0.8"/>')
        o.append(text(unten, yy, -rb, t, "middle", dy=dy))
    o.append(text(unten, h["wand"], rb - h["wand"], f"Wand {zahl(h['wand'])}", gr=11, dx=3, dy=13))

    # Maße Seitenansicht
    o.append(mass_h(seite, 0, l, -h["zu_h"], zahl(l), 40, ref_v=0))
    o.append(mass_h(seite, -h["rohr_v"], l, -h["zu_h"], "24,0 gesamt", 70, ref_v=za - rr))
    o.append(mass_h(seite, 0, yu_v - h["zu_vorn_d"] / 2, -h["zu_h"], zahl(h["zu_vorn_rand"]), 16))
    o.append(mass_h(seite, yu_h + h["zu_hint_d"] / 2, l, -h["zu_h"], zahl(h["zu_hint_rand"]), 16))
    o.append(mass_h(seite, y_frei, l, hebel_top, zahl(h["rohr_frei"]), -14, ref_v=hh))
    o.append(mass_v(seite, za + rr, hebel_top, l, zahl(h["hebel_h"]), 28, ref_u=yh + h["hebel_d"] / 2))
    o.append(mass_v(seite, -h["zu_h"], 0, l, zahl(h["zu_h"]), 28, ref_u=l))
    o.append(mass_v(seite, hh, hh + h["zo_h"], h["zo_y"] - h["zo_d"] / 2, zahl(h["zo_h"]), -14))
    o.append(text(seite, -h["rohr_v"], za + rr, zahl(h["rohr_v"]), "end", dx=-4, dy=-6))
    # Maße vorn
    o.append(mass_h(vorn, -rb, rb, -h["zu_h"], zahl(b), 30, ref_v=0))
    o.append(mass_v(vorn, 0, hh, -rb, zahl(hh), -24, ref_u=0))
    o.append(mass_v(vorn, 0, za, -rb, zahl(za), -72, ref_u=-rb))
    o.append(text(vorn, -rb, za / 2, "Strahlachse", "end", 11, MASS, dx=-78, dy=22))
    # Maße hinten
    o.append(mass_h(hinten, -rb, rb, -h["zu_h"], zahl(b), 30, ref_v=0))
    # Maße unten
    o.append(mass_v(unten, -rb, rb, l, zahl(b), 26, ref_u=l))

    # Symbol Projektionsmethode 3
    px0, py0 = 960.0, 760.0
    o.append(f'<circle cx="{px0}" cy="{py0}" r="16" fill="none" stroke="{LINIE}" stroke-width="1.3"/>')
    o.append(f'<circle cx="{px0}" cy="{py0}" r="8" fill="none" stroke="{LINIE}" stroke-width="1.3"/>')
    o.append(f'<path d="M{px0 + 40},{py0 - 8} L{px0 + 80},{py0 - 16} L{px0 + 80},{py0 + 16} L{px0 + 40},{py0 + 8} Z" '
             f'fill="none" stroke="{LINIE}" stroke-width="1.3"/>')
    o.append(f'<line x1="{px0 - 24}" y1="{py0}" x2="{px0 + 88}" y2="{py0}" stroke="{MASS}" stroke-width="0.7" '
             f'stroke-dasharray="10,3,2,3"/>')
    o.append(f'<text x="{px0 + 30}" y="{py0 + 36}" text-anchor="middle" font-size="11" fill="{MASS}">Projektionsmethode 3</text>')

    offen = ["Noch nicht gemessen:",
             "1  Ø der beiden oberen Zapfen (Madenschraube, Hebelrohr)",
             "2  Lage des Zapfens mit Madenschraube entlang der Achse",
             "3  Zapfen unten: Lücke gemessen 4,3, aus den Randabständen 3,0 und 2,9 folgen 6,6 – bitte nachmessen"]
    for k, t in enumerate(offen):
        gewicht = ' font-weight="bold"' if k == 0 else ""
        o.append(f'<text x="20" y="{730 + k * 22}" font-size="13"{gewicht}>{t}</text>')
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    fest, rohr = modell()
    for name, teil in (("fest", fest), ("rohr", rohr)):
        print(f"{name}: gültig={teil.val().isValid()}, Volumen {teil.val().Volume():.0f} mm³")
    ziel = ROOT / "modelle" / "kwtrio_halter.step"
    cq.exporters.export(cq.Workplane().add(cq.Compound.makeCompound([fest.val(), rohr.val()])), str(ziel))
    print("geschrieben:", ziel)
    bild = ROOT / "docs" / "bilder" / "kwtrio_halter.svg"
    bild.write_text(zeichnung(fest, rohr) + "\n", encoding="utf-8")
    print("geschrieben:", bild)
