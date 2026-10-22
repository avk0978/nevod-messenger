# French content for nevod.network — same facts and structure as content_uk.py / content_en.py.

T = {
    "nav": {"index": "Accueil", "manifesto": "Manifeste ZKI", "compare": "Comparaison", "security": "Sécurité",
            "cities": "Pour les villes", "download": "Télécharger", "about": "Le projet"},
    "nav_support": "Assistance", "nav_privacy": "Confidentialité", "nav_terms": "Conditions d'utilisation", "nav_node": "Votre nœud",
    "footer_owner": "© 2026 Nevod · Kolpakov Andrey",
}

INDEX = """
<section class="hero"><div class="wrap">
<div class="eyebrow">Zero Knowledge Infrastructure</div>
<h1>Nevod : une messagerie dont le développeur est techniquement coupé de vos données</h1>
<p class="lead">Non par une promesse, ni seulement par le chiffrement, mais par l'architecture. Le développeur n'a ni vos clés, ni clé maîtresse, ni serveur central, ni base de données des utilisateurs. Même si quelqu'un se présente avec une réquisition, il n'y a rien à remettre.</p>
<div class="btns"><a class="btn primary" href="/fr/manifesto/">Lire le manifeste ZKI</a><a class="btn ghost" href="/fr/download/">Télécharger</a></div>
</div></section>
<main><div class="wrap">
<h2>Le chiffrement est une serrure. ZKI, c'est l'absence de clé chez le développeur</h2>
<p>La plupart des messageries chiffrent les messages, mais l'entreprise continue d'exploiter les serveurs, de tenir la base des utilisateurs, de lier les comptes à des numéros de téléphone et de voir qui parle à qui et quand. Le chiffrement protège le contenu en transit ; tout le reste reste entre les mains de l'entreprise.</p>
<p>Nevod est construit selon le principe de la <b>Zero Knowledge Infrastructure</b> : l'infrastructure est conçue pour que son créateur ne puisse pas accéder au contenu, ni s'il le voulait, ni s'il y était contraint.</p>
<div class="grid">
<div class="card"><h3>🔑 Les clés, vous seul les avez</h3><p>Les clés sont créées sur votre appareil et ne le quittent jamais. Le développeur n'a ni copie, ni clé maîtresse, ni sauvegarde.</p></div>
<div class="card"><h3>🌐 Un nœud à soi pour chacun</h3><p>Pas de serveur central : le réseau est fait de nœuds indépendants, et rien ne vous empêche d'exploiter le vôtre. Il n'existe aucun point unique où tout se concentre.</p></div>
<div class="card"><h3>📵 L'identité est une clé, pas un numéro</h3><p>Ni numéro de téléphone ni e-mail. Le développeur ne tient pas de registre des personnes et ne sait pas qui vous êtes.</p></div>
<div class="card"><h3>📭 Rien à remettre</h3><p>Si quelqu'un exige une conversation, le développeur n'a rien à donner. Non parce qu'il la cache, mais parce qu'il ne l'a pas.</p></div>
</div>
<p class="note">ZKI est le fondement du développement de Nevod. Chaque décision technique est soumise à une seule question : le créateur de l'infrastructure obtient-il un accès au contenu ? <a href="/fr/manifesto/">Manifeste de la Zero Knowledge Infrastructure →</a></p>
<h2>Réseau distribué à faible charge</h2>
<p>La charge de chaque nœud Nevod est limitée par son propre cercle (famille, foyer, équipe), et non par la taille de tout le réseau : un million de nouveaux utilisateurs ailleurs n'ajoutent pas un seul octet à votre nœud. Le nœud tourne sur du matériel domestique ordinaire, le réseau n'a pas de centre et le nœud lui-même ne transporte que du texte chiffré.</p>
<p><a href="/fr/compare/#low-load">Une comparaison de Nevod avec 14 autres réseaux, de FidoNet à Signal →</a></p>
<h2>Ce que fait Nevod</h2>
<div class="grid">
<div class="card"><h3>🔒 Chiffrement de bout en bout</h3><p>Chaque message, photo, message vocal et appel est chiffré sur le téléphone. Les nœuds ne voient que des données chiffrées.</p></div>
<div class="card"><h3>📞 Appels et vidéo</h3><p>Appels audio et vidéo, messages vocaux, photos, vidéos et fichiers.</p></div>
<div class="card"><h3>🏙️ Communication sans internet</h3><p>L'architecture peut acheminer les messages par n'importe quel canal disponible, y compris à l'intérieur d'une ville privée d'accès à internet.</p></div>
<div class="card"><h3>🛡️ Protection contre les abus</h3><p>Blocage et signalements, comptes officiels vérifiés, protection contre l'usurpation de l'administration.</p></div>
</div>
<h2>État du projet</h2>
<div class="tbl"><table class="status">
<tr><th style="width:34%">Domaine</th><th>État</th></tr>
<tr><td>Application iPhone</td><td>Test fermé (TestFlight) ; publication sur l'App Store en préparation</td></tr>
<tr><td>Application Android</td><td>En développement</td></tr>
<tr><td>Nœuds du réseau</td><td>En fonctionnement, installés avec Docker</td></tr>
<tr><td>Langues de l'application</td><td>8 : ukrainien, anglais, russe, allemand, turc, espagnol, italien, français</td></tr>
</table></div>
</div></main>
"""

