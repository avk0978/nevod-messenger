# Das Admin-Panel: alle Seiten und Einstellungen

Ein Nachschlagewerk zum Admin-Panel des Nodes: was auf jeder Seite ist und was jede Einstellung tut. Hast du den Node gerade erst installiert, beginne mit [Ersteinrichtung im Admin-Panel](../node-panel/) — dort steht das Nötigste Schritt für Schritt.

Das Panel öffnet sich unter `https://deine-domain/nevod-admin` (oder über einen SSH-Tunnel, wenn du es gesperrt hast — siehe [Installation](../node-install/), Schritt 10). Beliebiger Benutzername; das Passwort ist `NEVOD_ADMIN_PASSWORD` aus `.env` oder ein persönliches, das auf der Seite „Sicherheit“ angelegt wurde. Die Sprache wird in der Kopfzeile umgeschaltet.

## Kopfzeile

Oben auf jeder Seite — der Name des Nodes, seine Kennung (`node_id`) und Plaketten mit dem aktuellen Stand: ob der Node in „Netzwerk erkunden“ sichtbar ist, der Zulassungsmodus für Zellen, wer veröffentlichte Zellen sieht.

## Übersicht

Eine Liste aller Zellen (Nutzer und Bots), die auf dem Node registriert sind.

| Spalte | Was sie zeigt |
|---|---|
| Name | Deine eigene Bezeichnung für diese Zelle — nur du siehst sie, im Panel. Eintippen und ✓ oder Enter drücken. Den vom Nutzer gewählten Namen ändert sie nicht. |
| `cell_id` | Die Kennung der Zelle. Vollständig im Tooltip. |
| Sprache | Die Telefonsprache des Nutzers — schreib ihm darin. „Magyar → English“: Nevod hat diese Sprache nicht, die Person sieht die App auf Englisch — schreib auf Englisch. „—“: App älter als 1.3. |
| Status | Online oder offline — ob die App gerade verbunden ist. |
| Puffer | Was darauf wartet, dass der Nutzer online kommt (bis zu 72 Stunden aufbewahrt): **msg** — Nachrichten und Dateiteile, **Dienst** — „zugestellt/gelesen“-Markierungen, Reaktionen und Signale. Dienstpakete kommen an, wenn die Person die App öffnet. |
| Registrierung | Wann sich die Zelle registriert hat. |

Unter der Tabelle — **Sprachen der Mitglieder**: wie viele Personen welche Sprache nutzen, auch Sprachen, die Nevod noch nicht hat. Daran sieht man, welche Sprachen am meisten gebraucht werden.

Tasten:

- **✕** in einer Zeile — die Zelle löschen. Das widerruft ihre Zulassung vollständig: Registrierung, nicht zugestellte Nachrichten und Mitteilungs-Tokens werden gelöscht, der Name wird frei. Um zurückzukommen, braucht die Person einen neuen Einladungscode oder eine neue Anfrage. Der Node löscht Zellen nie selbst — nur du.
- **Registrierungen zurücksetzen** — alle Zellen registrieren sich bei der nächsten Verbindung neu; ein Code muss nicht erneut eingegeben werden.
- **Vollständig zurücksetzen** — unumkehrbar: Alle Mitglieder müssen sich erneut mit einem Einladungscode anmelden. In der Praxis nur nötig beim Umzug oder bei einem kompletten Wechsel der Mitglieder.

## Einstellungen

