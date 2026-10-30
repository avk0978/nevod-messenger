# Preguntas y problemas

Respuestas breves a preguntas frecuentes y qué hacer si algo no funciona. Si tu pregunta no está aquí, escríbenos (al final de esta sección).

## Preguntas generales

**¿Nevod es de pago?**
No. La app es gratuita, sin suscripciones ni publicidad. Solo podrías tener que pagar a un proveedor de IA si usas asistentes de IA con tu propia clave; consulta [Bots y asistentes de IA](../bots/).

**¿Necesito un número de teléfono?**
No. Nevod no necesita número de teléfono ni correo electrónico y no los pide. Solo te conocen aquellos con quienes intercambiaste tarjetas.

**¿Hay Nevod para Android o para ordenador?**
Por ahora, solo para iPhone y iPad. La versión para Android está en desarrollo.

**¿Puedo usar Nevod en dos dispositivos a la vez?**
Todavía no: una identidad vive en un dispositivo. En un segundo iPhone o iPad tendrás una identidad aparte con sus propios contactos.

**He cambiado de teléfono. ¿Cómo paso mis conversaciones?**
Por ahora no se puede: no hay traspaso a un dispositivo nuevo, y Nevod no hace copias de seguridad de las conversaciones a propósito. En el teléfono nuevo, crea una identidad nueva y envía tu nueva tarjeta a tus contactos. Más en [Seguridad y copias de seguridad](../security/).

**¿Cómo me cambio a otro nodo?**
Solo restableciendo la identidad: **Perfil → Restablecer identidad…** y luego abre la invitación al nuevo nodo. Restablecerla borra para siempre tu identidad, tus contactos, los mensajes del teléfono y tu registro en el nodo anterior. Para simplemente chatear con alguien de otro nodo no hace falta cambiarse: basta con su tarjeta.

## Registro

| Qué ves | Qué hacer |
|---|---|
| «Ese nombre ya está en uso, elige otro» | ese nombre ya existe en el nodo, o es un nombre de servicio (administrator, support, Nevod…). Elige otro. |
| «Se necesita un código de invitación» | el nodo solo admite con invitación. Pide una al administrador del nodo o elige otro nodo. |
| «Código no válido o caducado: consigue uno nuevo» | el código ya se usó o ha caducado. Pide uno nuevo. |
| «Esperando aprobación» | el nodo admite por solicitud: espera la decisión del administrador; recibirás una notificación. |
| «Solicitud rechazada» | el administrador del nodo rechazó tu solicitud. Puedes elegir otro nodo, como Nevod Open. |
| abriste una invitación y la app dice «Invitación a otro nodo» | ya estás registrado en un nodo. Consulta «¿Cómo me cambio a otro nodo?» más arriba. |

## Conexión

**Encima del campo de texto del chat pone «Sin conexión» o «Conectando…» durante mucho tiempo, y no puedes enviar.**
Comprueba tu conexión a internet: abre cualquier web. Si usas una VPN, prueba a desactivarla o a cambiar de servidor. Cambia entre Wi-Fi y datos móviles. Si no sirve, puede que tu nodo no esté disponible temporalmente: espera unos minutos; si estás en un nodo privado, avisa a su administrador.

**No llegan notificaciones con Nevod cerrado.**
- **Ajustes del iPhone → Nevod → Notificaciones**: deben estar permitidas.
- Comprueba que no esté activado No molestar u otro modo de concentración.
- Comprueba que no estén desactivadas las notificaciones de este chat: ajustes del chat (el engranaje) → **Notificaciones**.
- En un nodo privado: pide al administrador que compruebe que el nodo está [conectado a la red Nevod](../node-network/); sin eso no llegan notificaciones.

**Una llamada no se conecta.** Consulta [Llamadas](../calls/), «Si una llamada no se conecta».

## Mensajes y archivos

**Hay un reloj naranja junto a un mensaje.**
La otra persona no está conectada: el mensaje la espera en el nodo y se entregará cuando se conecte. El nodo guarda esos mensajes hasta 72 horas; si la persona no se conecta en ese tiempo, el mensaje no llegará.

**«Mensaje no enviado. ¿Volver a enviar?»**
No había conexión al enviarlo. Toca esa línea cuando vuelva la conexión.

**Un archivo no se envía.**
- Ocupa más de 50 MB: la app te lo dice. Elige los vídeos con **Foto o vídeo**: se comprimen.
- «No se pudo cargar el vídeo»: si el clip está guardado en iCloud, puede que en el teléfono solo haya una copia reducida. Abre el vídeo en la app Fotos, espera a que se descargue entero y vuelve a intentarlo. Si el error se repite, avísanos (consulta «Informar de un problema» más abajo).
- «No se pudo comprimir el vídeo»: prueba con un clip más corto o envíalo con **Archivo** si ocupa menos de 50 MB.

**«No se pudo guardar el archivo: almacenamiento lleno».**
Los archivos recibidos ocupan espacio en el teléfono dentro de la cuota de Nevod. Auméntala: **Perfil → Almacenamiento → Cuota**, o elimina chats que no necesites (en la lista de chats, desliza a la izquierda → **Eliminar**).

## Asistentes de IA

**El bot dice que hace falta una clave, o la clave no se acepta.**
Comprueba que la clave se copió entera y no se ha revocado en el sitio del proveedor, y que tu cuenta del proveedor tiene saldo o no has agotado el límite gratuito. Puedes cambiar la clave en el chat con el bot: **Cambiar**. Más en [Bots y asistentes de IA](../bots/).

## Informar de un problema

**Perfil → Diagnóstico**: describe qué pasó y más o menos cuándo (por ejemplo, «no llegaron 2 de 3 fotos, hacia las 21:00») y toca **Enviar a los desarrolladores**. Junto con tu descripción se envía el registro técnico de la app: se guarda solo en el teléfono y no contiene texto de mensajes. El registro se envía por correo a support@nevod.network o, si el teléfono no tiene una cuenta de correo configurada, al administrador de tu nodo en Nevod; la respuesta llega al chat con él.

Para denunciar a una persona o un mensaje, consulta [Seguridad](../security/), «Bloquear y denunciar».
