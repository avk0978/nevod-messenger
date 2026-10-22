# Spanish content for nevod.network — same facts and structure as content_uk.py / content_en.py.

T = {
    "nav": {"index": "Inicio", "manifesto": "Manifiesto ZKI", "compare": "Comparación", "security": "Seguridad",
            "cities": "Para ciudades", "download": "Descargar", "about": "Sobre el proyecto"},
    "nav_support": "Soporte", "nav_privacy": "Privacidad", "nav_terms": "Condiciones de uso", "nav_node": "Tu propio nodo",
    "footer_owner": "© 2026 Nevod · Kolpakov Andrey",
}

INDEX = """
<section class="hero"><div class="wrap">
<div class="eyebrow">Zero Knowledge Infrastructure</div>
<h1>Nevod: un mensajero cuyo desarrollador está técnicamente separado de tus datos</h1>
<p class="lead">No por una promesa ni solo por el cifrado, sino por la arquitectura. El desarrollador no tiene tus claves, ni una clave maestra, ni un servidor central, ni una base de datos de usuarios. Aunque alguien llegue con una exigencia, no hay nada que entregar.</p>
<div class="btns"><a class="btn primary" href="/es/manifesto/">Leer el manifiesto ZKI</a><a class="btn ghost" href="/es/download/">Descargar</a></div>
</div></section>
<main><div class="wrap">
<h2>El cifrado es una cerradura. ZKI es que el desarrollador no tenga la llave</h2>
<p>La mayoría de los mensajeros cifran los mensajes, pero la empresa sigue operando los servidores, mantiene la base de datos de usuarios, vincula las cuentas a números de teléfono y ve quién habla con quién y cuándo. El cifrado protege el contenido en tránsito; todo lo demás queda en manos de la empresa.</p>
<p>Nevod está construido según el principio de <b>Zero Knowledge Infrastructure</b>: la infraestructura está diseñada para que su creador no pueda acceder al contenido, ni aunque quisiera ni aunque lo obligaran.</p>
<div class="grid">
<div class="card"><h3>🔑 Las claves solo las tienes tú</h3><p>Las claves se crean en tu dispositivo y nunca salen de él. El desarrollador no tiene copias, ni clave maestra, ni copias de seguridad.</p></div>
<div class="card"><h3>🌐 Un nodo propio para cualquiera</h3><p>No hay servidor central: la red está formada por nodos independientes y nadie te impide ejecutar el tuyo. No existe un único punto donde se concentre todo.</p></div>
<div class="card"><h3>📵 La identidad es una clave, no un número</h3><p>Sin número de teléfono ni correo electrónico. El desarrollador no lleva un registro de personas y no sabe quién eres.</p></div>
<div class="card"><h3>📭 No hay nada que entregar</h3><p>Si alguien exige una conversación, el desarrollador no tiene nada que dar. No porque lo oculte, sino porque no lo tiene.</p></div>
</div>
<p class="note">ZKI es la base del desarrollo de Nevod. Cada decisión técnica se somete a una sola pregunta: ¿obtiene el creador de la infraestructura acceso al contenido? <a href="/es/manifesto/">Manifiesto de Zero Knowledge Infrastructure →</a></p>
<h2>Red distribuida de baja carga</h2>
<p>La carga de cada nodo de Nevod está limitada por su propio círculo (familia, hogar, equipo), no por el tamaño de toda la red: un millón de usuarios nuevos en otro lugar no añaden ni un byte a tu nodo. El nodo funciona en hardware doméstico común, la red no tiene centro y el propio nodo solo transporta texto cifrado.</p>
<p><a href="/es/compare/#low-load">Una comparación de Nevod con otras 14 redes, de FidoNet a Signal →</a></p>
<h2>Qué hace Nevod</h2>
<div class="grid">
<div class="card"><h3>🔒 Cifrado de extremo a extremo</h3><p>Cada mensaje, foto, mensaje de voz y llamada se cifra en el teléfono. Los nodos solo ven datos cifrados.</p></div>
<div class="card"><h3>📞 Llamadas y vídeo</h3><p>Llamadas de voz y vídeo, mensajes de voz, fotos, vídeos y archivos.</p></div>
<div class="card"><h3>🏙️ Comunicación sin internet</h3><p>La arquitectura puede transmitir mensajes por cualquier canal disponible, también dentro de una ciudad sin acceso a internet.</p></div>
<div class="card"><h3>🛡️ Protección contra abusos</h3><p>Bloqueo y denuncias, cuentas oficiales verificadas, protección contra la suplantación de la administración.</p></div>
</div>
<h2>Estado del proyecto</h2>
<div class="tbl"><table class="status">
<tr><th style="width:34%">Área</th><th>Estado</th></tr>
<tr><td>App para iPhone</td><td>Prueba cerrada (TestFlight); publicación en App Store en preparación</td></tr>
<tr><td>App para Android</td><td>En desarrollo</td></tr>
<tr><td>Nodos de la red</td><td>En funcionamiento, se instalan con Docker</td></tr>
<tr><td>Idiomas de la app</td><td>8: ucraniano, inglés, ruso, alemán, turco, español, italiano, francés</td></tr>
</table></div>
</div></main>
"""

