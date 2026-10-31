# Sicurezza e backup

Cosa protegge Nevod da solo, come ti protegge da truffatori e attacchi, cosa dovresti fare tu, come difenderti dagli sconosciuti, come bloccare una chat con una password, come bloccare e segnalare, e perché Nevod non fa backup delle conversazioni.

## Cosa è protetto senza che tu faccia nulla

- **Le conversazioni e le chiamate sono cifrate** sul tuo telefono con la chiave dell'altra persona. Né i nodi, né gli sviluppatori di Nevod, né Apple possono vederle.
- **Chiavi, contatti e cronologia dei messaggi sono salvati solo sul tuo telefono.** Non sono nei backup di iCloud o del computer, né sui nodi, né presso lo sviluppatore.
- **Un nodo sa solo ciò che serve per consegnare un messaggio:** chi è registrato su di esso, a chi scrivi e quando, ma non cosa.

Come funziona nel dettaglio: nella pagina [Sicurezza](../../security/).

## Protezione da truffatori e attacchi

- **Nessuno può trovarti dal numero di telefono.** Nevod non ha numeri di telefono né indirizzi email, quindi non si possono prendere da un database trafugato e usare per spam o chiamate truffa. Può scriverti solo chi ha la tua scheda o un membro del tuo nodo.
- **Non c'è una password dell'account: non c'è niente da rubare.** Non si può spiare, indovinare o estorcere. Quando si collega, il telefono dimostra al nodo di possedere la chiave, ma la chiave stessa non lascia mai il telefono.
- **Nessuno può spacciarsi per l'amministrazione.** I nomi di servizio — administrator, support, Nevod e simili — non si possono registrare. La vera amministrazione ha il badge blu ✓, l'amministratore di un nodo privato il contrassegno **Amministratore del nodo**. Un account con un nome di servizio senza badge né contrassegno l'app lo segna con un ⚠ arancione e un avviso nella chat.
- **Le notifiche false non passano.** Una notifica di nuovo messaggio non contiene alcun testo che un estraneo possa impostare: solo «Nuovo messaggio» e il nome del mittente, e i nomi di servizio vengono sostituiti con «Nevod». Una notifica «da Nevod» che ti chiede di inserire un codice o di aprire un link è una truffa.
- **Il tuo nodo non si può sostituire.** Tutto ciò che arriva dal nodo è firmato con la sua chiave, e l'app verifica la firma. Anche su una rete Wi-Fi altrui nessuno in mezzo può spacciarsi per il tuo nodo o infilare messaggi falsi a suo nome.
- **I file e le immagini pericolosi vengono scartati.** Gli attacchi più pericolosi ai telefoni — come lo spyware Pegasus — arrivano come un'immagine o un file appositamente preparati e agiscono senza un solo tocco. Per questo Nevod controlla tutto ciò che riceve dagli altri: la dimensione dei file è limitata e il tipo deve corrispondere al contenuto, altrimenti il file non viene mostrato come immagine o video e non si apre da solo. Gli avatar sono accettati solo dai tuoi contatti e dai membri del tuo nodo, e l'app non mostra mai l'immagine ricevuta: la ridisegna lei stessa.
- **Mentre il telefono è bloccato, i file sono chiusi.** Foto, video e file delle chat sono cifrati da iOS e diventano inaccessibili pochi secondi dopo il blocco, anche per chi ha ottenuto accesso alla memoria del telefono. Nel selettore delle app al posto della conversazione si vede una copertina di Nevod.
- **Violare un nodo non espone le tue conversazioni.** Su un nodo non ci sono né il testo dei messaggi né le tue chiavi: anche con accesso al nodo, un aggressore non può leggere le tue conversazioni.
- **I nodi verificati sono contrassegnati.** I nodi del progetto Nevod in **Esplora la rete** hanno un anello dorato: lo conferma la firma del progetto, e un nodo falso non può ottenerlo.

## Cosa dovresti fare tu

Il punto più vulnerabile è il telefono stesso: chi sblocca il tuo telefono vede anche le tue conversazioni. E se sul telefono c'è già uno spyware che ha violato iOS stesso, vede tutto ciò che vedi tu sullo schermo: da questo non ti protegge nessuna app, nemmeno Nevod. Per questo è importante che non ci entri.

- **Un codice sull'iPhone**: obbligatorio, e non uno semplice come 000000.
- **Tieni iOS aggiornato**: gli aggiornamenti chiudono le vulnerabilità sfruttate dagli spyware.
- **Riavvia il telefono di tanto in tanto.** Molti spyware non sopravvivono a un riavvio.
- **Se sei un giornalista, un difensore dei diritti umani o per altri motivi potresti essere un bersaglio**, attiva la **Modalità di isolamento** dell'iPhone: **Impostazioni → Privacy e sicurezza → Modalità di isolamento**. Chiude molte delle vie usate da attacchi come Pegasus.
- **Una password sulle chat importanti**: vedi sotto.
- **Non dare a nessuno codici o chiavi.** L'amministrazione di Nevod scrive solo nell'app, dall'account **administrator** con il badge ✓ (su un nodo privato, con il contrassegno **Amministratore del nodo**), mai via email, e non chiede mai password, chiavi o codici. Chi li chiede è un truffatore.

