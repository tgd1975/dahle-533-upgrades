# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Zeichnet die Erklär-Skizzen als SVG (weißer Grund, damit sie in hellem und dunklem Design gleich aussehen).

- winkelanlage_querschnitt.svg – Querschnitt der Winkelanlage mit den Maßen A–E aus cad/masse.toml, maßstäblich
- laser_seitenansicht.svg      – Seitenansicht des Laser-Konzepts (docs/laser.md), maßstäblich
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
                      ("kwtrio_kleinteile.svg", kleinteile())]:
        (HIER / name).write_text(svg + "\n", encoding="utf-8")
        print("geschrieben:", HIER / name)
