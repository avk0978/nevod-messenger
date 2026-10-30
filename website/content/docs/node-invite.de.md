# Leute einladen

Wie Menschen auf deinen Node kommen — per Einladung, per Anfrage oder frei — und wie sie sich danach finden, auch Menschen auf anderen Nodes. Welchen Modus du nutzt, legst du im Panel fest: **Einstellungen → Zulassungsmodus für Zellen** (siehe [Ersteinrichtung](../node-panel/), Schritt 2).

## Eine Einladung vom Administrator

Der Hauptweg — und der einzige, solange der Node im Standardmodus (`delegated`) läuft.

1. Panel → **Einladungen** → wähle die Gültigkeit: 1 Stunde, 24 Stunden oder 7 Tage → **+ Code erstellen**.
2. Gib der Person die Einladung auf einem dieser Wege:
   - **zeig den QR-Code** auf dem Bildschirm — die Person scannt ihn mit der normalen Kamera des Telefons;
   - **Link kopieren** — und schick ihn über einen beliebigen Messenger oder per E-Mail;
   - **diktiere den kurzen Code** wie `ABCD-EFGH` — das funktioniert nur, wenn in der App der Person schon dein Node eingestellt ist.
3. Die Person installiert Nevod aus dem App Store, öffnet den Link (auf der Einladungsseite gibt es die Taste **In Nevod öffnen**), gibt einen Namen ein und tippt auf **Los geht's**.

Was du über Codes wissen solltest:

- **Jeder Code gilt einmal.** Ein Code pro Person. Ein benutzter Code ist in der Liste als „verwendet“ markiert, daneben, wer damit beigetreten ist.
- **Gültigkeit.** Wähle keine Woche für einen Code, den du in einen Gruppenchat stellst: Solange der Code nicht benutzt ist, kann ihn jeder verwenden, der ihn in die Hände bekommt. 1 Stunde ist für einen Code, den du jemandem persönlich zeigst.
- **Der Link verrät nichts Überflüssiges.** Er enthält nur die Adresse des Nodes und den Code. Die Einladungsseite auf nevod.network sieht weder den Code noch die Adresse: Sie stehen im Teil des Links nach `#`, den der Browser nicht an den Server schickt.

Nutzt die Person Nevod schon auf einem anderen Node, verschiebt die Einladung sie nicht von selbst: Die App warnt, dass sie zuerst ihre Identität zurücksetzen muss (**Profil → Identität zurücksetzen…**). Das Zurücksetzen löscht dauerhaft ihre Identität, ihre Kontakte, die Nachrichten auf dem Telefon und ihre Registrierung auf dem bisherigen Node. Um einfach miteinander zu schreiben, muss sie nicht wechseln: Kontakte auszutauschen genügt (siehe unten).

## Mitglieder laden selbst ein

Im Modus `delegated` kannst du Einladungen Vertrauenspersonen überlassen: Panel → **Einladungen** → **Zugelassene Zellen** → schalte bei der Person **Darf einladen** ein. Dann erstellt **Profil → Jemanden einladen** in ihrer App einen Code, und die App zeigt einen QR-Code zum Scannen.

Im Modus `open` kann jedes Mitglied einladen — aber in diesem Modus braucht man ohnehin keinen Code.

## Anfragen mit Freigabe

Der Modus `admin` passt, wenn man den Node finden und um Aufnahme bitten können soll, aber du entscheidest.

1. Die Person findet deinen Node in „Netzwerk erkunden“ und tippt auf **Diesem Node beitreten** (wenn der Node dort sichtbar ist, siehe [Ersteinrichtung](../node-panel/), Schritt 4) — oder tippt beim ersten Start der App auf **Server wechseln…** und gibt die Adresse des Nodes `node.example.org/nevod-ws` ein.
2. Die App sendet selbst eine Anfrage und zeigt „Warten auf Freigabe“.
3. Die Anfrage erscheint im Panel auf der Seite **Beitrittsanfragen**. Ist unter **Einstellungen → Administratoren** deine `cell_id` eingetragen, bekommst du zusätzlich eine Nachricht in Nevod.
4. **Freigeben** — die Person bekommt eine Mitteilung und ist sofort drin. **Ablehnen** — die App zeigt ihr, dass die Anfrage abgelehnt wurde.

Einladungscodes funktionieren auch im Modus `admin` — mit Code ist man sofort drin, ohne Anfrage.

## Freie Registrierung

Im Modus `open` kann sich jeder registrieren, der die Adresse des Nodes kennt. Das passt zu einer offenen Community. Bedenke:

- der Node löscht nie selbst Registrierungen und gibt keine Namen frei — Überflüssiges musst du von Hand aufräumen, auf der Seite **Übersicht** (Taste ✕);
- Dienstnamen (Nevod, administrator, support und Ähnliches) können in keinem Modus vergeben werden.

## Wie Mitglieder sich finden

Die Registrierung auf demselben Node macht Menschen nicht zu Kontakten. Um zu schreiben, müssen sie Kontakte austauschen:

- **Profil → Meine Karte teilen** — zeigt einen QR-Code und den Kartentext; die andere Person: **Kontakte → Kontakt hinzufügen**, dann QR-Code scannen oder Text einfügen;
- die Karte kann auf jedem Weg verschickt werden — nichts darin ist geheim, nur eine Kennung und öffentliche Schlüssel.

Menschen **auf anderen Nodes** werden genauso hinzugefügt — die Karte enthält die Adresse ihres Heim-Nodes. Damit solche Unterhaltungen funktionieren, muss dein Node [mit dem Nevod-Netz verbunden](../node-network/) sein.

> Einen Nutzer löschen (Panel → **Übersicht** → ✕) widerruft seine Zulassung vollständig: Registrierung, nicht zugestellte Nachrichten und Mitteilungs-Tokens werden gelöscht. Um zurückzukommen, braucht die Person eine neue Einladung.
