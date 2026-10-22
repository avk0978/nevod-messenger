# Italian content for nevod.network — same facts and structure as content_uk.py / content_en.py.

T = {
    "nav": {"index": "Home", "manifesto": "Manifesto ZKI", "compare": "Confronto", "security": "Sicurezza",
            "cities": "Per le città", "download": "Scarica", "about": "Il progetto"},
    "nav_support": "Supporto", "nav_privacy": "Privacy", "nav_terms": "Condizioni d'uso", "nav_node": "Il tuo nodo", "nav_source": "Codice sorgente",
    "footer_owner": "© 2026 Nevod · Kolpakov Andrey",
}

INDEX = """
<section class="hero"><div class="wrap">
<div class="eyebrow">Zero Knowledge Infrastructure</div>
<h1>Nevod: un messenger il cui sviluppatore è tecnicamente tagliato fuori dai tuoi dati</h1>
<p class="lead">Non per una promessa, né solo per la crittografia, ma per l'architettura. Lo sviluppatore non ha le tue chiavi, né una chiave master, né un server centrale, né un database degli utenti. Anche se qualcuno arriva con una richiesta, non c'è nulla da consegnare.</p>
<div class="btns"><a class="btn primary" href="/it/manifesto/">Leggi il manifesto ZKI</a><a class="btn ghost" href="/it/download/">Scarica</a></div>
</div></section>
<main><div class="wrap">
<h2>La crittografia è una serratura. ZKI significa che lo sviluppatore non ha la chiave</h2>
<p>La maggior parte dei messenger cifra i messaggi, ma l'azienda continua a gestire i server, a tenere il database degli utenti, a legare gli account ai numeri di telefono e a vedere chi parla con chi e quando. La crittografia protegge il contenuto in transito; tutto il resto resta in mano all'azienda.</p>
<p>Nevod è costruito secondo il principio della <b>Zero Knowledge Infrastructure</b>: l'infrastruttura è progettata in modo che il suo creatore non possa accedere ai contenuti, né volendolo né se costretto.</p>
<div class="grid">
<div class="card"><h3>🔑 Le chiavi le hai solo tu</h3><p>Le chiavi vengono create sul tuo dispositivo e non lo lasciano mai. Lo sviluppatore non ha copie, né chiave master, né backup.</p></div>
<div class="card"><h3>🌐 Un nodo proprio per chiunque</h3><p>Nessun server centrale: la rete è fatta di nodi indipendenti e nessuno ti impedisce di gestire il tuo. Non esiste un unico punto in cui si concentra tutto.</p></div>
<div class="card"><h3>📵 L'identità è una chiave, non un numero</h3><p>Nessun numero di telefono né e-mail. Lo sviluppatore non tiene un registro delle persone e non sa chi sei.</p></div>
<div class="card"><h3>📭 Nulla da consegnare</h3><p>Se qualcuno chiede una conversazione, lo sviluppatore non ha nulla da dare. Non perché la nasconda, ma perché non ce l'ha.</p></div>
</div>
<p class="note">ZKI è il fondamento dello sviluppo di Nevod. Ogni decisione tecnica viene verificata con una sola domanda: il creatore dell'infrastruttura ottiene accesso ai contenuti? <a href="/it/manifesto/">Manifesto della Zero Knowledge Infrastructure →</a></p>
<h2>Rete distribuita a basso carico</h2>
<p>Il carico di ogni nodo Nevod è limitato dalla sua cerchia (famiglia, casa, squadra), non dalle dimensioni dell'intera rete: un milione di nuovi utenti altrove non aggiunge un solo byte al tuo nodo. Il nodo funziona su hardware domestico comune, la rete non ha un centro e il nodo stesso trasporta solo testo cifrato.</p>
<p><a href="/it/compare/#low-load">Un confronto di Nevod con altre 14 reti, da FidoNet a Signal →</a></p>
<h2>Cosa fa Nevod</h2>
<div class="grid">
<div class="card"><h3>🔒 Crittografia end-to-end</h3><p>Ogni messaggio, foto, messaggio vocale e chiamata è cifrato sul telefono. I nodi vedono solo dati cifrati.</p></div>
<div class="card"><h3>📞 Chiamate e video</h3><p>Chiamate vocali e video, messaggi vocali, foto, video e file.</p></div>
<div class="card"><h3>🏙️ Comunicazione senza internet</h3><p>L'architettura può trasmettere messaggi su qualsiasi canale disponibile, anche all'interno di una città senza accesso a internet.</p></div>
<div class="card"><h3>🛡️ Protezione dagli abusi</h3><p>Blocco e segnalazioni, account ufficiali verificati, protezione contro chi si spaccia per l'amministrazione.</p></div>
</div>
<h2>Stato del progetto</h2>
<div class="tbl"><table class="status">
<tr><th style="width:34%">Ambito</th><th>Stato</th></tr>
<tr><td>App per iPhone</td><td>Test chiuso (TestFlight); pubblicazione su App Store in preparazione</td></tr>
<tr><td>App per Android</td><td>In sviluppo</td></tr>
<tr><td>Nodi della rete</td><td>Operativi, installabili con Docker</td></tr>
<tr><td>Lingue dell'app</td><td>8: ucraino, inglese, russo, tedesco, turco, spagnolo, italiano, francese</td></tr>
</table></div>
</div></main>
"""

