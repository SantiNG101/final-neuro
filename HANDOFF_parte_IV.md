# Handoff · Parte IV (segunda mitad)

Estado al 26/11/2026. Las Partes 0–III y la **primera mitad de la Parte IV (IV.1 y IV.2)** están hechas, en el notebook
y en la presentación. Este documento explica qué hay, cómo correrlo y qué falta (**IV.3–IV.6**), con el detalle
suficiente para hacerlo sin rehacer nada.

---

## 1. La pregunta (opción A, con la B como sub-análisis)

**¿El contexto recompensado cambia cómo se coordinan las neuronas de la corteza piriforme, y no sólo cuánto disparan?**
Sub-análisis (ensambles): **¿se coordinan más las neuronas que responden parecido?** y **¿el contexto actúa sobre todo
entre ellas?**

- **H1**: la correlación de ruido (r_sc) difiere entre contexto recompensado (CR) y no recompensado (CU) en la
  aproximación y durante el olor, pero no en el corredor (control negativo).
- **H2**: la coordinación es mayor entre neuronas con respuestas parecidas (like-to-like), y el efecto del contexto se
  concentra en esos pares.

Épocas: **Corredor** 0,5–2 s desde el inicio (control) · **Aproximación** −1 a 0 s antes de entrar · **Olor** 0–0,5 s
tras la primera inhalación (se corta en 0,5 s porque en CU el ratón sale ~0,5 s después de inhalar).
Comparaciones: CR (tipos 1, 3, 5) vs CU (2, 4, 6) en corredor y aproximación; OR·CR vs OR·CU y OU·CR vs OU·CU en el olor.

## 2. Lo que ya está hecho y qué dio

| Paso | Resultado | Figura |
|---|---|---|
| **IV.1** r_sc por contexto y época, permutando la etiqueta de contexto (1000 veces) | **Ninguna diferencia** en ninguna época (p = 0,75 / 0,78 / 0,46 / 0,49). Diferencia detectable con estos ensayos: \|Δ\| ≈ 0,015–0,026 | `figuras/parte4/rsc_por_contexto.png` |
| **IV.1** controles | Δ ajustado por tasa (regresión) tampoco aparece (p ≥ 0,45). En la aproximación la **tasa** sí sube en CR (6,6 vs 6,0 Hz): el contexto cambia cuánto disparan, no cuánto co-varían | `figuras/parte4/rsc_controles.png` |
| **IV.2** semejanza de respuesta vs acoplamiento | **Like-to-like**: Mantel ρ = 0,13, p = 0,001. Interacciones de ms más frecuentes en los extremos: entre neuronas parecidas dominan dirigidas y sincronía; entre muy distintas, inhibitorias (16 de 38) | `figuras/parte4/ensambles_semejanza.png` |
| **IV.2** ¿dónde actúa el contexto? | Efecto chico y de **signo opuesto** según la época (aproximación ρ = +0,08, p = 0,015; olor ρ = −0,07, p = 0,03). **Control corredor: ρ = 0,04, p = 0,23** (pasa, pero el patrón por cuartil de la aproximación se parece al del corredor; el Δ grande en Q1 del olor es lo único distinto del control) | mismo panel derecho |
| **IV.3** interacciones de ms por contexto (140 pares, CCG por ensayo sumado, 1000 permutaciones) | **Estables**: fuerza mediana 0,29 (CR) vs 0,27 (CU), Δ = −0,002, p = 0,95; igual con pares bien medidos, CR submuestreado y por tipo de interacción. Δ detectable ≈ 0,05 | `figuras/parte4/ccg_por_contexto.png` |
| **IV.4** decodificar OR vs OU (0–0,5 s, logística, GroupKFold por bloques de 20 ensayos) | Olor decodificable en ambos contextos (balanced acc. CR 0,79, CU 0,78; azar 0,50, p < 0,01). **Mezclar (sin correlaciones) no cambia nada** (0,80 / 0,77; p = 0,85 / 0,93). Igualando ensayos, efecto CR − CU = +0,02 (IC −0,12 a +0,16). Confusores: en CR, OU frena al ratón (~10 s vs 2 s); 0–1 s en CU (0,99) incluye la salida/ventana de respuesta | `figuras/parte4/decodificacion.png` |
| **IV.5** ensambles por clustering (average linkage sobre 1 − SENAL) | k = 3, silhouette 0,19 vs nulo 0,14 (p = 0,015): ensambles **blandos**. E3 (6) "de olor" (excitado, antes con OR); E2 (12) "de contexto" (CR > CU desde antes del olor); E1 (26) débil, con 8 de las 9 inhibidas. "Inhibición entre ensambles" **no se sostiene** (inhibitorias 6,0 % dentro vs 2,8 % entre, p = 0,16). Δ r_sc olor entre (+0,019) > dentro (+0,001), p = 0,30 | `figuras/parte4/ensambles_clusters.png`, `ensambles_psth.png` |