MANIFESTO = """
<main><div class="wrap">
<div class="eyebrow" style="color:#8A6A00">Manifiesto</div>
<h1>Zero Knowledge Infrastructure</h1>
<p><b>La red que estás viendo, Nevod, es la primera implementación completa de una sola idea: quienes construyen la infraestructura de comunicación no deben poder ver técnicamente lo que pasa por ella.</b></p>
<h2>La postura</h2>
<p>Yo construyo herramientas.<br>No vigilo cómo se usan.<br>No tengo acceso a los datos.<br>¡Y esa es la arquitectura del software!</p>
<p>No es una política de privacidad. No es una promesa de marketing. Es una imposibilidad técnica incorporada en los cimientos.</p>
<h2>El principio del cuchillo</h2>
<p>El fabricante de un cuchillo no es responsable de cómo se usa. Con un cuchillo se puede cortar pan, o no. Es la elección de quien lo sostiene, no de quien lo forjó.</p>
<p>La misma lógica se aplica a la infraestructura de comunicación.</p>
<p>Yo construyo el canal. Lo que pasa por él no es asunto mío.<br>No porque no me importe. Porque <b>no debe</b> serlo.</p>
<p>El derecho a la comunicación privada es un derecho humano fundamental. La infraestructura de comunicación no debe ser un punto de vigilancia.</p>
<h2>Qué significa técnicamente</h2>
<p>Las claves de cifrado se generan en el dispositivo del usuario.<br>Nunca salen de ese dispositivo.<br>No tengo servidores que guarden claves.<br>No tengo clave maestra.<br>No tengo copia de seguridad.</p>
<p>Si alguien viene a pedirme una conversación, no tengo nada que darle. No porque lo esconda, sino porque <b>no lo tengo</b>.</p>
<p>Esto no es una promesa. Es una garantía arquitectónica.</p>
<h2>Qué significa como postura</h2>
<p>No quiero ganar dinero con los datos personales de la gente. No quiero saber de qué hablan. No quiero ser un intermediario al que se le pueda enviar una citación judicial.</p>
<p>Los ingresos vienen de la herramienta, no del contenido. Vendo el martillo, no lo que se construye con él.</p>
<h2>Los agentes de IA y la próxima frontera</h2>
<p>El mundo avanza hacia agentes de IA autónomos. Los agentes hablarán entre sí: negociarán, se delegarán tareas, intercambiarán datos.</p>
<p>La pregunta pasa a ser: ¿quién ve esas conversaciones?</p>
<p>La respuesta actual de la industria es la plataforma. OpenAI ve lo que los agentes hacen en OpenAI. Google ve lo que los agentes hacen en Google. El operador del orquestador lo ve todo.</p>
<p>Mi respuesta: <b>nadie</b>.</p>
<p>Si los agentes se comunican a través de una infraestructura ZKI, su correspondencia está cifrada de extremo a extremo. El operador de la plataforma solo ve el enrutamiento. El contenido de la negociación queda entre los agentes.</p>
<div class="tbl"><table>
<tr><th>Agente A</th><th style="width:30%">⇄ cifrado de extremo a extremo ⇄</th><th>Agente B</th></tr>
<tr><td>Nodo de Nevod — solo ve texto cifrado</td><td></td><td>Nodo de Nevod — solo ve texto cifrado</td></tr>
<tr><td>Operador — no ve nada</td><td></td><td>Operador — no ve nada</td></tr>
</table></div>
<p><i>«Opero un servicio que usan agentes de IA. No sé qué acordaron con tu agente».</i></p>
<p>No es eludir la responsabilidad. Es una arquitectura para un mundo en el que los agentes son actores independientes.</p>
<h2>Por qué importa ahora</h2>
<p>En 2025–2026:</p>
<ul><li>Los agentes de IA empiezan a actuar de forma autónoma</li><li>Agentes de distintas empresas empiezan a interactuar</li><li>Nadie ha decidido quién ve las negociaciones entre agentes</li><li>Nadie ha decidido quién responde de lo que «dijo» un agente</li></ul>
<p>ZKI responde:</p>
<ul><li>Las negociaciones están cifradas: el operador no las ve</li><li>La responsabilidad por los actos de un agente recae en quien lo ejecuta</li><li>La infraestructura de comunicación sigue siendo neutral, como una línea telefónica</li></ul>
<h2>Precedentes</h2>
<div class="tbl"><table>
<tr><th style="width:30%">Herramienta</th><th>Postura</th></tr>
<tr><td>Tor Project</td><td>«Construimos una herramienta de anonimato. No vemos el tráfico».</td></tr>
<tr><td>Signal Foundation</td><td>«Las claves están en los usuarios. No tenemos nada que entregar».</td></tr>
<tr><td>ProtonMail</td><td>«Cifrado de conocimiento cero. No podemos leer tu correo».</td></tr>
<tr><td>Proveedores de VPN</td><td>«Nosotros damos el túnel. El contenido no es nuestro».</td></tr>
<tr><td>Carteras de hardware</td><td>«Las claves están en el dispositivo. No tenemos copia».</td></tr>
</table></div>
<p>Todas estas posturas han superado el escrutinio legal en la mayoría de los países democráticos. ZKI es la misma postura, llevada al nivel de una filosofía de diseño.</p>
<h2>Qué estoy construyendo</h2>
<p><b>Nevod</b> es la primera implementación del principio ZKI como red completa. No es un producto. Es un protocolo.</p>
<p>Puede servir de base para:</p>
<ul><li>Mensajeros</li><li>Almacenamiento de archivos</li><li>Sistemas de votación</li><li>Interruptores de hombre muerto</li><li>Protocolos para agentes de IA</li><li>Infraestructura corporativa</li></ul>
<p>Un solo principio en todas partes: <b>el creador de la infraestructura está técnicamente separado de su contenido</b>.</p>
<p style="margin-top:2em"><i>Abril de 2026</i></p>
<p><b>Kolpakov Andrey</b></p>
<p class="note">© 2026. Al citar este manifiesto o hacer referencia a él, incluye un enlace a <a href="https://nevod.network">nevod.network</a>. Original en inglés: <a href="/manifesto/">nevod.network/manifesto</a>.</p>
</div></main>
"""