MANIFESTO = """
<main><div class="wrap">
<div class="eyebrow" style="color:#8A6A00">Manifesto</div>
<h1>Zero Knowledge Infrastructure</h1>
<p><b>La rete che stai guardando, Nevod, è la prima implementazione completa di un'unica idea: chi costruisce l'infrastruttura di comunicazione non deve poter vedere tecnicamente ciò che vi passa attraverso.</b></p>
<h2>La posizione</h2>
<p>Io costruisco strumenti.<br>Non controllo come vengono usati.<br>Non ho accesso ai dati.<br>E questa è l'architettura del software!</p>
<p>Non è una privacy policy. Non è una promessa di marketing. È un'impossibilità tecnica inserita nelle fondamenta.</p>
<h2>Il principio del coltello</h2>
<p>Chi fabbrica un coltello non è responsabile di come viene usato. Con un coltello si può tagliare il pane, oppure no. È la scelta di chi lo impugna, non di chi lo ha forgiato.</p>
<p>La stessa logica vale per l'infrastruttura di comunicazione.</p>
<p>Io costruisco il canale. Ciò che vi passa non è affar mio.<br>Non perché non mi importi. Perché <b>non deve</b> esserlo.</p>
<p>Il diritto alla comunicazione privata è un diritto umano fondamentale. L'infrastruttura di comunicazione non deve essere un punto di sorveglianza.</p>
<h2>Cosa significa tecnicamente</h2>
<p>Le chiavi di cifratura vengono generate sul dispositivo dell'utente.<br>Non lasciano mai quel dispositivo.<br>Non ho server che conservano chiavi.<br>Non ho una chiave master.<br>Non ho backup.</p>
<p>Se qualcuno viene a chiedermi una conversazione, non ho nulla da dargli. Non perché la nasconda, ma perché <b>non ce l'ho</b>.</p>
<p>Non è una promessa. È una garanzia architetturale.</p>
<h2>Cosa significa come posizione</h2>
<p>Non voglio guadagnare sui dati personali delle persone. Non voglio sapere di cosa parlano. Non voglio essere un intermediario a cui si possa notificare un'ingiunzione.</p>
<p>I ricavi vengono dallo strumento, non dal contenuto. Vendo il martello, non ciò che ci si costruisce.</p>
<h2>Gli agenti IA e la prossima frontiera</h2>
<p>Il mondo si sta muovendo verso agenti IA autonomi. Gli agenti parleranno tra loro: negozieranno, si delegheranno compiti, si scambieranno dati.</p>
<p>La domanda diventa: chi vede queste conversazioni?</p>
<p>La risposta attuale del settore è la piattaforma. OpenAI vede cosa fanno gli agenti su OpenAI. Google vede cosa fanno gli agenti su Google. L'operatore dell'orchestratore vede tutto.</p>
<p>La mia risposta: <b>nessuno</b>.</p>
<p>Se gli agenti comunicano attraverso un'infrastruttura ZKI, la loro corrispondenza è cifrata end-to-end. L'operatore della piattaforma vede solo l'instradamento. Il contenuto della trattativa resta tra gli agenti.</p>
<div class="tbl"><table>
<tr><th>Agente A</th><th style="width:30%">⇄ cifrato end-to-end ⇄</th><th>Agente B</th></tr>
<tr><td>Nodo Nevod — vede solo testo cifrato</td><td></td><td>Nodo Nevod — vede solo testo cifrato</td></tr>
<tr><td>Operatore — non vede nulla</td><td></td><td>Operatore — non vede nulla</td></tr>
</table></div>
<p><i>«Gestisco un servizio usato da agenti IA. Non so cosa abbiano concordato con il tuo agente.»</i></p>
<p>Non è sottrarsi alla responsabilità. È un'architettura per un mondo in cui gli agenti sono attori indipendenti.</p>
<h2>Perché conta proprio ora</h2>
<p>Nel 2025–2026:</p>
<ul><li>Gli agenti IA iniziano ad agire in modo autonomo</li><li>Agenti di aziende diverse iniziano a interagire</li><li>Nessuno ha deciso chi vede le trattative tra agenti</li><li>Nessuno ha deciso chi risponde di ciò che un agente ha «detto»</li></ul>
<p>ZKI risponde:</p>
<ul><li>Le trattative sono cifrate: l'operatore non le vede</li><li>La responsabilità delle azioni di un agente ricade su chi lo esegue</li><li>L'infrastruttura di comunicazione resta neutrale, come una linea telefonica</li></ul>
<h2>Precedenti</h2>
<div class="tbl"><table>
<tr><th style="width:30%">Strumento</th><th>Posizione</th></tr>
<tr><td>Tor Project</td><td>«Abbiamo costruito uno strumento per l'anonimato. Non vediamo il traffico.»</td></tr>
<tr><td>Signal Foundation</td><td>«Le chiavi sono degli utenti. Non abbiamo nulla da consegnare.»</td></tr>
<tr><td>ProtonMail</td><td>«Crittografia a conoscenza zero. Non possiamo leggere la tua posta.»</td></tr>
<tr><td>Fornitori di VPN</td><td>«Forniamo il tunnel. Il contenuto non è nostro.»</td></tr>
<tr><td>Wallet hardware</td><td>«Le chiavi sono sul dispositivo. Non ne abbiamo copia.»</td></tr>
</table></div>
<p>Tutte queste posizioni hanno superato il vaglio giuridico nella maggior parte dei paesi democratici. ZKI è la stessa posizione, portata al livello di una filosofia di progettazione.</p>
<h2>Cosa sto costruendo</h2>
<p><b>Nevod</b> è la prima implementazione del principio ZKI come rete completa. Non è un prodotto. È un protocollo.</p>
<p>Può essere la base per:</p>
<ul><li>Messenger</li><li>Archiviazione di file</li><li>Sistemi di voto</li><li>Dead man's switch</li><li>Protocolli per agenti IA</li><li>Infrastruttura aziendale</li></ul>
<p>Un unico principio ovunque: <b>il creatore dell'infrastruttura è tecnicamente tagliato fuori dal suo contenuto</b>.</p>
<p style="margin-top:2em"><i>Aprile 2026</i></p>
<p><b>Kolpakov Andrey</b></p>
<p class="note">© 2026. Quando citi questo manifesto o vi fai riferimento, includi un link a <a href="https://nevod.network">nevod.network</a>. Originale inglese: <a href="/manifesto/">nevod.network/manifesto</a>.</p>
</div></main>
"""

