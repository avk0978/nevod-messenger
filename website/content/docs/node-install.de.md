# Installation Schritt für Schritt

Wie du einen Nevod-Node von Grund auf auf einem gemieteten Server einrichtest: vom Kauf des Servers bis zur ersten Anmeldung im Admin-Panel. Das Beispiel nutzt einen Server mit Ubuntu 26.04 und die Domain `node.example.org`; setz überall deine eigene ein.

Alle Befehle unten werden im Terminal des Servers eingegeben; du kannst sie vollständig kopieren. Was ein Node ist und was er speichert — siehe [Wie ein Node funktioniert](../node-how/).

## 1. Miete einen Server

Jeder VPS bei jedem Anbieter genügt: 1 CPU, 1 GB Arbeitsspeicher, 10 GB Festplatte, **Ubuntu 24.04** oder **26.04**. Bei der Bestellung gibt dir der Anbieter die **IP-Adresse** des Servers und das Passwort des Benutzers `root` (oder bittet dich, einen SSH-Schlüssel hochzuladen).

Hat der Anbieter eine eigene Netzwerk-Firewall im Kundenpanel (zum Beispiel Firewalls bei Hetzner, Security Groups bei anderen), öffne dort die eingehenden Ports **22, 80, 443 und 8765** (TCP).

## 2. Lass die Domain auf den Server zeigen

Der Node braucht eine eigene Domain oder Subdomain, zum Beispiel `node.example.org`. Ohne geht es aus zwei Gründen nicht:

- **Telefone verbinden sich mit dem Node über `https://Domain/nevod-ws`.** Das HTTPS-Zertifikat, dem ein iPhone ohne jede Einstellung vertraut, holt Caddy bei Let's Encrypt für einen Domainnamen.
- **Die Adresse des Nodes ist überall gespeichert:** auf den Telefonen der Nutzer, in ihren Kontaktkarten, bei anderen Nodes im Netz. Ziehst du auf einen anderen Server um oder ändert der Provider die IP-Adresse, korrigierst du einen DNS-Eintrag, und die Nutzer merken nichts. Mit einer nackten IP-Adresse wären nach einem Umzug alle getrennt, und du müsstest die Einladungen neu verschicken.

Hast du noch keine Domain, kannst du sie bei jedem Registrar kaufen (Cloudflare, Namecheap, Porkbun, Gandi und andere) — meist ein paar Dollar oder Euro im Jahr. Für den Node genügt eine Subdomain, die Domain selbst kannst du auch für anderes nutzen.

Lege in der Verwaltung deiner Domain einen **A-Eintrag** an: Name — zum Beispiel `node` (ergibt `node.example.org`), Wert — die IP-Adresse des Servers.

Warte ein paar Minuten und prüfe von einem beliebigen Computer:

```
ping node.example.org
```

Die Antwort muss die IP-Adresse deines Servers zeigen. Solange das nicht so ist, hat es keinen Sinn weiterzumachen: Ein HTTPS-Zertifikat wird nur für eine Domain ausgestellt, die schon auf den Server zeigt.

> Wird die Domain von Cloudflare bedient, schalte für diesen Eintrag das Proxying aus (graue Wolke, „DNS only“). Sonst verbinden sich Telefone und andere Nodes mit Cloudflare statt mit deinem Server.

## 3. Verbinde dich mit dem Server

Öffne auf deinem Computer ein Terminal (unter Windows PowerShell, auf dem Mac „Terminal“) und gib ein:

```
ssh root@node.example.org
```

Antworte bei der ersten Verbindung mit `yes` und gib das Passwort vom Anbieter ein.

## 4. Installiere Docker und git

```
apt update && apt upgrade -y
apt install -y git
curl -fsSL https://get.docker.com | sh
```

Der letzte Befehl ist das offizielle Docker-Installationsskript. Prüfe, ob alles da ist:

```
docker compose version
```

Es sollte eine Zeile wie `Docker Compose version v…` erscheinen.

> Erscheint nach dem Update (auf dem Bildschirm oder bei der nächsten Anmeldung) `*** System restart required ***`, starte den Server mit `reboot` neu, verbinde dich nach einer Minute wieder (Schritt 3) und mach weiter.

## 5. Schalte die Firewall ein

```
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8765/tcp
ufw enable
```

Beantworte die Frage mit `y`. Die Ports 80 und 443 sind für HTTPS (Telefone und Panel), 8765 für die Verbindung mit anderen Nodes.

> Docker öffnet die Ports seiner Container selbst, an `ufw` vorbei. Deshalb ist das Admin-Panel (Port 8766) in unserem Paket nur für den Server selbst freigegeben — ändere das nicht in `docker-compose.yml`.

## 6. Lade Nevod herunter

> Alle folgenden Befehle gibst du auf dem Server ein: Links in der Eingabezeile muss `root@…` stehen. Steht dort `PS C:\…>` oder der Name deines Computers, ist die Verbindung zum Server geschlossen — verbinde dich neu (Schritt 3).

```
git clone https://github.com/avk0978/nevod-messenger.git /opt/nevod
cd /opt/nevod/installer/docker
```

## 7. Fülle die Einstellungen aus

Erstelle die Einstellungsdatei aus der Vorlage:

```
cp .env.example .env
```

Denk dir ein Passwort für das Admin-Panel aus. Am einfachsten erzeugst du ein langes zufälliges:

```
openssl rand -base64 24
```

