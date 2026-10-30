# Invitar a personas

Cómo llega la gente a tu nodo —por invitación, por solicitud o libremente— y cómo se encuentran después, también con personas de otros nodos. Qué modo usar se decide en el panel: **Ajustes → Modo de admisión de celdas** (consulta [Primera configuración](../node-panel/), paso 2).

## Invitación del administrador

La vía principal, y la única mientras el nodo funcione en el modo por defecto (`delegated`).

1. Panel → **Invitaciones** → elige la validez: 1 hora, 24 horas o 7 días → **+ Crear código**.
2. Da la invitación a la persona de una de estas formas:
   - **muestra el código QR** en pantalla: la persona lo escanea con la cámara normal del teléfono;
   - **Copiar enlace**, y envíalo por cualquier mensajero o por correo;
   - **dicta el código corto**, como `ABCD-EFGH`: solo sirve si la app de la persona ya tiene puesto tu nodo.
3. La persona instala Nevod desde el App Store, abre el enlace (la página de invitación tiene el botón **Abrir en Nevod**), escribe un nombre y toca **Empezar**.

Lo que conviene saber de los códigos:

- **Cada código sirve una sola vez.** Un código por persona. Un código usado aparece en la lista como «usado», con quién entró con él.
- **Validez.** No elijas una semana para un código que publicas en un chat de grupo: mientras no se use, cualquiera que lo consiga puede usarlo. 1 hora es para un código que enseñas a alguien en persona.
- **El enlace no revela nada de más.** Solo contiene la dirección del nodo y el código. La página de invitación de nevod.network no ve ni el código ni la dirección: quedan en la parte del enlace que va tras `#`, que el navegador no envía al servidor.

Si la persona ya usa Nevod en otro nodo, la invitación no la cambia por sí sola: la app le avisa de que primero tiene que restablecer su identidad (**Perfil → Restablecer identidad…**). Restablecerla borra para siempre su identidad, sus contactos, los mensajes del teléfono y su registro en el nodo anterior. Para simplemente chatear, no hace falta cambiarse: basta con intercambiar contactos (ver más abajo).

## Los miembros invitan ellos mismos

En el modo `delegated` puedes delegar las invitaciones en personas de confianza: panel → **Invitaciones** → **Celdas admitidas** → activa **Puede invitar** para esa persona. Entonces **Perfil → Invitar a alguien** en su app crea un código, y la app muestra un código QR para escanear.

En el modo `open` cualquier miembro puede invitar, aunque en ese modo no hace falta código.

## Solicitudes con aprobación

El modo `admin` sirve si quieres que el nodo se pueda encontrar y que se pueda pedir la entrada, pero decides tú.

1. La persona encuentra tu nodo en «Explorar la red» y toca **Unirse a este nodo** (si el nodo es visible ahí; consulta [Primera configuración](../node-panel/), paso 4), o en el primer arranque de la app toca **Cambiar servidor…** y escribe la dirección del nodo `node.example.org/nevod-ws`.
2. La app envía una solicitud por sí sola y muestra «Esperando aprobación».
3. La solicitud aparece en el panel, en la página **Solicitudes de acceso**. Si en **Ajustes → Administradores** está tu `cell_id`, además te llega un mensaje en Nevod.
4. **Aprobar**: la persona recibe una notificación y entra al momento. **Rechazar**: la app le muestra que la solicitud fue rechazada.

Los códigos de invitación también funcionan en el modo `admin`: con código se entra al momento, sin solicitud.

## Registro libre

En el modo `open` puede registrarse cualquiera que conozca la dirección del nodo. Sirve para una comunidad abierta. Ten en cuenta:

- el nodo nunca borra registros ni libera nombres por su cuenta: tendrás que limpiar a mano, en la página **Resumen** (botón ✕);
- los nombres de servicio (Nevod, administrator, support y similares) no se pueden ocupar en ningún modo.

## Cómo se encuentran los miembros

Registrarse en el mismo nodo no convierte a las personas en contactos. Para chatear, tienen que intercambiar contactos:

- **Perfil → Compartir mi tarjeta**: muestra un código QR y el texto de la tarjeta; la otra persona: **Contactos → Añadir contacto**, y escanea el QR o pega el texto;
- la tarjeta se puede enviar por cualquier medio: no tiene nada secreto, solo un identificador y claves públicas.

A las personas **de otros nodos** se las añade igual: la tarjeta contiene la dirección de su nodo de origen. Para que esas conversaciones funcionen, tu nodo debe estar [conectado a la red Nevod](../node-network/).

> Eliminar a un usuario (panel → **Resumen** → ✕) revoca por completo su admisión: se borran el registro, los mensajes no entregados y los tokens de notificación. Para volver, la persona necesitará una nueva invitación.