MANIFESTO = """
<main><div class="wrap">
<div class="eyebrow" style="color:#8A6A00">Manifeste</div>
<h1>Zero Knowledge Infrastructure</h1>
<p><b>Le réseau que vous regardez, Nevod, est la première mise en œuvre complète d'une seule idée : ceux qui construisent l'infrastructure de communication ne doivent pas pouvoir, techniquement, voir ce qui la traverse.</b></p>
<h2>La position</h2>
<p>Je construis des outils.<br>Je ne surveille pas la façon dont on les utilise.<br>Je n'ai pas accès aux données.<br>Et c'est l'architecture du logiciel !</p>
<p>Ce n'est pas une politique de confidentialité. Ce n'est pas une promesse marketing. C'est une impossibilité technique inscrite dans les fondations.</p>
<h2>Le principe du couteau</h2>
<p>Le fabricant d'un couteau n'est pas responsable de l'usage qui en est fait. Avec un couteau, on peut couper du pain ou non. C'est le choix de celui qui le tient, pas de celui qui l'a forgé.</p>
<p>La même logique s'applique à l'infrastructure de communication.</p>
<p>Je construis le canal. Ce qui y passe ne me regarde pas.<br>Non parce que cela m'est égal. Parce que cela <b>ne doit pas</b> me regarder.</p>
<p>Le droit à une communication privée est un droit humain fondamental. L'infrastructure de communication ne doit pas être un point de surveillance.</p>
<h2>Ce que cela signifie techniquement</h2>
<p>Les clés de chiffrement sont générées sur l'appareil de l'utilisateur.<br>Elles ne quittent jamais cet appareil.<br>Je n'ai pas de serveurs qui conservent des clés.<br>Je n'ai pas de clé maîtresse.<br>Je n'ai pas de sauvegarde.</p>
<p>Si quelqu'un vient me demander une conversation, je n'ai rien à lui donner. Non parce que je la cache, mais parce que <b>je ne l'ai pas</b>.</p>
<p>Ce n'est pas une promesse. C'est une garantie architecturale.</p>
<h2>Ce que cela signifie comme position</h2>
<p>Je ne veux pas gagner d'argent avec les données personnelles des gens. Je ne veux pas savoir de quoi ils parlent. Je ne veux pas être un intermédiaire auquel on peut adresser une réquisition judiciaire.</p>
<p>Les revenus viennent de l'outil, pas du contenu. Je vends le marteau, pas ce que l'on construit avec.</p>
<h2>Les agents IA et la prochaine frontière</h2>
<p>Le monde se dirige vers des agents IA autonomes. Les agents se parleront : ils négocieront, se délégueront des tâches, échangeront des données.</p>
<p>La question devient : qui voit ces conversations ?</p>
<p>La réponse actuelle du secteur, c'est la plateforme. OpenAI voit ce que font les agents sur OpenAI. Google voit ce que font les agents sur Google. L'opérateur de l'orchestrateur voit tout.</p>
<p>Ma réponse : <b>personne</b>.</p>
<p>Si les agents communiquent via une infrastructure ZKI, leur correspondance est chiffrée de bout en bout. L'opérateur de la plateforme ne voit que le routage. Le contenu de la négociation reste entre les agents.</p>
<div class="tbl"><table>
<tr><th>Agent A</th><th style="width:30%">⇄ chiffré de bout en bout ⇄</th><th>Agent B</th></tr>
<tr><td>Nœud Nevod — ne voit que du texte chiffré</td><td></td><td>Nœud Nevod — ne voit que du texte chiffré</td></tr>
<tr><td>Opérateur — ne voit rien</td><td></td><td>Opérateur — ne voit rien</td></tr>
</table></div>
<p><i>« J'exploite un service utilisé par des agents IA. Je ne sais pas ce qu'ils ont convenu avec votre agent. »</i></p>
<p>Ce n'est pas se dérober à ses responsabilités. C'est une architecture pour un monde où les agents sont des acteurs indépendants.</p>
<h2>Pourquoi c'est important maintenant</h2>
<p>En 2025–2026 :</p>
<ul><li>Les agents IA commencent à agir de manière autonome</li><li>Des agents de différentes entreprises commencent à interagir</li><li>Personne n'a décidé qui voit les négociations entre agents</li><li>Personne n'a décidé qui répond de ce qu'un agent a « dit »</li></ul>
<p>ZKI répond :</p>
<ul><li>Les négociations sont chiffrées : l'opérateur ne les voit pas</li><li>La responsabilité des actes d'un agent incombe à celui qui l'exécute</li><li>L'infrastructure de communication reste neutre, comme une ligne téléphonique</li></ul>
<h2>Précédents</h2>
<div class="tbl"><table>
<tr><th style="width:30%">Outil</th><th>Position</th></tr>
<tr><td>Tor Project</td><td>« Nous avons construit un outil d'anonymat. Nous ne voyons pas le trafic. »</td></tr>
<tr><td>Signal Foundation</td><td>« Les clés sont chez les utilisateurs. Nous n'avons rien à remettre. »</td></tr>
<tr><td>ProtonMail</td><td>« Chiffrement à connaissance nulle. Nous ne pouvons pas lire vos e-mails. »</td></tr>
<tr><td>Fournisseurs de VPN</td><td>« Nous fournissons le tunnel. Le contenu ne nous appartient pas. »</td></tr>
<tr><td>Portefeuilles matériels</td><td>« Les clés sont sur l'appareil. Nous n'en avons pas de copie. »</td></tr>
</table></div>
<p>Toutes ces positions ont résisté à l'examen juridique dans la plupart des pays démocratiques. ZKI est la même position, élevée au rang de philosophie de conception.</p>
<h2>Ce que je construis</h2>
<p><b>Nevod</b> est la première mise en œuvre du principe ZKI sous forme de réseau complet. Ce n'est pas un produit. C'est un protocole.</p>
<p>Il peut servir de base à :</p>
<ul><li>Des messageries</li><li>Du stockage de fichiers</li><li>Des systèmes de vote</li><li>Des dispositifs « homme mort »</li><li>Des protocoles pour agents IA</li><li>Des infrastructures d'entreprise</li></ul>
<p>Un seul principe partout : <b>le créateur de l'infrastructure est techniquement coupé de son contenu</b>.</p>
<p style="margin-top:2em"><i>Avril 2026</i></p>
<p><b>Kolpakov Andrey</b></p>
<p class="note">© 2026. Lorsque vous citez ce manifeste ou y faites référence, merci d'inclure un lien vers <a href="https://nevod.network">nevod.network</a>. Original anglais : <a href="/manifesto/">nevod.network/manifesto</a>.</p>
</div></main>
"""

