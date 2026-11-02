# Bots und KI-Assistenten

Wo du Bots findest, wie du KI-Assistenten mit deinem eigenen Schlüssel nutzt, was das kostet und wer deine Unterhaltung mit einem Bot sieht.

## Was ein Bot in Nevod ist

Ein Bot ist ein Mitglied des Netzes wie ein Mensch, nur antwortet ein Programm. Es gibt einfache Bots — zum Beispiel wiederholt **Echo** auf Nevod Open deine Nachrichten, damit kannst du bequem prüfen, ob die Verbindung funktioniert — und **KI-Assistenten**, die mit Claude, ChatGPT oder Gemini antworten.

## Wo du Bots findest

- **Nodes** → tippe auf einen Node — seine Seite zeigt die Bots und Seiten, die der Node seinen Nutzern anbietet. Tippe auf einen Bot, um einen Chat mit ihm zu öffnen. Bist du noch nicht registriert, fragt die App nach einem Namen oder Spitznamen und registriert dich auf diesem Node.
- **Kontakte → Auf diesem Node** — die Bots deines Heim-Nodes.

Auf Nevod Open laufen derzeit **AI Assistant**, ein Assistent für alles, und **Tolmach**, ein Übersetzer.

Bots auf privaten Nodes richtet der Administrator des Nodes ein: Welche Bots du hast, hängt von deinem Node ab.

## KI-Assistenten mit deinem Schlüssel

KI-Assistenten in Nevod haben keinen eigenen bezahlten Zugang zu Claude, ChatGPT oder Gemini. Ein Bot antwortet mit **deinem eigenen Schlüssel** — so wählst du den Anbieter selbst und bezahlst ihn direkt, und weder der Node noch die Nevod-Entwickler sind an dieser Zahlung beteiligt.

**So verbindest du einen Schlüssel:**

1. Öffne einen Chat mit einem KI-Assistenten. Es erscheint „Dieser Bot antwortet mit deinem eigenen KI-Schlüssel.“ → **KI-Schlüssel hinzufügen**.
2. Arbeitet der Bot mit mehreren Anbietern, wähle den **Anbieter**: Claude (Anthropic), ChatGPT (OpenAI) oder Gemini (Google).
3. Hol dir einen Schlüssel auf der Website des Anbieters — der Link **Wo bekomme ich einen Schlüssel?** führt direkt zur richtigen Seite. Kopiere den Schlüssel und füge ihn in das Feld **API-Schlüssel einfügen** ein.
4. Lies, wohin deine Nachrichten gehen, schalte **Ich stimme zu** ein und tippe auf **Prüfen und speichern**. Die App prüft, ob der Schlüssel funktioniert.

Fertig — du kannst dem Bot schreiben. Anbieter oder Schlüssel wechseln — die Taste **Ändern** im Chat mit dem Bot. Ein Schlüssel pro Anbieter gilt für alle Bots: Ist schon ein Schlüssel gespeichert, bietet die App **Gespeicherten Schlüssel verwenden** an.

**Alle gespeicherten Schlüssel** — **Profil → Sicherheit → KI-Schlüssel**. Dort ist auch **Schlüssel löschen**.

## Was es kostet

Der Anbieter berechnet jede Anfrage — zu seinen eigenen Tarifen, vom Konto, mit dem dein Schlüssel verknüpft ist. Für Unterhaltungen mit einem Assistenten sind das meist kleine Beträge; manche Anbieter haben eine kostenlose Stufe mit Grenzen. Tarife und Grenzen findest du auf der Website des Anbieters; dort kannst du auch ein Ausgabenlimit für den Schlüssel festlegen — so gibst du nie mehr aus, als du beschlossen hast.

## Wer deine Unterhaltung mit einem KI-Bot sieht

Hier liegt der Unterschied zu normalen Unterhaltungen.

- **Dein Schlüssel** wird nur auf deinem Telefon gespeichert. Mit jeder Nachricht geht er verschlüsselt an den Bot; der Bot nutzt ihn für eine Anfrage beim Anbieter und speichert ihn nicht.
- **Deine Nachrichten an den Bot** entschlüsselt der Node, auf dem der Bot läuft, und gibt sie an den gewählten Anbieter weiter — sonst könnte die KI nicht antworten. **Der Anbieter (Anthropic, OpenAI oder Google) sieht deine Unterhaltung mit dem Bot** und verarbeitet sie nach seinen eigenen Regeln.
- Zwischen Menschen ändert sich nichts: Unterhaltungen zwischen Menschen sehen weder Nodes noch KI-Anbieter.

Schick KI-Bots deshalb nichts, was du dem Anbieter nicht zeigen willst: Passwörter, Kartennummern, persönliche Daten anderer. Mehr in der [Datenschutzerklärung](../../privacy/), Abschnitt 5.

> KI-Antworten können ungenau sein. Prüfe Wichtiges nach — besonders Übersetzungen von Dokumenten sowie medizinische, rechtliche und finanzielle Fragen.
