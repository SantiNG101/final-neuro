# Guión de la presentación (máx. 30 min)

Las mismas notas están en las notas del orador de cada diapositiva. Entre corchetes, qué señalar.
Se regenera con `presentacion/construir_presentacion.py`.

## Tiempos

| # | Diapositiva | Duración | Acumulado |
|---|---|---|---|
| 1 | ¿Qué sabe la corteza olfativa además del olor? | 0:20 | 0:20 |
| 2 | Más que un detector de olores | 0:40 | 1:00 |
| 3 | El mismo olor sólo vale en un contexto | 1:15 | 2:15 |
| 4 | El ratón aprendió: en el contexto recompensado se frena | 1:00 | 3:15 |
| 5 | La población anticipa el contexto recompensado | 1:00 | 4:15 |
| 6 | 16 de 44 neuronas laten a ~2,8 Hz, como la respiración | 1:45 | 6:00 |
| 7 | Algunos pares disparan a milisegundos uno del otro | 1:45 | 7:45 |
| 8 | 140 de 909 pares interactúan a escala de ms | 1:15 | 9:00 |
| 9 | A escala lenta manda el estímulo, pero no del todo | 1:15 | 10:15 |
| 10 | Parte IV · ¿El contexto cambia la coordinación? | 1:30 | 11:45 |
| 11 | El contexto cambia cuánto disparan, no cuánto co-varían | 1:45 | 13:30 |
| 12 | Ni el número de ensayos ni la tasa esconden un efecto | 1:15 | 14:45 |
| 13 | Se coordinan más las neuronas que responden parecido | 2:00 | 16:45 |
| 14 | Lo que sigue: milisegundos por contexto y decodificación | 3:00 | 19:45 |
| 15 | Conclusiones | 1:30 | 21:15 |
| 16 | GRACIAS | 0:10 | 21:25 |

La Parte I (exploración neurona por neurona) está sólo en el notebook. Parte II ~1 min, Parte III ~6 min, Parte IV ~10 min (3 de ellos reservados para IV.3–IV.4), con margen para preguntas.

## Texto por diapositiva

### 1 · ¿Qué sabe la corteza olfativa además del olor?

(20 s) Buenos días. Somos [nombres]. Vamos a presentar el análisis de registros de neuronas de la corteza piriforme, la corteza olfativa primaria, de un ratón que aprendió a asociar olores y contextos con una recompensa. La pregunta de fondo es qué información, además del olor, lleva esta corteza.

### 2 · Más que un detector de olores

(40 s) La idea central [señalar el recuadro celeste]: en un ratón entrenado, la corteza piriforme no sólo detecta olores; su actividad cambia según el contexto en el que espera la recompensa. Pero ese cambio está en cuánto disparan las neuronas, no en cuánto co-varían, y la coordinación entre neuronas se organiza según qué responde cada una. Vamos en tres partes: un repaso breve de la tarea y de la población; la correlación neuronal, que es el análisis que elegimos; y nuestra pregunta propia. La exploración neurona por neurona está completa en el notebook.

### 3 · El mismo olor sólo vale en un contexto

(75 s) La tarea [señalar el esquema]: el ratón corre en un corredor de realidad virtual. En un punto entra a uno de dos contextos visuales, verde o gris, y apenas entra recibe uno de dos olores durante un segundo. Sólo una de las cuatro combinaciones da agua al salir del contexto: el olor recompensado en el contexto recompensado, en rojo. Las otras tres no dan nada [señalar la columna de tipos]. Además hay ensayos sin olor, sólo con contexto. Los datos ya vienen con spike sorting: para cada spike sabemos la neurona y el momento, y para cada ensayo cuándo entró, cuándo salió y cuándo inhaló el olor por primera vez. Es una sola sesión de 65 minutos y no tenemos ni los lamidos ni la velocidad, así que eso hay que tenerlo en cuenta.

### 4 · El ratón aprendió: en el contexto recompensado se frena

(60 s) Antes de mirar neuronas, chequeamos que el animal hubiera aprendido. No tenemos lamidos, pero sí el tiempo que pasa dentro del contexto, que depende de su velocidad [señalar el gráfico]. En el contexto gris, el no recompensado, cruza en alrededor de un segundo. En el contexto recompensado se frena: con el olor no recompensado se queda unos 10,9 segundos, como esperando. Es decir, el contexto ya cambia su conducta. Esto es importante por dos razones: muestra que el ratón es experto, y nos avisa de un confusor. Si vemos diferencias neuronales entre contextos, una parte podría ser movimiento. Además filtramos neuronas: de 64 quedaron 44 estables, las que tienen suficiente actividad y no se pierden a mitad de sesión.