COMPARE = """
<main><div class="wrap">
<h1>Nevod et les autres messageries</h1>
<p>La plupart des messageries modernes chiffrent les messages. La différence ne tient pas à la présence du chiffrement, mais à <b>ce qui reste entre les mains de l'entreprise</b> : serveurs, base des utilisateurs, numéros de téléphone, carnet d'adresses, métadonnées — et ce qui peut en être exigé.</p>
<p class="note">Nevod applique le principe de la <a href="/fr/manifesto/">Zero Knowledge Infrastructure</a> : le développeur est coupé des données des utilisateurs par l'<b>architecture</b>, pas seulement par le chiffrement. Les informations sur les autres messageries reposent sur leurs descriptions publiques en 2026 et peuvent évoluer.</p>
<div class="tbl"><table>
<tr><th style="width:24%"></th><th>Nevod</th><th>Signal</th><th>Telegram</th><th>WhatsApp</th></tr>
<tr><td>Qui peut techniquement lire une conversation ordinaire</td><td>Uniquement les participants</td><td>Uniquement les participants</td><td>Conversations ordinaires et groupes : les serveurs de Telegram (bout en bout seulement dans les « conversations secrètes » à deux)</td><td>Uniquement les participants</td></tr>
<tr><td>Serveurs centraux de l'entreprise</td><td>Non : des nœuds indépendants que chacun peut exploiter</td><td>Oui</td><td>Oui</td><td>Oui, ceux de Meta</td></tr>
<tr><td>Lié à un numéro de téléphone</td><td>Non : l'identité est une clé</td><td>Oui (le numéro peut être masqué derrière un nom d'utilisateur)</td><td>Oui</td><td>Oui</td></tr>
<tr><td>Envoi du carnet d'adresses</td><td>Non : les contacts s'ajoutent par carte ou QR</td><td>Découverte privée des contacts</td><td>Oui, si autorisé</td><td>Oui, si autorisé</td></tr>
<tr><td>Base des utilisateurs chez l'entreprise</td><td>Aucune centrale : chaque nœud ne connaît que ses propres utilisateurs</td><td>Minimale</td><td>Oui</td><td>Oui</td></tr>
<tr><td>Ce que l'entreprise peut remettre sur réquisition</td><td>Le développeur n'a rien à donner : ni clés, ni messages, ni base</td><td>Selon ses rapports : date de création du compte et de dernière connexion</td><td>Selon sa politique : dans certains cas, adresse IP et numéro de téléphone</td><td>Métadonnées du compte, selon sa politique</td></tr>
<tr><td>Sauvegardes des conversations dans le cloud</td><td>Aucune : les clés et l'historique n'existent que sur l'appareil (téléphone perdu, historique perdu)</td><td>Facultatives ; chiffrées avec une clé que seul l'utilisateur détient</td><td>Inutiles : les conversations ordinaires sont déjà stockées sur les serveurs de Telegram</td><td>Vers iCloud / Google Drive ; sans chiffrement de bout en bout par défaut (à activer manuellement)</td></tr>
<tr><td>Point unique de défaillance ou de blocage</td><td>Non : les nœuds sont indépendants</td><td>Oui</td><td>Oui</td><td>Oui</td></tr>
<tr><td>Fonctionnement sans internet à l'intérieur d'une ville</td><td>Fait partie de l'architecture (réseau urbain, Wi-Fi mesh, radio)</td><td>Non</td><td>Non</td><td>Non</td></tr>
<tr><td>Modèle économique</td><td>Sur l'outil, pas sur les données</td><td>Dons (à but non lucratif)</td><td>Publicité et Premium</td><td>Services professionnels de Meta</td></tr>
<tr><td>Code ouvert</td><td>Pas encore : fermé jusqu'à la version de production</td><td>Oui</td><td>En partie (clients)</td><td>Non</td></tr>
</table></div>
<h2>Pourquoi « le chiffrement seul » ne suffit pas</h2>
<p>Le chiffrement de bout en bout protège le contenu d'un message en transit. Mais si une entreprise exploite tous les serveurs, tient une base de comptes par numéro de téléphone et voit qui parle à qui et quand, elle garde le pouvoir sur le système : elle peut être contrainte, piratée ou bloquée, et une mise à jour de l'application peut changer les règles.</p>
<p>ZKI pose une autre question : <b>que peut obtenir, même en théorie, le créateur de l'infrastructure ?</b> Dans Nevod, la réponse est dans l'architecture : les clés ne quittent jamais l'appareil, il n'existe ni clé maîtresse ni sauvegarde, ni serveur central ni registre des personnes par numéro de téléphone.</p>
<h2 id="low-load">Réseau distribué à faible charge : une comparaison</h2>
<p>Nous évaluons les réseaux selon six traits d'un réseau distribué à faible charge : la charge de chaque nœud est limitée par son propre cercle de personnes, et non par la taille de tout le réseau. Ces traits découlent des principes mêmes de Nevod ; la comparaison lui est donc favorable d'emblée.</p>
<ol>
<li>Cercle propre : la charge d'un nœud croît avec son cercle (famille, foyer, équipe), et non avec tout le réseau.</li>
<li>Matériel ordinaire : un ordinateur domestique, un mini-serveur ou un routeur ; pas besoin de centre de données.</li>
<li>Économie : d'abord le texte et les signaux, le lourd à la demande.</li>
<li>Tolérance aux délais : sans connexion, le message attend et part plus tard, y compris par un canal lent.</li>
<li>Pas de centre : aucun point unique de panne, de blocage ou de saisie.</li>
<li>Nœud aveugle : le nœud ne transporte que du texte chiffré et ne peut pas le lire.</li>
</ol>
<p class="note">1 : oui, ½ : en partie, 0 : non. Année : première version publique. Classe : LL-0, la charge du nœud est limitée par son cercle ; LL-1, plus un transit d'autrui borné ; LL-3, la charge croît avec tout le réseau ou dépend d'utilisateurs extérieurs. Plus : <a href="/fr/publications/low-load-networks/">l'article</a>.</p>
<div class="tbl"><table>
<tr><th>Réseau</th><th>Année</th><th>Cercle propre</th><th>Matériel ordinaire</th><th>Économie</th><th>Délais</th><th>Pas de centre</th><th>Nœud aveugle</th><th>Classe</th></tr>
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
<p>Signal et WhatsApp obtiennent ½ pour l'aveuglement : le contenu est chiffré de bout en bout, mais l'entreprise voit les métadonnées et gère les serveurs. Dans Reticulum et NNCP, des nœuds intermédiaires transportent et stockent les paquets d'autrui. Nevod envoie encore les médias en entier, conserve les messages non remis 72 heures et ne fonctionne que par internet.</p>
<h3>À l'épreuve de la pratique</h3>
<div class="tbl"><table>
<tr><th>Réseau</th><th>Année</th><th>Pour tout le monde</th><th>Maturité</th><th>Audit indépendant</th></tr>
<tr><td>Reticulum / LXMF</td><td>2016</td><td>non, pour passionnés</td><td>communauté active</td><td>non</td></tr>
<tr><td>NNCP</td><td>2016</td><td>non, outil en ligne de commande</td><td>de niche</td><td>non</td></tr>
<tr><td><b>Nevod</b></td><td>2026</td><td>oui : iPhone/iPad, messages, médias, appels</td><td>en test, pas encore d'utilisateurs réels</td><td>non</td></tr>
<tr><td>Briar</td><td>2018</td><td>oui, mais sans appels ; Android et ordinateur</td><td>mature</td><td>oui (Cure53, 2017)</td></tr>
<tr><td>Signal</td><td>2014</td><td>oui</td><td>très mature</td><td>oui, à plusieurs reprises</td></tr>
</table></div>
<p>Selon le trait principal, Nevod relève de la classe LL-0 avec Briar et Secure Scuttlebutt ; Reticulum et NNCP, proches sur les autres traits, relèvent de LL-1. Sa différence est ailleurs : parmi ces réseaux, il est le seul conçu comme une messagerie complète pour tout le monde, avec médias, appels et une app iPhone. Mais il est jeune : pas encore d'utilisateurs réels, pas d'audit indépendant, iOS seulement. Le chemin vers six sur six : les médias à la demande et la remise sans internet par des canaux lents.</p>
<h2>Ce que nous reconnaissons</h2>
<ul>
<li>Un nœud ne traite techniquement que des données d'acheminement — quel paquet chiffré va à qui — et ne voit jamais le contenu. Rien ne vous empêche d'exploiter votre propre nœud : même ces données d'acheminement restent alors chez vous.</li>
<li>Le protocole de Signal est ouvert et largement audité ; nous le reconnaissons comme une force. Le code de Nevod est pour l'instant fermé ; son ouverture est prévue.</li>
</ul>
</div></main>
"""

