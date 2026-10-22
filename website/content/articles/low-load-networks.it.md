# Reti distribuite di dati a basso carico: concetto, classificazione e analisi comparativa

**Autore del concetto:** Kolpakov Andrey

**Versione:** 30 settembre 2026

**Materiali correlati:** [Manifesto Zero Knowledge Infrastructure](/it/manifesto/), [confronto tra reti](/it/compare/#low-load).

---

## Sommario

L'articolo introduce il concetto di *rete distribuita di dati a basso carico*: una rete in cui il
carico di ogni nodo (traffico, archiviazione, stato di servizio) è limitato dalla cerchia di
partecipanti di quel nodo e non cresce con la crescita della rete nel suo insieme. Si mostra che
le classificazioni del carico usate nella teoria delle comunicazioni (fattore di utilizzo,
erlang, i punti del «ginocchio» (knee) e della «scogliera» (cliff) sulla curva del throughput in funzione del carico, classi di qualità del servizio)
descrivono lo *stato* di una rete in un dato momento e non una proprietà della sua architettura,
e perciò non distinguono le reti secondo questo tratto. Si propongono sei tratti di una rete a
basso carico e una classificazione LL-0…LL-3 in base all'andamento asintotico del carico per
nodo. Si confrontano quindici reti, da FidoNet (1984) a Nevod (2026), indicandone i predecessori
nella letteratura: reti friend-to-friend (F2F), reti tolleranti ai ritardi (DTN), tabelle hash
distribuite, software local-first e reti comunitarie (community networks).

**Parole chiave:** reti distribuite, decentralizzazione, carico per nodo, scalabilità, F2F, DTN,
reti peer-to-peer, messaggistica, Zero Knowledge Infrastructure.

---

## 1. Introduzione

La maggior parte degli odierni servizi di messaggistica è centralizzata: l'intera rete è servita
dai server di un'unica azienda, e il carico di quei server cresce con il numero di utenti. Le
alternative decentralizzate (reti federate, overlay peer-to-peer, reti di anonimato) distribuiscono
la *proprietà* dell'infrastruttura ma, come mostrato più avanti, di norma non distribuiscono il
*carico*: un server di federazione o un nodo overlay trasporta traffico, cronologia e stato di
servizio prodotti dagli utenti altrui, e il suo carico torna a crescere con la dimensione della
rete o della sua parte più popolare.

Lo scopo del lavoro è isolare la classe di reti in cui il carico di un nodo è determinato solo dalla sua cerchia: gli utenti e gli agenti software (bot, agenti di IA, servizi) per cui esso è il nodo di casa; definirla, proporre una classificazione misurabile e confrontare le reti esistenti secondo questo tratto.

## 2. Il carico nelle reti di dati: concetti esistenti

### 2.1 Fattore di utilizzo

Nella teoria delle code il carico di un canale o di un nodo è caratterizzato dal fattore di
utilizzo ρ = λ/μ, il rapporto tra tasso di arrivo e tasso di servizio [1]. Per ρ → 1 la lunghezza
della coda e il ritardo crescono senza limite; con ρ > 1 il sistema è sovraccarico. In pratica si
usano livelli indicativi: utilizzo basso (ρ < ~0,3), moderato (0,3–0,7), alto (0,7–0,9),
saturazione e sovraccarico; gli operatori dimensionano di solito i collegamenti con un margine
fino a ~70–80 % nell'ora di punta. Queste soglie sono linee guida ingegneristiche, non uno standard
unico.

### 2.2 Teletraffico: erlang e ora di punta

In telefonia l'intensità di traffico si misura in erlang (1 Erl è un canale occupato in modo
continuo) [2]; il dimensionamento si basa sull'ora di punta; si distinguono traffico offerto,
smaltito e perso, e il grado di servizio si fissa come probabilità di blocco ammissibile (formule
di Erlang B e C) [1, 2].

### 2.3 Come una rete reagisce all'aumento del carico: il «ginocchio» e la «scogliera»

