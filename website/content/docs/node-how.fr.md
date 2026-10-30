# Comment fonctionne un nœud

Un nœud est un programme installé sur un serveur, par lequel les téléphones échangent des messages et établissent des appels. Voici, en bref, ce que fait un nœud, ce qu'il conserve et ce qu'il ne voit pas, pour que vous sachiez avant l'installation à quoi vous vous engagez.

## Nœud, cellule et nœud d'attache

Chaque utilisateur de Nevod est une **cellule** : une paire de clés de chiffrement créée sur le téléphone et qui ne le quitte jamais. Une cellule s'inscrit sur un nœud : son **nœud d'attache**. C'est par lui que le téléphone reçoit les messages envoyés pendant qu'il était éteint.

Les nœuds sont reliés en un réseau commun. Si vous écrivez à quelqu'un d'un autre nœud, votre nœud transmet le message chiffré à son nœud. Il n'y a pas de serveur central : le réseau, ce sont les nœuds eux-mêmes.

La charge d'un nœud ne dépend que de son propre cercle — ses utilisateurs et ses bots — et non de la taille de tout le réseau : un nœud ne relaie ni ne conserve les messages d'autres nœuds. C'est pourquoi un ordinateur ordinaire suffit à un nœud, et il ne s'alourdit pas, quel que soit le nombre de personnes qui rejoignent Nevod sur d'autres nœuds. Ces réseaux sont dits **à faible charge** (classe LL-0) — voir l'article [« Low-Load Distributed Data Networks »](../../publications/low-load-networks/) (DOI 10.5281/zenodo.23621073).

## Les types de nœuds

Tous les nœuds font tourner le même programme. Ce que devient un nœud — un nœud familial fermé, un nœud communautaire ouvert ou le nœud d'une organisation — dépend de trois réglages du [panneau d'administration](../node-admin/) :

- **qui admettre** : le mode d'admission des cellules : uniquement avec un code d'invitation, avec un code ou sur demande avec votre approbation, ou tout le monde (détails dans le tableau des [Premiers réglages](../node-panel/), étape 2) ;
- **si le nœud est visible dans « Explorer le réseau »** pour les utilisateurs d'autres nœuds ;
- **ce que le nœud montre à ses utilisateurs** : les bots et pages qui y sont publiés.

| Quel nœud | Qui admettre | Visible dans « Explorer le réseau » | Exemple |
|---|---|---|---|
| Fermé : famille, amis, organisation | avec un code d'invitation | non | le nœud d'une entreprise où l'administrateur invite chaque salarié |
| Communauté avec sélection | avec un code ou sur demande avec approbation | oui | le nœud d'un club : tout le monde peut le trouver, mais l'administrateur approuve les membres |
| Communauté ouverte | tout le monde | oui | un nœud public comme Nevod Open |

**Là où tourne le nœud** — sur un serveur loué avec un nom de domaine ou chez vous, sur votre ordinateur — ne change rien à ses possibilités. Un nœud à domicile doit être joignable depuis Internet : redirection de ports sur le routeur et nom de domaine. C'est pourquoi il est plus simple de commencer avec un serveur loué : toute la documentation est écrite pour ce cas.

**Important pour un nœud à domicile : depuis votre réseau local, on le joint selon d'autres règles.** Les téléphones se connectent au nœud par son nom de domaine, et le domaine pointe vers l'adresse externe de votre routeur. Un téléphone sur le Wi-Fi de la maison cherche à joindre cette adresse externe depuis l'intérieur du réseau, et beaucoup de routeurs ne laissent pas passer ces connexions. Le nœud fonctionne alors en données mobiles, mais sur le Wi-Fi de la maison l'app affiche « Pas de connexion ». Se connecter par l'adresse locale du serveur (par exemple `192.168.1.10`) ne marche pas non plus : le certificat est délivré pour le domaine, pas pour l'adresse. Cela se règle sur le routeur, de l'une de ces deux façons :

- activez le **NAT loopback** (aussi appelé NAT hairpinning ou NAT reflection), si le routeur le permet ;
- ou ajoutez dans le DNS du routeur un enregistrement local : votre domaine → l'adresse locale du serveur.

Vérifiez-le juste après l'installation : connectez-vous au nœud depuis un téléphone, à la fois par le Wi-Fi de la maison et par les données mobiles.

**Les nœuds du projet Nevod** — Nevod Open, Dev Planet et quelques autres — ne se distinguent pas des autres par leur programme, mais par trois choses :

- ils disposent d'une clé Apple pour les notifications push et d'un relais d'appels, et les partagent avec les nœuds du réseau (voir plus bas) ;
- dans « Explorer le réseau », ils portent l'**anneau doré** de nœud vérifié et une étiquette de vocation : « Communauté », « Informatif », « Agent IA ». L'anneau est confirmé par la signature du curateur du projet et n'existe pour l'instant que sur les nœuds du projet ;
- **Nevod Open** est le nœud sur lequel l'app inscrit les utilisateurs par défaut, et le point d'entrée dans le réseau pour les nouveaux nœuds : on peut s'y connecter sans invitation.

