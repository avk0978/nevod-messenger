# Invitare le persone

Come le persone arrivano sul tuo nodo — su invito, su richiesta o liberamente — e come poi si trovano tra loro, anche con persone di altri nodi. Quale modalità usare si decide nel pannello: **Impostazioni → Modalità di ammissione delle celle** (vedi [Prima configurazione](../node-panel/), passo 2).

## Invito dell'amministratore

La via principale, e l'unica finché il nodo funziona nella modalità predefinita (`delegated`).

1. Pannello → **Inviti** → scegli la validità: 1 ora, 24 ore o 7 giorni → **+ Crea codice**.
2. Dai l'invito alla persona in uno di questi modi:
   - **mostra il codice QR** sullo schermo: la persona lo inquadra con la normale fotocamera del telefono;
   - **Copia link**, e invialo con qualsiasi messenger o via email;
   - **detta il codice breve**, come `ABCD-EFGH`: funziona solo se nell'app della persona è già impostato il tuo nodo.
3. La persona installa Nevod dall'App Store, apre il link (nella pagina di invito c'è il pulsante **Apri in Nevod**), inserisce un nome e tocca **Inizia**.

Cosa sapere sui codici:

- **Ogni codice vale una sola volta.** Un codice per persona. Un codice usato è segnato nell'elenco come «usato», con accanto chi è entrato con esso.
- **Validità.** Non scegliere una settimana per un codice che pubblichi in una chat di gruppo: finché non viene usato, può usarlo chiunque lo ottenga. 1 ora è per un codice che mostri a qualcuno di persona.
- **Il link non rivela niente di superfluo.** Contiene solo l'indirizzo del nodo e il codice. La pagina di invito su nevod.network non vede né il codice né l'indirizzo: restano nella parte del link dopo `#`, che il browser non invia al server.

Se la persona usa già Nevod su un altro nodo, l'invito non la sposta da solo: l'app avvisa che prima deve reimpostare l'identità (**Profilo → Reimposta identità…**). La reimpostazione elimina per sempre la sua identità, i contatti, i messaggi sul telefono e la registrazione sul nodo precedente. Per scrivervi semplicemente non serve spostarsi: basta scambiarsi i contatti (vedi sotto).

## Invitano i membri stessi

Nella modalità `delegated` puoi affidare gli inviti a persone di fiducia: pannello → **Inviti** → **Celle ammesse** → attiva **Può invitare** per quella persona. Allora **Profilo → Invita qualcuno** nella sua app crea un codice, e l'app mostra un codice QR da inquadrare.

Nella modalità `open` qualsiasi membro può invitare, ma in questa modalità il codice non serve comunque.

## Richieste con approvazione

La modalità `admin` è adatta se vuoi che il nodo si possa trovare e che si possa chiedere di entrare, ma decidi tu.

1. La persona trova il tuo nodo in «Esplora la rete» e tocca **Unisciti a questo nodo** (se il nodo è visibile lì; vedi [Prima configurazione](../node-panel/), passo 4), oppure al primo avvio dell'app tocca **Cambia server…** e inserisce l'indirizzo del nodo `node.example.org/nevod-ws`.
2. L'app invia da sola una richiesta e mostra «In attesa di approvazione».
3. La richiesta compare nel pannello nella pagina **Richieste di accesso**. Se in **Impostazioni → Amministratori** c'è il tuo `cell_id`, ricevi anche un messaggio in Nevod.
4. **Approva**: la persona riceve una notifica ed entra subito. **Rifiuta**: l'app le mostra che la richiesta è stata rifiutata.

I codici di invito funzionano anche nella modalità `admin`: con il codice si entra subito, senza richiesta.

## Registrazione libera

Nella modalità `open` può registrarsi chiunque conosca l'indirizzo del nodo. È adatta a una comunità aperta. Tieni conto che:

- il nodo non elimina mai le registrazioni né libera i nomi da solo: dovrai fare pulizia a mano, nella pagina **Panoramica** (pulsante ✕);
- i nomi di servizio (Nevod, administrator, support e simili) non si possono occupare in nessuna modalità.

## Come si trovano i membri

Registrarsi sullo stesso nodo non rende le persone contatti tra loro. Per scriversi devono scambiarsi i contatti:

- **Profilo → Condividi la mia scheda**: mostra un codice QR e il testo della scheda; l'altra persona: **Contatti → Aggiungi contatto**, e inquadra il QR o incolla il testo;
- la scheda si può inviare in qualsiasi modo: non contiene nulla di segreto, solo un identificativo e chiavi pubbliche.

Le persone **di altri nodi** si aggiungono allo stesso modo: la scheda contiene l'indirizzo del loro nodo di casa. Perché queste conversazioni funzionino, il tuo nodo deve essere [collegato alla rete Nevod](../node-network/).

> Eliminare un utente (pannello → **Panoramica** → ✕) revoca del tutto la sua ammissione: la registrazione, i messaggi non consegnati e i token di notifica vengono eliminati. Per tornare, la persona avrà bisogno di un nuovo invito.
