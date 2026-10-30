# Mantenimiento

Actualizar el nodo, copias de seguridad, mudanza a otro servidor, registros y el cuidado habitual del servidor. Todos los comandos `docker compose` se ejecutan en el servidor desde la carpeta `/opt/nevod/installer/docker`:

```
cd /opt/nevod/installer/docker
```

## Actualizar el nodo

Las versiones nuevas del nodo se publican en el [código fuente en GitHub](https://github.com/avk0978/nevod-messenger); para enterarte, pulsa **Watch** allí. Para actualizar:

```
cd /opt/nevod
git pull
cd installer/docker
docker compose up -d --build
```

El nodo se reinicia con la versión nueva; los usuarios se reconectan solos y los datos de la carpeta `data/` se conservan. Después de actualizar, revisa en el panel **Diagnóstico** → **Comprobar**.

Tras algunas actualizaciones, las imágenes antiguas ocupan espacio en disco; puedes borrarlas:

```
docker image prune -f
```

## Copia de seguridad

Lo más valioso del servidor es la carpeta `data/`, y en ella el archivo `node.json`: es la identidad del nodo. Si lo pierdes, habrá que crear el nodo de nuevo, con un identificador nuevo, y todos los usuarios tendrán que volver a registrarse. Haz una copia al menos una vez por semana y después de cada cambio de ajustes.

**Hacer una copia** (el nodo se detiene unos segundos):

```
docker compose stop nevod_node
tar czf ~/nevod-backup-$(date +%F).tar.gz data .env
docker compose start nevod_node
```

**Descargarla.** En tu ordenador:

```
scp root@node.example.org:~/nevod-backup-*.tar.gz .
```

No guardes la copia en el mismo servidor: si al servidor le pasa algo, la copia se pierde con él.

> La copia contiene las claves del nodo y la contraseña del panel de `.env`. Guárdala con el mismo cuidado que una contraseña: un disco cifrado, un gestor de contraseñas con adjuntos o un sitio parecido.

## Restaurar y mudarse a otro servidor

Así es también como se muda un nodo a un servidor nuevo. El dominio sigue siendo el mismo; solo cambia el servidor al que apunta.

1. En el servidor nuevo, haz los pasos 1 y 3–6 de la [instalación](../node-install/) (servidor, Docker, cortafuegos, descargar Nevod), **sin** los pasos 7–8.
2. Copia la copia de seguridad al servidor nuevo y descomprímela en la carpeta del kit:

   ```
   scp nevod-backup-FECHA.tar.gz root@IP-NUEVA:/opt/nevod/installer/docker/
   ```

   y en el servidor nuevo:

   ```
   cd /opt/nevod/installer/docker
   tar xzf nevod-backup-FECHA.tar.gz
   ```

3. **Detén el nodo en el servidor antiguo** (`docker compose down`): dos nodos con la misma identidad no deben funcionar a la vez.
4. Cambia el registro A del dominio a la IP del servidor nuevo y espera hasta que `ping node.example.org` muestre la dirección nueva.
5. Arranca el nodo en el servidor nuevo: `docker compose up -d --build`. Caddy vuelve a obtener el certificado por sí solo.

Los usuarios no tienen que hacer nada: la app se conecta al mismo dominio y encuentra allí el mismo nodo.

> El **dominio** del nodo no se puede cambiar tan fácilmente: la dirección para las conexiones con otros nodos se escribe en la identidad del nodo en su primer arranque. Elige un dominio que no vayas a tener que cambiar.

## Registros

```
docker compose logs --tail 100 nevod_node
docker compose logs -f nevod_node
```

El primer comando muestra las últimas 100 líneas; el segundo, el registro en tiempo real (para salir, **Ctrl+C**). El registro de Caddy: `docker compose logs caddy`. Las últimas entradas del nodo también se ven en el panel: **Diagnóstico → Registros**.

Los registros tienen tamaño limitado: 3 archivos de 10 MB por contenedor, y las entradas antiguas se sobrescriben solas. El texto de los mensajes nunca entra en el registro.

## Reiniciar, detener, contraseña

| Qué necesitas | Comando |
|---|---|
| Reiniciar el nodo (por ejemplo, tras cambiar el nombre o la visibilidad en el panel) | `docker compose restart nevod_node` |
| Detenerlo todo | `docker compose down` |
| Volver a arrancar | `docker compose up -d` |
| Ver qué está funcionando | `docker compose ps` |

**Cambiar la contraseña principal del panel:** pon la nueva en la línea `NEVOD_ADMIN_PASSWORD` de `.env` (`nano .env`) y ejecuta `docker compose up -d`: el nodo se reinicia con la contraseña nueva. Las cuentas personales de la página «Seguridad» no cambian.

## Cuidado del servidor

- **Actualizaciones del sistema**, una vez al mes o más a menudo:

  ```
  apt update && apt upgrade -y
  reboot
  ```

  Después del reinicio, el nodo, Caddy y coturn (si lo instalaste) arrancan solos.
- **Espacio en disco**: `df -h /`. Si queda poco, borra las imágenes antiguas (`docker image prune -f`) y las copias de seguridad viejas del servidor.
- **El certificado HTTPS** lo renueva Caddy solo. No hay que hacer nada, pero el puerto 80 tiene que seguir abierto.
- **¿El nodo no responde?** La forma más fácil de enterarte enseguida es apuntar un servicio gratuito de monitorización de webs a `https://node.example.org`: te enviará un correo si el nodo deja de responder.

## Si el nodo estuvo mucho tiempo parado

Los mensajes para usuarios que no se conectaron, el nodo los guarda hasta 72 horas y luego los borra. Los demás nodos de la red quitan de sus listas a un nodo que lleva 72 horas sin dar señales; tras arrancar, vuelve a ellas solo a medida que se intercambian las listas.