> Les réglages du panneau comportent aussi « Type de nœud » — `permanent` ou `temporary` — et « ID du nœud parent ». Ils sont **en développement** : des nœuds temporaires (par exemple pour la durée d'un événement). L'app ne les utilise pas encore : laissez `permanent` et l'ID du nœud parent vide.

## Ce que conserve un nœud

- **Les inscriptions des cellules** : l'identifiant, les clés publiques et le nom affiché choisi par l'utilisateur.
- **Les messages non remis**, chiffrés, jusqu'à ce que le destinataire se connecte, mais pas plus de 72 heures. Une fois remis, le message est supprimé.
- **Les jetons de notification** des téléphones, pour « réveiller » un téléphone quand arrive un message ou un appel.
- **Les codes d'invitation**, les demandes d'adhésion, les messages des utilisateurs à l'administrateur du nœud.
- **La liste des autres nœuds du réseau** et ses propres réglages.
- **Les journaux techniques**, de taille limitée (3 fichiers de 10 Mo par conteneur) ; les anciennes entrées sont écrasées.

## Ce que ne voit pas un nœud

- **Le texte des messages, les photos, vidéos, messages vocaux et fichiers.** Ils sont chiffrés sur le téléphone de l'expéditeur avec la clé du destinataire. Le nœud les achemine sans avoir la clé qui permettrait de les ouvrir.
- **Le contenu des appels.** Le son et la vidéo passent entre les téléphones directement ou par un relais (TURN), chiffrés.
- **Les contacts et les conversations sur le téléphone.** Ils ne sont conservés que sur l'appareil.

Ce que le nœud voit en revanche : quelles cellules y sont inscrites et sous quels noms, qui écrit à qui et quand, la taille des messages, les adresses IP des connexions. Ce sont des données d'acheminement : sans elles, le nœud ne pourrait pas fonctionner. Plus de détails dans la [Politique de confidentialité](../../privacy/).

> Le propriétaire du nœud est responsable de son bon fonctionnement et de la sauvegarde de ses données. Il ne peut pas lire les conversations des utilisateurs : cela découle de la conception du réseau, et non d'une promesse.

## Notifications et appels via les nœuds du projet

Seul un nœud qui possède une clé Apple peut envoyer des notifications push à l'app Nevod de l'App Store, et seuls les nœuds du projet en ont une. Un nœud connecté au réseau demande donc à un nœud du projet d'envoyer la notification à sa place. Le nœud du projet voit alors le jeton du téléphone et le nom de l'expéditeur pour le titre de la notification, et le texte est toujours le même : « Nouveau message ». Si l'expéditeur est dans les contacts du destinataire, le téléphone affiche lui-même le nom sous lequel il est enregistré.

**Puis-je envoyer des notifications directement depuis mon nœud ?** Non. Les notifications vers une app de l'App Store ne sont acceptées qu'avec une clé du compte développeur Apple sous lequel l'app est publiée — et Nevod est publié par le projet. Cette clé ne peut pas être confiée aux propriétaires de nœuds : elle ne peut pas être limitée à un seul nœud et permet d'envoyer à n'importe quel utilisateur de Nevod une notification avec n'importe quel texte. C'est pourquoi les notifications passent par les nœuds du projet, et leur texte est toujours « Nouveau message ».

De la même façon, un nœud sans son propre relais d'appels (TURN) en obtient un auprès des nœuds du réseau — voir [Appels via votre propre nœud](../node-turn/).

D'où une conclusion importante : **un nœud non connecté au réseau achemine les messages, mais les téléphones ne reçoivent pas de notifications** tant que l'app est fermée. Comment se connecter : voir [Rejoindre le réseau Nevod](../node-network/).

## De quoi se compose l'installation

Le kit serveur prêt à l'emploi (le dossier `installer/docker` du [code source](https://github.com/avk0978/nevod-messenger)) se compose de deux conteneurs Docker :

| Conteneur | Rôle | Ports |
|---|---|---|
| `nevod_node` | le nœud lui-même | 8765 : pour les autres nœuds ; 8766 : le panneau d'administration, accessible uniquement depuis le serveur lui-même |
| `nevod_caddy` | le serveur web Caddy : obtient tout seul un certificat HTTPS pour votre domaine et transmet au nœud les connexions des téléphones et du panneau | 80 et 443 |

Toutes les données du nœud se trouvent dans le dossier `data/`, à côté du fichier de réglages :

- `node.json` : **l'identité du nœud**, ses clés. Perdre ce fichier, c'est perdre le nœud : on ne peut pas recréer un nœud avec la même identité, et tous les utilisateurs devraient s'inscrire sur un nouveau. Gardez-en une sauvegarde.
- `node.db` : la base de données : inscriptions, invitations, tampon de messages.

## Ce qu'il vous faut

- **Un serveur Linux** : le VPS loué le moins cher suffit : 1 processeur, 1 Go de mémoire, 10 Go de disque. C'est assez pour des dizaines et des centaines d'utilisateurs.
- **Un nom de domaine** (ou sous-domaine) que vous pouvez faire pointer vers le serveur, par exemple `node.example.org`. Sans domaine, les téléphones ne peuvent pas vérifier le certificat HTTPS.
- **Environ une demi-heure** et savoir vous connecter au serveur en SSH. Toutes les commandes figurent dans [Installation pas à pas](../node-install/) : vous pouvez les copier telles quelles.