Jain, Ramakrishnan e Chiu [3] descrissero tre regioni di funzionamento di una rete: prima del
«ginocchio» il throughput cresce con il carico e il ritardo è basso; tra il «ginocchio» e la
«scogliera» il throughput quasi non cresce mentre il ritardo sale rapidamente; oltre la
«scogliera» arrivano congestione e collasso. Nel «ginocchio» il rapporto tra throughput e ritardo (la «potenza» della rete) raggiunge il massimo; su questa distinzione si basano l'evitamento della congestione (congestion avoidance: mantenere il funzionamento vicino al «ginocchio») e il controllo della congestione (congestion control: impedire la caduta dalla «scogliera»). Il controllo della congestione di TCP si basa su
queste idee [4].

### 2.4 Classi di traffico e di qualità del servizio

L'architettura Differentiated Services [5] introduce comportamenti di inoltro (Expedited
Forwarding EF, Assured Forwarding AF, Best Effort BE); la Raccomandazione ITU-T Y.1541 [6] definisce
classi di qualità 0–5 per le reti IP secondo ritardo, jitter e perdite. Sono classificazioni dei
*requisiti* di consegna, non del carico.

### 2.5 Regimi di carico: dal sottocarico al collasso

I regimi di funzionamento di una rete secondo il carico sono descritti nelle norme e nei lavori
classici:

| Regime | Dove è definito | Significato |
|---|---|---|
| Sottocarico (underutilization) | descrittivo, non definito nelle norme | i collegamenti sono visibilmente inattivi; spesso è una riserva di capacità voluta (overprovisioning) |
| Carico normale | ITU-T E.500 [36] | periodi di attività frequenti in cui le aspettative degli utenti devono essere soddisfatte; per esso si fissano gli obiettivi di grado di servizio |
| Carico elevato | ITU-T E.500 [36] | periodi di picco poco frequenti: le aspettative possono non essere soddisfatte, ma le prestazioni devono restare sufficienti a evitare che la congestione si diffonda nella rete |
| Sovraccarico | ITU-T E.412 [37]; considerato nelle norme GOST sulle reti di comunicazione [39] | il traffico supera la capacità della rete; entrano in gioco misure di gestione: controllo automatico della congestione, riserva di circuiti, reinstradamento |
| Collasso da congestione (congestion collapse) | RFC 896, J. Nagle, 1984 [38] | ogni pacchetto viene inviato più volte e il throughput utile scende quasi a zero; osservato per la prima volta nell'ottobre 1986, quando la dorsale NSFnet passò da 32 kbit/s a 40 bit/s |

Non esiste un termine consolidato per una rete «pienamente carica»; il livello per cui una rete è
dimensionata corrisponde al «carico normale» di E.500.

Tutti questi regimi sono **stati** di una rete in un dato momento: la stessa rete è sottocarica al
mattino, in carico normale la sera e sovraccarica durante un guasto. L'asse dei regimi e l'asse
delle classi architetturali introdotto più avanti sono indipendenti: anche una rete di classe LL-0
può andare in sovraccarico, ad esempio se un nodo funziona su un collegamento debole.

### 2.6 Scalabilità del carico per nodo

Nella letteratura sui sistemi distribuiti il costo di un nodo si valuta in modo asintotico in
funzione del numero di partecipanti N: la diffusione a tutti i nodi costa O(N) per messaggio; le
tabelle hash distribuite (Chord [7], Kademlia [8]) costano O(log N) per instradamento e tabella dei
vicini. Si trova anche l'affermazione che nei sistemi peer-to-peer il carico massimo per nodo non
cresce con il numero di nodi, perché i nuovi nodi portano più risorse di quante ne consumino [9],
ma si tratta di un *bilanciamento statistico* di un carico fatto di richieste altrui.

### 2.7 Conclusione

Le classificazioni 2.1–2.5 rispondono alla domanda «quanto è carica la rete *adesso*»; secondo
esse la stessa rete è a volte poco e a volte molto carica. L'espressione russa «rete poco carica» (малонагруженная сеть) si usa in pratica proprio in questo senso descrittivo (una rete o una
macchina con basso utilizzo) e non è un termine che designi una classe architetturale. Nella
telefonia su cavo la parola «carico» ha perfino un terzo significato: la «linea caricata» con
bobine di induttanza (pupinizzazione). Solo l'asse 2.6 riguarda una *proprietà dell'architettura*,
e non esiste una classificazione standard delle reti secondo esso.

## 3. Reti distribuite: panoramica degli approcci

