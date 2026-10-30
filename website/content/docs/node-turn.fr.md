# Appels via votre propre nœud

Comment Nevod établit les appels, quand un nœud a besoin de son propre relais d'appels (TURN) et comment l'installer sur le même serveur. Si vous débutez, vous pouvez passer cette section : un nœud connecté au réseau obtient un relais auprès des nœuds du projet.

## Comment s'établit un appel

Le son et la vidéo passent **directement entre les téléphones**, et le nœud ne fait que les aider à s'accorder sur la connexion. Mais la connexion directe n'est pas toujours possible : les opérateurs mobiles et beaucoup de routeurs cachent les téléphones derrière des adresses partagées (NAT), et deux téléphones dans ce cas ne peuvent pas se joindre. L'appel passe alors par un **relais (TURN)** : un serveur qui retransmet les paquets entre les téléphones.

Un appel est chiffré de téléphone à téléphone (DTLS-SRTP). Le relais ne voit que des paquets chiffrés, les adresses des téléphones, l'heure et le volume de l'appel : il ne peut ni entendre ni voir la conversation.

## Avez-vous besoin de votre propre relais ?

**Sans relais propre**, un nœud [connecté au réseau](../node-network/) demande, pour chaque utilisateur qui se connecte, l'accès au relais de l'un des nœuds du réseau qui en ont un, choisi au hasard. Les appels fonctionnent, et il n'y a rien à configurer. Un nœud non connecté au réseau n'obtient pas de relais : les appels entre téléphones derrière un NAT peuvent ne pas s'établir pour ses utilisateurs.

**Un relais propre** vaut la peine si :

- vous voulez que les appels de vos utilisateurs ne dépendent pas des nœuds du projet ;
- vos utilisateurs sont loin des serveurs du projet, et les appels qui y passent ont du retard ;
- vous avez beaucoup d'utilisateurs et beaucoup d'appels.

À prendre en compte :

- **le trafic.** Tout l'appel passe par le relais : la voix, environ 100 kbit/s dans chaque sens ; la vidéo, 1 à 2 Mbit/s. La plupart des VPS incluent plusieurs téraoctets de trafic par mois : c'est largement suffisant pour un nœud de quelques dizaines d'utilisateurs ;
- **votre relais aidera aussi d'autres nœuds du réseau.** Le nœud signale au réseau qu'il a un relais, et les nœuds qui n'en ont pas le distribueront au hasard à leurs utilisateurs. La configuration ci-dessous comporte des limites pour que cela n'accapare pas toute la bande passante du serveur.

## Installer coturn

Nous installons coturn — le relais le plus répandu — directement sur le serveur du nœud. Toutes les commandes s'exécutent sur le serveur.

**1. Installez coturn et créez un secret :**

```
apt install -y coturn
openssl rand -hex 32
```

Conservez le résultat de la seconde commande : c'est le secret partagé par le relais et le nœud.

**2. Trouvez l'adresse IP externe du serveur :**

```
curl -4 ifconfig.me
```

**3. Écrivez la configuration.** Ouvrez le fichier :

```
nano /etc/turnserver.conf
```

effacez tout son contenu et collez ce qui suit, avec votre adresse IP et votre secret :

```
listening-port=3478
external-ip=ADRESSE-IP-DU-SERVEUR
realm=nevod
use-auth-secret
static-auth-secret=SECRET
min-port=49152
max-port=65535
no-tls
no-dtls
fingerprint
no-loopback-peers
no-multicast-peers
denied-peer-ip=0.0.0.0-0.255.255.255
denied-peer-ip=10.0.0.0-10.255.255.255
denied-peer-ip=100.64.0.0-100.127.255.255
denied-peer-ip=127.0.0.0-127.255.255.255
denied-peer-ip=169.254.0.0-169.254.255.255
denied-peer-ip=172.16.0.0-172.31.255.255
denied-peer-ip=192.168.0.0-192.168.255.255
total-quota=200
user-quota=10
max-bps=4000000
```

Enregistrez : **Ctrl+O**, **Entrée**, **Ctrl+X**.

Les lignes `denied-peer-ip` interdisent au relais de retransmettre quoi que ce soit vers des adresses internes, y compris à l'intérieur de Docker sur ce même serveur. Ne les supprimez pas. `total-quota`, `user-quota` et `max-bps` limitent le nombre de connexions simultanées et le débit d'une connexion (4 Mbit/s).

**4. Démarrez coturn :**

```
systemctl enable --now coturn
systemctl status coturn
```

La sortie doit indiquer `active (running)`. Si coturn ne démarre pas, ouvrez `/etc/default/coturn` et décommentez la ligne `TURNSERVER_ENABLED=1` : certaines versions du paquet l'exigent.

**5. Ouvrez les ports :**

```
ufw allow 3478/tcp
ufw allow 3478/udp
ufw allow 49152:65535/udp
```

Et les mêmes ports dans le pare-feu de l'hébergeur, s'il y en a un.

**6. Transmettez le secret au nœud.** Dans le dossier `/opt/nevod/installer/docker` :

```
nano .env
```

inscrivez le même secret sur la ligne `TURN_SECRET=` et appliquez :

```
docker compose up -d
```

## Vérification

- **Diagnostic → Vérifier → Dépendances et configuration** : il ne doit y avoir aucun avertissement concernant TURN.
- Le nœud donne aux téléphones l'adresse du relais `turn:votre-domaine:3478` : le domaine doit pointer vers ce serveur (c'est déjà le cas si le nœud fonctionne).
- Appelez depuis un téléphone en données mobiles un téléphone en Wi-Fi. Si l'appel s'établit et que vous vous entendez tous les deux, le relais fonctionne. Le journal de coturn : `journalctl -u coturn -n 50`.

> Le relais fonctionne en UDP et TCP sur le port 3478, sans chiffrer le canal jusqu'au relais (l'appel lui-même est toujours chiffré). Certains réseaux d'entreprise bloquent ces ports : les appels depuis ces réseaux ne passeront alors pas par le relais.
