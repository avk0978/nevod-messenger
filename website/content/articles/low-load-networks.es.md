# Redes distribuidas de datos de baja carga: concepto, clasificación y análisis comparativo

**Autor del concepto:** Kolpakov Andrey

**Versión:** 30 de septiembre de 2026

**Materiales relacionados:** [Manifiesto Zero Knowledge Infrastructure](/es/manifesto/), [comparación de redes](/es/compare/#low-load).

---

## Resumen

El artículo introduce el concepto de *red distribuida de datos de baja carga*: una red en la que
la carga de cada nodo (tráfico, almacenamiento, estado de servicio) está limitada por el círculo
de participantes de ese nodo y no crece a medida que crece la red en su conjunto. Se muestra que
las clasificaciones de carga de la teoría de las comunicaciones (factor de utilización, erlangs,
los puntos de «rodilla» (knee) y «acantilado» (cliff) en la curva de caudal frente a carga, clases de calidad de servicio) describen el *estado* de
una red en un momento dado y no una propiedad de su arquitectura, por lo que no distinguen redes
según este rasgo. Se proponen seis rasgos de una red de baja carga y una clasificación LL-0…LL-3
según la asintótica de la carga por nodo. Se comparan quince redes, desde FidoNet (1984) hasta
Nevod (2026), y se señalan sus predecesores en la literatura: redes de amigo a amigo (F2F), redes
tolerantes a retrasos (DTN), tablas hash distribuidas, software local-first y redes comunitarias
(community networks).

**Palabras clave:** redes distribuidas, descentralización, carga por nodo, escalabilidad, F2F,
DTN, redes entre pares, mensajería, Zero Knowledge Infrastructure.

---

## 1. Introducción

La mayoría de los servicios de mensajería actuales son centralizados: toda la red la atienden los
servidores de una sola empresa, y la carga de esos servidores crece con el número de usuarios.
Las alternativas descentralizadas (redes federadas, superposiciones entre pares, redes de anonimato) distribuyen la *propiedad* de la infraestructura pero, como se muestra más abajo, por
lo general no distribuyen la *carga*: un servidor de federación o un nodo de superposición
transporta tráfico, historial y estado de servicio generados por usuarios ajenos, y su carga
vuelve a crecer con el tamaño de la red o de su parte popular.

El objetivo del trabajo es delimitar la clase de redes en las que la carga de un nodo depende solo de su propio círculo: los usuarios y agentes de software (bots, agentes de IA, servicios) para los que es el nodo de origen; definirla, proponer una clasificación medible y comparar las redes existentes según este rasgo.

## 2. La carga en las redes de datos: conceptos existentes

### 2.1 Factor de utilización

En la teoría de colas, la carga de un canal o nodo se caracteriza por el factor de utilización
ρ = λ/μ, el cociente entre la tasa de llegadas y la tasa de servicio [1]. Cuando ρ → 1, la
longitud de la cola y el retardo crecen sin límite; con ρ > 1 el sistema está sobrecargado. En la
práctica se usan niveles aproximados: utilización baja (ρ < ~0,3), moderada (0,3–0,7), alta
(0,7–0,9), saturación y sobrecarga; los operadores suelen dimensionar los enlaces con margen hasta
~70–80 % en la hora punta. Estos umbrales son pautas de ingeniería, no un estándar único.

### 2.2 Teletráfico: erlangs y hora cargada

En telefonía, la intensidad de tráfico se mide en erlangs (1 Erl es un canal ocupado de forma
continua) [2]; el dimensionamiento se hace con la hora cargada; se distingue tráfico ofrecido,
cursado y perdido, y el grado de servicio se fija como una probabilidad de bloqueo admisible
(fórmulas de Erlang B y C) [1, 2].

### 2.3 Cómo reacciona una red al aumento de carga: la «rodilla» y el «acantilado»

Jain, Ramakrishnan y Chiu [3] describieron tres regiones de funcionamiento de una red: antes de la
«rodilla», el caudal crece con la carga y el retardo es bajo; entre la «rodilla» y el
«acantilado», el caudal apenas crece y el retardo aumenta con rapidez; más allá del «acantilado»
llegan la congestión y el colapso. En la «rodilla», el cociente entre caudal y retardo (la «potencia» de la red) alcanza su máximo; en esta distinción se basan la evitación de la congestión (congestion avoidance: mantener el funcionamiento cerca de la «rodilla») y el control de la congestión (congestion control: impedir la caída por el «acantilado»). El control de congestión de TCP se basa en estas ideas [4].

### 2.4 Clases de tráfico y de calidad de servicio

La arquitectura de servicios diferenciados DiffServ [5] introduce comportamientos de reenvío
(reenvío acelerado EF, reenvío asegurado AF, mejor esfuerzo BE); la Recomendación UIT-T Y.1541 [6]
define clases de calidad 0–5 para redes IP según retardo, jitter y pérdidas. Son clasificaciones
de *requisitos* de entrega, no de carga.

### 2.5 Regímenes de carga: de la subcarga al colapso

Los regímenes de funcionamiento de una red según su carga están descritos en normas y trabajos
clásicos:

| Régimen | Dónde se define | Significado |
|---|---|---|
| Subcarga (underutilization) | descriptivo, no definido en normas | los enlaces están notablemente ociosos; a menudo es una reserva de capacidad deliberada (overprovisioning) |
| Carga normal | UIT-T E.500 [36] | periodos de actividad frecuentes en los que deben cumplirse las expectativas de los usuarios; para ella se fijan los objetivos de grado de servicio |
| Carga alta | UIT-T E.500 [36] | periodos pico poco frecuentes: las expectativas pueden no cumplirse, pero el rendimiento debe ser suficiente para que la congestión no se extienda por la red |
| Sobrecarga | UIT-T E.412 [37]; contemplada en las normas GOST sobre redes de comunicación [39] | el tráfico supera la capacidad de la red; entran en juego medidas de gestión: control automático de congestión, reserva de circuitos, reencaminamiento |
| Colapso por congestión (congestion collapse) | RFC 896, J. Nagle, 1984 [38] | cada paquete se envía muchas veces y el caudal útil cae casi a cero; se observó por primera vez en octubre de 1986, cuando la troncal de NSFnet cayó de 32 kbit/s a 40 bit/s |

No existe un término establecido para una red «plenamente cargada»; el nivel para el que se
dimensiona una red corresponde a la «carga normal» de E.500.

Todos estos regímenes son **estados** de una red en un momento dado: la misma red está subcargada
por la mañana, en carga normal por la tarde y sobrecargada durante una avería. El eje de regímenes
y el eje de clases arquitectónicas que se introduce más abajo son independientes: una red de clase
LL-0 también puede sobrecargarse, por ejemplo si un nodo funciona sobre un enlace débil.

### 2.6 Escalado de la carga por nodo

En la literatura sobre sistemas distribuidos el coste de un nodo se evalúa de forma asintótica en
función del número de participantes N: difundir a todos los nodos cuesta O(N) por mensaje; las
tablas hash distribuidas (Chord [7], Kademlia [8]) cuestan O(log N) en encaminamiento y tabla de
vecinos. También aparece la afirmación de que en los sistemas entre pares la carga máxima por nodo
no crece con el número de nodos, porque los nodos nuevos aportan más recursos de los que consumen
[9], pero se trata de un *equilibrio estadístico* de una carga compuesta por peticiones ajenas.

### 2.7 Conclusión

Las clasificaciones 2.1–2.5 responden a la pregunta «qué tan cargada está la red *ahora*»; según
ellas, la misma red está unas veces poco y otras muy cargada. La expresión rusa «red poco cargada» (малонагруженная сеть) se usa en la práctica justo en este sentido descriptivo (una red o
máquina con baja utilización) y no es un término que designe una clase de arquitectura. En la
telefonía por cable la palabra «carga» tiene incluso un tercer significado: la «línea cargada» con
bobinas de inductancia (pupinización). Solo el eje 2.6 se refiere a una *propiedad de la
arquitectura*, y no existe una clasificación estándar de redes según él.

## 3. Redes distribuidas: panorama de enfoques

**Servicios centralizados** (WhatsApp, 2009; Telegram, 2013; Signal, 2014 [10]): el cifrado de
extremo a extremo del contenido puede ser sólido, pero los servidores, las cuentas y los metadatos
están en manos de una sola organización; la carga de los servidores crece con toda la audiencia.

**Redes federadas**: correo electrónico, Matrix (2014) [11], ActivityPub/Mastodon (2016;
Recomendación W3C 2018) [12]. La propiedad se reparte entre servidores, pero la carga de un
servidor crece con sus conexiones externas: en Matrix el historial de una sala grande se replica
en cada servidor participante; en ActivityPub la distribución crece con el número de seguidores.

**Superposiciones entre pares y tablas hash distribuidas**: Freenet (2001) [13], Chord [7],
Kademlia [8]. Los nodos son iguales y la carga es O(log N), pero un nodo almacena y encamina datos
de desconocidos.

**Redes de amigo a amigo (F2F).** El término lo propuso D. Bricklin en 2000 [14]: un nodo solo se
conecta con los nodos de sus conocidos. Ejemplos: Turtle (Popescu, Crispo, Tanenbaum, 2004) [15],
OneSwarm [16], el modo «darknet» de Freenet, RetroShare, GNUnet; también el almacenamiento en nodos
de confianza [17]. El número de conexiones de un nodo está limitado por su número de amigos
[18, 19], pero los mensajes recorren cadenas de amigos a través de nodos no interesados, y el
encaminamiento en estas redes sigue siendo un problema difícil [18, 19, 20]. **Las redes F2F son
el predecesor más cercano del concepto propuesto**: fueron las primeras en limitar un nodo a su
círculo de conocidos, pero por número de conexiones, no por carga.

**Redes superpuestas de anonimato** (enrutamiento cebolla): desarrollo de las redes de mezcla de D. Chaum (1981) [40] y del enrutamiento cebolla de D. Goldschlag, M. Reed y P. Syverson (1996) [41]; sus implementaciones son Tor (2002–2004) [21] y Session (2020) [22]. Los nodos de retransmisión, mantenidos por voluntarios u operadores, llevan tránsito ajeno en proporción a su ancho de banda.

**Redes tolerantes a retrasos (DTN)**: la arquitectura de Fall (2003) [23], RFC 4838 [24], Bundle
Protocol v7, RFC 9171 [25]: «almacenar y reenviar» ante cortes de enlace. Una implementación
histórica del mismo principio es FidoNet (1984) [26]; una actual, NNCP (2016) [27].

**Pilas para cualquier medio y redes de radio**: Reticulum (protocolo publicado en 2016) y la
mensajería LXMF [28]: funcionamiento desde unos pocos bits por segundo (LoRa, radio por paquetes)
hasta internet, con cifrado por defecto; Meshtastic (2020) [29]: mensajes de texto mediante
módulos de radio LoRa.

**Redes comunitarias** (community networks): Freifunk, Guifi.net [30]: redes que crean y mantienen los propios usuarios.

**Software local-first** [31] y **Secure Scuttlebutt** (2014) [32]: los datos viven con el usuario;
en SSB un nodo guarda los canales de sus amigos y de los amigos de sus amigos, y la sincronización
ocurre cuando los nodos se encuentran.

**Relés**: Nostr (2020) [33]: servidores de retransmisión simples, de los cuales los populares
soportan la carga de toda la audiencia.

## 4. El concepto de red distribuida de baja carga

### 4.1 Definición

**Una red distribuida de datos de baja carga** es una red en la que cada nodo atiende a un círculo
de participantes pequeño y naturalmente limitado y transporta sobre todo su propio tráfico. Los
nodos son iguales y funcionan en hardware común. La red transmite solo lo necesario, tolera
retrasos y cortes de enlace y no tiene un centro cuyo apagado o incautación detendría su
funcionamiento.

El concepto se refiere al *diseño* de una red, no a su carga en un momento dado (apartados 2.5,
2.7).

### 4.2 Rasgos

1. **Círculo propio**: la carga de un nodo crece con su círculo, las personas y los agentes de software a los que atiende, no con el tamaño de toda la red. El rasgo principal.
2. **Hardware común**: un ordenador doméstico, un miniservidor o un router; no hace falta un centro
   de datos.
3. **Economía de transmisión**: primero texto y señales, los datos voluminosos bajo demanda.
4. **Tolerancia a retrasos**: sin conexión, el mensaje espera y se transmite después, también por
   un canal lento.
5. **Sin centro**: ningún punto único de fallo, bloqueo o incautación.
6. **Ceguera del nodo**: el nodo solo transporta texto cifrado y no puede leerlo (el principio
   Zero Knowledge Infrastructure).

### 4.3 En qué se diferencia de sus predecesores

| Concepto | Qué se limita | En qué se diferencia |
|---|---|---|
| F2F [14–20] | el número de conexiones del nodo, por su círculo de conocidos | el tránsito por cadenas de conocidos se mantiene; la carga no está limitada |
| DHT [7, 8] | el crecimiento de la carga, por un logaritmo | el nodo transporta datos de desconocidos |
| DTN [23–25] | nada sobre la carga | trata de retrasos y cortes, no del reparto de carga |
| Local-first [31] | dónde se guardan los datos: con el usuario | trata de la propiedad de los datos, no de la red |
| **Red de baja carga** | **toda la carga del nodo, por su círculo** | combinación de los rasgos 1–6; el rasgo 1 es el determinante |

## 5. Clasificación: clases LL

**La clase de carga de un nodo** la determina la que crece más rápido de sus tres componentes: tráfico transportado, datos almacenados, estado de servicio mantenido. N es el número de participantes de la red; k, el tamaño del círculo del nodo: el número de sus usuarios y agentes de software. La notación O(x) («O grande de x»; introducida por P. Bachmann en 1894 [42] y difundida por E. Landau en 1909 [43]) significa que una magnitud no crece más rápido que x multiplicado por una constante; para la clase LL-0 la estimación de la carga no contiene N, solo k.

| Clase | Carga del nodo | Definición |
|---|---|---|
| **LL-0** | O(k) | el nodo transporta, guarda y recuerda solo lo relativo a su círculo; no hay tránsito ajeno |
| **LL-1** | O(k) + ajeno limitado | además, tránsito o almacenamiento para otros limitado con independencia de N (límite de saltos, cuotas, vecinos elegidos por el propio nodo) |
| **LL-2** | O(log N) | la carga crece despacio (tablas hash distribuidas) |
| **LL-3** | O(N) o no limitada por su círculo | la carga crece con toda la red o depende de cuántos usuarios ajenos acceden al nodo (un servidor popular, un relé) |

Una red de baja carga en sentido estricto es una red de clase **LL-0**; LL-1 es casi de baja carga.

## 6. Análisis comparativo

### 6.1 Rasgos (1 = cumple, ½ = en parte, 0 = no cumple) y clases

| Red | Año | Círculo propio | Hardware | Economía | Retrasos | Sin centro | Nodo ciego | Clase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Secure Scuttlebutt [32] | 2014 | 1 | 1 | ½ | 1 | 1 | 0 | LL-0 |
| Briar [35] | 2018 | 1 | 1 | ½ | ½ | 1 | 1 | LL-0 |
| Nevod [34] | 2026 | 1 | 1 | ½ | ½ | 1 | 1 | LL-0 |
| FidoNet [26] | 1984 | 1 | 1 | 1 | 1 | 0 | 0 | LL-1 |
| NNCP [27] | 2016 | ½ | 1 | 1 | 1 | 1 | 1 | LL-1 |
| Reticulum / LXMF [28] | 2016 | ½ | 1 | 1 | 1 | 1 | 1 | LL-1 |
| Meshtastic [29] | 2020 | 0 | 1 | 1 | ½ | 1 | ½ | LL-1 |
| Tor [21] | 2002 | 0 | ½ | 0 | 0 | 1 | 1 | LL-3 |
| WhatsApp | 2009 | 0 | 0 | 0 | 0 | 0 | ½ | LL-3 |
| Telegram | 2013 | 0 | 0 | 0 | 0 | 0 | 0 | LL-3 |
| Matrix [11] | 2014 | 0 | ½ | 0 | 0 | ½ | ½ | LL-3 |
| Signal [10] | 2014 | 0 | 0 | 0 | 0 | 0 | ½ | LL-3 |
| Mastodon [12] | 2016 | 0 | ½ | 0 | 0 | ½ | 0 | LL-3 |
| Nostr [33] | 2020 | 0 | ½ | 0 | 0 | 1 | ½ | LL-3 |
| Session [22] | 2020 | 0 | ½ | 0 | ½ | 1 | 1 | LL-3 |

Notas. Signal y WhatsApp obtienen ½ en el rasgo 6: el contenido está cifrado de extremo a extremo,
pero la organización ve los metadatos y gestiona los servidores. En Reticulum y NNCP los nodos
intermedios transportan y guardan paquetes ajenos (rasgo 1 = ½, clase LL-1). El año es la primera
versión pública (Reticulum: en desarrollo desde 2014; Signal: predecesores TextSecure/RedPhone,
2010; Briar: en desarrollo desde 2011).

### 6.2 Observaciones

- Por el rasgo principal (clase LL), los más estrictos son Nevod, Briar y Secure Scuttlebutt
  (LL-0); Reticulum y NNCP pertenecen a LL-1.
- Todas las redes centralizadas y federadas, así como las redes superpuestas de anonimato, son
  LL-3: descentralizar la propiedad no significa descentralizar la carga.

## 7. Nevod como ejemplo de la clase LL-0 y sus limitaciones

Nevod [34] es una red de mensajería construida según el principio Zero Knowledge Infrastructure:
un nodo («node») atiende solo a sus propios participantes y transporta mensajes cifrados sin
acceso a su contenido; no hay centro; los nodos funcionan en hardware doméstico o en servidores
alquilados. La tabla de servicio de nodos crece con el número de *nodos*, no de usuarios, y es
pequeña.

Limitaciones a septiembre de 2026 (rasgos no cumplidos del todo, sin validación práctica):

- rasgo 3: los archivos multimedia se transmiten completos, sin vista previa ni descarga bajo
  demanda;
- rasgo 4: los mensajes no entregados se guardan 72 horas; funciona solo por internet;
- no hay secreto perfecto hacia adelante (forward secrecy): los mensajes se cifran con la clave de
  larga duración del destinatario;
- un nodo ve los metadatos de entrega (quién, a quién, cuándo);
- un prototipo funcional sin usuarios reales ni auditoría independiente; código cerrado; app solo
  para iOS.

Los rasgos se derivaron de los principios de Nevod, así que la comparación le favorece de entrada;
la puntuación de Nevod refleja su arquitectura, no la madurez del producto.

## 8. Cuestiones abiertas

1. Almacenamiento para un destinatario desconectado durante mucho tiempo: quién lo guarda y
   cuánto, sin romper la clase LL-0.
2. Búsqueda de rutas entre muchos nodos sin un directorio central.
3. ¿Es admisible un tránsito limitado (LL-1) para entregar por canales lentos? ¿Hace falta
   reciprocidad («llevas lo ajeno, llevan lo tuyo»)?
4. Qué componentes cuentan como carga: tráfico, almacenamiento, estado, consumo de energía, tiempo
   del administrador.
5. Una métrica formal del círculo del nodo k y su medición en redes reales.

## 9. Conclusión

Los conceptos de carga de la teoría de las comunicaciones describen el estado de una red, no una
propiedad de su arquitectura. El concepto propuesto de red distribuida de baja carga delimita una
clase arquitectónica en la que la carga de un nodo está limitada por su círculo, y completa los
enfoques conocidos (F2F, DTN, tablas hash distribuidas, local-first, redes comunitarias) con una
combinación de seis rasgos. La clasificación LL-0…LL-3 hace medible el concepto y permite asignar
cualquier red a una clase. La validación práctica y una revisión bibliográfica completa en bases
de datos cerradas (IEEE, ACM, eLibrary) son los siguientes pasos.

---

## Referencias

{{REFS}}

---

*Nota sobre el método.* La revisión se hizo con fuentes abiertas; las bases de datos de pago (IEEE
Xplore, textos completos de ACM Digital Library, Springer, eLibrary) no se consultaron de forma
sistemática. Las puntuaciones de rasgos y clases son valoraciones expertas basadas en descripciones
públicas de las redes a septiembre de 2026.