COMPARE = """
<main><div class="wrap">
<h1>Nevod e gli altri messenger</h1>
<p>La maggior parte dei messenger moderni cifra i messaggi. La differenza non sta nella presenza della crittografia, ma in <b>ciò che resta in mano all'azienda</b>: server, database degli utenti, numeri di telefono, rubrica, metadati, e quanto di tutto ciò le si può chiedere.</p>
<p class="note">Nevod applica il principio della <a href="/it/manifesto/">Zero Knowledge Infrastructure</a>: lo sviluppatore è tagliato fuori dai dati degli utenti dall'<b>architettura</b>, non solo dalla crittografia. Le informazioni sugli altri messenger si basano sulle loro descrizioni pubbliche aggiornate al 2026 e possono cambiare.</p>
<div class="tbl"><table>
<tr><th style="width:24%"></th><th>Nevod</th><th>Signal</th><th>Telegram</th><th>WhatsApp</th></tr>
<tr><td>Chi può tecnicamente leggere una chat normale</td><td>Solo i partecipanti</td><td>Solo i partecipanti</td><td>Chat normali e gruppi: i server di Telegram (end-to-end solo nelle «chat segrete» uno a uno)</td><td>Solo i partecipanti</td></tr>
<tr><td>Server centrali dell'azienda</td><td>No: nodi indipendenti che chiunque può gestire</td><td>Sì</td><td>Sì</td><td>Sì, di Meta</td></tr>
<tr><td>Legato a un numero di telefono</td><td>No: l'identità è una chiave</td><td>Sì (il numero può essere nascosto dietro un nome utente)</td><td>Sì</td><td>Sì</td></tr>
<tr><td>Caricamento della rubrica</td><td>No: i contatti si aggiungono con scheda o QR</td><td>Individuazione privata dei contatti</td><td>Sì, se consentito</td><td>Sì, se consentito</td></tr>
<tr><td>Database degli utenti presso l'azienda</td><td>Nessuno centrale: ogni nodo conosce solo i propri utenti</td><td>Minimo</td><td>Sì</td><td>Sì</td></tr>
<tr><td>Cosa può consegnare l'azienda su richiesta</td><td>Lo sviluppatore non ha nulla da dare: né chiavi, né messaggi, né database</td><td>Secondo i suoi report: data di creazione dell'account e dell'ultima connessione</td><td>Secondo la sua policy: in alcuni casi indirizzo IP e numero di telefono</td><td>Metadati dell'account, secondo la sua policy</td></tr>
<tr><td>Backup delle chat nel cloud</td><td>Nessuno: chiavi e cronologia esistono solo sul dispositivo (perso il telefono, persa la cronologia)</td><td>Facoltativi; cifrati con una chiave che ha solo l'utente</td><td>Non servono: le chat normali sono già conservate sui server di Telegram</td><td>Su iCloud / Google Drive; senza crittografia end-to-end per impostazione predefinita (va attivata manualmente)</td></tr>
<tr><td>Punto unico di guasto o di blocco</td><td>No: i nodi sono indipendenti</td><td>Sì</td><td>Sì</td><td>Sì</td></tr>
<tr><td>Funzionamento senza internet all'interno di una città</td><td>Parte dell'architettura (rete cittadina, Wi-Fi mesh, radio)</td><td>No</td><td>No</td><td>No</td></tr>
<tr><td>Modello di business</td><td>Sullo strumento, non sui dati</td><td>Donazioni (non profit)</td><td>Pubblicità e Premium</td><td>Servizi business di Meta</td></tr>
<tr><td>Codice aperto</td><td>Non ancora: chiuso fino alla versione di produzione</td><td>Sì</td><td>In parte (client)</td><td>No</td></tr>
</table></div>
<h2>Perché «solo crittografia» non basta</h2>
<p>La crittografia end-to-end protegge il contenuto di un messaggio in transito. Ma se un'azienda gestisce tutti i server, tiene un database degli account per numero di telefono e vede chi parla con chi e quando, conserva il potere sul sistema: può essere costretta, violata o bloccata, e un aggiornamento dell'app può cambiare le regole.</p>
<p>ZKI pone un'altra domanda: <b>cosa può ottenere, anche solo in teoria, il creatore dell'infrastruttura?</b> In Nevod la risposta è nell'architettura: le chiavi non lasciano mai il dispositivo, non esistono chiave master né backup, non c'è un server centrale né un registro delle persone per numero di telefono.</p>
<h2 id="low-load">Rete distribuita a basso carico: un confronto</h2>
<p>Valutiamo le reti secondo sei tratti di una rete distribuita a basso carico: il carico di ogni nodo è limitato dalla sua cerchia di persone, non dalle dimensioni dell'intera rete. I tratti derivano dai principi stessi di Nevod, quindi il confronto lo favorisce in partenza.</p>
<ol>
<li>Cerchia propria: il carico di un nodo cresce con la sua cerchia (famiglia, casa, squadra), non con l'intera rete.</li>
<li>Hardware comune: un computer di casa, un mini server o un router; non serve un data center.</li>
<li>Economia: prima testo e segnali, i dati pesanti su richiesta.</li>
<li>Tolleranza ai ritardi: senza connessione il messaggio aspetta e parte dopo, anche su un canale lento.</li>
<li>Nessun centro: nessun singolo punto di guasto, blocco o sequestro.</li>
<li>Nodo cieco: il nodo trasporta solo testo cifrato e non può leggerlo.</li>
</ol>
<p class="note">1: sì, ½: in parte, 0: no. Anno: prima versione pubblica. Classe: LL-0, il carico del nodo è limitato dalla sua cerchia; LL-1, in più transito altrui limitato; LL-3, il carico cresce con l'intera rete o dipende da utenti esterni. Di più: <a href="/it/publications/low-load-networks/">l'articolo</a>.</p>
<div class="tbl"><table>
<tr><th>Rete</th><th>Anno</th><th>Cerchia propria</th><th>Hardware comune</th><th>Economia</th><th>Ritardi</th><th>Nessun centro</th><th>Nodo cieco</th><th>Classe</th></tr>
<tr><td>Secure Scuttlebutt</td><td>2014</td><td>1</td><td>1</td><td>½</td><td>1</td><td>1</td><td>0</td><td>LL-0</td></tr>
<tr><td>Briar</td><td>2018</td><td>1</td><td>1</td><td>½</td><td>½</td><td>1</td><td>1</td><td>LL-0</td></tr>
<tr><td><b>Nevod</b></td><td>2026</td><td>1</td><td>1</td><td>½</td><td>½</td><td>1</td><td>1</td><td>LL-0</td></tr>
<tr><td>FidoNet</td><td>1984</td><td>1</td><td>1</td><td>1</td><td>1</td><td>0</td><td>0</td><td>LL-1</td></tr>
<tr><td>NNCP</td><td>2016</td><td>½</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>LL-1</td></tr>
<tr><td>Reticulum / LXMF</td><td>2016</td><td>½</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>LL-1</td></tr>
<tr><td>Meshtastic</td><td>2020</td><td>0</td><td>1</td><td>1</td><td>½</td><td>1</td><td>½</td><td>LL-1</td></tr>
<tr><td>Tor</td><td>2002</td><td>0</td><td>½</td><td>0</td><td>0</td><td>1</td><td>1</td><td>LL-3</td></tr>
<tr><td>WhatsApp</td><td>2009</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>½</td><td>LL-3</td></tr>
<tr><td>Telegram</td><td>2013</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>LL-3</td></tr>
<tr><td>Matrix</td><td>2014</td><td>0</td><td>½</td><td>0</td><td>0</td><td>½</td><td>½</td><td>LL-3</td></tr>
<tr><td>Signal</td><td>2014</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>½</td><td>LL-3</td></tr>
<tr><td>Mastodon</td><td>2016</td><td>0</td><td>½</td><td>0</td><td>0</td><td>½</td><td>0</td><td>LL-3</td></tr>
<tr><td>Nostr</td><td>2020</td><td>0</td><td>½</td><td>0</td><td>0</td><td>1</td><td>½</td><td>LL-3</td></tr>
<tr><td>Session</td><td>2020</td><td>0</td><td>½</td><td>0</td><td>½</td><td>1</td><td>1</td><td>LL-3</td></tr>
</table></div>
<p>Signal e WhatsApp ottengono ½ per la cecità: il contenuto è cifrato end-to-end, ma l'azienda vede i metadati e gestisce i server. In Reticulum e NNCP i nodi intermedi trasportano e conservano pacchetti altrui. Nevod per ora invia i contenuti multimediali per intero, conserva i messaggi non consegnati per 72 ore e funziona solo via internet.</p>
<h3>Alla prova dei fatti</h3>
<div class="tbl"><table>
<tr><th>Rete</th><th>Anno</th><th>Per persone comuni</th><th>Maturità</th><th>Audit indipendente</th></tr>
<tr><td>Reticulum / LXMF</td><td>2016</td><td>no, per appassionati</td><td>comunità attiva</td><td>no</td></tr>
<tr><td>NNCP</td><td>2016</td><td>no, strumento da riga di comando</td><td>di nicchia</td><td>no</td></tr>
<tr><td><b>Nevod</b></td><td>2026</td><td>sì: iPhone/iPad, messaggi, contenuti multimediali, chiamate</td><td>in test, ancora nessun utente reale</td><td>no</td></tr>
<tr><td>Briar</td><td>2018</td><td>sì, ma senza chiamate; Android e desktop</td><td>maturo</td><td>sì (Cure53, 2017)</td></tr>
<tr><td>Signal</td><td>2014</td><td>sì</td><td>molto maturo</td><td>sì, più volte</td></tr>
</table></div>
<p>Per il tratto principale, Nevod appartiene alla classe LL-0 insieme a Briar e Secure Scuttlebutt; Reticulum e NNCP, vicini negli altri tratti, appartengono a LL-1. La differenza di Nevod è altrove: tra queste reti è l'unico pensato come messenger completo per persone comuni, con contenuti multimediali, chiamate e un'app per iPhone. Ma è giovane: ancora nessun utente reale, nessun audit indipendente, solo iOS. La strada verso sei su sei: contenuti multimediali su richiesta e consegna senza internet su canali lenti.</p>
<h2>Cosa riconosciamo</h2>
<ul>
<li>Un nodo tecnicamente elabora solo i dati di consegna — quale pacchetto cifrato va a chi — e non vede mai il contenuto. Nessuno ti impedisce di gestire un nodo tuo: così anche quei dati di consegna restano a te.</li>
<li>Il protocollo di Signal è aperto e ampiamente verificato: lo riconosciamo come un punto di forza. Il codice di Nevod per ora è chiuso; è prevista la sua apertura.</li>
</ul>
</div></main>
"""

