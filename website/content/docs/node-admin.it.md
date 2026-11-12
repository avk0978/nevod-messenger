# Il pannello di amministrazione: tutte le pagine e le impostazioni

Una guida di riferimento al pannello di amministrazione del nodo: cosa c'è in ogni pagina e cosa fa ogni impostazione. Se hai appena installato il nodo, comincia da [Prima configurazione nel pannello di amministrazione](../node-panel/): lì c'è l'essenziale, passo per passo.

Il pannello si apre all'indirizzo `https://tuo-dominio/nevod-admin` (oppure tramite un tunnel SSH, se l'hai chiuso; vedi l'[installazione](../node-install/), passo 10). Nome utente qualsiasi; la password è `NEVOD_ADMIN_PASSWORD` di `.env` o una personale creata nella pagina «Sicurezza». La lingua si cambia nell'intestazione.

## Intestazione

In cima a ogni pagina: il nome del nodo, il suo identificativo (`node_id`) e delle etichette con lo stato attuale: se il nodo è visibile in «Esplora la rete», la modalità di ammissione delle celle, chi vede le celle pubblicate.

## Panoramica

L'elenco di tutte le celle (utenti e bot) registrate sul nodo.

| Colonna | Cosa mostra |
|---|---|
| Nome | Una tua etichetta per questa cella: la vedi solo tu, nel pannello. Scrivila e premi ✓ o Invio. Non cambia il nome scelto dall'utente. |
| `cell_id` | L'identificativo della cella. Quello completo è nel suggerimento. |
| Lingua | La lingua del telefono dell’utente: scrivigli in quella. «Magyar → English»: Nevod non ha questa lingua, la persona vede l’app in inglese; scrivi in inglese. «—»: app precedente alla 1.3. |
| Stato | Online o offline: se l'app è collegata in questo momento. |
| Buffer | Ciò che aspetta che l'utente si colleghi (conservato fino a 72 ore): **msg**, messaggi e parti di file; **di servizio**, segni «consegnato/letto», reazioni e segnali. Quelli di servizio arrivano quando la persona apre l'app. |
| Registrazione | Quando la cella si è registrata. |

Sotto la tabella, **Lingue dei membri**: quante persone usano ciascuna lingua, comprese quelle che Nevod non ha ancora. Mostra quali lingue servono di più.

Pulsanti:

- **✕** in una riga: eliminare la cella. Revoca del tutto la sua ammissione: la registrazione, i messaggi non consegnati e i token di notifica vengono eliminati, e il nome torna libero. Per tornare, la persona avrà bisogno di un nuovo codice di invito o di una nuova richiesta. Il nodo non elimina mai le celle da solo: solo tu.
- **Azzera le registrazioni**: tutte le celle si registrano di nuovo al prossimo collegamento; non serve reinserire il codice.
- **Azzeramento completo**: irreversibile: tutti i membri dovranno rientrare con un codice di invito. In pratica serve solo in caso di trasloco o di cambio completo dei membri del nodo.

## Impostazioni

| Impostazione | Cosa fa | Quando si applica |
|---|---|---|
| **Nome del nodo** | Il nome del nodo che vedono gli utenti. Non si possono usare parole di servizio (Nevod, admin, support, official e simili). | Nel pannello, subito; per gli altri nodi, dopo un riavvio. |
| **Tipo di nodo** *(in sviluppo)* | `permanent`: un nodo normale. `temporary`: un nodo temporaneo, per esempio per la durata di un evento; l'app non usa ancora questi nodi. Lascia `permanent`. | Dopo un riavvio. |
| **ID del nodo padre** *(in sviluppo)* | Serve solo a un nodo temporaneo: a quale nodo permanente appartiene. Lascialo vuoto. | Subito. |
| **Visibilità in «Esplora la rete»** | `closed`: il nodo non viene mostrato agli utenti di altri nodi. `open`: il nodo compare nel loro «Esplora la rete». Questo non apre la registrazione. | Dopo un riavvio. |
| **Visibilità delle celle pubblicate** | Chi vede l'elenco dei bot e delle pagine della pagina «Pubblicazione»: `off`, nessuno; `members`, solo gli utenti di questo nodo; `public`, tutti. | Subito. |
| **Modalità di ammissione delle celle** | `delegated`: solo con codice di invito; `admin`: con codice o su richiesta con la tua approvazione; `open`: chiunque conosca l'indirizzo. | Subito. |
| **Amministratori** | Gli identificativi (`cell_id`) delle tue celle, separati da virgole. Nella modalità `admin` ricevono in Nevod un messaggio per ogni nuova richiesta. Il tuo `cell_id` è nella pagina «Panoramica». | Subito. |

Riavviare il nodo, sul server, nella cartella `/opt/nevod/installer/docker`:

```
docker compose restart nevod_node
```

## Richieste di accesso

Funziona nella modalità di ammissione `admin`. Quando qualcuno senza codice cerca di registrarsi, l'app invia da sola una richiesta, che compare qui con un nome e una nota. **Approva**: la persona ottiene subito l'accesso e una notifica sul telefono. **Rifiuta**: l'app le mostra che la richiesta è stata rifiutata.

## Messaggi

I messaggi che gli utenti del nodo hanno inviato dall'app al suo account **administrator**: segnalazioni di messaggi, domande. Ogni nodo ha un account administrator, che viene creato da solo al primo avvio.

Apri una conversazione, scrivi una risposta e premi **Rispondi**: la risposta arriva all'utente in Nevod, cifrata, a nome di administrator. Ai messaggi degli utenti si risponde solo così, nell'app, non via email.

