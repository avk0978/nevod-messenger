# Sécurité et sauvegardes

Ce que Nevod protège de lui-même, comment il vous protège des escrocs et des attaques, ce que vous devriez faire, comment vous protéger des inconnus, comment verrouiller une discussion par mot de passe, comment bloquer et signaler — et pourquoi Nevod ne sauvegarde pas les conversations.

## Ce qui est protégé sans que vous ayez à intervenir

- **Les conversations et les appels sont chiffrés** sur votre téléphone avec la clé de votre interlocuteur. Ni les nœuds, ni les développeurs de Nevod, ni Apple ne peuvent les voir.
- **Les clés, les contacts et l'historique des messages ne sont conservés que sur votre téléphone.** Ils ne figurent ni dans les sauvegardes iCloud ou d'ordinateur, ni sur les nœuds, ni chez le développeur.
- **Un nœud ne sait que ce qu'il faut pour acheminer un message :** qui y est inscrit, à qui vous écrivez et quand — mais pas ce que vous écrivez.

Comment cela fonctionne en détail : sur la page [Sécurité](../../security/).

## Protection contre les escrocs et les attaques

- **Personne ne peut vous trouver par votre numéro de téléphone.** Nevod n'a ni numéros de téléphone ni adresses e-mail : ils ne peuvent donc pas être tirés d'une base de données piratée pour du spam ou des appels frauduleux. Seul quelqu'un qui a votre carte, ou un membre de votre nœud, peut vous écrire.
- **Il n'y a pas de mot de passe de compte : rien à voler.** Il ne peut être ni espionné, ni deviné, ni soutiré. À la connexion, le téléphone prouve au nœud qu'il détient la clé, mais la clé elle-même ne quitte jamais le téléphone.
- **Personne ne peut se faire passer pour l'administration.** Les noms de service — administrator, support, Nevod et leurs imitations — ne peuvent pas être enregistrés. La vraie administration porte le badge bleu ✓, l'administrateur d'un nœud privé la mention **Administrateur du nœud**. Un compte portant un nom de service sans badge ni mention est signalé par l'app avec un ⚠ orange et un avertissement dans la discussion.
- **Les fausses notifications ne passent pas.** Une notification de nouveau message ne contient aucun texte qu'un tiers pourrait choisir : seulement « Nouveau message » et le nom de l'expéditeur, et les noms de service y sont remplacés par « Nevod ». Une notification « de Nevod » vous demandant de saisir un code ou de suivre un lien est une escroquerie.
- **Votre nœud ne peut pas être usurpé.** Tout ce qui vient du nœud est signé avec sa clé, et l'app vérifie la signature. Même sur le Wi-Fi d'un tiers, personne entre les deux ne peut se faire passer pour votre nœud ni glisser de faux messages en son nom.
- **Les fichiers et images dangereux sont écartés.** Les attaques les plus dangereuses contre les téléphones — comme le logiciel espion Pegasus — arrivent sous forme d'une image ou d'un fichier spécialement préparés et agissent sans un seul toucher. C'est pourquoi Nevod vérifie tout ce qu'il reçoit des autres : la taille des fichiers est limitée et le type doit correspondre au contenu ; sinon, le fichier n'est pas affiché comme image ou vidéo et ne s'ouvre pas tout seul. Les avatars ne sont acceptés que de vos contacts et des membres de votre nœud, et l'app n'affiche jamais l'image reçue : elle la redessine elle-même.
- **Quand le téléphone est verrouillé, les fichiers sont fermés.** Les photos, vidéos et fichiers des discussions sont chiffrés par iOS et deviennent inaccessibles quelques secondes après le verrouillage, même pour quelqu'un qui aurait accédé à la mémoire du téléphone. Le sélecteur d'apps affiche une couverture Nevod à la place de votre conversation.
- **Pirater un nœud n'expose pas vos conversations.** Un nœud ne contient ni le texte des messages ni vos clés : même avec un accès au nœud, un attaquant ne peut pas lire vos conversations.
- **Les nœuds vérifiés sont signalés.** Les nœuds du projet Nevod portent dans **Explorer le réseau** un anneau doré : il est confirmé par la signature du projet, et un faux nœud ne peut pas l'obtenir.

## Ce que vous devriez faire

Le point le plus vulnérable, c'est le téléphone lui-même : qui déverrouille votre téléphone voit aussi vos conversations. Et si un logiciel espion ayant piraté iOS lui-même est déjà sur le téléphone, il voit tout ce que vous voyez à l'écran : aucune app, Nevod compris, ne peut vous en protéger. Il est donc important qu'il n'y entre pas.

- **Un code sur l'iPhone** : indispensable, et pas un code simple comme 000000.
- **Gardez iOS à jour** : les mises à jour corrigent les failles qu'exploitent les logiciels espions.
- **Redémarrez votre téléphone de temps en temps.** Beaucoup de logiciels espions ne survivent pas à un redémarrage.
- **Si vous êtes journaliste, défenseur des droits humains ou pourriez être une cible pour une autre raison**, activez le **Mode Isolement** de l'iPhone : **Réglages → Confidentialité et sécurité → Mode Isolement**. Il ferme bien des voies qu'empruntent les attaques comme Pegasus.
- **Un mot de passe sur les discussions importantes** : voir ci-dessous.
- **Ne donnez jamais de codes ni de clés.** L'administration de Nevod n'écrit que dans l'app, depuis le compte **administrator** avec le badge ✓ (sur un nœud privé, avec la mention **Administrateur du nœud**), jamais par e-mail, et ne demande jamais de mot de passe, de clé ni de code. Celui qui en demande est un escroc.