SECURITY = """
<main><div class="wrap">
<h1>Sicurezza e crittografia</h1>
<p class="note">La crittografia è solo una parte della protezione. Il fondamento di Nevod è l'architettura della <a href="/it/manifesto/">Zero Knowledge Infrastructure</a>, in cui lo sviluppatore non ha accesso alle chiavi né ai dati degli utenti.</p>
<h2>Come sono protetti i tuoi messaggi</h2>
<p>Nevod usa la crittografia end-to-end: un messaggio viene cifrato sul tuo dispositivo e decifrato solo su quello del destinatario. Il nodo che lo trasporta vede solo dati cifrati e le informazioni di servizio necessarie alla consegna, mai il contenuto.</p>
<div class="tbl"><table>
<tr><th style="width:38%">Cosa</th><th>Come</th></tr>
<tr><td>Cifratura dei messaggi</td><td>CryptoKit, la libreria crittografica di sistema di Apple: scambio di chiavi X25519, SHA-256, cifrario ChaCha20-Poly1305</td></tr>
<tr><td>Firme</td><td>CryptoKit: Ed25519</td></tr>
<tr><td>Prova d'identità alla connessione a un nodo</td><td>Protocollo a conoscenza zero di Schnorr su CryptoKit (Curve25519, SHA-256/512) e un'unica operazione aritmetica modulare implementata in Nevod stesso</td></tr>
</table></div>
<p>Il mittente crea una nuova chiave monouso per ogni messaggio. La chiave del destinatario è a lungo termine: se venisse rubata dal suo dispositivo, potrebbero essere decifrati anche messaggi intercettati in precedenza e a lui destinati. Per questo è importante proteggere il dispositivo stesso: un codice di accesso e un iOS aggiornato.</p>
<p>Il protocollo di Schnorr ti permette di dimostrare a un nodo che possiedi la tua chiave senza inviarla né rivelarla.</p>
<h2>Se perdi il telefono</h2>
<p>Le tue chiavi, i contatti e la cronologia dei messaggi sono conservati solo sul tuo dispositivo. Non si trovano nei backup di iCloud o del computer, né sui nodi, né presso lo sviluppatore. Per questo, se il telefono viene perso, si rompe o viene ripristinato, non è possibile recuperarli. Anche eliminare l'app cancella la cronologia.</p>
<p>Il trasferimento su un nuovo dispositivo non è ancora disponibile. Su un nuovo telefono creerai una nuova identità e i tuoi contatti avranno bisogno della tua nuova scheda. È una conseguenza dell'architettura: una copia da cui recuperare le tue conversazioni sarebbe anche una copia a cui qualcuno potrebbe accedere.</p>
<h2>Il tuo nodo, le tue regole</h2>
<p>Lo sviluppatore non vede nulla. Un nodo elabora solo ciò senza cui la consegna non funziona: identificativi dei partecipanti, nomi scelti, token per le notifiche e quale pacchetto cifrato va a chi. Un nodo non vede mai il contenuto di messaggi, foto, messaggi vocali o chiamate.</p>
<p>Nessuno ti impedisce di creare un nodo tuo: per te, per la tua famiglia, per un'organizzazione o una comunità. Così anche i dati di consegna restano a te. <a href="/it/node/">Come gestire il tuo nodo →</a></p>
<h2>Controllo delle esportazioni e App Store</h2>
<p>Quando pubblica su App Store, lo sviluppatore dichiara se l'app usa crittografia soggetta al controllo delle esportazioni (EAR statunitensi, Categoria 5, Parte 2). Nevod dichiara di no, ed ecco perché:</p>
<ul>
<li><b>Tutto ciò che nasconde il contenuto dei messaggi è crittografia di sistema di Apple (CryptoKit).</b> Le app che usano solo la crittografia integrata nel sistema operativo di Apple rientrano in un'esenzione e non richiedono documentazione di esportazione.</li>
<li><b>L'implementazione propria di Nevod — un'unica operazione aritmetica nel protocollo di Schnorr — serve solo a dimostrare l'identità.</b> Il controllo delle esportazioni riguarda la crittografia finalizzata alla riservatezza. La crittografia usata solo per autenticazione, firme e integrità ne è esclusa.</li>
</ul>
<p>Per questo Nevod non richiede documentazione di esportazione, compresa la distribuzione in Francia.</p>
<p><i>Questa è la nostra interpretazione delle norme vigenti, non un parere legale.</i></p>
</div></main>
"""