| Einstellung | Was sie tut | Wann sie gilt |
|---|---|---|
| **Node-Name** | Der Name des Nodes, den Nutzer sehen. Dienstwörter (Nevod, admin, support, official und Ähnliches) sind nicht erlaubt. | Im Panel — sofort; für andere Nodes — nach einem Neustart. |
| **Node-Typ** *(in Entwicklung)* | `permanent` — ein normaler Node. `temporary` — ein temporärer Node, etwa für die Dauer einer Veranstaltung; die App nutzt solche Nodes noch nicht. Lass `permanent` stehen. | Nach einem Neustart. |
| **ID des übergeordneten Nodes** *(in Entwicklung)* | Nur für einen temporären Node nötig: zu welchem dauerhaften Node er gehört. Leer lassen. | Sofort. |
| **Sichtbarkeit in „Netzwerk erkunden“** | `closed` — der Node wird Nutzern anderer Nodes nicht angezeigt. `open` — der Node erscheint in ihrem „Netzwerk erkunden“. Die Registrierung wird dadurch nicht geöffnet. | Nach einem Neustart. |
| **Sichtbarkeit veröffentlichter Zellen** | Wer die Liste der Bots und Seiten von der Seite „Veröffentlichung“ sieht: `off` — niemand, `members` — nur Nutzer dieses Nodes, `public` — alle. | Sofort. |
| **Zulassungsmodus für Zellen** | `delegated` — nur mit Einladungscode; `admin` — mit Code oder auf Antrag mit deiner Freigabe; `open` — jeder, der die Adresse kennt. | Sofort. |
| **Administratoren** | Die Kennungen (`cell_id`) deiner eigenen Zellen, durch Kommas getrennt. Im Modus `admin` bekommen sie in Nevod eine Nachricht über jede neue Anfrage. Deine `cell_id` findest du auf der Seite „Übersicht“. | Sofort. |

Den Node neu starten — auf dem Server, im Ordner `/opt/nevod/installer/docker`:

```
docker compose restart nevod_node
```

## Beitrittsanfragen

Funktioniert im Zulassungsmodus `admin`. Versucht sich jemand ohne Code zu registrieren, sendet die App selbst eine Anfrage — sie erscheint hier mit Name und Notiz. **Freigeben** — die Person bekommt sofort Zugang und eine Mitteilung auf dem Telefon. **Ablehnen** — die App zeigt ihr, dass die Anfrage abgelehnt wurde.

## Posteingang

Nachrichten, die die Nutzer des Nodes aus der App an sein Konto **administrator** geschickt haben: Meldungen zu Nachrichten, Fragen. Jeder Node hat ein Konto administrator; es wird beim ersten Start von selbst angelegt.

Öffne eine Unterhaltung, schreib eine Antwort und klick auf **Antworten** — die Antwort geht verschlüsselt an den Nutzer in Nevod, im Namen von administrator. Auf Nachrichten von Nutzern antwortet man nur so, in der App, nicht per E-Mail.

Hat der Nutzer der Nachricht das App-Protokoll beigefügt (um ein Problem zu untersuchen), erscheint in der Unterhaltung der Link **nevod.log herunterladen**.

Nutzer sehen das Konto administrator deines Nodes mit der Kennzeichnung **Node-Administrator** und dem Namen des Nodes. Die Kennzeichnung wird durch den Schlüssel deines Nodes bestätigt, deshalb kann sich niemand sonst als Administrator deines Nodes ausgeben. Das blaue ✓-Abzeichen ist das Zeichen der Administration des Nevod-Projekts: Es wird durch die Signatur des Projektkurators bestätigt und kommt nur bei Projekt-Nodes vor.

## Einladungen

**Einen Code erstellen:** Wähle die Gültigkeit (1 Stunde, 24 Stunden, 7 Tage) → **+ Code erstellen**. Ein QR-Code und ein Link erscheinen — du kannst sie auf dem Bildschirm zeigen, weiterleiten oder auf **Link kopieren** klicken. Der Link öffnet Nevod mit bereits ausgefüllter Node-Adresse und Code. Der kurze Code wie `ABCD-EFGH` funktioniert nur, wenn in der App der Person schon dein Node eingestellt ist.

Jeder Code gilt einmal. Darunter stehen alle Codes mit Gültigkeit und Status: aktiv, verwendet, von wem.

**Zugelassene Zellen** — wer auf wessen Einladung beigetreten ist. Der Schalter **Darf einladen** erlaubt dieser Person, Codes aus der App zu erstellen (Profil → Jemanden einladen) — im Modus `delegated` überlässt du so Einladungen Vertrauenspersonen.

Mehr unter [Leute einladen](../node-invite/).

## Nodes

**Anschluss an das Nevod-Netz.** Der Status („verbunden · Nodes online“ oder „nicht verbunden“) und die Taste **Mit dem Nevod-Netz verbinden**. Ein verbundener Node bekommt von den Projekt-Nodes Push-Mitteilungen für Telefone und ein Anruf-Relay. Das Feld **Token vom Administrator eines anderen Nodes** ist für den Anschluss über einen anderen Node statt über Nevod Open. Mehr unter [Anschluss an das Nevod-Netz](../node-network/).

