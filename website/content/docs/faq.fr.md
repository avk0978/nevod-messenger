# Questions et problèmes

Des réponses courtes aux questions fréquentes et que faire si quelque chose ne fonctionne pas. Si votre question n'y figure pas, écrivez-nous (à la fin de cette section).

## Questions générales

**Nevod est-il payant ?**
Non. L'app est gratuite, sans abonnement ni publicité. Vous n'aurez éventuellement à payer qu'un fournisseur d'IA, si vous utilisez des assistants IA avec votre propre clé : voir [Bots et assistants IA](../bots/).

**Faut-il un numéro de téléphone ?**
Non. Nevod n'a besoin ni de numéro de téléphone ni d'adresse e-mail, et ne les demande pas. Seules les personnes avec qui vous avez échangé votre carte vous connaissent.

**Nevod existe-t-il pour Android ou pour ordinateur ?**
Pour l'instant, seulement pour iPhone et iPad. Une version Android est en développement.

**Puis-je utiliser Nevod sur deux appareils à la fois ?**
Pas encore : une identité vit sur un seul appareil. Sur un deuxième iPhone ou iPad, vous aurez une identité distincte avec ses propres contacts.

**J'ai changé de téléphone. Comment transférer mes conversations ?**
Ce n'est pas encore possible : il n'y a pas de transfert vers un nouvel appareil, et Nevod ne sauvegarde volontairement pas les conversations. Sur le nouveau téléphone, créez une nouvelle identité et envoyez votre nouvelle carte à vos contacts. Plus de détails dans [Sécurité et sauvegardes](../security/).

**Comment changer de nœud ?**
Uniquement en réinitialisant l'identité : **Profil → Réinitialiser l'identité…**, puis ouvrez l'invitation vers le nouveau nœud. La réinitialisation supprime définitivement votre identité, vos contacts, les messages sur le téléphone et votre inscription sur l'ancien nœud. Pour simplement discuter avec quelqu'un d'un autre nœud, inutile de changer : sa carte suffit.

## Inscription

| Ce que vous voyez | Que faire |
|---|---|
| « Ce nom est déjà pris, choisissez-en un autre » | ce nom existe déjà sur le nœud, ou c'est un nom de service (administrator, support, Nevod…). Choisissez-en un autre. |
| « Code d'invitation requis » | le nœud n'admet que sur invitation. Demandez une invitation à l'administrateur du nœud ou choisissez un autre nœud. |
| « Code invalide ou expiré — demandez-en un nouveau » | le code a déjà servi ou a expiré. Demandez-en un nouveau. |
| « En attente d'approbation » | le nœud admet sur demande : attendez la décision de l'administrateur ; vous recevrez une notification. |
| « Demande refusée » | l'administrateur du nœud a refusé votre demande. Vous pouvez choisir un autre nœud, par exemple Nevod Open. |
| vous avez ouvert une invitation et l'app affiche « Invitation vers un autre nœud » | vous êtes déjà inscrit sur un nœud. Voir « Comment changer de nœud ? » ci-dessus. |
| vous avez ouvert une invitation et l'app affiche « Vous êtes déjà inscrit sur ce nœud » | l'invitation concerne votre propre nœud : rien à faire. |

## Connexion

**Au-dessus du champ de saisie, la discussion affiche « Pas de connexion » ou longtemps « Connexion… », et rien ne part.**
Vérifiez votre connexion Internet : ouvrez n'importe quel site. Si vous utilisez un VPN, essayez de le désactiver ou de changer de serveur. Passez du Wi-Fi aux données mobiles ou inversement. Si cela n'aide pas, votre nœud est peut-être momentanément indisponible : patientez quelques minutes ; si vous êtes sur un nœud privé, prévenez son administrateur.

**Les notifications n'arrivent pas quand Nevod est fermé.**
- **Réglages de l'iPhone → Nevod → Notifications** : elles doivent être autorisées.
- Vérifiez que Ne pas déranger ou un autre mode de concentration n'est pas activé.
- Vérifiez que les notifications de cette discussion ne sont pas coupées : réglages de la discussion (la roue dentée) → **Notifications**.
- Sur un nœud privé : demandez à l'administrateur de vérifier que le nœud est [connecté au réseau Nevod](../node-network/) ; sinon, les notifications n'arrivent pas.

**Un appel ne s'établit pas.** Voir [Appels](../calls/), « Si un appel ne s'établit pas ».

## Messages et fichiers

**Une horloge orange est affichée à côté d'un message.**
Votre interlocuteur n'est pas connecté : le message l'attend sur le nœud et lui sera remis dès qu'il se connectera. Le nœud conserve ces messages jusqu'à 72 heures : si la personne ne se connecte pas dans ce délai, le message ne lui parviendra pas.

**« Message non envoyé. Renvoyer ? »**
Il n'y avait pas de connexion au moment de l'envoi. Touchez cette ligne quand la connexion est revenue.

**Un fichier ne part pas.**
- Plus de 50 Mo : l'app vous le signale. Choisissez les vidéos via **Photo ou vidéo** : elles seront compressées.
- « Impossible de charger la vidéo » : si la vidéo est stockée dans iCloud, le téléphone n'en a peut-être qu'une copie réduite. Ouvrez la vidéo dans l'app Photos, attendez qu'elle soit entièrement téléchargée et réessayez. Si l'erreur se répète, prévenez-nous (voir « Signaler un problème » ci-dessous).
- « Impossible de compresser la vidéo » : essayez une vidéo plus courte, ou envoyez-la via **Fichier** si elle fait moins de 50 Mo.

**« Impossible d'enregistrer le fichier : stockage plein ».**
Les fichiers reçus occupent de la place sur le téléphone, dans la limite du quota de Nevod. Augmentez-le : **Profil → Stockage → Quota**, ou supprimez les discussions inutiles (dans la liste des discussions, balayez vers la gauche → **Supprimer**).

## Assistants IA

**Le bot indique qu'une clé est nécessaire, ou la clé est refusée.**
Vérifiez que la clé a été copiée en entier et n'a pas été révoquée sur le site du fournisseur, et que votre compte chez le fournisseur est approvisionné ou que la limite gratuite n'est pas épuisée. Vous pouvez changer la clé dans la discussion avec le bot : **Modifier**. Plus de détails dans [Bots et assistants IA](../bots/).

## Signaler un problème

**Profil → Diagnostic** : décrivez ce qui s'est passé et à peu près quand (par exemple, « 2 photos sur 3 ne sont pas arrivées, vers 21 h ») et touchez **Envoyer aux développeurs**. Le journal technique de l'app part avec votre description : il n'est conservé que sur le téléphone et ne contient pas le texte des messages. Le journal est envoyé par e-mail à support@nevod.network ou, si aucun compte e-mail n'est configuré sur le téléphone, à l'administrateur de votre nœud dans Nevod ; la réponse arrive dans la discussion avec lui.

Pour signaler une personne ou un message : voir [Sécurité](../security/), « Bloquer et signaler ».
