# Primera configuración en el panel de administración

El nodo está funcionando: ahora hay que ponerle nombre, decidir a quién admitir y registrarte tú en él. Todo se hace en el panel de administración, en `https://node.example.org/nevod-admin` (cómo abrirlo: paso 9 de la [instalación](../node-install/)).

El idioma del panel se cambia en su cabecera. La descripción detallada de cada página y ajuste: en [El panel de administración: todas las páginas y ajustes](../node-admin/).

## Qué hay en cada parte del panel

| Página | Para qué sirve |
|---|---|
| **Resumen** | Las celdas (usuarios) registradas en el nodo. |
| **Ajustes** | Nombre del nodo, modo de admisión, visibilidad. |
| **Solicitudes de acceso** | Las solicitudes de los usuarios, si el nodo funciona en modo de aprobación. |
| **Buzón** | Mensajes de los usuarios al administrador del nodo: denuncias, preguntas. Puedes responder desde aquí. |
| **Invitaciones** | Códigos de invitación para usuarios. |
| **Nodos** | Conexión a la red Nevod y los demás nodos que conoce tu nodo. |
| **Publicación**, **Bots de IA** | Los bots y canales que el nodo muestra a sus usuarios. |
| **Seguridad** | Cuentas de administrador adicionales. |
| **Diagnóstico** | El autodiagnóstico del nodo y su registro. |

## 1. Ponle nombre al nodo

**Ajustes → Nombre del nodo** → escribe un nombre, por ejemplo «Familia García» o «Colegio n.º 5» → **Guardar**.

Los usuarios ven el nombre en la app. Los demás nodos de la red conocen el nombre nuevo después de reiniciar el nodo (ver más abajo). No se pueden usar nombres que hagan pasar el nodo por un nodo del proyecto: con las palabras Nevod, admin, support, official y similares.

## 2. Decide a quién admitir

**Ajustes → Modo de admisión de celdas.** Un nodo nuevo funciona por defecto **por invitación**: solo puede registrarse quien tenga un código que tú hayas dado. Normalmente es justo lo que se necesita.

| Modo en el panel | Quién puede registrarse | Quién crea los códigos de invitación |
|---|---|---|
| `delegated` — solo con código de invitación (por defecto) | Solo con código de invitación. Sin código, el nodo no acepta el registro. | Tú en el panel, y los usuarios a los que hayas dado el derecho **Puede invitar**. |
| `admin` — solicitud + tu aprobación | Con código, al momento. Sin código, la app envía una solicitud por sí sola y muestra «Esperando aprobación»; tú la apruebas o la rechazas en la página **Solicitudes de acceso**. | Solo tú, en el panel. |
| `open` — sin código | Cualquiera que conozca la dirección del nodo. Sirve para una comunidad abierta; ten en cuenta que luego tendrás que ordenar a mano los registros y los nombres ocupados. | No hace falta código. |

El modo se aplica al momento.

## 3. Regístrate en tu nodo

1. En el panel: **Invitaciones** → elige la validez (1 hora, 24 horas o 7 días) → **+ Crear código**. Aparecen un código QR y un código corto como `ABCD-EFGH`.
2. En el teléfono, instala Nevod desde el App Store.
3. Escanea el código QR con la cámara normal del teléfono. Es un enlace: se abre la página de invitación; toca en ella **Abrir en Nevod**. La app se abre con la dirección de tu nodo y el código ya rellenados.
4. Escribe tu nombre y toca **Empezar**.

Si escanear no es cómodo, pulsa **Copiar enlace** en el panel y envíatelo. Si «Abrir en Nevod» no funcionó: en la app toca **Empezar a chatear**, escribe tu nombre, toca **¿Tienes un código de invitación?** y pega el enlace en el campo del código. El código corto en lugar del enlace solo sirve cuando la app ya tiene puesto tu nodo.

> Si Nevod en este teléfono ya está registrado en otro nodo (por ejemplo, en Nevod Open), la invitación no te pasa a tu nodo por sí sola: la app avisa de que primero tienes que restablecer la identidad: **Perfil → Restablecer identidad…**. Restablecerla borra para siempre tu identidad, tus contactos, los mensajes del teléfono y tu registro en el nodo anterior. Después, abre de nuevo el enlace de invitación.

Cada código sirve una sola vez. Crea uno distinto para cada persona; más en [Invitar a personas](../node-invite/).

## 4. Decide si el nodo es visible en la red

**Ajustes → Visibilidad en «Explorar la red»**:

- `closed` (por defecto): el nodo no aparece en «Explorar la red» para los usuarios de otros nodos. Sirve para una familia, una organización, cualquier grupo cerrado.
- `open`: el nodo aparece en «Explorar la red» y los usuarios de otros nodos pueden encontrarlo. Sirve para una comunidad abierta. El nodo se ve mientras está conectado a la red, y solo para quien ya está registrado en algún nodo: antes de registrarse, la app solo muestra los nodos del proyecto.

Esta elección no abre el registro: a quién admitir lo sigue decidiendo el modo de admisión de celdas (paso 2). El anillo dorado de nodo verificado en «Explorar la red» por ahora solo lo tienen los nodos del proyecto Nevod.

Este ajuste, igual que el nombre del nodo para otros nodos, se aplica tras reiniciar el nodo. En el servidor, en la carpeta `/opt/nevod/installer/docker`:

```
docker compose restart nevod_node
```

## 5. Comprueba el nodo

**Diagnóstico → Comprobar.** En unos segundos el nodo muestra si todo está bien: si su código está al día, si sus ajustes coinciden con la base de datos, si hay problemas de configuración, si el nodo es accesible desde fuera.

La accesibilidad desde fuera el nodo la comprueba a través de otros nodos de la red. Mientras tu nodo no esté conectado a nadie, esa línea mostrará «No hay pares conocidos»: es lo esperado. Conectarse a la red es el siguiente paso, y es importante: sin él, los teléfonos no recibirán notificaciones mientras la app esté cerrada. Consulta [Conectarse a la red Nevod](../node-network/).

## 6. Opcional: más administradores

**Seguridad → Añadir / cambiar contraseña**: cada administrador tendrá su propio usuario y contraseña, y podrás revocarlos sin cambiar la contraseña principal de `.env`. La contraseña principal queda como acceso de reserva por si se pierden las demás.