COMPARE = """
<main><div class="wrap">
<h1>Nevod y otros mensajeros</h1>
<p>La mayoría de los mensajeros modernos cifran los mensajes. La diferencia no está en si hay cifrado, sino en <b>qué queda en manos de la empresa</b>: servidores, base de datos de usuarios, números de teléfono, agenda, metadatos, y qué de todo eso se le puede exigir.</p>
<p class="note">Nevod aplica el principio de <a href="/es/manifesto/">Zero Knowledge Infrastructure</a>: el desarrollador está separado de los datos de los usuarios por la <b>arquitectura</b>, no solo por el cifrado. La información sobre otros mensajeros se basa en sus descripciones públicas a 2026 y puede cambiar.</p>
<div class="tbl"><table>
<tr><th style="width:24%"></th><th>Nevod</th><th>Signal</th><th>Telegram</th><th>WhatsApp</th></tr>
<tr><td>Quién puede técnicamente leer un chat normal</td><td>Solo los participantes</td><td>Solo los participantes</td><td>Chats normales y grupos: los servidores de Telegram (extremo a extremo solo en los «chats secretos» uno a uno)</td><td>Solo los participantes</td></tr>
<tr><td>Servidores centrales de la empresa</td><td>No: nodos independientes que cualquiera puede ejecutar</td><td>Sí</td><td>Sí</td><td>Sí, de Meta</td></tr>
<tr><td>Vinculado a un número de teléfono</td><td>No: la identidad es una clave</td><td>Sí (el número puede ocultarse tras un nombre de usuario)</td><td>Sí</td><td>Sí</td></tr>
<tr><td>Subida de la agenda</td><td>No: los contactos se añaden con tarjeta o QR</td><td>Descubrimiento privado de contactos</td><td>Sí, si se permite</td><td>Sí, si se permite</td></tr>
<tr><td>Base de datos de usuarios en la empresa</td><td>No hay una central: cada nodo solo conoce a sus usuarios</td><td>Mínima</td><td>Sí</td><td>Sí</td></tr>
<tr><td>Qué puede entregar la empresa ante una exigencia</td><td>El desarrollador no tiene nada que dar: ni claves, ni mensajes, ni base de datos</td><td>Según sus informes: la fecha de creación de la cuenta y de la última conexión</td><td>Según su política: en algunos casos, dirección IP y número de teléfono</td><td>Metadatos de la cuenta, según su política</td></tr>
<tr><td>Copias de seguridad de chats en la nube</td><td>No hay: las claves y el historial solo existen en el dispositivo (si pierdes el teléfono, pierdes el historial)</td><td>Opcionales; cifradas con una clave que solo tiene el usuario</td><td>No hacen falta: los chats normales ya se guardan en los servidores de Telegram</td><td>En iCloud / Google Drive; sin cifrado de extremo a extremo por defecto (hay que activarlo manualmente)</td></tr>
<tr><td>Punto único de fallo o bloqueo</td><td>No: los nodos son independientes</td><td>Sí</td><td>Sí</td><td>Sí</td></tr>
<tr><td>Funcionamiento sin internet dentro de una ciudad</td><td>Parte de la arquitectura (red urbana, Wi-Fi mesh, radio)</td><td>No</td><td>No</td><td>No</td></tr>
<tr><td>Modelo de negocio</td><td>Con la herramienta, no con los datos</td><td>Donaciones (sin ánimo de lucro)</td><td>Publicidad y Premium</td><td>Servicios empresariales de Meta</td></tr>
<tr><td>Código abierto</td><td>Aún no: cerrado hasta la versión de producción</td><td>Sí</td><td>Parcialmente (clientes)</td><td>No</td></tr>
</table></div>
<h2>Por qué «solo cifrado» no basta</h2>
<p>El cifrado de extremo a extremo protege el contenido de un mensaje en tránsito. Pero si una empresa opera todos los servidores, mantiene una base de cuentas por número de teléfono y ve quién habla con quién y cuándo, conserva el poder sobre el sistema: se la puede obligar, hackear o bloquear, y una actualización de la app puede cambiar las reglas.</p>
<p>ZKI plantea otra pregunta: <b>¿qué puede obtener, siquiera en teoría, el creador de la infraestructura?</b> En Nevod la respuesta está en la arquitectura: las claves nunca salen del dispositivo, no hay clave maestra ni copias de seguridad, no hay servidor central ni registro de personas por número de teléfono.</p>
<h2 id="low-load">Red distribuida de baja carga: una comparación</h2>
<p>Evaluamos las redes según seis rasgos de una red distribuida de baja carga: la carga de cada nodo está limitada por su propio círculo de personas, no por el tamaño de toda la red. Los rasgos salen de los propios principios de Nevod, así que la comparación le favorece de entrada.</p>
<ol>
<li>Círculo propio: la carga de un nodo crece con su círculo (familia, hogar, equipo), no con toda la red.</li>
<li>Hardware común: un ordenador doméstico, un miniservidor o un router; no hace falta un centro de datos.</li>
<li>Economía: primero texto y señales, lo pesado bajo demanda.</li>
<li>Tolerancia a retrasos: sin conexión, el mensaje espera y sale después, también por un canal lento.</li>
<li>Sin centro: ningún punto único de fallo, bloqueo o incautación.</li>
<li>Nodo ciego: el nodo solo transporta texto cifrado y no puede leerlo.</li>
</ol>
<p class="note">1: sí, ½: en parte, 0: no. Año: primera versión pública. Clase: LL-0, la carga del nodo está limitada por su círculo; LL-1, además tránsito ajeno limitado; LL-3, la carga crece con toda la red o depende de usuarios ajenos. Más: <a href="/es/publications/low-load-networks/">el artículo</a>.</p>
<div class="tbl"><table>
<tr><th>Red</th><th>Año</th><th>Círculo propio</th><th>Hardware común</th><th>Economía</th><th>Retrasos</th><th>Sin centro</th><th>Nodo ciego</th><th>Clase</th></tr>
<tr><td>Secure Scuttlebutt</td><td>2014</td><td>1</td><td>1</td><td>½</td><td>1</td><td>1</td><td>0</td><td>LL-0</td></tr>
<tr><td>Briar</td><td>2018</td><td>1</td><td>1</td><td>½</td><td>½</td><td>1</td><td>1</td><td>LL-0</td></tr>
<tr><td><b>Nevod</b></td><td>2026</td><td>1</td><td>1</td><td>½</td><td>½</td><td>1</td><td>1</td><td>LL-0</td></tr>
<tr><td>FidoNet</td><td>1984</td><td>1</td><td>1</td><td>1</td><td>1</td><td>0</td><td>0</td><td>LL-1</td></tr>
<tr><td>NNCP</td><td>2016</td><td>½</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>LL-1</td></tr>
<tr><td>Reticulum / LXMF</td><td>2016</td><td>½</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>LL-1</td></tr>
<tr><td>Meshtastic</td><td>2020</td><td>0</td><td>1</td><td>1</td><td>½</td><td>1</td><td>½</td><td>LL-1</td></tr>
<tr><td>Tor</td><td>2002</td><td>0</td><td>½</td><td>0</td><td>0</td><td>1</td><td>1</td><td>LL-3</td></tr>
<tr><td>WhatsApp</td><td>2009</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>½</td><td>LL-3</td></tr>
<tr><td>Telegram</td><td>2013</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>LL-3</td></tr>
<tr><td>Matrix</td><td>2014</td><td>0</td><td>½</td><td>0</td><td>0</td><td>½</td><td>½</td><td>LL-3</td></tr>
<tr><td>Signal</td><td>2014</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>½</td><td>LL-3</td></tr>
<tr><td>Mastodon</td><td>2016</td><td>0</td><td>½</td><td>0</td><td>0</td><td>½</td><td>0</td><td>LL-3</td></tr>
<tr><td>Nostr</td><td>2020</td><td>0</td><td>½</td><td>0</td><td>0</td><td>1</td><td>½</td><td>LL-3</td></tr>
<tr><td>Session</td><td>2020</td><td>0</td><td>½</td><td>0</td><td>½</td><td>1</td><td>1</td><td>LL-3</td></tr>
</table></div>
<p>Signal y WhatsApp reciben ½ por ceguera: el contenido está cifrado de extremo a extremo, pero la empresa ve los metadatos y gestiona los servidores. En Reticulum y NNCP, los nodos intermedios transportan y almacenan paquetes ajenos. Nevod todavía envía los archivos multimedia completos, guarda lo no entregado durante 72 horas y solo funciona por internet.</p>
<h3>La prueba de la práctica</h3>
<div class="tbl"><table>
<tr><th>Red</th><th>Año</th><th>Para gente común</th><th>Madurez</th><th>Auditoría independiente</th></tr>
<tr><td>Reticulum / LXMF</td><td>2016</td><td>no, para entusiastas</td><td>comunidad activa</td><td>no</td></tr>
<tr><td>NNCP</td><td>2016</td><td>no, herramienta de línea de comandos</td><td>de nicho</td><td>no</td></tr>
<tr><td><b>Nevod</b></td><td>2026</td><td>sí: iPhone/iPad, mensajes, multimedia, llamadas</td><td>en pruebas, aún sin usuarios reales</td><td>no</td></tr>
<tr><td>Briar</td><td>2018</td><td>sí, pero sin llamadas; Android y escritorio</td><td>maduro</td><td>sí (Cure53, 2017)</td></tr>
<tr><td>Signal</td><td>2014</td><td>sí</td><td>muy maduro</td><td>sí, varias veces</td></tr>
</table></div>
<p>Por el rasgo principal, Nevod pertenece a la clase LL-0 junto a Briar y Secure Scuttlebutt; Reticulum y NNCP, cercanas en los demás rasgos, pertenecen a LL-1. La diferencia de Nevod está en otra parte: de estas redes es el único pensado como mensajería completa para gente común, con multimedia, llamadas y una app para iPhone. Pero es joven: todavía no tiene usuarios reales ni auditoría independiente, y solo funciona en iOS. El camino a seis de seis: multimedia bajo demanda y entrega sin internet por canales lentos.</p>
<h2>Lo que reconocemos</h2>
<ul>
<li>Un nodo técnicamente solo procesa datos de entrega —qué paquete cifrado va a quién— y nunca ve el contenido. Nadie te impide ejecutar tu propio nodo: entonces incluso esos datos de entrega se quedan contigo.</li>
<li>El protocolo de Signal es abierto y ha sido ampliamente auditado; lo reconocemos como una fortaleza. El código de Nevod es cerrado por ahora; está previsto abrirlo.</li>
</ul>
</div></main>
"""

