# Wartung

Den Node aktualisieren, Backups, Umzug auf einen anderen Server, Protokolle und die übliche Serverpflege. Alle `docker compose`-Befehle werden auf dem Server im Ordner `/opt/nevod/installer/docker` ausgeführt:

```
cd /opt/nevod/installer/docker
```

## Den Node aktualisieren

Neue Versionen des Nodes erscheinen im [Quellcode auf GitHub](https://github.com/avk0978/nevod-messenger) — um davon zu erfahren, klick dort auf **Watch**. Aktualisieren:

```
cd /opt/nevod
git pull
cd installer/docker
docker compose up -d --build
```

Der Node startet mit der neuen Version neu; Nutzer verbinden sich von selbst wieder, und die Daten im Ordner `data/` bleiben erhalten. Sieh nach dem Update im Panel unter **Diagnose** → **Prüfen** nach.

Nach einigen Updates belegen alte Images Speicherplatz — du kannst sie löschen:

```
docker image prune -f
```

## Backup

Das Wertvollste auf dem Server ist der Ordner `data/` und darin die Datei `node.json`: Das ist die Identität des Nodes. Verlierst du sie, muss der Node neu angelegt werden, mit neuer Kennung, und alle Nutzer müssen sich erneut registrieren. Mach mindestens einmal pro Woche und nach jeder Änderung der Einstellungen ein Backup.

**Backup erstellen** (der Node hält für ein paar Sekunden an):

```
docker compose stop nevod_node
tar czf ~/nevod-backup-$(date +%F).tar.gz data .env
docker compose start nevod_node
```

**Herunterladen.** Auf deinem Computer:

```
scp root@node.example.org:~/nevod-backup-*.tar.gz .
```

Bewahre das Backup nicht auf demselben Server auf: Passiert dem Server etwas, ist das Backup mit weg.

> Das Backup enthält die Schlüssel des Nodes und das Panel-Passwort aus `.env`. Bewahre es so sorgfältig auf wie ein Passwort: verschlüsselte Festplatte, Passwortmanager mit Anhängen oder ein ähnlicher Ort.

## Wiederherstellen und auf einen anderen Server umziehen

So ziehst du einen Node auch auf einen neuen Server um. Die Domain bleibt dieselbe — nur der Server, auf den sie zeigt, ändert sich.

1. Führe auf dem neuen Server die Schritte 1 und 3–6 der [Installation](../node-install/) aus (Server, Docker, Firewall, Nevod herunterladen) — **ohne** die Schritte 7–8.
2. Kopiere das Backup auf den neuen Server und entpacke es im Ordner des Pakets:

   ```
   scp nevod-backup-DATUM.tar.gz root@NEUE-IP:/opt/nevod/installer/docker/
   ```

   und auf dem neuen Server:

   ```
   cd /opt/nevod/installer/docker
   tar xzf nevod-backup-DATUM.tar.gz
   ```

3. **Stoppe den Node auf dem alten Server** (`docker compose down`) — zwei Nodes mit derselben Identität dürfen nicht gleichzeitig laufen.
4. Ändere den A-Eintrag der Domain auf die IP des neuen Servers und warte, bis `ping node.example.org` die neue Adresse zeigt.
5. Starte den Node auf dem neuen Server: `docker compose up -d --build`. Caddy holt das Zertifikat von selbst neu.

Nutzer müssen nichts tun: Die App verbindet sich mit derselben Domain und findet dort denselben Node.

> Die **Domain** des Nodes lässt sich nicht so einfach ändern: Die Adresse für Verbindungen mit anderen Nodes wird beim ersten Start in die Identität des Nodes geschrieben. Wähle eine Domain, die du nicht ändern musst.

## Protokolle

```
docker compose logs --tail 100 nevod_node
docker compose logs -f nevod_node
```

Der erste Befehl zeigt die letzten 100 Zeilen, der zweite das Protokoll in Echtzeit (beenden mit **Ctrl+C**). Das Caddy-Protokoll — `docker compose logs caddy`. Die letzten Einträge des Nodes siehst du auch im Panel: **Diagnose → Protokolle**.

Protokolle sind in der Größe begrenzt: 3 Dateien zu je 10 MB pro Container, alte Einträge werden von selbst überschrieben. Nachrichtentexte gelangen nie ins Protokoll.

## Neustart, Stopp, Passwort

| Was du brauchst | Befehl |
|---|---|
| Den Node neu starten (zum Beispiel nach Änderung von Name oder Sichtbarkeit im Panel) | `docker compose restart nevod_node` |
| Alles stoppen | `docker compose down` |
| Wieder starten | `docker compose up -d` |
| Sehen, was läuft | `docker compose ps` |

**Das Hauptpasswort des Panels ändern:** Trag das neue in die Zeile `NEVOD_ADMIN_PASSWORD` in `.env` ein (`nano .env`) und führe `docker compose up -d` aus — der Node startet mit dem neuen Passwort neu. Persönliche Konten von der Seite „Sicherheit“ bleiben davon unberührt.

## Serverpflege

- **System-Updates** — einmal im Monat oder öfter:

  ```
  apt update && apt upgrade -y
  reboot
  ```

  Nach dem Neustart starten Node, Caddy und coturn (falls installiert) von selbst.
- **Speicherplatz** — `df -h /`. Wird der Platz knapp, lösche alte Images (`docker image prune -f`) und alte Backups auf dem Server.
- **Das HTTPS-Zertifikat** verlängert Caddy von selbst. Du musst nichts tun, aber Port 80 muss offen bleiben.
- **Node nicht erreichbar?** Am einfachsten erfährst du es sofort, wenn du einen kostenlosen Uptime-Monitor auf `https://node.example.org` ansetzt: Er schickt eine E-Mail, wenn der Node nicht mehr antwortet.

## Wenn der Node lange ausgefallen war

Nachrichten für Nutzer, die nicht online waren, bewahrt der Node bis zu 72 Stunden auf und löscht sie dann. Einen Node, der sich 72 Stunden nicht gemeldet hat, entfernen die anderen Nodes des Netzes aus ihren Listen — nach dem Start kommt er von selbst wieder hinein, während die Listen ausgetauscht werden.