CITIES = """
<section class="hero"><div class="wrap">
<div class="eyebrow">Per le città</div>
<h1>Comunicazione per una città senza internet né data center</h1>
<p class="lead">Ogni città moderna dipende dai data center e dai collegamenti dorsali. L'architettura di Nevod può trasmettere messaggi cifrati su qualsiasi canale disponibile, quindi su di essa si può costruire una rete di comunicazione cittadina di riserva.</p>
</div></section>
<main><div class="wrap">
<h2>Quattro livelli di comunicazione</h2>
<div class="tbl"><table>
<tr><th style="width:24%">Livello</th><th>Cosa usa</th><th style="width:16%">Portata</th><th style="width:20%">Cosa trasporta</th></tr>
<tr><td>1. Nodi cittadini</td><td>Reti dei provider senza uscita verso internet</td><td>Tutta la città</td><td>Tutto, all'interno della città</td></tr>
<tr><td>2. Wi-Fi mesh</td><td>Router comuni nei «punti di resilienza»: rifugi, scuole, centri di assistenza</td><td>Isolato–quartiere</td><td>Tutto, chiamate comprese</td></tr>
<tr><td>3. Collegamenti radio</td><td>Radiomodem direzionali in linea di vista</td><td>10–20 km</td><td>Tutto, chiamate comprese</td></tr>
<tr><td>4. LoRa</td><td>Moduli radio a basso costo</td><td>1–10+ km</td><td>Solo brevi testi</td></tr>
</table></div>
<p>Per le persone è lo stesso Nevod: l'app sceglie da sola il canale disponibile.</p>
<h2>Un punto di resilienza</h2>
<p>Un kit di apparecchiature economiche e reperibili in commercio: alcuni router con software aperto, un piccolo server di nodo, alimentazione di riserva e, se serve, un collegamento radio verso altri quartieri e un modulo LoRa per brevi testi. Non c'è nulla da inventare.</p>
<h2>Come iniziare</h2>
<p>Proponiamo alle città un progetto pilota in un solo quartiere: alcuni punti di resilienza collegati tra loro, testati per messaggi e chiamate senza alcun internet. Il risultato è un rapporto e un piano di estensione. Contatto: <a href="mailto:support@nevod.network">support@nevod.network</a>.</p>
<p class="note">Ogni trasmettitore può essere localizzato con la radiogoniometria, perciò i siti vengono scelti con cura, e il contenuto dei messaggi è cifrato end-to-end su ogni livello. L'architettura ZKI vale anche qui: l'operatore della rete cittadina non ha accesso ai contenuti.</p>
</div></main>
"""

