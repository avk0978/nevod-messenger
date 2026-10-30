# Conectarse a la red Nevod

Para qué necesita un nodo la red común, cómo conectarse con un botón y qué ven después los demás nodos.

## Para qué conectarse

Un nodo que no está conectado a nadie es una isla. Funciona, pero:

- **sus usuarios solo pueden escribirse y llamarse entre ellos.** Escribir a alguien de otro nodo, o recibir un mensaje suyo, es imposible: el nodo no sabe adónde mandarlo;
- **los teléfonos no reciben notificaciones** mientras la app está cerrada: solo los nodos del proyecto, que tienen la clave de Apple, pueden enviar notificaciones push a Nevod del App Store, y lo hacen para los nodos de la red;
- **las llamadas a través de redes complicadas pueden no conectarse:** un nodo sin repetidor de llamadas (TURN) propio lo obtiene de los nodos de la red; más en [Llamadas a través de tu propio nodo](../node-turn/).

Por eso casi siempre conviene conectar el nodo a la red, incluso un nodo cerrado de una familia u organización. Conectarse a la red **no abre el registro** y **no muestra el nodo en «Explorar la red»**: a quién admitir y si el nodo es visible lo sigues decidiendo tú en los ajustes.

## Cómo conectarse

1. Asegúrate de que el puerto **8765** del servidor está abierto desde fuera, tanto en `ufw` como en el cortafuegos del proveedor (consulta la [instalación](../node-install/), pasos 1 y 5). Por él se comunican los nodos.
2. Panel → **Nodos** → **Conectarse a la red Nevod**.
3. En unos segundos aparece un mensaje de que el nodo se ha conectado. El estado de arriba del bloque pasa a «conectado · nodos en línea: N», y en la lista **Nodos conocidos** aparecen los nodos de la red.

El nodo se conecta a través de Nevod Open, un nodo del proyecto que admite nodos en la red sin invitación. La autenticidad de Open se comprueba por la huella de su certificado, incluida en el programa del nodo: no se puede sustituir por el camino.

Si el panel dice que **el nodo de la red no pudo llegar a tu nodo desde fuera**, la conexión se hizo, pero nadie puede conectarse de vuelta a ti. Casi siempre es el puerto 8765 cerrado. Ábrelo y pulsa el botón otra vez. También puedes comprobarlo luego: **Diagnóstico → Comprobar → Accesibilidad externa**.

La conexión se conserva: tras un reinicio, el nodo vuelve a contactar solo con todos los nodos que conoce.

## Conectarse a través de otro nodo

Si conoces al administrador de otro nodo, puedes conectarte a través de su nodo en lugar de Open:

1. Él, en su panel: **Nodos → Invitaciones de nodos → + Crear invitación de nodo**, y te da el token en persona (el token vale 10 minutos).
2. Tú: **Nodos** → pega el token en el campo **Token del administrador de otro nodo** → **Conectarse con token**.

El resultado es el mismo: tu nodo pasa a formar parte de la red. Del mismo modo puedes dejar entrar en la red a través del tuyo a un nodo que conozcas: crea un token para él.

## Qué ven los demás nodos

Los nodos de la red intercambian una lista de nodos. Sobre tu nodo, contiene:

- el identificador del nodo (`node_id`), su nombre y su dirección para las conexiones entre nodos (`dominio:8765`);
- la huella del certificado del nodo;
- si el nodo es visible en «Explorar la red», y si tiene repetidor de llamadas y clave de notificaciones propios.

Si el nodo es visible en «Explorar la red» (ajuste `open`), los nodos de la red saben además qué celdas están registradas en él, por sus identificadores, sin nombres. Un nodo cerrado no lo comunica: un mensaje para su usuario llega a la dirección de la tarjeta de contacto, que indica el nodo de origen.

Lo que los nodos de la red no reciben nunca: el texto de los mensajes, los archivos, las llamadas, los contactos de los usuarios, los nombres y claves de las celdas de un nodo cerrado.

## Cómo salir de la red

Todavía no hay un botón «salir de la red». Los demás nodos quitan por sí solos de sus listas a un nodo que lleva 72 horas sin dar señales. Si el nodo debe desconectarse de la red para siempre, detenlo o cierra el puerto 8765.