Todos los números están en `figuras/resumen_parte4.json`, que la presentación lee automáticamente.

## 3. Archivos y cómo correr todo

| Archivo | Qué es |
|---|---|
| `trabajo_final.py` | **Fuente** del análisis, con celdas `# %%` (VS Code las corre como notebook interactivo) |
| `trabajo_final.ipynb` | Notebook generado desde el `.py`, ya ejecutado (es el que se entrega) |
| `herramientas/py_a_notebook.py` | Convierte el `.py` en `.ipynb` |
| `presentacion/construir_presentacion.py` | Arma el `.pptx` sobre la plantilla de referencia y escribe `presentacion/guion.md` |
| `figuras/` | Todas las figuras; `tabla_neuronas.csv`, `tabla_pares.csv`, `resumen.json`, `resumen_parte4.json` |

Comandos (desde la carpeta `neurociencias/`; en Windows `python` puede no estar en el PATH, por eso `py -3.12`):

```powershell
py -3.12 -m pip install python-pptx
py -3.12 herramientas/py_a_notebook.py trabajo_final.py trabajo_final.ipynb
py -3.12 -m jupyter nbconvert --to notebook --execute --inplace trabajo_final.ipynb
py -3.12 presentacion/construir_presentacion.py
```

Si `py -3.12` no existe, hay un entorno local: `py -3.14 -m venv .venv` + `.venv/Scripts/python -m pip install numpy pandas scipy matplotlib scikit-learn nbformat nbconvert ipykernel python-pptx`, y usar `.venv/Scripts/python` en lugar de `py -3.12`.

El análisis completo tarda ~2 minutos (lo ejecuta `nbconvert`, que además regenera todas las figuras y los `.json`).
Si corrés el `.py` directo en una terminal, antes poné `$env:MPLBACKEND = "Agg"` para que los gráficos no abran
ventanas. **Editá siempre `trabajo_final.py`** y regenerá el notebook; si preferís trabajar
directo en el `.ipynb`, avisá al grupo y dejen de usar el `.py`, para no tener dos versiones.

## 4. Variables del notebook que conviene reutilizar

| Variable / función | Contenido |
|---|---|
| `spikes[n]` | tiempos de spike (s, absolutos) de la neurona `n`, ordenados |
| `trials`, `VALIDOS` | tabla de ensayos (`t_inicio`, `t_entrada`, `t_salida`, `t_inhal`, `tipo`, `dur_contexto`); `VALIDOS` excluye el ensayo 144 (inhalación antes de entrar) |
| `ESTABLES`, `ix` | las 44 neuronas estables y su índice (`ix[n]`) |
| `clas`, `neur` | clasificación por neurona (excitada/inhibida por el olor, selectividades) y QC |
| `POB[alin][tipo]`, `TC[alin]` | PSTH en z (neuronas × tiempo) por alineación y tipo |
| `pares`, `pares_ok`, `IA`, `IB` | tabla de pares (flags `exc_ab`, `exc_ba`, `sincronia`, `inh_ab`, `inh_ba`, `artefacto`, `significativo`, `r_sc`); `pares_ok` sin artefactos; `IA`, `IB` índices de sus neuronas |
| `correlograma(a, b, ventana, ancho)` | CCG por conteo de diferencias (bins centrados en 0) |
| `base_gauss_hueca(ccg)`, `p_exceso`, `p_defecto` | línea de base y tests de Poisson de la Parte III.b |
| `CCG[(a, b)]` | (conteos, base) del CCG de ±50 ms de toda la sesión |
| `EPOCAS`, `conteos_epoca(epoca, tr)` | ventanas de la Parte IV y conteos neurona × ensayo |
| `rsc_pares(C, clase)`, `efecto_contexto(C, clase, ctx)` | r_sc de todos los pares y Δ CR − CU (crudo y ajustado por tasa) |
| `RES4`, `SENAL`, `RSC`, `COMP_Q` | resultados de IV.1, matriz de semejanza de respuesta, matriz r_sc (Parte III), composición de interacciones por cuartil |
| `RNG`, `N_PERM`, `guardar(fig, nombre)`, `p_txt`, `coma_py` | semilla, permutaciones, guardado de figuras, formato de p y decimales con coma |

