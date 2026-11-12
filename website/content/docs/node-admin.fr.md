# Le panneau d'administration : toutes les pages et tous les réglages

Une référence du panneau d'administration du nœud : ce que contient chaque page et ce que fait chaque réglage. Si vous venez d'installer le nœud, commencez par [Premiers réglages dans le panneau d'administration](../node-panel/) : l'essentiel y est expliqué pas à pas.

Le panneau s'ouvre à l'adresse `https://votre-domaine/nevod-admin` (ou par un tunnel SSH si vous l'avez fermé — voir l'[installation](../node-install/), étape 10). N'importe quel identifiant ; le mot de passe est `NEVOD_ADMIN_PASSWORD` de `.env` ou un mot de passe personnel créé sur la page « Sécurité ». La langue se change dans l'en-tête.

## En-tête

En haut de chaque page : le nom du nœud, son identifiant (`node_id`) et des pastilles indiquant l'état actuel : si le nœud est visible dans « Explorer le réseau », le mode d'admission des cellules, qui voit les cellules publiées.

## Aperçu

La liste de toutes les cellules (utilisateurs et bots) inscrites sur le nœud.

| Colonne | Ce qu'elle affiche |
|---|---|
| Nom | Votre propre étiquette pour cette cellule : vous seul la voyez, dans le panneau. Saisissez-la et appuyez sur ✓ ou Entrée. Elle ne change pas le nom choisi par l'utilisateur. |
| `cell_id` | L'identifiant de la cellule. La version complète apparaît dans l'infobulle. |
| Langue | La langue du téléphone de l'utilisateur : écrivez-lui dans celle-ci. « Magyar → English » : Nevod n'a pas cette langue, la personne voit l'app en anglais ; écrivez en anglais. « — » : app antérieure à 1.3. |
| Statut | En ligne ou hors ligne : si l'app est connectée en ce moment. |
| Tampon | Ce qui attend que l'utilisateur se connecte (conservé jusqu'à 72 heures) : **msg**, messages et parties de fichiers ; **de service**, marques « distribué/lu », réactions et signaux. Les éléments de service arrivent quand la personne ouvre l'app. |
| Inscription | Quand la cellule s'est inscrite. |

Sous le tableau, **Langues des membres** : combien de personnes utilisent chaque langue, y compris celles que Nevod n'a pas encore. Cela montre quelles langues sont les plus demandées.

Boutons :

- **✕** sur une ligne : supprimer la cellule. Cela révoque entièrement son admission : l'inscription, les messages non remis et les jetons de notification sont supprimés, et le nom est libéré. Pour revenir, la personne aura besoin d'un nouveau code d'invitation ou d'une nouvelle demande. Le nœud ne supprime jamais de cellules de lui-même : vous seul le faites.
- **Réinitialiser les inscriptions** : toutes les cellules se réinscrivent à leur prochaine connexion ; inutile de ressaisir le code.
- **Réinitialisation complète** : irréversible : tous les membres devront revenir avec un code d'invitation. En pratique, elle n'est utile que lors d'un déménagement ou d'un renouvellement complet des membres du nœud.

## Paramètres

| Réglage | Ce qu'il fait | Quand il s'applique |
|---|---|---|
| **Nom du nœud** | Le nom du nœud que voient les utilisateurs. Les mots de service (Nevod, admin, support, official, etc.) sont interdits. | Dans le panneau : immédiatement ; pour les autres nœuds : après un redémarrage. |
| **Type de nœud** *(en développement)* | `permanent` : un nœud ordinaire. `temporary` : un nœud temporaire, par exemple pour la durée d'un événement ; l'app n'utilise pas encore ces nœuds. Laissez `permanent`. | Après un redémarrage. |
| **ID du nœud parent** *(en développement)* | Utile seulement à un nœud temporaire : à quel nœud permanent il se rattache. Laissez vide. | Immédiatement. |
| **Visibilité dans « Explorer le réseau »** | `closed` : le nœud n'est pas montré aux utilisateurs d'autres nœuds. `open` : le nœud apparaît dans leur « Explorer le réseau ». Cela n'ouvre pas l'inscription. | Après un redémarrage. |
| **Visibilité des cellules publiées** | Qui voit la liste des bots et pages de la page « Publication » : `off`, personne ; `members`, seulement les utilisateurs de ce nœud ; `public`, tout le monde. | Immédiatement. |
| **Mode d'admission des cellules** | `delegated` : uniquement avec un code d'invitation ; `admin` : avec un code ou sur demande avec votre approbation ; `open` : quiconque connaît l'adresse. | Immédiatement. |
| **Administrateurs** | Les identifiants (`cell_id`) de vos propres cellules, séparés par des virgules. En mode `admin`, ils reçoivent dans Nevod un message à chaque nouvelle demande. Votre `cell_id` figure sur la page « Aperçu ». | Immédiatement. |

Redémarrer le nœud — sur le serveur, dans le dossier `/opt/nevod/installer/docker` :

```
docker compose restart nevod_node
```

## Demandes d'adhésion

Fonctionne en mode d'admission `admin`. Quand quelqu'un sans code essaie de s'inscrire, l'app envoie elle-même une demande, qui apparaît ici avec un nom et une note. **Approuver** : la personne obtient l'accès aussitôt et une notification sur son téléphone. **Refuser** : l'app lui indique que sa demande a été refusée.

## Messages

Les messages que les utilisateurs du nœud ont envoyés depuis l'app à son compte **administrator** : signalements de messages, questions. Chaque nœud a un compte administrator, créé automatiquement au premier démarrage.

Ouvrez une conversation, écrivez une réponse et cliquez sur **Répondre** : la réponse part chiffrée vers l'utilisateur dans Nevod, au nom d'administrator. On ne répond aux messages des utilisateurs que de cette façon, dans l'app, et pas par e-mail.

