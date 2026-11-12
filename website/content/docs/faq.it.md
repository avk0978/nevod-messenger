# Domande e problemi

Risposte brevi alle domande frequenti e cosa fare se qualcosa non funziona. Se la tua domanda non c'è, scrivici (in fondo a questa sezione).

## Domande generali

**Nevod è a pagamento?**
No. L'app è gratuita, senza abbonamenti né pubblicità. Potresti dover pagare solo un provider IA, se usi gli assistenti IA con la tua chiave: vedi [Bot e assistenti IA](../bots/).

**Serve un numero di telefono?**
No. Nevod non ha bisogno di numero di telefono né di indirizzo email e non li chiede. Ti conoscono solo le persone con cui hai scambiato la scheda.

**Esiste Nevod per Android o per computer?**
Per ora solo per iPhone e iPad. La versione per Android è in sviluppo.

**Posso usare Nevod su due dispositivi contemporaneamente?**
Non ancora: un'identità vive su un dispositivo. Su un secondo iPhone o iPad avrai un'identità separata con i propri contatti.

**Ho cambiato telefono. Come trasferisco le conversazioni?**
Per ora non si può: non c'è il trasferimento su un nuovo dispositivo, e Nevod di proposito non fa backup delle conversazioni. Sul nuovo telefono crea una nuova identità e invia ai tuoi contatti la nuova scheda. Di più in [Sicurezza e backup](../security/).

**Come passo a un altro nodo?**
Solo reimpostando l'identità: **Profilo → Reimposta identità…**, poi apri l'invito al nuovo nodo. La reimpostazione elimina per sempre la tua identità, i contatti, i messaggi sul telefono e la registrazione sul nodo precedente. Per scrivere semplicemente a qualcuno di un altro nodo non serve passare a quel nodo: basta la sua scheda.

## Registrazione

| Cosa vedi | Cosa fare |
|---|---|
| «Nome già in uso, scegline un altro» | questo nome esiste già sul nodo, oppure è un nome di servizio (administrator, support, Nevod…). Scegline un altro. |
| «Codice di invito richiesto» | il nodo accetta solo su invito. Chiedi un invito all'amministratore del nodo o scegli un altro nodo. |
| «Codice non valido o scaduto — richiedine uno nuovo» | il codice è già stato usato o è scaduto. Chiedine uno nuovo. |
| «In attesa di approvazione» | il nodo accetta su richiesta: attendi la decisione dell'amministratore; riceverai una notifica. |
| «Richiesta rifiutata» | l'amministratore del nodo ha rifiutato la richiesta. Puoi scegliere un altro nodo, per esempio Nevod Open. |
| hai aperto un invito e l'app dice «Invito a un altro nodo» | sei già registrato su un nodo. Vedi «Come passo a un altro nodo?» qui sopra. |
| hai aperto un invito e l'app dice «Sei già registrato su questo nodo» | l'invito è per il tuo stesso nodo: non serve fare nulla. |

## Connessione

**Sopra il campo di testo della chat c'è «Nessuna connessione» o a lungo «Connessione…», e non si riesce a inviare.**
Controlla internet: apri un qualsiasi sito. Se usi una VPN, prova a disattivarla o a cambiare server. Passa dal Wi-Fi alla rete cellulare o viceversa. Se non serve, forse il tuo nodo è temporaneamente irraggiungibile: aspetta qualche minuto; se sei su un nodo privato, avvisa il suo amministratore.

**Le notifiche non arrivano quando Nevod è chiuso.**
- **Impostazioni dell'iPhone → Nevod → Notifiche**: devono essere consentite.
- Controlla che non sia attivo Non disturbare o un'altra modalità Full immersion.
- Controlla che le notifiche di questa chat non siano disattivate: impostazioni della chat (l'ingranaggio) → **Notifiche**.
- Su un nodo privato: chiedi all'amministratore di verificare che il nodo sia [collegato alla rete Nevod](../node-network/); senza, le notifiche non arrivano.

**Una chiamata non si collega.** Vedi [Chiamate](../calls/), «Se una chiamata non si collega».

## Messaggi e file

**Accanto a un messaggio c'è un orologio arancione.**
L'altra persona non è connessa: il messaggio la aspetta sul nodo e sarà consegnato quando si connetterà. Il nodo conserva questi messaggi fino a 72 ore: se la persona non si connette in quel tempo, il messaggio non arriverà.

**«Messaggio non inviato. Inviare di nuovo?»**
Al momento dell'invio non c'era connessione. Tocca questa riga quando la connessione torna.

**Un file non si invia.**
- Supera i 50 MB: l'app te lo dice. Scegli i video con **Foto o video**: verranno compressi.
- «Impossibile caricare il video»: se il filmato è su iCloud, sul telefono potrebbe esserci solo una copia ridotta. Apri il video nell'app Foto, aspetta che si scarichi del tutto e riprova. Se l'errore si ripete, avvisaci (vedi «Segnalare un problema» più sotto).
- «Impossibile comprimere il video»: prova con un filmato più corto o invialo con **File**, se è sotto i 50 MB.

**«Impossibile salvare il file: spazio esaurito».**
I file ricevuti occupano spazio sul telefono entro la quota di Nevod. Aumentala: **Profilo → Spazio di archiviazione → Quota**, oppure elimina le chat che non ti servono (nell'elenco delle chat scorri verso sinistra → **Elimina**).

## Assistenti IA

**Il bot dice che serve una chiave, oppure la chiave non viene accettata.**
Controlla che la chiave sia stata copiata per intero e non sia stata revocata sul sito del provider, e che sul tuo account del provider ci sia credito o che il limite gratuito non sia esaurito. Puoi cambiare la chiave nella chat con il bot: **Cambia**. Di più in [Bot e assistenti IA](../bots/).

## Segnalare un problema

**Profilo → Diagnostica**: descrivi cosa è successo e più o meno quando (per esempio, «non sono arrivate 2 foto su 3, verso le 21») e tocca **Invia agli sviluppatori**. Insieme alla descrizione parte il registro tecnico dell'app: è salvato solo sul telefono e non contiene il testo dei messaggi. Il registro va via email a support@nevod.network oppure, se sul telefono non è configurato un account email, all'amministratore del tuo nodo in Nevod; la risposta arriva nella chat con lui.

Prima di riprodurre un problema puoi cancellare il log: **Profilo → Diagnostica → Cancella log**, così conterrà solo ciò che serve.

Per segnalare una persona o un messaggio: vedi [Sicurezza](../security/), «Bloccare e segnalare».
