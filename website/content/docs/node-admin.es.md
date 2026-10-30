# El panel de administración: todas las páginas y ajustes

Una referencia del panel de administración del nodo: qué hay en cada página y qué hace cada ajuste. Si acabas de instalar el nodo, empieza por [Primera configuración en el panel de administración](../node-panel/): ahí está lo imprescindible, paso a paso.

El panel se abre en `https://tu-dominio/nevod-admin` (o por un túnel SSH si lo cerraste; consulta la [instalación](../node-install/), paso 10). Cualquier usuario; la contraseña es `NEVOD_ADMIN_PASSWORD` de `.env` o una personal creada en la página «Seguridad». El idioma se cambia en la cabecera.

## Cabecera

Arriba de cada página: el nombre del nodo, su identificador (`node_id`) y unas etiquetas con el estado actual: si el nodo es visible en «Explorar la red», el modo de admisión de celdas, quién ve las celdas publicadas.

## Resumen

La lista de todas las celdas (usuarios y bots) registradas en el nodo.

| Columna | Qué muestra |
|---|---|
| Nombre | Tu propia etiqueta para esta celda: solo la ves tú, en el panel. Escríbela y pulsa ✓ o Enter. No cambia el nombre que eligió el usuario. |
| `cell_id` | El identificador de la celda. El completo, en la información emergente. |
| Estado | En línea o desconectado: si la app está conectada ahora. |
| Búfer | Cuántos mensajes esperan a que el usuario se conecte (se guardan hasta 72 horas). |
| Registro | Cuándo se registró la celda. |

Botones:

- **✕** en una fila: eliminar la celda. Revoca por completo su admisión: se borran el registro, los mensajes no entregados y los tokens de notificación, y el nombre queda libre. Para volver, la persona necesitará un código de invitación nuevo o una nueva solicitud. El nodo nunca borra celdas por su cuenta: solo tú.
- **Restablecer registros**: todas las celdas se vuelven a registrar en su próxima conexión; no hace falta volver a introducir el código.
- **Restablecimiento total**: irreversible: todos los miembros tendrán que volver a entrar con un código de invitación. En la práctica solo hace falta en una mudanza o un cambio completo de miembros.

## Ajustes

| Ajuste | Qué hace | Cuándo se aplica |
|---|---|---|
| **Nombre del nodo** | El nombre del nodo que ven los usuarios. No se pueden usar palabras de servicio (Nevod, admin, support, official y similares). | En el panel, al momento; para otros nodos, tras un reinicio. |
| **Tipo de nodo** *(en desarrollo)* | `permanent`: un nodo normal. `temporary`: un nodo temporal, por ejemplo para la duración de un evento; la app aún no usa estos nodos. Deja `permanent`. | Tras un reinicio. |
| **ID del nodo padre** *(en desarrollo)* | Solo lo necesita un nodo temporal: a qué nodo permanente pertenece. Déjalo vacío. | Al momento. |
| **Visibilidad en «Explorar la red»** | `closed`: el nodo no se muestra a los usuarios de otros nodos. `open`: el nodo aparece en su «Explorar la red». Esto no abre el registro. | Tras un reinicio. |
| **Visibilidad de las celdas publicadas** | Quién ve la lista de bots y páginas de la página «Publicación»: `off`, nadie; `members`, solo los usuarios de este nodo; `public`, todos. | Al momento. |
| **Modo de admisión de celdas** | `delegated`: solo con código de invitación; `admin`: con código o por solicitud con tu aprobación; `open`: cualquiera que conozca la dirección. | Al momento. |
| **Administradores** | Los identificadores (`cell_id`) de tus propias celdas, separados por comas. En el modo `admin` reciben en Nevod un mensaje por cada solicitud nueva. Tu `cell_id` está en la página «Resumen». | Al momento. |

Reiniciar el nodo, en el servidor, en la carpeta `/opt/nevod/installer/docker`:

```
docker compose restart nevod_node
```

## Solicitudes de acceso

Funciona en el modo de admisión `admin`. Cuando alguien sin código intenta registrarse, la app envía una solicitud por sí sola, que aparece aquí con un nombre y una nota. **Aprobar**: la persona obtiene acceso al momento y una notificación en el teléfono. **Rechazar**: la app le muestra que la solicitud fue rechazada.

## Buzón

Los mensajes que los usuarios del nodo enviaron desde la app a su cuenta **administrator**: denuncias de mensajes, preguntas. Todo nodo tiene una cuenta administrator, que se crea sola en el primer arranque.

Abre una conversación, escribe una respuesta y pulsa **Responder**: la respuesta llega al usuario en Nevod, cifrada, en nombre de administrator. A los mensajes de los usuarios se responde solo así, en la app, no por correo.

Si el usuario adjuntó al mensaje el registro de la app (para investigar un problema), en la conversación aparece el enlace **descargar nevod.log**.