## 5. Lo que falta

Agregar cada paso como celdas nuevas **después de IV.2 y antes del resumen final** (la celda que escribe
`resumen_parte4.json`), y sumar sus números a `res4` para que la presentación los pueda usar.

### IV.3 · ¿Cambian las interacciones de milisegundos con el contexto?

r_sc mide co-variación de ensayo a ensayo; puede no cambiar y que sí cambie la sincronía fina.

1. Ventana por ensayo: de `t_entrada − 1` a `t_inhal + 0,5` (en los ensayos 5 y 6, sin olor, usar `t_entrada + 0,9`).
2. Para cada neurona, quedarse con los spikes dentro de las ventanas de los ensayos CR y, por separado, de los CU
   (máscara sobre `spikes[n]`). Las ventanas están separadas por segundos, así que concatenarlas no crea lags falsos de ±50 ms.
3. Para los pares con interacción en la Parte III (`pares_ok.significativo`, 140 pares; los demás tienen muy pocas
   coincidencias), `correlograma(..., 0.05, 0.001)` en cada contexto y `base_gauss_hueca`.
4. Medida por par: exceso relativo en el pico, `(c − base)/base` en el bin de `lag_pico_ms` (o la media en ±1–4 ms).
   Al ser relativo a la base, no depende de la tasa.
5. Test: Wilcoxon pareado CR vs CU entre pares y, más robusto, **permutar la etiqueta de contexto de los ensayos**
   (200 veces alcanza) y recalcular la mediana del Δ.
6. Ojo: CR tiene más ensayos (100 vs 75) y ventanas más largas, así que su CCG es menos ruidoso. Para comparar en
   igualdad, submuestrear ensayos CR al número de CU.
7. Figura `figuras/parte4/ccg_por_contexto.png`: dispersión exceso CR vs exceso CU con la identidad, más un par de ejemplo.

### IV.4 · ¿La coordinación ayuda o perjudica a decodificar el olor?

Es el giro de la pregunta: aunque el r_sc medio no cambie, su estructura puede importar para el código.

1. Features: `conteos_epoca("Olor", tr)` (neurona × ensayo; probar también una ventana de 0–1 s). Etiqueta: OR (1, 2)
   vs OU (3, 4). Por separado en **CR** (63 OR·CR vs 24 OU·CR) y **CU** (30 vs 33).
2. Modelo: `Pipeline(StandardScaler(), LogisticRegression(C=1))` de scikit-learn.
3. Validación (chequeo TIME de Uribarri): ensayos vecinos se parecen, así que nada de partir al azar. Usar
   `GroupKFold` con grupos = bloques de ensayos contiguos (por ejemplo, `numero_de_ensayo // 20`).
4. Métrica: **balanced accuracy** (clases desbalanceadas, sobre todo en CR). Línea de base: el mismo pipeline con las
   etiquetas permutadas (azar).
5. **Mezcla que destruye las correlaciones**: dentro de cada clase, permutar los ensayos **de cada neurona por
   separado**. Se conserva la respuesta media de cada neurona y se pierde la co-variación entre neuronas. Entrenar y
   testear sobre datos mezclados; repetir 100 veces.
6. Resultado: accuracy real vs mezclada en cada contexto. Si la real es menor, las correlaciones **perjudican**; si es
   mayor, **ayudan**. Comparar CR vs CU.
