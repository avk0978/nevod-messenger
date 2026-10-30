# Chiamate tramite il proprio nodo

Come Nevod collega le chiamate, quando un nodo ha bisogno di un proprio relay per le chiamate (TURN) e come installarlo sullo stesso server. Se stai iniziando, puoi saltare questa sezione: un nodo collegato alla rete ottiene un relay dai nodi del progetto.

## Come si collega una chiamata

Audio e video viaggiano **direttamente tra i telefoni**, e il nodo li aiuta solo ad accordarsi sul collegamento. Ma il collegamento diretto non sempre riesce: gli operatori mobili e molti router nascondono i telefoni dietro indirizzi condivisi (NAT), e due telefoni così non riescono a raggiungersi. Allora la chiamata passa attraverso un **relay (TURN)**, un server che inoltra i pacchetti tra i telefoni.

Una chiamata è cifrata da telefono a telefono (DTLS-SRTP). Il relay vede solo pacchetti cifrati, gli indirizzi dei telefoni, l'ora e il volume della chiamata: non può sentire né vedere la conversazione.

## Ti serve un tuo relay?

**Senza un relay proprio**, un nodo [collegato alla rete](../node-network/) chiede, per ogni utente che accede, l'accesso al relay di uno dei nodi della rete che ne hanno uno, scelto a caso. Le chiamate funzionano e non c'è nulla da configurare. Un nodo non collegato alla rete non ottiene un relay: le chiamate tra telefoni dietro NAT potrebbero non collegarsi per i suoi utenti.

**Un relay proprio** conviene se:

- vuoi che le chiamate dei tuoi utenti non dipendano dai nodi del progetto;
- i tuoi utenti sono lontani dai server del progetto e le chiamate attraverso di essi hanno ritardo;
- hai molti utenti e molte chiamate.

Cosa tenere presente:

- **il traffico.** Tutta la chiamata passa dal relay: voce, circa 100 kbit/s per direzione; video, 1–2 Mbit/s. La maggior parte dei VPS include diversi terabyte di traffico al mese: per un nodo con decine di utenti è più che sufficiente;
- **il tuo relay aiuterà anche gli altri nodi della rete.** Il nodo comunica alla rete di avere un relay, e i nodi senza uno proprio lo daranno a caso ai loro utenti. La configurazione qui sotto ha dei limiti perché questo non si mangi tutta la banda del server.

## Installare coturn

Installiamo coturn, il relay più diffuso, direttamente sul server del nodo. Tutti i comandi si eseguono sul server.

**1. Installa coturn e crea un segreto:**

```
apt install -y coturn
openssl rand -hex 32
```

Salva l'output del secondo comando: è il segreto condiviso tra relay e nodo.

**2. Scopri l'indirizzo IP esterno del server:**

```
curl -4 ifconfig.me
```

**3. Scrivi la configurazione.** Apri il file:

```
nano /etc/turnserver.conf
```

cancella tutto quello che contiene e incolla quanto segue, con il tuo indirizzo IP e il tuo segreto:

```
listening-port=3478
external-ip=IP-DEL-SERVER
realm=nevod
use-auth-secret
static-auth-secret=SEGRETO
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

Salva: **Ctrl+O**, **Invio**, **Ctrl+X**.

Le righe `denied-peer-ip` vietano al relay di inoltrare qualsiasi cosa verso indirizzi interni, compreso l'interno di Docker su questo stesso server. Non cancellarle. `total-quota`, `user-quota` e `max-bps` limitano il numero di collegamenti contemporanei e la velocità di un collegamento (4 Mbit/s).

**4. Avvia coturn:**

```
systemctl enable --now coturn
systemctl status coturn
```

L'output deve dire `active (running)`. Se coturn non si avvia, apri `/etc/default/coturn` e togli il commento dalla riga `TURNSERVER_ENABLED=1`: alcune versioni del pacchetto lo richiedono.

**5. Apri le porte:**

```
ufw allow 3478/tcp
ufw allow 3478/udp
ufw allow 49152:65535/udp
```

E le stesse porte nel firewall del provider, se c'è.

**6. Passa il segreto al nodo.** Nella cartella `/opt/nevod/installer/docker`:

```
nano .env
```

scrivi lo stesso segreto nella riga `TURN_SECRET=` e applica:

```
docker compose up -d
```

## Verifica

- **Diagnostica → Verifica → Dipendenze e configurazione**: non devono esserci avvisi su TURN.
- Il nodo dà ai telefoni l'indirizzo del relay `turn:tuo-dominio:3478`: il dominio deve puntare a questo server (lo fa già, se il nodo funziona).
- Chiama da un telefono sulla rete cellulare un telefono sul Wi-Fi. Se la chiamata si collega e vi sentite entrambi, il relay funziona. Il log di coturn: `journalctl -u coturn -n 50`.

> Il relay funziona via UDP e TCP sulla porta 3478 senza cifrare il canale verso il relay (la chiamata in sé è sempre cifrata). In alcune reti aziendali queste porte sono chiuse: allora le chiamate da quelle reti non passeranno dal relay.
