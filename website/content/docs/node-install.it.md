# Installazione passo per passo

Come installare da zero un nodo Nevod su un server a noleggio: dall'acquisto del server al primo accesso al pannello di amministrazione. L'esempio usa un server con Ubuntu 24.04 e il dominio `node.example.org`; sostituiscilo ovunque con il tuo.

Tutti i comandi qui sotto si digitano nel terminale del server; puoi copiarli per intero. Cos'è un nodo e cosa conserva: in [Come funziona un nodo](../node-how/).

## 1. Noleggia un server

Va bene qualsiasi VPS di qualsiasi provider: 1 CPU, 1 GB di memoria, 10 GB di disco, **Ubuntu 24.04**. Al momento dell'ordine il provider ti dà l'**indirizzo IP** del server e la password dell'utente `root` (oppure ti chiede di caricare una chiave SSH).

Se il provider ha un proprio firewall di rete nel pannello di controllo (per esempio Firewalls su Hetzner, Security groups altrove), apri lì le porte in ingresso **22, 80, 443 e 8765** (TCP).

## 2. Fai puntare il dominio al server

Il nodo ha bisogno di un dominio o sottodominio proprio, per esempio `node.example.org`. Non può farne a meno per due motivi:

- **I telefoni si collegano al nodo all'indirizzo `https://dominio/nevod-ws`.** Caddy ottiene da Let's Encrypt, per un nome di dominio, il certificato HTTPS di cui un iPhone si fida senza alcuna configurazione.
- **L'indirizzo del nodo è salvato ovunque:** nei telefoni degli utenti, nelle loro schede contatto, negli altri nodi della rete. Se ti sposti su un altro server o il provider cambia l'indirizzo IP, basta correggere un record DNS e gli utenti non si accorgono di nulla. Con un semplice indirizzo IP, un trasloco lascerebbe tutti senza collegamento e dovresti inviare di nuovo gli inviti.

Se non hai ancora un dominio, puoi acquistarlo da un qualsiasi registrar (Cloudflare, Namecheap, Porkbun, Gandi e altri): di solito costa pochi dollari o euro all'anno. Per il nodo basta un sottodominio, e il dominio stesso può servirti anche per altro.

Nel pannello di gestione del tuo dominio crea un **record A**: nome — per esempio `node` (diventa `node.example.org`) —, valore: l'indirizzo IP del server.

Aspetta qualche minuto e verifica da un computer qualsiasi:

```
ping node.example.org
```

La risposta deve mostrare l'indirizzo IP del tuo server. Finché non è così, non ha senso andare avanti: un certificato HTTPS viene emesso solo per un dominio che punta già al server.

> Se il dominio è gestito da Cloudflare, disattiva il proxy per questo record (nuvola grigia, «DNS only»). Altrimenti i telefoni e gli altri nodi si collegheranno a Cloudflare invece che al tuo server.

## 3. Collegati al server

Sul tuo computer apri un terminale (su Windows PowerShell, su Mac Terminale) e digita:

```
ssh root@node.example.org
```

Al primo collegamento rispondi `yes` e inserisci la password del provider.

## 4. Installa Docker e git

```
apt update && apt upgrade -y
apt install -y git
curl -fsSL https://get.docker.com | sh
```

L'ultimo comando è l'installatore ufficiale di Docker. Verifica che sia tutto a posto:

```
docker compose version
```

Dovrebbe comparire una riga come `Docker Compose version v2…`.

## 5. Attiva il firewall

```
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8765/tcp
ufw enable
```

Rispondi `y` alla domanda. Le porte 80 e 443 servono per HTTPS (telefoni e pannello), la 8765 per comunicare con gli altri nodi.

> Docker apre da solo le porte dei suoi container, scavalcando `ufw`. Per questo nel nostro kit il pannello di amministrazione (porta 8766) è pubblicato solo per il server stesso: non cambiarlo in `docker-compose.yml`.

## 6. Scarica Nevod

```
git clone https://github.com/avk0978/nevod-messenger.git /opt/nevod
cd /opt/nevod/installer/docker
```

## 7. Compila le impostazioni

Crea il file delle impostazioni dal modello:

```
cp .env.example .env
```