7. Con 24 ensayos OU·CR los intervalos van a ser anchos: reportar la dispersión entre folds y mezclas.
8. Figura `figuras/parte4/decodificacion.png`.

### IV.5 · Ensambles por clustering (completa el sub-análisis B)

1. Clustering jerárquico (`scipy.cluster.hierarchy.linkage`, método `average`) sobre la distancia `1 − SENAL`; elegir
   k entre 2 y 6 con silhouette (`sklearn.metrics.silhouette_score` con `metric="precomputed"`).
2. Para cada ensamble: PSTH medio por tipo (`POB`), cuántas son excitadas/inhibidas (`clas.resp_olor`) y sus
   selectividades (`clas.sel_*`). ¿Hay un ensamble "de olor recompensado", uno inhibido, etc.?
3. Formalizar la observación de IV.2: ¿las interacciones **inhibitorias** son sobre todo **entre** ensambles y las
   excitatorias y de sincronía **dentro**? Tabla dentro/entre × tipo, con chi-cuadrado o permutando las etiquetas de ensamble.
4. Figura `figuras/parte4/ensambles_clusters.png` (dendrograma o matriz ordenada + PSTH por ensamble).

### IV.6 · Control de la velocidad y cierre

1. El tiempo en el contexto (`trials.dur_contexto`) es el único proxy de velocidad, y difiere mucho entre CR y CU.
   En la época de olor: para cada neurona, regresar los conteos sobre `log(dur_contexto)` dentro de cada tipo, quedarse
   con los residuos y recalcular `efecto_contexto`. ¿Cambia la conclusión de IV.1?
2. Para la aproximación no hay proxy de velocidad (el tiempo en el contexto se mide después); dejarlo como limitación.
3. Resumir IV.1–IV.6 en una celda markdown de conclusiones al final del notebook.

## 6. Qué cambiar en la presentación

En `presentacion/construir_presentacion.py`:

- **Diapositiva 14** (sección `14 · IV.3–IV.4 pendientes`): reemplazarla por una diapositiva por resultado (IV.3 e
  IV.4), copiando el patrón de las secciones 11 y 13: `nueva(título)`, `imagen(...)`, `stat(...)` o `tarjeta(...)`, y
  `notas("(90 s) ...")`. El número entre paréntesis al comienzo de la nota alimenta la tabla de tiempos del guión.
  Presupuesto: ~1:30 por diapositiva (hay 3 min reservados).
- IV.5 puede entrar como tarjeta en la diapositiva 13 o como una diapositiva más si el resultado es claro. IV.6, como
  una línea en la diapositiva 12 (controles).
- **Conclusiones** (sección 15): reemplazar `IV.3–IV.4: [completar]` y la nota con los resultados.
- **Diapositiva 2**: revisar si "la idea central" sigue valiendo después de IV.3–IV.4.
- **Portada**: completar los nombres del grupo (`[completar resto del grupo]`).
- El guión (`presentacion/guion.md`) se regenera solo con las notas.

**Antes de dar por terminada la presentación, abrila en PowerPoint.** Dos cosas la corrompen sin aviso: una caja de
texto con alto negativo (el helper `tarjeta` ya lo evita) y renombrar las partes de notas.

## 7. Checklist

- [x] IV.3 CCG por contexto + figura + números en `res4` (nulo: Δ fuerza mediana −0,002, p = 0,95; `res4["ccg_contexto"]`)
- [x] IV.4 decodificación real vs mezclada + figura + números en `res4` (`res4["decodificacion"]`; mezcla hecha dentro de cada fold)
- [x] IV.5 ensambles por clustering + figura (`res4["ensambles_clusters"]`; `ensambles_clusters.png`, `ensambles_psth.png`)
- [ ] IV.6 control de velocidad + conclusiones en el notebook
- [ ] Notebook regenerado y ejecutado sin errores
- [ ] Diapositivas 14 → resultados, 15 conclusiones, 2 idea central, portada con nombres
- [ ] Presentación abierta en PowerPoint y ensayada con el guión (≤ 30 min)