## Password della chat

Puoi bloccare una singola chat con una password: così, anche se qualcuno ha in mano il tuo telefono sbloccato, non potrà aprire quella chat.

1. Apri la chat → l'ingranaggio in alto a destra → attiva **Protezione con password**.
2. Imposta due password:
   - **Password di sblocco**: con questa apri la chat;
   - **Password di emergenza**: per quando ti costringono ad aprire la chat. Se la inserisci al posto di quella vera, la conversazione di questa chat viene **cancellata in silenzio** dal tuo telefono e sullo schermo compare il solito «Password errata»: per chi guarda, sembra un errore di battitura.
3. Le password devono essere diverse. Per cambiarle, nello stesso punto: **Cambia password**.

> La password della chat è salvata solo su questo telefono, e non la password stessa ma il suo hash. **Una password dimenticata non si può recuperare**, né da te né dagli sviluppatori, e la chat non si potrà più aprire. Scegli una password che non dimenticherai. La password di emergenza cancella la conversazione solo da te: l'altra persona la conserva.

## Protezione dagli sconosciuti

Non solo le persone a cui hai dato la tua scheda possono scriverti e chiamarti. Su un nodo aperto, come Nevod Open, chiunque può registrarsi, e i membri del nodo si vedono in **Contatti → Su questo nodo**. Inoltre qualcuno con cui scrivi può inoltrare la tua scheda a un altro. Qui sconosciuto è chi non è nei tuoi contatti. Gli account ufficiali Nevod e l'amministratore del tuo nodo non contano come sconosciuti.

In **Profilo → Sicurezza** ci sono due impostazioni. Se attivarle lo decidi tu; all'inizio sono entrambe disattivate:

- **Chiamate solo dai contatti**: una chiamata da qualcuno che non è nei tuoi contatti viene rifiutata in silenzio, il telefono non squilla. Per chi chiama, la chiamata termina subito; nella tua cronologia chiamate compare come **Rifiutata: non nei contatti**.
- **Immagini dagli sconosciuti: al tocco**: foto e video di qualcuno che non è nei tuoi contatti non vengono mostrati subito: la chat mostra un segnaposto **Foto: mostra** o **Video: mostra**, e l'app apre il file solo dopo che l'hai toccato. Così nemmeno un'immagine preparata può attivarsi da sola.

Su un nodo chiuso, dove l'amministratore conosce tutti i membri, queste impostazioni di solito non servono. Su un nodo aperto conviene attivarle.

## Bloccare e segnalare

- **Bloccare** qualcuno: impostazioni della chat (l'ingranaggio) → **Blocca**. Non potrà scriverti né chiamarti e non lo saprà. L'elenco dei bloccati: **Profilo → Sicurezza → Bloccati**.
- **Segnalare un messaggio**: tienilo premuto → **Segnala**. Segnalare una persona: impostazioni della chat → **Segnala**.
- **Segnalare un abuso** senza una chat precisa: **Profilo → Sicurezza → Segnala un abuso**.

La segnalazione va all'amministrazione del tuo nodo, come messaggio nell'app all'account administrator (o via email ad abuse@nevod.network). I messaggi di Nevod sono cifrati e l'amministrazione non li vede, perciò l'app allega alla segnalazione il testo del messaggio segnalato. La risposta arriva nella chat con administrator. Insieme alla segnalazione puoi bloccare subito la persona: **Blocca anche**.

## Non ci sono backup, ed è voluto

Chiavi, contatti e cronologia dei messaggi esistono solo sul tuo telefono. Quindi:

- **se il telefono viene perso, si rompe o viene inizializzato, le conversazioni non si possono recuperare;**
- **anche eliminare l'app cancella la cronologia;**
- **non c'è ancora il trasferimento su un nuovo telefono.** Su un nuovo telefono crei una nuova identità, e i tuoi contatti avranno bisogno della tua nuova scheda.

È una conseguenza di come è fatto Nevod: una copia da cui si potessero ripristinare le tue conversazioni sarebbe anche una copia a cui qualcun altro potrebbe accedere. Se devi conservare a lungo qualcosa di una conversazione, salvalo a parte: foto e file, con **Condividi**.

## Reimpostare l'identità

**Profilo → Reimposta identità…** elimina per sempre la tua identità, i contatti, i messaggi sul telefono e la registrazione sul nodo. L'app ti chiede di scrivere una parola di conferma, così non può succedere per sbaglio.

Serve se vuoi ricominciare da zero o passare a un altro nodo. I tuoi contatti vedranno **Identità eliminata** nella vostra chat; per scriverti di nuovo avranno bisogno della tua nuova scheda.