### 5 · La población anticipa el contexto recompensado

(60 s) De la exploración mostramos sólo la actividad promedio de la población, en z respecto de la línea de base; los rasters y PSTH de cada neurona están en el notebook. Alineado a la entrada al contexto [señalar el panel de la izquierda]: en los ensayos con contexto recompensado, rojo, negro y azul punteado, la actividad sube alrededor de un segundo antes, cuando el ratón ya ve el contexto pero todavía no olió nada. En el otro contexto no. Es decir, la población anticipa el contexto; parte podría ser movimiento, porque ahí se frena. Al olor responden 9 neuronas excitándose y 9 inhibiéndose [señalar los otros paneles]; promediadas juntas se cancelarían. Esta anticipación es el punto de partida de nuestra pregunta.

### 6 · 16 de 44 neuronas laten a ~2,8 Hz, como la respiración

(105 s) Empezamos la parte tres con el autocorrelograma: tomamos cada spike de una neurona y miramos cuándo aparecen sus otros spikes. Arriba, la escala corta, de milisegundos [señalar]: el hueco en cero es el período refractario y un pico a pocos milisegundos indica ráfagas; 4 neuronas disparan así. Abajo, la escala larga, de un segundo: algunas neuronas muestran picos repetidos, es decir, disparan rítmicamente. A la derecha están las 44, ordenadas por cuán rítmicas son [señalar el mapa]. Para no confundir ritmo con modulación por la tarea, comparamos contra trenes donde movimos los spikes al azar dentro de ventanas de medio segundo: eso conserva lo lento y destruye el ritmo. 16 neuronas superan ese control, con un pico mediano en 2,8 hertz, dentro del rango de la respiración del ratón. Tiene sentido: en la corteza piriforme, cada inhalación trae una nueva muestra del olor.

### 7 · Algunos pares disparan a milisegundos uno del otro

(105 s) Ahora entre pares de neuronas. El cross-correlograma muestra cómo dispara una neurona B alrededor de cada spike de otra neurona A. El problema es que dos neuronas que responden al mismo olor van a tener un correlograma con un lomo ancho aunque no estén conectadas. Para separar eso estimamos una línea de base suavizando el propio correlograma con una gaussiana hueca de 10 milisegundos [señalar la línea azul]. Es el equivalente analítico de mover los spikes al azar unos milisegundos, y lo propusieron Stark y Abeles en 2009. Lo que supera el umbral punteado es coordinación fina. Vemos tres patrones [señalar de izquierda a derecha]: un pico sólo del lado positivo, a dos o tres milisegundos, que es la firma de una posible conexión de A hacia B; un exceso a ambos lados del cero, típico de dos neuronas que reciben la misma entrada; y un único bin gigante exactamente en cero. Este último no es biología: es el mismo spike asignado a dos unidades por el spike sorting. Lo detectamos y lo excluimos, y es un buen ejemplo de por qué hay que mirar los datos antes de contar conexiones.

### 8 · 140 de 909 pares interactúan a escala de ms

(75 s) Aplicamos ese test a los 909 pares con suficientes spikes. Primero descartamos 10 pares con un único bin gigante en cero, que interpretamos como spikes duplicados por el sorting. De los demás, 140 muestran alguna interacción fina, un 15 por ciento: 85 con un pico sólo del lado causal, candidatas a conexión excitatoria, 43 con sincronía a ambos lados y 40 con un valle, candidatas a inhibición [señalar las barras]. Casi todos los picos caen entre uno y dos milisegundos [señalar el histograma], el retardo esperable de una sinapsis. Los excesos son moderados, de un 40 por ciento sobre la base. Tres cuidados: esperamos menos de dos falsos positivos; las neuronas que más disparan aparecen en más pares simplemente porque el test tiene más potencia con ellas; y una correlación así es una conexión funcional posible, no una sinapsis demostrada.

### 9 · A escala lenta manda el estímulo, pero no del todo