DOWNLOAD = """
<main><div class="wrap">
<h1>Scarica Nevod</h1>
<div class="grid">
<div class="card"><h3>📱 iPhone e iPad</h3><p>Attualmente in test chiuso tramite TestFlight; la pubblicazione su App Store è in preparazione. Per partecipare al test scrivi a <a href="mailto:support@nevod.network">support@nevod.network</a>.</p></div>
<div class="card"><h3>🤖 Android</h3><p>L'app è in sviluppo. Lo annunceremo qui quando sarà pronta per i test.</p></div>
<div class="card"><h3>🖥️ Nodo della rete</h3><p>Un nodo Nevod funziona con Docker su un server o su un normale computer. Vedi <a href="/it/node/">Il tuo nodo</a>.</p></div>
</div>
</div></main>
"""

NODE = """
<main><div class="wrap">
<h1>Gestisci il tuo nodo Nevod</h1>
<p>Un nodo è un piccolo server attraverso cui i telefoni si scambiano messaggi e chiamate. Vede solo dati cifrati. Un'organizzazione, una comunità, una scuola o una famiglia può gestire il proprio nodo: proprio per questo la rete non ha un punto centrale controllato dallo sviluppatore.</p>
<h2>Cosa serve</h2>
<ul>
<li>Un computer o server con Linux o Windows e Docker installato</li>
<li>Almeno 1 GB di RAM</li>
<li>Per l'accesso da internet, un indirizzo pubblico o un dominio; per una rete cittadina o Wi-Fi basta un indirizzo locale</li>
</ul>
<h2>Come funziona</h2>
<ol>
<li>Il nodo gira in Docker e ha un pannello di amministrazione web.</li>
<li>Nel pannello imposti il nome del nodo e la modalità di ammissione (aperta, su invito o con approvazione dell'amministratore) e, se vuoi, colleghi il nodo alla rete Nevod.</li>
<li>I telefoni si collegano al nodo tramite il suo indirizzo o un codice QR d'invito.</li>
</ol>
<p class="note">Il software del nodo è open source: <a href="https://github.com/avk0978/nevod-messenger">github.com/avk0978/nevod-messenger</a> (GNU AGPL-3.0). I file per eseguire un nodo in Docker si trovano nella cartella <code>installer/docker</code> del repository. È in sviluppo anche l'installazione di un nodo con l'aiuto di un assistente IA.</p>
</div></main>
"""

ABOUT = """
<main><div class="wrap">
<h1>Il progetto</h1>
<p>Nevod è la prima implementazione del principio della <a href="/it/manifesto/">Zero Knowledge Infrastructure</a>: un'infrastruttura di comunicazione il cui creatore è tecnicamente tagliato fuori dal suo contenuto. Il progetto non dipende da un solo server, da un solo provider né da un solo paese.</p>
<h2>Autore</h2>
<p><b>Kolpakov Andrey</b> — autore del manifesto ZKI e sviluppatore di Nevod.</p>
<!--BIO-->
<h2>Codice sorgente</h2>
<p>Il codice sorgente di Nevod è aperto: il nodo, l'app per iOS e le specifiche del protocollo: <a href="https://github.com/avk0978/nevod-messenger">github.com/avk0978/nevod-messenger</a>. Licenza: GNU AGPL-3.0. Chiunque può verificare che l'app e il nodo funzionino esattamente come descritto su questo sito.</p>
<h2>Contatti</h2>
<ul>
<li>Domande generali e supporto: <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Segnalazione di abusi: <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Privacy e dati: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
</div></main>
"""

