# Gering belastete verteilte Datennetze: Begriff, Klassifikation und vergleichende Analyse

**Urheber des Begriffs:** Kolpakov Andrey

**Fassung:** 30. September 2026

**Verwandte Materialien:** [Manifest Zero Knowledge Infrastructure](/de/manifesto/), [Vergleich der Netze](/de/compare/#low-load).

---

## Zusammenfassung

Der Artikel führt den Begriff des *gering belasteten verteilten Datennetzes* ein: eines Netzes,
in dem die Last jedes Knotens (Datenverkehr, Speicherung, Dienstzustand) durch den Kreis der
Teilnehmer dieses Knotens begrenzt ist und mit dem Wachstum des Netzes insgesamt nicht steigt. Es
wird gezeigt, dass die in der Nachrichtentechnik üblichen Lastklassifikationen (Auslastungsgrad,
Erlang, die Punkte „Knie“ (knee) und „Klippe“ (cliff) auf der Kurve des Durchsatzes über der Last, Dienstgüteklassen) den *Zustand* eines Netzes zu einem
bestimmten Zeitpunkt beschreiben, nicht eine Eigenschaft seiner Architektur, und Netze daher
nicht nach diesem Merkmal unterscheiden. Vorgeschlagen werden sechs Merkmale eines gering
belasteten Netzes und eine Klassifikation LL-0…LL-3 nach der asymptotischen Last je Knoten.
Fünfzehn Netze, von FidoNet (1984) bis Nevod (2026), werden verglichen und ihre Vorgänger in der
Literatur benannt: Friend-to-Friend-Netze (F2F), verzögerungstolerante Netze (DTN), verteilte
Hashtabellen, Local-first-Software und Gemeinschaftsnetze (Community Networks).

**Schlüsselwörter:** verteilte Netze, Dezentralisierung, Last je Knoten, Skalierbarkeit, F2F,
DTN, Peer-to-Peer-Netze, Messenger, Zero Knowledge Infrastructure.

---

## 1. Einleitung

Die meisten heutigen Nachrichtendienste sind zentralisiert: Das ganze Netz wird von den Servern
eines Unternehmens bedient, und deren Last wächst mit der Zahl der Nutzer. Dezentrale
Alternativen (föderierte Netze, Peer-to-Peer-Overlays, Anonymisierungsnetze) verteilen das
*Eigentum* an der Infrastruktur, aber, wie unten gezeigt, in der Regel nicht die *Last*: Ein
Föderationsserver oder Overlay-Knoten trägt Verkehr, Verlauf und Dienstzustand fremder Nutzer,
und seine Last wächst wieder mit der Größe des Netzes oder seines populären Teils.

Ziel der Arbeit ist es, die Klasse von Netzen herauszuarbeiten, in denen die Last eines Knotens nur von seinem eigenen Kreis bestimmt wird: den Nutzern und Softwareagenten (Bots, KI-Agenten, Dienste), für die er der Heimatknoten ist; diese Klasse zu definieren, eine messbare Klassifikation vorzuschlagen und bestehende Netze nach diesem Merkmal zu vergleichen.

## 2. Last in Datennetzen: bestehende Begriffe

### 2.1 Auslastungsgrad

In der Warteschlangentheorie wird die Last eines Kanals oder Knotens durch den Auslastungsgrad
ρ = λ/μ beschrieben, das Verhältnis von Ankunftsrate zu Bedienrate [1]. Für ρ → 1 wachsen
Warteschlangenlänge und Verzögerung unbegrenzt; bei ρ > 1 ist das System überlastet. In der
Praxis nutzt man grobe Stufen: geringe Auslastung (ρ < ~0,3), mäßige (0,3–0,7), hohe (0,7–0,9),
Sättigung und Überlast; Betreiber planen Leitungen meist mit Reserve bis ~70–80 % zur
Hauptverkehrsstunde. Diese Schwellen sind technische Richtwerte, kein einheitlicher Standard.

### 2.2 Teletraffic: Erlang und Hauptverkehrsstunde

In der Telefonie wird die Verkehrsintensität in Erlang gemessen (1 Erl ist ein ununterbrochen
belegter Kanal) [2]; bemessen wird nach der Hauptverkehrsstunde; man unterscheidet angebotenen,
abgewickelten und verlorenen Verkehr und legt die Dienstgüte als zulässige
Blockierwahrscheinlichkeit fest (Erlang-B- und -C-Formel) [1, 2].

### 2.3 Wie ein Netz auf steigende Last reagiert: „Knie“ und „Klippe“

Jain, Ramakrishnan und Chiu [3] beschrieben drei Betriebsbereiche eines Netzes: vor dem „Knie“
wächst der Durchsatz mit der Last bei geringer Verzögerung; zwischen „Knie“ und „Klippe“ wächst
der Durchsatz kaum noch, während die Verzögerung rasch steigt; hinter der „Klippe“ folgen Stau
und Kollaps. Im „Knie“ erreicht das Verhältnis von Durchsatz zu Verzögerung (die „Leistung“ des Netzes) sein Maximum; auf dieser Unterscheidung beruhen Überlastvermeidung (congestion avoidance: Betrieb nahe am „Knie“) und Überlaststeuerung (congestion control: den Sturz über die „Klippe“ verhindern). Die TCP-Überlaststeuerung beruht auf diesen Ideen [4].

### 2.4 Verkehrs- und Dienstgüteklassen

Die Architektur Differentiated Services [5] führt Weiterleitungsklassen ein (Expedited
Forwarding EF, Assured Forwarding AF, Best Effort BE); die Empfehlung ITU-T Y.1541 [6] legt
Dienstgüteklassen 0–5 für IP-Netze nach Verzögerung, Jitter und Verlusten fest. Das sind
Klassifikationen von *Anforderungen* an die Zustellung, nicht von Last.

### 2.5 Lastzustände: von Unterlast bis Kollaps

Die Betriebszustände eines Netzes nach Last sind in Normen und klassischen Arbeiten beschrieben:

| Zustand | Wo definiert | Bedeutung |
|---|---|---|
| Unterlast (underutilization) | beschreibend, in Normen nicht definiert | Leitungen stehen merklich leer; oft eine bewusste Kapazitätsreserve (Overprovisioning) |
| Normallast | ITU-T E.500 [36] | häufige belastete Zeiträume, in denen die Erwartungen der Nutzer erfüllt werden sollen; für sie werden Dienstgüte-Zielwerte festgelegt |
| Hochlast | ITU-T E.500 [36] | seltene Spitzenzeiten: Erwartungen werden womöglich nicht erfüllt, die Leistung muss aber hoch genug bleiben, damit sich Staus nicht im Netz ausbreiten |
| Überlast | ITU-T E.412 [37]; berücksichtigt in GOST-Normen für Kommunikationsnetze [39] | der Verkehr übersteigt die Leistungsfähigkeit des Netzes; Steuerungsmaßnahmen greifen: automatische Lastbegrenzung, Leitungsreservierung, Umleitung |
| Überlastkollaps (congestion collapse) | RFC 896, J. Nagle, 1984 [38] | jedes Paket wird mehrfach gesendet, der Nutzdurchsatz sinkt fast auf null; erstmals beobachtet im Oktober 1986, als das NSFnet-Backbone von 32 kbit/s auf 40 bit/s abfiel |

Einen etablierten Begriff für ein „voll ausgelastetes“ Netz gibt es nicht; dem Niveau, auf das
ein Netz ausgelegt ist, entspricht die „Normallast“ nach E.500.

Alle diese Zustände sind **Zustände** eines Netzes zu einem bestimmten Zeitpunkt: Dasselbe Netz
ist morgens unterlastet, abends unter Normallast und bei einer Störung überlastet. Die Achse der
Zustände und die unten eingeführte Achse der Architekturklassen sind unabhängig: Auch ein Netz
der Klasse LL-0 kann überlastet werden, etwa wenn ein Knoten an einer schwachen Leitung hängt.

### 2.6 Skalierung der Last je Knoten

In der Literatur zu verteilten Systemen werden die Kosten eines Knotens asymptotisch in
Abhängigkeit von der Teilnehmerzahl N bewertet: Senden an alle Knoten kostet O(N) je Nachricht;
verteilte Hashtabellen (Chord [7], Kademlia [8]) kosten O(log N) für Routing und
Nachbartabelle. Es gibt auch die Aussage, dass in Peer-to-Peer-Systemen die maximale Last je
Knoten nicht mit der Knotenzahl wächst, weil neue Knoten mehr Ressourcen mitbringen, als sie
verbrauchen [9]; gemeint ist aber ein *statistischer Ausgleich* einer Last, die aus fremden
Anfragen besteht.

### 2.7 Fazit

Die Klassifikationen 2.1–2.5 beantworten die Frage „wie ausgelastet ist das Netz *jetzt*“;
danach ist dasselbe Netz mal gering, mal stark belastet. Die russische Wendung
„gering belastetes Netz“ (малонагруженная сеть) wird in der Praxis genau in diesem
beschreibenden Sinn verwendet (ein Netz oder Rechner mit geringer Auslastung) und ist kein
Begriff für eine Architekturklasse. In der Kabeltelefonie hat das Wort „Belastung“ sogar eine
dritte Bedeutung: die „bespulte Leitung“ mit Induktivitätsspulen (Pupinisierung). Nur die Achse
2.6 betrifft eine *Eigenschaft der Architektur*, und eine standardisierte Klassifikation von
Netzen danach gibt es nicht.

## 3. Verteilte Netze: ein Überblick über Ansätze

**Zentralisierte Dienste** (WhatsApp, 2009; Telegram, 2013; Signal, 2014 [10]): Die
Ende-zu-Ende-Verschlüsselung der Inhalte kann stark sein, aber Server, Konten und Metadaten
liegen bei einer Organisation; die Serverlast wächst mit dem gesamten Publikum.

**Föderierte Netze**: E-Mail, Matrix (2014) [11], ActivityPub/Mastodon (2016; W3C-Empfehlung
2018) [12]. Das Eigentum ist auf Server verteilt, doch die Last eines Servers wächst mit seinen
externen Verbindungen: In Matrix wird der Verlauf eines großen Raums auf jeden teilnehmenden
Server repliziert, in ActivityPub wächst die Zustellung mit der Zahl der Follower.

**Peer-to-Peer-Overlays und verteilte Hashtabellen**: Freenet (2001) [13], Chord [7],
Kademlia [8]. Die Knoten sind gleichberechtigt, die Last ist O(log N), aber ein Knoten speichert
und routet Daten fremder Teilnehmer.

**Friend-to-Friend-Netze (F2F).** Den Begriff prägte D. Bricklin im Jahr 2000 [14]: Ein Knoten
verbindet sich nur mit Knoten von Bekannten. Beispiele: Turtle (Popescu, Crispo, Tanenbaum,
2004) [15], OneSwarm [16], der „Darknet“-Modus von Freenet, RetroShare, GNUnet; dazu gehört auch
Speicherung auf vertrauenswürdigen Knoten [17]. Die Zahl der Verbindungen eines Knotens ist durch
die Zahl seiner Freunde begrenzt [18, 19], doch Nachrichten laufen über Freundesketten durch
unbeteiligte Knoten, und das Routing in solchen Netzen bleibt eine schwierige Aufgabe
[18, 19, 20]. **F2F-Netze sind der nächste Vorgänger des vorgeschlagenen Begriffs**: Sie haben
einen Knoten als Erste auf seinen Bekanntenkreis begrenzt, aber nach der Zahl der Verbindungen,
nicht nach der Last.

**Anonymisierende Overlay-Netze** (Onion-Routing): eine Weiterentwicklung der Mix-Netze von D. Chaum (1981) [40] und des Onion-Routings von D. Goldschlag, M. Reed und P. Syverson (1996) [41]; Umsetzungen sind Tor (2002–2004) [21] und Session (2020) [22]. Relay-Knoten, die von Freiwilligen oder Betreibern unterhalten werden, tragen fremden Transitverkehr im Verhältnis zu ihrer Bandbreite.

**Verzögerungstolerante Netze (DTN)**: Falls Architektur (2003) [23], RFC 4838 [24], Bundle
Protocol v7, RFC 9171 [25]: „Speichern und Weiterleiten“ bei Verbindungsabbrüchen. Eine
historische Umsetzung desselben Prinzips ist FidoNet (1984) [26], eine moderne NNCP (2016) [27].

**Stacks für beliebige Übertragungswege und Funknetze**: Reticulum (Protokoll 2016
veröffentlicht) und der Messenger LXMF [28]: Betrieb von wenigen Bit pro Sekunde (LoRa,
Packet Radio) bis zum Internet, standardmäßig verschlüsselt; Meshtastic (2020) [29]:
Textnachrichten über LoRa-Funkmodule.

**Gemeinschaftsnetze** (Community Networks): Freifunk, Guifi.net [30]: Netze, die die Nutzer selbst schaffen und betreiben.

**Local-first-Software** [31] und **Secure Scuttlebutt** (2014) [32]: Daten liegen beim Nutzer;
in SSB speichert ein Knoten die Feeds seiner Freunde und Freundesfreunde, synchronisiert wird,
wenn sich Knoten begegnen.

**Relays**: Nostr (2020) [33]: einfache Relay-Server, von denen die populären vom gesamten
Publikum belastet werden.

## 4. Der Begriff des gering belasteten verteilten Netzes

### 4.1 Definition

**Ein gering belastetes verteiltes Datennetz** ist ein Netz, in dem jeder Knoten einen kleinen,
natürlich begrenzten Teilnehmerkreis bedient und überwiegend dessen eigenen Verkehr trägt. Die
Knoten sind gleichberechtigt und laufen auf gewöhnlicher Hardware. Das Netz überträgt nur das
Nötige, toleriert Verzögerungen und Verbindungsabbrüche und hat kein Zentrum, dessen Abschaltung
oder Beschlagnahme seinen Betrieb stoppen würde.

Der Begriff betrifft den *Aufbau* eines Netzes, nicht seine Auslastung zu einem bestimmten
Zeitpunkt (Abschnitte 2.5, 2.7).

### 4.2 Merkmale

1. **Eigener Kreis**: Die Last eines Knotens wächst mit seinem Kreis, den Menschen und Softwareagenten, die er bedient, nicht mit der Größe des ganzen Netzes. Das Hauptmerkmal.
2. **Gewöhnliche Hardware**: Heimcomputer, Mini-Server oder Router; kein Rechenzentrum nötig.
3. **Sparsame Übertragung**: zuerst Text und Signale, umfangreiche Daten auf Anfrage.
4. **Verzögerungstoleranz**: Ohne Verbindung wartet eine Nachricht und wird später übertragen,
   auch über einen langsamen Kanal.
5. **Kein Zentrum**: kein einzelner Ausfall-, Sperr- oder Beschlagnahmepunkt.
6. **Blindheit des Knotens**: Ein Knoten transportiert nur Chiffretext und kann ihn nicht lesen
   (das Prinzip Zero Knowledge Infrastructure).

### 4.3 Abgrenzung zu den Vorgängern

| Begriff | Was begrenzt ist | Worin er sich unterscheidet |
|---|---|---|
| F2F [14–20] | die Zahl der Verbindungen eines Knotens, durch den Bekanntenkreis | Transit über Bekanntenketten bleibt; die Last ist nicht begrenzt |
| DHT [7, 8] | das Lastwachstum, logarithmisch | ein Knoten trägt Daten Fremder |
| DTN [23–25] | nichts zur Last | Verzögerungen und Abbrüche, nicht Lastverteilung |
| Local-first [31] | der Speicherort der Daten: beim Nutzer | Dateneigentum, nicht das Netz |
| **Gering belastetes Netz** | **die gesamte Last eines Knotens, durch seinen Kreis** | Kombination der Merkmale 1–6; Merkmal 1 ist bestimmend |

## 5. Klassifikation: LL-Klassen

**Die Lastklasse eines Knotens** bestimmt sich nach der am schnellsten wachsenden ihrer drei Komponenten: getragener Verkehr, gespeicherte Daten, gehaltener Dienstzustand. N ist die Zahl der Teilnehmer im Netz, k die Größe des Kreises des Knotens: die Zahl seiner Nutzer und Softwareagenten. Die Schreibweise O(x) („groß O von x“; eingeführt von P. Bachmann 1894 [42], verbreitet durch E. Landau 1909 [43]) bedeutet, dass eine Größe nicht schneller wächst als x mal eine Konstante; für die Klasse LL-0 enthält die Lastabschätzung kein N, nur k.

| Klasse | Knotenlast | Definition |
|---|---|---|
| **LL-0** | O(k) | der Knoten trägt, speichert und merkt sich nur, was seinen Kreis betrifft; kein fremder Transit |
| **LL-1** | O(k) + begrenzt Fremdes | dazu Transit oder Speicherung für andere, begrenzt unabhängig von N (Weiterleitungslimit, Kontingente, Nachbarwahl durch den Knoten selbst) |
| **LL-2** | O(log N) | die Last wächst langsam (verteilte Hashtabellen) |
| **LL-3** | O(N) oder nicht durch den eigenen Kreis begrenzt | die Last wächst mit dem ganzen Netz oder hängt davon ab, wie viele fremde Nutzer auf den Knoten zugreifen (ein populärer Server, ein Relay) |

Ein gering belastetes Netz im strengen Sinn ist ein Netz der Klasse **LL-0**; LL-1 ist fast
gering belastet.

## 6. Vergleichende Analyse

### 6.1 Merkmale (1 = erfüllt, ½ = teilweise, 0 = nicht erfüllt) und Klassen

| Netz | Jahr | Eigener Kreis | Hardware | Sparsamkeit | Verzögerungen | Kein Zentrum | Blinder Knoten | Klasse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Secure Scuttlebutt [32] | 2014 | 1 | 1 | ½ | 1 | 1 | 0 | LL-0 |
| Briar [35] | 2018 | 1 | 1 | ½ | ½ | 1 | 1 | LL-0 |
| Nevod [34] | 2026 | 1 | 1 | ½ | ½ | 1 | 1 | LL-0 |
| FidoNet [26] | 1984 | 1 | 1 | 1 | 1 | 0 | 0 | LL-1 |
| NNCP [27] | 2016 | ½ | 1 | 1 | 1 | 1 | 1 | LL-1 |
| Reticulum / LXMF [28] | 2016 | ½ | 1 | 1 | 1 | 1 | 1 | LL-1 |
| Meshtastic [29] | 2020 | 0 | 1 | 1 | ½ | 1 | ½ | LL-1 |
| Tor [21] | 2002 | 0 | ½ | 0 | 0 | 1 | 1 | LL-3 |
| WhatsApp | 2009 | 0 | 0 | 0 | 0 | 0 | ½ | LL-3 |
| Telegram | 2013 | 0 | 0 | 0 | 0 | 0 | 0 | LL-3 |
| Matrix [11] | 2014 | 0 | ½ | 0 | 0 | ½ | ½ | LL-3 |
| Signal [10] | 2014 | 0 | 0 | 0 | 0 | 0 | ½ | LL-3 |
| Mastodon [12] | 2016 | 0 | ½ | 0 | 0 | ½ | 0 | LL-3 |
| Nostr [33] | 2020 | 0 | ½ | 0 | 0 | 1 | ½ | LL-3 |
| Session [22] | 2020 | 0 | ½ | 0 | ½ | 1 | 1 | LL-3 |

Anmerkungen. Signal und WhatsApp erhalten ½ bei Merkmal 6: Die Inhalte sind Ende-zu-Ende
verschlüsselt, aber die Organisation sieht Metadaten und betreibt die Server. Bei Reticulum und
NNCP tragen und speichern Zwischenknoten fremde Pakete (Merkmal 1 = ½, Klasse LL-1). Jahr ist
die erste öffentliche Version (Reticulum: in Entwicklung seit 2014; Signal: Vorgänger
TextSecure/RedPhone, 2010; Briar: in Entwicklung seit 2011).

### 6.2 Beobachtungen

- Nach dem Hauptmerkmal (LL-Klasse) sind Nevod, Briar und Secure Scuttlebutt am strengsten
  (LL-0); Reticulum und NNCP gehören zu LL-1.
- Alle zentralisierten und föderierten Netze sowie die anonymisierenden Overlay-Netze sind LL-3: Die
  Dezentralisierung des Eigentums bedeutet keine Dezentralisierung der Last.

## 7. Nevod als Beispiel der Klasse LL-0 und seine Grenzen

Nevod [34] ist ein Nachrichtennetz nach dem Prinzip Zero Knowledge Infrastructure: Ein Knoten
(„Node“) bedient nur seine eigenen Teilnehmer und transportiert verschlüsselte Nachrichten ohne
Zugriff auf deren Inhalt; es gibt kein Zentrum; Nodes laufen auf Heim-Hardware oder gemieteten
Servern. Die Dienst-Tabelle der Nodes wächst mit der Zahl der *Nodes*, nicht der Nutzer, und ist
klein.

Grenzen, Stand September 2026 (Merkmale nicht vollständig erfüllt, in der Praxis nicht
bestätigt):

- Merkmal 3: Medien werden vollständig übertragen, ohne Vorschau und Laden auf Anfrage;
- Merkmal 4: Nicht zugestellte Nachrichten werden 72 Stunden gespeichert; Betrieb nur über das
  Internet;
- keine Forward Secrecy: Nachrichten werden auf den Langzeitschlüssel des Empfängers
  verschlüsselt;
- ein Knoten sieht Zustellmetadaten (wer, an wen, wann);
- ein funktionierender Prototyp ohne echte Nutzer und ohne unabhängiges Audit; geschlossener
  Quellcode; App nur für iOS.

Die Merkmale wurden aus den Prinzipien von Nevod abgeleitet, der Vergleich begünstigt es also von
vornherein; die Bewertung von Nevod spiegelt die Architektur wider, nicht die Reife des Produkts.

## 8. Offene Fragen

1. Speicherung für einen Empfänger, der lange offline ist: wer speichert und wie lange, ohne die
   Klasse LL-0 zu verletzen.
2. Wegfindung zwischen vielen Knoten ohne zentrales Verzeichnis.
3. Ist begrenzter Transit (LL-1) für die Zustellung über langsame Kanäle zulässig, und braucht es
   Gegenseitigkeit („du leitest Fremdes weiter, andere leiten deines weiter“)?
4. Welche Komponenten zählen als Last: Verkehr, Speicherung, Zustand, Energieverbrauch, Zeit des
   Administrators.
5. Eine formale Metrik für den Kreis eines Knotens k und ihre Messung in realen Netzen.

## 9. Schluss

Die Lastbegriffe der Nachrichtentechnik beschreiben den Zustand eines Netzes, nicht eine
Eigenschaft seiner Architektur. Der vorgeschlagene Begriff des gering belasteten verteilten
Netzes grenzt eine Architekturklasse ab, in der die Last eines Knotens durch seinen Kreis
begrenzt ist, und ergänzt bekannte Ansätze (F2F, DTN, verteilte Hashtabellen, Local-first,
Gemeinschaftsnetze) um eine Kombination von sechs Merkmalen. Die Klassifikation LL-0…LL-3 macht
den Begriff messbar und erlaubt es, jedes Netz einer Klasse zuzuordnen. Praktische Erprobung und
eine vollständige Literaturrecherche in geschlossenen Datenbanken (IEEE, ACM, eLibrary) sind die
nächsten Schritte.

---

## Literatur

{{REFS}}

---

*Hinweis zur Methode.* Die Übersicht stützt sich auf offene Quellen; kostenpflichtige Datenbanken
(IEEE Xplore, ACM Digital Library im Volltext, Springer, eLibrary) wurden nicht systematisch
durchsucht. Die Bewertungen der Merkmale und Klassen sind Expertenschätzungen auf Grundlage
öffentlicher Beschreibungen der Netze, Stand September 2026.
