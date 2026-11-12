# Premiers réglages dans le panneau d'administration

Le nœud tourne : il faut maintenant lui donner un nom, décider qui admettre et vous y inscrire vous-même. Tout cela se fait dans le panneau d'administration, à l'adresse `https://node.example.org/nevod-admin` (comment l'ouvrir : étape 9 de l'[installation](../node-install/)).

La langue du panneau se change dans son en-tête. La description détaillée de chaque page et de chaque réglage : voir [Le panneau d'administration : toutes les pages et tous les réglages](../node-admin/).

## Où trouver quoi dans le panneau

| Page | À quoi elle sert |
|---|---|
| **Aperçu** | Les cellules (utilisateurs) inscrites sur le nœud. |
| **Paramètres** | Nom du nœud, mode d'admission, visibilité. |
| **Demandes d'adhésion** | Les demandes des utilisateurs, si le nœud fonctionne en mode approbation. |
| **Messages** | Les messages des utilisateurs à l'administrateur du nœud : signalements, questions. Vous pouvez répondre directement d'ici ou écrire en premier à un membre : bouton **écrire** à côté de lui dans **Aperçu**. |
| **Invitations** | Les codes d'invitation pour les utilisateurs. |
| **Nœuds** | La connexion au réseau Nevod et les autres nœuds que connaît votre nœud. |
| **Publication**, **Bots IA** | Les bots et canaux que le nœud montre à ses utilisateurs. |
| **Sécurité** | Des comptes administrateur supplémentaires. |
| **Diagnostic** | L'autodiagnostic du nœud et son journal. |

## 1. Nommez le nœud

**Paramètres → Nom du nœud** → saisissez un nom, par exemple « Famille Martin » ou « École n° 5 » → **Enregistrer**.

Les utilisateurs voient ce nom dans l'app. Les autres nœuds du réseau apprennent le nouveau nom après le redémarrage du nœud (voir plus bas). Les noms qui feraient passer le nœud pour un nœud du projet sont interdits : avec les mots Nevod, admin, support, official, etc.

## 2. Décidez qui admettre

**Paramètres → Mode d'admission des cellules.** Un nouveau nœud fonctionne par défaut **sur invitation** : on ne peut s'inscrire qu'avec un code que vous avez délivré. C'est généralement ce qu'il faut. Dans l'app, sous **Explorer le réseau**, un nœud en mode invitation ou approbation est marqué d'un cadenas 🔒 : chacun voit ainsi d'avance qu'on ne peut pas s'y inscrire librement.

| Mode dans le panneau | Qui peut s'inscrire | Qui crée les codes d'invitation |
|---|---|---|
| `delegated` — uniquement avec un code d'invitation (par défaut) | Uniquement avec un code d'invitation. Sans code, le nœud refuse l'inscription. | Vous, dans le panneau, ainsi que les utilisateurs à qui vous avez donné le droit **Peut inviter**. |
| `admin` — demande + votre approbation | Avec un code : immédiatement. Sans code, l'app envoie elle-même une demande et affiche « En attente d'approbation » ; vous l'approuvez ou la refusez sur la page **Demandes d'adhésion**. | Vous seul, dans le panneau. |
| `open` — sans code | Quiconque connaît l'adresse du nœud. Convient à une communauté ouverte ; sachez qu'il faudra ensuite trier à la main les inscriptions et les noms pris. | Pas besoin de code. |

Le mode s'applique immédiatement.

## 3. Inscrivez-vous sur votre nœud

1. Dans le panneau : **Invitations** → choisissez la durée de validité (1 heure, 24 heures ou 7 jours) → **+ Créer un code**. Un code QR et un code court du type `ABCD-EFGH` s'affichent.
2. Sur votre téléphone, installez Nevod depuis l'App Store.
3. Scannez le code QR avec l'appareil photo habituel du téléphone. C'est un lien : la page d'invitation s'ouvre ; touchez **Ouvrir dans Nevod**. L'app s'ouvre avec l'adresse de votre nœud et le code déjà remplis.
4. Saisissez votre nom et touchez **Commencer**.

Si scanner n'est pas pratique, cliquez sur **Copier le lien** dans le panneau et envoyez-le-vous. Si « Ouvrir dans Nevod » n'a pas fonctionné : dans l'app, touchez **Commencer à discuter**, saisissez votre nom, touchez **Vous avez un code d'invitation ?** et collez le lien dans le champ du code. Le code court à la place du lien ne marche que si votre nœud est déjà défini dans l'app.

> Si Nevod est déjà inscrit sur un autre nœud sur ce téléphone (par exemple sur Nevod Open), l'invitation ne vous fait pas passer sur votre nœud d'elle-même : l'app prévient qu'il faut d'abord réinitialiser l'identité : **Profil → Réinitialiser l'identité…**. La réinitialisation supprime définitivement votre identité, vos contacts, les messages sur le téléphone et votre inscription sur l'ancien nœud. Ensuite, rouvrez le lien d'invitation.

Chaque code ne sert qu'une fois. Créez-en un par personne — plus de détails dans [Inviter des personnes](../node-invite/).

## 4. Décidez si le nœud est visible dans le réseau

**Paramètres → Visibilité dans « Explorer le réseau »** :

- `closed` (par défaut) : le nœud n'apparaît pas dans « Explorer le réseau » pour les utilisateurs d'autres nœuds. Convient à une famille, une organisation, tout groupe fermé.
- `open` : le nœud apparaît dans « Explorer le réseau », et les utilisateurs d'autres nœuds peuvent le trouver. Convient à une communauté ouverte. Le nœud est visible tant qu'il est connecté au réseau, et seulement pour les personnes déjà inscrites sur un nœud : avant l'inscription, l'app ne montre que les nœuds du projet.

Ce choix n'ouvre pas l'inscription : qui admettre reste décidé par le mode d'admission des cellules (étape 2). L'anneau doré de nœud vérifié dans « Explorer le réseau » n'existe pour l'instant que sur les nœuds du projet Nevod.

Ce réglage, comme le nom du nœud pour les autres nœuds, s'applique après le redémarrage du nœud. Sur le serveur, dans le dossier `/opt/nevod/installer/docker` :

```
docker compose restart nevod_node
```

## 5. Vérifiez le nœud

**Diagnostic → Vérifier.** En quelques secondes, le nœud indique si tout va bien : si son code est à jour, si ses réglages correspondent à la base de données, s'il y a des problèmes de configuration, s'il est joignable de l'extérieur.

L'accessibilité depuis l'extérieur, le nœud la vérifie par l'intermédiaire d'autres nœuds du réseau. Tant que votre nœud n'est relié à personne, cette ligne affiche « Aucun pair connu » : c'est normal. Rejoindre le réseau est l'étape suivante, et elle compte : sans elle, les téléphones ne reçoivent pas de notifications quand l'app est fermée. Voir [Rejoindre le réseau Nevod](../node-network/).

## 6. Facultatif : d'autres administrateurs

**Sécurité → Ajouter / changer le mot de passe** : chaque administrateur a son propre identifiant et son propre mot de passe, et vous pouvez les révoquer sans changer le mot de passe principal de `.env`. Le mot de passe principal reste un accès de secours au cas où les autres seraient perdus.
