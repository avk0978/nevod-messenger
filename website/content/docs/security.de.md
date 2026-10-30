# Sicherheit und Backups

Was Nevod selbst schützt, wie es dich vor Betrügern und Angriffen schützt, was du tun solltest, wie du einen Chat mit einem Passwort sperrst, wie du blockierst und meldest — und warum es in Nevod keine Backups der Nachrichten gibt.

## Was ohne dein Zutun geschützt ist

- **Nachrichten und Anrufe sind verschlüsselt** — auf deinem Telefon, mit dem Schlüssel des Gesprächspartners. Nodes, die Nevod-Entwickler und Apple sehen sie nicht.
- **Schlüssel, Kontakte und Nachrichtenverlauf liegen nur auf deinem Telefon.** Sie sind weder in iCloud- noch in Computer-Backups, weder auf Nodes noch beim Entwickler.
- **Ein Node weiß nur, was er zur Zustellung braucht:** wer auf ihm registriert ist, wem und wann du schreibst — aber nicht, was.

Wie das im Einzelnen funktioniert, steht auf der Seite [Sicherheit](../../security/).

## Schutz vor Betrügern und Angriffen

- **Niemand findet dich über deine Telefonnummer.** Nevod hat keine Telefonnummern und E-Mail-Adressen, sie lassen sich also nicht aus einer geleakten Datenbank holen und für Spam oder Betrugsanrufe nutzen. Schreiben kann dir nur, wer deine Karte hat, oder ein Mitglied deines Nodes.
- **Es gibt kein Kontopasswort — nichts zu stehlen.** Es kann weder ausgespäht noch erraten noch dir entlockt werden. Beim Verbinden beweist das Telefon dem Node, dass es den Schlüssel besitzt, aber der Schlüssel selbst verlässt das Telefon nie.
- **Niemand kann sich als Administration ausgeben.** Dienstnamen — administrator, support, Nevod und ähnlich aussehende — lassen sich nicht registrieren. Die echte Administration trägt ein blaues ✓-Abzeichen, der Administrator eines privaten Nodes die Kennzeichnung **Node-Administrator**. Ein Konto mit Dienstnamen ohne Abzeichen und Kennzeichnung markiert die App mit einem orangen ⚠ und einer Warnung im Chat.
- **Gefälschte Mitteilungen kommen nicht durch.** Eine Mitteilung über eine neue Nachricht enthält keinen Text, den ein Außenstehender festlegen könnte: nur „Neue Nachricht“ und den Namen des Absenders, und Dienstnamen darin werden durch „Nevod“ ersetzt. Eine Mitteilung „von Nevod“, die dich auffordert, einen Code einzugeben oder einem Link zu folgen, ist Betrug.
- **Dein Node lässt sich nicht vortäuschen.** Alles, was vom Node kommt, ist mit seinem Schlüssel signiert, und die App prüft die Signatur. Selbst in einem fremden WLAN kann sich niemand dazwischen als dein Node ausgeben oder gefälschte Nachrichten in seinem Namen unterschieben.
- **Gefährliche Dateien und Bilder werden aussortiert.** Die gefährlichsten Angriffe auf Telefone — etwa die Spionagesoftware Pegasus — kommen als speziell präpariertes Bild oder Datei und wirken ohne ein einziges Antippen. Deshalb prüft Nevod alles, was es von anderen erhält: Die Dateigröße ist begrenzt, und der Typ muss zum Inhalt passen — sonst wird die Datei nicht als Bild oder Video angezeigt und öffnet sich nicht von selbst. Avatare werden nur von deinen Kontakten und Mitgliedern deines Nodes angenommen, und die App zeigt nie das gesendete Bild an, sondern zeichnet es selbst neu.
- **Solange das Telefon gesperrt ist, sind Dateien verschlossen.** Fotos, Videos und Dateien aus Chats werden von iOS verschlüsselt und sind wenige Sekunden nach dem Sperren unzugänglich — selbst für jemanden, der Zugriff auf den Speicher des Telefons erlangt hat. Der App-Umschalter zeigt statt deiner Unterhaltung ein Nevod-Deckblatt.
- **Ein Angriff auf einen Node legt deine Nachrichten nicht offen.** Auf einem Node liegen weder Nachrichtentexte noch deine Schlüssel: Selbst mit Zugriff auf den Node kann ein Angreifer deine Unterhaltungen nicht lesen.
- **Geprüfte Nodes sind gekennzeichnet.** Die Nodes des Nevod-Projekts tragen in **Netzwerk erkunden** einen goldenen Ring — er wird durch die Signatur des Projekts bestätigt, und ein gefälschter Node kann ihn nicht bekommen.

## Was du tun solltest

Die verwundbarste Stelle ist das Telefon selbst: Wer dein Telefon entsperrt, sieht auch deine Unterhaltungen. Und ist bereits Spionagesoftware auf dem Telefon, die iOS selbst geknackt hat, sieht sie alles, was du auf dem Bildschirm siehst — davor schützt keine App, auch Nevod nicht. Deshalb ist es wichtig, dass sie gar nicht erst dorthin gelangt.

