# Collegarsi alla rete Nevod

A cosa serve la rete comune a un nodo, come collegarsi con un pulsante e cosa vedono poi gli altri nodi.

## Perché collegarsi

Un nodo non collegato a nessuno è un'isola. Funziona, ma:

- **i suoi utenti possono scriversi e chiamarsi solo tra loro.** Scrivere a qualcuno di un altro nodo, o ricevere un suo messaggio, è impossibile: il nodo non sa dove inviarlo;
- **i telefoni non ricevono notifiche** mentre l'app è chiusa: solo i nodi del progetto, che hanno la chiave Apple, possono inviare notifiche push a Nevod dell'App Store, e lo fanno per i nodi della rete;
- **le chiamate attraverso reti complicate potrebbero non collegarsi:** un nodo senza un proprio relay per le chiamate (TURN) lo ottiene dai nodi della rete; di più in [Chiamate tramite il proprio nodo](../node-turn/).

Per questo conviene quasi sempre collegare il nodo alla rete, anche un nodo chiuso di una famiglia o di un'organizzazione. Collegarsi alla rete **non apre la registrazione** e **non mostra il nodo in «Esplora la rete»**: chi ammettere e se il nodo è visibile continui a deciderlo tu nelle impostazioni.

## Come collegarsi

1. Assicurati che la porta **8765** del server sia aperta dall'esterno, sia in `ufw` sia nel firewall del provider (vedi l'[installazione](../node-install/), passi 1 e 5). I nodi comunicano tra loro attraverso questa porta.
2. Pannello → **Nodi** → **Collegati alla rete Nevod**.
3. In pochi secondi compare un messaggio che conferma il collegamento. Lo stato in cima al blocco diventa «collegato · nodi online: N», e nell'elenco **Nodi noti** compaiono i nodi della rete.

Il nodo si collega tramite Nevod Open, un nodo del progetto che ammette nodi nella rete senza invito. L'autenticità di Open viene verificata tramite l'impronta del suo certificato, integrata nel programma del nodo: non può essere sostituita lungo il percorso.

Se il pannello dice che **il nodo della rete non è riuscito a raggiungere il tuo nodo dall'esterno**, il collegamento è avvenuto, ma nessuno può collegarsi a te in risposta. Quasi sempre la porta 8765 è chiusa. Aprila e premi di nuovo il pulsante. Puoi verificarlo anche dopo: **Diagnostica → Verifica → Raggiungibilità esterna**.

Il collegamento si conserva: dopo un riavvio, il nodo ricontatta da solo tutti i nodi che conosce.

## Collegarsi tramite un altro nodo

Se conosci l'amministratore di un altro nodo, puoi collegarti tramite il suo nodo invece che tramite Open:

1. Lui, nel suo pannello: **Nodi → Inviti per nodi → + Crea invito per nodo**, e ti passa il token di persona (il token vale 10 minuti).
2. Tu: **Nodi** → incolla il token nel campo **Token dall'amministratore di un altro nodo** → **Collegati con token**.

Il risultato è lo stesso: il tuo nodo diventa parte della rete. Allo stesso modo puoi far entrare nella rete tramite il tuo un nodo che conosci: crea un token per lui.

## Cosa vedono gli altri nodi

I nodi della rete si scambiano un elenco di nodi. Del tuo nodo contiene:

- l'identificativo del nodo (`node_id`), il suo nome e il suo indirizzo per i collegamenti tra nodi (`dominio:8765`);
- l'impronta del certificato del nodo;
- se il nodo è visibile in «Esplora la rete», se ha un proprio relay per le chiamate e una chiave per le notifiche.

Se il nodo è visibile in «Esplora la rete» (impostazione `open`), i nodi della rete sanno anche quali celle vi sono registrate, tramite gli identificativi, senza nomi. Un nodo chiuso non lo comunica: un messaggio per un suo utente arriva all'indirizzo della scheda contatto, che indica il nodo di casa.

Cosa non ricevono mai i nodi della rete: il testo dei messaggi, i file, le chiamate, i contatti degli utenti, i nomi e le chiavi delle celle di un nodo chiuso.

## Come lasciare la rete

Un pulsante «lascia la rete» non c'è ancora. Gli altri nodi rimuovono da soli dai loro elenchi un nodo che non si fa sentire da 72 ore. Se il nodo va scollegato dalla rete per sempre, fermalo o chiudi la porta 8765.