SECURITY = """
<main><div class="wrap">
<h1>Sécurité et chiffrement</h1>
<p class="note">Le chiffrement n'est qu'une partie de la protection. Le fondement de Nevod est l'architecture de la <a href="/fr/manifesto/">Zero Knowledge Infrastructure</a>, dans laquelle le développeur n'a accès ni aux clés ni aux données des utilisateurs.</p>
<h2>Comment vos messages sont protégés</h2>
<p>Nevod utilise le chiffrement de bout en bout : un message est chiffré sur votre appareil et déchiffré uniquement sur celui du destinataire. Le nœud qui l'achemine ne voit que des données chiffrées et les informations de service nécessaires à la remise — jamais le contenu.</p>
<div class="tbl"><table>
<tr><th style="width:38%">Quoi</th><th>Comment</th></tr>
<tr><td>Chiffrement des messages</td><td>CryptoKit, la bibliothèque cryptographique système d'Apple : échange de clés X25519, SHA-256, chiffrement ChaCha20-Poly1305</td></tr>
<tr><td>Signatures</td><td>CryptoKit : Ed25519</td></tr>
<tr><td>Preuve d'identité lors de la connexion à un nœud</td><td>Protocole à divulgation nulle de connaissance de Schnorr sur CryptoKit (Curve25519, SHA-256/512) et une seule opération arithmétique modulaire implémentée dans Nevod lui-même</td></tr>
</table></div>
<p>L'expéditeur crée une nouvelle clé à usage unique pour chaque message. La clé du destinataire est de longue durée : si elle est volée sur l'appareil du destinataire, des messages interceptés auparavant et qui lui étaient adressés pourraient aussi être déchiffrés. Il est donc important de protéger l'appareil lui-même : un code d'accès et un iOS à jour.</p>
<p>Le protocole de Schnorr vous permet de prouver à un nœud que vous détenez votre clé sans l'envoyer ni la révéler.</p>
<h2>Si vous perdez votre téléphone</h2>
<p>Vos clés, vos contacts et l'historique de vos messages sont stockés uniquement sur votre appareil. Ils ne figurent ni dans les sauvegardes iCloud ou sur ordinateur, ni sur les nœuds, ni chez le développeur. Si le téléphone est perdu, cassé ou réinitialisé, ils ne peuvent donc pas être restaurés. Supprimer l'app efface aussi l'historique.</p>
<p>Le transfert vers un nouvel appareil n'est pas encore disponible. Sur un nouveau téléphone, vous créerez une nouvelle identité, et vos contacts auront besoin de votre nouvelle carte. C'est une conséquence de l'architecture : une copie permettant de restaurer vos conversations serait aussi une copie à laquelle quelqu'un pourrait accéder.</p>
<h2>Votre nœud, vos règles</h2>
<p>Le développeur ne voit rien. Un nœud ne traite que ce sans quoi la remise ne fonctionne pas : identifiants des participants, noms choisis, jetons de notification et quel paquet chiffré va à qui. Un nœud ne voit jamais le contenu des messages, photos, messages vocaux ou appels.</p>
<p>Rien ne vous empêche de créer votre propre nœud — pour vous, votre famille, une organisation ou une communauté. Même les données d'acheminement restent alors chez vous. <a href="/fr/node/">Comment exploiter votre propre nœud →</a></p>
<h2>Contrôle des exportations et App Store</h2>
<p>Lors d'une publication sur l'App Store, le développeur déclare si l'application utilise un chiffrement soumis au contrôle des exportations (EAR américaines, catégorie 5, partie 2). Nevod déclare que non, et voici pourquoi :</p>
<ul>
<li><b>Tout ce qui masque le contenu des messages relève de la cryptographie système d'Apple (CryptoKit).</b> Les applications qui n'utilisent que le chiffrement intégré au système d'exploitation d'Apple bénéficient d'une exemption et n'ont pas besoin de documents d'exportation.</li>
<li><b>L'implémentation propre de Nevod — une seule opération arithmétique dans le protocole de Schnorr — sert uniquement à prouver l'identité.</b> Le contrôle des exportations vise la cryptographie destinée à la confidentialité. La cryptographie utilisée uniquement pour l'authentification, les signatures et l'intégrité en est exclue.</li>
</ul>
<p>C'est pourquoi Nevod n'a pas besoin de documents d'exportation, y compris pour la distribution en France.</p>
<p><i>Il s'agit de notre interprétation des règles en vigueur, et non d'un avis juridique.</i></p>
</div></main>
"""

