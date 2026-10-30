# Wie ein Node funktioniert

Ein Node ist ein Programm auf einem Server, über das Telefone Nachrichten austauschen und Anrufe aufbauen. Hier kurz, was ein Node tut, was er speichert und was er nicht sieht — damit du vor der Installation weißt, worauf du dich einlässt.

## Node, Zelle und Heim-Node

Jeder Nevod-Nutzer ist eine **Zelle**: ein Paar Verschlüsselungsschlüssel, das auf dem Telefon erzeugt wird und es nie verlässt. Eine Zelle registriert sich auf einem Node — ihrem **Heim-Node**. Über ihn bekommt das Telefon Nachrichten, die geschickt wurden, während es aus war.

Nodes sind zu einem gemeinsamen Netz verbunden. Schreibst du jemandem auf einem anderen Node, gibt dein Node die verschlüsselte Nachricht an dessen Node weiter. Einen zentralen Server gibt es nicht: Das Netz sind die Nodes selbst.

Die Last eines Nodes hängt nur von seinem eigenen Kreis ab — seinen Nutzern und Bots — und nicht von der Größe des ganzen Netzes: Ein Node leitet keine Nachrichten anderer Nodes weiter und speichert sie nicht. Deshalb reicht für einen Node ein gewöhnlicher Computer, und er wird nicht schwerer, egal wie viele Menschen auf anderen Nodes zu Nevod kommen. Solche Netze heißen **gering belastet** (Klasse LL-0) — mehr im Artikel [„Low-Load Distributed Data Networks“](../../publications/low-load-networks/) (DOI 10.5281/zenodo.23621073).

## Arten von Nodes

Alle Nodes laufen mit demselben Programm. Was ein Node wird — ein geschlossener Familien-Node, ein offener Community-Node oder der Node einer Organisation —, entscheiden drei Einstellungen im [Admin-Panel](../node-admin/):

- **wen zulassen** — der Zulassungsmodus für Zellen: nur mit Einladungscode, mit Code oder auf Antrag mit deiner Freigabe, oder alle (Einzelheiten in der Tabelle unter [Ersteinrichtung](../node-panel/), Schritt 2);
- **ob der Node in „Netzwerk erkunden“ sichtbar ist** für Nutzer anderer Nodes;
- **was der Node seinen Nutzern zeigt** — die auf ihm veröffentlichten Bots und Seiten.

| Welcher Node | Wen zulassen | Sichtbar in „Netzwerk erkunden“ | Beispiel |
|---|---|---|---|
| Geschlossen: Familie, Freunde, Organisation | mit Einladungscode | nein | Firmen-Node, auf den der Administrator jeden Mitarbeiter einlädt |
| Community mit Auswahl | mit Code oder auf Antrag mit Freigabe | ja | Vereins-Node: jeder kann ihn finden, aber Mitglieder gibt der Administrator frei |
| Offene Community | alle | ja | öffentlicher Node wie Nevod Open |

**Wo der Node läuft** — auf einem gemieteten Server mit Domain oder zu Hause auf deinem Computer — ändert nichts an seinen Möglichkeiten. Ein Heim-Node muss aus dem Internet erreichbar sein: Portweiterleitung am Router und eine Domain. Deshalb ist der Start mit einem gemieteten Server einfacher — die ganze Dokumentation ist dafür geschrieben.

**Wichtig für einen Heim-Node: Aus deinem Heimnetz wird er nach anderen Regeln erreicht.** Telefone verbinden sich über die Domain mit dem Node, und die Domain zeigt auf die externe Adresse deines Routers. Ein Telefon im Heim-WLAN spricht diese externe Adresse von innerhalb des Netzes an, und viele Router lassen solche Verbindungen nicht durch. Dann funktioniert der Node über Mobilfunk, aber im Heim-WLAN meldet die App „Keine Verbindung“. Über die lokale Adresse des Servers (zum Beispiel `192.168.1.10`) geht es auch nicht: Das Zertifikat ist für die Domain ausgestellt, nicht für die Adresse. Gelöst wird das am Router, auf eine von zwei Arten:

- schalte **NAT-Loopback** ein (auch NAT-Hairpinning oder NAT-Reflection genannt), wenn der Router es unterstützt;
- oder lege im DNS des Routers einen lokalen Eintrag an: deine Domain → lokale Adresse des Servers.

Prüfe das gleich nach der Installation: Verbinde dich mit einem Telefon sowohl über das Heim-WLAN als auch über Mobilfunk mit dem Node.

**Die Nodes des Nevod-Projekts** — Nevod Open, Dev Planet und einige andere — unterscheiden sich von den übrigen nicht durch das Programm, sondern durch drei Dinge:

- sie haben einen Apple-Schlüssel für Push-Mitteilungen und ein Anruf-Relay und teilen beides mit den Nodes des Netzes (siehe unten);
- in „Netzwerk erkunden“ tragen sie den **goldenen Ring** eines geprüften Nodes und ein Zweck-Etikett — „Community“, „Informativ“, „KI-Agent“. Der Ring wird durch die Signatur des Projektkurators bestätigt und kommt derzeit nur bei Projekt-Nodes vor;
- **Nevod Open** ist der Node, auf dem die App Nutzer standardmäßig registriert, und der Einstiegspunkt ins Netz für neue Nodes: Man kann sich ohne Einladung mit ihm verbinden.

> In den Panel-Einstellungen gibt es noch „Node-Typ“ — `permanent` oder `temporary` — und „ID des übergeordneten Nodes“. Das ist **in Entwicklung**: temporäre Nodes (zum Beispiel für die Dauer einer Veranstaltung). Die App nutzt sie noch nicht — lass `permanent` stehen und die ID des übergeordneten Nodes leer.

