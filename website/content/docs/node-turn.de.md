# Anrufe über den eigenen Node

Wie Nevod Anrufe verbindet, wann ein Node ein eigenes Anruf-Relay (TURN) braucht und wie du es auf demselben Server einrichtest. Wenn du gerade erst anfängst, kannst du diesen Abschnitt überspringen: Ein mit dem Netz verbundener Node bekommt ein Relay von den Projekt-Nodes.

## Wie ein Anruf verbunden wird

Ton und Video gehen **direkt zwischen den Telefonen**, und der Node hilft ihnen nur, sich auf die Verbindung zu einigen. Aber direkt klappt es nicht immer: Mobilfunkanbieter und viele Router verstecken Telefone hinter gemeinsamen Adressen (NAT), und zwei solche Telefone erreichen einander nicht. Dann läuft der Anruf über ein **Relay (TURN)** — einen Server, der Pakete zwischen den Telefonen weiterleitet.

Ein Anruf ist von Telefon zu Telefon verschlüsselt (DTLS-SRTP). Das Relay sieht nur verschlüsselte Pakete, die Adressen der Telefone sowie Zeit und Umfang des Anrufs — das Gespräch hören oder sehen kann es nicht.

## Brauchst du ein eigenes Relay

**Ohne eigenes Relay** fordert ein [mit dem Netz verbundener](../node-network/) Node für jeden Nutzer, der sich anmeldet, Zugang zum Relay eines der Netz-Nodes an, die eines haben — zufällig ausgewählt. Anrufe funktionieren, und es gibt nichts einzurichten. Ein nicht verbundener Node bekommt kein Relay: Anrufe zwischen Telefonen hinter NAT kommen bei seinen Nutzern womöglich nicht zustande.

**Ein eigenes Relay** lohnt sich, wenn:

- die Anrufe deiner Nutzer nicht von den Projekt-Nodes abhängen sollen;
- deine Nutzer weit von den Projekt-Servern entfernt sind und Anrufe darüber verzögert sind;
- du viele Nutzer und viele Anrufe hast.

Was du bedenken solltest:

- **Datenverkehr.** Über das Relay läuft der ganze Anruf: Sprache — etwa 100 kbit/s pro Richtung, Video — 1–2 Mbit/s. Die meisten VPS enthalten mehrere Terabyte Datenverkehr im Monat — für einen Node mit Dutzenden Nutzern mehr als genug;
- **dein Relay hilft auch anderen Nodes des Netzes.** Der Node teilt dem Netz mit, dass er ein Relay hat, und Nodes ohne eigenes geben es zufällig an ihre Nutzer weiter. Die Konfiguration unten hat Grenzen, damit das nicht die ganze Bandbreite des Servers frisst.

## coturn installieren

Wir installieren coturn — das verbreitetste Relay — direkt auf dem Server des Nodes. Alle Befehle werden auf dem Server ausgeführt.

**1. Installiere coturn und erzeuge ein Geheimnis:**

```
apt install -y coturn
openssl rand -hex 32
```

Speichere die Ausgabe des zweiten Befehls — das ist das gemeinsame Geheimnis von Relay und Node.

**2. Ermittle die externe IP-Adresse des Servers:**

```
curl -4 ifconfig.me
```

**3. Schreib die Konfiguration.** Öffne die Datei:

```
nano /etc/turnserver.conf
```

lösche alles darin und füge Folgendes ein, mit deiner IP-Adresse und deinem Geheimnis:

```
listening-port=3478
external-ip=IP-ADRESSE-DES-SERVERS
realm=nevod
use-auth-secret
static-auth-secret=GEHEIMNIS
min-port=49152
max-port=65535
no-tls
no-dtls
fingerprint
no-loopback-peers
no-multicast-peers
denied-peer-ip=0.0.0.0-0.255.255.255
denied-peer-ip=10.0.0.0-10.255.255.255
denied-peer-ip=100.64.0.0-100.127.255.255
denied-peer-ip=127.0.0.0-127.255.255.255
denied-peer-ip=169.254.0.0-169.254.255.255
denied-peer-ip=172.16.0.0-172.31.255.255
denied-peer-ip=192.168.0.0-192.168.255.255
total-quota=200
user-quota=10
max-bps=4000000
```

Speichern: **Ctrl+O**, **Enter**, **Ctrl+X**.

Die Zeilen `denied-peer-ip` verbieten dem Relay, irgendetwas an interne Adressen weiterzuleiten — auch nicht in Docker auf demselben Server. Lösch sie nicht. `total-quota`, `user-quota` und `max-bps` begrenzen die Zahl gleichzeitiger Verbindungen und die Geschwindigkeit einer Verbindung (4 Mbit/s).

**4. Starte coturn:**

```
systemctl enable --now coturn
systemctl status coturn
```

Die Ausgabe sollte `active (running)` zeigen. Startet coturn nicht, öffne `/etc/default/coturn` und entferne das Kommentarzeichen vor `TURNSERVER_ENABLED=1` — manche Paketversionen brauchen das.

**5. Öffne die Ports:**

```
ufw allow 3478/tcp
ufw allow 3478/udp
ufw allow 49152:65535/udp
```

Und dieselben Ports in der Firewall des Anbieters, falls es eine gibt.

**6. Gib dem Node das Geheimnis.** Im Ordner `/opt/nevod/installer/docker`:

```
nano .env
```

trag dasselbe Geheimnis in die Zeile `TURN_SECRET=` ein und übernimm es:

```
docker compose up -d
```

## Prüfen

- **Diagnose → Prüfen → Abhängigkeiten und Konfiguration** — es sollte keine Warnungen zu TURN geben.
- Der Node gibt Telefonen die Relay-Adresse `turn:deine-domain:3478` — die Domain muss auf diesen Server zeigen (das tut sie ohnehin, wenn der Node funktioniert).
- Ruf von einem Telefon im Mobilfunk ein Telefon im WLAN an. Kommt der Anruf zustande und sind beide zu hören, funktioniert das Relay. Das coturn-Protokoll: `journalctl -u coturn -n 50`.

> Das Relay arbeitet über UDP und TCP auf Port 3478 ohne Verschlüsselung des Kanals zum Relay (der Anruf selbst ist immer verschlüsselt). In manchen Firmennetzen sind solche Ports gesperrt — dann gehen Anrufe aus diesen Netzen nicht über das Relay.