CITIES = """
<section class="hero"><div class="wrap">
<div class="eyebrow">Pour les villes</div>
<h1>Une communication pour la ville, sans internet ni centres de données</h1>
<p class="lead">Toute ville moderne dépend des centres de données et des liaisons dorsales. L'architecture de Nevod peut acheminer des messages chiffrés par n'importe quel canal disponible ; on peut donc bâtir dessus un réseau urbain de communication de secours.</p>
</div></section>
<main><div class="wrap">
<h2>Quatre couches de communication</h2>
<div class="tbl"><table>
<tr><th style="width:24%">Couche</th><th>Ce qu'elle utilise</th><th style="width:16%">Portée</th><th style="width:20%">Ce qu'elle transporte</th></tr>
<tr><td>1. Nœuds urbains</td><td>Réseaux des fournisseurs sans sortie vers internet</td><td>Toute la ville</td><td>Tout, à l'intérieur de la ville</td></tr>
<tr><td>2. Wi-Fi mesh</td><td>Routeurs ordinaires dans des « points de résilience » : abris, écoles, centres d'aide</td><td>Îlot–quartier</td><td>Tout, appels compris</td></tr>
<tr><td>3. Liaisons radio</td><td>Radiomodems directionnels en visibilité directe</td><td>10–20 km</td><td>Tout, appels compris</td></tr>
<tr><td>4. LoRa</td><td>Modules radio bon marché</td><td>1–10+ km</td><td>Textes courts uniquement</td></tr>
</table></div>
<p>Pour les gens, c'est le même Nevod : l'application choisit elle-même le canal disponible.</p>
<h2>Un point de résilience</h2>
<p>Un kit de matériel bon marché et disponible dans le commerce : quelques routeurs à logiciel libre, un petit serveur de nœud, une alimentation de secours et, si nécessaire, une liaison radio vers d'autres quartiers et un module LoRa pour les textes courts. Rien n'est à inventer.</p>
<h2>Comment commencer</h2>
<p>Nous proposons aux villes un pilote dans un seul quartier : quelques points de résilience reliés entre eux, testés pour les messages et les appels sans aucun internet. Le résultat : un rapport et un plan d'extension. Contact : <a href="mailto:support@nevod.network">support@nevod.network</a>.</p>
<p class="note">Tout émetteur peut être localisé par radiogoniométrie : les emplacements sont donc choisis avec soin, et le contenu des messages est chiffré de bout en bout sur chaque couche. L'architecture ZKI s'applique ici aussi : l'opérateur du réseau urbain n'a pas accès au contenu.</p>
</div></main>
"""

