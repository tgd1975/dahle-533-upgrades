# Schnittlinien-Laser zum Nachrüsten – Konzept

**Konzept ohne Druckteil.** Der Halter braucht die drei Maße aus dem Abschnitt „Offene Maße“ – ohne sie wäre er
geraten.

Aus den Fotos der Maschine ([docs/fotos/](fotos/)): Hinter der hinteren Winkelanlage liegt ein blauer Streifen
Tisch von rund 20 mm (mit dem Dahle-Schriftzug), die Winkelanlage hat dieselbe Nut wie vorne (4,0 mm breit), und
entlang der Schnittkante ist keine Schutz- und Anpressleiste montiert – die Lichtebene hat dort freie Bahn.

## Prinzip

Ein Linienlaser spannt eine Lichtebene auf. Liegt die Schnittkante (Kante des Untermessers) in dieser Ebene,
zeichnet der Laser die Schnittlinie auf das Papier – egal, wo in der Ebene er sitzt.

![Seitenansicht: Laser auf einem Reiter an der hinteren Winkelanlage, Lichtfächer auf die Schnittkante](bilder/laser_seitenansicht.svg)

- **Ort:** hinten am Drehpunkt des Messers, auf einem Reiter, der wie der Anschlagschieber mit einer Zunge in der
  Nut der hinteren Winkelanlage sitzt. Der Laser steht wenige Millimeter links der Schnittebene (Tischseite) –
  rechts davon schwenkt das Messer.
- **Nicht** am Messerarm (bewegt sich) und nicht über der Tischmitte (stört beim Arbeiten).
- **Warum Laserklasse 1:** der Fächer zeigt in Richtung der Person am Griff. Klasse 1 ist auch beim direkten
  Blick in den Strahl ungefährlich; Module mit 5 mW ohne Klassenangabe sind dafür ungeeignet.

## Lasermodul

