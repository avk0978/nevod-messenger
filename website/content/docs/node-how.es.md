# Cómo funciona un nodo

Un nodo es un programa en un servidor a través del cual los teléfonos intercambian mensajes y establecen llamadas. Aquí, en breve, qué hace un nodo, qué guarda y qué no puede ver, para que antes de instalarlo sepas qué asumes.

## Nodo, celda y nodo de origen

Cada usuario de Nevod es una **celda**: un par de claves de cifrado que se crea en el teléfono y nunca sale de él. Una celda se registra en un nodo: su **nodo de origen**. A través de él, el teléfono recibe los mensajes que le enviaron mientras estaba apagado.

Los nodos están unidos en una red común. Si escribes a alguien de otro nodo, tu nodo pasa el mensaje cifrado al nodo de esa persona. No hay servidor central: la red son los propios nodos.

La carga de un nodo depende solo de su propio círculo —sus usuarios y bots—, no del tamaño de toda la red: un nodo no retransmite ni guarda mensajes de otros nodos. Por eso a un nodo le basta un ordenador corriente, y no se vuelve más pesado por mucha gente que llegue a Nevod en otros nodos. Estas redes se llaman **de baja carga** (clase LL-0); más en el artículo [«Low-Load Distributed Data Networks»](../../publications/low-load-networks/) (DOI 10.5281/zenodo.23621073).

## Tipos de nodos

Todos los nodos ejecutan el mismo programa. Lo que un nodo llega a ser —un nodo familiar cerrado, un nodo comunitario abierto o el nodo de una organización— lo deciden tres ajustes del [panel de administración](../node-admin/):

- **a quién admitir**: el modo de admisión de celdas: solo con código de invitación, con código o por solicitud con tu aprobación, o a todos (detalles en la tabla de [Primera configuración](../node-panel/), paso 2);
- **si el nodo es visible en «Explorar la red»** para los usuarios de otros nodos;
- **qué muestra el nodo a sus usuarios**: los bots y páginas publicados en él.

| Qué nodo | A quién admitir | Visible en «Explorar la red» | Ejemplo |
|---|---|---|---|
| Cerrado: familia, amigos, organización | con código de invitación | no | el nodo de una empresa donde el administrador invita a cada empleado |
| Comunidad con selección | con código o por solicitud con aprobación | sí | el nodo de un club: cualquiera puede encontrarlo, pero el administrador aprueba a los miembros |
| Comunidad abierta | a todos | sí | un nodo público como Nevod Open |

**Dónde funciona el nodo** —en un servidor alquilado con dominio o en casa, en tu ordenador— no cambia lo que puede hacer. Un nodo doméstico tiene que ser accesible desde internet: redirección de puertos en el router y un dominio. Por eso es más fácil empezar con un servidor alquilado: toda la documentación está escrita para él.

**Importante para un nodo doméstico: desde tu red de casa se llega a él con otras reglas.** Los teléfonos se conectan al nodo por su dominio, y el dominio apunta a la dirección externa de tu router. Un teléfono en el Wi-Fi de casa intenta llegar a esa dirección externa desde dentro de la red, y muchos routers no dejan pasar esas conexiones. Entonces el nodo funciona con datos móviles, pero con el Wi-Fi de casa la app dice «Sin conexión». Conectarse por la dirección local del servidor (por ejemplo, `192.168.1.10`) tampoco funciona: el certificado está emitido para el dominio, no para la dirección. Se resuelve en el router, de una de estas dos formas:

- activa **NAT loopback** (también llamado NAT hairpinning o NAT reflection), si el router lo admite;
- o añade en el DNS del router un registro local: tu dominio → la dirección local del servidor.

Compruébalo justo después de instalar: conéctate al nodo desde un teléfono tanto por el Wi-Fi de casa como por datos móviles.

**Los nodos del proyecto Nevod** —Nevod Open, Dev Planet y algunos más— no se distinguen de los demás por el programa, sino por tres cosas:

- tienen una clave de Apple para notificaciones push y un repetidor de llamadas, y los comparten con los nodos de la red (ver más abajo);
- en «Explorar la red» llevan el **anillo dorado** de nodo verificado y una etiqueta de propósito: «Comunidad», «Informativo», «Agente de IA». El anillo lo confirma la firma del curador del proyecto y por ahora solo lo tienen los nodos del proyecto;
- **Nevod Open** es el nodo en el que la app registra a los usuarios por defecto y el punto de entrada a la red para los nodos nuevos: se puede conectar a él sin invitación.

> En los ajustes del panel también hay «Tipo de nodo» —`permanent` o `temporary`— e «ID del nodo padre». Están **en desarrollo**: nodos temporales (por ejemplo, para la duración de un evento). La app aún no los usa: deja `permanent` y el ID del nodo padre vacío.