Los usuarios ven la cuenta administrator de tu nodo con la marca **Administrador del nodo** y el nombre del nodo. La marca la confirma la clave de tu nodo, así que nadie más puede hacerse pasar por el administrador de tu nodo. La insignia azul ✓ es la señal de la administración del proyecto Nevod: la confirma la firma del curador del proyecto y solo la tienen los nodos del proyecto.

## Invitaciones

**Crear un código:** elige la validez (1 hora, 24 horas, 7 días) → **+ Crear código**. Aparecen un código QR y un enlace: puedes mostrarlos en pantalla, reenviarlos o pulsar **Copiar enlace**. El enlace abre Nevod con la dirección del nodo y el código ya rellenados. El código corto, como `ABCD-EFGH`, solo sirve si la app de la persona ya tiene puesto tu nodo.

Cada código sirve una sola vez. Debajo están todos los códigos con su validez y estado: activo, usado, por quién.

**Celdas admitidas**: quién entró y por invitación de quién. El interruptor **Puede invitar** permite a esa persona crear códigos desde la app (Perfil → Invitar a alguien); en el modo `delegated` así delegas las invitaciones en personas de confianza.

Más en [Invitar a personas](../node-invite/).

## Nodos

**Conexión a la red Nevod.** El estado («conectado · nodos en línea» o «no conectado») y el botón **Conectarse a la red Nevod**. Un nodo conectado recibe de los nodos del proyecto notificaciones push para los teléfonos y un repetidor de llamadas. El campo **Token del administrador de otro nodo** sirve para conectarse a través de otro nodo en lugar de Nevod Open. Más en [Conectarse a la red Nevod](../node-network/).

**Nodos conocidos**: todos los nodos de la red que conoce tu nodo: nombre, dirección, en línea o no, cuándo dio señales por última vez. Un nodo que lleva 72 horas sin dar señales se quita de la lista y vuelve solo cuando reaparece en la red.

**Invitaciones de nodos**: un token con el que otro nodo puede conectarse a través del tuyo. Vale 10 minutos; dáselo al administrador del otro nodo en persona, no en público.

## Publicación

Los bots y páginas que tu nodo muestra a los usuarios en la app, en el «planeta» del nodo en «Explorar la red». Elige una celda, pon un título, un tipo (`bot`: un bot; `page`: una página de texto) y una descripción → **Publicar**. Retirarla de la publicación la quita de la lista; la celda en sí se queda.

Las casillas Claude, ChatGPT, Gemini son para un bot de IA externo que funciona con la clave del usuario: qué proveedores acepta. Para un bot normal, no marques ninguna.

Quién ve esta lista se fija en «Ajustes» → «Visibilidad de las celdas publicadas».

## Bots de IA

Bots de IA que funcionan dentro del propio nodo y responden con Claude, ChatGPT o Gemini **con la clave del usuario**: la persona añade su clave en el chat con el bot, la clave llega con cada mensaje y el bot no la guarda. El nodo no tiene claves propias y no paga por la IA.

**Añadir un bot**: pon un nombre, una descripción, una instrucción para el modelo y los proveedores, o toma una plantilla ya hecha (AI Assistant, Tolmach el traductor) y ajústala. Un bot activado aparece a los usuarios del nodo en la lista «En este nodo». Uno desactivado queda detenido y oculto, y conserva su nombre. Eliminarlo es definitivo: se borran las claves y el nombre del bot; los usuarios conservan sus conversaciones.

> Las conversaciones con un bot de IA las descifra código de tu nodo y las pasa al proveedor elegido. Los usuarios están avisados en la [Política de privacidad](../../privacy/) (sección 5). Si activas bots de IA, tú, como propietario del nodo, participas en esa transferencia.

## Seguridad

Cuentas personales de administrador: **Añadir / cambiar contraseña**: un usuario y una contraseña (guardada como hash). Una cuenta por administrador; si alguien se va, borra su cuenta sin cambiar la contraseña principal. La contraseña principal de `.env` siempre funciona como acceso de reserva.

Cinco contraseñas incorrectas seguidas desde una misma dirección bloquean el acceso para esa dirección durante 15 minutos.

## Diagnóstico

**Comprobar**: el autodiagnóstico del nodo (hasta 10 segundos):

| Comprobación | Qué significa |
|---|---|
| Código actualizado | Si la versión instalada del nodo se ha quedado atrás respecto al protocolo; si es así, actualiza el nodo (consulta [Mantenimiento](../node-maintenance/)). |
| Coherencia identity/DB | Si los ajustes de `node.json` coinciden con la base de datos. |
| Dependencias y configuración | Si hay errores en los ajustes (por ejemplo, un repetidor de llamadas sin `TURN_SECRET`). |
| Accesibilidad externa | Si otro nodo de la red puede llegar al tuyo desde fuera. Mientras el nodo no esté conectado a la red, muestra «No hay pares conocidos»: es lo esperado. |

**Registros**: las últimas entradas del registro del nodo. El texto de los mensajes nunca entra en el registro.
