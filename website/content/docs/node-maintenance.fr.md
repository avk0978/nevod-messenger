# Maintenance

Mettre à jour le nœud, les sauvegardes, le déménagement vers un autre serveur, les journaux et l'entretien courant du serveur. Toutes les commandes `docker compose` s'exécutent sur le serveur depuis le dossier `/opt/nevod/installer/docker` :

```
cd /opt/nevod/installer/docker
```

## Mettre à jour le nœud

Les nouvelles versions du nœud sont publiées dans le [code source sur GitHub](https://github.com/avk0978/nevod-messenger) ; pour en être averti, cliquez sur **Watch**. Pour mettre à jour :

```
cd /opt/nevod
git pull
cd installer/docker
docker compose up -d --build
```

Le nœud redémarre avec la nouvelle version ; les utilisateurs se reconnectent d'eux-mêmes, et les données du dossier `data/` sont conservées. Après la mise à jour, jetez un œil au panneau : **Diagnostic** → **Vérifier**.

Après plusieurs mises à jour, les anciennes images occupent de l'espace disque ; vous pouvez les supprimer :

```
docker image prune -f
```

## Sauvegarde

Ce qu'il y a de plus précieux sur le serveur, c'est le dossier `data/`, et dedans le fichier `node.json` : c'est l'identité du nœud. Si vous le perdez, il faudra recréer le nœud, avec un nouvel identifiant, et tous les utilisateurs devront s'y réinscrire. Faites une sauvegarde au moins une fois par semaine et après chaque changement de réglages.

**Faire une sauvegarde** (le nœud s'arrête quelques secondes) :

```
docker compose stop nevod_node
tar czf ~/nevod-backup-$(date +%F).tar.gz data .env
docker compose start nevod_node
```

**La télécharger.** Sur votre ordinateur :

```
scp root@node.example.org:~/nevod-backup-*.tar.gz .
```

Ne gardez pas la sauvegarde sur le même serveur : s'il arrive quelque chose au serveur, elle disparaît avec lui.

> La sauvegarde contient les clés du nœud et le mot de passe du panneau figurant dans `.env`. Conservez-la avec autant de soin qu'un mot de passe : disque chiffré, gestionnaire de mots de passe avec pièces jointes ou équivalent.

## Restauration et déménagement vers un autre serveur

C'est aussi ainsi que l'on déménage un nœud vers un nouveau serveur. Le domaine reste le même ; seul change le serveur vers lequel il pointe.

1. Sur le nouveau serveur, effectuez les étapes 1 et 3 à 6 de l'[installation](../node-install/) (serveur, Docker, pare-feu, téléchargement de Nevod), **sans** les étapes 7 et 8.
2. Copiez la sauvegarde sur le nouveau serveur et décompressez-la dans le dossier du kit :

   ```
   scp nevod-backup-DATE.tar.gz root@NOUVELLE-IP:/opt/nevod/installer/docker/
   ```

   puis, sur le nouveau serveur :

   ```
   cd /opt/nevod/installer/docker
   tar xzf nevod-backup-DATE.tar.gz
   ```

3. **Arrêtez le nœud sur l'ancien serveur** (`docker compose down`) : deux nœuds avec la même identité ne doivent pas tourner en même temps.
4. Faites pointer l'enregistrement A du domaine vers l'IP du nouveau serveur et attendez que `ping node.example.org` affiche la nouvelle adresse.
5. Démarrez le nœud sur le nouveau serveur : `docker compose up -d --build`. Caddy obtient de nouveau le certificat de lui-même.

Les utilisateurs n'ont rien à faire : l'app se connecte au même domaine et y retrouve le même nœud.

> Le **domaine** du nœud ne se change pas si facilement : l'adresse servant aux connexions avec les autres nœuds est inscrite dans l'identité du nœud lors de son premier démarrage. Choisissez un domaine que vous n'aurez pas à changer.

## Journaux

```
docker compose logs --tail 100 nevod_node
docker compose logs -f nevod_node
```

La première commande affiche les 100 dernières lignes, la seconde le journal en temps réel (pour quitter, **Ctrl+C**). Le journal de Caddy : `docker compose logs caddy`. Les dernières entrées du nœud sont aussi visibles dans le panneau : **Diagnostic → Journaux**.

Les journaux sont de taille limitée : 3 fichiers de 10 Mo par conteneur, et les anciennes entrées sont écrasées d'elles-mêmes. Le texte des messages n'entre jamais dans le journal.

## Redémarrage, arrêt, mot de passe

| Ce dont vous avez besoin | Commande |
|---|---|
| Redémarrer le nœud (par exemple après avoir changé le nom ou la visibilité dans le panneau) | `docker compose restart nevod_node` |
| Tout arrêter | `docker compose down` |
| Redémarrer le tout | `docker compose up -d` |
| Voir ce qui tourne | `docker compose ps` |

**Changer le mot de passe principal du panneau :** inscrivez le nouveau sur la ligne `NEVOD_ADMIN_PASSWORD` de `.env` (`nano .env`) et lancez `docker compose up -d` : le nœud redémarre avec le nouveau mot de passe. Les comptes personnels de la page « Sécurité » ne sont pas modifiés.

## Entretien du serveur

- **Mises à jour du système**, une fois par mois ou plus souvent :

  ```
  apt update && apt upgrade -y
  reboot
  ```

  Après le redémarrage, le nœud, Caddy et coturn (si vous l'avez installé) repartent d'eux-mêmes.
- **Espace disque** : `df -h /`. S'il en manque, supprimez les anciennes images (`docker image prune -f`) et les vieilles sauvegardes sur le serveur.
- **Le certificat HTTPS** est renouvelé par Caddy tout seul. Il n'y a rien à faire, mais le port 80 doit rester ouvert.
- **Le nœud ne répond plus ?** Le plus simple pour le savoir tout de suite est de faire surveiller `https://node.example.org` par un service gratuit de surveillance de sites : il vous enverra un e-mail si le nœud cesse de répondre.

## Si le nœud est resté longtemps arrêté

Les messages destinés aux utilisateurs qui ne se sont pas connectés sont conservés par le nœud jusqu'à 72 heures, puis supprimés. Les autres nœuds du réseau retirent de leurs listes un nœud qui ne s'est pas manifesté depuis 72 heures ; après son redémarrage, il y revient de lui-même, au fil des échanges de listes.