(75 s) A escala más lenta, cientos de milisegundos, usamos el shift predictor clásico: correlacionamos la neurona A de un ensayo con la neurona B del ensayo siguiente del mismo tipo. Eso conserva lo que está atado al estímulo y rompe lo que pasa dentro del mismo ensayo. En el promedio de todos los pares [señalar el panel de la izquierda], la curva naranja, la del estímulo, explica casi todo el lomo: dos neuronas co-varían sobre todo porque responden al mismo olor. Pero queda un exceso, en celeste: en mediana un 2,6 por ciento más de coincidencias, chico pero muy consistente [señalar el histograma]. Y conecta con la escala de milisegundos [señalar el panel de la derecha]: los pares que interactúan fino tienen más coordinación propia, 4,1 contra 2,4 por ciento, y también más correlación de ruido entre ensayos. Son efectos chicos, con p cercanos a 0,02 y 0,03, así que los tomamos como tendencia consistente, no como algo concluyente.

### 10 · Parte IV · ¿El contexto cambia la coordinación?

(90 s) Juntamos las dos cosas que vimos. Por un lado, la población anticipa el contexto recompensado: dispara más antes del olor. Por otro, las neuronas no son independientes: co-varían. Nuestra pregunta es si el contexto cambia también cómo se coordinan, y no sólo cuánto disparan. La idea viene de corteza visual, donde la atención baja las correlaciones de ruido; acá, un estado de expectativa compartido podría subirlas o bajarlas, así que dejamos la dirección abierta [señalar H1]. Y como sub-análisis [señalar H2] nos preguntamos si se coordinan más las neuronas que responden parecido, lo que sería la firma de un ensamble, y si el contexto actúa sobre todo entre ellas. El diseño tiene tres épocas [señalar las cajas]: el corredor, antes de ver el contexto, que es nuestro control; la aproximación, el segundo previo a entrar; y el olor, los primeros 500 milisegundos, comparando el mismo olor en los dos contextos. Cortamos a 500 milisegundos porque en el contexto no recompensado el ratón sale enseguida.

### 11 · El contexto cambia cuánto disparan, no cuánto co-varían

(105 s) El resultado principal [señalar el gráfico]: en verde el contexto recompensado y en gris el no recompensado, para cada época. En el corredor, el control, no hay diferencia, como esperábamos. Pero tampoco la hay en la aproximación ni durante el olor: todos los p de la permutación dan por encima de 0,46. En el olor recompensado hay una tendencia a más correlación en el contexto recompensado, pero está dentro de lo esperable por azar. Lo interesante es la disociación [señalar el número del medio]: en la aproximación la tasa media sí es más alta en el contexto recompensado, 6,6 contra 6,0 hertz, pero la variabilidad compartida no cambia. O sea, el contexto modula cuánto disparan las neuronas, no cuánto co-varían. Y somos honestos con el alcance [señalar el último número]: con estos ensayos podíamos detectar diferencias de r_sc de alrededor de 0,015 o más; un efecto más chico no lo podemos descartar.

### 12 · Ni el número de ensayos ni la tasa esconden un efecto

(75 s) Dos controles [señalar la fila de arriba]: cada histograma es lo que da la diferencia entre contextos si mezclamos al azar las etiquetas de contexto entre ensayos; la línea verde es lo observado, y cae siempre en el centro. Este test ya tiene en cuenta que hay el doble de ensayos recompensados. Abajo, el control por tasa: la correlación de ruido sube con la tasa de disparo, así que si un contexto disparara más podría parecer más correlacionado sólo por eso. Separamos los pares por cuartil de tasa y además ajustamos por tasa con una regresión: el efecto del contexto sigue sin aparecer.

### 13 · Se coordinan más las neuronas que responden parecido

(120 s) El sub-análisis de ensambles. Para cada par medimos cuánto se parecen sus respuestas, la correlación entre sus PSTH en los cuatro tipos de ensayo, y lo comparamos con cuánto co-varían [señalar el primer panel]. Hay una relación clara: los pares que responden parecido tienen más correlación de ruido. Como cada neurona participa en muchos pares, lo testeamos con un test de Mantel, que permuta las etiquetas de las neuronas: rho 0,13, p menor a 0,001. Es la firma de ensambles: grupos de neuronas con la misma respuesta que además disparan juntas. El panel del medio agrega algo que no esperábamos: las interacciones de milisegundos son más frecuentes en los dos extremos, pero de distinto tipo. Entre neuronas muy parecidas dominan las dirigidas y la sincronía; entre neuronas muy distintas, las inhibitorias, 16 de 38. Eso es compatible con ensambles que se excitan por dentro y compiten entre sí. Por último [señalar el tercer panel], miramos si el contexto cambia la coordinación sólo en algunos pares: aparece un efecto chico, pero con signo opuesto en la aproximación y en el olor, así que no lo interpretamos hasta tener el análisis de milisegundos por contexto.

