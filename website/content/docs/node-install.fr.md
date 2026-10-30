# Installation pas à pas

Comment installer un nœud Nevod de zéro sur un serveur loué : de la location du serveur à la première connexion au panneau d'administration. L'exemple utilise un serveur sous Ubuntu 24.04 et le domaine `node.example.org` ; remplacez-le partout par le vôtre.

Toutes les commandes ci-dessous se tapent dans le terminal du serveur ; vous pouvez les copier en entier. Ce qu'est un nœud et ce qu'il conserve : voir [Comment fonctionne un nœud](../node-how/).

## 1. Louez un serveur

N'importe quel VPS chez n'importe quel hébergeur convient : 1 processeur, 1 Go de mémoire, 10 Go de disque, **Ubuntu 24.04**. À la commande, l'hébergeur vous donne l'**adresse IP** du serveur et le mot de passe de l'utilisateur `root` (ou vous demande de déposer une clé SSH).

Si l'hébergeur propose son propre pare-feu réseau dans l'espace client (par exemple Firewalls chez Hetzner, Security groups ailleurs), ouvrez-y les ports entrants **22, 80, 443 et 8765** (TCP).

## 2. Faites pointer le domaine vers le serveur

Le nœud a besoin de son propre domaine ou sous-domaine, par exemple `node.example.org`. Il ne peut pas s'en passer, pour deux raisons :

- **Les téléphones se connectent au nœud à l'adresse `https://domaine/nevod-ws`.** Caddy obtient de Let's Encrypt, pour un nom de domaine, le certificat HTTPS auquel un iPhone fait confiance sans aucun réglage.
- **L'adresse du nœud est enregistrée partout :** sur les téléphones des utilisateurs, dans leurs cartes de contact, chez les autres nœuds du réseau. Si vous passez sur un autre serveur ou si votre hébergeur change l'adresse IP, il suffit de corriger un enregistrement DNS et les utilisateurs ne remarquent rien. Avec une simple adresse IP, un déménagement couperait tout le monde et il faudrait renvoyer les invitations.

