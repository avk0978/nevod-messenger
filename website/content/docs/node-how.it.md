# Come funziona un nodo

Un nodo è un programma su un server attraverso il quale i telefoni si scambiano messaggi e avviano chiamate. Qui, in breve, cosa fa un nodo, cosa conserva e cosa non può vedere, così che prima dell'installazione tu sappia cosa ti assumi.

## Nodo, cella e nodo di casa

Ogni utente di Nevod è una **cella**: una coppia di chiavi di cifratura creata sul telefono che non lo lascia mai. Una cella si registra su un nodo: il suo **nodo di casa**. Attraverso di esso il telefono riceve i messaggi inviati mentre era spento.

I nodi sono collegati in una rete comune. Se scrivi a qualcuno di un altro nodo, il tuo nodo passa il messaggio cifrato al nodo di quella persona. Non c'è un server centrale: la rete sono i nodi stessi.

Il carico di un nodo dipende solo dalla sua cerchia — i suoi utenti e i suoi bot — e non dalle dimensioni dell'intera rete: un nodo non inoltra né conserva messaggi di altri nodi. Per questo a un nodo basta un computer comune, e non diventa più pesante per quante persone arrivino su Nevod tramite altri nodi. Queste reti si chiamano **a basso carico** (classe LL-0); di più nell'articolo [«Low-Load Distributed Data Networks»](../../publications/low-load-networks/) (DOI 10.5281/zenodo.23621073).

## Tipi di nodo

Tutti i nodi eseguono lo stesso programma. Cosa diventa un nodo — un nodo familiare chiuso, un nodo aperto di una comunità o il nodo di un'organizzazione — lo decidono tre impostazioni del [pannello di amministrazione](../node-admin/):

- **chi ammettere**: la modalità di ammissione delle celle: solo con codice di invito, con codice o su richiesta con la tua approvazione, oppure tutti (dettagli nella tabella di [Prima configurazione](../node-panel/), passo 2);
- **se il nodo è visibile in «Esplora la rete»** per gli utenti di altri nodi;
- **cosa mostra il nodo ai suoi utenti**: i bot e le pagine pubblicati su di esso.

| Che nodo | Chi ammettere | Visibile in «Esplora la rete» | Esempio |
|---|---|---|---|
| Chiuso: famiglia, amici, organizzazione | con codice di invito | no | il nodo di un'azienda in cui l'amministratore invita ogni dipendente |
| Comunità con selezione | con codice o su richiesta con approvazione | sì | il nodo di un club: chiunque può trovarlo, ma i membri li approva l'amministratore |
| Comunità aperta | tutti | sì | un nodo pubblico come Nevod Open |

**Dove gira il nodo** — su un server a noleggio con un dominio o a casa, sul tuo computer — non cambia ciò che può fare. Un nodo di casa deve essere raggiungibile da internet: inoltro delle porte sul router e un dominio. Per questo è più semplice iniziare con un server a noleggio: tutta la documentazione è scritta per quello.

**Importante per un nodo di casa: dalla rete di casa ci si collega con regole diverse.** I telefoni si collegano al nodo tramite il dominio, e il dominio punta all'indirizzo esterno del tuo router. Un telefono sul Wi-Fi di casa cerca di raggiungere quell'indirizzo esterno dall'interno della rete, e molti router non lasciano passare queste connessioni. Allora il nodo funziona con la rete cellulare, ma sul Wi-Fi di casa l'app dice «Nessuna connessione». Collegarsi con l'indirizzo locale del server (per esempio `192.168.1.10`) non funziona nemmeno: il certificato è emesso per il dominio, non per l'indirizzo. Si risolve sul router, in uno di due modi:

- attiva il **NAT loopback** (detto anche NAT hairpinning o NAT reflection), se il router lo supporta;
- oppure aggiungi nel DNS del router un record locale: il tuo dominio → l'indirizzo locale del server.

Controllalo subito dopo l'installazione: collegati al nodo da un telefono sia tramite il Wi-Fi di casa sia tramite la rete cellulare.

**I nodi del progetto Nevod** — Nevod Open, Dev Planet e pochi altri — non si distinguono dagli altri per il programma, ma per tre cose:

- hanno una chiave Apple per le notifiche push e un relay per le chiamate, e li condividono con i nodi della rete (vedi sotto);
- in «Esplora la rete» hanno l'**anello dorato** di nodo verificato e un'etichetta di scopo: «Comunità», «Informativo», «Agente IA». L'anello è confermato dalla firma del curatore del progetto e per ora ce l'hanno solo i nodi del progetto;
- **Nevod Open** è il nodo su cui l'app registra gli utenti per impostazione predefinita, e il punto d'ingresso nella rete per i nuovi nodi: ci si può collegare senza invito.

> Nelle impostazioni del pannello ci sono anche «Tipo di nodo» — `permanent` o `temporary` — e «ID del nodo padre». Sono **in sviluppo**: nodi temporanei (per esempio per la durata di un evento). L'app non li usa ancora: lascia `permanent` e l'ID del nodo padre vuoto.

