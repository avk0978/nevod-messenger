# Instalación paso a paso

Cómo instalar un nodo Nevod desde cero en un servidor alquilado: desde comprar el servidor hasta entrar por primera vez en el panel de administración. El ejemplo usa un servidor con Ubuntu 24.04 y el dominio `node.example.org`; pon el tuyo en su lugar en todas partes.

Todos los comandos de abajo se escriben en la terminal del servidor; puedes copiarlos enteros. Qué es un nodo y qué guarda: en [Cómo funciona un nodo](../node-how/).

## 1. Alquila un servidor

Sirve cualquier VPS de cualquier proveedor: 1 CPU, 1 GB de memoria, 10 GB de disco, **Ubuntu 24.04**. Al contratarlo, el proveedor te da la **dirección IP** del servidor y la contraseña del usuario `root` (o te pide subir una clave SSH).

Si el proveedor tiene su propio cortafuegos de red en el panel de control (por ejemplo, Firewalls en Hetzner, Security groups en otros), abre en él los puertos de entrada **22, 80, 443 y 8765** (TCP).

## 2. Apunta el dominio al servidor

El nodo necesita un dominio o subdominio propio, por ejemplo `node.example.org`. No puede prescindir de él por dos motivos:

- **Los teléfonos se conectan al nodo en `https://dominio/nevod-ws`.** Caddy obtiene de Let's Encrypt, para un nombre de dominio, el certificado HTTPS en el que un iPhone confía sin ninguna configuración.
- **La dirección del nodo está guardada en todas partes:** en los teléfonos de los usuarios, en sus tarjetas de contacto, en otros nodos de la red. Si te mudas a otro servidor o tu proveedor cambia la dirección IP, corriges un registro DNS y los usuarios no notan nada. Con una dirección IP sin más, una mudanza dejaría a todos sin conexión y tendrías que volver a enviar las invitaciones.

Si todavía no tienes dominio, puedes comprarlo en cualquier registrador (Cloudflare, Namecheap, Porkbun, Gandi y otros): suele costar unos pocos dólares o euros al año. Para el nodo basta un subdominio, y el dominio en sí puede servirte también para otras cosas.

En el panel de gestión de tu dominio, crea un **registro A**: nombre —por ejemplo `node` (queda `node.example.org`)—, valor: la dirección IP del servidor.

Espera unos minutos y compruébalo desde cualquier ordenador:

```
ping node.example.org
```

La respuesta debe mostrar la dirección IP de tu servidor. Mientras no sea así, no tiene sentido seguir: un certificado HTTPS solo se emite para un dominio que ya apunta al servidor.

> Si el dominio lo gestiona Cloudflare, desactiva el proxy para este registro (nube gris, «DNS only»). Si no, los teléfonos y los demás nodos se conectarán a Cloudflare en lugar de a tu servidor.

## 3. Conéctate al servidor

En tu ordenador, abre una terminal (en Windows, PowerShell; en Mac, Terminal) y escribe:

```
ssh root@node.example.org
```

En la primera conexión, responde `yes` y escribe la contraseña del proveedor.

## 4. Instala Docker y git

```
apt update && apt upgrade -y
apt install -y git
curl -fsSL https://get.docker.com | sh
```

El último comando es el instalador oficial de Docker. Comprueba que todo está en su sitio:

```
docker compose version
```

Debería aparecer una línea como `Docker Compose version v2…`.

## 5. Activa el cortafuegos

```
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8765/tcp
ufw enable
```

Responde `y` a la pregunta. Los puertos 80 y 443 son para HTTPS (teléfonos y panel), y el 8765, para comunicarse con otros nodos.

> Docker abre los puertos de sus contenedores por su cuenta, sin pasar por `ufw`. Por eso en nuestro kit el panel de administración (puerto 8766) solo está publicado para el propio servidor: no lo cambies en `docker-compose.yml`.

## 6. Descarga Nevod

```
git clone https://github.com/avk0978/nevod-messenger.git /opt/nevod
cd /opt/nevod/installer/docker
```

## 7. Rellena los ajustes

Crea el archivo de ajustes a partir de la plantilla:

```
cp .env.example .env
```