## Mot de passe de discussion

Vous pouvez verrouiller une discussion par mot de passe : même quelqu'un qui tient votre téléphone déverrouillé ne pourra pas l'ouvrir.

1. Ouvrez la discussion → la roue dentée en haut à droite → activez **Protection par mot de passe**.
2. Définissez deux mots de passe :
   - **Mot de passe de déverrouillage** : il sert à ouvrir la discussion ;
   - **Mot de passe de contrainte** : pour le cas où l'on vous force à ouvrir la discussion. Si vous le saisissez à la place du vrai, la conversation de cette discussion est **supprimée en silence** de votre téléphone, et l'écran affiche le classique « Mot de passe incorrect » : vu de l'extérieur, cela ressemble à une faute de frappe.
3. Les mots de passe doivent être différents. Pour les changer, au même endroit : **Changer les mots de passe**.

> Le mot de passe de la discussion n'est conservé que sur ce téléphone, et pas le mot de passe lui-même mais son empreinte (hash). **Un mot de passe oublié ne peut pas être récupéré**, ni par vous ni par les développeurs, et la discussion ne pourra plus être ouverte. Choisissez un mot de passe que vous n'oublierez pas. Le mot de passe de contrainte ne supprime la conversation que chez vous : votre interlocuteur la conserve.

## Protection contre les inconnus

Les personnes à qui vous avez donné votre carte ne sont pas les seules à pouvoir vous écrire et vous appeler. Sur un nœud ouvert comme Nevod Open, n'importe qui peut s'inscrire, et les membres du nœud se voient dans **Contacts → Sur ce nœud**. De plus, quelqu'un avec qui vous échangez peut transmettre votre carte à un autre. Un inconnu, ici, c'est quelqu'un qui n'est pas dans vos contacts.

**Profil → Sécurité** propose deux réglages. Les activer ou non, c'est vous qui décidez ; au départ, ils sont tous deux désactivés :

- **Appels des contacts uniquement** : un appel de quelqu'un qui n'est pas dans vos contacts est refusé en silence, le téléphone ne sonne pas. L'appel apparaît dans l'historique comme manqué.
- **Images d'inconnus — au toucher** : les photos et vidéos de quelqu'un qui n'est pas dans vos contacts ne s'affichent pas tout de suite : la discussion montre un emplacement **Afficher**, et l'app n'ouvre le fichier qu'après que vous l'avez touché. Ainsi, même une image piégée ne peut pas se déclencher toute seule.

Sur un nœud fermé, où l'administrateur connaît tous les membres, ces réglages sont généralement inutiles. Sur un nœud ouvert, il vaut la peine de les activer.

## Bloquer et signaler

- **Bloquer** quelqu'un : réglages de la discussion (la roue dentée) → **Bloquer**. Il ne pourra plus vous écrire ni vous appeler, et n'en saura rien. La liste des personnes bloquées : **Profil → Sécurité → Bloqués**.
- **Signaler un message** : maintenez le doigt dessus → **Signaler**. Signaler une personne : réglages de la discussion → **Signaler**.
- **Signaler un abus** sans discussion précise : **Profil → Sécurité → Signaler un abus**.

Le signalement est envoyé à l'administration de votre nœud, sous forme de message dans l'app au compte administrator (ou par e-mail à abuse@nevod.network). Les messages de Nevod sont chiffrés et l'administration ne les voit pas : l'app joint donc au signalement le texte du message signalé. La réponse arrive dans la discussion avec administrator. Vous pouvez bloquer la personne en même temps que vous la signalez : **Bloquer aussi**.

## Pas de sauvegarde, et c'est voulu

Les clés, les contacts et l'historique des messages n'existent que sur votre téléphone. Par conséquent :

- **si le téléphone est perdu, cassé ou réinitialisé, les conversations ne peuvent pas être récupérées ;**
- **supprimer l'app efface aussi l'historique ;**
- **il n'existe pas encore de transfert vers un nouveau téléphone.** Sur un nouveau téléphone, vous créerez une nouvelle identité, et vos contacts auront besoin de votre nouvelle carte.

C'est la conséquence de la conception de Nevod : une copie permettant de restaurer vos conversations serait aussi une copie à laquelle quelqu'un d'autre pourrait accéder. Si vous devez conserver longtemps quelque chose d'une conversation, enregistrez-le à part : photos et fichiers, via **Partager**.

## Réinitialiser l'identité

**Profil → Réinitialiser l'identité…** supprime définitivement votre identité, vos contacts, les messages sur le téléphone et votre inscription sur le nœud. L'app vous demande de taper un mot de confirmation pour éviter toute réinitialisation par erreur.

Elle sert si vous voulez repartir de zéro ou changer de nœud. Vos contacts verront **Identité supprimée** dans votre discussion ; pour vous écrire à nouveau, il leur faudra votre nouvelle carte.