SUPPORT = """
<main><div class="wrap">
<h1>Supporto</h1>
<p class="note"><b>Importante.</b> L'amministrazione di Nevod risponde solo all'interno dell'app Nevod, dall'account ufficiale <b>administrator</b> con il badge ✓. Non rispondiamo mai via e-mail e non chiediamo mai password, chiavi o codici. Se l'«amministrazione» ti contatta in un altro modo, è una truffa.</p>
<h2>Come contattarci</h2>
<ul>
<li>Domande e aiuto: <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Segnalare un utente o un contenuto: nell'app, tieni premuto un messaggio → «Segnala», oppure Impostazioni chat → «Segnala». Inoltre: <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Privacy e dati: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
<h2>Bloccare un utente</h2>
<p>Impostazioni chat → «Blocca». Un utente bloccato non può inviarti messaggi né chiamarti; puoi sbloccarlo nello stesso punto o in Profilo → Bloccati.</p>
<h2>Eliminare l'account</h2>
<p>Profilo → «Reimposta identità». Elimina in modo definitivo la tua identità, i contatti e i messaggi dal dispositivo e la tua registrazione sul nodo. Le persone con cui chattavi vedranno che l'identità è stata eliminata.</p>
</div></main>
"""

PRIVACY = """
<main class="legal"><div class="wrap">
<h1>Informativa sulla privacy</h1>
<p>Versione del 17 ottobre 2026. Nevod è sviluppato da Kolpakov Andrey. Domande sui dati: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a>.</p>
<h2>1. In sintesi</h2>
<p>Nevod è costruito secondo il principio della Zero Knowledge Infrastructure. Il contenuto di messaggi, foto, video, messaggi vocali, file e chiamate è cifrato end-to-end e le chiavi non lasciano mai il tuo dispositivo. Né i nodi della rete né lo sviluppatore possono leggere il contenuto. L'unica eccezione è ciò che scrivi tu stesso ai bot IA: vedi la sezione 5.</p>
<h2>2. Cosa è conservato sul tuo dispositivo</h2>
<p>La tua identità crittografica (chiavi nell'archivio sicuro di iOS), i contatti, la cronologia dei messaggi e i contenuti multimediali, le impostazioni e un registro tecnico per la diagnostica. Il registro non lascia il dispositivo a meno che non sia tu a inviarlo.</p>
<p>Questi dati non sono inclusi nei backup di iCloud o del computer e non vengono trasferiti su altri dispositivi. Se il dispositivo viene perso o ripristinato, o l'app viene eliminata, la cronologia non può essere recuperata: né i nodi né lo sviluppatore ne hanno una copia.</p>
<h2>3. Cosa elabora un nodo</h2>
<ul>
<li>L'identificativo della tua identità (cell ID) e le tue chiavi pubbliche.</li>
<li>Il nome visualizzato che scegli.</li>
<li>Token del dispositivo per notifiche push e chiamate.</li>
<li>Messaggi cifrati fino alla consegna: i messaggi non consegnati vengono eliminati dopo 72 ore.</li>
<li>Le tue impostazioni di notifica e l'elenco degli utenti bloccati.</li>
<li>Metadati di consegna (chi invia un pacchetto a chi e quando) e registri diagnostici conservati per un periodo limitato.</li>
<li>I tuoi messaggi all'account administrator (segnalazioni e domande inviate dall'app). L'operatore del nodo li legge per poter rispondere: sono indirizzati a lui. Le tue conversazioni con altre persone restano inaccessibili all'operatore.</li>
</ul>
<p>I nodi possono appartenere a diversi operatori indipendenti. L'operatore del nodo a cui ti connetti tratta questi dati per il funzionamento della rete.</p>
<h2>4. Notifiche</h2>
<p>Le notifiche su iPhone sono consegnate tramite il servizio Apple Push Notification. Una notifica contiene il nome del mittente e il testo generico «Nuovo messaggio», mai il contenuto del messaggio.</p>
<h2>5. Bot IA</h2>
<p>Un nodo può offrire bot IA, ad esempio un assistente o un traduttore. Un bot di questo tipo risponde tramite il fornitore di IA che scegli tu — Anthropic (Claude), OpenAI (ChatGPT) o Google (Gemini) — con la tua chiave API. Nevod non vende accesso all'IA e non ha chiavi proprie. Puoi usare Nevod anche senza bot.</p>
<ul>
<li><b>La tua chiave</b> è conservata solo sul tuo dispositivo, nell'archivio sicuro di iOS, e non passa ad altri dispositivi. Arriva al bot cifrata end-to-end, insieme a ogni messaggio. Il bot la usa solo per quella richiesta e non la salva.</li>
<li><b>I tuoi messaggi a un bot.</b> Un bot è un partecipante a sé della rete, gestito dall'operatore del nodo su cui è pubblicato. Lungo il percorso i messaggi che gli invii sono cifrati end-to-end come tutti gli altri; il bot li decifra per rispondere e passa il testo al fornitore che hai scelto. Scrivi a un bot solo ciò che sei disposto a condividere con quel fornitore.</li>
<li><b>Cosa conserva il bot:</b> solo gli ultimi messaggi della conversazione, in memoria, per rispondere nel contesto; spariscono al riavvio del bot. Nel registro del bot finiscono solo il fatto che c'è stata una richiesta, il fornitore e la lunghezza — mai il testo o la chiave.</li>
<li><b>Il fornitore</b> riceve i tuoi messaggi, la parte recente della conversazione e la tua chiave e li tratta secondo i propri termini e la propria informativa sulla privacy (<a href="https://www.anthropic.com/legal/privacy">Anthropic</a>, <a href="https://openai.com/policies/privacy-policy">OpenAI</a>, <a href="https://policies.google.com/privacy">Google</a>). Le richieste gli arrivano dal server del bot, non dal tuo dispositivo.</li>
<li><b>Consenso.</b> Prima di aggiungere una chiave, l'app ti chiede di accettare che i tuoi messaggi ai bot vengano inviati a quel fornitore. Per revocarlo: Profilo → Sicurezza → Chiavi IA → elimina la chiave. Anche «Reimposta identità» elimina tutte le chiavi.</li>
<li>I bot ricevono solo testo: foto, file, messaggi vocali e chiamate non vengono mai passati a loro.</li>
</ul>
<h2>6. Terze parti</h2>
<p>Non vendiamo dati e non li usiamo per pubblicità o tracciamento. Utilizziamo: Apple (notifiche, distribuzione dell'app), hosting dei nodi e Cloudflare (DNS ed e-mail del dominio). Se aggiungi una chiave IA: il fornitore che hai scelto, per i tuoi messaggi ai bot (sezione 5).</p>
<h2>7. Cancellazione</h2>
<p>Profilo → «Reimposta identità» elimina i tuoi dati dal dispositivo e la tua registrazione dal nodo.</p>
<h2>8. Minori</h2>
<p>Nevod non è destinato ai minori al di sotto dell'età in cui, nel tuo paese, si può acconsentire autonomamente al trattamento dei dati.</p>
<h2>9. Modifiche</h2>
<p>Annunceremo le modifiche rilevanti a questa informativa su questa pagina e nell'app.</p>
</div></main>
"""