DOWNLOAD = """
<main><div class="wrap">
<h1>Télécharger Nevod</h1>
<div class="grid">
<div class="card"><h3>📱 iPhone et iPad</h3><p>Actuellement en test fermé via TestFlight ; la publication sur l'App Store est en préparation. Pour rejoindre le test, écrivez à <a href="mailto:support@nevod.network">support@nevod.network</a>.</p></div>
<div class="card"><h3>🤖 Android</h3><p>L'application est en développement. Nous l'annoncerons ici lorsqu'elle sera prête pour les tests.</p></div>
<div class="card"><h3>🖥️ Nœud du réseau</h3><p>Un nœud Nevod fonctionne avec Docker sur un serveur ou un ordinateur ordinaire. Voir <a href="/fr/node/">Votre nœud</a>.</p></div>
</div>
</div></main>
"""

NODE = """
<main><div class="wrap">
<h1>Exploitez votre propre nœud Nevod</h1>
<p>Un nœud est un petit serveur par lequel les téléphones échangent messages et appels. Il ne voit que des données chiffrées. Une organisation, une communauté, une école ou une famille peut exploiter son propre nœud — c'est précisément pour cela que le réseau n'a pas de point central contrôlé par le développeur.</p>
<h2>Ce qu'il faut</h2>
<ul>
<li>Un ordinateur ou un serveur sous Linux ou Windows avec Docker installé</li>
<li>Au moins 1 Go de RAM</li>
<li>Pour un accès depuis internet, une adresse publique ou un nom de domaine ; pour un réseau urbain ou Wi-Fi, une adresse locale suffit</li>
</ul>
<h2>Comment ça marche</h2>
<ol>
<li>Le nœud tourne dans Docker et dispose d'un panneau d'administration web.</li>
<li>Dans le panneau, vous définissez le nom du nœud et le mode d'admission (ouvert, sur invitation ou avec approbation de l'administrateur) et, si vous le souhaitez, vous reliez le nœud au réseau Nevod.</li>
<li>Les téléphones se connectent au nœud par son adresse ou par un code QR d'invitation.</li>
</ol>
<p class="note">Une version publique du logiciel de nœud est en préparation. Pour l'instant, l'accès est accordé sur demande à <a href="mailto:support@nevod.network">support@nevod.network</a>. L'installation d'un nœud avec l'aide d'un assistant IA est également en développement.</p>
</div></main>
"""

ABOUT = """
<main><div class="wrap">
<h1>Le projet</h1>
<p>Nevod est la première mise en œuvre du principe de la <a href="/fr/manifesto/">Zero Knowledge Infrastructure</a> : une infrastructure de communication dont le créateur est techniquement coupé de son contenu. Le projet ne dépend ni d'un seul serveur, ni d'un seul fournisseur, ni d'un seul pays.</p>
<h2>Auteur</h2>
<p><b>Kolpakov Andrey</b> — auteur du manifeste ZKI et développeur de Nevod.</p>
<!--BIO-->
<h2>Contact</h2>
<ul>
<li>Questions générales et assistance : <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Signaler un abus : <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Confidentialité et données : <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
</div></main>
"""

