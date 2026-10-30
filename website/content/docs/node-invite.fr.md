# Inviter des personnes

Comment les gens arrivent sur votre nœud — sur invitation, sur demande ou librement — et comment ils se retrouvent ensuite, y compris avec des personnes d'autres nœuds. Le mode à utiliser se choisit dans le panneau : **Paramètres → Mode d'admission des cellules** (voir [Premiers réglages](../node-panel/), étape 2).

## L'invitation de l'administrateur

La voie principale, et la seule tant que le nœud fonctionne dans le mode par défaut (`delegated`).

1. Panneau → **Invitations** → choisissez la durée de validité : 1 heure, 24 heures ou 7 jours → **+ Créer un code**.
2. Transmettez l'invitation à la personne de l'une de ces façons :
   - **montrez le code QR** à l'écran : la personne le scanne avec l'appareil photo habituel de son téléphone ;
   - **Copier le lien**, puis envoyez-le par n'importe quelle messagerie ou par e-mail ;
   - **dictez le code court**, du type `ABCD-EFGH` : cela ne marche que si votre nœud est déjà défini dans l'app de la personne.
3. La personne installe Nevod depuis l'App Store, ouvre le lien (la page d'invitation a un bouton **Ouvrir dans Nevod**), saisit un nom et touche **Commencer**.

Ce qu'il faut savoir sur les codes :

- **Chaque code ne sert qu'une fois.** Un code par personne. Un code utilisé est marqué « utilisé » dans la liste, avec la personne qui l'a utilisé.
- **Durée de validité.** Ne choisissez pas une semaine pour un code publié dans une discussion de groupe : tant qu'il n'est pas utilisé, quiconque le récupère peut s'en servir. 1 heure, c'est pour un code que vous montrez à quelqu'un en personne.
- **Le lien ne révèle rien de superflu.** Il ne contient que l'adresse du nœud et le code. La page d'invitation sur nevod.network ne voit ni le code ni l'adresse : ils restent dans la partie du lien après `#`, que le navigateur n'envoie pas au serveur.

Si la personne utilise déjà Nevod sur un autre nœud, l'invitation ne la fait pas changer d'elle-même : l'app la prévient qu'il faut d'abord réinitialiser son identité (**Profil → Réinitialiser l'identité…**). La réinitialisation supprime définitivement son identité, ses contacts, les messages sur le téléphone et son inscription sur l'ancien nœud. Pour simplement discuter, inutile de changer : échanger les contacts suffit (voir plus bas).

## Les membres invitent eux-mêmes

En mode `delegated`, vous pouvez confier les invitations à des personnes de confiance : panneau → **Invitations** → **Cellules admises** → activez **Peut inviter** pour la personne voulue. Dans son app, **Profil → Inviter quelqu'un** crée alors un code, et l'app affiche un code QR à scanner.

En mode `open`, tout membre peut inviter — mais dans ce mode, aucun code n'est nécessaire de toute façon.

## Les demandes avec approbation

Le mode `admin` convient si vous voulez qu'on puisse trouver le nœud et demander à le rejoindre, tout en gardant la décision.

1. La personne trouve votre nœud dans « Explorer le réseau » et touche **Rejoindre ce nœud** (si le nœud y est visible ; voir [Premiers réglages](../node-panel/), étape 4), ou, au premier lancement de l'app, touche **Changer de serveur…** et saisit l'adresse du nœud `node.example.org/nevod-ws`.
2. L'app envoie elle-même une demande et affiche « En attente d'approbation ».
3. La demande apparaît dans le panneau, sur la page **Demandes d'adhésion**. Si votre `cell_id` est inscrit dans **Paramètres → Administrateurs**, vous recevez aussi un message dans Nevod.
4. **Approuver** : la personne reçoit une notification et entre aussitôt. **Refuser** : l'app lui indique que sa demande a été refusée.

Les codes d'invitation fonctionnent aussi en mode `admin` : avec un code, on entre aussitôt, sans demande.

## L'inscription libre

En mode `open`, quiconque connaît l'adresse du nœud peut s'inscrire. Cela convient à une communauté ouverte. Sachez que :

- le nœud ne supprime jamais d'inscriptions ni ne libère de noms de lui-même : le ménage se fait à la main, sur la page **Aperçu** (bouton ✕) ;
- les noms de service (Nevod, administrator, support, etc.) ne peuvent être pris dans aucun mode.

## Comment les membres se retrouvent

S'inscrire sur le même nœud ne fait pas des gens des contacts. Pour discuter, il faut échanger les contacts :

- **Profil → Partager ma carte** : affiche un code QR et le texte de la carte ; l'autre personne : **Contacts → Ajouter un contact**, puis scanne le QR ou colle le texte ;
- la carte peut être envoyée par n'importe quel moyen : elle ne contient rien de secret, seulement un identifiant et des clés publiques.

Les personnes **d'autres nœuds** s'ajoutent de la même façon : la carte contient l'adresse de leur nœud d'attache. Pour que ces conversations fonctionnent, votre nœud doit être [connecté au réseau Nevod](../node-network/).

> Supprimer un utilisateur (panneau → **Aperçu** → ✕) révoque entièrement son admission : l'inscription, les messages non remis et les jetons de notification sont supprimés. Pour revenir, la personne aura besoin d'une nouvelle invitation.