**Servizi centralizzati** (WhatsApp, 2009; Telegram, 2013; Signal, 2014 [10]): la cifratura
end-to-end dei contenuti può essere robusta, ma server, account e metadati sono nelle mani di
un'unica organizzazione; il carico dei server cresce con l'intero pubblico.

**Reti federate**: posta elettronica, Matrix (2014) [11], ActivityPub/Mastodon (2016;
Raccomandazione W3C 2018) [12]. La proprietà è distribuita tra i server, ma il carico di un server
cresce con i suoi collegamenti esterni: in Matrix la cronologia di una stanza grande viene
replicata su ogni server partecipante, in ActivityPub la distribuzione cresce con il numero di
follower.

**Overlay peer-to-peer e tabelle hash distribuite**: Freenet (2001) [13], Chord [7], Kademlia [8].
I nodi sono pari e il carico è O(log N), ma un nodo archivia e instrada dati di sconosciuti.

**Reti friend-to-friend (F2F).** Il termine fu proposto da D. Bricklin nel 2000 [14]: un nodo si
collega solo ai nodi dei propri conoscenti. Esempi: Turtle (Popescu, Crispo, Tanenbaum, 2004) [15],
OneSwarm [16], la modalità «darknet» di Freenet, RetroShare, GNUnet; rientra qui anche
l'archiviazione su nodi fidati [17]. Il numero di connessioni di un nodo è limitato dal numero dei
suoi amici [18, 19], ma i messaggi percorrono catene di amici attraverso nodi non interessati, e
l'instradamento in queste reti resta un problema difficile [18, 19, 20]. **Le reti F2F sono il
predecessore più vicino del concetto proposto**: sono state le prime a limitare un nodo alla sua
cerchia di conoscenti, ma per numero di connessioni, non per carico.

**Reti overlay di anonimato** (onion routing): sviluppo delle reti di mix di D. Chaum (1981) [40] e dell'onion routing di D. Goldschlag, M. Reed e P. Syverson (1996) [41]; implementazioni: Tor (2002–2004) [21] e Session (2020) [22]. I nodi relay, gestiti da volontari o operatori, trasportano transito altrui in proporzione alla propria larghezza di banda.

**Reti tolleranti ai ritardi (DTN)**: l'architettura di Fall (2003) [23], RFC 4838 [24], Bundle
Protocol v7, RFC 9171 [25]: «memorizza e inoltra» in caso di interruzioni. Un'implementazione
storica dello stesso principio è FidoNet (1984) [26], una moderna è NNCP (2016) [27].

**Stack per qualsiasi mezzo e reti radio**: Reticulum (protocollo pubblicato nel 2016) e il
messenger LXMF [28]: funzionamento da pochi bit al secondo (LoRa, radio a pacchetto) fino a
internet, con cifratura predefinita; Meshtastic (2020) [29]: messaggi di testo tramite moduli radio
LoRa.

**Reti comunitarie** (community networks): Freifunk, Guifi.net [30]: reti create e gestite dagli stessi utenti.

**Software local-first** [31] e **Secure Scuttlebutt** (2014) [32]: i dati restano all'utente; in
SSB un nodo conserva i feed dei suoi amici e degli amici degli amici, e la sincronizzazione avviene
quando i nodi si incontrano.

**Relay**: Nostr (2020) [33]: semplici server relay, dei quali quelli popolari sono caricati
dall'intero pubblico.

## 4. Il concetto di rete distribuita a basso carico

### 4.1 Definizione

**Una rete distribuita di dati a basso carico** è una rete in cui ogni nodo serve una cerchia di
partecipanti piccola e naturalmente limitata e trasporta soprattutto il loro traffico. I nodi sono
pari e funzionano su hardware comune. La rete trasmette solo il necessario, tollera ritardi e
interruzioni dei collegamenti e non ha un centro il cui spegnimento o sequestro ne fermerebbe il
funzionamento.

Il concetto riguarda la *struttura* di una rete, non il suo carico in un dato momento (paragrafi
2.5, 2.7).

### 4.2 Tratti

1. **Cerchia propria**: il carico di un nodo cresce con la sua cerchia, le persone e gli agenti software che serve, non con la dimensione dell'intera rete. Il tratto principale.
2. **Hardware comune**: un computer di casa, un mini server o un router; non serve un data center.
3. **Economia di trasmissione**: prima testo e segnali, i dati voluminosi su richiesta.
4. **Tolleranza ai ritardi**: senza connessione il messaggio attende e viene trasmesso più tardi,
   anche su un canale lento.
