# Prima configurazione nel pannello di amministrazione

Il nodo è avviato: ora bisogna dargli un nome, decidere chi ammettere e registrarti tu stesso. Tutto si fa nel pannello di amministrazione, all'indirizzo `https://node.example.org/nevod-admin` (come aprirlo: passo 9 dell'[installazione](../node-install/)).

La lingua del pannello si cambia nella sua intestazione. La descrizione dettagliata di ogni pagina e impostazione: in [Il pannello di amministrazione: tutte le pagine e le impostazioni](../node-admin/).

## Cosa c'è dove nel pannello

| Pagina | A cosa serve |
|---|---|
| **Panoramica** | Le celle (utenti) registrate sul nodo. |
| **Impostazioni** | Nome del nodo, modalità di ammissione, visibilità. |
| **Richieste di accesso** | Le richieste degli utenti, se il nodo funziona in modalità di approvazione. |
| **Messaggi** | I messaggi degli utenti all'amministratore del nodo: segnalazioni, domande. Puoi rispondere direttamente da qui. |
| **Inviti** | Codici di invito per gli utenti. |
| **Nodi** | Il collegamento alla rete Nevod e gli altri nodi che il tuo nodo conosce. |
| **Pubblicazione**, **Bot IA** | I bot e i canali che il nodo mostra ai suoi utenti. |
| **Sicurezza** | Account di amministratore aggiuntivi. |
| **Diagnostica** | L'autodiagnosi del nodo e il suo log. |

## 1. Dai un nome al nodo

**Impostazioni → Nome del nodo** → inserisci un nome, per esempio «Famiglia Rossi» o «Scuola n. 5» → **Salva**.

Il nome lo vedono gli utenti nell'app. Gli altri nodi della rete conoscono il nuovo nome dopo il riavvio del nodo (vedi sotto). Non si possono usare nomi che spacciano il nodo per un nodo del progetto: con le parole Nevod, admin, support, official e simili.

## 2. Decidi chi ammettere

**Impostazioni → Modalità di ammissione delle celle.** Un nodo nuovo funziona per impostazione predefinita **su invito**: ci si può registrare solo con un codice che hai dato tu. Di solito è proprio ciò che serve.

| Modalità nel pannello | Chi può registrarsi | Chi crea i codici di invito |
|---|---|---|
| `delegated` — solo con codice di invito (predefinita) | Solo con codice di invito. Senza codice il nodo non accetta la registrazione. | Tu nel pannello, e gli utenti a cui hai dato il diritto **Può invitare**. |
| `admin` — richiesta + la tua approvazione | Con il codice, subito. Senza codice l'app invia da sola una richiesta e mostra «In attesa di approvazione»; tu la approvi o la rifiuti nella pagina **Richieste di accesso**. | Solo tu, nel pannello. |
| `open` — senza codice | Chiunque conosca l'indirizzo del nodo. Adatta a una comunità aperta; tieni conto che poi dovrai riordinare a mano le registrazioni e i nomi occupati. | Il codice non serve. |

La modalità si applica subito.

## 3. Registrati sul tuo nodo

1. Nel pannello: **Inviti** → scegli la validità (1 ora, 24 ore o 7 giorni) → **+ Crea codice**. Compaiono un codice QR e un codice breve come `ABCD-EFGH`.
2. Sul telefono installa Nevod dall'App Store.
3. Inquadra il codice QR con la normale fotocamera del telefono. È un link: si apre la pagina di invito; tocca **Apri in Nevod**. L'app si apre con l'indirizzo del tuo nodo e il codice già compilati.
4. Inserisci il tuo nome e tocca **Inizia**.

Se inquadrare è scomodo, premi **Copia link** nel pannello e invialo a te stesso. Se «Apri in Nevod» non ha funzionato: nell'app tocca **Inizia a scrivere**, inserisci il nome, tocca **Hai un codice di invito?** e incolla il link nel campo del codice. Il codice breve al posto del link funziona solo quando nell'app è già impostato il tuo nodo.

> Se Nevod su questo telefono è già registrato su un altro nodo (per esempio su Nevod Open), l'invito non ti sposta da solo sul tuo nodo: l'app avvisa che prima devi reimpostare l'identità: **Profilo → Reimposta identità…**. La reimpostazione elimina per sempre la tua identità, i contatti, i messaggi sul telefono e la registrazione sul nodo precedente. Dopo, apri di nuovo il link di invito.

Ogni codice vale una sola volta. Creane uno per ogni persona; di più in [Invitare le persone](../node-invite/).

## 4. Decidi se il nodo è visibile nella rete

**Impostazioni → Visibilità in «Esplora la rete»**:

- `closed` (predefinita): il nodo non compare in «Esplora la rete» per gli utenti di altri nodi. Adatta a una famiglia, a un'organizzazione, a qualsiasi gruppo chiuso.
- `open`: il nodo compare in «Esplora la rete» e gli utenti di altri nodi possono trovarlo. Adatta a una comunità aperta. Il nodo è visibile finché è collegato alla rete, e solo a chi è già registrato su un nodo: prima della registrazione l'app mostra solo i nodi del progetto.

Questa scelta non apre la registrazione: chi ammettere lo decide sempre la modalità di ammissione delle celle (passo 2). L'anello dorato di nodo verificato in «Esplora la rete» per ora ce l'hanno solo i nodi del progetto Nevod.

Questa impostazione, come il nome del nodo per gli altri nodi, si applica dopo il riavvio del nodo. Sul server, nella cartella `/opt/nevod/installer/docker`:

```
docker compose restart nevod_node
```

## 5. Verifica il nodo

**Diagnostica → Verifica.** In pochi secondi il nodo mostra se è tutto a posto: se il suo codice è aggiornato, se le impostazioni coincidono con il database, se ci sono problemi di configurazione, se il nodo è raggiungibile dall'esterno.

La raggiungibilità dall'esterno il nodo la verifica tramite gli altri nodi della rete. Finché il tuo nodo non è collegato a nessuno, questa riga mostra «Nessun peer noto»: è normale. Il collegamento alla rete è il passo successivo, ed è importante: senza, i telefoni non riceveranno notifiche mentre l'app è chiusa. Vedi [Collegarsi alla rete Nevod](../node-network/).

## 6. Facoltativo: altri amministratori

**Sicurezza → Aggiungi / cambia password**: ogni amministratore avrà il proprio nome utente e la propria password, e potrai revocarli senza cambiare la password principale di `.env`. La password principale resta come accesso di riserva nel caso le altre vadano perse.