Inventa una contraseña para el panel de administración. Lo más cómodo es generar una larga y aleatoria:

```
openssl rand -base64 24
```

Copia el resultado y guárdalo en tu gestor de contraseñas. Ahora abre el archivo de ajustes:

```
nano .env
```

Cambia dos líneas:

```
NEVOD_DOMAIN=node.example.org
NEVOD_ADMIN_PASSWORD=aqui-la-contrasena-generada
```

Deja el resto como está. Guarda el archivo: **Ctrl+O**, luego **Enter**; para salir, **Ctrl+X**.

| Ajuste | Qué significa |
|---|---|
| `NEVOD_DOMAIN` | El dominio del nodo. Los teléfonos se conectan a `https://dominio/nevod-ws`, y los demás nodos a `dominio:8765`. |
| `NEVOD_ADMIN_PASSWORD` | La contraseña del panel de administración. Sin ella el nodo no arranca. |
| `NEVOD_ADMIN_PUBLIC` | `true`: el panel se abre en el navegador en `https://dominio/nevod-admin`; `false`: el panel está cerrado a internet (ver paso 10). |
| `TURN_SECRET` | Solo si instalas tu propio repetidor de llamadas; consulta [Llamadas a través de tu propio nodo](../node-turn/). Normalmente vacío. |

## 8. Arranca el nodo

```
docker compose up -d --build
```

El primer arranque tarda unos minutos: Docker construye la imagen del nodo y descarga Caddy. Cuando termine el comando, comprueba:

```
docker compose ps
```

Los dos contenedores —`nevod_node` y `nevod_caddy`— deben estar en estado `Up` (o `running`).

## 9. Comprueba que todo funciona

Abre `https://node.example.org` en el navegador: debe aparecer la línea «Nevod node — https://nevod.network», y el navegador no debe quejarse del certificado.

Ahora abre `https://node.example.org/nevod-admin`. El navegador pide usuario y contraseña: cualquier usuario, y la contraseña que pusiste en `.env`. Se abre el panel de administración. Qué hacer primero en él: en [Primera configuración en el panel de administración](../node-panel/).

> Cinco contraseñas incorrectas seguidas desde una misma dirección bloquean el panel para esa dirección durante 15 minutos. Si pasa, simplemente espera.

## 10. Opcional: cierra el panel a internet

Si no quieres que la dirección del panel se abra desde internet, añade a `.env` la línea `NEVOD_ADMIN_PUBLIC=false` y aplícala:

```
docker compose up -d
```

Entonces al panel solo se llega por un túnel SSH. En tu ordenador, ejecuta

```
ssh -L 8766:127.0.0.1:8766 root@node.example.org
```

y, mientras esa ventana siga abierta, abre en el navegador `http://localhost:8766/nevod-admin`.

## Si algo va mal

| Qué ves | Causa habitual |
|---|---|
| El navegador dice que el certificado no es válido, o la web no se abre | El dominio aún no apunta al servidor (paso 2) o el puerto 80/443 está cerrado (pasos 1 y 5). Mira el registro de Caddy: `docker compose logs caddy`. Cuando se corrige la causa, Caddy lo vuelve a intentar solo. |
| `docker compose up` dice `address already in use` | En el servidor ya funciona otro servidor web (a menudo Apache o nginx del proveedor). Detenlo: `systemctl disable --now apache2` o `systemctl disable --now nginx`. |
| El error `set NEVOD_ADMIN_PASSWORD in .env` o `set NEVOD_DOMAIN in .env` | Esa línea de `.env` no está rellenada (paso 7). |
| El panel pide la contraseña una y otra vez | Contraseña incorrecta. Para ver cuál está puesta: `grep PASSWORD .env`. |
| El panel responde «Too many failed logins» | Ha saltado la protección contra adivinar contraseñas: espera 15 minutos. |
| `nevod_node` se reinicia sin parar | El registro del nodo muestra la causa: `docker compose logs --tail 50 nevod_node`. |

Los registros completos de los dos contenedores: `docker compose logs`. Todos los comandos `docker compose` se ejecutan desde la carpeta `/opt/nevod/installer/docker`.
