# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Zeichnet die Erklär-Skizzen als SVG (weißer Grund, damit sie in hellem und dunklem Design gleich aussehen).

- winkelanlage_querschnitt.svg – Querschnitt der Winkelanlage mit den Maßen A–E aus cad/masse.toml, maßstäblich
- laser_seitenansicht.svg      – Seitenansicht des Laser-Konzepts (docs/laser.md), maßstäblich
- kwtrio_halter.svg            – Zinkhalter des KW-triO-Lasers in drei Ansichten, aus HALTER
- kwtrio_kleinteile.svg        – Schraube, Feder und Taster des KW-triO-Lasers, aus KLEIN

Aufruf im Repo-Wurzelverzeichnis:  uv run docs/bilder/skizzen.py 2>&1 | cat
"""

from __future__ import annotations

import math
import tomllib
from pathlib import Path

HIER = Path(__file__).resolve().parent
MASSE = tomllib.loads((HIER.parent.parent / "cad" / "masse.toml").read_text(encoding="utf-8"))

TEXT = "#222"
LINIE = "#333"
MASS = "#555"
SCHIENE = "#d8d4c8"  # grau-beige wie die Kunststoffschiene
TISCH = "#2f6fa6"  # blau wie der Tisch
ROT = "#d62728"


def zahl(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def kopf(breite: int, hoehe: int, titel: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{breite}" height="{hoehe}" '
        f'viewBox="0 0 {breite} {hoehe}" font-family="sans-serif" font-size="14" fill="{TEXT}">',
        f"<title>{titel}</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        "<defs>",
        f'<marker id="pfeil" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" '
        f'orient="auto"><path d="M0,1 L10,5 L0,9 z" fill="{MASS}"/></marker>',
        f'<marker id="pfeil0" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="8" markerHeight="8" '
        f'orient="auto"><path d="M10,1 L0,5 L10,9 z" fill="{MASS}"/></marker>',
        "</defs>",
    ]


def mass_h(x1: float, x2: float, y: float, text: str, oben: bool = True) -> str:
    ty = y - 6 if oben else y + 18
    return (
        f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{MASS}" marker-start="url(#pfeil0)" '
        f'marker-end="url(#pfeil)"/>'
        f'<text x="{(x1 + x2) / 2}" y="{ty}" text-anchor="middle">{text}</text>'
    )


def mass_v(x: float, y1: float, y2: float, text: str, links: bool = False) -> str:
    tx, anker = (x - 8, "end") if links else (x + 8, "start")
    return (
        f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{MASS}" marker-start="url(#pfeil0)" '
        f'marker-end="url(#pfeil)"/>'
        f'<text x="{tx}" y="{(y1 + y2) / 2 + 5}" text-anchor="{anker}">{text}</text>'
    )


def hilfslinie(x1: float, y1: float, x2: float, y2: float) -> str:
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{MASS}" stroke-width="0.8" stroke-dasharray="3,3"/>'


def querschnitt() -> str:
    w = MASSE["winkelanlage"]
    a, b, c, d, e = w["innensteg_b"], w["innensteg_h"], w["nut_b"], w["nut_t"], w["aussensteg_h"]
    gesamt = 18.0  # gemessen, siehe README
    aussen_b = gesamt - a - c
    grund = b - d  # Höhe des Nutgrunds über dem Tisch

    s = 20.0  # px je mm
    x0, y0 = 200.0, 300.0  # linke untere Ecke der Schiene (Tischkante-Seite)

    def px(x: float) -> float:
        return x0 + x * s

    def py(y: float) -> float:
        return y0 - y * s

    profil = [(0, 0), (0, e), (aussen_b, e), (aussen_b, grund), (aussen_b + c, grund), (aussen_b + c, b),
              (gesamt, b), (gesamt, 0)]
    punkte = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in profil)

    o = kopf(820, 450, "Querschnitt der Winkelanlage, Blick entlang der Schiene")
    # Tisch
    o.append(f'<rect x="40" y="{y0}" width="740" height="18" fill="{TISCH}"/>')
    o.append(f'<text x="40" y="{y0 + 40}">Tischkante</text>')
    o.append(f'<text x="780" y="{y0 + 40}" text-anchor="end">Tischmitte (Papier)</text>')
    o.append(f'<text x="774" y="{y0 + 14}" text-anchor="end" fill="white" font-size="12">Tisch</text>')
    # Schiene
    o.append(f'<polygon points="{punkte}" fill="{SCHIENE}" stroke="{LINIE}" stroke-width="2"/>')
    o.append(f'<text x="{px(aussen_b / 2)}" y="{py(e / 2) + 5}" text-anchor="middle">außen</text>')
    o.append(f'<text x="{px(aussen_b + c + a / 2)}" y="{py(grund / 2) + 5}" text-anchor="middle">innen</text>')
    o.append(f'<text x="{px(aussen_b + c / 2)}" y="{py((grund + b) / 2) + 5}" text-anchor="middle" font-size="12">Nut</text>')

    # E: Höhe außen, links
    o.append(hilfslinie(px(0), py(e), px(-2.5), py(e)))
    o.append(mass_v(px(-2), py(0), py(e), f"E {zahl(e)}", links=True))
    # C: Nutbreite, oben über der Nut
    yc = py(e) - 22
    o.append(hilfslinie(px(aussen_b), py(e), px(aussen_b), yc - 4))
    o.append(hilfslinie(px(aussen_b + c), py(b), px(aussen_b + c), yc - 4))
    o.append(mass_h(px(aussen_b), px(aussen_b + c), yc, f"C {zahl(c)}"))
    # D: Nuttiefe ab Oberkante innerer Steg
    xd = px(gesamt + 2)
    o.append(hilfslinie(px(gesamt), py(b), xd + 10, py(b)))
    o.append(hilfslinie(px(aussen_b + c), py(grund), xd + 10, py(grund)))
    o.append(mass_v(xd, py(grund), py(b), f"D {zahl(d)}"))
    # B: Höhe innen
    xb = px(gesamt + 6)
    o.append(hilfslinie(xd + 10, py(b), xb + 10, py(b)))
    o.append(mass_v(xb, py(0), py(b), f"B {zahl(b)}"))
    # A und Gesamtbreite unter dem Tisch
    ya = y0 + 70
    o.append(hilfslinie(px(aussen_b + c), py(grund), px(aussen_b + c), ya + 4))
    o.append(hilfslinie(px(gesamt), py(0), px(gesamt), y0 + 104))
    o.append(mass_h(px(aussen_b + c), px(gesamt), ya, f"A {zahl(a)}", oben=False))
    o.append(hilfslinie(px(0), py(0), px(0), y0 + 104))
    o.append(mass_h(px(0), px(gesamt), y0 + 100, f"{zahl(gesamt)} gesamt", oben=False))
    o.append(f'<text x="40" y="30" font-size="13" fill="{MASS}">Maße in mm, Maßstab 20 : 1</text>')
    o.append("</svg>")
    return "\n".join(o)


def laser() -> str:
    # Werte aus docs/laser.md (Konzept)
    hoehe, versatz, linie, neigung, faecher = 70.0, 20.0, 340.0, 35.0, 90.0

    s = 1.7  # px je mm
    x0, y0 = 300.0, 330.0  # Punkt auf dem Tisch unter dem Laser

    def px(x: float) -> float:
        return x0 + x * s

    def py(y: float) -> float:
        return y0 - y * s

    xmax = versatz + linie + 30  # Zeichenrand vorne
    lx, ly = px(0), py(hoehe)
    unten = neigung + faecher / 2  # steilster Strahl, Grad unter der Waagerechten
    oben = neigung - faecher / 2  # flachster Strahl (negativ = über der Waagerechten)

    def treffer(winkel: float) -> tuple[float, float]:
        """Endpunkt eines Strahls: auf dem Tisch oder am vorderen Zeichenrand."""
        if winkel > 0:
            x = hoehe / math.tan(math.radians(winkel))
            if x <= xmax:
                return px(x), py(0)
        y = hoehe - xmax * math.tan(math.radians(winkel))
        return px(xmax), py(y)

    o = kopf(1000, 450, "Laser-Konzept, Seitenansicht")
    # Fächer
    fl = [(lx, ly), treffer(unten), (px(xmax), py(0)), treffer(oben)]
    o.append(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in fl)}" fill="{ROT}" fill-opacity="0.12"/>')
    for k in range(9):
        w = unten - k * faecher / 8
        x, y = treffer(w)
        o.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="{ROT}" stroke-opacity="0.45"/>')
    # Tisch und Schnittlinie
    o.append(f'<rect x="{px(-60)}" y="{y0}" width="{px(xmax) - px(-60)}" height="14" fill="{TISCH}"/>')
    o.append(f'<line x1="{px(versatz)}" y1="{y0}" x2="{px(versatz + linie)}" y2="{y0}" stroke="{ROT}" stroke-width="4"/>')
    o.append(mass_h(px(versatz), px(versatz + linie), y0 + 40, f"Schnittkante = Laserlinie, {zahl(linie).replace(',0', '')} mm", oben=False))
    o.append(f'<text x="{px(versatz)}" y="{y0 + 90}">hinten (Drehpunkt)</text>')
    o.append(f'<text x="{px(versatz + linie)}" y="{y0 + 90}" text-anchor="end">vorne (Griff)</text>')
    # Reiter mit Ausleger
    o.append(f'<rect x="{px(-14)}" y="{py(4)}" width="{28 * s}" height="{4 * s}" fill="{SCHIENE}" stroke="{LINIE}"/>')
    o.append(f'<rect x="{px(-3)}" y="{py(hoehe - 5)}" width="{6 * s}" height="{(hoehe - 9) * s}" fill="{SCHIENE}" stroke="{LINIE}"/>')
    o.append(f'<text x="{px(-16)}" y="{py(30)}" text-anchor="end">Reiter auf der</text>')
    o.append(f'<text x="{px(-16)}" y="{py(30) + 18}" text-anchor="end">hinteren Winkelanlage</text>')
    # Lasermodul Ø9 × 26, um die Neigung gedreht
    o.append(
        f'<g transform="translate({lx:.1f},{ly:.1f}) rotate({neigung})">'
        f'<rect x="{-26 * s:.1f}" y="{-4.5 * s:.1f}" width="{26 * s:.1f}" height="{9 * s:.1f}" rx="2" '
        f'fill="#b08d3c" stroke="{LINIE}"/></g>'
    )
    o.append(f'<text x="{lx - 60}" y="{ly - 50}" text-anchor="end">Laser, ~{zahl(hoehe).replace(",0", "")} mm über dem Tisch,</text>')
    o.append(f'<text x="{lx - 60}" y="{ly - 32}" text-anchor="end">~{zahl(neigung).replace(",0", "")}° nach unten geneigt</text>')
    o.append(f'<text x="{px(150)}" y="{py(52)}" fill="{ROT}">Lichtfächer {zahl(faecher).replace(",0", "")}°</text>')
    o.append(f'<text x="20" y="30" font-size="13" fill="{MASS}">Blick quer zur Schnittebene, maßstäblich, Maße in mm</text>')
    o.append("</svg>")
    return "\n".join(o)


# Zinkhalter des KW-triO-Lasers, gemessen mit dem Messschieber.
# Koordinaten: y entlang der Strahlachse ab Stirnseite des Körpers (Laser vorne, Kabel hinten),
# z ab Unterseite nach oben, x quer. "?" = nicht gemessen oder Zuordnung unsicher.
HALTER = {
    "breite": 15.5,        # quer
    "hoehe": 19.1,         # Unterseite bis Scheitel des Bogens vorne
    "laenge": 22.7,        # Körper
    "ring_v": 1.2,         # Ring vorne steht vor
    "ring_d": 12.0,        # Ring vorne
    "dreh_d": 11.9,        # Drehteil hinten (Zylinder)
    "dreh_l": 11.35,       # Drehteil reicht von hinten bis zur Mitte der Länge – geschätzt
    "wand": 1.5,           # Wand der offenen Unterseite
    "zu_vorn_d": 5.7,      # Zapfen unten vorne, steckt im Loch des Blechs
    "zu_hint_d": 4.5,      # Zapfen unten hinten, Gewinde für die M3-Schraube mit Feder
    "zu_h": 4.2,           # Zapfen unten stehen vor
    "luecke": 4.3,         # Lücke zwischen den Zapfen unten
    "zo_kurz_d": 4.5,      # Zapfen oben vorne, Innensechskant – Ø geschätzt
    "zo_kurz_h": 3.7,      # über dem Scheitel
    "hebel_d": 5.0,        # Hebelrohr auf dem Drehteil – Ø geschätzt
    "hebel_h": 6.4,        # über dem Drehteil – Zuordnung unsicher
    "modul_d": 9.0,        # Messinghülse des Lasermoduls – geschätzt
}


def halter() -> str:
    h = HALTER
    s = 7.0
    b, hh, l = h["breite"], h["hoehe"], h["laenge"]
    rb = b / 2
    za = hh - rb                    # Strahlachse über der Unterseite: Bogen konzentrisch zum Drehteil
    rd = h["dreh_d"] / 2
    y_dreh = l - h["dreh_l"]        # Beginn des Drehteils
    dz_top = za + rd                # Oberkante Drehteil
    # Zapfen: unten mittig verteilt, oben geschätzt
    abst = h["zu_vorn_d"] / 2 + h["luecke"] + h["zu_hint_d"] / 2
    yu_v, yu_h = l / 2 - abst / 2, l / 2 + abst / 2
    yo_k, yo_h = y_dreh / 2, y_dreh + h["dreh_l"] / 2
    fest = f'fill="#e4e4e4" stroke="{LINIE}" stroke-width="1.5"'
    dreh = f'fill="#cfd8e3" stroke="{LINIE}" stroke-width="1.5"'
    mitte = f'stroke="{MASS}" stroke-width="0.8" stroke-dasharray="10,3,2,3"'

    o = kopf(1080, 790, "Zinkhalter des KW-triO-Lasers, Ansichten nach Projektionsmethode 3")
    o.append('<text x="20" y="30" font-size="16" font-weight="bold">Zinkhalter des Lasers aus dem KW-triO 13036</text>')
    o.append(f'<text x="20" y="52" font-size="13" fill="{MASS}">Maße in mm, Maßstab 7 : 1, Projektionsmethode 3 (ISO 5456-2), Hauptansicht = Seitenansicht.</text>')
    o.append(f'<text x="20" y="72" font-size="13" fill="{MASS}">Blau = drehbares Teil. „?“ = nicht gemessen oder Zuordnung unsicher, „ca.“ = aus dem Foto geschätzt.</text>')

    # ---------- A: Vorderansicht (Laser) ----------
    ax, az = 250.0, 340.0           # Mitte x, Unterseite z=0
    def AX(x): return ax + x * s
    def AZ(z): return az - z * s
    o.append(f'<text x="{ax}" y="{AZ(h["hebel_h"] + dz_top) - 34}" text-anchor="middle" font-weight="bold">Ansicht von vorn (Laser)</text>')
    o.append(f'<rect x="{AX(-h["hebel_d"]/2)}" y="{AZ(dz_top + h["hebel_h"])}" width="{h["hebel_d"]*s}" height="{(h["hebel_h"] + 1)*s}" {dreh}/>')
    o.append(f'<rect x="{AX(-h["zo_kurz_d"]/2)}" y="{AZ(hh + h["zo_kurz_h"])}" width="{h["zo_kurz_d"]*s}" height="{(h["zo_kurz_h"] + 1)*s}" {fest}/>')
    o.append(f'<rect x="{AX(-h["zu_vorn_d"]/2)}" y="{AZ(0) - 2}" width="{h["zu_vorn_d"]*s}" height="{h["zu_h"]*s + 2}" {fest}/>')
    o.append(f'<path d="M{AX(-rb)},{AZ(0)} L{AX(-rb)},{AZ(za)} A{rb*s},{rb*s} 0 0 1 {AX(rb)},{AZ(za)} L{AX(rb)},{AZ(0)} Z" {fest}/>')
    o.append(f'<circle cx="{AX(0)}" cy="{AZ(za)}" r="{h["ring_d"]/2*s}" fill="#d6d6d6" stroke="{LINIE}" stroke-width="1.3"/>')
    o.append(f'<circle cx="{AX(0)}" cy="{AZ(za)}" r="{h["modul_d"]/2*s}" fill="#d9b44a" stroke="{LINIE}"/>')
    o.append(f'<line x1="{AX(-2.6)}" y1="{AZ(za - 2.2)}" x2="{AX(2.6)}" y2="{AZ(za + 2.2)}" stroke="{ROT}" stroke-width="2"/>')
    o.append(f'<line x1="{AX(-rb - 3)}" y1="{AZ(za)}" x2="{AX(rb + 3)}" y2="{AZ(za)}" {mitte}/>')
    o.append(f'<line x1="{AX(0)}" y1="{AZ(-h["zu_h"] - 2)}" x2="{AX(0)}" y2="{AZ(dz_top + h["hebel_h"] + 2)}" {mitte}/>')
    yb = AZ(-h["zu_h"]) + 26
    o.append(hilfslinie(AX(-rb), AZ(0), AX(-rb), yb + 4)); o.append(hilfslinie(AX(rb), AZ(0), AX(rb), yb + 4))
    o.append(mass_h(AX(-rb), AX(rb), yb, zahl(b), oben=False))
    xl = AX(-rb) - 22
    o.append(hilfslinie(AX(0), AZ(hh), xl - 4, AZ(hh)))
    o.append(mass_v(xl, AZ(0), AZ(hh), zahl(hh), links=True))
    xl2 = xl - 48
    o.append(hilfslinie(AX(-rb), AZ(za), xl2 - 4, AZ(za)))
    o.append(mass_v(xl2, AZ(0), AZ(za), f"{zahl(za)} ?", links=True))
    o.append(f'<text x="{xl2 - 8}" y="{AZ(za/2) + 22}" text-anchor="end" font-size="11" fill="{MASS}">Strahlachse,</text>')
    o.append(f'<text x="{xl2 - 8}" y="{AZ(za/2) + 36}" text-anchor="end" font-size="11" fill="{MASS}">gerechnet</text>')
    o.append(f'<text x="{AX(rb) + 8}" y="{AZ(za + 6.5)}" font-size="12">Ring Ø{zahl(h["ring_d"])}</text>')

    # ---------- C: Ansicht von links, rechts neben A ----------
    cx0, cz = 450.0, az
    def CY(y): return cx0 + (y + h["ring_v"]) * s     # Laser links, Kabel rechts
    def CZ(z): return cz - z * s
    o.append(f'<text x="{CY(l/2)}" y="{CZ(h["hebel_h"] + dz_top) - 34}" text-anchor="middle" font-weight="bold">Seitenansicht (Hauptansicht)</text>')
    o.append(f'<rect x="{CY(yo_k) - h["zo_kurz_d"]/2*s}" y="{CZ(hh + h["zo_kurz_h"])}" width="{h["zo_kurz_d"]*s}" height="{(h["zo_kurz_h"] + 1)*s}" {fest}/>')
    o.append(f'<rect x="{CY(yo_h) - h["hebel_d"]/2*s}" y="{CZ(dz_top + h["hebel_h"])}" width="{h["hebel_d"]*s}" height="{(h["hebel_h"] + 1)*s}" {dreh}/>')
    for yy, d in [(yu_v, h["zu_vorn_d"]), (yu_h, h["zu_hint_d"])]:
        o.append(f'<rect x="{CY(yy) - d/2*s}" y="{CZ(0) - 2}" width="{d*s}" height="{h["zu_h"]*s + 2}" {fest}/>')
    o.append(f'<rect x="{CY(y_dreh)}" y="{CZ(dz_top)}" width="{h["dreh_l"]*s}" height="{(dz_top - za)*s}" {dreh}/>')
    o.append(f'<path d="M{CY(0)},{CZ(0)} L{CY(0)},{CZ(hh)} L{CY(y_dreh)},{CZ(hh)} L{CY(y_dreh)},{CZ(za)} L{CY(l)},{CZ(za)} L{CY(l)},{CZ(0)} Z" {fest}/>')
    o.append(f'<rect x="{CY(-h["ring_v"])}" y="{CZ(za + h["ring_d"]/2)}" width="{h["ring_v"]*s}" height="{h["ring_d"]*s}" fill="#d6d6d6" stroke="{LINIE}" stroke-width="1.3"/>')
    o.append(f'<line x1="{CY(-h["ring_v"]) - 10}" y1="{CZ(za)}" x2="{CY(l) + 10}" y2="{CZ(za)}" {mitte}/>')
    o.append(f'<line x1="{CY(-h["ring_v"]) - 40}" y1="{CZ(za)}" x2="{CY(-h["ring_v"]) - 4}" y2="{CZ(za)}" stroke="{ROT}" stroke-width="3"/>')
    o.append(f'<text x="{CY(-h["ring_v"]) - 42}" y="{CZ(za) - 8}" text-anchor="end" font-size="12" fill="{ROT}">Strahl</text>')
    o.append(f'<text x="{CY(y_dreh + h["dreh_l"]/2)}" y="{CZ((dz_top + za)/2) + 5}" text-anchor="middle" font-size="12">drehbar</text>')
    # Maße C
    y1 = CZ(-h["zu_h"]) + 26
    o.append(hilfslinie(CY(0), CZ(0), CY(0), y1 + 40)); o.append(hilfslinie(CY(l), CZ(0), CY(l), y1 + 40))
    o.append(hilfslinie(CY(-h["ring_v"]), CZ(za - h["ring_d"]/2), CY(-h["ring_v"]), y1 + 40))
    o.append(mass_h(CY(yu_v) + h["zu_vorn_d"]/2*s, CY(yu_h) - h["zu_hint_d"]/2*s, y1 - 6, zahl(h["luecke"])))
    o.append(mass_h(CY(0), CY(l), y1 + 6, zahl(l), oben=False))
    o.append(mass_h(CY(-h["ring_v"]), CY(l), y1 + 36, "24,0 gesamt", oben=False))
    o.append(f'<text x="{CY(-h["ring_v"]) - 4}" y="{CZ(za + h["ring_d"]/2) - 6}" text-anchor="end" font-size="12">{zahl(h["ring_v"])}</text>')
    yt = CZ(dz_top + h["hebel_h"]) - 12
    o.append(hilfslinie(CY(y_dreh), CZ(hh), CY(y_dreh), yt - 4))
    o.append(mass_h(CY(y_dreh), CY(l), yt, f"ca. {zahl(h['dreh_l'])}"))
    xr = CY(l) + 26
    o.append(hilfslinie(CY(yo_h) + h["hebel_d"]/2*s, CZ(dz_top + h["hebel_h"]), xr + 4, CZ(dz_top + h["hebel_h"])))
    o.append(hilfslinie(CY(l), CZ(dz_top), xr + 4, CZ(dz_top)))
    o.append(mass_v(xr, CZ(dz_top), CZ(dz_top + h["hebel_h"]), f"{zahl(h['hebel_h'])} ?"))
    o.append(hilfslinie(CY(l), CZ(0), xr + 4, CZ(0)))
    o.append(mass_v(xr, CZ(-h["zu_h"]), CZ(0), zahl(h["zu_h"])))
    o.append(hilfslinie(CY(l), CZ(-h["zu_h"]), xr + 4, CZ(-h["zu_h"])))
    xk = CY(yo_k) - h["zo_kurz_d"]/2*s - 14
    o.append(mass_v(xk, CZ(hh), CZ(hh + h["zo_kurz_h"]), zahl(h["zo_kurz_h"]), links=True))
    o.append(f'<text x="{CY(l) + 6}" y="{CZ(za) - 8}" font-size="12">Kabel</text>')

    # ---------- F: Rückansicht (Hebel), rechts neben C ----------
    fx, fz = 850.0, az
    def FX(x): return fx - x * s      # gespiegelt, symmetrisch
    def FZ(z): return fz - z * s
    o.append(f'<text x="{fx}" y="{FZ(h["hebel_h"] + dz_top) - 34}" text-anchor="middle" font-weight="bold">Ansicht von hinten (Hebel)</text>')
    o.append(f'<rect x="{FX(h["zo_kurz_d"]/2)}" y="{FZ(hh + h["zo_kurz_h"])}" width="{h["zo_kurz_d"]*s}" height="{(h["zo_kurz_h"] + 1)*s}" {fest}/>')
    o.append(f'<path d="M{FX(-rb)},{FZ(za)} A{rb*s},{rb*s} 0 0 1 {FX(rb)},{FZ(za)} Z" {fest}/>')
    o.append(f'<rect x="{FX(h["zu_hint_d"]/2)}" y="{FZ(0) - 2}" width="{h["zu_hint_d"]*s}" height="{h["zu_h"]*s + 2}" {fest}/>')
    o.append(f'<rect x="{FX(rb)}" y="{FZ(za)}" width="{b*s}" height="{za*s}" {fest}/>')
    o.append(f'<rect x="{FX(h["hebel_d"]/2)}" y="{FZ(dz_top + h["hebel_h"])}" width="{h["hebel_d"]*s}" height="{(h["hebel_h"] + 1)*s}" {dreh}/>')
    o.append(f'<circle cx="{FX(0)}" cy="{FZ(za)}" r="{rd*s}" {dreh}/>')
    o.append(f'<circle cx="{FX(0)}" cy="{FZ(za)}" r="{h["modul_d"]/2*s}" fill="#d9b44a" stroke="{LINIE}"/>')
    o.append(f'<circle cx="{FX(0)}" cy="{FZ(za)}" r="{1.6*s}" fill="#333"/>')
    o.append(f'<line x1="{FX(rb + 3)}" y1="{FZ(za)}" x2="{FX(-rb - 3)}" y2="{FZ(za)}" {mitte}/>')
    o.append(f'<line x1="{FX(0)}" y1="{FZ(-h["zu_h"] - 2)}" x2="{FX(0)}" y2="{FZ(dz_top + h["hebel_h"] + 2)}" {mitte}/>')
    o.append(f'<text x="{FX(-rb) + 8}" y="{FZ(za + rd + 0.5)}" font-size="12">Drehteil Ø{zahl(h["dreh_d"])}</text>')
    o.append(f'<text x="{FX(-rb) + 8}" y="{FZ(za) + 22}" font-size="12">Kabel</text>')
    o.append(f'<text x="{FX(-h["hebel_d"]/2) + 8}" y="{FZ(dz_top + h["hebel_h"]) + 14}" font-size="12">Hebelrohr Ø ca. {zahl(h["hebel_d"])}</text>')
    yf = FZ(-h["zu_h"]) + 26
    o.append(hilfslinie(FX(rb), FZ(0), FX(rb), yf + 4)); o.append(hilfslinie(FX(-rb), FZ(0), FX(-rb), yf + 4))
    o.append(mass_h(FX(rb), FX(-rb), yf, zahl(b), oben=False))

    # ---------- Untersicht, unter der Hauptansicht ----------
    ez = CZ(-h["zu_h"]) + 26 + 36 + 70 + rb * s       # Mittellinie (x = 0)
    def EZ(x): return ez + x * s
    w = h["wand"]
    o.append(f'<text x="{CY(l/2)}" y="{EZ(-rb) - 14}" text-anchor="middle" font-weight="bold">Untersicht</text>')
    o.append(f'<rect x="{CY(-h["ring_v"])}" y="{EZ(-h["ring_d"]/2)}" width="{h["ring_v"]*s}" height="{h["ring_d"]*s}" fill="#d6d6d6" stroke="{LINIE}" stroke-width="1.3"/>')
    o.append(f'<rect x="{CY(0)}" y="{EZ(-rb)}" width="{l*s}" height="{b*s}" {fest}/>')
    o.append(f'<rect x="{CY(w)}" y="{EZ(-rb + w)}" width="{(l - 2*w)*s}" height="{(b - 2*w)*s}" fill="#a8a8a8" stroke="{LINIE}"/>')
    for yy, d, art, dy in [(yu_v, h["zu_vorn_d"], "Ø5,7 Steckzapfen (Blechloch)", 34), (yu_h, h["zu_hint_d"], "Ø4,5 M3, Schraube mit Feder", 56)]:
        o.append(f'<circle cx="{CY(yy)}" cy="{EZ(0)}" r="{d/2*s}" {fest}/>')
        o.append(f'<circle cx="{CY(yy)}" cy="{EZ(0)}" r="{1.3*s}" fill="#444"/>')
        o.append(f'<line x1="{CY(yy)}" y1="{EZ(d/2) + 2}" x2="{CY(yy)}" y2="{EZ(rb) + dy - 12}" stroke="{MASS}" stroke-width="0.8"/>')
        o.append(f'<text x="{CY(yy)}" y="{EZ(rb) + dy}" text-anchor="middle" font-size="12">{art}</text>')
    o.append(f'<line x1="{CY(-h["ring_v"]) - 10}" y1="{EZ(0)}" x2="{CY(l) + 10}" y2="{EZ(0)}" {mitte}/>')
    xe = CY(l) + 26
    o.append(hilfslinie(CY(l), EZ(-rb), xe + 4, EZ(-rb))); o.append(hilfslinie(CY(l), EZ(rb), xe + 4, EZ(rb)))
    o.append(mass_v(xe, EZ(-rb), EZ(rb), zahl(b)))
    o.append(f'<text x="{CY(w) + 3}" y="{EZ(-rb + w) + 14}" font-size="11">Wand {zahl(w)}</text>')
    o.append(f'<text x="{CY(-h["ring_v"]) - 16}" y="{EZ(0) - 6}" text-anchor="end" font-size="11" fill="{MASS}">Laser</text>')

    # ---------- Symbol Projektionsmethode 3 ----------
    unten = EZ(rb) + 100
    px0, py0 = 960.0, unten + 20
    o.append(f'<circle cx="{px0}" cy="{py0}" r="16" fill="none" stroke="{LINIE}" stroke-width="1.3"/>')
    o.append(f'<circle cx="{px0}" cy="{py0}" r="8" fill="none" stroke="{LINIE}" stroke-width="1.3"/>')
    o.append(f'<path d="M{px0 + 40},{py0 - 8} L{px0 + 80},{py0 - 16} L{px0 + 80},{py0 + 16} L{px0 + 40},{py0 + 8} Z" fill="none" stroke="{LINIE}" stroke-width="1.3"/>')
    o.append(f'<line x1="{px0 - 24}" y1="{py0}" x2="{px0 + 88}" y2="{py0}" {mitte}/>')
    o.append(f'<text x="{px0 + 30}" y="{py0 + 36}" text-anchor="middle" font-size="11" fill="{MASS}">Projektionsmethode 3</text>')

    # ---------- offen ----------
    fehl = [
        "Für den Halter am Reiter fehlen noch:",
        "1  Länge des Drehteils (geschätzt halbe Körperlänge) und Höhe des Hebelrohrs über dem Drehteil (6,4 ?)",
        "2  Ø der beiden oberen Zapfen; Lage der Zapfen entlang der Achse (Mitte bis Stirnseite)",
        "3  Strahlachse über der Unterseite (Tiefenmaß von unten bis Mitte Ring) – gerechnet 11,4",
    ]
    for k, t in enumerate(fehl):
        o.append(f'<text x="20" y="{unten + k*22}" font-size="13" {"font-weight=\"bold\"" if k == 0 else ""}>{t}</text>')
    o.append("</svg>")
    return "\n".join(o)


# Kleinteile des KW-triO-Lasers, gemessen mit dem Messschieber; "≈" = aus dem Foto geschätzt.
KLEIN = {
    "schraube_kopf_d": 7.0,   # Bund, gemessen
    "schraube_l_ges": 10.0,   # mit Kopf, gemessen
    "schraube_kopf_h": 2.0,   # geschätzt
    "schraube_d": 2.8,        # gemessen: Außen-Ø des Gewindes -> M3
    "feder_da": 7.6,          # gemessen
    "feder_l": 5.2,           # entspannt, gemessen
    "feder_draht": 0.8,       # geschätzt
    "taster_b": 8.3, "taster_t": 8.4,  # Gehäuse, gemessen
    "taster_kappe_d": 7.9,    # gemessen
    "taster_kappe_h": 4.0, "taster_l": 9.0, "pin_l": 3.0,  # geschätzt
}


def kleinteile() -> str:
    k = KLEIN
    s = 12.0
    o = kopf(1100, 520, "Kleinteile des KW-triO-Lasers")
    o.append('<text x="20" y="30" font-size="16" font-weight="bold">Schraube, Feder und Taster aus dem KW-triO 13036</text>')
    o.append(f'<text x="20" y="52" font-size="13" fill="{MASS}">Maße in mm, gemessen mit dem Messschieber; „ca.“ = aus dem Foto geschätzt, „?“ = Zuordnung unsicher. Maßstab 12 : 1.</text>')
    stil = f'fill="#e4e4e4" stroke="{LINIE}" stroke-width="1.6"'

    # Schraube, Seitenansicht: Kopf oben
    cx, yk = 150.0, 130.0
    kd, kh, d = k["schraube_kopf_d"], k["schraube_kopf_h"], k["schraube_d"]
    l = k["schraube_l_ges"] - kh
    o.append(f'<text x="{cx}" y="100" text-anchor="middle" font-weight="bold">Schraube</text>')
    o.append(f'<path d="M{cx - kd/2*s},{yk + kh*s} Q{cx - kd/2*s},{yk} {cx},{yk} Q{cx + kd/2*s},{yk} {cx + kd/2*s},{yk + kh*s} Z" {stil}/>')
    o.append(f'<rect x="{cx - d/2*s}" y="{yk + kh*s}" width="{d*s}" height="{l*s}" {stil}/>')
    for i in range(1, int(l / 0.5)):
        y = yk + kh*s + i * 0.5 * s
        o.append(f'<line x1="{cx - d/2*s}" y1="{y}" x2="{cx + d/2*s}" y2="{y + 3}" stroke="{LINIE}" stroke-width="0.6"/>')
    o.append(mass_h(cx - kd/2*s, cx + kd/2*s, yk - 10, f"Ø{zahl(kd)}"))
    o.append(hilfslinie(cx + kd/2*s, yk, cx + kd/2*s + 24, yk))
    o.append(mass_v(cx + kd/2*s + 20, yk, yk + (kh + l)*s, f"{zahl(k['schraube_l_ges'])} gesamt"))
    o.append(hilfslinie(cx + d/2*s, yk + (kh + l)*s, cx + kd/2*s + 24, yk + (kh + l)*s))
    o.append(mass_h(cx - d/2*s, cx + d/2*s, yk + (kh + l)*s + 30, f"Ø{zahl(d)} = M3", oben=False))
    o.append(f'<text x="{cx}" y="{yk + (kh + l)*s + 80}" text-anchor="middle" font-size="12">M3 × 8, Linsenkopf mit Bund, Kreuzschlitz (DIN 967)</text>')

    # Feder: Seitenansicht und Draufsicht
    fx0, fy0 = 470.0, 150.0
    da, fl, dr = k["feder_da"], k["feder_l"], k["feder_draht"]
    di = da - 2 * dr
    o.append(f'<text x="{fx0}" y="100" text-anchor="middle" font-weight="bold">Druckfeder</text>')
    wind = 3
    for i in range(wind):
        y = fy0 + (i + 0.5) * fl / wind * s
        o.append(f'<line x1="{fx0 - da/2*s + dr/2*s}" y1="{y - dr/2*s}" x2="{fx0 + da/2*s - dr/2*s}" y2="{y + dr/2*s}" stroke="{LINIE}" stroke-width="{dr*s*0.8}" stroke-linecap="round"/>')
    o.append(mass_h(fx0 - da/2*s, fx0 + da/2*s, fy0 - 10, f"Ø{zahl(da)} außen"))
    o.append(mass_v(fx0 + da/2*s + 20, fy0, fy0 + fl*s, f"{zahl(fl)} entspannt"))
    fy1 = fy0 + fl*s + 150
    o.append(f'<circle cx="{fx0}" cy="{fy1}" r="{(da + di)/4*s}" fill="none" stroke="{LINIE}" stroke-width="{dr*s}"/>')
    o.append(mass_h(fx0 - di/2*s, fx0 + di/2*s, fy1, "", oben=False))
    o.append(f'<text x="{fx0 + da/2*s + 12}" y="{fy1 + 5}" font-size="12">ca. Ø{zahl(di)} innen</text>')
    o.append(f'<text x="{fx0}" y="{fy1 + da/2*s + 28}" text-anchor="middle" font-size="12">3 Windungen; sitzt auf der M3-Schraube im Zapfen Ø4,5</text>')

    # Taster: Seitenansicht
    tx0, ty0 = 800.0, 140.0
    kd2, kh2, tb, tl, pl = k["taster_kappe_d"], k["taster_kappe_h"], k["taster_b"], k["taster_l"], k["pin_l"]
    tt = k["taster_t"]
    o.append(f'<text x="{tx0 + 60}" y="100" text-anchor="middle" font-weight="bold">Taster, 6 Pins</text>')
    o.append(f'<rect x="{tx0 - kd2/2*s}" y="{ty0}" width="{kd2*s}" height="{kh2*s}" rx="6" fill="#d62728" stroke="{LINIE}" stroke-width="1.6"/>')
    o.append(f'<rect x="{tx0 - tb/2*s}" y="{ty0 + kh2*s}" width="{tb*s}" height="{tl*0.55*s}" fill="#c8c8c8" stroke="{LINIE}" stroke-width="1.6"/>')
    o.append(f'<rect x="{tx0 - tb/2*s}" y="{ty0 + (kh2 + tl*0.55)*s}" width="{tb*s}" height="{tl*0.45*s}" fill="#333" stroke="{LINIE}" stroke-width="1.6"/>')
    for x in (-3.0, 0.0, 3.0):
        o.append(f'<rect x="{tx0 + x*s - 3}" y="{ty0 + (kh2 + tl)*s}" width="6" height="{pl*s}" fill="#b08d3c" stroke="{LINIE}"/>')
    o.append(mass_h(tx0 - kd2/2*s, tx0 + kd2/2*s, ty0 - 10, f"Ø{zahl(kd2)}"))
    o.append(mass_h(tx0 - tb/2*s, tx0 + tb/2*s, ty0 + (kh2 + tl + pl)*s + 30, f"{zahl(tb)} × {zahl(tt)}", oben=False))
    xr = tx0 + tb/2*s + 20
    o.append(hilfslinie(tx0 + kd2/2*s, ty0, xr + 4, ty0))
    o.append(hilfslinie(tx0 + tb/2*s, ty0 + (kh2 + tl)*s, xr + 4, ty0 + (kh2 + tl)*s))
    o.append(mass_v(xr, ty0, ty0 + (kh2 + tl)*s, f"ca. {zahl(kh2 + tl)}"))
    o.append(f'<text x="{tx0}" y="{ty0 + (kh2 + tl + pl)*s + 80}" text-anchor="middle" font-size="12">2 × 3 Pins: vermutlich Rastschalter 8 × 8 (2 × Umschalter)</text>')
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    for name, svg in [("winkelanlage_querschnitt.svg", querschnitt()), ("laser_seitenansicht.svg", laser()),
                      ("kwtrio_halter.svg", halter()),
                      ("kwtrio_kleinteile.svg", kleinteile())]:
        (HIER / name).write_text(svg + "\n", encoding="utf-8")
        print("geschrieben:", HIER / name)