SECURITY = """
<main><div class="wrap">
<h1>Seguridad y cifrado</h1>
<p class="note">El cifrado es solo una parte de la protección. La base de Nevod es la arquitectura de <a href="/es/manifesto/">Zero Knowledge Infrastructure</a>, en la que el desarrollador no tiene acceso a las claves ni a los datos de los usuarios.</p>
<h2>Cómo se protegen tus mensajes</h2>
<p>Nevod usa cifrado de extremo a extremo: un mensaje se cifra en tu dispositivo y solo se descifra en el del destinatario. El nodo que lo transporta solo ve datos cifrados y la información de servicio necesaria para la entrega, nunca el contenido.</p>
<div class="tbl"><table>
<tr><th style="width:38%">Qué</th><th>Cómo</th></tr>
<tr><td>Cifrado de mensajes</td><td>CryptoKit, la biblioteca criptográfica del sistema de Apple: intercambio de claves X25519, SHA-256, cifrado ChaCha20-Poly1305</td></tr>
<tr><td>Firmas</td><td>CryptoKit: Ed25519</td></tr>
<tr><td>Prueba de identidad al conectarse a un nodo</td><td>Protocolo de conocimiento cero de Schnorr sobre CryptoKit (Curve25519, SHA-256/512) y una única operación aritmética modular implementada en el propio Nevod</td></tr>
</table></div>
<p>El remitente crea una nueva clave de un solo uso para cada mensaje. La clave del destinatario es de larga duración: si se roba del dispositivo del destinatario, también podrían descifrarse mensajes interceptados antes y dirigidos a él. Por eso es importante proteger el propio dispositivo: un código de acceso y un iOS actualizado.</p>
<p>El protocolo de Schnorr permite demostrar a un nodo que tienes tu clave sin enviarla ni revelarla.</p>
<h2>Si pierdes el teléfono</h2>
<p>Tus claves, contactos e historial de mensajes se guardan solo en tu dispositivo. No están en las copias de seguridad de iCloud ni del ordenador, ni en los nodos, ni en manos del desarrollador. Por eso, si el teléfono se pierde, se rompe o se restablece, no se pueden recuperar. Eliminar la app también borra el historial.</p>
<p>Todavía no es posible transferirlos a un dispositivo nuevo. En un teléfono nuevo crearás una identidad nueva, y tus contactos necesitarán tu nueva tarjeta. Es una consecuencia de la arquitectura: una copia que permitiera recuperar tus conversaciones sería también una copia a la que alguien podría acceder.</p>
<h2>Tu nodo, tus reglas</h2>
<p>El desarrollador no ve nada. Un nodo solo procesa aquello sin lo cual la entrega no funciona: identificadores de participantes, nombres elegidos, tokens de notificación y qué paquete cifrado va a quién. Un nodo nunca ve el contenido de mensajes, fotos, mensajes de voz ni llamadas.</p>
<p>Nadie te impide crear tu propio nodo: para ti, tu familia, una organización o una comunidad. Entonces incluso los datos de entrega se quedan contigo. <a href="/es/node/">Cómo ejecutar tu propio nodo →</a></p>
<h2>Control de exportaciones y App Store</h2>
<p>Al publicar en App Store, el desarrollador declara si la app usa cifrado sujeto a control de exportaciones (EAR de EE. UU., Categoría 5, Parte 2). Nevod declara que no, y este es el motivo:</p>
<ul>
<li><b>Todo lo que oculta el contenido de los mensajes es criptografía del sistema de Apple (CryptoKit).</b> Las apps que solo usan el cifrado integrado en el sistema operativo de Apple se acogen a una exención y no necesitan documentación de exportación.</li>
<li><b>La implementación propia de Nevod —una única operación aritmética en el protocolo de Schnorr— solo sirve para demostrar la identidad.</b> El control de exportaciones cubre la criptografía destinada a la confidencialidad. La criptografía usada solo para autenticación, firmas e integridad queda excluida.</li>
</ul>
<p>Por eso Nevod no necesita documentación de exportación, incluida la distribución en Francia.</p>
<p><i>Esta es nuestra interpretación de las normas vigentes, no un dictamen jurídico.</i></p>
</div></main>
"""