**Bekannte Nodes** — alle Nodes des Netzes, die dein Node kennt: Name, Adresse, online oder nicht, wann zuletzt erreichbar. Ein Node, der sich 72 Stunden nicht gemeldet hat, wird aus der Liste entfernt und kommt von selbst zurück, wenn er wieder im Netz auftaucht.

**Node-Einladungen** — ein Token, mit dem sich ein anderer Node über deinen verbinden kann. Es gilt 10 Minuten; gib es dem Administrator des anderen Nodes persönlich, nicht öffentlich.

## Veröffentlichung

Die Bots und Seiten, die dein Node Nutzern in der App zeigt — auf dem „Planeten“ des Nodes in „Netzwerk erkunden“. Wähle eine Zelle, leg Titel, Typ (`bot` — ein Bot, `page` — eine Seite mit Text) und Beschreibung fest → **Veröffentlichen**. **Veröffentlichung zurückziehen** entfernt sie aus der Liste; die Zelle selbst bleibt.

Die Häkchen Claude, ChatGPT, Gemini sind für einen externen KI-Bot, der mit dem Schlüssel des Nutzers arbeitet: welche Anbieter er annimmt. Bei einem normalen Bot nichts ankreuzen.

Wer diese Liste sieht, legst du unter „Einstellungen“ → „Sichtbarkeit veröffentlichter Zellen“ fest.

## KI-Bots

KI-Bots, die direkt im Node laufen und über Claude, ChatGPT oder Gemini **mit dem Schlüssel des Nutzers** antworten: Die Person fügt ihren Schlüssel im Chat mit dem Bot hinzu, der Schlüssel kommt mit jeder Nachricht und wird vom Bot nicht gespeichert. Der Node hat keine eigenen Schlüssel und bezahlt nicht für KI.

**Bot hinzufügen** — leg Name, Beschreibung, eine Anweisung für das Modell und die Anbieter fest oder nimm eine fertige Vorlage (AI Assistant, Tolmach der Übersetzer) und pass sie an. Ein eingeschalteter Bot erscheint bei den Nutzern des Nodes in der Liste „Auf diesem Node“. Ein ausgeschalteter ist gestoppt und verborgen und behält seinen Namen. Löschen ist endgültig: Schlüssel und Name des Bots werden gelöscht, die Unterhaltungen bleiben bei den Nutzern.

> Unterhaltungen mit einem KI-Bot entschlüsselt Code auf deinem Node und gibt sie an den gewählten Anbieter weiter. Nutzer werden darauf in der [Datenschutzerklärung](../../privacy/) (Abschnitt 5) hingewiesen. Schaltest du KI-Bots ein, bist du als Betreiber des Nodes an dieser Weitergabe beteiligt.

## Sicherheit

Persönliche Administratorkonten: **Hinzufügen / Passwort ändern** — Login und Passwort (als Hash gespeichert). Ein Konto pro Administrator; geht jemand, lösch sein Konto, ohne das Hauptpasswort zu ändern. Das Hauptpasswort aus `.env` funktioniert immer als Notzugang.

Fünf falsche Passwörter hintereinander von einer Adresse sperren die Anmeldung für diese Adresse für 15 Minuten.

## Diagnose

**Prüfen** — Selbsttest des Nodes (bis zu 10 Sekunden):

| Prüfung | Bedeutung |
|---|---|
| Aktualität des Codes | Ob der installierte Node-Build hinter dem Protokoll zurückliegt — wenn ja, aktualisiere den Node (siehe [Wartung](../node-maintenance/)). |
| Konsistenz identity/DB | Ob die Einstellungen in `node.json` mit der Datenbank übereinstimmen. |
| Abhängigkeiten und Konfiguration | Ob es Fehler in den Einstellungen gibt (zum Beispiel ein Anruf-Relay ohne `TURN_SECRET`). |
| Externe Erreichbarkeit | Ob ein anderer Node des Netzes deinen von außen erreichen kann. Solange der Node nicht mit dem Netz verbunden ist, zeigt sie „Keine bekannten Peers“ — das ist zu erwarten. |

**Protokolle** — die letzten Einträge des Node-Protokolls. Nachrichtentexte gelangen nie ins Protokoll.