SUPPORT = """
<main><div class="wrap">
<h1>Assistance</h1>
<p class="note"><b>Important.</b> L'administration de Nevod ne répond qu'à l'intérieur de l'application Nevod, depuis le compte officiel <b>administrator</b> doté du badge ✓. Nous ne répondons jamais par e-mail et ne demandons jamais de mots de passe, de clés ni de codes. Si « l'administration » vous contacte par un autre moyen, c'est une escroquerie.</p>
<h2>Comment nous joindre</h2>
<ul>
<li>Questions et aide : <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Signaler un utilisateur ou un contenu : dans l'application, appui long sur un message → « Signaler », ou Réglages de la conversation → « Signaler ». Également : <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Confidentialité et données : <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
<h2>Bloquer un utilisateur</h2>
<p>Réglages de la conversation → « Bloquer ». Un utilisateur bloqué ne peut ni vous écrire ni vous appeler ; vous pouvez le débloquer au même endroit ou dans Profil → Bloqués.</p>
<h2>Supprimer le compte</h2>
<p>Profil → « Réinitialiser l'identité ». Cela supprime définitivement votre identité, vos contacts et vos messages de l'appareil ainsi que votre inscription sur le nœud. Les personnes avec qui vous discutiez verront que l'identité a été supprimée.</p>
</div></main>
"""

PRIVACY = """
<main class="legal"><div class="wrap">
<h1>Politique de confidentialité</h1>
<p>Version du 17 octobre 2026. Nevod est développé par Kolpakov Andrey. Questions relatives aux données : <a href="mailto:privacy@nevod.network">privacy@nevod.network</a>.</p>
<h2>1. L'essentiel</h2>
<p>Nevod est construit selon le principe de la Zero Knowledge Infrastructure. Le contenu de vos messages, photos, vidéos, messages vocaux, fichiers et appels est chiffré de bout en bout, et les clés ne quittent jamais votre appareil. Ni les nœuds du réseau ni le développeur ne peuvent lire le contenu. La seule exception est ce que vous écrivez vous-même aux bots d'IA : voir la section 5.</p>
<h2>2. Ce qui est stocké sur votre appareil</h2>
<p>Votre identité cryptographique (clés dans le stockage sécurisé d'iOS), vos contacts, votre historique de messages et vos médias, vos réglages et un journal technique de diagnostic. Le journal ne quitte l'appareil que si vous l'envoyez vous-même.</p>
<p>Ces données ne sont pas incluses dans les sauvegardes iCloud ou sur ordinateur et ne sont pas transférées vers d'autres appareils. Si l'appareil est perdu ou réinitialisé, ou si l'app est supprimée, l'historique ne peut pas être restauré : ni les nœuds ni le développeur n'en ont de copie.</p>
<h2>3. Ce que traite un nœud</h2>
<ul>
<li>L'identifiant de votre identité (cell ID) et vos clés publiques.</li>
<li>Le nom d'affichage que vous choisissez.</li>
<li>Les jetons de l'appareil pour les notifications push et les appels.</li>
<li>Les messages chiffrés jusqu'à leur remise : les messages non remis sont supprimés au bout de 72 heures.</li>
<li>Vos réglages de notification et votre liste d'utilisateurs bloqués.</li>
<li>Les métadonnées d'acheminement (qui envoie un paquet à qui et quand) et des journaux de diagnostic conservés pour une durée limitée.</li>
<li>Vos messages au compte administrator (signalements et questions envoyés depuis l'app). L'opérateur du nœud les lit pour pouvoir répondre : c'est à lui qu'ils sont adressés. Vos conversations avec d'autres personnes restent inaccessibles à l'opérateur.</li>
</ul>
<p>Les nœuds peuvent appartenir à différents opérateurs indépendants. L'opérateur du nœud auquel vous vous connectez traite ces données pour le fonctionnement du réseau.</p>
<h2>4. Notifications</h2>
<p>Sur iPhone, les notifications sont acheminées par le service Apple Push Notification. Une notification contient le nom de l'expéditeur et le texte générique « Nouveau message » — jamais le contenu du message.</p>
<h2>5. Bots d'IA</h2>
<p>Un nœud peut proposer des bots d'IA, par exemple un assistant ou un traducteur. Un tel bot répond par l'intermédiaire du fournisseur d'IA que vous choisissez — Anthropic (Claude), OpenAI (ChatGPT) ou Google (Gemini) — avec votre propre clé d'API. Nevod ne vend pas d'accès à l'IA et n'a pas de clés à lui. Vous pouvez utiliser Nevod sans aucun bot.</p>
<ul>
<li><b>Votre clé</b> est conservée uniquement sur votre appareil, dans le stockage sécurisé d'iOS, et n'est pas transférée vers d'autres appareils. Elle parvient au bot chiffrée de bout en bout, avec chaque message. Le bot l'utilise pour cette seule requête et ne l'enregistre pas.</li>
<li><b>Vos messages à un bot.</b> Un bot est un participant distinct du réseau, exploité par l'opérateur du nœud où il est publié. En chemin, les messages qui lui sont adressés sont chiffrés de bout en bout comme tous les autres ; le bot les déchiffre pour répondre et transmet le texte au fournisseur que vous avez choisi. N'écrivez à un bot que ce que vous acceptez de partager avec ce fournisseur.</li>
<li><b>Ce que le bot conserve :</b> seulement les derniers messages de la conversation, en mémoire, pour répondre dans le contexte ; ils disparaissent au redémarrage du bot. Le journal du bot note qu'une requête a eu lieu, son fournisseur et sa longueur — jamais le texte ni la clé.</li>
<li><b>Le fournisseur</b> reçoit vos messages, la partie récente de la conversation et votre clé, et les traite selon ses propres conditions et sa politique de confidentialité (<a href="https://www.anthropic.com/legal/privacy">Anthropic</a>, <a href="https://openai.com/policies/privacy-policy">OpenAI</a>, <a href="https://policies.google.com/privacy">Google</a>). Les requêtes lui parviennent depuis le serveur du bot, pas depuis votre appareil.</li>
<li><b>Consentement.</b> Avant que vous ajoutiez une clé, l'application vous demande d'accepter que vos messages aux bots soient transmis à ce fournisseur. Pour le retirer : Profil → Sécurité → Clés d'IA → supprimer la clé. « Réinitialiser l'identité » supprime aussi toutes les clés.</li>
<li>Les bots ne reçoivent que du texte : photos, fichiers, messages vocaux et appels ne leur sont jamais transmis.</li>
</ul>
<h2>6. Tiers</h2>
<p>Nous ne vendons pas de données et ne les utilisons ni pour la publicité ni pour le pistage. Nous utilisons : Apple (notifications, distribution de l'application), l'hébergement des nœuds et Cloudflare (DNS et e-mail du domaine). Si vous ajoutez une clé d'IA : le fournisseur que vous avez choisi, pour vos messages aux bots (section 5).</p>
<h2>7. Suppression</h2>
<p>Profil → « Réinitialiser l'identité » supprime vos données de l'appareil et votre inscription sur le nœud.</p>
<h2>8. Enfants</h2>
<p>Nevod ne s'adresse pas aux enfants n'ayant pas atteint l'âge auquel, dans votre pays, on peut consentir seul au traitement de ses données.</p>
<h2>9. Modifications</h2>
<p>Nous annoncerons les modifications importantes de cette politique sur cette page et dans l'application.</p>
</div></main>
"""

