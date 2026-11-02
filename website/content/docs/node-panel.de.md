# Ersteinrichtung im Admin-Panel

Der Node läuft — jetzt gibst du ihm einen Namen, entscheidest, wen du zulässt, und registrierst dich selbst darauf. All das geschieht im Admin-Panel unter `https://node.example.org/nevod-admin` (wie du es öffnest — Schritt 9 der [Installation](../node-install/)).

Die Sprache des Panels wird in seiner Kopfzeile umgeschaltet. Eine ausführliche Beschreibung jeder Seite und Einstellung — siehe [Das Admin-Panel: alle Seiten und Einstellungen](../node-admin/).

## Was wo im Panel ist

| Seite | Wofür |
|---|---|
| **Übersicht** | Die auf dem Node registrierten Zellen (Nutzer). |
| **Einstellungen** | Name des Nodes, Zulassungsmodus, Sichtbarkeit. |
| **Beitrittsanfragen** | Anfragen von Nutzern, wenn der Node im Freigabemodus läuft. |
| **Posteingang** | Nachrichten von Nutzern an den Administrator des Nodes — Meldungen, Fragen. Du kannst direkt von hier antworten. |
| **Einladungen** | Einladungscodes für Nutzer. |
| **Nodes** | Anschluss an das Nevod-Netz und die anderen Nodes, die dein Node kennt. |
| **Veröffentlichung**, **KI-Bots** | Die Bots und Kanäle, die der Node seinen Nutzern zeigt. |
| **Sicherheit** | Zusätzliche Administratorkonten. |
| **Diagnose** | Selbsttest des Nodes und sein Protokoll. |

## 1. Gib dem Node einen Namen

**Einstellungen → Node-Name** → gib einen Namen ein, zum Beispiel „Familie Schmidt“ oder „Schule Nr. 5“ → **Speichern**.

Den Namen sehen Nutzer in der App. Andere Nodes des Netzes erfahren den neuen Namen nach einem Neustart des Nodes (siehe unten). Namen, die den Node als Projekt-Node ausgeben, sind nicht erlaubt: mit den Wörtern Nevod, admin, support, official und Ähnlichem.

## 2. Entscheide, wen du zulässt

**Einstellungen → Zulassungsmodus für Zellen.** Ein neuer Node arbeitet standardmäßig **auf Einladung**: Registrieren kann man sich nur mit einem Code, den du ausgegeben hast. Meist ist das genau richtig. In der App, unter **Netzwerk erkunden**, ist ein Node im Einladungs- oder Freigabemodus mit einem Schloss 🔒 markiert — so sehen Menschen vorher, dass sie sich nicht einfach registrieren können.

| Modus im Panel | Wer sich registrieren kann | Wer Einladungscodes erstellt |
|---|---|---|
| `delegated` — nur mit Einladungscode (Standard) | Nur mit Einladungscode. Ohne Code nimmt der Node keine Registrierung an. | Du im Panel, außerdem Nutzer, denen du das Recht **Darf einladen** gegeben hast. |
| `admin` — Anfrage + deine Freigabe | Mit Code — sofort. Ohne Code sendet die App selbst eine Anfrage und zeigt „Warten auf Freigabe“; du gibst sie auf der Seite **Beitrittsanfragen** frei oder lehnst sie ab. | Nur du, im Panel. |
| `open` — ohne Code | Jeder, der die Adresse des Nodes kennt. Passt zu einer offenen Community; bedenke, dass du Registrierungen und vergebene Namen später von Hand aufräumen musst. | Kein Code nötig. |

Der Modus gilt sofort.

## 3. Registriere dich auf deinem Node