## Qué guarda un nodo

- **Los registros de las celdas**: identificador, claves públicas y el nombre visible que eligió el usuario.
- **Los mensajes no entregados**, cifrados, hasta que el destinatario se conecte, pero no más de 72 horas. Tras la entrega, el mensaje se borra.
- **Los tokens de notificación** de los teléfonos, para «despertar» un teléfono cuando llega un mensaje o una llamada.
- **Los códigos de invitación**, las solicitudes de acceso y los mensajes de los usuarios al administrador del nodo.
- **La lista de los demás nodos de la red** y sus propios ajustes.
- **Los registros técnicos**, de tamaño limitado (3 archivos de 10 MB por contenedor); las entradas antiguas se sobrescriben.

## Qué no puede ver un nodo

- **El texto de los mensajes, las fotos, los vídeos, los mensajes de voz y los archivos.** Se cifran en el teléfono del remitente con la clave del destinatario. El nodo los entrega sin tener la clave que podría abrirlos.
- **El contenido de las llamadas.** El sonido y el vídeo van entre los teléfonos directamente o a través de un repetidor (TURN), cifrados.
- **Los contactos y las conversaciones del teléfono.** Se guardan solo en el dispositivo.

Lo que sí ve el nodo: qué celdas están registradas en él y con qué nombres, quién escribe a quién y cuándo, el tamaño de los mensajes, las direcciones IP de las conexiones. Son datos de entrega: sin ellos el nodo no podría funcionar. Más en la [Política de privacidad](../../privacy/).

> El propietario del nodo es responsable de que el nodo funcione y de la copia de seguridad de sus datos. No puede leer las conversaciones de los usuarios: esto se deriva de cómo está construida la red, no de una promesa.

## Notificaciones y llamadas a través de los nodos del proyecto

Solo un nodo que tenga clave de Apple puede enviar notificaciones push a la app Nevod del App Store, y solo los nodos del proyecto la tienen. Por eso, un nodo conectado a la red pide a un nodo del proyecto que envíe la notificación por él. El nodo del proyecto ve entonces el token del teléfono y el nombre del remitente para el título de la notificación, y el texto es siempre el mismo: «Mensaje nuevo». Si el remitente está en los contactos del destinatario, el propio teléfono pone el nombre con el que está guardado.

**¿Puedo enviar notificaciones directamente desde mi nodo?** No. Las notificaciones a una app del App Store solo se aceptan con una clave de la cuenta de desarrollador de Apple con la que se publicó la app, y Nevod lo publica el proyecto. Esa clave no se puede dar a los propietarios de nodos: no se puede limitar a un solo nodo y permite enviar a cualquier usuario de Nevod una notificación con cualquier texto. Por eso las notificaciones pasan por los nodos del proyecto, y su texto es siempre «Mensaje nuevo».

Del mismo modo, un nodo sin repetidor de llamadas (TURN) propio obtiene uno de los nodos de la red; más en [Llamadas a través de tu propio nodo](../node-turn/).

De ahí una conclusión importante: **un nodo que no está conectado a la red entregará mensajes, pero los teléfonos no recibirán notificaciones** mientras la app esté cerrada. Cómo conectarse: en [Conectarse a la red Nevod](../node-network/).

## De qué consta la instalación

El kit de servidor ya preparado (la carpeta `installer/docker` del [código fuente](https://github.com/avk0978/nevod-messenger)) son dos contenedores Docker:

| Contenedor | Qué hace | Puertos |
|---|---|---|
| `nevod_node` | el propio nodo | 8765: para otros nodos; 8766: el panel de administración, accesible solo desde el propio servidor |
| `nevod_caddy` | el servidor web Caddy: obtiene por sí solo un certificado HTTPS para tu dominio y pasa al nodo las conexiones de los teléfonos y del panel | 80 y 443 |

Todos los datos del nodo están en la carpeta `data/`, junto al archivo de ajustes:

- `node.json`: **la identidad del nodo**, sus claves. Si pierdes este archivo, pierdes el nodo: no se puede volver a crear un nodo con la misma identidad, y todos los usuarios tendrían que registrarse en uno nuevo. Guarda una copia de seguridad.
- `node.db`: la base de datos: registros, invitaciones, el búfer de mensajes.

## Qué vas a necesitar

- **Un servidor Linux**: sirve el VPS alquilado más barato: 1 CPU, 1 GB de memoria, 10 GB de disco. Basta para decenas y cientos de usuarios.
- **Un dominio** (o subdominio) que puedas apuntar al servidor, por ejemplo `node.example.org`. Sin dominio, los teléfonos no pueden verificar el certificado HTTPS.
- **Una media hora** y saber conectarte al servidor por SSH. Todos los comandos están en [Instalación paso a paso](../node-install/); puedes copiarlos tal cual.