## Was ein Node speichert

- **Registrierungen der Zellen**: Kennung, öffentliche Schlüssel und den vom Nutzer gewählten Anzeigenamen.
- **Nicht zugestellte Nachrichten** — verschlüsselt, bis der Empfänger online kommt, aber höchstens 72 Stunden. Nach der Zustellung wird die Nachricht gelöscht.
- **Mitteilungs-Tokens** der Telefone — um ein Telefon zu „wecken“, wenn eine Nachricht oder ein Anruf kommt.
- **Einladungscodes**, Beitrittsanfragen, Nachrichten von Nutzern an den Administrator des Nodes.
- **Die Liste der anderen Nodes im Netz** und seine eigenen Einstellungen.
- **Technische Protokolle** — in der Größe begrenzt (3 Dateien zu je 10 MB pro Container); alte Einträge werden überschrieben.

## Was ein Node nicht sieht

- **Text von Nachrichten, Fotos, Videos, Sprachnachrichten und Dateien.** Sie werden auf dem Telefon des Absenders mit dem Schlüssel des Empfängers verschlüsselt. Der Node stellt sie zu, ohne den Schlüssel zu haben, mit dem man sie öffnen könnte.
- **Den Inhalt von Anrufen.** Ton und Video gehen direkt oder über ein Relay (TURN) verschlüsselt zwischen den Telefonen.
- **Kontakte und Unterhaltungen auf dem Telefon.** Sie liegen nur auf dem Gerät.

Was der Node dabei sieht: welche Zellen auf ihm registriert sind und unter welchen Namen, wer wem wann schreibt, die Größe von Nachrichten, die IP-Adressen der Verbindungen. Das sind Zustelldaten — ohne sie könnte der Node nicht arbeiten. Mehr in der [Datenschutzerklärung](../../privacy/).

> Der Betreiber des Nodes ist dafür verantwortlich, dass der Node läuft, und für das Backup seiner Daten. Die Unterhaltungen der Nutzer lesen kann er nicht — das folgt aus dem Aufbau des Netzes, nicht aus einem Versprechen.

## Mitteilungen und Anrufe über Projekt-Nodes

Push-Mitteilungen an die Nevod-App aus dem App Store kann nur ein Node senden, der einen Apple-Schlüssel hat, und den haben nur Projekt-Nodes. Deshalb bittet ein mit dem Netz verbundener Node einen Projekt-Node, die Mitteilung für ihn zu senden. Der Projekt-Node sieht dabei das Token des Telefons und den Namen des Absenders für den Mitteilungstitel, und der Text ist immer derselbe — „Neue Nachricht“. Ist der Absender in den Kontakten des Empfängers, setzt das Telefon selbst den Namen ein, unter dem er gespeichert ist.

**Kann ich Mitteilungen direkt von meinem Node senden?** Nein. Mitteilungen an eine App aus dem App Store werden nur mit einem Schlüssel des Apple-Entwicklerkontos angenommen, unter dem die App veröffentlicht wurde — und Nevod wird vom Projekt veröffentlicht. Diesen Schlüssel kann man nicht an Node-Betreiber weitergeben: Er lässt sich nicht auf einen Node beschränken und erlaubt es, jedem Nevod-Nutzer eine Mitteilung mit beliebigem Text zu senden. Deshalb gehen Mitteilungen über Projekt-Nodes, und ihr Text ist immer „Neue Nachricht“.

Ebenso bekommt ein Node ohne eigenes Anruf-Relay (TURN) eines von den Nodes des Netzes — mehr unter [Anrufe über den eigenen Node](../node-turn/).

Daraus folgt Wichtiges: **Ein nicht mit dem Netz verbundener Node stellt Nachrichten zu, aber Telefone bekommen keine Mitteilungen**, solange die App geschlossen ist. Wie du dich verbindest — siehe [Anschluss an das Nevod-Netz](../node-network/).

## Woraus die Installation besteht

Das fertige Server-Paket (der Ordner `installer/docker` im [Quellcode](https://github.com/avk0978/nevod-messenger)) besteht aus zwei Docker-Containern:

| Container | Was er tut | Ports |
|---|---|---|
| `nevod_node` | der Node selbst | 8765 — für andere Nodes; 8766 — das Admin-Panel, nur vom Server selbst erreichbar |
| `nevod_caddy` | der Webserver Caddy: holt selbst ein HTTPS-Zertifikat für deine Domain und reicht Verbindungen von Telefonen und Panel an den Node weiter | 80 und 443 |

Alle Daten des Nodes liegen im Ordner `data/` neben der Einstellungsdatei:

- `node.json` — **die Identität des Nodes**: seine Schlüssel. Verlierst du diese Datei, verlierst du den Node: Ein Node mit derselben Identität lässt sich nicht neu anlegen, und alle Nutzer müssten sich auf einem neuen registrieren. Mach ein Backup.
- `node.db` — die Datenbank: Registrierungen, Einladungen, der Nachrichtenpuffer.

## Was du brauchst

- **Einen Linux-Server** — der günstigste gemietete VPS genügt: 1 CPU, 1 GB Arbeitsspeicher, 10 GB Festplatte. Für Dutzende und Hunderte Nutzer reicht das.
- **Eine Domain** (oder Subdomain), die du auf den Server zeigen lassen kannst — zum Beispiel `node.example.org`. Ohne Domain können Telefone das HTTPS-Zertifikat nicht prüfen.
- **Etwa eine halbe Stunde** und die Fähigkeit, dich per SSH mit dem Server zu verbinden. Alle Befehle stehen unter [Installation Schritt für Schritt](../node-install/) — du kannst sie unverändert kopieren.