Picotronic **L650-1-3(9x26)**, Artikel 70131109, 33,90 € ([Datenblatt/Shop](https://shop.picotronic.de/de/p/70131109)),
beim Hersteller in Koblenz bestellbar.

| Datenblatt | Wert | Prüfung gegen die 533 |
|---|---|---|
| Laserklasse / Leistung | 1 / 1 mW, 650 nm rot | augensicher ✓ |
| Öffnungswinkel | 90° | nötig sind 63° (Laser 70 mm hoch, 20 mm hinter dem Linienanfang, Linie 340 mm) ✓ |
| Gehäuse | Ø9 × 26 mm, Messing, 6 g, Kabel 115 mm | bestimmt die Aufnahme im Halter |
| Betriebsspannung | 2,5–5 V, typisch 3 V, 30 mA | 2 × AAA (3 V) reichen etwa 30 Stunden |
| Liniendicke | < 1,2 mm in 1 m (Fokus fest auf 1 m) | **im Nahbereich 0,1–0,4 m nicht angegeben**, siehe Risiken |
| Betriebstemperatur | 15–30 °C | Innenraum ✓ |

Strom: Batteriehalter 2 × AAA mit Schalter (Reichelt, Berrybase). Nicht direkt an USB – 5 V ist die Obergrenze
des Moduls, USB-Netzteile liefern bis 5,25 V.

Alternative mit einstellbarem Fokus (dünnere Linie): Picotronic LC650-5-3-F(14x45), Klasse 1, aber 153,90 €.

### Alternative: Laser aus dem KW-triO 13036

Ein vorhandener Hebelschneider KW-triO 13036 („Paper Guillotine with Laser Positioning System“, A4, 315 mm
Schnittlänge) hat einen Schnittlinien-Laser, der sich ausbauen lässt. Was die Fotos des eingebauten Lasers zeigen:

| Befund | Bedeutung für die 533 |
|---|---|
| Laserklasse 2 laut Typenschild, Leistung nicht angegeben (Klasse 2: sichtbar, höchstens 1 mW) | Der Fächer darf nur auf den Tisch fallen: Halter so geneigt, dass kein Strahl über die Waagerechte geht, dazu eine Blende oben |
| rundes Messingmodul im Lagerblock am Drehpunkt, Austritt durch ein Loch in der Stirnseite knapp über dem Tisch | dieselbe Lage wie im Konzept, aber niedrig: Der KW-triO zeichnet aus dieser Höhe eine 315-mm-Linie, die 533 braucht 340 mm |
| Innensechskantschraube oben im Lagerblock, mit Drehpfeilen | dreht die Linie; der Halter für die 533 hat seine eigene Einstellung |
| 2 × AAA im Fuß eingeformt, roter Taster | 3 V wie beim Picotronic-Modul; Batteriefach und Taster bleiben im KW-triO, der Halter bekommt einen Batteriehalter 2 × AAA mit Schalter |

Das Modul stammt aus einem Gerät für unter 35 €: Linienqualität und Leistung sind ohne Datenblatt. Die Linie im
KW-triO zeigt, was es an der 533 leisten würde (L-7). Die Klassenangabe eines Billiggeräts ist nicht verlässlich –
die Auslegung mit Fächer nur auf den Tisch und Blende hält auch ein stärkeres Modul unter Augenhöhe.

Niedrig montiert braucht der Reiter keinen hohen Ausleger, und das Licht bleibt nahe am Tisch, weit unter Augenhöhe.
Ob der Laser bei der 533 niedrig sitzen kann oder über den Lagerbock hinwegsehen muss, entscheidet L-2.

## Halter (geplant)

| Einstellung | Wie |
|---|---|
| Linie seitlich verschieben | Reiter auf der Winkelanlage verschieben |
| Linie parallel zur Schnittkante drehen | Modul in seiner Hülse drehen, über einen Hebel mit M3-Stellschraube – 1/10 Umdrehung ≈ 0,25 mm am vorderen Linienende |
| Linie dünner machen | aufsteckbare Schlitzblende (0,8 mm) vor der Optik |

Gerichtet wird einmal: Blatt schneiden, Schnittkante liegen lassen, Linie darauf einstellen.

## Offene Maße

| | Maß | wofür |
|---|---|---|
| L-1 (Streifen hinter der Schiene) | Breite der blauen Tischfläche zwischen hinterer Winkelanlage und Tischkante | Platz für die Haltemagnete des Reiters |
| L-2 (Lagerbock) | Höhe und Breite des grauen Lagerbocks am Drehpunkt, über dem Tisch | Laser muss darüber hinwegsehen |
| L-3 (Schienenende) | Abstand vom messerseitigen Ende der hinteren Winkelanlage zur Schnittkante | Länge des Auslegers |
| L-4 (Austrittshöhe KW-triO) | Höhe der Mitte des Austrittslochs über dem Tisch des KW-triO – ohne Ausbau | Höhe, aus der der Laser eine brauchbare Linie zeichnet |
| L-5 (Linienbeginn KW-triO) | Abstand vom Austrittsloch bis zum Beginn der Linie auf dem Tisch, und ob die Linie bis zum vorderen Ende reicht – ohne Ausbau | steilster Strahl des Fächers, Reichweite |
| L-7 (Linie KW-triO) | Linie im KW-triO einschalten und ansehen: Dicke am nahen und am fernen Ende, gut sichtbar bei Raumlicht? – ohne Ausbau | entscheidet zwischen KW-triO-Modul und Picotronic |
| L-6 (Modul KW-triO) | Durchmesser und Länge des Moduls, Befestigung, Kabellänge – erst nach dem Ausbau | Aufnahme im Halter |

Dazu ein Foto der hinteren rechten Ecke der 533 (Drehpunkt), schräg von oben.

## Risiken

| Risiko | Wahrscheinlichkeit | Folge |
|---|---|---|
| Linie im Nahbereich 1–2 mm dick statt haarfein | wahrscheinlich | Schlitzblende aufstecken (10 min Druck) oder an einer Linienkante orientieren |
| Linie am vorderen Ende (flacher Einfall) bei hellem Licht blass | möglich | Laser höher setzen (Parameter, Neudruck 1 h) |
| Halter wird angestoßen und verstellt sich | gelegentlich | 1 min neu richten |

Die Einstufung als Laserklasse 1 stammt aus dem Datenblatt des Herstellers; das ist eine Einschätzung, keine
Rechtsberatung, ohne Gewähr.
