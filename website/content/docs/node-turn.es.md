# Llamadas a través de tu propio nodo

Cómo conecta Nevod las llamadas, cuándo necesita un nodo su propio repetidor de llamadas (TURN) y cómo instalarlo en el mismo servidor. Si estás empezando, puedes saltarte esta sección: un nodo conectado a la red obtiene un repetidor de los nodos del proyecto.

## Cómo se conecta una llamada

El sonido y el vídeo van **directamente entre los teléfonos**, y el nodo solo les ayuda a ponerse de acuerdo sobre la conexión. Pero la conexión directa no siempre es posible: los operadores móviles y muchos routers esconden los teléfonos tras direcciones compartidas (NAT), y dos teléfonos así no pueden alcanzarse. Entonces la llamada va a través de un **repetidor (TURN)**, un servidor que reenvía los paquetes entre los teléfonos.

Una llamada está cifrada de teléfono a teléfono (DTLS-SRTP). El repetidor solo ve paquetes cifrados, las direcciones de los teléfonos y la hora y el volumen de la llamada: no puede oír ni ver la conversación.

## ¿Necesitas tu propio repetidor?

**Sin repetidor propio**, un nodo [conectado a la red](../node-network/) pide, para cada usuario que inicia sesión, acceso al repetidor de uno de los nodos de la red que lo tienen, elegido al azar. Las llamadas funcionan y no hay nada que configurar. Un nodo no conectado a la red no obtiene repetidor: las llamadas entre teléfonos tras NAT pueden no conectarse para sus usuarios.

**Un repetidor propio** merece la pena si:

- quieres que las llamadas de tus usuarios no dependan de los nodos del proyecto;
- tus usuarios están lejos de los servidores del proyecto y las llamadas a través de ellos tienen retardo;
- tienes muchos usuarios y muchas llamadas.

Qué tener en cuenta:

- **el tráfico.** Toda la llamada pasa por el repetidor: voz, unos 100 kbit/s en cada sentido; vídeo, 1–2 Mbit/s. La mayoría de los VPS incluyen varios terabytes de tráfico al mes: para un nodo con decenas de usuarios sobra;
- **tu repetidor ayudará también a otros nodos de la red.** El nodo comunica a la red que tiene repetidor, y los nodos sin uno propio lo darán al azar a sus usuarios. La configuración de abajo tiene límites para que esto no se coma todo el ancho de banda del servidor.

## Instalar coturn

Instalamos coturn —el repetidor más extendido— directamente en el servidor del nodo. Todos los comandos se ejecutan en el servidor.

**1. Instala coturn y crea un secreto:**

```
apt install -y coturn
openssl rand -hex 32
```

Guarda la salida del segundo comando: es el secreto compartido por el repetidor y el nodo.

**2. Averigua la dirección IP externa del servidor:**

```
curl -4 ifconfig.me
```

**3. Escribe la configuración.** Abre el archivo:

```
nano /etc/turnserver.conf
```

borra todo lo que tenga y pega lo siguiente, con tu dirección IP y tu secreto:

```
listening-port=3478
external-ip=IP-DEL-SERVIDOR
realm=nevod
use-auth-secret
static-auth-secret=SECRETO
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

Guarda: **Ctrl+O**, **Enter**, **Ctrl+X**.

Las líneas `denied-peer-ip` prohíben al repetidor reenviar nada a direcciones internas, incluido el interior de Docker en este mismo servidor. No las borres. `total-quota`, `user-quota` y `max-bps` limitan el número de conexiones simultáneas y la velocidad de una conexión (4 Mbit/s).

**4. Arranca coturn:**

```
systemctl enable --now coturn
systemctl status coturn
```

La salida debe decir `active (running)`. Si coturn no arranca, abre `/etc/default/coturn` y quita el comentario de la línea `TURNSERVER_ENABLED=1`: algunas versiones del paquete lo necesitan.

**5. Abre los puertos:**

```
ufw allow 3478/tcp
ufw allow 3478/udp
ufw allow 49152:65535/udp
```

Y los mismos puertos en el cortafuegos del proveedor, si lo hay.

**6. Pasa el secreto al nodo.** En la carpeta `/opt/nevod/installer/docker`:

```
nano .env
```

pon el mismo secreto en la línea `TURN_SECRET=` y aplícalo:

```
docker compose up -d
```

## Comprobación

- **Diagnóstico → Comprobar → Dependencias y configuración**: no debe haber avisos sobre TURN.
- El nodo da a los teléfonos la dirección del repetidor `turn:tu-dominio:3478`: el dominio debe apuntar a este servidor (ya lo hace si el nodo funciona).
- Llama desde un teléfono con datos móviles a un teléfono con Wi-Fi. Si la llamada se conecta y se os oye a los dos, el repetidor funciona. El registro de coturn: `journalctl -u coturn -n 50`.

> El repetidor funciona por UDP y TCP en el puerto 3478 sin cifrar el canal hasta el repetidor (la llamada en sí siempre está cifrada). En algunas redes corporativas esos puertos están cerrados: entonces las llamadas desde esas redes no pasarán por el repetidor.
