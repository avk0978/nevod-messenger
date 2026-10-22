# Réseaux distribués de données à faible charge : concept, classification et analyse comparative

**Auteur du concept :** Kolpakov Andrey

**Version :** 30 septembre 2026

**Ressources liées :** [Manifeste Zero Knowledge Infrastructure](/fr/manifesto/), [comparaison des réseaux](/fr/compare/#low-load).

---

## Résumé

L'article introduit le concept de *réseau distribué de données à faible charge* : un réseau dans
lequel la charge de chaque nœud (trafic, stockage, état de service) est limitée par le cercle de
participants de ce nœud et ne croît pas avec la croissance du réseau dans son ensemble. On montre
que les classifications de la charge utilisées en théorie des télécommunications (taux
d'utilisation, erlangs, points du « genou » (knee) et de la « falaise » (cliff) sur la courbe du débit en fonction de la charge, classes de qualité de service)
décrivent l'*état* d'un réseau à un instant donné et non une propriété de son architecture, et ne
permettent donc pas de distinguer les réseaux selon ce trait. On propose six traits d'un réseau à
faible charge et une classification LL-0…LL-3 selon le comportement asymptotique de la charge par
nœud. Quinze réseaux sont comparés, de FidoNet (1984) à Nevod (2026), et leurs prédécesseurs dans
la littérature sont nommés : réseaux d'ami à ami (F2F), réseaux tolérants aux délais (DTN), tables
de hachage distribuées, logiciels local-first et réseaux communautaires (community networks).

**Mots-clés :** réseaux distribués, décentralisation, charge par nœud, passage à l'échelle, F2F,
DTN, réseaux pair-à-pair, messageries, Zero Knowledge Infrastructure.

---

## 1. Introduction

La plupart des services de messagerie actuels sont centralisés : tout le réseau est servi par les
serveurs d'une seule entreprise, et la charge de ces serveurs croît avec le nombre d'utilisateurs.
Les alternatives décentralisées (réseaux fédérés, réseaux superposés pair-à-pair, réseaux d'anonymat) répartissent la *propriété* de l'infrastructure mais, comme on le verra plus loin,
généralement pas la *charge* : un serveur de fédération ou un nœud superposé transporte le trafic,
l'historique et l'état de service produits par les utilisateurs d'autrui, et sa charge croît de
nouveau avec la taille du réseau ou de sa partie populaire.

Le but de ce travail est d'isoler la classe de réseaux dans lesquels la charge d'un nœud dépend uniquement de son propre cercle : les utilisateurs et agents logiciels (bots, agents d'IA, services) dont il est le nœud d'attache ; de la définir, de proposer une classification mesurable et de comparer les réseaux existants selon ce trait.

## 2. La charge dans les réseaux de données : concepts existants

### 2.1 Taux d'utilisation

En théorie des files d'attente, la charge d'un canal ou d'un nœud se caractérise par le taux
d'utilisation ρ = λ/μ, rapport entre le taux d'arrivée et le taux de service [1]. Quand ρ → 1, la
longueur de la file et le délai croissent sans limite ; pour ρ > 1 le système est surchargé. En
pratique on utilise des niveaux indicatifs : utilisation faible (ρ < ~0,3), modérée (0,3–0,7),
élevée (0,7–0,9), saturation et surcharge ; les opérateurs dimensionnent généralement les liaisons
avec une marge jusqu'à ~70–80 % à l'heure de pointe. Ces seuils sont des repères d'ingénierie, pas
une norme unique.

### 2.2 Télétrafic : erlangs et heure chargée

En téléphonie, l'intensité du trafic se mesure en erlangs (1 Erl correspond à un canal occupé en
continu) [2] ; le dimensionnement se fait sur l'heure chargée ; on distingue le trafic offert,
écoulé et perdu, et le degré de service se fixe comme une probabilité de blocage admissible
(formules d'Erlang B et C) [1, 2].

### 2.3 Réaction d'un réseau à la hausse de la charge : le « genou » et la « falaise »

Jain, Ramakrishnan et Chiu [3] ont décrit trois zones de fonctionnement d'un réseau : avant le
« genou », le débit croît avec la charge pour un délai faible ; entre le « genou » et la
« falaise », le débit ne croît presque plus tandis que le délai augmente vite ; au-delà de la
« falaise » surviennent la congestion et l'effondrement. Au « genou », le rapport entre débit et délai (la « puissance » du réseau) atteint son maximum ; sur cette distinction reposent l'évitement de la congestion (congestion avoidance : maintenir le fonctionnement près du « genou ») et le contrôle de congestion (congestion control : empêcher la chute de la « falaise »). Le contrôle de congestion de TCP repose
sur ces idées [4].

### 2.4 Classes de trafic et de qualité de service

L'architecture de services différenciés DiffServ [5] introduit des comportements de transfert
(Expedited Forwarding EF, Assured Forwarding AF, Best Effort BE) ; la Recommandation UIT-T Y.1541
[6] définit des classes de qualité 0–5 pour les réseaux IP selon le délai, la gigue et les pertes.
Ce sont des classifications d'*exigences* de livraison, pas de charge.

### 2.5 Régimes de charge : de la sous-charge à l'effondrement

Les régimes de fonctionnement d'un réseau selon sa charge sont décrits dans les normes et les
travaux classiques :

| Régime | Où il est défini | Signification |
|---|---|---|
| Sous-charge (underutilization) | descriptif, non défini dans les normes | les liaisons sont nettement inactives ; souvent une réserve de capacité voulue (overprovisioning) |
| Charge normale | UIT-T E.500 [36] | périodes d'activité fréquentes où les attentes des utilisateurs doivent être satisfaites ; on y fixe les objectifs de degré de service |
| Charge élevée | UIT-T E.500 [36] | périodes de pointe peu fréquentes : les attentes peuvent ne pas être satisfaites, mais les performances doivent rester suffisantes pour que la congestion ne se propage pas dans le réseau |
| Surcharge | UIT-T E.412 [37] ; prise en compte dans les normes GOST sur les réseaux de communication [39] | le trafic dépasse la capacité du réseau ; des mesures de gestion s'activent : contrôle automatique de congestion, réservation de circuits, réacheminement |
| Effondrement par congestion (congestion collapse) | RFC 896, J. Nagle, 1984 [38] | chaque paquet est envoyé plusieurs fois et le débit utile tombe presque à zéro ; observé pour la première fois en octobre 1986, quand la dorsale NSFnet est passée de 32 kbit/s à 40 bit/s |

Il n'existe pas de terme établi pour un réseau « pleinement chargé » ; le niveau pour lequel un
réseau est dimensionné correspond à la « charge normale » de E.500.

Tous ces régimes sont des **états** d'un réseau à un instant donné : le même réseau est sous-chargé
le matin, en charge normale le soir et surchargé lors d'une panne. L'axe des régimes et l'axe des
classes architecturales introduit plus bas sont indépendants : un réseau de classe LL-0 peut lui
aussi se retrouver surchargé, par exemple si un nœud fonctionne sur une liaison faible.

### 2.6 Passage à l'échelle de la charge par nœud

Dans la littérature sur les systèmes distribués, le coût d'un nœud s'évalue de manière
asymptotique en fonction du nombre de participants N : diffuser à tous les nœuds coûte O(N) par
message ; les tables de hachage distribuées (Chord [7], Kademlia [8]) coûtent O(log N) pour le
routage et la table de voisins. On trouve aussi l'affirmation que, dans les systèmes pair-à-pair,
la charge maximale par nœud ne croît pas avec le nombre de nœuds, car les nouveaux nœuds apportent
plus de ressources qu'ils n'en consomment [9] ; mais il s'agit d'un *équilibrage statistique* d'une
charge constituée des requêtes d'autrui.

### 2.7 Conclusion

Les classifications 2.1–2.5 répondent à la question « à quel point le réseau est-il chargé
*maintenant* » ; selon elles, le même réseau est tantôt peu, tantôt très chargé. L'expression russe
« réseau peu chargé » (малонагруженная сеть) s'emploie en pratique précisément dans ce sens
descriptif (un réseau ou une machine faiblement utilisés) et ne désigne pas une classe
d'architecture. En téléphonie filaire, le mot « charge » a même un troisième sens : la « ligne
chargée » munie de bobines d'inductance (pupinisation). Seul l'axe 2.6 concerne une *propriété de
l'architecture*, et il n'existe pas de classification normalisée des réseaux selon cet axe.

## 3. Réseaux distribués : panorama des approches

**Services centralisés** (WhatsApp, 2009 ; Telegram, 2013 ; Signal, 2014 [10]) : le chiffrement de
bout en bout du contenu peut être solide, mais les serveurs, les comptes et les métadonnées sont
détenus par une seule organisation ; la charge des serveurs croît avec toute l'audience.

**Réseaux fédérés** : courrier électronique, Matrix (2014) [11], ActivityPub/Mastodon (2016 ;
Recommandation W3C 2018) [12]. La propriété est répartie entre les serveurs, mais la charge d'un
serveur croît avec ses liens externes : dans Matrix, l'historique d'un grand salon est répliqué sur
chaque serveur participant ; dans ActivityPub, la diffusion croît avec le nombre d'abonnés.

**Réseaux superposés pair-à-pair et tables de hachage distribuées** : Freenet (2001) [13],
Chord [7], Kademlia [8]. Les nœuds sont égaux et la charge est en O(log N), mais un nœud stocke et
achemine des données d'inconnus.

**Réseaux d'ami à ami (F2F).** Le terme a été proposé par D. Bricklin en 2000 [14] : un nœud ne se
connecte qu'aux nœuds de ses connaissances. Exemples : Turtle (Popescu, Crispo, Tanenbaum, 2004)
[15], OneSwarm [16], le mode « darknet » de Freenet, RetroShare, GNUnet ; le stockage sur des nœuds
de confiance en relève aussi [17]. Le nombre de connexions d'un nœud est borné par son nombre
d'amis [18, 19], mais les messages suivent des chaînes d'amis à travers des nœuds non concernés, et
le routage dans ces réseaux reste un problème difficile [18, 19, 20]. **Les réseaux F2F sont le
prédécesseur le plus proche du concept proposé** : ils ont été les premiers à limiter un nœud à son
cercle de connaissances, mais par le nombre de connexions, pas par la charge.

**Réseaux superposés d'anonymat** (routage en oignon) : prolongement des réseaux de mélange de D. Chaum (1981) [40] et du routage en oignon de D. Goldschlag, M. Reed et P. Syverson (1996) [41] ; mises en œuvre : Tor (2002–2004) [21] et Session (2020) [22]. Les nœuds relais, tenus par des bénévoles ou des opérateurs, transportent le transit d'autrui en proportion de leur bande passante.

**Réseaux tolérants aux délais (DTN)** : l'architecture de Fall (2003) [23], RFC 4838 [24], Bundle
Protocol v7, RFC 9171 [25] : « stocker et retransmettre » en cas de coupures. Une mise en œuvre
historique du même principe est FidoNet (1984) [26] ; une mise en œuvre moderne, NNCP (2016) [27].

**Piles pour tout support et réseaux radio** : Reticulum (protocole publié en 2016) et la
messagerie LXMF [28] : fonctionnement de quelques bits par seconde (LoRa, radio par paquets)
jusqu'à internet, chiffrement par défaut ; Meshtastic (2020) [29] : messages texte via des modules
radio LoRa.

**Réseaux communautaires** (community networks) : Freifunk, Guifi.net [30] : des réseaux créés et entretenus par les utilisateurs eux-mêmes.

**Logiciels local-first** [31] et **Secure Scuttlebutt** (2014) [32] : les données restent chez
l'utilisateur ; dans SSB, un nœud conserve les flux de ses amis et des amis de ses amis, et la
synchronisation a lieu quand les nœuds se rencontrent.

**Relais** : Nostr (2020) [33] : de simples serveurs relais, dont les plus populaires supportent la
charge de toute l'audience.

## 4. Le concept de réseau distribué à faible charge

### 4.1 Définition

**Un réseau distribué de données à faible charge** est un réseau dans lequel chaque nœud sert un
cercle de participants petit et naturellement limité et transporte surtout leur propre trafic. Les
nœuds sont égaux et fonctionnent sur du matériel ordinaire. Le réseau ne transmet que le
nécessaire, tolère les délais et les coupures et n'a pas de centre dont l'arrêt ou la saisie
stopperait son fonctionnement.

Le concept porte sur la *conception* d'un réseau, non sur sa charge à un instant donné
(sections 2.5, 2.7).

### 4.2 Traits

1. **Cercle propre** : la charge d'un nœud croît avec son cercle, les personnes et les agents logiciels qu'il sert, non avec la taille de tout le réseau. Le trait principal.
2. **Matériel ordinaire** : un ordinateur domestique, un mini-serveur ou un routeur ; pas besoin de
   centre de données.
3. **Économie de transmission** : d'abord le texte et les signaux, les données volumineuses à la
   demande.
4. **Tolérance aux délais** : sans connexion, le message attend et part plus tard, y compris par un
   canal lent.
5. **Pas de centre** : aucun point unique de panne, de blocage ou de saisie.
6. **Aveuglement du nœud** : le nœud ne transporte que du texte chiffré et ne peut pas le lire (le
   principe Zero Knowledge Infrastructure).

### 4.3 Ce qui le distingue de ses prédécesseurs

| Concept | Ce qui est limité | Ce qui le distingue |
|---|---|---|
| F2F [14–20] | le nombre de connexions du nœud, par son cercle de connaissances | le transit le long de chaînes de connaissances demeure ; la charge n'est pas limitée |
| DHT [7, 8] | la croissance de la charge, par un logarithme | le nœud transporte des données d'inconnus |
| DTN [23–25] | rien sur la charge | porte sur les délais et les coupures, pas sur la répartition de la charge |
| Local-first [31] | le lieu de stockage des données : chez l'utilisateur | porte sur la propriété des données, pas sur le réseau |
| **Réseau à faible charge** | **toute la charge du nœud, par son cercle** | combinaison des traits 1–6 ; le trait 1 est déterminant |

## 5. Classification : classes LL

**La classe de charge d'un nœud** est déterminée par celle de ses trois composantes qui croît le plus vite : trafic transporté, données stockées, état de service maintenu. N est le nombre de participants du réseau, k la taille du cercle du nœud : le nombre de ses utilisateurs et agents logiciels. La notation O(x) (« grand O de x » ; introduite par P. Bachmann en 1894 [42] et popularisée par E. Landau en 1909 [43]) signifie qu'une grandeur ne croît pas plus vite que x multiplié par une constante ; pour la classe LL-0, l'estimation de la charge ne contient pas N, seulement k.

| Classe | Charge du nœud | Définition |
|---|---|---|
| **LL-0** | O(k) | le nœud transporte, stocke et mémorise uniquement ce qui concerne son cercle ; pas de transit pour autrui |
| **LL-1** | O(k) + part d'autrui bornée | en plus, transit ou stockage pour d'autres, borné indépendamment de N (limite de sauts, quotas, voisins choisis par le nœud lui-même) |
| **LL-2** | O(log N) | la charge croît lentement (tables de hachage distribuées) |
| **LL-3** | O(N) ou non bornée par son cercle | la charge croît avec tout le réseau ou dépend du nombre d'utilisateurs extérieurs qui sollicitent le nœud (un serveur populaire, un relais) |

Un réseau à faible charge au sens strict est un réseau de classe **LL-0** ; LL-1 est presque à
faible charge.

## 6. Analyse comparative

### 6.1 Traits (1 = rempli, ½ = en partie, 0 = non) et classes

| Réseau | Année | Cercle propre | Matériel | Économie | Délais | Pas de centre | Nœud aveugle | Classe |
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

Notes. Signal et WhatsApp obtiennent ½ au trait 6 : le contenu est chiffré de bout en bout, mais
l'organisation voit les métadonnées et gère les serveurs. Dans Reticulum et NNCP, des nœuds
intermédiaires transportent et stockent les paquets d'autrui (trait 1 = ½, classe LL-1). L'année
est celle de la première version publique (Reticulum : en développement depuis 2014 ; Signal :
prédécesseurs TextSecure/RedPhone, 2010 ; Briar : en développement depuis 2011).

### 6.2 Observations

- Selon le trait principal (classe LL), les plus stricts sont Nevod, Briar et Secure Scuttlebutt
  (LL-0) ; Reticulum et NNCP relèvent de LL-1.
- Tous les réseaux centralisés et fédérés, ainsi que les réseaux superposés d'anonymat, sont
  LL-3 : décentraliser la propriété ne signifie pas décentraliser la charge.

## 7. Nevod, exemple de la classe LL-0, et ses limites

Nevod [34] est un réseau de messagerie fondé sur le principe Zero Knowledge Infrastructure : un nœud
(« node ») ne sert que ses propres participants et transporte des messages chiffrés sans accès à
leur contenu ; il n'y a pas de centre ; les nœuds fonctionnent sur du matériel domestique ou des
serveurs loués. La table de service des nœuds croît avec le nombre de *nœuds*, non d'utilisateurs,
et reste petite.

Limites en septembre 2026 (traits pas entièrement remplis, pas de validation pratique) :

- trait 3 : les médias sont transmis en entier, sans aperçu ni téléchargement à la demande ;
- trait 4 : les messages non remis sont conservés 72 heures ; fonctionne uniquement par internet ;
- pas de confidentialité persistante (forward secrecy) : les messages sont chiffrés avec la clé à
  long terme du destinataire ;
- un nœud voit les métadonnées de livraison (qui, à qui, quand) ;
- un prototype fonctionnel sans utilisateurs réels ni audit indépendant ; code fermé ; application
  iOS uniquement.

Les traits ont été tirés des principes de Nevod, la comparaison lui est donc favorable d'emblée ;
la note de Nevod reflète son architecture, non la maturité du produit.

## 8. Questions ouvertes

1. Le stockage pour un destinataire longtemps hors ligne : qui le conserve et combien de temps,
   sans enfreindre la classe LL-0.
2. La recherche de chemin entre de nombreux nœuds sans annuaire central.
3. Un transit borné (LL-1) est-il admissible pour livrer par des canaux lents, et faut-il une
   réciprocité (« tu transportes le trafic d'autrui, on transporte le tien ») ?
4. Quelles composantes comptent comme charge : trafic, stockage, état, consommation d'énergie,
   temps de l'administrateur.
5. Une métrique formelle du cercle du nœud k et sa mesure sur des réseaux réels.

## 9. Conclusion

Les concepts de charge de la théorie des télécommunications décrivent l'état d'un réseau, non une
propriété de son architecture. Le concept proposé de réseau distribué à faible charge isole une
classe architecturale dans laquelle la charge d'un nœud est limitée par son cercle, et complète
les approches connues (F2F, DTN, tables de hachage distribuées, local-first, réseaux
communautaires) par une combinaison de six traits. La classification LL-0…LL-3 rend le concept
mesurable et permet de rattacher n'importe quel réseau à une classe. La validation pratique et une
revue complète de la littérature dans les bases fermées (IEEE, ACM, eLibrary) sont les prochaines
étapes.

---

## Références

{{REFS}}

---

*Note de méthode.* La revue a été menée sur des sources ouvertes ; les bases payantes (IEEE Xplore,
textes intégraux de l'ACM Digital Library, Springer, eLibrary) n'ont pas été consultées de manière
systématique. Les notes des traits et des classes sont des évaluations d'expert fondées sur les
descriptions publiques des réseaux en septembre 2026.