Si vous n'avez pas encore de domaine, vous pouvez en acheter un chez n'importe quel registraire (Cloudflare, Namecheap, Porkbun, Gandi et d'autres) — en général quelques dollars ou euros par an. Un seul sous-domaine suffit pour le nœud, et le domaine lui-même peut servir à autre chose.

Dans l'interface de gestion de votre domaine, créez un **enregistrement A** : nom — par exemple `node` (ce qui donne `node.example.org`) —, valeur : l'adresse IP du serveur.

Attendez quelques minutes et vérifiez depuis n'importe quel ordinateur :

```
ping node.example.org
```

La réponse doit afficher l'adresse IP de votre serveur. Tant que ce n'est pas le cas, inutile d'aller plus loin : un certificat HTTPS n'est délivré que pour un domaine qui pointe déjà vers le serveur.

> Si le domaine est géré par Cloudflare, désactivez le proxy pour cet enregistrement (nuage gris, « DNS only »). Sinon, les téléphones et les autres nœuds se connecteront à Cloudflare au lieu de votre serveur.

## 3. Connectez-vous au serveur

Sur votre ordinateur, ouvrez un terminal (PowerShell sous Windows, Terminal sur Mac) et tapez :

```
ssh root@node.example.org
```

À la première connexion, répondez `yes` et saisissez le mot de passe fourni par l'hébergeur.

## 4. Installez Docker et git

```
apt update && apt upgrade -y
apt install -y git
curl -fsSL https://get.docker.com | sh
```

La dernière commande est l'installateur officiel de Docker. Vérifiez que tout est en place :

```
docker compose version
```

Une ligne du type `Docker Compose version v2…` doit s'afficher.

## 5. Activez le pare-feu

```
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8765/tcp
ufw enable
```

Répondez `y` à la question. Les ports 80 et 443 servent au HTTPS (téléphones et panneau), le 8765 aux échanges avec les autres nœuds.

> Docker ouvre lui-même les ports de ses conteneurs, en contournant `ufw`. C'est pourquoi, dans notre kit, le panneau d'administration (port 8766) n'est publié que pour le serveur lui-même : ne changez pas cela dans `docker-compose.yml`.

## 6. Téléchargez Nevod

```
git clone https://github.com/avk0978/nevod-messenger.git /opt/nevod
cd /opt/nevod/installer/docker
```

## 7. Remplissez les réglages

Créez le fichier de réglages à partir du modèle :

```
cp .env.example .env
```

Choisissez un mot de passe pour le panneau d'administration. Le plus simple est d'en générer un long et aléatoire :

```
openssl rand -base64 24
```

Copiez le résultat et enregistrez-le dans votre gestionnaire de mots de passe. Ouvrez ensuite le fichier de réglages :

```
nano .env
```

Modifiez deux lignes :

```
NEVOD_DOMAIN=node.example.org
NEVOD_ADMIN_PASSWORD=ici-le-mot-de-passe-genere
```

Laissez le reste tel quel. Enregistrez le fichier : **Ctrl+O**, puis **Entrée** ; pour quitter, **Ctrl+X**.

| Réglage | Signification |
|---|---|
| `NEVOD_DOMAIN` | Le domaine du nœud. Les téléphones se connectent à `https://domaine/nevod-ws`, les autres nœuds à `domaine:8765`. |
| `NEVOD_ADMIN_PASSWORD` | Le mot de passe du panneau d'administration. Sans lui, le nœud ne démarre pas. |
| `NEVOD_ADMIN_PUBLIC` | `true` : le panneau s'ouvre dans le navigateur à l'adresse `https://domaine/nevod-admin` ; `false` : le panneau est fermé à Internet (voir l'étape 10). |
| `TURN_SECRET` | Uniquement si vous installez votre propre relais d'appels ; voir [Appels via votre propre nœud](../node-turn/). Généralement vide. |

## 8. Démarrez le nœud

```
docker compose up -d --build
```

Le premier démarrage prend quelques minutes : Docker construit l'image du nœud et télécharge Caddy. Une fois la commande terminée, vérifiez :

```
docker compose ps
```

Les deux conteneurs — `nevod_node` et `nevod_caddy` — doivent être à l'état `Up` (ou `running`).

## 9. Vérifiez que tout fonctionne

Ouvrez `https://node.example.org` dans un navigateur : la ligne « Nevod node — https://nevod.network » doit s'afficher, et le navigateur ne doit pas se plaindre du certificat.

Ouvrez maintenant `https://node.example.org/nevod-admin`. Le navigateur demande un identifiant et un mot de passe : n'importe quel identifiant, et le mot de passe inscrit dans `.env`. Le panneau d'administration s'ouvre. Que faire en premier : voir [Premiers réglages dans le panneau d'administration](../node-panel/).

> Cinq mots de passe erronés d'affilée depuis une même adresse bloquent le panneau pour cette adresse pendant 15 minutes. Si cela arrive, patientez simplement.

## 10. Facultatif : fermez le panneau à Internet

Si vous ne voulez pas que l'adresse du panneau s'ouvre depuis Internet, ajoutez la ligne `NEVOD_ADMIN_PUBLIC=false` dans `.env` et appliquez :

```
docker compose up -d
```

Le panneau n'est alors accessible que par un tunnel SSH. Sur votre ordinateur, lancez

```
ssh -L 8766:127.0.0.1:8766 root@node.example.org
```

et, tant que cette fenêtre reste ouverte, ouvrez `http://localhost:8766/nevod-admin` dans le navigateur.

## Si quelque chose ne va pas

| Ce que vous voyez | La cause habituelle |
|---|---|
| Le navigateur signale un certificat invalide, ou le site ne s'ouvre pas | Le domaine ne pointe pas encore vers le serveur (étape 2), ou le port 80/443 est fermé (étapes 1 et 5). Consultez le journal de Caddy : `docker compose logs caddy`. Une fois la cause corrigée, Caddy réessaie de lui-même. |
| `docker compose up` affiche `address already in use` | Un autre serveur web tourne déjà sur le serveur (souvent Apache ou nginx de l'hébergeur). Arrêtez-le : `systemctl disable --now apache2` ou `systemctl disable --now nginx`. |
| L'erreur `set NEVOD_ADMIN_PASSWORD in .env` ou `set NEVOD_DOMAIN in .env` | Cette ligne de `.env` n'est pas remplie (étape 7). |
| Le panneau redemande sans cesse le mot de passe | Mot de passe erroné. Pour voir celui qui est inscrit : `grep PASSWORD .env`. |
| Le panneau répond « Too many failed logins » | La protection contre les tentatives de devinette s'est déclenchée : patientez 15 minutes. |
| `nevod_node` redémarre en boucle | Le journal du nœud indique pourquoi : `docker compose logs --tail 50 nevod_node`. |

Les journaux complets des deux conteneurs : `docker compose logs`. Toutes les commandes `docker compose` s'exécutent depuis le dossier `/opt/nevod/installer/docker`.