Scegli una password per il pannello di amministrazione. La cosa più comoda è generarne una lunga e casuale:

```
openssl rand -base64 24
```

Copia il risultato e salvalo nel tuo gestore di password. Ora apri il file delle impostazioni:

```
nano .env
```

Modifica due righe:

```
NEVOD_DOMAIN=node.example.org
NEVOD_ADMIN_PASSWORD=qui-la-password-generata
```

Lascia il resto com'è. Salva il file: **Ctrl+O**, poi **Invio**; per uscire **Ctrl+X**.

| Impostazione | Cosa significa |
|---|---|
| `NEVOD_DOMAIN` | Il dominio del nodo. I telefoni si collegano a `https://dominio/nevod-ws`, gli altri nodi a `dominio:8765`. |
| `NEVOD_ADMIN_PASSWORD` | La password del pannello di amministrazione. Senza, il nodo non si avvia. |
| `NEVOD_ADMIN_PUBLIC` | `true`: il pannello si apre nel browser all'indirizzo `https://dominio/nevod-admin`; `false`: il pannello è chiuso a internet (vedi il passo 10). |
| `TURN_SECRET` | Solo se installi un tuo relay per le chiamate; vedi [Chiamate tramite il proprio nodo](../node-turn/). Di solito vuoto. |

## 8. Avvia il nodo

```
docker compose up -d --build
```

Il primo avvio richiede qualche minuto: Docker costruisce l'immagine del nodo e scarica Caddy. Quando il comando termina, verifica:

```
docker compose ps
```

Entrambi i container — `nevod_node` e `nevod_caddy` — devono essere nello stato `Up` (o `running`).

## 9. Verifica che tutto funzioni

Apri `https://node.example.org` nel browser: deve comparire la riga «Nevod node — https://nevod.network», e il browser non deve lamentarsi del certificato.

Ora apri `https://node.example.org/nevod-admin`. Il browser chiede nome utente e password: un nome utente qualsiasi, e la password che hai scritto in `.env`. Si apre il pannello di amministrazione. Cosa fare per prima cosa: in [Prima configurazione nel pannello di amministrazione](../node-panel/).

> Cinque password sbagliate di fila dallo stesso indirizzo bloccano il pannello per quell'indirizzo per 15 minuti. Se succede, aspetta e basta.

## 10. Facoltativo: chiudi il pannello a internet

Se non vuoi che l'indirizzo del pannello si apra da internet, aggiungi a `.env` la riga `NEVOD_ADMIN_PUBLIC=false` e applicala:

```
docker compose up -d
```

Allora il pannello è raggiungibile solo tramite un tunnel SSH. Sul tuo computer esegui

```
ssh -L 8766:127.0.0.1:8766 root@node.example.org
```

e, finché quella finestra resta aperta, apri nel browser `http://localhost:8766/nevod-admin`.

## Se qualcosa non va

| Cosa vedi | Di solito la causa è |
|---|---|
| Il browser dice che il certificato non è valido, o il sito non si apre | Il dominio non punta ancora al server (passo 2), oppure la porta 80/443 è chiusa (passi 1 e 5). Guarda il log di Caddy: `docker compose logs caddy`. Una volta eliminata la causa, Caddy riprova da solo. |
| `docker compose up` dice `address already in use` | Sul server è già attivo un altro server web (spesso Apache o nginx del provider). Fermalo: `systemctl disable --now apache2` oppure `systemctl disable --now nginx`. |
| L'errore `set NEVOD_ADMIN_PASSWORD in .env` o `set NEVOD_DOMAIN in .env` | Quella riga di `.env` non è compilata (passo 7). |
| Il pannello chiede la password in continuazione | Password sbagliata. Per vedere quale è impostata: `grep PASSWORD .env`. |
| Il pannello risponde «Too many failed logins» | È scattata la protezione contro i tentativi di indovinare la password: aspetta 15 minuti. |
| `nevod_node` si riavvia di continuo | Il log del nodo mostra il motivo: `docker compose logs --tail 50 nevod_node`. |

I log completi di entrambi i container: `docker compose logs`. Tutti i comandi `docker compose` si eseguono dalla cartella `/opt/nevod/installer/docker`.
