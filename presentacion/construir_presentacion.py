"""Arma la presentación sobre la plantilla de referencia (misma estética, layouts y tipografías).

Uso (desde la carpeta neurociencias/):  py -3.12 presentacion/construir_presentacion.py
Requiere: pip install python-pptx   ·  Lee los números de figuras/resumen.json (lo genera trabajo_final.py).
"""
import copy
import json
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

RAIZ = Path(__file__).resolve().parents[1]
PLANTILLA = RAIZ / "presentacion referencia" / "Ecobici-04-storytelling-corregido.pptx"
FIG = RAIZ / "figuras"
IMG = RAIZ / "presentacion" / "img"
SALIDA = RAIZ / "presentacion" / "presentacion_trabajo_final.pptx"
R = json.loads((FIG / "resumen.json").read_text(encoding="utf-8"))

TINTA, GRIS, ACENTO, CLARO, NEGRO, BLANCO = "262425", "666666", "4A86E8", "E6EEFC", "191919", "FFFFFF"
CUERPO, NUMEROS = "Raleway", "Asap"


def rgb(h):
    return RGBColor.from_string(h)


def coma(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


# ---------------------------------------------------------------- plantilla
prs = Presentation(PLANTILLA)
lista = prs.slides._sldIdLst
ids = list(lista)
for sid in ids[1:-1]:                       # se quedan la portada y "GRACIAS"
    prs.part.drop_rel(sid.rId)
    lista.remove(sid)
from pptx.opc.packuri import PackURI

prs.slides[1].part.partname = PackURI("/ppt/slides/slide99.xml")   # evita choque de nombres con las nuevas
LAYOUT = next(l for m in prs.slide_masters for l in m.slide_layouts if l.name == "CUSTOM_5")


def nueva(titulo):
    s = prs.slides.add_slide(LAYOUT)
    for ph in list(s.placeholders):
        if ph.placeholder_format.idx != 0:
            ph._element.getparent().remove(ph._element)
    tf = s.shapes.title.text_frame
    tf.text = titulo
    for r in tf.paragraphs[0].runs:              # mismo tamaño que la plantilla
        r.font.size = Pt(22)
    return s


def texto(s, x, y, w, h, runs, size=11, color=TINTA, font=CUERPO, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
          espacio=0, margen=0):
    """runs: str | lista de párrafos; cada párrafo es str o lista de (texto, {bold, color, size, font, italic})."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for lado in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, lado, Inches(margen))
    parrafos = runs if isinstance(runs, list) else [runs]
    for i, par in enumerate(parrafos):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if espacio and i > 0:
            p.space_before = Pt(espacio)
        for t, o in ([(par, {})] if isinstance(par, str) else par):
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = o.get("font", font)
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", False)
            f.italic = o.get("italic", False)
            f.color.rgb = rgb(o.get("color", color))
    return tb


def caja(s, x, y, w, h, fill, linea=None):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = rgb(fill)
    if linea:
        sh.line.color.rgb = rgb(linea)
        sh.line.width = Pt(1.5)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def etiqueta(s, x, y, w, t, fill=NEGRO, color=BLANCO, h=0.36, size=11):
    caja(s, x, y, w, h, fill)
    texto(s, x, y, w, h, [[(t, {"bold": True})]], size=size, color=color, align=PP_ALIGN.CENTER,
          anchor=MSO_ANCHOR.MIDDLE)


def imagen(s, ruta, x, y, w=None, h=None):
    W, H = Image.open(ruta).size
    if w and h:                              # encaja dentro de la caja manteniendo proporción
        if W / H > w / h:
            h2 = w * H / W
            y += (h - h2) / 2
            h = h2
        else:
            w2 = h * W / H
            x += (w - w2) / 2
            w = w2
    elif w:
        h = w * H / W
    else:
        w = h * W / H
    return s.shapes.add_picture(str(ruta), Inches(x), Inches(y), Inches(w), Inches(h))


def stat(s, x, y, w, numero, desc, size_num=26, size_desc=10.5, color=ACENTO, h_desc=0.6):
    texto(s, x, y, w, 0.5, [[(numero, {"bold": True, "font": NUMEROS})]], size=size_num, color=color)
    texto(s, x, y + 0.5, w, h_desc, desc, size=size_desc)


def tarjeta(s, x, y, w, h, kicker, titulo, cuerpo, fill=CLARO, oscuro=False, size_cuerpo=10.5):
    caja(s, x, y, w, h, fill)
    c1, c2 = (BLANCO, BLANCO) if oscuro else (ACENTO, TINTA)
    texto(s, x + 0.18, y + 0.14, w - 0.36, 0.25, [[(kicker, {"bold": True})]], size=8.5, color=c1)
    y_cuerpo = y + 0.42
    if titulo:
        texto(s, x + 0.18, y + 0.4, w - 0.36, 0.5, [[(titulo, {"bold": True})]], size=13, color=c2)
        y_cuerpo = y + 0.95
    alto = max(y + h - 0.1 - y_cuerpo, 0.3)        # un alto negativo corrompe el .pptx
    texto(s, x + 0.18, y_cuerpo, w - 0.36, alto, cuerpo, size=size_cuerpo, color=c2, espacio=4)


def letra(s, x, y, t, w=0.81, h=0.71, size=24, fill=NEGRO):
    caja(s, x, y, w, h, fill)
    texto(s, x, y, w, h, t, size=size, color=BLANCO, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def notas(s, t):
    s.notes_slide.notes_text_frame.text = t


B = {"bold": True}

# ---------------------------------------------------------------- 1 · portada
portada = prs.slides[0]
for sh in portada.shapes:
    if not sh.has_text_frame:
        continue
    ps = sh.text_frame.paragraphs
    if sh.is_placeholder and sh.placeholder_format.idx == 0:
        ps[0].runs[0].text = "¿Qué sabe la corteza olfativa además del olor?"
        ps[1].runs[0].text = "Correlación neuronal y contexto en una tarea olor–contexto–recompensa"
    elif sh.is_placeholder and sh.placeholder_format.idx == 1:
        ps[0].runs[0].text = "Neurociencias · ITBA · 2.º cuatrimestre 2026"
        ps[1].runs[0].text = "Santiago Joaquín Nartallo Galvagno - 62208"
        ps[2].runs[0].text = "Josefina Miguez - 63132"
notas(portada, "(20 s) Buenos días. Somos [nombres]. Vamos a presentar el análisis de registros de neuronas de la "
               "corteza piriforme, la corteza olfativa primaria, de un ratón que aprendió a asociar olores y contextos "
               "con una recompensa. La pregunta de fondo es qué información, además del olor, lleva esta corteza.")

# ---------------------------------------------------------------- 2 · hoja de ruta
s = nueva("Más que un detector de olores")
for i, (l, neg, resto) in enumerate([
        ("A", "Tarea y población: ", "qué aprendió el ratón y cómo responde la población (breve)."),
        ("B", "Correlación neuronal: ", "el ritmo propio de cada neurona y qué pares disparan coordinados."),
        ("C", "Nuestra pregunta: ", "¿el contexto recompensado cambia cómo se coordinan las neuronas?")]):
    y = 1.4 + i * 1.05
    letra(s, 0.75, y, l)
    texto(s, 1.75, y, 3.55, 0.71, [[(neg, B), (resto, {})]], size=12, anchor=MSO_ANCHOR.MIDDLE)
caja(s, 5.75, 1.4, 3.45, 2.81, CLARO)
texto(s, 5.95, 1.55, 3.05, 2.55, [
    [("LA IDEA CENTRAL", {"bold": True, "size": 9, "color": ACENTO, "font": NUMEROS})],
    [("El contexto recompensado cambia cuánto disparan las neuronas de la corteza piriforme, pero no cuánto "
      "co-varían: la coordinación sigue a qué responde cada neurona.", {"bold": True, "size": 13})],
    [(f"{R['estables']} neuronas estables · {R['ensayos']} ensayos · una sesión.",
      {"size": 11, "color": GRIS, "font": NUMEROS})]], espacio=8)
notas(s, "(40 s) La idea central [señalar el recuadro celeste]: en un ratón entrenado, la corteza piriforme no sólo "
         "detecta olores; su actividad cambia según el contexto en el que espera la recompensa. Pero ese cambio está "
         "en cuánto disparan las neuronas, no en cuánto co-varían, y la coordinación entre neuronas se organiza según "
         "qué responde cada una. Vamos en tres partes: un repaso breve de la tarea y de la población; la correlación "
         "neuronal, que es el análisis que elegimos; y nuestra pregunta propia. La exploración neurona por neurona "
         "está completa en el notebook.")

# ---------------------------------------------------------------- 3 · tarea y datos
s = nueva("El mismo olor sólo vale en un contexto")
imagen(s, IMG / "tarea.png", 0.75, 1.3, w=5.3, h=2.45)
tipos = [("OR·CR", "D62728", "63", "olor y contexto recompensados → agua"), ("OR·CU", "FF8C1A", "31", "olor recompensado, contexto no"),
         ("OU·CR", "111111", "24", "contexto recompensado, olor no"), ("OU·CU", "9E9E9E", "33", "ninguno"),
         ("Sin olor", ACENTO, "25", "sólo contexto (CR 13 · CU 12)")]
for i, (t, c, n, d) in enumerate(tipos):
    y = 1.3 + i * 0.5
    caja(s, 6.35, y, 0.95, 0.38, BLANCO, linea=c)
    texto(s, 6.35, y, 0.95, 0.38, [[(t, {"bold": True, "color": c})]], size=10, align=PP_ALIGN.CENTER,
          anchor=MSO_ANCHOR.MIDDLE)
    texto(s, 7.42, y, 0.4, 0.38, [[(n, {"bold": True, "font": NUMEROS})]], size=12, color=ACENTO, anchor=MSO_ANCHOR.MIDDLE)
    texto(s, 7.85, y, 1.45, 0.38, d, size=8.5, color=GRIS, anchor=MSO_ANCHOR.MIDDLE)
texto(s, 0.75, 3.95, 8.5, 0.3, [[("Los datos: ", B), ("tiempos de spike después del spike sorting, con la entrada y la salida "
                                 "del contexto y la primera inhalación del olor en cada ensayo.", {})]], size=11)
for i, (t, fill, col) in enumerate([(f"{R['neuronas']} neuronas", CLARO, TINTA), (f"{R['ensayos']} ensayos", CLARO, TINTA),
                                    ("65 min · 1 sesión", ACENTO, BLANCO), ("Sin lamidos ni velocidad", NEGRO, BLANCO)]):
    caja(s, 0.77 + i * 2.13, 4.45, 2.05, 0.42, fill)
    texto(s, 0.77 + i * 2.13, 4.45, 2.05, 0.42, [[(t, B)]], size=10, color=col, align=PP_ALIGN.CENTER,
          anchor=MSO_ANCHOR.MIDDLE)
notas(s, "(75 s) La tarea [señalar el esquema]: el ratón corre en un corredor de realidad virtual. En un punto entra "
         "a uno de dos contextos visuales, verde o gris, y apenas entra recibe uno de dos olores durante un segundo. "
         "Sólo una de las cuatro combinaciones da agua al salir del contexto: el olor recompensado en el contexto "
         "recompensado, en rojo. Las otras tres no dan nada [señalar la columna de tipos]. Además hay ensayos sin olor, "
         "sólo con contexto. Los datos ya vienen con spike sorting: para cada spike sabemos la neurona y el momento, y "
         "para cada ensayo cuándo entró, cuándo salió y cuándo inhaló el olor por primera vez. Es una sola sesión de "
         "65 minutos y no tenemos ni los lamidos ni la velocidad, así que eso hay que tenerlo en cuenta.")

# ---------------------------------------------------------------- 4 · comportamiento y calidad
s = nueva("El ratón aprendió: en el contexto recompensado se frena")
imagen(s, FIG / "parte0" / "comportamiento.png", 0.75, 1.25, w=4.3, h=3.25)
d = {int(k): v for k, v in R["dur_ctx_mediana"].items()}
stat(s, 5.5, 1.3, 3.7, f"{coma(d[3])} s vs {coma(d[4])} s",
     "tiempo en el contexto con el olor no recompensado: en el contexto recompensado se queda, en el otro sigue de largo")
stat(s, 5.5, 2.45, 3.7, f"{R['estables']} de {R['neuronas']}",
     "neuronas estables (≥ 0,5 Hz y presentes en ≥ 90 % de los ensayos): son las que usamos para promedios y pares")
texto(s, 0.75, 4.6, 8.3, 0.45, [[("Ojo: ", B), ("el tiempo en el contexto es nuestro único proxy de la velocidad. Cambia "
                                 "mucho entre tipos de ensayo, así que puede confundir cualquier diferencia entre contextos.", {})]],
      size=10.5)
notas(s, "(60 s) Antes de mirar neuronas, chequeamos que el animal hubiera aprendido. No tenemos lamidos, pero sí el tiempo "
         "que pasa dentro del contexto, que depende de su velocidad [señalar el gráfico]. En el contexto gris, el no "
         f"recompensado, cruza en alrededor de un segundo. En el contexto recompensado se frena: con el olor no "
         f"recompensado se queda unos {coma(d[3])} segundos, como esperando. Es decir, el contexto ya cambia su conducta. "
         f"Esto es importante por dos razones: muestra que el ratón es experto, y nos avisa de un confusor. Si vemos "
         f"diferencias neuronales entre contextos, una parte podría ser movimiento. Además filtramos neuronas: de "
         f"{R['neuronas']} quedaron {R['estables']} estables, las que tienen suficiente actividad y no se pierden a mitad de sesión.")

# ---------------------------------------------------------------- 5 · población (Parte II, breve)
s = nueva("La población anticipa el contexto recompensado")
imagen(s, FIG / "parte2" / "poblacion_slide.png", 0.75, 1.2, w=8.5, h=2.65)
tarjeta(s, 0.75, 3.95, 2.72, 1.0, "ANTES DEL OLOR", "", [[("Sólo en CR (rojo, negro, azul) sube ~1 s antes de la "
        "inhalación.", {})]], size_cuerpo=10)
tarjeta(s, 3.67, 3.95, 2.72, 1.0, "DESPUÉS DEL OLOR", "", [[("Excitadas: pico a ~0,5 s. Inhibidas: caen y se quedan "
        "abajo.", {})]], size_cuerpo=10)
tarjeta(s, 6.59, 3.95, 2.72, 1.0, "PROMEDIAR CANCELA", "", [[("Todas juntas, excitación e inhibición se compensan.",
        {"color": BLANCO})]], fill=ACENTO, oscuro=True, size_cuerpo=10)
notas(s, f"(60 s) De la exploración mostramos sólo la actividad promedio de la población, en z respecto de la línea "
         f"de base; los rasters y PSTH de cada neurona están en el notebook. Alineado a la entrada al contexto "
         f"[señalar el panel de la izquierda]: en los ensayos con contexto recompensado, rojo, negro y azul punteado, la "
         f"actividad sube alrededor de un segundo antes, cuando el ratón ya ve el contexto pero todavía no olió nada. En "
         f"el otro contexto no. Es decir, la población anticipa el contexto; parte podría ser movimiento, porque ahí se "
         f"frena. Al olor responden {R['excitadas_olor']} neuronas excitándose y {R['inhibidas_olor']} inhibiéndose "
         f"[señalar los otros paneles]; promediadas juntas se cancelarían. Esta anticipación es el punto de partida de "
         f"nuestra pregunta.")

# ---------------------------------------------------------------- 6 · autocorrelación
s = nueva(f"{R['ritmicas']} de {R['estables']} neuronas laten a ~{coma(R['f_pico_mediana'])} Hz, como la respiración")
imagen(s, FIG / "parte3" / "autocorrelogramas.png", 0.75, 1.2, w=8.5, h=3.3)
texto(s, 0.75, 4.55, 8.5, 0.5, [[("Autocorrelograma: ", B), ("la tasa de la neurona en función del tiempo desde uno de sus "
                                 "propios spikes. Control: mover cada spike al azar dentro de ventanas de 500 ms conserva "
                                 "la modulación por la tarea y destruye el ritmo.", {})]], size=10)
notas(s, f"(105 s) Empezamos la parte tres con el autocorrelograma: tomamos cada spike de una neurona y miramos cuándo "
         f"aparecen sus otros spikes. Arriba, la escala corta, de milisegundos [señalar]: el hueco en cero es el período "
         f"refractario y un pico a pocos milisegundos indica ráfagas; {R['bursty']} neuronas disparan así. Abajo, la "
         f"escala larga, de un segundo: algunas neuronas muestran picos repetidos, es decir, disparan rítmicamente. A la "
         f"derecha están las {R['estables']}, ordenadas por cuán rítmicas son [señalar el mapa]. Para no confundir ritmo "
         f"con modulación por la tarea, comparamos contra trenes donde movimos los spikes al azar dentro de ventanas de "
         f"medio segundo: eso conserva lo lento y destruye el ritmo. {R['ritmicas']} neuronas superan ese control, con "
         f"un pico mediano en {coma(R['f_pico_mediana'])} hertz, dentro del rango de la respiración del ratón. Tiene "
         f"sentido: en la corteza piriforme, cada inhalación trae una nueva muestra del olor.")

# ---------------------------------------------------------------- 7 · CCG ejemplos
s = nueva("Algunos pares disparan a milisegundos uno del otro")
texto(s, 0.75, 1.2, 8.5, 0.5, [[("Cross-correlograma: ", B), ("la tasa de B alrededor de cada spike de A. La línea azul es la "
                                "parte que se explica por co-variaciones lentas (> 10 ms), como responder al mismo olor; "
                                "lo que la supera es coordinación fina.", {})]], size=10.5)
imagen(s, FIG / "parte3" / "ccg_ejemplos.png", 0.75, 1.85, w=8.5, h=2.5)
for i, (t, fill, col) in enumerate([("Un solo lado: posible conexión A → B", NEGRO, BLANCO),
                                    ("Ambos lados: entrada común", ACENTO, BLANCO),
                                    ("Un bin gigante: artefacto, se excluye", CLARO, TINTA)]):
    caja(s, 0.77 + i * 2.85, 4.45, 2.75, 0.42, fill)
    texto(s, 0.77 + i * 2.85, 4.45, 2.75, 0.42, [[(t, B)]], size=9.5, color=col, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
notas(s, "(105 s) Ahora entre pares de neuronas. El cross-correlograma muestra cómo dispara una neurona B alrededor de "
         "cada spike de otra neurona A. El problema es que dos neuronas que responden al mismo olor van a tener un "
         "correlograma con un lomo ancho aunque no estén conectadas. Para separar eso estimamos una línea de base "
         "suavizando el propio correlograma con una gaussiana hueca de 10 milisegundos [señalar la línea azul]. Es "
         "el equivalente analítico de mover los spikes al azar unos milisegundos, y lo propusieron Stark y Abeles en "
         "2009. Lo que supera el umbral punteado es coordinación fina. Vemos tres patrones [señalar de izquierda a "
         "derecha]: un pico sólo del lado positivo, a dos o tres milisegundos, que es la firma de una posible conexión "
         "de A hacia B; un exceso a ambos lados del cero, típico de dos neuronas que reciben la misma entrada; y un "
         "único bin gigante exactamente en cero. Este último no es biología: es el mismo spike asignado a dos unidades "
         "por el spike sorting. Lo detectamos y lo excluimos, y es un buen ejemplo de por qué hay que mirar los datos "
         "antes de contar conexiones.")

# ---------------------------------------------------------------- 8 · red
s = nueva(f"{R['pares_sig']} de {R['pares_testeables']} pares interactúan a escala de ms")
imagen(s, FIG / "parte3" / "red_conexiones.png", 0.75, 1.2, w=8.5, h=3.4)
texto(s, 0.75, 4.62, 8.5, 0.45, [[("Cuidados: ", B), (f"~{coma(R['fp_esperados'],1)} falsos positivos esperados; las "
                                 f"neuronas de tasa alta acumulan más pares (ρ = {coma(R['rho_grado_tasa'],2)}) porque el "
                                 "test tiene más potencia, y «posible conexión» no es sinapsis probada.", {})]], size=10)
notas(s, f"(75 s) Aplicamos ese test a los {R['pares_testeables']} pares con suficientes spikes. Primero descartamos "
         f"{R['artefactos']} pares con un único bin gigante en cero, que interpretamos como spikes duplicados por el "
         f"sorting. De los demás, {R['pares_sig']} muestran alguna interacción fina, un {round(100*R['pares_sig']/R['pares_testeables'])} "
         f"por ciento: {R['exc_dirigidas']} con un pico sólo del lado causal, candidatas a conexión excitatoria, "
         f"{R['sincronia']} con sincronía a ambos lados y {R['inhibitorias']} con un valle, candidatas a inhibición "
         f"[señalar las barras]. Casi todos los picos caen entre uno y dos milisegundos [señalar el histograma], el "
         f"retardo esperable de una sinapsis. Los excesos son moderados, de un {round(100*R['exceso_mediano_sig'])} por "
         f"ciento sobre la base. Tres cuidados: esperamos menos de dos falsos positivos; las neuronas que más disparan "
         f"aparecen en más pares simplemente porque el test tiene más potencia con ellas; y una correlación así es una "
         f"conexión funcional posible, no una sinapsis demostrada.")

# ---------------------------------------------------------------- 9 · shift predictor y r_sc
s = nueva("A escala lenta manda el estímulo, pero no del todo")
imagen(s, FIG / "parte3" / "shift_predictor_rsc.png", 0.75, 1.2, w=8.5, h=2.55)
tarjeta(s, 0.75, 3.9, 4.15, 1.05, "SHIFT PREDICTOR", "", [[("A del ensayo i con B del siguiente del mismo tipo: explica casi "
        f"todo el lomo; quedan +{coma(R['exceso_intra_mediana'])} % de coincidencias propias del ensayo (p < 0,001).", {})]],
        size_cuerpo=10)
tarjeta(s, 5.1, 3.9, 4.15, 1.05, "DE MILISEGUNDOS A ENSAYOS", "", [[(f"Los pares con interacción fina tienen más: "
        f"+{coma(R['exceso_intra_sig'])} % vs +{coma(R['exceso_intra_ns'])} % (p = {coma(R['p_ei'],2)}); r_sc "
        f"{coma(R['rsc_sig'],3)} vs {coma(R['rsc_ns'],3)}.", {"color": BLANCO})]], fill=ACENTO, oscuro=True, size_cuerpo=10)
notas(s, f"(75 s) A escala más lenta, cientos de milisegundos, usamos el shift predictor clásico: correlacionamos la "
         f"neurona A de un ensayo con la neurona B del ensayo siguiente del mismo tipo. Eso conserva lo que está atado "
         f"al estímulo y rompe lo que pasa dentro del mismo ensayo. En el promedio de todos los pares [señalar el panel "
         f"de la izquierda], la curva naranja, la del estímulo, explica casi todo el lomo: dos neuronas co-varían sobre "
         f"todo porque responden al mismo olor. Pero queda un exceso, en celeste: en mediana un "
         f"{coma(R['exceso_intra_mediana'])} por ciento más de coincidencias, chico pero muy consistente [señalar el "
         f"histograma]. Y conecta con la escala de milisegundos [señalar el panel de la derecha]: los pares que "
         f"interactúan fino tienen más coordinación propia, {coma(R['exceso_intra_sig'])} contra "
         f"{coma(R['exceso_intra_ns'])} por ciento, y también más correlación de ruido entre ensayos. Son efectos chicos, "
         f"con p cercanos a 0,02 y 0,03, así que los tomamos como tendencia consistente, no como algo concluyente.")

# ---------------------------------------------------------------- 10 · parte IV: pregunta y diseño
R4 = json.loads((FIG / "resumen_parte4.json").read_text(encoding="utf-8"))
K_COR, K_APR, K_OR, K_OU = "Corredor | CR vs CU", "Aproximación | CR vs CU", "Olor | OR: CR vs CU", "Olor | OU: CR vs CU"
VERDE = "4C9A2A"

s = nueva("Parte IV · ¿El contexto cambia la coordinación?")
tarjeta(s, 0.75, 1.25, 4.15, 1.3, "H1 · CONTEXTO", "", [[("La variabilidad compartida entre neuronas (r_sc) cambia entre "
        "contextos en la aproximación y durante el olor, pero no en el corredor.", {})]], size_cuerpo=10.5)
tarjeta(s, 5.1, 1.25, 4.15, 1.3, "H2 · ENSAMBLES", "", [[("Se coordinan más las neuronas que responden parecido, y el "
        "contexto actúa sobre todo entre ellas.", {"color": BLANCO})]], fill=ACENTO, oscuro=True, size_cuerpo=10.5)
for i, (nom, ven, comp, fill, col) in enumerate([
        ("Corredor (control)", "0,5–2 s tras el inicio", "CR vs CU", CLARO, TINTA),
        ("Aproximación", "−1 a 0 s antes de entrar", "CR vs CU", CLARO, TINTA),
        ("Olor", "0–0,5 s tras la inhalación", "OR·CR vs OR·CU · OU·CR vs OU·CU", NEGRO, BLANCO)]):
    x = 0.75 + i * 2.92
    caja(s, x, 2.85, 2.72, 1.1, fill)
    texto(s, x + 0.15, 2.92, 2.42, 1.0, [[(nom, {"bold": True, "size": 12})], [(ven, {"size": 10})],
                                          [(comp, {"size": 9.5, "bold": True, "color": ACENTO if fill != NEGRO else "A9C4F5"})]],
          color=col, espacio=3)
    if i < 2:
        texto(s, x + 2.72, 3.2, 0.2, 0.4, "→", size=14, color=GRIS, align=PP_ALIGN.CENTER)
texto(s, 0.75, 4.15, 8.5, 0.75, [[("r_sc: ", B), ("correlación entre los conteos por ensayo de dos neuronas, después de restar la "
                                 "media de cada tipo de ensayo: mide sólo la co-variación de ensayo a ensayo. Test: permutar la "
                                 "etiqueta de contexto entre ensayos, 1000 veces.", {})]], size=10)
notas(s, "(90 s) Juntamos las dos cosas que vimos. Por un lado, la población anticipa el contexto recompensado: dispara "
         "más antes del olor. Por otro, las neuronas no son independientes: co-varían. Nuestra pregunta es si el "
         "contexto cambia también cómo se coordinan, y no sólo cuánto disparan. La idea viene de corteza visual, donde "
         "la atención baja las correlaciones de ruido; acá, un estado de expectativa compartido podría subirlas o "
         "bajarlas, así que dejamos la dirección abierta [señalar H1]. Y como sub-análisis [señalar H2] nos preguntamos "
         "si se coordinan más las neuronas que responden parecido, lo que sería la firma de un ensamble, y si el contexto "
         "actúa sobre todo entre ellas. El diseño tiene tres épocas [señalar las cajas]: el corredor, antes de ver el "
         "contexto, que es nuestro control; la aproximación, el segundo previo a entrar; y el olor, los primeros 500 "
         "milisegundos, comparando el mismo olor en los dos contextos. Cortamos a 500 milisegundos porque en el contexto "
         "no recompensado el ratón sale enseguida.")

# ---------------------------------------------------------------- 11 · IV.1 resultado
s = nueva("El contexto cambia cuánto disparan, no cuánto co-varían")
imagen(s, FIG / "parte4" / "rsc_por_contexto.png", 0.6, 1.2, w=5.7, h=3.65)
ps = [R4[k]["p"] for k in (K_COR, K_APR, K_OR, K_OU)]
stat(s, 6.6, 1.25, 2.65, f"p ≥ {coma(min(ps), 2)}", "en todas las épocas: r_sc no difiere entre contextos", h_desc=0.55)
stat(s, 6.6, 2.4, 2.65, f"{coma(R4[K_APR]['tasa_cr'])} vs {coma(R4[K_APR]['tasa_cu'])} Hz",
     "tasa media en la aproximación (CR vs CU): ahí sí cambia", h_desc=0.55)
mdes = [R4[k]["mde"] for k in (K_APR, K_OR, K_OU)]
stat(s, 6.6, 3.55, 2.65, f"|Δ| ≥ {coma(min(mdes), 3)}", "lo que podíamos detectar: descartamos cambios grandes, no chicos",
     h_desc=0.55)
notas(s, f"(105 s) El resultado principal [señalar el gráfico]: en verde el contexto recompensado y en gris el no "
         f"recompensado, para cada época. En el corredor, el control, no hay diferencia, como esperábamos. Pero tampoco "
         f"la hay en la aproximación ni durante el olor: todos los p de la permutación dan por encima de "
         f"{coma(min(ps), 2)}. En el olor recompensado hay una tendencia a más correlación en el contexto recompensado, "
         f"pero está dentro de lo esperable por azar. Lo interesante es la disociación [señalar el número del medio]: en la "
         f"aproximación la tasa media sí es más alta en el contexto recompensado, {coma(R4[K_APR]['tasa_cr'])} contra "
         f"{coma(R4[K_APR]['tasa_cu'])} hertz, pero la variabilidad compartida no cambia. O sea, el contexto modula "
         f"cuánto disparan las neuronas, no cuánto co-varían. Y somos honestos con el alcance [señalar el último "
         f"número]: con estos ensayos podíamos detectar diferencias de r_sc de alrededor de {coma(min(mdes), 3)} o más; "
         f"un efecto más chico no lo podemos descartar.")

# ---------------------------------------------------------------- 12 · IV.1 controles
s = nueva("Ni el número de ensayos ni la tasa esconden un efecto")
imagen(s, FIG / "parte4" / "rsc_controles.png", 0.75, 1.2, w=8.5, h=3.35)
texto(s, 0.75, 4.62, 8.5, 0.45, [[("Arriba: ", B), ("Δ observado (verde) contra 1000 permutaciones de contexto, que respetan "
                                 "el número desigual de ensayos. ", {}), ("Abajo: ", B),
                                 ("Δ por cuartil de tasa del par y Δ ajustado por tasa con regresión: tampoco aparece.", {})]],
      size=10)
notas(s, "(75 s) Dos controles [señalar la fila de arriba]: cada histograma es lo que da la diferencia entre contextos "
         "si mezclamos al azar las etiquetas de contexto entre ensayos; la línea verde es lo observado, y cae siempre en "
         "el centro. Este test ya tiene en cuenta que hay el doble de ensayos recompensados. Abajo, el control por tasa: "
         "la correlación de ruido sube con la tasa de disparo, así que si un contexto disparara más podría parecer más "
         "correlacionado sólo por eso. Separamos los pares por cuartil de tasa y además ajustamos por tasa con una "
         "regresión: el efecto del contexto sigue sin aparecer.")

# ---------------------------------------------------------------- 13 · IV.2 ensambles
comp = R4["composicion_por_cuartil"]
q1, q4 = comp["Q1 distintas"], comp["Q4 parecidas"]
dq = R4["delta_vs_semejanza"]
s = nueva("Se coordinan más las neuronas que responden parecido")
imagen(s, FIG / "parte4" / "ensambles_semejanza.png", 0.75, 1.2, w=8.5, h=2.6)
tarjeta(s, 0.75, 3.95, 2.72, 1.0, "LIKE-TO-LIKE", "", [[(f"Mantel ρ = {coma(R4['mantel_rho'], 2)}, "
        f"{'p < 0,001' if R4['mantel_p'] < 0.001 else 'p = ' + coma(R4['mantel_p'], 3)}: más semejanza, más r_sc.", {})]],
        size_cuerpo=10)
tarjeta(s, 3.67, 3.95, 2.72, 1.0, "INTERACCIONES DE MS", "", [[(f"Distintas: más inhibitorias ({q1['inhibitoria']} de "
        f"{sum(q1.values())}). Parecidas: más dirigidas y sincronía.", {})]], size_cuerpo=10)
tarjeta(s, 6.59, 3.95, 2.72, 1.0, "¿Y EL CONTEXTO?", "", [[(f"Efecto chico y de signo opuesto según la época "
        f"(ρ = {coma(dq[K_APR]['rho'], 2)} y {coma(dq[K_OR]['rho'], 2)}): sin interpretar todavía.", {"color": BLANCO})]],
        fill=ACENTO, oscuro=True, size_cuerpo=10)
notas(s, f"(120 s) El sub-análisis de ensambles. Para cada par medimos cuánto se parecen sus respuestas, la correlación "
         f"entre sus PSTH en los cuatro tipos de ensayo, y lo comparamos con cuánto co-varían [señalar el primer panel]. "
         f"Hay una relación clara: los pares que responden parecido tienen más correlación de ruido. Como cada neurona "
         f"participa en muchos pares, lo testeamos con un test de Mantel, que permuta las etiquetas de las neuronas: "
         f"rho {coma(R4['mantel_rho'], 2)}, p {'menor a 0,001' if R4['mantel_p'] < 0.001 else coma(R4['mantel_p'], 3)}. "
         f"Es la firma de ensambles: grupos de neuronas con la misma respuesta que además disparan juntas. El panel del "
         f"medio agrega algo que no esperábamos: las interacciones de milisegundos son más frecuentes en los dos extremos, "
         f"pero de distinto tipo. Entre neuronas muy parecidas dominan las dirigidas y la sincronía; entre neuronas muy "
         f"distintas, las inhibitorias, {q1['inhibitoria']} de {sum(q1.values())}. Eso es compatible con ensambles que se "
         f"excitan por dentro y compiten entre sí. Por último [señalar el tercer panel], miramos si el contexto cambia la "
         f"coordinación sólo en algunos pares: aparece un efecto chico, pero con signo opuesto en la aproximación y en el "
         f"olor, así que no lo interpretamos hasta tener el análisis de milisegundos por contexto.")

# ---------------------------------------------------------------- 14 · IV.3–IV.4 pendientes
s = nueva("Lo que sigue: milisegundos por contexto y decodificación")
tarjeta(s, 0.75, 1.3, 4.15, 2.6, "IV.3 · PENDIENTE", "¿Cambian las interacciones de ms con el contexto?",
        [[("Mismo CCG con base de gaussiana hueca, pero sólo con los spikes de cada contexto (aproximación + olor). "
           "Figura: exceso del pico por par, CR vs CU.", {})]], size_cuerpo=10.5)
tarjeta(s, 5.1, 1.3, 4.15, 2.6, "IV.4 · PENDIENTE", "¿La coordinación ayuda a decodificar el olor?",
        [[("Regresión logística OR vs OU con validación por bloques de ensayos, con datos reales y con ensayos mezclados "
           "entre neuronas (sin correlaciones), en cada contexto.", {"color": BLANCO})]], fill=ACENTO, oscuro=True,
        size_cuerpo=10.5)
texto(s, 0.75, 4.15, 8.5, 0.7, [[("También en curso: ", B), ("IV.5 ensambles por clustering y qué codifica cada uno; IV.6 "
                                 "control de la velocidad (tiempo en el contexto) en r_sc.", {})]], size=10.5)
notas(s, "(3 min reservados) [PENDIENTE: reemplazar por las diapositivas de resultados de IV.3 y IV.4 cuando estén. "
         "Ver HANDOFF_parte_IV.md.] Lo que nos falta responder: si el contexto cambia las interacciones de milisegundos, "
         "aunque no cambie la co-variación entre ensayos; y si esa coordinación ayuda o perjudica a decodificar el olor, "
         "comparando un decodificador con datos reales contra uno donde mezclamos los ensayos entre neuronas.")

# ---------------------------------------------------------------- 15 · conclusiones
s = nueva("Conclusiones")
etiqueta(s, 0.75, 1.3, 2.6, "Lo que encontramos")
texto(s, 0.75, 1.8, 4.1, 2.9, [
    [("El ratón aprendió: ", B), ("se frena en el contexto recompensado.", {})],
    [("La población anticipa ese contexto: ", B), ("dispara más antes del olor.", {})],
    [("Ritmo respiratorio ", B), (f"en {R['ritmicas']} de {R['estables']} neuronas.", {})],
    [("Red funcional: ", B), (f"{R['pares_sig']} pares con interacción a 1–2 ms.", {})],
    [("El contexto no cambia la co-variación ", B), ("(r_sc), sólo la tasa.", {})],
    [("Ensambles: ", B), ("se coordinan más las neuronas que responden parecido.", {})],
    [("IV.3–IV.4: ", B), ("[completar]", {"italic": True, "color": GRIS})]], size=10.5, espacio=5)
etiqueta(s, 5.1, 1.3, 2.6, "Limitaciones")
texto(s, 5.1, 1.8, 4.15, 2.9, [
    [("Una sola sesión y un animal: ", B), ("no podemos comparar aprendizaje.", {})],
    [("Sin lamidos ni velocidad: ", B), ("el tiempo en el contexto es el único proxy de conducta.", {})],
    [("Potencia: ", B), (f"con ~30–60 ensayos por condición sólo descartamos cambios de r_sc ≥ {coma(min(mdes), 3)}.", {})],
    [("Correlación no es conexión: ", B), ("faltan la geometría de los electrodos y manipulaciones.", {})]],
    size=10.5, espacio=6)
notas(s, "(90 s) Para cerrar: el ratón aprendió la tarea y la corteza piriforme anticipa el contexto recompensado en su "
         "tasa de disparo; muchas neuronas siguen el ritmo respiratorio y forman una red con interacciones de "
         "milisegundos. Nuestra pregunta: el contexto cambia cuánto disparan pero no cuánto co-varían, y la coordinación "
         "se organiza según qué responde cada neurona, como ensambles. [Completar con IV.3 y IV.4.] Limitaciones: una "
         "sola sesión, sin conducta fina, potencia limitada para efectos chicos, y correlación no es conexión.")

# ---------------------------------------------------------------- orden final: GRACIAS al final
gracias = ids[-1]
lista.remove(gracias)
lista.append(gracias)
notas(prs.slides[len(prs.slides) - 1], "(10 s) Gracias. Quedamos para preguntas.")

# renumerar las partes (las diapositivas conservadas de la plantilla chocan con los nombres de las nuevas)
from pptx.opc.packuri import PackURI

for paso in ("tmp", "final"):                 # sólo las diapositivas: renombrar notas rompe el archivo
    for i, sl in enumerate(prs.slides, 1):
        sl.part.partname = PackURI(f"/ppt/slides/{'slide' if paso == 'final' else 'tmp'}{i}.xml")

prs.save(SALIDA)
print("Guardado:", SALIDA, "·", len(prs.slides), "diapositivas")

# ---------------------------------------------------------------- guión (mismas notas + tiempos + preguntas posibles)
import re

filas, cuerpo, total = [], [], 0
for i, sl in enumerate(prs.slides, 1):
    tit = sl.shapes.title.text_frame.text if sl.shapes.title is not None else ""
    if not tit:
        tit = next((sh.text_frame.text.split("\n")[0] for sh in sl.shapes if sh.has_text_frame and sh.text_frame.text.strip()), "")
    tit = tit.splitlines()[0] if tit else tit
    nota = sl.notes_slide.notes_text_frame.text if sl.has_notes_slide else ""
    m = re.match(r"\((\d+) (s|min)", nota)
    seg = (int(m.group(1)) * (60 if m.group(2) == "min" else 1)) if m else 0
    total += seg
    filas.append(f"| {i} | {tit} | {seg // 60}:{seg % 60:02d} | {total // 60}:{total % 60:02d} |")
    cuerpo.append(f"### {i} · {tit}\n\n{nota}\n")
GUION = RAIZ / "presentacion" / "guion.md"
GUION.write_text(
    "# Guión de la presentación (máx. 30 min)\n\n"
    "Las mismas notas están en las notas del orador de cada diapositiva. Entre corchetes, qué señalar.\n"
    "Se regenera con `presentacion/construir_presentacion.py`.\n\n"
    "## Tiempos\n\n| # | Diapositiva | Duración | Acumulado |\n|---|---|---|---|\n" + "\n".join(filas) +
    "\n\nLa Parte I (exploración neurona por neurona) está sólo en el notebook. Parte II ~1 min, Parte III ~6 min, "
    "Parte IV ~10 min (3 de ellos reservados para IV.3–IV.4), con margen para preguntas.\n\n"
    "## Texto por diapositiva\n\n" + "\n".join(cuerpo) +
    "\n## Preguntas que nos pueden hacer\n\n"
    "- **¿Por qué la línea de base a 0,5–2 s del inicio y no justo antes del contexto?** Porque el contexto se ve "
    "venir en la realidad virtual; justo antes de entrar ya hay anticipación (la vemos en la Parte II). Y antes del "
    "inicio está la ventana de respuesta del ensayo anterior (lamidos, agua).\n"
    "- **¿Un pico en el CCG prueba una sinapsis?** No. Es compatible con una conexión monosináptica (retardo de 1–4 ms, "
    "asimetría), pero también con entrada común con retardos distintos o con artefactos del spike sorting (una neurona "
    "partida en dos unidades). Por eso decimos «posible conexión funcional».\n"
    "- **¿Por qué la gaussiana hueca y no el shift predictor para los ms?** El shift predictor sólo saca lo que está "
    "atado al estímulo; la gaussiana hueca saca cualquier co-variación más lenta que ~10 ms (incluida la respiración), "
    "que es lo que queremos para hablar de conexiones. Para la escala lenta usamos el shift predictor.\n"
    "- **¿Cuántos falsos positivos esperan?** Con α = 10⁻⁴ por bin y ~16 bins testeados por par, "
    f"~{coma(R['fp_esperados'])} pares en total, muy por debajo de los {R['pares_sig']} encontrados.\n"
    "- **¿La anticipación del contexto no es movimiento?** Puede serlo en parte: en el contexto recompensado el ratón "
    "se frena. No tenemos velocidad, sólo el tiempo en el contexto como proxy. Lo marcamos como limitación.\n"
    "- **¿Por qué excluyeron neuronas?** Por baja tasa (< 0,5 Hz: los correlogramas quedan vacíos) o porque el sorting "
    "las pierde a mitad de sesión (aparecen en < 90 % de los ensayos). Igual están graficadas en la Parte I.\n"
    "- **¿Por qué el ritmo y no el espectro directamente?** El espectro del autocorrelograma es el espectro de potencia "
    "del tren de spikes (Wiener–Khinchin); lo hacemos desde la ACG porque es la herramienta de nuestra parte.\n"
    "- **¿No ver diferencia en r_sc prueba que el contexto no cambia la coordinación?** No: con nuestros ensayos sólo "
    f"descartamos cambios de r_sc de ~{coma(min(mdes), 3)} o más (el 95 % de las permutaciones queda por debajo). Además "
    "r_sc mide co-variación de ensayo a ensayo; la coordinación de milisegundos por contexto es IV.3.\n"
    "- **¿Por qué la ventana de olor es de 0,5 s?** En el contexto no recompensado el ratón sale ~0,5 s después de "
    "inhalar; con una ventana más larga compararíamos «dentro del contexto» contra «afuera».\n"
    "- **¿Por qué permutación y no un test t sobre los pares?** Los pares no son independientes (cada neurona está en 43 "
    "pares) y los grupos tienen distinto número de ensayos; permutar la etiqueta de contexto entre ensayos respeta ambas.\n"
    "- **¿Qué es la correlación de señal?** La correlación entre los PSTH promedio de dos neuronas en los cuatro tipos "
    "de ensayo: mide si responden a lo mismo con el mismo curso temporal. Mantel permuta las neuronas para testearla.\n",
    encoding="utf-8")
print("Guión:", GUION)