## Cosa conserva un nodo

- **Le registrazioni delle celle**: identificativo, chiavi pubbliche e il nome visualizzato scelto dall'utente.
- **I messaggi non consegnati**, cifrati, finché il destinatario non si collega, ma non oltre 72 ore. Dopo la consegna il messaggio viene eliminato.
- **I token di notifica** dei telefoni, per «svegliare» un telefono quando arriva un messaggio o una chiamata.
- **I codici di invito**, le richieste di accesso, i messaggi degli utenti all'amministratore del nodo.
- **L'elenco degli altri nodi della rete** e le proprie impostazioni.
- **I log tecnici**, di dimensione limitata (3 file da 10 MB per container); le voci vecchie vengono sovrascritte.

## Cosa non vede un nodo

- **Il testo dei messaggi, le foto, i video, i messaggi vocali e i file.** Vengono cifrati sul telefono del mittente con la chiave del destinatario. Il nodo li consegna senza avere la chiave per aprirli.
- **Il contenuto delle chiamate.** Audio e video viaggiano tra i telefoni direttamente o attraverso un relay (TURN), cifrati.
- **I contatti e le conversazioni sul telefono.** Sono salvati solo sul dispositivo.

Cosa vede invece il nodo: quali celle sono registrate su di esso e con quali nomi, chi scrive a chi e quando, la dimensione dei messaggi, gli indirizzi IP delle connessioni. Sono dati di consegna: senza di essi il nodo non potrebbe funzionare. Di più nell'[Informativa sulla privacy](../../privacy/).

> Il proprietario del nodo è responsabile del suo funzionamento e del backup dei suoi dati. Non può leggere le conversazioni degli utenti: questo deriva da come è costruita la rete, non da una promessa.

## Notifiche e chiamate tramite i nodi del progetto

Solo un nodo che ha una chiave Apple può inviare notifiche push all'app Nevod dell'App Store, e solo i nodi del progetto ce l'hanno. Per questo un nodo collegato alla rete chiede a un nodo del progetto di inviare la notifica al posto suo. Il nodo del progetto vede il token del telefono e il nome del mittente per il titolo della notifica, e il testo è sempre lo stesso: «Nuovo messaggio». Se il mittente è nei contatti del destinatario, il telefono stesso mette il nome con cui è salvato.

**Posso inviare notifiche direttamente dal mio nodo?** No. Le notifiche a un'app dell'App Store sono accettate solo con una chiave dell'account sviluppatore Apple con cui l'app è pubblicata, e Nevod è pubblicato dal progetto. Questa chiave non si può dare ai proprietari dei nodi: non si può limitare a un singolo nodo e permette di inviare a qualsiasi utente di Nevod una notifica con qualsiasi testo. Per questo le notifiche passano dai nodi del progetto, e il loro testo è sempre «Nuovo messaggio».

Allo stesso modo, un nodo senza un proprio relay per le chiamate (TURN) ne ottiene uno dai nodi della rete; di più in [Chiamate tramite il proprio nodo](../node-turn/).

Da qui una conclusione importante: **un nodo non collegato alla rete consegnerà i messaggi, ma i telefoni non riceveranno notifiche** mentre l'app è chiusa. Come collegarsi: in [Collegarsi alla rete Nevod](../node-network/).

## Di cosa è fatta l'installazione

Il kit per server già pronto (la cartella `installer/docker` nel [codice sorgente](https://github.com/avk0978/nevod-messenger)) è composto da due container Docker:

| Container | Cosa fa | Porte |
|---|---|---|
| `nevod_node` | il nodo vero e proprio | 8765: per gli altri nodi; 8766: il pannello di amministrazione, raggiungibile solo dal server stesso |
| `nevod_caddy` | il server web Caddy: ottiene da solo un certificato HTTPS per il tuo dominio e passa al nodo le connessioni dei telefoni e del pannello | 80 e 443 |

Tutti i dati del nodo sono nella cartella `data/`, accanto al file delle impostazioni:

- `node.json`: **l'identità del nodo**, le sue chiavi. Se perdi questo file, perdi il nodo: non si può ricreare un nodo con la stessa identità, e tutti gli utenti dovrebbero registrarsi su uno nuovo. Tienine un backup.
- `node.db`: il database: registrazioni, inviti, il buffer dei messaggi.

## Cosa ti serve

- **Un server Linux**: va bene il VPS a noleggio più economico: 1 CPU, 1 GB di memoria, 10 GB di disco. Basta per decine e centinaia di utenti.
- **Un dominio** (o sottodominio) che puoi far puntare al server, per esempio `node.example.org`. Senza dominio i telefoni non possono verificare il certificato HTTPS.
- **Circa mezz'ora** e saperti collegare al server via SSH. Tutti i comandi sono in [Installazione passo per passo](../node-install/): puoi copiarli così come sono.
