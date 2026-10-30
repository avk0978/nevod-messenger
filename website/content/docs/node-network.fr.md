# Rejoindre le réseau Nevod

Pourquoi un nœud a besoin du réseau commun, comment le rejoindre d'un clic et ce que voient ensuite les autres nœuds.

## Pourquoi rejoindre le réseau

Un nœud relié à personne est une île. Il fonctionne, mais :

- **ses utilisateurs ne peuvent écrire et appeler qu'entre eux.** Écrire à quelqu'un d'un autre nœud, ou recevoir un message de sa part, est impossible : le nœud ne sait pas où l'envoyer ;
- **les téléphones ne reçoivent pas de notifications** tant que l'app est fermée : seuls les nœuds du projet, qui ont la clé Apple, peuvent envoyer des notifications push à Nevod sur l'App Store, et ils le font pour les nœuds du réseau ;
- **les appels à travers des réseaux difficiles peuvent ne pas s'établir :** un nœud sans son propre relais d'appels (TURN) en obtient un auprès des nœuds du réseau — voir [Appels via votre propre nœud](../node-turn/).

Il vaut donc presque toujours la peine de connecter votre nœud au réseau, même un nœud fermé de famille ou d'organisation. Rejoindre le réseau **n'ouvre pas l'inscription** et **n'affiche pas le nœud dans « Explorer le réseau »** : c'est toujours vous qui décidez, dans les paramètres, qui admettre et si le nœud est visible.

## Comment rejoindre le réseau

1. Vérifiez que le port **8765** du serveur est ouvert depuis l'extérieur, à la fois dans `ufw` et dans le pare-feu de l'hébergeur (voir l'[installation](../node-install/), étapes 1 et 5). C'est par lui que les nœuds communiquent entre eux.
2. Panneau → **Nœuds** → **Rejoindre le réseau Nevod**.
3. Au bout de quelques secondes, un message confirme la connexion. L'état en haut du bloc devient « connecté · nœuds en ligne : N », et les nœuds du réseau apparaissent dans la liste **Nœuds connus**.

Le nœud rejoint le réseau par l'intermédiaire de Nevod Open, un nœud du projet qui admet les nœuds sans invitation. L'authenticité d'Open est vérifiée grâce à l'empreinte de son certificat, intégrée au programme du nœud : elle ne peut pas être substituée en chemin.

Si le panneau indique que **le nœud du réseau n'a pas pu joindre votre nœud depuis l'extérieur**, la connexion a bien eu lieu, mais personne ne peut se connecter à vous en retour. C'est presque toujours le port 8765 qui est fermé. Ouvrez-le et cliquez à nouveau sur le bouton. Vous pouvez aussi vérifier plus tard : **Diagnostic → Vérifier → Accessibilité externe**.

La connexion est conservée : après un redémarrage, le nœud reprend contact de lui-même avec tous les nœuds qu'il connaît.

## Rejoindre le réseau par un autre nœud

Si vous connaissez l'administrateur d'un autre nœud, vous pouvez rejoindre le réseau par son nœud plutôt que par Open :

1. Lui, dans son panneau : **Nœuds → Invitations de nœuds → + Créer une invitation de nœud**, puis il vous remet le jeton en main propre (le jeton est valable 10 minutes).
2. Vous : **Nœuds** → collez le jeton dans le champ **Jeton de l'administrateur d'un autre nœud** → **Rejoindre avec un jeton**.

Le résultat est le même : votre nœud fait partie du réseau. De la même façon, vous pouvez faire entrer dans le réseau, par le vôtre, un nœud que vous connaissez : créez un jeton pour lui.

## Ce que voient les autres nœuds

Les nœuds du réseau échangent une liste des nœuds. Sur votre nœud, elle contient :

- l'identifiant du nœud (`node_id`), son nom et son adresse pour les connexions entre nœuds (`domaine:8765`) ;
- l'empreinte du certificat du nœud ;
- si le nœud est visible dans « Explorer le réseau », et s'il a son propre relais d'appels et sa propre clé de notification.

Si le nœud est visible dans « Explorer le réseau » (réglage `open`), les nœuds du réseau apprennent aussi quelles cellules y sont inscrites — par leurs identifiants, sans les noms. Un nœud fermé ne le communique pas : un message destiné à l'un de ses utilisateurs arrive à l'adresse figurant sur la carte de contact, qui indique le nœud d'attache.

Ce que les nœuds du réseau ne reçoivent jamais : le texte des messages, les fichiers, les appels, les contacts des utilisateurs, les noms et les clés des cellules d'un nœud fermé.

## Quitter le réseau

Il n'existe pas encore de bouton « quitter le réseau ». Les autres nœuds retirent d'eux-mêmes de leurs listes un nœud qui ne s'est pas manifesté depuis 72 heures. Pour déconnecter définitivement le nœud du réseau, arrêtez-le ou fermez le port 8765.