CITIES = """
<section class="hero"><div class="wrap">
<div class="eyebrow">Para ciudades</div>
<h1>Comunicación para una ciudad sin internet ni centros de datos</h1>
<p class="lead">Toda ciudad moderna depende de centros de datos y enlaces troncales. La arquitectura de Nevod puede transmitir mensajes cifrados por cualquier canal disponible, así que sobre ella se puede construir una red urbana de comunicación de reserva.</p>
</div></section>
<main><div class="wrap">
<h2>Cuatro capas de comunicación</h2>
<div class="tbl"><table>
<tr><th style="width:24%">Capa</th><th>Qué usa</th><th style="width:16%">Alcance</th><th style="width:20%">Qué transporta</th></tr>
<tr><td>1. Nodos urbanos</td><td>Redes de proveedores sin salida a internet</td><td>Toda la ciudad</td><td>Todo dentro de la ciudad</td></tr>
<tr><td>2. Wi-Fi mesh</td><td>Routers corrientes en «puntos de resiliencia»: refugios, escuelas, centros de asistencia</td><td>Manzana–barrio</td><td>Todo, llamadas incluidas</td></tr>
<tr><td>3. Enlaces de radio</td><td>Radiomódems direccionales con línea de visión</td><td>10–20 km</td><td>Todo, llamadas incluidas</td></tr>
<tr><td>4. LoRa</td><td>Módulos de radio de bajo coste</td><td>1–10+ km</td><td>Solo texto breve</td></tr>
</table></div>
<p>Para las personas es el mismo Nevod: la app elige por sí misma el canal disponible.</p>
<h2>Un punto de resiliencia</h2>
<p>Un kit de equipos económicos y comerciales: varios routers con software abierto, un pequeño servidor de nodo, alimentación de respaldo y, si hace falta, un enlace de radio a otros barrios y un módulo LoRa para textos breves. No hay que inventar nada.</p>
<h2>Cómo empezar</h2>
<p>Ofrecemos a las ciudades un piloto en un solo barrio: varios puntos de resiliencia conectados entre sí, probados para mensajes y llamadas sin ningún internet. El resultado es un informe y un plan de ampliación. Contacto: <a href="mailto:support@nevod.network">support@nevod.network</a>.</p>
<p class="note">Cualquier transmisor puede localizarse por radiogoniometría, así que los emplazamientos se eligen con cuidado, y el contenido de los mensajes está cifrado de extremo a extremo en todas las capas. La arquitectura ZKI también se aplica aquí: el operador de la red urbana no tiene acceso al contenido.</p>
</div></main>
"""