- **Ein Code auf dem iPhone** — unbedingt, und kein einfacher wie 000000.
- **Halte iOS aktuell** — Updates schließen die Lücken, die Spionagesoftware nutzt.
- **Starte dein Telefon ab und zu neu.** Viele Spionageprogramme überstehen keinen Neustart.
- **Wenn du Journalist, Menschenrechtsverteidiger bist oder aus einem anderen Grund Ziel werden könntest** — schalte den **Blockierungsmodus** des iPhone ein: **Einstellungen → Datenschutz & Sicherheit → Blockierungsmodus**. Er schließt viele der Wege, die Angriffe wie Pegasus nutzen.
- **Ein Passwort für wichtige Chats** — siehe unten.
- **Gib niemandem Codes oder Schlüssel.** Die Nevod-Administration schreibt nur in der App, vom Konto **administrator** mit dem ✓-Abzeichen (auf einem privaten Node — mit der Kennzeichnung **Node-Administrator**), nie per E-Mail, und fragt nie nach Passwörtern, Schlüsseln oder Codes. Wer danach fragt, ist ein Betrüger.

## Chat-Passwort

Du kannst einen einzelnen Chat mit einem Passwort sperren — dann kann selbst jemand, der dein entsperrtes Telefon in der Hand hat, diesen Chat nicht öffnen.

1. Öffne den Chat → das Zahnrad oben rechts → schalte **Passwortschutz** ein.
2. Lege zwei Passwörter fest:
   - **Entsperrpasswort** — damit öffnest du den Chat;
   - **Notfallpasswort** — für den Fall, dass du gezwungen wirst, den Chat zu öffnen. Gibst du es statt des echten ein, wird die Unterhaltung in diesem Chat **still gelöscht** von deinem Telefon, und auf dem Bildschirm erscheint das übliche „Falsches Passwort“ — für Zuschauer sieht es wie ein Tippfehler aus.
3. Die Passwörter müssen verschieden sein. Ändern kannst du sie am selben Ort — **Passwörter ändern**.

> Das Chat-Passwort wird nur auf diesem Telefon gespeichert, und zwar nicht das Passwort selbst, sondern sein Hash. **Ein vergessenes Passwort lässt sich nicht wiederherstellen** — weder von dir noch von den Entwicklern —, und der Chat lässt sich dann nicht mehr öffnen. Wähle ein Passwort, das du nicht vergisst. Das Notfallpasswort löscht die Unterhaltung nur bei dir: Der Gesprächspartner behält sie.

## Blockieren und melden

- Jemanden **blockieren** — Chat-Einstellungen (Zahnrad) → **Blockieren**. Die Person kann dir weder schreiben noch dich anrufen und erfährt nichts davon. Die Liste der Blockierten — **Profil → Sicherheit → Blockiert**.
- **Eine Nachricht melden** — halte sie gedrückt → **Melden**. Eine Person melden — Chat-Einstellungen → **Melden**.
- **Missbrauch melden** ohne bestimmten Chat — **Profil → Sicherheit → Missbrauch melden**.

Die Meldung geht an die Administration deines Nodes — als Nachricht in der App an das Konto administrator (oder per E-Mail an abuse@nevod.network). Nachrichten in Nevod sind verschlüsselt, und die Administration sieht sie nicht, deshalb fügt die App den Text der gemeldeten Nachricht der Meldung bei. Die Antwort kommt im Chat mit administrator. Zusammen mit der Meldung kannst du die Person gleich blockieren — **Auch blockieren**.

## Es gibt keine Backups — mit Absicht

Schlüssel, Kontakte und Nachrichtenverlauf gibt es nur auf deinem Telefon. Deshalb:

- **ist das Telefon verloren, kaputt oder zurückgesetzt, lassen sich die Unterhaltungen nicht wiederherstellen;**
- **löscht auch das Löschen der App den Verlauf;**
- **gibt es noch keine Übertragung auf ein neues Telefon.** Auf einem neuen Telefon erstellst du eine neue Identität, und deine Kontakte brauchen deine neue Karte.

Das folgt aus dem Aufbau von Nevod: Eine Kopie, aus der sich deine Unterhaltungen wiederherstellen ließen, wäre auch eine Kopie, auf die jemand anderes zugreifen könnte. Musst du etwas aus einer Unterhaltung lange aufbewahren, speichere es separat: Fotos und Dateien — über **Teilen**.

## Identität zurücksetzen

**Profil → Identität zurücksetzen…** löscht dauerhaft deine Identität, deine Kontakte, die Nachrichten auf dem Telefon und deine Registrierung auf dem Node. Die App bittet dich, ein Bestätigungswort einzugeben, damit das nicht versehentlich passiert.

Zurücksetzen brauchst du, wenn du neu anfangen oder auf einen anderen Node wechseln willst. Deine Kontakte sehen in eurem Chat **Identität gelöscht**; um dir wieder zu schreiben, brauchen sie deine neue Karte.
