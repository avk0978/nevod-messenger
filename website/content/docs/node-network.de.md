# Anschluss an das Nevod-Netz

Wozu ein Node das Netz braucht, wie du ihn mit einer Taste verbindest und was andere Nodes danach sehen.

## Wozu verbinden

Ein Node, der mit niemandem verbunden ist, ist eine Insel. Er funktioniert, aber:

- **seine Nutzer können nur einander schreiben und anrufen.** Jemandem auf einem anderen Node zu schreiben oder von ihm eine Nachricht zu bekommen, ist unmöglich — der Node weiß nicht, wohin damit;
- **Telefone bekommen keine Mitteilungen,** solange die App geschlossen ist: Push-Mitteilungen an Nevod aus dem App Store können nur Projekt-Nodes senden, die den Apple-Schlüssel haben, und sie tun das für die Nodes des Netzes;
- **Anrufe über schwierige Netze kommen womöglich nicht zustande:** Ein Node ohne eigenes Anruf-Relay (TURN) bekommt eines von den Nodes des Netzes — mehr unter [Anrufe über den eigenen Node](../node-turn/).

Deshalb lohnt es sich fast immer, den Node mit dem Netz zu verbinden — auch einen geschlossenen Familien- oder Organisations-Node. Der Anschluss ans Netz **öffnet nicht die Registrierung** und **zeigt den Node nicht in „Netzwerk erkunden“**: Wen du zulässt und ob der Node sichtbar ist, entscheidest weiterhin du in den Einstellungen.

## So verbindest du dich

1. Stell sicher, dass Port **8765** auf dem Server von außen offen ist — sowohl in `ufw` als auch in der Firewall des Anbieters (siehe [Installation](../node-install/), Schritte 1 und 5). Über ihn sprechen Nodes miteinander.
2. Panel → **Nodes** → **Mit dem Nevod-Netz verbinden**.
3. Nach wenigen Sekunden erscheint „Verbunden“. Der Status oben im Block wechselt zu „verbunden · Nodes online: N“, und in der Liste **Bekannte Nodes** erscheinen die Nodes des Netzes.

Der Node verbindet sich über Nevod Open — einen Projekt-Node, der Nodes ohne Einladung ins Netz aufnimmt. Die Echtheit von Open wird anhand des Fingerabdrucks seines Zertifikats geprüft, der im Node-Programm hinterlegt ist: Unterwegs lässt er sich nicht austauschen.

Meldet das Panel, dass **der Netz-Node deinen Node von außen nicht erreichen konnte**, ist die Verbindung zwar zustande gekommen, aber niemand kann sich zurück zu dir verbinden. Fast immer ist Port 8765 zu. Öffne ihn und drück die Taste noch einmal. Prüfen kannst du das auch später: **Diagnose → Prüfen → Externe Erreichbarkeit**.

Die Verbindung bleibt bestehen: Nach einem Neustart meldet sich der Node von selbst bei allen Nodes, die er kennt.

## Verbinden über einen anderen Node

Kennst du den Administrator eines anderen Nodes, kannst du dich über seinen Node statt über Open verbinden:

1. Er, in seinem Panel: **Nodes → Node-Einladungen → + Node-Einladung erstellen** — und gibt dir das Token persönlich (das Token gilt 10 Minuten).
2. Du: **Nodes** → füge das Token in das Feld **Token vom Administrator eines anderen Nodes** ein → **Mit Token verbinden**.

Das Ergebnis ist dasselbe: Dein Node wird Teil des Netzes. Genauso kannst du einen dir bekannten Node über deinen ins Netz lassen — erstelle ein Token für ihn.

## Was andere Nodes sehen

Die Nodes des Netzes tauschen eine Liste der Nodes aus. Über deinen Node enthält sie:

- die Kennung des Nodes (`node_id`), seinen Namen und seine Adresse für Verbindungen zwischen Nodes (`domain:8765`);
- den Zertifikats-Fingerabdruck des Nodes;
- ob der Node in „Netzwerk erkunden“ sichtbar ist und ob er ein eigenes Anruf-Relay und einen Mitteilungsschlüssel hat.

Ist der Node in „Netzwerk erkunden“ sichtbar (Einstellung `open`), erfahren die Nodes des Netzes außerdem, welche Zellen auf ihm registriert sind — anhand der Kennungen, ohne Namen. Ein geschlossener Node teilt das nicht mit: Eine Nachricht an seinen Nutzer kommt über die Adresse aus der Kontaktkarte an, in der der Heim-Node steht.

Was die Nodes des Netzes nie bekommen: Nachrichtentexte, Dateien, Anrufe, Kontakte der Nutzer, Namen und Schlüssel der Zellen eines geschlossenen Nodes.

## Das Netz verlassen

Eine eigene Taste „Netz verlassen“ gibt es noch nicht. Einen Node, der sich 72 Stunden nicht gemeldet hat, entfernen die anderen Nodes von selbst aus ihren Listen. Soll der Node dauerhaft vom Netz getrennt werden, stoppe ihn oder schließe Port 8765.