DOWNLOAD = """
<main><div class="wrap">
<h1>Descargar Nevod</h1>
<div class="grid">
<div class="card"><h3>📱 iPhone y iPad</h3><p>Ahora en prueba cerrada mediante TestFlight; la publicación en App Store está en preparación. Para unirte a la prueba, escribe a <a href="mailto:support@nevod.network">support@nevod.network</a>.</p></div>
<div class="card"><h3>🤖 Android</h3><p>La app está en desarrollo. Lo anunciaremos aquí cuando esté lista para pruebas.</p></div>
<div class="card"><h3>🖥️ Nodo de la red</h3><p>Un nodo de Nevod funciona con Docker en un servidor o en un ordenador corriente. Consulta <a href="/es/node/">Tu propio nodo</a>.</p></div>
</div>
</div></main>
"""

NODE = """
<main><div class="wrap">
<h1>Ejecuta tu propio nodo de Nevod</h1>
<p>Un nodo es un pequeño servidor a través del cual los teléfonos intercambian mensajes y llamadas. Solo ve datos cifrados. Una organización, una comunidad, una escuela o una familia puede ejecutar su propio nodo; precisamente por eso la red no tiene un punto central controlado por el desarrollador.</p>
<h2>Qué necesitas</h2>
<ul>
<li>Un ordenador o servidor con Linux o Windows y Docker instalado</li>
<li>Al menos 1 GB de RAM</li>
<li>Para acceso desde internet, una dirección pública o un dominio; para una red urbana o Wi-Fi basta una dirección local</li>
</ul>
<h2>Cómo funciona</h2>
<ol>
<li>El nodo se ejecuta en Docker y tiene un panel de administración web.</li>
<li>En el panel defines el nombre del nodo y el modo de admisión (abierto, por invitación o con aprobación del administrador) y, si quieres, conectas el nodo a la red Nevod.</li>
<li>Los teléfonos se conectan al nodo por su dirección o con un código QR de invitación.</li>
</ol>
<p class="note">Se está preparando una versión pública del software del nodo. Por ahora el acceso se concede a petición en <a href="mailto:support@nevod.network">support@nevod.network</a>. También está en desarrollo la instalación de un nodo con ayuda de un asistente de IA.</p>
</div></main>
"""

