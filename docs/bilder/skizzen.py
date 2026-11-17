# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Zeichnet die Erklär-Skizzen als SVG (weißer Grund, damit sie in hellem und dunklem Design gleich aussehen).

- winkelanlage_querschnitt.svg – Querschnitt der Winkelanlage mit den Maßen A–E aus cad/masse.toml, maßstäblich
- laser_seitenansicht.svg      – Seitenansicht des Laser-Konzepts (docs/laser.md), maßstäblich

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


if __name__ == "__main__":
    for name, svg in [("winkelanlage_querschnitt.svg", querschnitt()), ("laser_seitenansicht.svg", laser())]:
        (HIER / name).write_text(svg + "\n", encoding="utf-8")
        print("geschrieben:", HIER / name)