Si l'utilisateur a joint au message le journal de l'app (pour analyser un problème), un lien **télécharger nevod.log** apparaît dans la conversation.

Les utilisateurs voient le compte administrator de votre nœud avec la mention **Administrateur du nœud** et le nom du nœud. Cette mention est confirmée par la clé de votre nœud : personne d'autre ne peut donc se faire passer pour l'administrateur de votre nœud. Le badge bleu ✓ est la marque de l'administration du projet Nevod : il est confirmé par la signature du curateur du projet et n'existe que sur les nœuds du projet.

## Invitations

**Créer un code :** choisissez la durée de validité (1 heure, 24 heures, 7 jours) → **+ Créer un code**. Un code QR et un lien apparaissent : vous pouvez les montrer à l'écran, les transmettre ou cliquer sur **Copier le lien**. Le lien ouvre Nevod avec l'adresse du nœud et le code déjà remplis. Le code court, du type `ABCD-EFGH`, ne marche que si votre nœud est déjà défini dans l'app de la personne.

Chaque code ne sert qu'une fois. En dessous figurent tous les codes avec leur durée de validité et leur état : actif, utilisé, par qui.

**Cellules admises** : qui est entré, et sur l'invitation de qui. L'interrupteur **Peut inviter** permet à cette personne de créer des codes depuis l'app (Profil → Inviter quelqu'un) ; en mode `delegated`, c'est ainsi que vous confiez les invitations à des personnes de confiance.

Plus de détails dans [Inviter des personnes](../node-invite/).

## Nœuds

**Connexion au réseau Nevod.** L'état (« connecté · nœuds en ligne » ou « non connecté ») et le bouton **Rejoindre le réseau Nevod**. Un nœud connecté reçoit des nœuds du projet les notifications push pour les téléphones et un relais d'appels. Le champ **Jeton de l'administrateur d'un autre nœud** sert à rejoindre le réseau par un autre nœud plutôt que par Nevod Open. Plus de détails dans [Rejoindre le réseau Nevod](../node-network/).

**Nœuds connus** : tous les nœuds du réseau que connaît votre nœud : nom, adresse, en ligne ou non, dernier contact. Un nœud qui ne s'est pas manifesté depuis 72 heures est retiré de la liste et y revient de lui-même quand il réapparaît dans le réseau.

**Invitations de nœuds** : un jeton grâce auquel un autre nœud peut rejoindre le réseau par le vôtre. Il est valable 10 minutes ; remettez-le à l'administrateur de l'autre nœud en main propre, pas publiquement.

## Publication

Les bots et pages que votre nœud montre aux utilisateurs dans l'app, sur la « planète » du nœud dans « Explorer le réseau ». Choisissez une cellule, définissez un titre, un type (`bot` : un bot ; `page` : une page de texte) et une description → **Publier**. Retirer de la publication l'enlève de la liste ; la cellule elle-même reste.

Les cases Claude, ChatGPT, Gemini concernent un bot IA externe qui fonctionne avec la clé de l'utilisateur : quels fournisseurs il accepte. Pour un bot ordinaire, ne cochez rien.

Qui voit cette liste se règle dans « Paramètres » → « Visibilité des cellules publiées ».

## Bots IA

Des bots IA qui tournent directement dans le nœud et répondent via Claude, ChatGPT ou Gemini **avec la clé de l'utilisateur** : la personne ajoute sa clé dans la discussion avec le bot, la clé arrive avec chaque message et le bot ne la conserve pas. Le nœud n'a pas de clés à lui et ne paie pas pour l'IA.

**Ajouter un bot** : définissez un nom, une description, une instruction pour le modèle et les fournisseurs, ou prenez un modèle tout prêt (AI Assistant, Tolmach le traducteur) et adaptez-le. Un bot activé apparaît pour les utilisateurs du nœud dans la liste « Sur ce nœud ». Un bot désactivé est arrêté et masqué, et garde son nom. La suppression est définitive : les clés et le nom du bot sont supprimés, tandis que les utilisateurs conservent leurs conversations.

> Les conversations avec un bot IA sont déchiffrées par du code sur votre nœud et transmises au fournisseur choisi. Les utilisateurs en sont avertis dans la [Politique de confidentialité](../../privacy/) (section 5). Si vous activez des bots IA, vous participez, en tant que propriétaire du nœud, à cette transmission.

## Sécurité

Les comptes administrateur personnels : **Ajouter / changer le mot de passe** : un identifiant et un mot de passe (conservé sous forme d'empreinte). Un compte par administrateur ; quand quelqu'un s'en va, supprimez son compte sans changer le mot de passe principal. Le mot de passe principal de `.env` fonctionne toujours comme accès de secours.

Cinq mots de passe erronés d'affilée depuis une même adresse bloquent la connexion pour cette adresse pendant 15 minutes.

## Diagnostic

**Vérifier** : l'autodiagnostic du nœud (jusqu'à 10 secondes) :

| Vérification | Signification |
|---|---|
| Code à jour | Si la version installée du nœud est en retard sur le protocole ; si c'est le cas, mettez le nœud à jour (voir [Maintenance](../node-maintenance/)). |
| Cohérence identity/DB | Si les réglages de `node.json` correspondent à la base de données. |
| Dépendances et configuration | S'il y a des erreurs dans les réglages (par exemple un relais d'appels sans `TURN_SECRET`). |
| Accessibilité externe | Si un autre nœud du réseau peut joindre le vôtre depuis l'extérieur. Tant que le nœud n'est pas connecté au réseau, elle affiche « Aucun pair connu » : c'est normal. |

**Journaux** : les dernières entrées du journal du nœud. Le texte des messages n'entre jamais dans le journal.