ABOUT = """
<main><div class="wrap">
<h1>Sobre el proyecto</h1>
<p>Nevod es la primera implementación del principio de <a href="/es/manifesto/">Zero Knowledge Infrastructure</a>: una infraestructura de comunicación cuyo creador está técnicamente separado de su contenido. El proyecto no depende de un solo servidor, un solo proveedor ni un solo país.</p>
<h2>Autor</h2>
<p><b>Kolpakov Andrey</b> — autor del manifiesto ZKI y desarrollador de Nevod.</p>
<!--BIO-->
<h2>Contacto</h2>
<ul>
<li>Preguntas generales y soporte: <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Denunciar abusos: <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Privacidad y datos: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
</div></main>
"""

SUPPORT = """
<main><div class="wrap">
<h1>Soporte</h1>
<p class="note"><b>Importante.</b> La administración de Nevod responde solo dentro de la app Nevod, desde la cuenta oficial <b>administrator</b> con la insignia ✓. Nunca respondemos por correo electrónico y nunca pedimos contraseñas, claves ni códigos. Si la «administración» te contacta por otra vía, es un fraude.</p>
<h2>Cómo contactarnos</h2>
<ul>
<li>Preguntas y ayuda: <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Denunciar a un usuario o un contenido: en la app, mantén pulsado un mensaje → «Denunciar», o Ajustes del chat → «Denunciar». También: <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Privacidad y datos: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
<h2>Bloquear a un usuario</h2>
<p>Ajustes del chat → «Bloquear». Un usuario bloqueado no puede enviarte mensajes ni llamarte; puedes desbloquearlo en el mismo lugar o en Perfil → Bloqueados.</p>
<h2>Eliminar la cuenta</h2>
<p>Perfil → «Restablecer identidad». Elimina de forma permanente tu identidad, tus contactos y tus mensajes del dispositivo y tu registro en el nodo. Las personas con las que chateabas verán que la identidad ha sido eliminada.</p>
</div></main>
"""

PRIVACY = """
<main class="legal"><div class="wrap">
<h1>Política de privacidad</h1>
<p>Versión del 17 de octubre de 2026. Nevod es desarrollado por Kolpakov Andrey. Preguntas sobre datos: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a>.</p>
<h2>1. Lo esencial</h2>
<p>Nevod está construido según el principio de Zero Knowledge Infrastructure. El contenido de tus mensajes, fotos, vídeos, mensajes de voz, archivos y llamadas está cifrado de extremo a extremo, y las claves nunca salen de tu dispositivo. Ni los nodos de la red ni el desarrollador pueden leer el contenido. La única excepción es lo que tú mismo escribes a los bots de IA; consulta la sección 5.</p>
<h2>2. Qué se guarda en tu dispositivo</h2>
<p>Tu identidad criptográfica (claves en el almacenamiento seguro de iOS), tus contactos, tu historial de mensajes y multimedia, tus ajustes y un registro técnico para diagnóstico. El registro no sale del dispositivo a menos que lo envíes tú.</p>
<p>Estos datos no se incluyen en las copias de seguridad de iCloud ni del ordenador y no se transfieren a otros dispositivos. Si el dispositivo se pierde o se restablece, o se elimina la app, el historial no se puede recuperar: ni los nodos ni el desarrollador tienen una copia.</p>
<h2>3. Qué procesa un nodo</h2>
<ul>
<li>El identificador de tu identidad (cell ID) y tus claves públicas.</li>
<li>El nombre visible que elijas.</li>
<li>Tokens del dispositivo para notificaciones push y llamadas.</li>
<li>Mensajes cifrados hasta su entrega: los mensajes no entregados se eliminan a las 72 horas.</li>
<li>Tus ajustes de notificaciones y tu lista de usuarios bloqueados.</li>
<li>Metadatos de entrega (quién envía un paquete a quién y cuándo) y registros de diagnóstico conservados durante un tiempo limitado.</li>
<li>Tus mensajes a la cuenta administrator (quejas y preguntas enviadas desde la app). El operador del nodo los lee para poder responder: van dirigidos a él. Tus conversaciones con otras personas siguen siendo inaccesibles para el operador.</li>
</ul>
<p>Los nodos pueden pertenecer a distintos operadores independientes. El operador del nodo al que te conectas procesa estos datos para el funcionamiento de la red.</p>
<h2>4. Notificaciones</h2>
<p>Las notificaciones en iPhone se entregan a través del servicio Apple Push Notification. Una notificación lleva el nombre del remitente y el texto genérico «Nuevo mensaje», nunca el contenido del mensaje.</p>
<h2>5. Bots de IA</h2>
<p>Un nodo puede ofrecer bots de IA, por ejemplo un asistente o un traductor. Un bot así responde a través del proveedor de IA que elijas — Anthropic (Claude), OpenAI (ChatGPT) o Google (Gemini) — con tu propia clave de API. Nevod no vende acceso a IA ni tiene claves propias. Puedes usar Nevod sin bots.</p>
<ul>
<li><b>Tu clave</b> se guarda solo en tu dispositivo, en el almacenamiento seguro de iOS, y no pasa a otros dispositivos. Viaja al bot cifrada de extremo a extremo, junto con cada mensaje. El bot la usa para esa única solicitud y no la guarda.</li>
<li><b>Tus mensajes a un bot.</b> Un bot es un participante independiente de la red, gestionado por el operador del nodo donde está publicado. Por el camino, los mensajes que le envías van cifrados de extremo a extremo como todos los demás; el bot los descifra para responder y pasa el texto al proveedor que elegiste. Escribe a un bot solo lo que estés dispuesto a compartir con ese proveedor.</li>
<li><b>Qué conserva el bot:</b> solo los últimos mensajes de la conversación, en memoria, para responder con contexto; desaparecen cuando el bot se reinicia. El registro del bot anota que hubo una solicitud, su proveedor y su longitud — nunca el texto ni la clave.</li>
<li><b>El proveedor</b> recibe tus mensajes, la parte reciente de la conversación y tu clave, y los trata según sus propias condiciones y política de privacidad (<a href="https://www.anthropic.com/legal/privacy">Anthropic</a>, <a href="https://openai.com/policies/privacy-policy">OpenAI</a>, <a href="https://policies.google.com/privacy">Google</a>). Las solicitudes le llegan desde el servidor del bot, no desde tu dispositivo.</li>
<li><b>Consentimiento.</b> Antes de añadir una clave, la app te pide aceptar que tus mensajes a los bots se envíen a ese proveedor. Para retirarlo: Perfil → Seguridad → Claves de IA → elimina la clave. «Restablecer identidad» también elimina todas las claves.</li>
<li>Los bots solo reciben texto: nunca se les pasan fotos, archivos, mensajes de voz ni llamadas.</li>
</ul>
<h2>6. Terceros</h2>
<p>No vendemos datos ni los usamos para publicidad o seguimiento. Usamos: Apple (notificaciones, distribución de la app), alojamiento de nodos y Cloudflare (DNS y correo del dominio). Si añades una clave de IA: el proveedor que elegiste, para tus mensajes a los bots (sección 5).</p>
<h2>7. Eliminación</h2>
<p>Perfil → «Restablecer identidad» elimina tus datos del dispositivo y tu registro del nodo.</p>
<h2>8. Menores</h2>
<p>Nevod no está dirigido a menores por debajo de la edad a la que, en tu país, se puede consentir por uno mismo el tratamiento de datos.</p>
<h2>9. Cambios</h2>
<p>Anunciaremos los cambios importantes de esta política en esta página y en la app.</p>
</div></main>
"""