5. **Nessun centro**: nessun singolo punto di guasto, blocco o sequestro.
6. **Cecità del nodo**: il nodo trasporta solo testo cifrato e non può leggerlo (il principio Zero
   Knowledge Infrastructure).

### 4.3 In che cosa differisce dai predecessori

| Concetto | Che cosa è limitato | In che cosa differisce |
|---|---|---|
| F2F [14–20] | il numero di connessioni del nodo, dalla cerchia di conoscenti | il transito lungo catene di conoscenti rimane; il carico non è limitato |
| DHT [7, 8] | la crescita del carico, da un logaritmo | il nodo trasporta dati di sconosciuti |
| DTN [23–25] | nulla sul carico | riguarda ritardi e interruzioni, non la ripartizione del carico |
| Local-first [31] | dove sono archiviati i dati: presso l'utente | riguarda la proprietà dei dati, non la rete |
| **Rete a basso carico** | **l'intero carico del nodo, dalla sua cerchia** | combinazione dei tratti 1–6; il tratto 1 è quello determinante |

## 5. Classificazione: classi LL

**La classe di carico di un nodo** è determinata dalla componente che cresce più rapidamente tra le tre: traffico trasportato, dati archiviati, stato di servizio mantenuto. N è il numero di partecipanti alla rete, k la dimensione della cerchia del nodo: il numero dei suoi utenti e agenti software. La notazione O(x) («O grande di x»; introdotta da P. Bachmann nel 1894 [42] e diffusa da E. Landau nel 1909 [43]) significa che una grandezza non cresce più rapidamente di x moltiplicato per una costante; per la classe LL-0 la stima del carico non contiene N, solo k.

| Classe | Carico del nodo | Definizione |
|---|---|---|
| **LL-0** | O(k) | il nodo trasporta, archivia e ricorda solo ciò che riguarda la sua cerchia; nessun transito altrui |
| **LL-1** | O(k) + altrui limitato | in più, transito o archiviazione per altri limitati indipendentemente da N (limite di salti, quote, vicini scelti dal nodo stesso) |
| **LL-2** | O(log N) | il carico cresce lentamente (tabelle hash distribuite) |
| **LL-3** | O(N) o non limitato dalla propria cerchia | il carico cresce con l'intera rete o dipende da quanti utenti esterni accedono al nodo (un server popolare, un relay) |

Una rete a basso carico in senso stretto è una rete di classe **LL-0**; LL-1 è quasi a basso carico.

## 6. Analisi comparativa

### 6.1 Tratti (1 = soddisfatto, ½ = in parte, 0 = no) e classi

| Rete | Anno | Cerchia propria | Hardware | Economia | Ritardi | Nessun centro | Nodo cieco | Classe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Secure Scuttlebutt [32] | 2014 | 1 | 1 | ½ | 1 | 1 | 0 | LL-0 |
| Briar [35] | 2018 | 1 | 1 | ½ | ½ | 1 | 1 | LL-0 |
| Nevod [34] | 2026 | 1 | 1 | ½ | ½ | 1 | 1 | LL-0 |
| FidoNet [26] | 1984 | 1 | 1 | 1 | 1 | 0 | 0 | LL-1 |
| NNCP [27] | 2016 | ½ | 1 | 1 | 1 | 1 | 1 | LL-1 |
| Reticulum / LXMF [28] | 2016 | ½ | 1 | 1 | 1 | 1 | 1 | LL-1 |
| Meshtastic [29] | 2020 | 0 | 1 | 1 | ½ | 1 | ½ | LL-1 |
| Tor [21] | 2002 | 0 | ½ | 0 | 0 | 1 | 1 | LL-3 |
| WhatsApp | 2009 | 0 | 0 | 0 | 0 | 0 | ½ | LL-3 |
| Telegram | 2013 | 0 | 0 | 0 | 0 | 0 | 0 | LL-3 |
| Matrix [11] | 2014 | 0 | ½ | 0 | 0 | ½ | ½ | LL-3 |
| Signal [10] | 2014 | 0 | 0 | 0 | 0 | 0 | ½ | LL-3 |
| Mastodon [12] | 2016 | 0 | ½ | 0 | 0 | ½ | 0 | LL-3 |
| Nostr [33] | 2020 | 0 | ½ | 0 | 0 | 1 | ½ | LL-3 |
| Session [22] | 2020 | 0 | ½ | 0 | ½ | 1 | 1 | LL-3 |