1. Im Panel: **Einladungen** → wähle die Gültigkeit (1 Stunde, 24 Stunden oder 7 Tage) → **+ Code erstellen**. Ein QR-Code und ein kurzer Code wie `ABCD-EFGH` erscheinen.
2. Installiere Nevod aus dem App Store auf deinem Telefon.
3. Scanne den QR-Code mit der normalen Kamera des Telefons. Es ist ein Link: Die Einladungsseite öffnet sich — tippe dort auf **In Nevod öffnen**. Die App öffnet sich mit bereits ausgefüllter Adresse deines Nodes und Code.
4. Gib deinen Namen ein und tippe auf **Los geht's**.

Ist Scannen unpraktisch, tippe im Panel auf **Link kopieren** und schick ihn dir selbst. Falls „In Nevod öffnen“ nicht funktioniert hat: Tippe in der App auf **Chatten beginnen**, gib deinen Namen ein, tippe auf **Hast du einen Einladungscode?** und füge den Link in das Code-Feld ein. Der kurze Code statt des Links funktioniert nur, wenn in der App schon dein Node eingestellt ist.

> Ist Nevod auf diesem Telefon schon auf einem anderen Node registriert (zum Beispiel auf Nevod Open), verschiebt dich die Einladung nicht von selbst auf deinen Node — die App warnt, dass du zuerst deine Identität zurücksetzen musst: **Profil → Identität zurücksetzen…**. Das Zurücksetzen löscht dauerhaft deine Identität, deine Kontakte, die Nachrichten auf dem Telefon und deine Registrierung auf dem bisherigen Node. Öffne danach den Einladungslink noch einmal.

Jeder Code gilt einmal. Erstelle für jede Person einen eigenen — mehr unter [Leute einladen](../node-invite/).

## 4. Entscheide, ob der Node im Netz sichtbar ist

**Einstellungen → Sichtbarkeit in „Netzwerk erkunden“**:

- `closed` (Standard) — der Node wird Nutzern anderer Nodes in „Netzwerk erkunden“ nicht angezeigt. Passt für Familie, Organisation, jede geschlossene Gruppe.
- `open` — der Node erscheint in „Netzwerk erkunden“, und Nutzer anderer Nodes können ihn finden. Passt für eine offene Community. Der Node ist sichtbar, solange er mit dem Netz verbunden ist, und nur für Leute, die schon auf irgendeinem Node registriert sind: Vor der Registrierung zeigt die App nur die Nodes des Projekts.

Diese Wahl öffnet nicht die Registrierung: Wen du zulässt, entscheidet weiterhin der Zulassungsmodus für Zellen (Schritt 2). Den goldenen Ring eines geprüften Nodes in „Netzwerk erkunden“ haben derzeit nur Nodes des Nevod-Projekts.

Diese Einstellung gilt, wie der Name des Nodes für andere Nodes, nach einem Neustart des Nodes. Auf dem Server, im Ordner `/opt/nevod/installer/docker`:

```
docker compose restart nevod_node
```

## 5. Prüfe den Node

**Diagnose → Prüfen.** In wenigen Sekunden zeigt der Node, ob alles in Ordnung ist: ob sein Code aktuell ist, ob Einstellungen und Datenbank übereinstimmen, ob es Konfigurationsprobleme gibt, ob der Node von außen erreichbar ist.

Die Erreichbarkeit von außen prüft der Node über andere Nodes des Netzes. Solange dein Node mit niemandem verbunden ist, zeigt diese Zeile „Keine bekannten Peers“ — das ist zu erwarten. Der Anschluss ans Netz ist der nächste Schritt, und er ist wichtig: Ohne ihn bekommen Telefone keine Mitteilungen, solange die App geschlossen ist. Siehe [Anschluss an das Nevod-Netz](../node-network/).

## 6. Optional: weitere Administratoren

**Sicherheit → Hinzufügen / Passwort ändern** — jeder Administrator bekommt eigenen Login und eigenes Passwort, und du kannst sie widerrufen, ohne das Hauptpasswort aus `.env` zu ändern. Das Hauptpasswort bleibt als Notzugang, falls die anderen verloren gehen.