TERMS = """
<main class="legal"><div class="wrap">
<h1>Condizioni d'uso</h1>
<p>Versione del 28 settembre 2026. Usando Nevod accetti queste condizioni.</p>
<h2>1. Tolleranza zero verso gli abusi</h2>
<p>È vietato inviare o pubblicare contenuti illegali, molesti o minacciosi, molestare altre persone, diffondere spam o truffe e spacciarsi per altri, compresa l'amministrazione di Nevod. Chi viola le regole viene bloccato.</p>
<h2>2. Segnalazioni e blocco</h2>
<p>Puoi bloccare e segnalare qualsiasi utente nell'app o a <a href="mailto:abuse@nevod.network">abuse@nevod.network</a>. Esaminiamo le segnalazioni e agiamo di conseguenza.</p>
<h2>3. Account ufficiali</h2>
<p>L'amministrazione risponde solo nell'app, dall'account administrator con il badge ✓ — mai via e-mail — e non chiede mai password, chiavi o codici.</p>
<h2>4. Nodi</h2>
<p>La rete è formata da nodi che possono essere gestiti da operatori indipendenti. L'operatore di un nodo è responsabile di gestirlo nel rispetto delle leggi del proprio paese.</p>
<h2>5. Nessuna garanzia</h2>
<p>Nevod è fornito «così com'è». Facciamo il possibile perché la comunicazione sia affidabile, ma non garantiamo la consegna ininterrotta dei messaggi.</p>
<h2>6. Contatti</h2>
<p><a href="mailto:support@nevod.network">support@nevod.network</a></p>
</div></main>
"""

PAGES = {
    "index": ("Nevod", "Nevod, la prima implementazione della Zero Knowledge Infrastructure: un messenger il cui sviluppatore non ha accesso tecnico ai dati degli utenti.", INDEX),
    "manifesto": ("Manifesto della Zero Knowledge Infrastructure", "Il manifesto ZKI, fondamento dello sviluppo di Nevod. Autore: Kolpakov Andrey.", MANIFESTO),
    "compare": ("Confronto", "Nevod a confronto con Signal, Telegram e WhatsApp: perché la sola crittografia non è ZKI.", COMPARE),
    "security": ("Sicurezza e crittografia", "Come Nevod cifra i messaggi, cosa elabora un nodo e perché non serve documentazione di esportazione.", SECURITY),
    "cities": ("Per le città", "Una rete di comunicazione cittadina di riserva basata su Nevod, senza internet né data center.", CITIES),
    "download": ("Scarica", "Nevod per iPhone, Android e il nodo della rete.", DOWNLOAD),
    "node": ("Il tuo nodo", "Come gestire il tuo nodo della rete Nevod.", NODE),
    "about": ("Il progetto", "Chi c'è dietro Nevod e come contattarci.", ABOUT),
    "support": ("Supporto", "Supporto, segnalazioni, blocco ed eliminazione dell'account in Nevod.", SUPPORT),
    "privacy": ("Informativa sulla privacy", "Quali dati tratta Nevod e come sono protetti.", PRIVACY),
    "terms": ("Condizioni d'uso", "Condizioni d'uso di Nevod.", TERMS),
}