Note. Signal e WhatsApp ottengono ½ nel tratto 6: il contenuto è cifrato end-to-end, ma
l'organizzazione vede i metadati e gestisce i server. In Reticulum e NNCP i nodi intermedi
trasportano e conservano pacchetti altrui (tratto 1 = ½, classe LL-1). L'anno è la prima versione
pubblica (Reticulum: in sviluppo dal 2014; Signal: predecessori TextSecure/RedPhone, 2010; Briar: in
sviluppo dal 2011).

### 6.2 Osservazioni

- Per il tratto principale (classe LL) i più rigorosi sono Nevod, Briar e Secure Scuttlebutt
  (LL-0); Reticulum e NNCP appartengono a LL-1.
- Tutte le reti centralizzate e federate, così come le reti overlay di anonimato, sono LL-3:
  decentralizzare la proprietà non significa decentralizzare il carico.

## 7. Nevod come esempio della classe LL-0 e i suoi limiti

Nevod [34] è una rete di messaggistica costruita secondo il principio Zero Knowledge
Infrastructure: un nodo («node») serve solo i propri partecipanti e trasporta messaggi cifrati
senza accesso al loro contenuto; non esiste un centro; i nodi funzionano su hardware domestico o su
server a noleggio. La tabella di servizio dei nodi cresce con il numero di *nodi*, non di utenti,
ed è piccola.

Limiti a settembre 2026 (tratti non pienamente soddisfatti, nessuna verifica pratica):

- tratto 3: i contenuti multimediali sono trasmessi interi, senza anteprima né scaricamento su
  richiesta;
- tratto 4: i messaggi non consegnati sono conservati per 72 ore; funziona solo via internet;
- nessuna forward secrecy: i messaggi sono cifrati con la chiave a lungo termine del destinatario;
- un nodo vede i metadati di consegna (chi, a chi, quando);
- un prototipo funzionante senza utenti reali e senza audit indipendente; codice chiuso; app solo
  per iOS.

I tratti sono stati ricavati dai principi di Nevod, quindi il confronto lo favorisce in partenza;
il punteggio di Nevod riflette la sua architettura, non la maturità del prodotto.

## 8. Questioni aperte

1. Archiviazione per un destinatario a lungo offline: chi la conserva e per quanto, senza violare
   la classe LL-0.
2. Ricerca del percorso tra molti nodi senza un indice centrale.
3. È ammissibile un transito limitato (LL-1) per consegnare su canali lenti, e serve reciprocità
   («porti il traffico altrui, altri portano il tuo»)?
4. Quali componenti contano come carico: traffico, archiviazione, stato, consumo di energia, tempo
   dell'amministratore.
5. Una metrica formale della cerchia del nodo k e la sua misurazione su reti reali.

## 9. Conclusione

I concetti di carico della teoria delle comunicazioni descrivono lo stato di una rete, non una
proprietà della sua architettura. Il concetto proposto di rete distribuita a basso carico isola una
classe architetturale in cui il carico di un nodo è limitato dalla sua cerchia, e integra gli
approcci noti (F2F, DTN, tabelle hash distribuite, local-first, reti comunitarie) con una
combinazione di sei tratti. La classificazione LL-0…LL-3 rende il concetto misurabile e permette
di assegnare qualsiasi rete a una classe. La verifica pratica e una rassegna completa della
letteratura nelle banche dati chiuse (IEEE, ACM, eLibrary) sono i prossimi passi.

---

## Bibliografia

{{REFS}}

---

*Nota sul metodo.* La rassegna è stata svolta su fonti aperte; le banche dati a pagamento (IEEE
Xplore, testi completi della ACM Digital Library, Springer, eLibrary) non sono state consultate in
modo sistematico. I punteggi dei tratti e delle classi sono valutazioni esperte basate sulle
descrizioni pubbliche delle reti a settembre 2026.