TERMS = """
<main class="legal"><div class="wrap">
<h1>Condiciones de uso</h1>
<p>Versión del 28 de septiembre de 2026. Al usar Nevod aceptas estas condiciones.</p>
<h2>1. Tolerancia cero con los abusos</h2>
<p>Está prohibido enviar o publicar contenido ilegal, acosador o amenazante, hostigar a otras personas, difundir spam o fraudes, y suplantar a otros, incluida la administración de Nevod. Quien incumpla las normas será bloqueado.</p>
<h2>2. Denuncias y bloqueo</h2>
<p>Puedes bloquear y denunciar a cualquier usuario en la app o en <a href="mailto:abuse@nevod.network">abuse@nevod.network</a>. Revisamos las denuncias y actuamos en consecuencia.</p>
<h2>3. Cuentas oficiales</h2>
<p>La administración responde solo en la app, desde la cuenta administrator con la insignia ✓ —nunca por correo electrónico— y nunca pide contraseñas, claves ni códigos.</p>
<h2>4. Nodos</h2>
<p>La red está formada por nodos que pueden gestionar operadores independientes. El operador de un nodo es responsable de gestionarlo conforme a las leyes de su país.</p>
<h2>5. Sin garantías</h2>
<p>Nevod se ofrece «tal cual». Hacemos todo lo posible para que la comunicación sea fiable, pero no garantizamos la entrega ininterrumpida de los mensajes.</p>
<h2>6. Contacto</h2>
<p><a href="mailto:support@nevod.network">support@nevod.network</a></p>
</div></main>
"""

PAGES = {
    "index": ("Nevod", "Nevod, la primera implementación de Zero Knowledge Infrastructure: un mensajero cuyo desarrollador no tiene acceso técnico a los datos de los usuarios.", INDEX),
    "manifesto": ("Manifiesto de Zero Knowledge Infrastructure", "El manifiesto ZKI, base del desarrollo de Nevod. Autor: Kolpakov Andrey.", MANIFESTO),
    "compare": ("Comparación", "Nevod frente a Signal, Telegram y WhatsApp: por qué el cifrado por sí solo no es ZKI.", COMPARE),
    "security": ("Seguridad y cifrado", "Cómo cifra Nevod los mensajes, qué procesa un nodo y por qué no hace falta documentación de exportación.", SECURITY),
    "cities": ("Para ciudades", "Una red urbana de comunicación de reserva basada en Nevod, sin internet ni centros de datos.", CITIES),
    "download": ("Descargar", "Nevod para iPhone, Android y el nodo de la red.", DOWNLOAD),
    "node": ("Tu propio nodo", "Cómo ejecutar tu propio nodo de la red Nevod.", NODE),
    "about": ("Sobre el proyecto", "Quién está detrás de Nevod y cómo contactarnos.", ABOUT),
    "support": ("Soporte", "Soporte, denuncias, bloqueo y eliminación de cuenta en Nevod.", SUPPORT),
    "privacy": ("Política de privacidad", "Qué datos procesa Nevod y cómo se protegen.", PRIVACY),
    "terms": ("Condiciones de uso", "Condiciones de uso de Nevod.", TERMS),
}