TERMS = """
<main class="legal"><div class="wrap">
<h1>Conditions d'utilisation</h1>
<p>Version du 28 septembre 2026. En utilisant Nevod, vous acceptez ces conditions.</p>
<h2>1. Tolérance zéro envers les abus</h2>
<p>Il est interdit d'envoyer ou de publier des contenus illégaux, harcelants ou menaçants, de harceler autrui, de diffuser du spam ou des escroqueries, et d'usurper l'identité d'autrui, y compris celle de l'administration de Nevod. Les contrevenants sont bloqués.</p>
<h2>2. Signalements et blocage</h2>
<p>Vous pouvez bloquer et signaler tout utilisateur dans l'application ou à <a href="mailto:abuse@nevod.network">abuse@nevod.network</a>. Nous examinons les signalements et agissons en conséquence.</p>
<h2>3. Comptes officiels</h2>
<p>L'administration ne répond que dans l'application, depuis le compte administrator doté du badge ✓ — jamais par e-mail — et ne demande jamais de mots de passe, de clés ni de codes.</p>
<h2>4. Nœuds</h2>
<p>Le réseau est constitué de nœuds pouvant être exploités par des opérateurs indépendants. L'opérateur d'un nœud est responsable de son exploitation conformément aux lois de son pays.</p>
<h2>5. Absence de garantie</h2>
<p>Nevod est fourni « en l'état ». Nous faisons tout notre possible pour que la communication soit fiable, mais nous ne garantissons pas la remise ininterrompue des messages.</p>
<h2>6. Contact</h2>
<p><a href="mailto:support@nevod.network">support@nevod.network</a></p>
</div></main>
"""

PAGES = {
    "index": ("Nevod", "Nevod, première mise en œuvre de la Zero Knowledge Infrastructure : une messagerie dont le développeur n'a techniquement pas accès aux données des utilisateurs.", INDEX),
    "manifesto": ("Manifeste de la Zero Knowledge Infrastructure", "Le manifeste ZKI, fondement du développement de Nevod. Auteur : Kolpakov Andrey.", MANIFESTO),
    "compare": ("Comparaison", "Nevod face à Signal, Telegram et WhatsApp : pourquoi le chiffrement seul n'est pas ZKI.", COMPARE),
    "security": ("Sécurité et chiffrement", "Comment Nevod chiffre les messages, ce que traite un nœud et pourquoi aucun document d'exportation n'est nécessaire.", SECURITY),
    "cities": ("Pour les villes", "Un réseau urbain de communication de secours fondé sur Nevod, sans internet ni centres de données.", CITIES),
    "download": ("Télécharger", "Nevod pour iPhone, Android et le nœud du réseau.", DOWNLOAD),
    "node": ("Votre nœud", "Comment exploiter votre propre nœud du réseau Nevod.", NODE),
    "about": ("Le projet", "Qui est derrière Nevod et comment nous joindre.", ABOUT),
    "support": ("Assistance", "Assistance, signalements, blocage et suppression de compte dans Nevod.", SUPPORT),
    "privacy": ("Politique de confidentialité", "Quelles données Nevod traite et comment elles sont protégées.", PRIVACY),
    "terms": ("Conditions d'utilisation", "Conditions d'utilisation de Nevod.", TERMS),
}
