# Manutenzione

Aggiornare il nodo, i backup, il trasloco su un altro server, i log e la normale cura del server. Tutti i comandi `docker compose` si eseguono sul server dalla cartella `/opt/nevod/installer/docker`:

```
cd /opt/nevod/installer/docker
```

## Aggiornare il nodo

Le nuove versioni del nodo escono nel [codice sorgente su GitHub](https://github.com/avk0978/nevod-messenger): per esserne informato, premi **Watch** lì. Per aggiornare:

```
cd /opt/nevod
git pull
cd installer/docker
docker compose up -d --build
```

Il nodo si riavvia con la nuova versione; gli utenti si ricollegano da soli e i dati nella cartella `data/` restano. Dopo l'aggiornamento, controlla nel pannello **Diagnostica** → **Verifica**.

Dopo alcuni aggiornamenti le immagini vecchie occupano spazio su disco: puoi eliminarle:

```
docker image prune -f
```

## Backup

La cosa più preziosa sul server è la cartella `data/`, e in essa il file `node.json`: è l'identità del nodo. Se lo perdi, il nodo dovrà essere ricreato, con un nuovo identificativo, e tutti gli utenti dovranno registrarsi di nuovo. Fai una copia almeno una volta alla settimana e dopo ogni modifica delle impostazioni.

**Fare una copia** (il nodo si ferma per qualche secondo):

```
docker compose stop nevod_node
tar czf ~/nevod-backup-$(date +%F).tar.gz data .env
docker compose start nevod_node
```

**Scaricarla.** Sul tuo computer:

```
scp root@node.example.org:~/nevod-backup-*.tar.gz .
```

Non tenere la copia sullo stesso server: se al server succede qualcosa, la copia sparisce con lui.

> La copia contiene le chiavi del nodo e la password del pannello di `.env`. Conservala con la stessa cura di una password: un disco cifrato, un gestore di password con allegati o un posto simile.

## Ripristino e trasloco su un altro server

È così che si trasloca un nodo su un nuovo server. Il dominio resta lo stesso; cambia solo il server a cui punta.

1. Sul nuovo server esegui i passi 1 e 3–6 dell'[installazione](../node-install/) (server, Docker, firewall, scaricare Nevod), **senza** i passi 7–8.
2. Copia il backup sul nuovo server e scompattalo nella cartella del kit:

   ```
   scp nevod-backup-DATA.tar.gz root@NUOVO-IP:/opt/nevod/installer/docker/
   ```

   e sul nuovo server:

   ```
   cd /opt/nevod/installer/docker
   tar xzf nevod-backup-DATA.tar.gz
   ```

3. **Ferma il nodo sul vecchio server** (`docker compose down`): due nodi con la stessa identità non devono funzionare contemporaneamente.
4. Cambia il record A del dominio sull'IP del nuovo server e aspetta che `ping node.example.org` mostri il nuovo indirizzo.
5. Avvia il nodo sul nuovo server: `docker compose up -d --build`. Caddy ottiene di nuovo il certificato da solo.

Gli utenti non devono fare niente: l'app si collega allo stesso dominio e lì trova lo stesso nodo.

> Il **dominio** del nodo non si cambia così facilmente: l'indirizzo per i collegamenti con gli altri nodi viene scritto nell'identità del nodo al primo avvio. Scegli un dominio che non dovrai cambiare.

## Log

```
docker compose logs --tail 100 nevod_node
docker compose logs -f nevod_node
```

Il primo comando mostra le ultime 100 righe, il secondo il log in tempo reale (per uscire **Ctrl+C**). Il log di Caddy: `docker compose logs caddy`. Le ultime voci del nodo si vedono anche nel pannello: **Diagnostica → Log**.

I log hanno dimensione limitata: 3 file da 10 MB per container, e le voci vecchie vengono sovrascritte da sole. Il testo dei messaggi non finisce mai nel log.

## Riavvio, arresto, password

| Cosa ti serve | Comando |
|---|---|
| Riavviare il nodo (per esempio dopo aver cambiato nome o visibilità nel pannello) | `docker compose restart nevod_node` |
| Fermare tutto | `docker compose down` |
| Riavviare tutto | `docker compose up -d` |
| Vedere cosa è in funzione | `docker compose ps` |

**Cambiare la password principale del pannello:** scrivi quella nuova nella riga `NEVOD_ADMIN_PASSWORD` di `.env` (`nano .env`) ed esegui `docker compose up -d`: il nodo si riavvia con la nuova password. Gli account personali della pagina «Sicurezza» non cambiano.

## Cura del server

- **Aggiornamenti del sistema**, una volta al mese o più spesso:

  ```
  apt update && apt upgrade -y
  reboot
  ```

  Dopo il riavvio il nodo, Caddy e coturn (se l'hai installato) partono da soli.
- **Spazio su disco**: `df -h /`. Se lo spazio è poco, elimina le immagini vecchie (`docker image prune -f`) e i vecchi backup sul server.
- **Il certificato HTTPS** lo rinnova Caddy da solo. Non devi fare nulla, ma la porta 80 deve restare aperta.
- **Il nodo non risponde?** Il modo più semplice per saperlo subito è puntare un servizio gratuito di monitoraggio dei siti su `https://node.example.org`: ti manderà un'email se il nodo smette di rispondere.

## Se il nodo è rimasto fermo a lungo

I messaggi per gli utenti che non si sono collegati il nodo li conserva fino a 72 ore, poi li elimina. Gli altri nodi della rete rimuovono dai loro elenchi un nodo che non si fa sentire da 72 ore; dopo l'avvio, ci rientra da solo man mano che gli elenchi vengono scambiati.