Kopiere das Ergebnis und speichere es an einem sicheren Ort — zum Beispiel in einem Passwortmanager (Bitwarden, KeePass, „Passwörter“ auf iPhone und Mac). Öffne jetzt die Einstellungsdatei:

```
nano .env
```

Ändere zwei Zeilen:

```
NEVOD_DOMAIN=node.example.org
NEVOD_ADMIN_PASSWORD=hier-das-erzeugte-passwort
```

Den Rest lässt du, wie er ist. Speichere die Datei: **Ctrl+O**, dann **Enter**, beenden mit **Ctrl+X**.

| Einstellung | Bedeutung |
|---|---|
| `NEVOD_DOMAIN` | Die Domain des Nodes. Telefone verbinden sich mit `https://domain/nevod-ws`, andere Nodes mit `domain:8765`. |
| `NEVOD_ADMIN_PASSWORD` | Das Passwort des Admin-Panels. Ohne es startet der Node nicht. |
| `NEVOD_ADMIN_PUBLIC` | `true` — das Panel öffnet sich im Browser unter `https://domain/nevod-admin`; `false` — das Panel ist für das Internet gesperrt (siehe Schritt 10). |
| `TURN_SECRET` | Nur wenn du ein eigenes Anruf-Relay einrichtest, siehe [Anrufe über den eigenen Node](../node-turn/). Meist leer. |

## 8. Starte den Node

```
docker compose up -d --build
```

Der erste Start dauert ein paar Minuten: Docker baut das Node-Image und lädt Caddy herunter. Wenn der Befehl fertig ist, prüfe:

```
docker compose ps
```

Beide Container — `nevod_node` und `nevod_caddy` — sollten `Up` (oder `running`) sein.

## 9. Prüfe, ob alles funktioniert

Öffne `https://node.example.org` im Browser — die Zeile „Nevod node — https://nevod.network“ sollte erscheinen, und der Browser sollte nicht über das Zertifikat meckern.

Öffne jetzt `https://node.example.org/nevod-admin`. Der Browser fragt nach Benutzername und Passwort: beliebiger Benutzername, und das Passwort, das du in `.env` eingetragen hast. Das Admin-Panel öffnet sich. Was du dort zuerst tun solltest — siehe [Ersteinrichtung im Admin-Panel](../node-panel/).

> Fünf falsche Passwörter hintereinander von einer Adresse sperren das Panel für diese Adresse für 15 Minuten. Wenn das passiert, warte einfach.

## 10. Optional: Sperre das Panel für das Internet

Soll die Adresse des Panels aus dem Internet gar nicht erreichbar sein, ändere in `.env` die Zeile `NEVOD_ADMIN_PUBLIC=true` in `NEVOD_ADMIN_PUBLIC=false` und übernimm sie:

```
docker compose up -d
```

Dann ist das Panel nur über einen SSH-Tunnel erreichbar. Führe auf deinem Computer aus

```
ssh -L 8766:127.0.0.1:8766 root@node.example.org
```

und öffne, solange dieses Fenster offen ist, im Browser `http://localhost:8766/nevod-admin`.

Ist Port 8766 auf deinem Computer schon belegt (zum Beispiel läuft dort ein anderer Nevod-Node), nimm einen anderen: `ssh -L 18766:127.0.0.1:8766 root@node.example.org` und `http://localhost:18766/nevod-admin`. Die erste Zahl ist der Port auf deinem Computer, die zweite der Port des Panels auf dem Server — die bleibt, wie sie ist.

## Wenn etwas nicht stimmt

| Was du siehst | Woran es meist liegt |
|---|---|
| Der Browser meldet ein ungültiges Zertifikat, oder die Seite öffnet sich nicht | Die Domain zeigt noch nicht auf den Server (Schritt 2), oder Port 80/443 ist zu (Schritte 1 und 5). Sieh dir das Caddy-Protokoll an: `docker compose logs caddy`. Ist die Ursache behoben, versucht Caddy es von selbst erneut. |
| `docker compose up` meldet `address already in use` | Auf dem Server läuft schon ein anderer Webserver (oft Apache oder nginx vom Anbieter). Stoppe ihn: `systemctl disable --now apache2` oder `systemctl disable --now nginx`. |
| Fehler `set NEVOD_ADMIN_PASSWORD in .env` oder `set NEVOD_DOMAIN in .env` | Diese Zeile in `.env` ist nicht ausgefüllt (Schritt 7). |
| Tippfehler in der Domain in `.env` (kein Zertifikat, im Caddy-Protokoll `NXDOMAIN`) | Stoppe den Node: `docker compose down`, korrigiere `NEVOD_DOMAIN` in `.env`, lösche den Datenordner: `rm -rf data`, und starte neu: `docker compose up -d`. Lösche `data` nur, solange noch niemand auf dem Node registriert ist — sonst behält der Node die alte Adresse, und du müsstest sie von Hand korrigieren. |
| Das Panel fragt immer wieder nach dem Passwort | Falsches Passwort. Welches eingetragen ist: `grep PASSWORD .env`. |
| Das Panel antwortet „Too many failed logins“ | Der Schutz gegen Passwort-Raten hat gegriffen — warte 15 Minuten. |
| `nevod_node` startet ständig neu | Das Node-Protokoll zeigt den Grund: `docker compose logs --tail 50 nevod_node`. |

Die vollständigen Protokolle beider Container: `docker compose logs`. Alle `docker compose`-Befehle werden im Ordner `/opt/nevod/installer/docker` ausgeführt.
