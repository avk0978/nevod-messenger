# Fragen und Probleme

Kurze Antworten auf häufige Fragen und was zu tun ist, wenn etwas nicht funktioniert. Ist deine Frage nicht dabei, schreib uns (am Ende dieses Abschnitts).

## Allgemeine Fragen

**Kostet Nevod etwas?**
Nein. Die App ist kostenlos, ohne Abos und ohne Werbung. Bezahlen musst du höchstens einen KI-Anbieter, wenn du KI-Assistenten mit deinem eigenen Schlüssel nutzt — siehe [Bots und KI-Assistenten](../bots/).

**Brauche ich eine Telefonnummer?**
Nein. Nevod braucht weder Telefonnummer noch E-Mail-Adresse und fragt nicht danach. Dich kennen nur die, mit denen du Karten ausgetauscht hast.

**Gibt es Nevod für Android oder den Computer?**
Derzeit nur für iPhone und iPad. Eine Android-Version ist in Entwicklung.

**Kann ich Nevod auf zwei Geräten gleichzeitig nutzen?**
Noch nicht: Eine Identität lebt auf einem Gerät. Auf einem zweiten iPhone oder iPad hast du eine eigene Identität mit eigenen Kontakten.

**Ich habe mein Telefon gewechselt. Wie übertrage ich meine Unterhaltungen?**
Vorerst gar nicht: Eine Übertragung auf ein neues Gerät gibt es nicht, und Backups der Nachrichten macht Nevod absichtlich nicht. Erstelle auf dem neuen Telefon eine neue Identität und schick deinen Kontakten deine neue Karte. Mehr unter [Sicherheit und Backups](../security/).

**Wie wechsle ich auf einen anderen Node?**
Nur über das Zurücksetzen der Identität: **Profil → Identität zurücksetzen…**, dann öffne die Einladung auf den neuen Node. Das Zurücksetzen löscht dauerhaft deine Identität, deine Kontakte, die Nachrichten auf dem Telefon und deine Registrierung auf dem bisherigen Node. Um einfach mit jemandem auf einem anderen Node zu schreiben, musst du nicht wechseln — seine Karte genügt.

## Registrierung

| Was du siehst | Was zu tun ist |
|---|---|
| „Name bereits vergeben, wähle einen anderen“ | dieser Name existiert auf dem Node schon, oder es ist ein Dienstname (administrator, support, Nevod…). Wähle einen anderen. |
| „Einladungscode erforderlich“ | der Node nimmt nur mit Einladung auf. Bitte den Administrator des Nodes um eine Einladung oder wähle einen anderen Node. |
| „Ungültiger oder abgelaufener Code — hol dir einen neuen“ | der Code wurde schon benutzt oder ist abgelaufen. Bitte um einen neuen. |
| „Warten auf Freigabe“ | der Node nimmt auf Antrag auf — warte auf die Entscheidung des Administrators; du bekommst eine Mitteilung. |
| „Anfrage abgelehnt“ | der Administrator des Nodes hat deinen Antrag abgelehnt. Du kannst einen anderen Node wählen, etwa Nevod Open. |
| du hast eine Einladung geöffnet, und die App zeigt „Einladung zu einem anderen Knoten“ | du bist schon auf einem Node registriert. Siehe „Wie wechsle ich auf einen anderen Node?“ oben. |
| du hast eine Einladung geöffnet, und die App zeigt „Du bist auf diesem Node bereits registriert“ | die Einladung ist für deinen eigenen Node — es ist nichts zu tun. |

## Verbindung

**Über dem Eingabefeld steht „Keine Verbindung“ oder lange „Verbindung wird hergestellt…“, und du kannst nichts senden.**
Prüfe dein Internet: Öffne irgendeine Website. Nutzt du ein VPN, schalte es aus oder wechsle den Server. Wechsle zwischen WLAN und Mobilfunk. Hilft das nicht, ist dein Node vielleicht vorübergehend nicht erreichbar — warte ein paar Minuten; bist du auf einem privaten Node, sag seinem Administrator Bescheid.

**Mitteilungen kommen nicht an, solange Nevod geschlossen ist.**
- **iPhone-Einstellungen → Nevod → Mitteilungen** — sie müssen erlaubt sein.
- Prüfe, ob „Nicht stören“ oder ein anderer Fokus eingeschaltet ist.
- Prüfe, ob Mitteilungen für diesen Chat ausgeschaltet sind: Chat-Einstellungen (Zahnrad) → **Mitteilungen**.
- Auf einem privaten Node: Bitte den Administrator zu prüfen, ob der Node [mit dem Nevod-Netz verbunden](../node-network/) ist — sonst kommen keine Mitteilungen an.

**Ein Anruf kommt nicht zustande.** Siehe [Anrufe](../calls/), „Wenn ein Anruf nicht zustande kommt“.

## Nachrichten und Dateien

**Neben einer Nachricht ist eine orange Uhr.**
Der Gesprächspartner ist offline: Die Nachricht wartet auf dem Node und wird zugestellt, sobald er sich verbindet. Der Node bewahrt solche Nachrichten bis zu 72 Stunden auf — kommt die Person in dieser Zeit nicht online, wird die Nachricht nicht zugestellt.

**„Nachricht nicht gesendet. Erneut senden?“**
Beim Senden gab es keine Verbindung. Tippe auf diese Zeile, wenn die Verbindung wieder da ist.

**Eine Datei lässt sich nicht senden.**
- Größer als 50 MB — die App sagt es dir. Wähle Videos über **Foto oder Video**: Sie werden komprimiert.
- „Video konnte nicht geladen werden“ — liegt der Clip in iCloud, hat das Telefon vielleicht nur eine verkleinerte Kopie. Öffne das Video in der Fotos-App, warte, bis es vollständig geladen ist, und versuch es noch einmal. Wiederholt sich der Fehler, sag uns Bescheid (siehe „Ein Problem melden“ unten).
- „Video konnte nicht komprimiert werden“ — versuch einen kürzeren Clip oder sende ihn über **Datei**, wenn er kleiner als 50 MB ist.

**„Datei konnte nicht gespeichert werden: Speicher voll“.**
Empfangene Dateien belegen auf dem Telefon Platz im Rahmen des Nevod-Kontingents. Erhöhe es: **Profil → Speicher → Kontingent** — oder lösche Chats, die du nicht brauchst (in der Chatliste nach links wischen → **Löschen**).

## KI-Assistenten

**Der Bot schreibt, dass ein Schlüssel nötig ist, oder der Schlüssel wird nicht angenommen.**
Prüfe, ob der Schlüssel vollständig kopiert und auf der Website des Anbieters nicht widerrufen wurde und ob dein Konto beim Anbieter Guthaben hat oder das kostenlose Limit noch nicht aufgebraucht ist. Den Schlüssel kannst du im Chat mit dem Bot wechseln — **Ändern**. Mehr unter [Bots und KI-Assistenten](../bots/).

## Ein Problem melden

**Profil → Diagnose** — beschreibe, was passiert ist und ungefähr wann (zum Beispiel „2 von 3 Fotos sind nicht angekommen, gegen 21 Uhr“), und tippe auf **An die Entwickler senden**. Mit deiner Beschreibung geht das technische Protokoll der App mit: Es liegt nur auf deinem Telefon und enthält keine Nachrichtentexte. Das Protokoll geht per E-Mail an support@nevod.network oder, wenn auf dem Telefon kein E-Mail-Konto eingerichtet ist, an den Administrator deines Nodes in Nevod; die Antwort kommt im Chat mit ihm.

Eine Person oder eine Nachricht melden — siehe [Sicherheit](../security/), „Blockieren und melden“.
