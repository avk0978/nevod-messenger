# Seguridad y copias de seguridad

Qué protege Nevod por sí solo, cómo te protege de estafadores y ataques, qué deberías hacer tú, cómo protegerte de desconocidos, cómo bloquear un chat con contraseña, cómo bloquear y denunciar, y por qué Nevod no hace copias de seguridad de las conversaciones.

## Qué está protegido sin que hagas nada

- **Las conversaciones y las llamadas están cifradas** en tu teléfono con la clave de la otra persona. Ni los nodos, ni los desarrolladores de Nevod, ni Apple pueden verlas.
- **Las claves, los contactos y el historial de mensajes se guardan solo en tu teléfono.** No están en las copias de seguridad de iCloud ni del ordenador, ni en los nodos, ni en manos del desarrollador.
- **Un nodo solo sabe lo necesario para entregar un mensaje:** quién está registrado en él, a quién escribes y cuándo, pero no qué.

Cómo funciona en detalle: en la página [Seguridad](../../security/).

## Protección frente a estafadores y ataques

- **Nadie puede encontrarte por tu número de teléfono.** Nevod no tiene números de teléfono ni direcciones de correo, así que no pueden sacarse de una base de datos filtrada para usarlos en spam o llamadas fraudulentas. Solo puede escribirte quien tiene tu tarjeta o un miembro de tu nodo.
- **No hay contraseña de cuenta: no hay nada que robar.** No se puede espiar, adivinar ni sonsacarte. Al conectarse, el teléfono demuestra al nodo que tiene la clave, pero la clave nunca sale del teléfono.
- **Nadie puede hacerse pasar por la administración.** Los nombres de servicio —administrator, support, Nevod y parecidos— no se pueden registrar. La administración real lleva la insignia azul ✓, y el administrador de un nodo privado, la marca **Administrador del nodo**. Una cuenta con nombre de servicio sin insignia ni marca la señala la app con un ⚠ naranja y un aviso en el chat.
- **Las notificaciones falsas no pasan.** Una notificación de mensaje nuevo no contiene ningún texto que pueda fijar un extraño: solo «Mensaje nuevo» y el nombre del remitente, y los nombres de servicio se sustituyen por «Nevod». Una notificación «de Nevod» que te pida introducir un código o abrir un enlace es una estafa.
- **No se puede suplantar a tu nodo.** Todo lo que llega del nodo está firmado con su clave, y la app comprueba la firma. Incluso en una red Wi-Fi ajena, nadie en medio puede hacerse pasar por tu nodo ni colar mensajes falsos en su nombre.
- **Los archivos e imágenes peligrosos se descartan.** Los ataques más peligrosos contra teléfonos —como el programa espía Pegasus— llegan como una imagen o un archivo preparados a propósito y actúan sin un solo toque. Por eso Nevod comprueba todo lo que recibe de los demás: el tamaño del archivo está limitado y el tipo debe coincidir con el contenido; si no, el archivo no se muestra como imagen o vídeo y no se abre solo. Los avatares solo se aceptan de tus contactos y de los miembros de tu nodo, y la app nunca muestra la imagen enviada: la vuelve a dibujar ella misma.
- **Con el teléfono bloqueado, los archivos están cerrados.** Las fotos, vídeos y archivos de los chats los cifra iOS y quedan inaccesibles unos segundos después de bloquear el teléfono, incluso para quien haya conseguido acceder a su almacenamiento. El selector de apps muestra una portada de Nevod en lugar de tu conversación.
- **Atacar un nodo no expone tus conversaciones.** En un nodo no hay ni texto de mensajes ni tus claves: aunque acceda al nodo, un atacante no puede leer tus conversaciones.
- **Los nodos verificados están marcados.** Los nodos del proyecto Nevod llevan en **Explorar la red** un anillo dorado: lo confirma la firma del proyecto, y un nodo falso no puede conseguirlo.

## Qué deberías hacer tú

El punto más vulnerable es el propio teléfono: quien desbloquea tu teléfono ve también tus conversaciones. Y si ya hay en el teléfono un programa espía que ha roto el propio iOS, ve todo lo que tú ves en pantalla; de eso no te protege ninguna app, tampoco Nevod. Por eso es importante que no llegue a entrar.

- **Un código en el iPhone**: imprescindible, y no uno simple como 000000.
- **Mantén iOS actualizado**: las actualizaciones cierran las vulnerabilidades que usan los programas espía.
- **Reinicia el teléfono de vez en cuando.** Muchos programas espía no sobreviven a un reinicio.
- **Si eres periodista, defensor de derechos humanos o por otro motivo podrías ser un objetivo**, activa el **Modo de aislamiento** del iPhone: **Ajustes → Privacidad y seguridad → Modo de aislamiento**. Cierra muchas de las vías que usan ataques como Pegasus.
- **Una contraseña en los chats importantes**: ver más abajo.
- **No des a nadie códigos ni claves.** La administración de Nevod solo escribe en la app, desde la cuenta **administrator** con la insignia ✓ (en un nodo privado, con la marca **Administrador del nodo**), nunca por correo, y nunca pide contraseñas, claves ni códigos. Quien los pide es un estafador.