Se l'utente ha allegato al messaggio il log dell'app (per analizzare un problema), nella conversazione compare il link **scarica nevod.log**.

Gli utenti vedono l'account administrator del tuo nodo con il contrassegno **Amministratore del nodo** e il nome del nodo. Il contrassegno è confermato dalla chiave del tuo nodo, quindi nessun altro può spacciarsi per l'amministratore del tuo nodo. Il badge blu ✓ è il segno dell'amministrazione del progetto Nevod: è confermato dalla firma del curatore del progetto e ce l'hanno solo i nodi del progetto.

## Inviti

**Creare un codice:** scegli la validità (1 ora, 24 ore, 7 giorni) → **+ Crea codice**. Compaiono un codice QR e un link: puoi mostrarli sullo schermo, inoltrarli o premere **Copia link**. Il link apre Nevod con l'indirizzo del nodo e il codice già compilati. Il codice breve, come `ABCD-EFGH`, funziona solo se nell'app della persona è già impostato il tuo nodo.

Ogni codice vale una sola volta. Sotto ci sono tutti i codici con la validità e lo stato: attivo, usato, da chi.

**Celle ammesse**: chi è entrato e su invito di chi. L'interruttore **Può invitare** permette a quella persona di creare codici dall'app (Profilo → Invita qualcuno); nella modalità `delegated` è così che affidi gli inviti a persone di fiducia.

Di più in [Invitare le persone](../node-invite/).

## Nodi

**Collegamento alla rete Nevod.** Lo stato («collegato · nodi online» o «non collegato») e il pulsante **Collegati alla rete Nevod**. Un nodo collegato riceve dai nodi del progetto le notifiche push per i telefoni e un relay per le chiamate. Il campo **Token dall'amministratore di un altro nodo** serve per collegarsi tramite un altro nodo invece che tramite Nevod Open. Di più in [Collegarsi alla rete Nevod](../node-network/).

**Nodi noti**: tutti i nodi della rete che il tuo nodo conosce: nome, indirizzo, online o no, quando si è fatto sentire l'ultima volta. Un nodo che non si fa sentire da 72 ore viene tolto dall'elenco e ci torna da solo quando ricompare nella rete.

**Inviti per nodi**: un token con cui un altro nodo può collegarsi tramite il tuo. Vale 10 minuti; dallo all'amministratore dell'altro nodo di persona, non pubblicamente.

## Pubblicazione

I bot e le pagine che il tuo nodo mostra agli utenti nell'app, sul «pianeta» del nodo in «Esplora la rete». Scegli una cella, imposta un titolo, un tipo (`bot`: un bot; `page`: una pagina di testo) e una descrizione → **Pubblica**. Ritirarla dalla pubblicazione la toglie dall'elenco; la cella in sé resta.

Le caselle Claude, ChatGPT, Gemini sono per un bot IA esterno che funziona con la chiave dell'utente: quali provider accetta. Per un bot normale non selezionare nulla.

Chi vede questo elenco si imposta in «Impostazioni» → «Visibilità delle celle pubblicate».

## Bot IA

Bot IA che funzionano direttamente dentro il nodo e rispondono tramite Claude, ChatGPT o Gemini **con la chiave dell'utente**: la persona aggiunge la propria chiave nella chat con il bot, la chiave arriva con ogni messaggio e il bot non la conserva. Il nodo non ha chiavi proprie e non paga per l'IA.

**Aggiungi un bot**: imposta un nome, una descrizione, un'istruzione per il modello e i provider, oppure prendi un modello già pronto (AI Assistant, Tolmach il traduttore) e adattalo. Un bot attivato compare agli utenti del nodo nell'elenco «Su questo nodo». Uno disattivato è fermo e nascosto, e conserva il suo nome. L'eliminazione è definitiva: le chiavi e il nome del bot vengono eliminati, mentre gli utenti conservano le loro conversazioni.

> Le conversazioni con un bot IA le decifra il codice sul tuo nodo e le passa al provider scelto. Gli utenti ne sono avvisati nell'[Informativa sulla privacy](../../privacy/) (sezione 5). Se attivi i bot IA, tu, come proprietario del nodo, partecipi a questo trasferimento.

## Sicurezza

Account personali degli amministratori: **Aggiungi / cambia password**: un nome utente e una password (salvata come hash). Un account per ogni amministratore; se qualcuno se ne va, elimina il suo account senza cambiare la password principale. La password principale di `.env` funziona sempre come accesso di riserva.

Cinque password sbagliate di fila dallo stesso indirizzo bloccano l'accesso per quell'indirizzo per 15 minuti.

## Diagnostica

**Verifica**: l'autodiagnosi del nodo (fino a 10 secondi):

| Verifica | Cosa significa |
|---|---|
| Codice aggiornato | Se la versione installata del nodo è rimasta indietro rispetto al protocollo; se sì, aggiorna il nodo (vedi [Manutenzione](../node-maintenance/)). |
| Coerenza identity/DB | Se le impostazioni di `node.json` coincidono con il database. |
| Dipendenze e configurazione | Se ci sono errori nelle impostazioni (per esempio un relay per le chiamate senza `TURN_SECRET`). |
| Raggiungibilità esterna | Se un altro nodo della rete riesce a raggiungere il tuo dall'esterno. Finché il nodo non è collegato alla rete, mostra «Nessun peer noto»: è normale. |

**Log**: le ultime voci del log del nodo. Il testo dei messaggi non finisce mai nel log.