### 14 · Lo que sigue: milisegundos por contexto y decodificación

(3 min reservados) [PENDIENTE: reemplazar por las diapositivas de resultados de IV.3 y IV.4 cuando estén. Ver HANDOFF_parte_IV.md.] Lo que nos falta responder: si el contexto cambia las interacciones de milisegundos, aunque no cambie la co-variación entre ensayos; y si esa coordinación ayuda o perjudica a decodificar el olor, comparando un decodificador con datos reales contra uno donde mezclamos los ensayos entre neuronas.

### 15 · Conclusiones

(90 s) Para cerrar: el ratón aprendió la tarea y la corteza piriforme anticipa el contexto recompensado en su tasa de disparo; muchas neuronas siguen el ritmo respiratorio y forman una red con interacciones de milisegundos. Nuestra pregunta: el contexto cambia cuánto disparan pero no cuánto co-varían, y la coordinación se organiza según qué responde cada neurona, como ensambles. [Completar con IV.3 y IV.4.] Limitaciones: una sola sesión, sin conducta fina, potencia limitada para efectos chicos, y correlación no es conexión.

### 16 · GRACIAS

(10 s) Gracias. Quedamos para preguntas.

## Preguntas que nos pueden hacer

- **¿Por qué la línea de base a 0,5–2 s del inicio y no justo antes del contexto?** Porque el contexto se ve venir en la realidad virtual; justo antes de entrar ya hay anticipación (la vemos en la Parte II). Y antes del inicio está la ventana de respuesta del ensayo anterior (lamidos, agua).
- **¿Un pico en el CCG prueba una sinapsis?** No. Es compatible con una conexión monosináptica (retardo de 1–4 ms, asimetría), pero también con entrada común con retardos distintos o con artefactos del spike sorting (una neurona partida en dos unidades). Por eso decimos «posible conexión funcional».
- **¿Por qué la gaussiana hueca y no el shift predictor para los ms?** El shift predictor sólo saca lo que está atado al estímulo; la gaussiana hueca saca cualquier co-variación más lenta que ~10 ms (incluida la respiración), que es lo que queremos para hablar de conexiones. Para la escala lenta usamos el shift predictor.
- **¿Cuántos falsos positivos esperan?** Con α = 10⁻⁴ por bin y ~16 bins testeados por par, ~1,5 pares en total, muy por debajo de los 140 encontrados.
- **¿La anticipación del contexto no es movimiento?** Puede serlo en parte: en el contexto recompensado el ratón se frena. No tenemos velocidad, sólo el tiempo en el contexto como proxy. Lo marcamos como limitación.
- **¿Por qué excluyeron neuronas?** Por baja tasa (< 0,5 Hz: los correlogramas quedan vacíos) o porque el sorting las pierde a mitad de sesión (aparecen en < 90 % de los ensayos). Igual están graficadas en la Parte I.
- **¿Por qué el ritmo y no el espectro directamente?** El espectro del autocorrelograma es el espectro de potencia del tren de spikes (Wiener–Khinchin); lo hacemos desde la ACG porque es la herramienta de nuestra parte.
- **¿No ver diferencia en r_sc prueba que el contexto no cambia la coordinación?** No: con nuestros ensayos sólo descartamos cambios de r_sc de ~0,015 o más (el 95 % de las permutaciones queda por debajo). Además r_sc mide co-variación de ensayo a ensayo; la coordinación de milisegundos por contexto es IV.3.
- **¿Por qué la ventana de olor es de 0,5 s?** En el contexto no recompensado el ratón sale ~0,5 s después de inhalar; con una ventana más larga compararíamos «dentro del contexto» contra «afuera».
- **¿Por qué permutación y no un test t sobre los pares?** Los pares no son independientes (cada neurona está en 43 pares) y los grupos tienen distinto número de ensayos; permutar la etiqueta de contexto entre ensayos respeta ambas.
- **¿Qué es la correlación de señal?** La correlación entre los PSTH promedio de dos neuronas en los cuatro tipos de ensayo: mide si responden a lo mismo con el mismo curso temporal. Mantel permuta las neuronas para testearla.