## Contraseña del chat

Puedes bloquear un chat con contraseña: así, aunque alguien tenga tu teléfono desbloqueado en la mano, no podrá abrir ese chat.

1. Abre el chat → el engranaje arriba a la derecha → activa **Protección con contraseña**.
2. Define dos contraseñas:
   - **Contraseña de desbloqueo**: con ella abres el chat;
   - **Contraseña de coacción**: para cuando te obliguen a abrir el chat. Si la introduces en lugar de la verdadera, la conversación de este chat se **borra en silencio** de tu teléfono y en la pantalla aparece el habitual «Contraseña incorrecta»; para quien mira, parece un error al teclear.
3. Las contraseñas deben ser distintas. Para cambiarlas, en el mismo sitio: **Cambiar contraseñas**.

> La contraseña del chat se guarda solo en este teléfono, y no la contraseña en sí sino su hash. **Una contraseña olvidada no se puede recuperar**, ni por ti ni por los desarrolladores. Si la olvidaste, toca **¿Olvidaste la contraseña?** en la pantalla de acceso: la conversación de este chat se borra del teléfono, se quita la protección con contraseña y el chat vuelve a abrirse, ya vacío. Elige una contraseña que no vayas a olvidar. La contraseña de coacción borra la conversación solo en tu teléfono: la otra persona la conserva.

## Protección frente a desconocidos

No solo pueden escribirte y llamarte las personas a las que diste tu tarjeta. En un nodo abierto, como Nevod Open, cualquiera puede registrarse, y los miembros del nodo se ven en **Contactos → En este nodo**. Además, alguien con quien hablas puede reenviar tu tarjeta a otra persona. Aquí, desconocido es quien no está en tus contactos. Las cuentas oficiales de Nevod y el administrador de tu nodo no cuentan como desconocidos.

En **Perfil → Seguridad** hay dos ajustes. Activarlos o no es decisión tuya; al principio los dos están desactivados:

- **Llamadas solo de contactos**: una llamada de alguien que no está en tus contactos se rechaza en silencio y el teléfono no suena. Para quien llama, la llamada termina enseguida; en tu historial de llamadas aparece como **Rechazada: no está en contactos**.
- **Imágenes de desconocidos: al tocar**: las fotos y vídeos de alguien que no está en tus contactos no se muestran enseguida: el chat muestra un marcador **Foto: mostrar** o **Vídeo: mostrar**, y la app abre el archivo solo después de que lo toques. Así, ni siquiera una imagen preparada puede activarse sola.

En un nodo cerrado, donde el administrador conoce a todos los miembros, estos ajustes no suelen hacer falta. En un nodo abierto conviene activarlos.

## Bloquear y denunciar

- **Bloquear** a alguien: ajustes del chat (el engranaje) → **Bloquear**. No podrá escribirte ni llamarte y no se enterará. La lista de bloqueados: **Perfil → Seguridad → Bloqueados**.
- **Denunciar un mensaje**: mantenlo pulsado → **Denunciar**. Denunciar a una persona: ajustes del chat → **Denunciar**.
- **Denunciar un abuso** sin un chat concreto: **Perfil → Seguridad → Denunciar un abuso**.

La denuncia va a la administración de tu nodo, como mensaje en la app a la cuenta administrator (o por correo a abuse@nevod.network). Los mensajes de Nevod están cifrados y la administración no los ve, así que la app adjunta a la denuncia el texto del mensaje denunciado. La respuesta llega al chat con administrator. Junto con la denuncia puedes bloquear a la persona: **Bloquear también**.

## No hay copias de seguridad, y es a propósito

Las claves, los contactos y el historial de mensajes existen solo en tu teléfono. Por eso:

- **si pierdes, rompes o restableces el teléfono, las conversaciones no se pueden recuperar;**
- **eliminar la app también borra el historial;**
- **todavía no hay traspaso a un teléfono nuevo.** En un teléfono nuevo crearás una identidad nueva, y tus contactos necesitarán tu nueva tarjeta.

Es consecuencia de cómo está hecho Nevod: una copia desde la que se pudieran restaurar tus conversaciones sería también una copia a la que podría acceder otra persona. Si necesitas conservar algo de una conversación mucho tiempo, guárdalo aparte: fotos y archivos, con **Compartir**.

## Restablecer la identidad

**Perfil → Restablecer identidad…** borra para siempre tu identidad, tus contactos, los mensajes del teléfono y tu registro en el nodo. La app te pide escribir una palabra de confirmación para que no ocurra por accidente.

Lo necesitas si quieres empezar de cero o cambiarte a otro nodo. Tus contactos verán **Identidad eliminada** en vuestro chat; para volver a escribirte necesitarán tu nueva tarjeta.
