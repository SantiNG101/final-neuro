# %% [markdown]
# # Trabajo final · Análisis de datos de corteza piriforme
#
# Datos: registros extracelulares de neuronas de corteza piriforme (PCx) de un ratón en la tarea
# olor–contexto–recompensa de **Federman, Romano et al. (2024, Nature Communications)**. Los datos ya vienen
# con spike sorting: para cada spike tenemos la neurona, el tiempo y la información del ensayo.
#
# Este notebook genera **todas las figuras de la presentación** (carpeta `figuras/`). Corre de punta a punta.
#
# | Parte | Contenido |
# |---|---|
# | 0 | Carga de datos, tabla de ensayos y control de calidad de neuronas |
# | I | Perfiles de respuesta: raster + PSTH por neurona, 4 alineaciones; clasificación de respuestas |
# | II | Actividad poblacional por tipo de ensayo |
# | III | Correlación neuronal: autocorrelogramas y cross-correlogramas |
# | IV | Análisis libre: ¿el contexto recompensado cambia la coordinación? (IV.1–IV.4 hechos; IV.5–IV.6 en el handoff) |
#
# **Convención de colores** (la de la consigna): OR·CR rojo, OR·CU naranja, OU·CR negro, OU·CU gris.
# Los ensayos sin olor (sólo contexto) van en azul (CR) y celeste (CU).

# %%
from pathlib import Path
import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch
from scipy import fft as sfft
from scipy import stats
from scipy.ndimage import gaussian_filter1d

warnings.filterwarnings("ignore", category=RuntimeWarning)

BASE = Path.cwd()
DATA = BASE / "MatrizFinal_8col.csv"
FIG = BASE / "figuras"
for sub in ["parte0", "parte1", "parte1/neuronas", "parte2", "parte3", "parte4"]:
    (FIG / sub).mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(2026)

# Paleta tomada de la presentación (tinta, gris, azul de acento, celeste de tarjetas)
TINTA, GRIS, ACENTO, CLARO = "#262425", "#666666", "#4A86E8", "#E6EEFC"
mpl.rcParams.update({
    "font.family": "Arial", "font.size": 10, "axes.titlesize": 10.5, "axes.labelsize": 10,
    "axes.edgecolor": TINTA, "axes.labelcolor": TINTA, "xtick.color": TINTA, "ytick.color": TINTA,
    "text.color": TINTA, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "legend.frameon": False,
    "figure.dpi": 110, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.facecolor": "white",
})

COLORES = {1: "#D62728", 2: "#FF8C1A", 3: "#111111", 4: "#9E9E9E", 5: ACENTO, 6: "#A9C4F5"}
ETIQ = {1: "OR·CR", 2: "OR·CU", 3: "OU·CR", 4: "OU·CU", 5: "CR sin olor", 6: "CU sin olor"}


def guardar(fig, nombre, cerrar=False):
    fig.savefig(FIG / nombre)
    if cerrar:
        plt.close(fig)


# %% [markdown]
# ## Parte 0 · Datos y control de calidad
#
# Cada fila del CSV es un spike: `neurona, t, ensayo, t_entrada, t_salida, t_inhal, tipo, t_inicio`.
# Los tiempos son **absolutos** (segundos desde el comienzo de la sesión), así que los ensayos son tramos contiguos de
# una única sesión continua. Eso permite calcular correlogramas sobre toda la sesión.

# %%
raw = pd.read_csv(DATA, header=None,
                  names=["neurona", "t", "ensayo", "t_entrada", "t_salida", "t_inhal", "tipo", "t_inicio"])
T_SESION = raw.t.max()

trials = (raw.groupby("ensayo")[["t_inicio", "t_entrada", "t_salida", "t_inhal", "tipo"]].first()
          .astype({"tipo": int}))
trials["dur_contexto"] = trials.t_salida - trials.t_entrada        # proxy de la velocidad del animal
trials["lat_inhal"] = trials.t_inhal - trials.t_entrada           # entrada -> primera inhalación del olor
trials["anomalo"] = trials.lat_inhal < 0                          # inhalación antes de entrar: se excluye
spikes = {int(n): np.sort(g.t.values) for n, g in raw.groupby("neurona")}
NEURONAS = sorted(spikes)

print(f"{len(raw):,} spikes · {len(NEURONAS)} neuronas · {len(trials)} ensayos · sesión de {T_SESION/60:.1f} min")
print(trials.tipo.map(ETIQ).value_counts().reindex(ETIQ.values()).to_string())
print("Ensayos anómalos (inhalación antes de la entrada):", list(trials.index[trials.anomalo]))
print(trials[["dur_contexto", "lat_inhal"]].describe().round(2).to_string())

# %% [markdown]
# **Control de calidad por neurona.** Calculamos la tasa media, la fracción de ensayos en los que la neurona dispara
# (si se "pierde" a mitad de sesión, el spike sorting no la siguió) y el % de intervalos entre spikes (ISI) < 2 ms,
# que una sola neurona no puede producir por el período refractario (si es alto, la unidad puede ser multi-unidad).
#
# Criterio de **neurona estable** para análisis poblacionales y de correlación: tasa ≥ 0,5 Hz y presente en ≥ 90 % de
# los ensayos. Las demás se grafican en la Parte I pero no entran en los promedios ni en los pares.

# %%
pres = raw.groupby("neurona").ensayo.nunique()
neur = pd.DataFrame(index=pd.Index(NEURONAS, name="neurona"))
neur["n_spikes"] = [len(spikes[n]) for n in NEURONAS]
neur["tasa_hz"] = neur.n_spikes / T_SESION
neur["frac_ensayos"] = pres.reindex(NEURONAS).values / len(trials)
neur["isi_viol_pct"] = [100 * np.mean(np.diff(spikes[n]) < 0.002) for n in NEURONAS]
neur["estable"] = (neur.tasa_hz >= 0.5) & (neur.frac_ensayos >= 0.9)
ESTABLES = list(neur.index[neur.estable])
print(f"Neuronas estables: {len(ESTABLES)} de {len(NEURONAS)}  ->  {len(ESTABLES)*(len(ESTABLES)-1)//2} pares")
print(f"ISI<2ms en estables: mediana {neur.loc[ESTABLES,'isi_viol_pct'].median():.2f} %, "
      f"máx {neur.loc[ESTABLES,'isi_viol_pct'].max():.2f} %")

# Tasa por ensayo (para ver estabilidad a lo largo de la sesión)
inicio, fin = trials.t_inicio.values, np.r_[trials.t_inicio.values[1:], T_SESION]
tasa_ensayo = np.array([(np.searchsorted(spikes[n], fin) - np.searchsorted(spikes[n], inicio)) / (fin - inicio)
                        for n in NEURONAS])

# %%
fig = plt.figure(figsize=(10, 3.4))
gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1.5, 1.1], wspace=0.35)

ax = fig.add_subplot(gs[0])
orden = neur.sort_values("tasa_hz").index
ax.barh(range(len(orden)), neur.loc[orden, "tasa_hz"],
        color=[ACENTO if neur.loc[n, "estable"] else "#C8C8C8" for n in orden], height=0.8)
ax.set_xscale("log"); ax.set_yticks([]); ax.set_xlabel("Tasa media (Hz, escala log)")
ax.axvline(0.5, color=TINTA, lw=0.8, ls="--")
ax.set_title(f"A · {len(ESTABLES)} de {len(NEURONAS)} neuronas son estables")
ax.text(0.98, 0.04, "azul: estable\ngris: descartada", transform=ax.transAxes, ha="right", fontsize=8, color=GRIS)

ax = fig.add_subplot(gs[1])
norm = tasa_ensayo[[NEURONAS.index(n) for n in orden]]
norm = norm / np.maximum(norm.max(1, keepdims=True), 1e-9)
ax.imshow(norm, aspect="auto", cmap="Blues", interpolation="nearest", origin="lower")
ax.set_xlabel("Ensayo"); ax.set_ylabel("Neuronas (ordenadas por tasa)"); ax.set_yticks([])
ax.set_title("B · Algunas unidades se pierden a mitad de sesión")

ax = fig.add_subplot(gs[2])
for k in [1, 2, 3, 4, 5, 6]:
    d = trials.loc[trials.tipo == k, "dur_contexto"]
    x = k + RNG.uniform(-0.18, 0.18, len(d))
    ax.scatter(x, d, s=7, color=COLORES[k], alpha=0.7, lw=0)
    ax.hlines(d.median(), k - 0.3, k + 0.3, color=TINTA, lw=1.5)
ax.set_yscale("log"); ax.set_xticks(range(1, 7)); ax.set_xticklabels([ETIQ[k] for k in range(1, 7)], rotation=45, ha="right")
ax.set_ylabel("Tiempo en el contexto (s, log)")
ax.set_title("C · Proxy conductual")
guardar(fig, "parte0/control_calidad.png")
plt.show()

# Versión grande del proxy conductual para la diapositiva
fig, ax = plt.subplots(figsize=(4.3, 3.2))
for k in [1, 2, 3, 4, 5, 6]:
    d = trials.loc[trials.tipo == k, "dur_contexto"]
    ax.scatter(k + RNG.uniform(-0.18, 0.18, len(d)), d, s=12, color=COLORES[k], alpha=0.75, lw=0)
    ax.hlines(d.median(), k - 0.32, k + 0.32, color=TINTA, lw=2)
ax.set_yscale("log"); ax.set_xticks(range(1, 7))
ax.set_xticklabels([ETIQ[k].replace(" sin olor", "\nsin olor") for k in range(1, 7)], fontsize=8.5)
ax.set_ylabel("Tiempo en el contexto (s, escala log)")
ax.axvspan(0.5, 1.5, color=CLARO, zorder=0); ax.axvspan(2.5, 3.5, color=CLARO, zorder=0); ax.axvspan(4.5, 5.5, color=CLARO, zorder=0)
ax.text(0.02, 0.98, "fondo celeste: contexto recompensado", transform=ax.transAxes, fontsize=7.5, color=GRIS, va="top")
guardar(fig, "parte0/comportamiento.png")
plt.show()

print("Mediana del tiempo en el contexto por tipo (s):")
print(trials.groupby(trials.tipo.map(ETIQ)).dur_contexto.median().round(2).to_string())

# %% [markdown]
# ## Utilidades: alinear spikes a eventos, conteos y PSTH
#
# - `alinear`: para cada evento, los tiempos de spike relativos a él dentro de una ventana.
# - `conteos`: matriz ensayos × bins.
# - `psth`: tasa promedio (Hz) suavizada con un núcleo gaussiano (σ = 30 ms por defecto).
#
# Alineaciones pedidas: inicio del ensayo, entrada al contexto, primera inhalación del olor y salida del contexto.
# La alineación a la inhalación sólo existe para los tipos 1–4 (los tipos 5–6 no tienen olor).

# %%
ALIN = {
    "inicio": ("t_inicio", (-1.0, 4.0), "Inicio del ensayo"),
    "entrada": ("t_entrada", (-2.0, 3.0), "Entrada al contexto"),
    "inhalacion": ("t_inhal", (-2.0, 3.0), "Primera inhalación del olor"),
    "salida": ("t_salida", (-2.0, 3.0), "Salida del contexto"),
}
TIPOS_OLOR = [1, 2, 3, 4]
VALIDOS = trials[~trials.anomalo]


def alinear(spk, eventos, ventana):
    lo = np.searchsorted(spk, eventos + ventana[0])
    hi = np.searchsorted(spk, eventos + ventana[1])
    return [spk[a:b] - e for a, b, e in zip(lo, hi, eventos)]


def conteos(spk, eventos, ventana, ancho):
    edges = np.arange(ventana[0], ventana[1] + ancho / 2, ancho)
    rel = alinear(spk, eventos, ventana)
    return np.array([np.histogram(r, edges)[0] for r in rel]), edges


def psth(spk, eventos, ventana, ancho=0.01, sigma=0.03):
    C, edges = conteos(spk, eventos, ventana, ancho)
    r = C.mean(0) / ancho
    return gaussian_filter1d(r, sigma / ancho), edges[:-1] + ancho / 2


def ensayos_para(alin, tipos=(1, 2, 3, 4, 5, 6)):
    tr = VALIDOS[VALIDOS.tipo.isin(tipos)]
    if alin == "inhalacion":
        tr = tr[tr.tipo.isin(TIPOS_OLOR)]
    return tr.sort_values(["tipo"], kind="stable")


def tasa_ventana(spk, eventos, a, b):
    return (np.searchsorted(spk, eventos + b) - np.searchsorted(spk, eventos + a)) / (b - a)


# %% [markdown]
# ## Parte I · Perfiles de respuesta neuronal
#
# Para cada neurona: raster (cada fila un ensayo, agrupados por tipo y coloreados) y PSTH por tipo de ensayo, con las
# cuatro alineaciones. En el raster alineado a la entrada marcamos con un punto la salida de cada ensayo: el tiempo en el
# contexto varía mucho entre ensayos porque depende de la velocidad del animal.
#
# Se exportan las 64 neuronas a `figuras/parte1/neuronas/`.

# %%
def fig_neurona(nid, alineaciones=tuple(ALIN), figsize=None, titulo=True):
    n = len(alineaciones)
    fig, axs = plt.subplots(2, n, figsize=figsize or (3.2 * n, 4.8), sharex="col",
                            gridspec_kw=dict(height_ratios=[1.5, 1], hspace=0.08, wspace=0.28), squeeze=False)
    for j, alin in enumerate(alineaciones):
        col, ven, nombre = ALIN[alin]
        tr = ensayos_para(alin)
        ev = tr[col].values
        rel = alinear(spikes[nid], ev, ven)
        ax = axs[0, j]
        fila, y0 = np.zeros(len(tr)), 0
        for k in sorted(tr.tipo.unique()):
            idx = np.where(tr.tipo.values == k)[0]
            fila[idx] = y0 + np.arange(len(idx))
            xs = np.concatenate([rel[i] for i in idx]) if len(idx) else np.array([])
            ys = np.concatenate([np.full(len(rel[i]), fila[i]) for i in idx]) if len(idx) else np.array([])
            ax.scatter(xs, ys, marker="|", s=3, lw=0.45, color=COLORES[k], rasterized=True)
            y0 += len(idx) + 4
        if alin == "entrada":
            sal = tr.t_salida.values - ev
            m = sal < ven[1]
            ax.scatter(sal[m], fila[m], s=2.5, color=ACENTO, zorder=3, lw=0)
        ax.axvline(0, color=TINTA, lw=0.7, ls="--")
        ax.set_ylim(-2, y0); ax.set_yticks([])
        ax.set_title(nombre, fontsize=9)
        ax.spines["left"].set_visible(False)
        ax2 = axs[1, j]
        for k in sorted(tr.tipo.unique()):
            r, tc = psth(spikes[nid], tr.loc[tr.tipo == k, col].values, ven)
            ax2.plot(tc, r, color=COLORES[k], lw=1.2 if k <= 4 else 0.9, ls="-" if k <= 4 else "--", label=ETIQ[k])
        ax2.axvline(0, color=TINTA, lw=0.7, ls="--")
        ax2.set_xlabel("Tiempo (s)")
        if j == 0:
            ax2.set_ylabel("Tasa (Hz)")
            axs[0, 0].set_ylabel("Ensayos por tipo")
    axs[1, -1].legend(fontsize=7, loc="upper right", ncol=1, handlelength=1.5)
    if titulo:
        fig.suptitle(f"Neurona {nid} · {neur.loc[nid, 'tasa_hz']:.1f} Hz" +
                     ("" if neur.loc[nid, "estable"] else " · (no estable)"), x=0.01, ha="left", fontweight="bold")
    return fig


for nid in NEURONAS:
    f = fig_neurona(nid)
    f.savefig(FIG / f"parte1/neuronas/neurona_{nid:02d}.png", dpi=150)
    plt.close(f)
print("Exportadas", len(NEURONAS), "figuras de neuronas")

# %% [markdown]
# ### Clasificación de respuestas
#
# Ventanas (justificación):
# - **Línea de base**: 0,5–2 s después del inicio del ensayo. El animal ya corre por el corredor, lejos del contexto, y
#   no se mezcla con la ventana de respuesta/recompensa del ensayo anterior.
# - **Contexto (anticipación)**: de −0,5 a +0,3 s respecto de la entrada. El contexto ya es visible y el olor todavía no
#   se inhaló (la primera inhalación llega ≥ 0,32 s después de entrar).
# - **Olor**: 0–1 s después de la primera inhalación (dura lo que el pulso de olor).
# - **Salida / recompensa**: 0–1,5 s después de salir del contexto (ventana de respuesta: lamidos y agua en OR·CR).
#
# Tests (por neurona, α = 0,01):
# 1. **Responde al olor**: Wilcoxon pareado, tasa en la ventana de olor vs línea de base del mismo ensayo → excitada o inhibida.
# 2. **Selectiva al olor**: Mann–Whitney, OR (tipos 1, 2) vs OU (3, 4) en la ventana de olor.
# 3. **Selectiva al contexto**: Mann–Whitney, CR (1, 3, 5) vs CU (2, 4, 6) en la ventana de anticipación.
# 4. **Selectiva a la recompensa**: Mann–Whitney, OR·CR vs OU·CR en la ventana de salida. Comparamos sólo dentro del
#    contexto recompensado porque en el contexto no recompensado el ratón sale a los ~0,9 s y la ventana de salida
#    todavía contiene la respuesta al olor; en OR·CR y OU·CR la salida llega cuando esa respuesta ya terminó.
#
# Con ~45 neuronas y α = 0,01 esperamos < 1 falso positivo por test. Ojo: la selectividad al contexto puede estar
# confundida con la velocidad (en el contexto recompensado el ratón se frena; ver Parte 0).

# %%
VEN = {"base": ("t_inicio", 0.5, 2.0), "contexto": ("t_entrada", -0.5, 0.3),
       "olor": ("t_inhal", 0.0, 1.0), "salida": ("t_salida", 0.0, 1.5)}
ALFA = 0.01
tr_olor = VALIDOS[VALIDOS.tipo.isin(TIPOS_OLOR)]


def clasificar(nid):
    s = spikes[nid]
    out = {}
    b = tasa_ventana(s, tr_olor.t_inicio.values, 0.5, 2.0)
    o = tasa_ventana(s, tr_olor.t_inhal.values, 0.0, 1.0)
    try:
        p = stats.wilcoxon(o, b).pvalue
    except ValueError:
        p = 1.0
    out["resp_olor"] = ("excitada" if o.mean() > b.mean() else "inhibida") if p < ALFA else "sin respuesta"
    out["d_olor_hz"] = o.mean() - b.mean()
    ty = tr_olor.tipo.values
    out["sel_olor"] = stats.mannwhitneyu(o[np.isin(ty, [1, 2])], o[np.isin(ty, [3, 4])]).pvalue < ALFA
    c = tasa_ventana(s, VALIDOS.t_entrada.values, -0.5, 0.3)
    tv = VALIDOS.tipo.values
    out["sel_contexto"] = stats.mannwhitneyu(c[np.isin(tv, [1, 3, 5])], c[np.isin(tv, [2, 4, 6])]).pvalue < ALFA
    sa = tasa_ventana(s, tr_olor.t_salida.values, 0.0, 1.5)
    out["sel_recompensa"] = stats.mannwhitneyu(sa[ty == 1], sa[ty == 3]).pvalue < ALFA
    return out


clas = pd.DataFrame.from_dict({n: clasificar(n) for n in ESTABLES}, orient="index")
clas = clas.astype({"sel_olor": bool, "sel_contexto": bool, "sel_recompensa": bool, "d_olor_hz": float})
clas["n_variables"] = clas[["sel_olor", "sel_contexto", "sel_recompensa"]].sum(1).astype(int)
neur = neur.join(clas)
print(clas.resp_olor.value_counts().to_string())
print(clas[["sel_olor", "sel_contexto", "sel_recompensa"]].sum().to_string())
print("Selectivas a 0/1/2/3 variables:", clas.n_variables.value_counts().sort_index().to_dict())

# %% [markdown]
# ### Normalización (z-score respecto de la línea de base) y mapa de toda la población
#
# Para comparar neuronas con tasas muy distintas, cada PSTH se expresa en unidades de la variabilidad de la línea de base
# de esa neurona: z = (PSTH − μ_base) / σ_base, con μ y σ de la tasa en bins de 100 ms de la ventana de base (todos los ensayos).

# %%
ANCHO_POB, SIGMA_POB = 0.02, 0.04
zbase = {}
for n in ESTABLES:
    Cb, _ = conteos(spikes[n], VALIDOS.t_inicio.values, (0.5, 2.0), 0.1)
    rb = Cb.ravel() / 0.1
    zbase[n] = (rb.mean(), max(rb.std(), 1e-6))

POB = {}   # POB[alin][tipo] -> (n_neuronas, n_bins) en z
TC = {}
for alin, (col, ven, _) in ALIN.items():
    POB[alin] = {}
    tr = ensayos_para(alin)
    for k in sorted(tr.tipo.unique()):
        ev = tr.loc[tr.tipo == k, col].values
        filas = []
        for n in ESTABLES:
            r, tc = psth(spikes[n], ev, ven, ANCHO_POB, SIGMA_POB)
            filas.append((r - zbase[n][0]) / zbase[n][1])
        POB[alin][k] = np.array(filas)
        TC[alin] = tc

# %%
tc = TC["inhalacion"]
m_resp = (tc >= 0) & (tc <= 1)
orden = np.argsort(-POB["inhalacion"][1][:, m_resp].mean(1))
ver = (tc >= -1) & (tc <= 2)
fig, axs = plt.subplots(1, 4, figsize=(10, 3.6), sharey=True)
for ax, k in zip(axs, TIPOS_OLOR):
    im = ax.imshow(POB["inhalacion"][k][orden][:, ver], aspect="auto", cmap="RdBu_r", vmin=-2.5, vmax=2.5,
                   extent=[tc[ver][0], tc[ver][-1], len(ESTABLES), 0], interpolation="nearest")
    ax.axvline(0, color=TINTA, lw=0.8, ls="--")
    ax.set_title(ETIQ[k], color=COLORES[k] if k != 4 else GRIS)
    ax.set_xlabel("Tiempo desde la inhalación (s)")
axs[0].set_ylabel("Neuronas (ordenadas por respuesta en OR·CR)")
cb = fig.colorbar(im, ax=axs, fraction=0.025, pad=0.02)
cb.set_label("z respecto de la base")
guardar(fig, "parte1/mapa_poblacion_inhalacion.png")
plt.show()

# %%
fig, axs = plt.subplots(1, 2, figsize=(7.5, 2.8), gridspec_kw=dict(width_ratios=[1, 1.25], wspace=0.45))
ax = axs[0]
cats = ["excitada", "inhibida", "sin respuesta"]
vals = [int((clas.resp_olor == c).sum()) for c in cats]
ax.barh(cats[::-1], vals[::-1], color=[GRIS, TINTA, ACENTO][::-1] if False else ["#C8C8C8", TINTA, ACENTO])
for i, v in enumerate(vals[::-1]):
    ax.text(v + 0.3, i, str(v), va="center")
ax.set_xlabel("Neuronas"); ax.set_title("Respuesta al olor")
ax = axs[1]
etq = ["Olor", "Contexto\n(antes del olor)", "Recompensa\n(salida)"]
vals = clas[["sel_olor", "sel_contexto", "sel_recompensa"]].sum().values
ax.bar(etq, vals, color=ACENTO, width=0.6)
for i, v in enumerate(vals):
    ax.text(i, v + 0.3, f"{v}", ha="center")
ax.set_ylabel("Neuronas selectivas"); ax.set_title("¿A qué variable es selectiva?")
ax.set_ylim(0, max(vals) * 1.25 + 1)
guardar(fig, "parte1/clasificacion.png")
plt.show()

# %% [markdown]
# ### Neuronas de ejemplo para la presentación
# Elegimos automáticamente: la más excitada por el olor con selectividad, la más inhibida, y una selectiva a la recompensa.

# %%
cand = clas[clas.resp_olor == "excitada"].copy()
cand["score"] = cand.d_olor_hz.astype(float) * (1 + cand.n_variables)
EJ_EXC = int(cand.score.idxmax())
EJ_INH = int(clas[clas.resp_olor == "inhibida"].d_olor_hz.astype(float).idxmin()) if (clas.resp_olor == "inhibida").any() else ESTABLES[0]
rec = clas[(clas.sel_recompensa) & (~clas.index.isin([EJ_EXC, EJ_INH]))]
EJ_REC = int(rec.d_olor_hz.astype(float).abs().idxmin()) if len(rec) else ESTABLES[1]
print("Ejemplos -> excitada:", EJ_EXC, "inhibida:", EJ_INH, "recompensa:", EJ_REC)
for nombre, nid in [("excitada", EJ_EXC), ("inhibida", EJ_INH), ("recompensa", EJ_REC)]:
    f = fig_neurona(nid, alineaciones=("entrada", "inhalacion", "salida"), figsize=(8.6, 4.2))
    guardar(f, f"parte1/ejemplo_{nombre}.png")
    plt.show() if nombre == "excitada" else plt.close(f)

# %% [markdown]
# ## Parte II · Actividad poblacional
#
# Promedio de las neuronas estables (z-score) por tipo de ensayo, ± error estándar entre neuronas. Promediar todas juntas
# cancela excitaciones con inhibiciones, por eso mostramos también las excitadas y las inhibidas por el olor por separado.

# %%
GRUPOS = {"Todas las estables": np.ones(len(ESTABLES), bool),
          "Excitadas por el olor": (clas.resp_olor == "excitada").values,
          "Inhibidas por el olor": (clas.resp_olor == "inhibida").values}


def panel_pob(ax, alin, mascara, tipos=None, leyenda=False):
    tc = TC[alin]
    for k in (tipos or sorted(POB[alin])):
        Z = POB[alin][k][mascara]
        if len(Z) == 0:
            continue
        m, e = Z.mean(0), Z.std(0, ddof=1) / np.sqrt(len(Z)) if len(Z) > 1 else np.zeros(Z.shape[1])
        ax.fill_between(tc, m - e, m + e, color=COLORES[k], alpha=0.18, lw=0)
        ax.plot(tc, m, color=COLORES[k], lw=1.3 if k <= 4 else 1.0, ls="-" if k <= 4 else "--", label=ETIQ[k])
    ax.axvline(0, color=TINTA, lw=0.7, ls="--"); ax.axhline(0, color="#BBBBBB", lw=0.6)
    if leyenda:
        ax.legend(fontsize=7, loc="upper right")


fig, axs = plt.subplots(3, 4, figsize=(12, 7.5), sharex="col")
for i, (g, mk) in enumerate(GRUPOS.items()):
    for j, alin in enumerate(ALIN):
        panel_pob(axs[i, j], alin, mk, leyenda=(i == 0 and j == 3))
        if i == 0:
            axs[i, j].set_title(ALIN[alin][2])
        if j == 0:
            axs[i, j].set_ylabel(f"{g}\n(n = {mk.sum()})  z")
        if i == 2:
            axs[i, j].set_xlabel("Tiempo (s)")
guardar(fig, "parte2/poblacion_completa.png")
plt.show()

# %%
# Versión para la diapositiva: inhalación (excitadas / inhibidas) + entrada (todas, con ensayos sin olor)
fig, axs = plt.subplots(1, 3, figsize=(10, 3.0), gridspec_kw=dict(wspace=0.3))
panel_pob(axs[0], "entrada", GRUPOS["Todas las estables"], leyenda=False)
axs[0].set_title(f"Todas (n = {len(ESTABLES)}) · entrada al contexto"); axs[0].set_ylabel("z (media ± EE)")
panel_pob(axs[1], "inhalacion", GRUPOS["Excitadas por el olor"])
axs[1].set_title(f"Excitadas (n = {GRUPOS['Excitadas por el olor'].sum()}) · inhalación")
panel_pob(axs[2], "inhalacion", GRUPOS["Inhibidas por el olor"], leyenda=True)
axs[2].set_title(f"Inhibidas (n = {GRUPOS['Inhibidas por el olor'].sum()}) · inhalación")
for ax in axs:
    ax.set_xlabel("Tiempo (s)"); ax.set_xlim(-1.5, 2.5)
guardar(fig, "parte2/poblacion_slide.png")
plt.show()

# %% [markdown]
# **Cuantificación.** Respuesta media (z en 0–1 s post inhalación) de las neuronas excitadas, por tipo de ensayo.
# La comparación clave es **mismo olor, distinto contexto** (OR·CR vs OR·CU y OU·CR vs OU·CU): si difieren, el contexto
# modula la respuesta al olor. Test de Wilcoxon pareado entre neuronas.

# %%
def resp_media(alin, k, mascara, a=0.0, b=1.0):
    tc = TC[alin]
    return POB[alin][k][mascara][:, (tc >= a) & (tc <= b)].mean(1)


mk = GRUPOS["Excitadas por el olor"]
R = {k: resp_media("inhalacion", k, mk) for k in TIPOS_OLOR}
p_or = stats.wilcoxon(R[1], R[2]).pvalue
p_ou = stats.wilcoxon(R[3], R[4]).pvalue
p_od = stats.wilcoxon((R[1] + R[2]) / 2, (R[3] + R[4]) / 2).pvalue
print(f"OR·CR vs OR·CU p = {p_or:.3g} | OU·CR vs OU·CU p = {p_ou:.3g} | OR vs OU p = {p_od:.3g}")

fig, ax = plt.subplots(figsize=(3.6, 2.8))
for i, k in enumerate(TIPOS_OLOR):
    ax.bar(i, R[k].mean(), yerr=R[k].std(ddof=1) / np.sqrt(len(R[k])), color=COLORES[k], width=0.65,
           error_kw=dict(lw=1, capsize=3))
for a_, b_ in [(R[1], R[2])]:
    for va, vb in zip(a_, b_):
        ax.plot([0, 1], [va, vb], color="#CCCCCC", lw=0.5, zorder=0)
for va, vb in zip(R[3], R[4]):
    ax.plot([2, 3], [va, vb], color="#CCCCCC", lw=0.5, zorder=0)
ax.set_xticks(range(4)); ax.set_xticklabels([ETIQ[k] for k in TIPOS_OLOR])
ax.set_ylabel("Respuesta al olor (z, 0–1 s)")


def p_txt(p):
    return "p < 0,001" if p < 0.001 else f"p = {p:.3f}".replace(".", ",")


def coma_py(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


top = max(R[k].mean() + R[k].std(ddof=1) / np.sqrt(len(R[k])) for k in TIPOS_OLOR)
ax.text(0.5, top * 1.08, p_txt(p_or), ha="center", fontsize=8)
ax.text(2.5, top * 1.08, p_txt(p_ou), ha="center", fontsize=8)
ax.set_title("Excitadas: respuesta por tipo")
guardar(fig, "parte2/respuesta_por_tipo.png")
plt.show()

# %% [markdown]
# ## Parte III · Correlación neuronal
#
# **Correlograma**: histograma de las diferencias de tiempo entre los spikes de una neurona A y los de una neurona B
# (cross-correlograma, CCG) o de una neurona consigo misma (autocorrelograma, ACG). Se calcula sobre toda la sesión
# (spikes en tiempo absoluto). Lo expresamos como **tasa condicional**: la tasa de B (Hz) en función del tiempo desde
# un spike de A.

# %%
def correlograma(a, b, ventana, ancho, auto=False):
    """Conteos de (b - a) en bins centrados en 0, entre -ventana y +ventana."""
    nb = int(round(ventana / ancho))
    edges = (np.arange(-nb, nb + 2) - 0.5) * ancho
    lo = np.searchsorted(b, a + edges[0])
    hi = np.searchsorted(b, a + edges[-1])
    n = hi - lo
    if n.sum() == 0:
        return np.zeros(len(edges) - 1), edges[:-1] + ancho / 2
    idx = np.repeat(np.arange(len(a)), n)
    offs = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
    d = b[np.repeat(lo, n) + offs] - a[idx]
    if auto:
        d = d[d != 0]
    k = np.floor((d - edges[0]) / ancho).astype(np.int64)        # bins uniformes: bincount es mucho más rápido
    k = k[(k >= 0) & (k < len(edges) - 1)]
    return np.bincount(k, minlength=len(edges) - 1).astype(float), edges[:-1] + ancho / 2


# %% [markdown]
# ### III.a · Autocorrelogramas
#
# Dos escalas:
# - **Corta (±50 ms, bins de 1 ms)**: período refractario (hueco en 0) y disparo en ráfagas (*bursts*: pico a 2–10 ms).
#   Índice de burst = tasa a 2–10 ms / tasa a 40–50 ms.
# - **Larga (±1 s, bins de 10 ms)**: ritmicidad. Por el teorema de Wiener–Khinchin, el espectro del ACG es el espectro de
#   potencia del tren de spikes. Le sacamos la tendencia lenta (filtro pasa-altos: ACG − ACG suavizado con σ = 100 ms) y
#   medimos qué fracción de la potencia entre 1 y 30 Hz cae en **2–8 Hz** (rango de la respiración/olfateo del ratón).
#
# **Control (surrogate)**: para saber si esa fracción es mayor que lo esperable por azar, recalculamos el índice sobre
# trenes con *jitter por intervalos* de 500 ms (cada spike se mueve al azar dentro de su ventana de 500 ms). Eso conserva la
# modulación lenta por la tarea (> 0,5 s) y destruye cualquier ritmo de 2–8 Hz. Una neurona es **rítmica** si su índice
# supera al de los 25 surrogates por z > 3. (La ACG larga se calcula con la FFT del tren binneado: es la misma cuenta,
# mucho más rápida.)

# %%
def jitter_intervalo(spk, delta, rng):
    return np.sort(np.floor(spk / delta) * delta + rng.uniform(0, delta, len(spk)))


def indice_ritmo(acg_larga, lags, ancho=0.01):
    pos = lags > 0.01
    x = acg_larga[pos]
    x = x - gaussian_filter1d(x, 0.1 / ancho, mode="nearest")
    x = x * np.hanning(len(x))
    nfft = 4096
    P = np.abs(np.fft.rfft(x, nfft)) ** 2
    f = np.fft.rfftfreq(nfft, ancho)
    tot = P[(f >= 1) & (f <= 30)].sum()
    banda = (f >= 2) & (f <= 8)
    return P[banda].sum() / tot, f[banda][np.argmax(P[banda])], f, P


def acg_larga(spk, ancho=0.01, maxlag=1.0):
    """ACG de escala larga vía FFT del tren binneado (mismo resultado que contar diferencias, mucho más rápido)."""
    nb = int(np.ceil(T_SESION / ancho)) + 1
    x = np.bincount((spk / ancho).astype(np.int64), minlength=nb).astype(np.float32)
    K = int(round(maxlag / ancho))
    nfft = sfft.next_fast_len(len(x) + K + 1, real=True)
    F = sfft.rfft(x, nfft, workers=-1)
    ac = sfft.irfft(F * np.conj(F), nfft, workers=-1)[:K + 1].astype(float)
    ac[0] -= x.sum()                      # quita cada spike consigo mismo
    lags = np.arange(K + 1) * ancho
    return np.r_[ac[:0:-1], ac], np.r_[-lags[:0:-1], lags]


N_SURR = 25
acg = {}
for n in ESTABLES:
    s = spikes[n]
    c_corta, lag_c = correlograma(s, s, 0.05, 0.001, auto=True)
    c_larga, lag_l = acg_larga(s)
    corta = c_corta / (len(s) * 0.001)
    larga = c_larga / (len(s) * 0.01)
    ri, fpico, _, _ = indice_ritmo(larga, lag_l)
    surr = []
    for _ in range(N_SURR):
        cj, _ = acg_larga(jitter_intervalo(s, 0.5, RNG))
        surr.append(indice_ritmo(cj / (len(s) * 0.01), lag_l)[0])
    surr = np.array(surr)
    base_c = corta[(np.abs(lag_c) >= 0.04)].mean()
    acg[n] = dict(corta=corta, larga=larga, ritmo=ri, f_pico=fpico,
                  z_ritmo=(ri - surr.mean()) / max(surr.std(ddof=1), 1e-9),
                  burst=corta[(np.abs(lag_c) >= 0.002) & (np.abs(lag_c) <= 0.01)].mean() / max(base_c, 1e-9),
                  refrac=corta[np.abs(lag_c) <= 0.0015].mean() / max(base_c, 1e-9))
LAG_C, LAG_L = lag_c, lag_l
A = pd.DataFrame({n: {k: v for k, v in d.items() if k not in ("corta", "larga")} for n, d in acg.items()}).T.astype(float)
A["ritmica"] = A.z_ritmo > 3
A["bursty"] = A.burst > 1.5
neur = neur.join(A)
print(f"Rítmicas (2–8 Hz, z>3): {A.ritmica.sum()} de {len(A)} | frecuencia pico mediana {A.loc[A.ritmica,'f_pico'].median():.1f} Hz")
print(f"Con ráfagas (índice > 1,5): {A.bursty.sum()} de {len(A)}")

# %%
# Ejemplos: la más rítmica, la más bursty (no rítmica) y una "plana"
ej_r = A.z_ritmo.idxmax()
ej_b = A[~A.index.isin([ej_r])].burst.idxmax()
plano = A[(~A.ritmica) & (~A.bursty)]
ej_p = (plano.z_ritmo.abs() + (plano.burst - 1).abs()).idxmin() if len(plano) else A.z_ritmo.idxmin()
EJ_ACG = [int(ej_r), int(ej_b), int(ej_p)]
desc = {int(ej_r): f"rítmica (~{coma_py(A.loc[ej_r, 'f_pico'])} Hz)", int(ej_b): "en ráfagas", int(ej_p): "no rítmica"}

fig = plt.figure(figsize=(10, 4.4))
gs = fig.add_gridspec(2, 4, width_ratios=[1, 1, 1, 1.35], hspace=0.55, wspace=0.4)
for j, n in enumerate(EJ_ACG):
    ax = fig.add_subplot(gs[0, j])
    ax.bar(LAG_C * 1e3, acg[n]["corta"], width=1.0, color=TINTA, lw=0)
    ax.set_title(f"N{n} · {desc[n]}", fontsize=9)
    ax.set_xlabel("Lag (ms)")
    if j == 0:
        ax.set_ylabel("Tasa cond. (Hz)")
    ax = fig.add_subplot(gs[1, j])
    yl = gaussian_filter1d(acg[n]["larga"], 1)
    lejos = np.abs(LAG_L) >= 0.05
    ax.plot(LAG_L, yl, color=ACENTO, lw=1)
    ax.set_ylim(yl[lejos].min() * 0.95, yl[lejos].max() * 1.05)   # el pico central no deja ver el ritmo
    ax.set_xlabel("Lag (s)")
    if j == 0:
        ax.set_ylabel("Tasa cond. (Hz)")
ax = fig.add_subplot(gs[:, 3])
orden = A.sort_values("z_ritmo", ascending=False).index
M = []
sel = LAG_L >= 0.05
for n in orden:
    x = gaussian_filter1d(acg[n]["larga"], 1)[sel]
    x = x - gaussian_filter1d(x, 10, mode="nearest")
    M.append(x / max(np.abs(x).max(), 1e-9))
im = ax.imshow(np.array(M), aspect="auto", cmap="RdBu_r", vmin=-1, vmax=1,
               extent=[0.05, 1, len(orden), 0], interpolation="nearest")
nr = int(A.ritmica.sum())
ax.axhline(nr, color=TINTA, lw=1, ls="--")
ax.text(0.97, nr / 2, "rítmicas", ha="right", va="center", fontsize=8, fontweight="bold",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.8))
ax.set_xlabel("Lag (s)"); ax.set_ylabel("Neuronas (ordenadas por ritmicidad)")
ax.set_title("ACG sin tendencia lenta")
guardar(fig, "parte3/autocorrelogramas.png")
plt.show()

# %%
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.6), gridspec_kw=dict(wspace=0.4))
ax = axs[0]
ax.hist(A.loc[A.ritmica, "f_pico"], bins=np.arange(2, 8.5, 0.5), color=ACENTO, edgecolor="white")
ax.hist(A.loc[~A.ritmica, "f_pico"], bins=np.arange(2, 8.5, 0.5), color="#C8C8C8", edgecolor="white", alpha=0.8)
ax.set_xlabel("Frecuencia pico en 2–8 Hz"); ax.set_ylabel("Neuronas")
ax.set_title("Frecuencia del ritmo")
ax = axs[1]
ax.scatter(A.z_ritmo, A.burst, c=[ACENTO if r else "#AAAAAA" for r in A.ritmica], s=16, lw=0)
ax.axvline(3, color=TINTA, ls="--", lw=0.7); ax.axhline(1.5, color=TINTA, ls=":", lw=0.7)
ax.set_xlabel("Ritmicidad (z vs surrogates)"); ax.set_ylabel("Índice de burst")
ax.set_title("Dos ejes del ACG")
guardar(fig, "parte3/ritmicidad_resumen.png")
plt.show()

# %% [markdown]
# ### III.b · Cross-correlogramas a escala de milisegundos: posibles conexiones funcionales
#
# Un pico angosto y **asimétrico** en el CCG a +1–4 ms (B dispara justo después de A) es la firma de una posible
# conexión excitatoria A→B; un pico centrado en 0 ms indica **sincronía**, típicamente por una entrada común; un valle a
# +1–5 ms, una posible inhibición.
#
# El problema: dos neuronas que responden a los mismos eventos de la tarea tienen CCG con un "lomo" ancho aunque no estén
# conectadas. Para separar eso usamos como línea de base el propio CCG suavizado con una **gaussiana hueca**
# (σ = 10 ms, 60 % de hueco en el centro; Stark & Abeles 2009). Esa base conserva todas las co-variaciones lentas (> ~10 ms),
# y es el equivalente analítico de hacer *jitter* de los spikes. Cada bin se compara con su base con un test de Poisson.
#
# Criterios (α por bin = 10⁻⁴; con ~900 pares × ~16 bins esperamos ~1–2 falsos positivos en total):
# - **Artefacto de sorting** (se excluye): un único bin gigante (> 3× la base) en |lag| ≤ 1 ms, más de 2,5 veces
#   mayor que sus "hombros" a 2–4 ms.
#   Es lo que produce un mismo spike asignado a dos unidades, o una neurona partida en dos clusters.
# - **Dirigida A→B**: algún bin en +1…+4 ms supera la base y del lado anticausal (−4…−1 ms) no hay nada (p > 0,01).
# - **Sincronía fina**: exceso a ambos lados, o centrado en |lag| ≤ 1 ms. Típico de entrada común u oscilaciones rápidas.
# - **Inhibitoria A→B**: algún bin en +1…+5 ms queda por debajo de la base.
# - Sólo se testean pares con ≥ 5 coincidencias esperadas por bin.
# - Una "posible conexión" en el CCG es una hipótesis: sin la posición de los electrodos ni manipulaciones no se puede
#   distinguir una sinapsis de una entrada común con retardos distintos.

# %%
def base_gauss_hueca(ccg, sigma=10, hueco=0.6):
    half = int(3 * sigma)
    x = np.arange(-half, half + 1)
    w = np.exp(-x ** 2 / (2 * sigma ** 2))
    w /= w.sum()
    w[half] *= (1 - hueco)
    w /= w.sum()
    pad = np.r_[ccg[half:0:-1], ccg, ccg[-2:-half - 2:-1]]
    return np.convolve(pad, w, mode="valid")


def p_exceso(c, lam):
    return np.clip(1 - stats.poisson.cdf(c - 1, lam) - 0.5 * stats.poisson.pmf(c, lam), 0, 1)


def p_defecto(c, lam):
    return np.clip(stats.poisson.cdf(c - 1, lam) + 0.5 * stats.poisson.pmf(c, lam), 0, 1)


ALFA_CCG = 1e-4
pares = []
CCG = {}
for i, a in enumerate(ESTABLES):
    for b in ESTABLES[i + 1:]:
        c, lag = correlograma(spikes[a], spikes[b], 0.05, 0.001)
        base = base_gauss_hueca(c)
        CCG[(a, b)] = (c, base)
        L = np.round(lag * 1e3).astype(int)
        pos, neg, cero = (L >= 1) & (L <= 4), (L <= -1) & (L >= -4), np.abs(L) <= 1
        testeable = base[np.abs(L) <= 5].mean() >= 5
        pe, pdf = p_exceso(c, base), p_defecto(c, base)
        ratio = c / np.maximum(base, 1e-9)
        # Artefacto de sorting: un pico gigante (> 3x la base) en |lag| <= 1 ms sin "hombros" a 2-4 ms.
        # Un mismo spike asignado a dos unidades (o una unidad partida) produce exactamente eso.
        pico1 = ratio[np.abs(L) <= 1].max()
        artefacto = testeable and pico1 > 3 and pico1 > 2.5 * ratio[(np.abs(L) >= 2) & (np.abs(L) <= 4)].mean()
        causal, anticausal = pe[pos].min() < ALFA_CCG, pe[neg].min() < ALFA_CCG
        ok = testeable and not artefacto
        r = dict(a=a, b=b, testeable=testeable, artefacto=artefacto, n_coinc=c.sum(),
                 exc_ab=ok and causal and pe[neg].min() > 0.01,          # pico sólo del lado causal
                 exc_ba=ok and anticausal and pe[pos].min() > 0.01,
                 sincronia=ok and ((pe[cero].min() < ALFA_CCG and not (causal ^ anticausal)) or (causal and anticausal)),
                 inh_ab=ok and pdf[(L >= 1) & (L <= 5)].min() < ALFA_CCG,
                 inh_ba=ok and pdf[(L <= -1) & (L >= -5)].min() < ALFA_CCG)
        exc = ratio - 1
        win = np.abs(L) <= 5
        r["lag_pico_ms"] = L[win][np.argmax(exc[win])]
        r["exceso_pico"] = exc[win].max()
        pares.append(r)
LAG_CCG = lag
pares = pd.DataFrame(pares)
pares["significativo"] = pares[["exc_ab", "exc_ba", "sincronia", "inh_ab", "inh_ba"]].any(axis=1)
nt = int(pares.testeable.sum())
print(f"Pares testeables: {nt} de {len(pares)}")
print(f"  Probables artefactos de sorting: {int(pares.artefacto.sum())}")
print(f"  Excitatorios dirigidos: {int(pares.exc_ab.sum() + pares.exc_ba.sum())}")
print(f"  Sincronía fina (bilateral o 0 ms): {int(pares.sincronia.sum())}")
print(f"  Inhibitorios:           {int(pares.inh_ab.sum() + pares.inh_ba.sum())}")
print(f"  Algún tipo:             {int(pares.significativo.sum())} ({100*pares.significativo.sum()/max(nt,1):.1f} % de los testeables)")
print(f"  Exceso mediano en los significativos: {100*pares.loc[pares.significativo,'exceso_pico'].median():.0f} %")
print(f"  Falsos positivos esperados ~ {nt * 16 * ALFA_CCG:.1f}")
grado = pd.concat([pares.loc[pares.significativo, "a"], pares.loc[pares.significativo, "b"]]).value_counts()
rho_tasa = stats.spearmanr(neur.loc[ESTABLES, "tasa_hz"], grado.reindex(ESTABLES).fillna(0))
print(f"  Interacciones por neurona vs tasa: Spearman rho = {rho_tasa.statistic:.2f} (p = {rho_tasa.pvalue:.2g})")

# %%
def panel_ccg(ax, a, b, titulo):
    c, base = CCG[(a, b)] if (a, b) in CCG else (CCG[(b, a)][0][::-1], CCG[(b, a)][1][::-1])
    t = LAG_CCG * 1e3
    hz = 1 / (len(spikes[a]) * 0.001)
    ax.bar(t, c * hz, width=1.0, color="#B9B9B9", lw=0)
    ax.plot(t, base * hz, color=ACENTO, lw=1.2, label="base (co-variación lenta)")
    lim = stats.poisson.ppf(1 - ALFA_CCG, base) * hz
    ax.plot(t, lim, color=ACENTO, lw=0.7, ls=":", label="umbral (α = 0,0001)")
    ax.axvline(0, color=TINTA, lw=0.5, ls="--")
    ax.set_title(titulo + f"\nN{a} → N{b}", fontsize=9)
    ax.set_xlabel("Lag (ms)")


def elegir(df, col):
    d = df[df[col]].sort_values("exceso_pico", ascending=False)
    return (int(d.iloc[0].a), int(d.iloc[0].b)) if len(d) else None


ej_exc = elegir(pares, "exc_ab")
if ej_exc is None:
    tmp = elegir(pares, "exc_ba")
    ej_exc = (tmp[1], tmp[0]) if tmp else None
bil = pares[pares.sincronia].copy()
bil["bilat"] = [min((CCG[(r.a, r.b)][0] / CCG[(r.a, r.b)][1])[np.r_[48:50]].mean(),
                    (CCG[(r.a, r.b)][0] / CCG[(r.a, r.b)][1])[np.r_[51:53]].mean()) for r in bil.itertuples()]
ej_sin = (int(bil.sort_values("bilat").iloc[-1].a), int(bil.sort_values("bilat").iloc[-1].b)) if len(bil) else None
ej_art = elegir(pares, "artefacto")
EJ_CCG = [(ej_exc, "Pico sólo a +1–4 ms: posible A→B"), (ej_sin, "Pico a ambos lados: sincronía fina"),
          (ej_art, "Un solo bin gigante: artefacto")]

fig, axs = plt.subplots(1, 3, figsize=(10, 2.8), gridspec_kw=dict(wspace=0.3))
for ax, (par, tit) in zip(axs, EJ_CCG):
    if par:
        panel_ccg(ax, par[0], par[1], tit)
        if "artefacto" in tit:
            ax.title.set_color("#D62728")
axs[0].set_ylabel("Tasa condicional (Hz)")
axs[0].legend(fontsize=7, loc="upper left")
for ax in axs[:2]:                       # zoom a ±20 ms para ver la forma del pico
    ax.set_xlim(-20, 20)
guardar(fig, "parte3/ccg_ejemplos.png")
plt.show()

# %% [markdown]
# **Mapa de conexiones funcionales.** Neuronas en círculo, coloreadas por su respuesta al olor (Parte I). Flechas:
# posibles conexiones excitatorias dirigidas; líneas: sincronía; flechas rojas punteadas: posibles inhibiciones.

# %%
COL_RESP = {"excitada": "#D62728", "inhibida": TINTA, "sin respuesta": "#BBBBBB"}
orden_nodos = sorted(ESTABLES, key=lambda n: (["excitada", "inhibida", "sin respuesta"].index(clas.loc[n, "resp_olor"]), n))
ang = np.linspace(0, 2 * np.pi, len(orden_nodos), endpoint=False) + np.pi / 2
pos = {n: (np.cos(t), np.sin(t)) for n, t in zip(orden_nodos, ang)}

fig = plt.figure(figsize=(10, 4.2))
gs = fig.add_gridspec(1, 3, width_ratios=[1.35, 1, 1], wspace=0.45)
ax = fig.add_subplot(gs[0])
for r in pares.itertuples():
    pa, pb = pos[r.a], pos[r.b]
    if r.sincronia:
        ax.plot([pa[0], pb[0]], [pa[1], pb[1]], color=ACENTO, lw=0.8, alpha=0.6, zorder=1)
    for flag, (o, d), col, ls in [(r.exc_ab, (pa, pb), TINTA, "-"), (r.exc_ba, (pb, pa), TINTA, "-"),
                                  (r.inh_ab, (pa, pb), "#D62728", ":"), (r.inh_ba, (pb, pa), "#D62728", ":")]:
        if flag:
            ax.add_patch(FancyArrowPatch(o, d, arrowstyle="-|>", mutation_scale=7, color=col, lw=0.8, ls=ls,
                                         shrinkA=6, shrinkB=6, connectionstyle="arc3,rad=0.12", zorder=2))
for n in orden_nodos:
    ax.scatter(*pos[n], s=60, color=COL_RESP[clas.loc[n, "resp_olor"]], edgecolor="white", zorder=3)
    ax.text(pos[n][0] * 1.13, pos[n][1] * 1.13, str(n), ha="center", va="center", fontsize=6, color=GRIS)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Red de pares significativos", loc="center")
for lab, col in COL_RESP.items():
    ax.scatter([], [], color=col, s=30, label=lab)
ax.plot([], [], color=ACENTO, label="sincronía"); ax.plot([], [], color=TINTA, label="excitatoria →")
ax.legend(fontsize=6.5, loc="lower center", bbox_to_anchor=(0.5, -0.2), ncol=3)

ax = fig.add_subplot(gs[1])
sig = pares[pares.significativo & (pares.exceso_pico > 0)]
ax.hist(sig.lag_pico_ms.abs(), bins=np.arange(-0.5, 6.5, 1), color=ACENTO, edgecolor="white")
ax.set_xlabel("|Lag| del pico (ms)"); ax.set_ylabel("Pares"); ax.set_title("¿Cuándo es el pico?")

ax = fig.add_subplot(gs[2])
cat = {"Dirigida": int(pares.exc_ab.sum() + pares.exc_ba.sum()),
       "Sincronía": int(pares.sincronia.sum()),
       "Inhibitoria": int(pares.inh_ab.sum() + pares.inh_ba.sum()),
       "Artefacto": int(pares.artefacto.sum())}
etq_cat = [k.replace(chr(10), " ") for k in cat][::-1]
ax.barh(etq_cat, list(cat.values())[::-1], color=[TINTA, ACENTO, "#D62728", "#C8C8C8"][::-1], height=0.6)
for i, v in enumerate(list(cat.values())[::-1]):
    ax.text(v + 1, i, str(v), va="center")
ax.set_xlabel("Pares"); ax.set_title(f"Tipos (de {nt} pares)")
guardar(fig, "parte3/red_conexiones.png")
plt.show()

# %% [markdown]
# ### III.c · Cross-correlación a escala de cientos de ms: ¿estímulo compartido o coordinación?
#
# A escala lenta (±500 ms, bins de 10 ms) dos neuronas pueden estar correlacionadas simplemente porque **ambas responden
# al olor**. El **shift predictor** (Perkel et al. 1967) estima esa parte: correlamos la neurona A del ensayo *i* con la
# neurona B del ensayo siguiente **del mismo tipo**. Mantiene la relación con el estímulo y rompe todo lo que ocurre
# "dentro del mismo ensayo". CCG crudo − shift predictor = coordinación que no se explica por la respuesta al estímulo.
#
# Ventana: −1 a +2 s alrededor de la primera inhalación, ensayos 1–4. Índice por par: coincidencias en ±100 ms por
# encima del shift predictor, en % de lo que predice el shift (0 % = todo se explica por el estímulo).

# %%
VEN_SP = (-1.0, 2.0)
tr_sp = VALIDOS[VALIDOS.tipo.isin(TIPOS_OLOR)].copy()
OFFSET = 100.0   # cada ensayo se coloca en su propio tramo de tiempo para no mezclar ensayos
tr_sp["orden"] = np.arange(len(tr_sp))
sig_tr = tr_sp.groupby("tipo").orden.transform(lambda x: np.roll(x.values, -1))   # ensayo siguiente del mismo tipo


def tren_ensayos(spk, ev, orden_destino):
    rel = alinear(spk, ev, VEN_SP)
    return np.sort(np.concatenate([r + OFFSET * o for r, o in zip(rel, orden_destino)]))


TREN = {n: tren_ensayos(spikes[n], tr_sp.t_inhal.values, tr_sp.orden.values) for n in ESTABLES}
TREN_SH = {n: tren_ensayos(spikes[n], tr_sp.t_inhal.values, sig_tr.values) for n in ESTABLES}

sp_res = []
SP = {}
for i, a in enumerate(ESTABLES):
    for b in ESTABLES[i + 1:]:
        cr, lg = correlograma(TREN[a], TREN[b], 0.5, 0.01)
        cs, _ = correlograma(TREN[a], TREN_SH[b], 0.5, 0.01)
        SP[(a, b)] = (cr, cs)
        w = np.abs(lg) <= 0.1
        # coincidencias en ±100 ms por encima de lo que predice el estímulo, en % de lo predicho
        sp_res.append(dict(a=a, b=b, crudo=cr[w].sum(), pred=cs[w].sum(),
                           exceso_intra=100 * (cr[w].sum() - cs[w].sum()) / max(cs[w].sum(), 1e-9)))
LAG_SP = lg
sp_res = pd.DataFrame(sp_res)
sp_res = sp_res[sp_res.pred > 50]          # pares con suficientes coincidencias para estimar
p_intra = stats.wilcoxon(sp_res.exceso_intra).pvalue
print(f"Coincidencias (±100 ms) por encima del shift predictor: mediana {sp_res.exceso_intra.median():.1f} % "
      f"(IQR {sp_res.exceso_intra.quantile(.25):.1f} a {sp_res.exceso_intra.quantile(.75):.1f} %), "
      f"Wilcoxon vs 0: p = {p_intra:.2g}, n = {len(sp_res)} pares")

# %% [markdown]
# **Correlaciones de ruido (r_sc).** Pasando de milisegundos a ensayos: para cada par, correlación de Pearson entre los
# conteos de spikes por ensayo en la ventana de olor (0–1 s), después de restar la media de cada tipo de ensayo. Mide
# cuánto co-varían las dos neuronas de un ensayo a otro **para el mismo estímulo**. ¿Los pares con interacción
# significativa en el CCG tienen más correlación de ruido?

# %%
cont = np.array([tasa_ventana(spikes[n], tr_sp.t_inhal.values, 0, 1.0) for n in ESTABLES])
res = cont.copy()
for k in TIPOS_OLOR:
    m = tr_sp.tipo.values == k
    res[:, m] = (cont[:, m] - cont[:, m].mean(1, keepdims=True)) / np.maximum(cont[:, m].std(1, keepdims=True), 1e-9)
RSC = np.corrcoef(res)
ix = {n: i for i, n in enumerate(ESTABLES)}
pares["r_sc"] = [RSC[ix[r.a], ix[r.b]] for r in pares.itertuples()]
pares = pares.merge(sp_res[["a", "b", "exceso_intra"]], on=["a", "b"], how="left")
g_sig = pares.loc[pares.significativo, "r_sc"]
g_ns = pares.loc[pares.testeable & ~pares.significativo & ~pares.artefacto, "r_sc"]
p_rsc = stats.mannwhitneyu(g_sig, g_ns).pvalue
p_rsc0 = stats.wilcoxon(pares.loc[~pares.artefacto, "r_sc"]).pvalue
ei_sig = pares.loc[pares.significativo, "exceso_intra"].dropna()
ei_ns = pares.loc[pares.testeable & ~pares.significativo & ~pares.artefacto, "exceso_intra"].dropna()
p_ei = stats.mannwhitneyu(ei_sig, ei_ns).pvalue
print(f"r_sc media: {pares.r_sc.mean():.3f} (vs 0: p = {p_rsc0:.2g}) | con interacción {g_sig.mean():.3f} "
      f"vs sin {g_ns.mean():.3f} (p = {p_rsc:.2g})")
print(f"Exceso intra-ensayo: con interacción {ei_sig.median():.1f} % vs sin {ei_ns.median():.1f} % (p = {p_ei:.2g})")

# %%
sin_art = [k for k in SP if not pares.loc[(pares.a == k[0]) & (pares.b == k[1]), "artefacto"].any()]
CR_ALL = np.array([SP[k][0] for k in sin_art]); CS_ALL = np.array([SP[k][1] for k in sin_art])
norm_ = CS_ALL.mean(1, keepdims=True)
crm, csm = (CR_ALL / norm_).mean(0), (CS_ALL / norm_).mean(0)
fig, axs = plt.subplots(1, 3, figsize=(10, 2.9), gridspec_kw=dict(wspace=0.38))
ax = axs[0]
ax.plot(LAG_SP * 1e3, crm, color=TINTA, lw=1.4, label="CCG crudo")
ax.plot(LAG_SP * 1e3, csm, color="#FF8C1A", lw=1.4, label="shift predictor (estímulo)")
ax.fill_between(LAG_SP * 1e3, csm, crm, where=crm > csm, color=ACENTO, alpha=0.35, lw=0, label="coordinación intra-ensayo")
ax.set_xlabel("Lag (ms)"); ax.set_ylabel("CCG normalizado")
ax.set_title(f"Promedio de {len(sin_art)} pares alrededor del olor", fontsize=9)
ax.legend(fontsize=6.5, loc="lower center")
ax = axs[1]
ax.hist(np.clip(sp_res.exceso_intra, -30, 60), bins=np.arange(-30, 61, 3), color=ACENTO, edgecolor="white")
ax.axvline(0, color=TINTA, ls="--", lw=0.8)
ax.axvline(sp_res.exceso_intra.median(), color="#D62728", lw=1.2)
ax.set_xlabel("Coincidencias sobre el shift predictor (%)"); ax.set_ylabel("Pares")
ax.set_title(f"Más allá del estímulo · mediana {coma_py(sp_res.exceso_intra.median())} %")
ax = axs[2]
bins = np.arange(-30, 61, 4)
ax.hist(np.clip(ei_ns, -30, 60), bins=bins, color="#C8C8C8", density=True, label=f"sin interacción fina (n={len(ei_ns)})")
ax.hist(np.clip(ei_sig, -30, 60), bins=bins, color=ACENTO, alpha=0.75, density=True, label=f"con interacción fina (n={len(ei_sig)})")
ax.axvline(0, color=TINTA, lw=0.6)
ax.set_xlabel("Coincidencias sobre el shift predictor (%)"); ax.set_ylabel("Densidad")
ax.set_title(f"De ms a cientos de ms · {p_txt(p_ei)}")
ax.legend(fontsize=6.5, loc="upper right")
guardar(fig, "parte3/shift_predictor_rsc.png")
plt.show()

# %% [markdown]
# ### Resumen numérico (se usa en la presentación)

# %%
resumen = {
    "neuronas": len(NEURONAS), "estables": len(ESTABLES), "ensayos": len(trials),
    "pares": len(pares), "pares_testeables": nt,
    "excitadas_olor": int((clas.resp_olor == "excitada").sum()),
    "inhibidas_olor": int((clas.resp_olor == "inhibida").sum()),
    "sel_olor": int(clas.sel_olor.sum()), "sel_contexto": int(clas.sel_contexto.sum()),
    "sel_recompensa": int(clas.sel_recompensa.sum()), "mixtas_2omas": int((clas.n_variables >= 2).sum()),
    "p_OR_CRvsCU": p_or, "p_OU_CRvsCU": p_ou, "p_OR_vs_OU": p_od,
    "ritmicas": int(A.ritmica.sum()), "f_pico_mediana": float(A.loc[A.ritmica, "f_pico"].median()) if A.ritmica.any() else np.nan,
    "bursty": int(A.bursty.sum()),
    "exc_dirigidas": int(pares.exc_ab.sum() + pares.exc_ba.sum()), "sincronia": int(pares.sincronia.sum()),
    "inhibitorias": int(pares.inh_ab.sum() + pares.inh_ba.sum()), "pares_sig": int(pares.significativo.sum()),
    "fp_esperados": nt * 16 * ALFA_CCG,
    "artefactos": int(pares.artefacto.sum()), "exceso_mediano_sig": float(pares.loc[pares.significativo, "exceso_pico"].median()),
    "rho_grado_tasa": float(rho_tasa.statistic), "p_grado_tasa": float(rho_tasa.pvalue),
    "exceso_intra_mediana": float(sp_res.exceso_intra.median()), "p_intra": float(p_intra), "n_sp": int(len(sp_res)),
    "exceso_intra_sig": float(ei_sig.median()), "exceso_intra_ns": float(ei_ns.median()), "p_ei": float(p_ei),
    "rsc_media": float(pares.r_sc.mean()), "p_rsc0": float(p_rsc0), "rsc_sig": float(g_sig.mean()),
    "rsc_ns": float(g_ns.mean()), "p_rsc": p_rsc,
    "selectivas_2omas": int((clas.n_variables >= 2).sum()),
    "ej_exc": EJ_EXC, "ej_inh": EJ_INH, "ej_rec": EJ_REC, "ej_acg": EJ_ACG,
    "ej_ccg": [p for p, _ in EJ_CCG],
    "dur_ctx_mediana": trials.groupby("tipo").dur_contexto.median().round(2).to_dict(),
}
pd.Series(resumen, dtype=object).to_json(FIG / "resumen.json", force_ascii=False, indent=1, default_handler=str)
neur.to_csv(FIG / "tabla_neuronas.csv")
pares.to_csv(FIG / "tabla_pares.csv", index=False)
pd.Series(resumen, dtype=object)

# %% [markdown]
# ## Parte IV · Análisis libre
#
# ### Pregunta
# **¿El contexto recompensado cambia cómo se coordinan las neuronas de la corteza piriforme, y no sólo cuánto disparan?**
#
# Sub-análisis (ensambles): **¿las neuronas que se coordinan son las que responden parecido?** Y si el contexto cambia la
# coordinación, **¿lo hace sobre todo entre esas neuronas?**
#
# **Por qué esta pregunta.** La Parte II mostró que la población *anticipa* el contexto recompensado (la actividad sube
# antes del olor) y la Parte III que las neuronas no son independientes: co-varían a escala de ms y de ensayo a ensayo.
# Juntando las dos: si el contexto cambia el estado de la red (expectativa, atención, arousal), debería notarse en la
# **variabilidad compartida**, no sólo en la tasa media. En corteza visual, la atención baja las correlaciones de ruido
# (Cohen & Maunsell 2009); un estado de expectativa común a toda la red podría, al revés, subirlas. Por eso la dirección
# queda abierta.
#
# **Hipótesis.**
# - **H1**: la correlación de ruido (r_sc) difiere entre el contexto recompensado (CR) y el no recompensado (CU) en la
#   aproximación y durante el olor, pero **no** en el corredor, antes de ver el contexto (control negativo).
# - **H2** (ensambles): la coordinación es mayor entre neuronas con respuestas parecidas (*like-to-like*), y el cambio por
#   contexto se concentra en esos pares.
#
# **Diseño** (r_sc: correlación de Pearson entre los conteos por ensayo de dos neuronas, restando la media y dividiendo por
# el desvío de cada tipo de ensayo, para quedarnos sólo con la co-variación de ensayo a ensayo):
#
# | Época | Ventana | Comparación |
# |---|---|---|
# | Corredor (control) | 0,5–2 s desde el inicio | CR (1, 3, 5) vs CU (2, 4, 6) |
# | Aproximación | −1 a 0 s antes de entrar | CR (1, 3, 5) vs CU (2, 4, 6) |
# | Olor | 0–0,5 s tras la inhalación | OR·CR vs OR·CU · OU·CR vs OU·CU (mismo olor, distinto contexto) |
#
# La ventana de olor termina a los 0,5 s porque en el contexto no recompensado el ratón sale ~0,5 s después de inhalar:
# así las dos condiciones se comparan dentro del contexto.
#
# **Plan completo** (esta entrega cubre IV.1 a IV.4; el resto está en `HANDOFF_parte_IV.md`):
# IV.1 r_sc por contexto y época con controles · IV.2 ensambles: semejanza de respuesta vs acoplamiento ·
# IV.3 CCG de ms por contexto · IV.4 ¿la coordinación ayuda o perjudica a decodificar el olor? ·
# IV.5 ensambles por clustering · IV.6 control de la velocidad y cierre.

# %%
VERDE_CR, GRIS_CU = "#4C9A2A", "#8C8C8C"           # contexto verde = recompensado (esquema de la tarea)
ODOR_CLASE = {1: "OR", 2: "OR", 3: "OU", 4: "OU", 5: "sin", 6: "sin"}
CTX = {1: "CR", 2: "CU", 3: "CR", 4: "CU", 5: "CR", 6: "CU"}

pares_ok = pares.loc[~pares.artefacto].reset_index(drop=True)          # sin artefactos de sorting
IA = pares_ok.a.map(ix).values
IB = pares_ok.b.map(ix).values

EPOCAS = {"Corredor": ("t_inicio", 0.5, 2.0), "Aproximación": ("t_entrada", -1.0, 0.0), "Olor": ("t_inhal", 0.0, 0.5)}
COMPARACIONES = [  # (época, etiqueta, tipos incluidos)
    ("Corredor", "CR vs CU", [1, 2, 3, 4, 5, 6]),
    ("Aproximación", "CR vs CU", [1, 2, 3, 4, 5, 6]),
    ("Olor", "OR: CR vs CU", [1, 2]),
    ("Olor", "OU: CR vs CU", [3, 4]),
]
N_PERM = 1000


def conteos_epoca(epoca, tr):
    col, a, b = EPOCAS[epoca]
    ev = tr[col].values
    return np.array([np.searchsorted(spikes[n], ev + b) - np.searchsorted(spikes[n], ev + a) for n in ESTABLES], float)


def rsc_pares(C, clase):
    """r_sc de todos los pares (sin artefactos): z-score dentro de cada clase de olor y correlación entre ensayos."""
    X = C.copy()
    for o in np.unique(clase):
        m = clase == o
        mu = X[:, m].mean(1, keepdims=True)
        sd = X[:, m].std(1, keepdims=True)
        X[:, m] = np.where(sd > 0, (X[:, m] - mu) / np.where(sd > 0, sd, 1), 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        R = np.corrcoef(X)
    return R[IA, IB]


def efecto_contexto(C, clase, ctx):
    """Δ r_sc medio (CR − CU) y el mismo efecto ajustado por la tasa geométrica del par (regresión lineal)."""
    r_cr, r_cu = rsc_pares(C[:, ctx == "CR"], clase[ctx == "CR"]), rsc_pares(C[:, ctx == "CU"], clase[ctx == "CU"])
    ok = np.isfinite(r_cr) & np.isfinite(r_cu)
    tasa = lambda m: np.sqrt(np.maximum(C[IA][:, m].mean(1), 1e-3) * np.maximum(C[IB][:, m].mean(1), 1e-3))
    g_cr, g_cu = tasa(ctx == "CR"), tasa(ctx == "CU")
    y = np.r_[r_cr[ok], r_cu[ok]]
    Xr = np.c_[np.ones(2 * ok.sum()), np.r_[np.ones(ok.sum()), np.zeros(ok.sum())], np.log(np.r_[g_cr[ok], g_cu[ok]])]
    beta = np.linalg.lstsq(Xr, y, rcond=None)[0]
    return dict(r_cr=r_cr, r_cu=r_cu, ok=ok, delta=np.mean(r_cr[ok] - r_cu[ok]), delta_aj=beta[1], g_cr=g_cr, g_cu=g_cu)


RES4 = {}
for epoca, etq, tipos in COMPARACIONES:
    tr = VALIDOS[VALIDOS.tipo.isin(tipos)]
    if epoca == "Olor":
        tr = tr[tr.tipo.isin(TIPOS_OLOR)]
    C = conteos_epoca(epoca, tr)
    clase = tr.tipo.map(ODOR_CLASE).values
    ctx = tr.tipo.map(CTX).values
    obs = efecto_contexto(C, clase, ctx)
    nulo, nulo_aj = np.empty(N_PERM), np.empty(N_PERM)
    for i in range(N_PERM):                      # permuto la etiqueta de contexto dentro de cada clase de olor
        ctx_p = ctx.copy()
        for o in np.unique(clase):
            m = np.where(clase == o)[0]
            ctx_p[m] = RNG.permutation(ctx[m])
        e = efecto_contexto(C, clase, ctx_p)
        nulo[i], nulo_aj[i] = e["delta"], e["delta_aj"]
    obs["p"] = (np.sum(np.abs(nulo) >= abs(obs["delta"])) + 1) / (N_PERM + 1)
    obs["p_aj"] = (np.sum(np.abs(nulo_aj) >= abs(obs["delta_aj"])) + 1) / (N_PERM + 1)
    obs["nulo"], obs["nulo_aj"] = nulo, nulo_aj
    obs["mde"] = float(np.quantile(np.abs(nulo), 0.95))   # |Δ| que habríamos detectado con p < 0,05
    obs["n_cr"], obs["n_cu"] = int((ctx == "CR").sum()), int((ctx == "CU").sum())
    obs["tasa_cr"], obs["tasa_cu"] = C[:, ctx == "CR"].mean() / (EPOCAS[epoca][2] - EPOCAS[epoca][1]), \
        C[:, ctx == "CU"].mean() / (EPOCAS[epoca][2] - EPOCAS[epoca][1])
    RES4[(epoca, etq)] = obs
    print(f"{epoca:13s} {etq:13s} n={obs['n_cr']}/{obs['n_cu']}  r_sc CR={np.nanmean(obs['r_cr'][obs['ok']]):.3f} "
          f"CU={np.nanmean(obs['r_cu'][obs['ok']]):.3f}  Δ={obs['delta']:+.3f} (p={obs['p']:.3f})  "
          f"Δ ajust. tasa={obs['delta_aj']:+.3f} (p={obs['p_aj']:.3f})  tasa media CR/CU={obs['tasa_cr']:.2f}/{obs['tasa_cu']:.2f} Hz"
          f"  |Δ| detectable ≈ {obs['mde']:.3f}")

# %% [markdown]
# ### IV.1 · Resultado: r_sc en cada contexto y época
#
# Cada punto es el r_sc medio de los pares (± error estándar entre pares). El p sale de **permutar la etiqueta de contexto**
# entre ensayos (dentro de cada clase de olor), 1000 veces: así el test respeta el número desigual de ensayos y la
# dependencia entre pares que comparten neuronas.

# %%
fig, ax = plt.subplots(figsize=(6.2, 3.2))
xs = np.arange(len(COMPARACIONES))
for i, (clave, o) in enumerate(RES4.items()):
    for dx, r, col, lab in [(-0.12, o["r_cr"][o["ok"]], VERDE_CR, "contexto recompensado (CR)"),
                            (0.12, o["r_cu"][o["ok"]], GRIS_CU, "contexto no recompensado (CU)")]:
        ax.errorbar(i + dx, r.mean(), yerr=r.std(ddof=1) / np.sqrt(len(r)), fmt="o", color=col, ms=7, capsize=3,
                    lw=1.3, label=lab if i == 0 else None)
    ax.text(i, 0.031, p_txt(o["p"]), ha="center", fontsize=8.5, fontweight="bold" if o["p"] < 0.05 else "normal")
ax.axhline(0, color="#BBBBBB", lw=0.7)
ax.axvspan(-0.5, 0.5, color="#F2F2F2", zorder=0)
ax.set_xticks(xs)
ax.set_xticklabels([f"{e}\n{c}" for e, c, _ in COMPARACIONES])
ax.set_xlim(-0.5, len(xs) - 0.5)
ax.set_ylabel("Correlación de ruido r_sc (media ± EE)")
ax.text(0, ax.get_ylim()[0] + 0.002, "control", ha="center", fontsize=8, color=GRIS, va="bottom")
ax.set_ylim(-0.01, 0.034)
ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2)
guardar(fig, "parte4/rsc_por_contexto.png")
plt.show()

# %% [markdown]
# ### IV.1 · Controles
#
# 1. **Distribución nula por permutación** (arriba): dónde cae el Δ observado respecto de 1000 permutaciones de contexto.
# 2. **Tasa de disparo**: r_sc crece con la tasa (de la Rocha et al. 2007). Si un contexto tiene más actividad, r_sc podría
#    subir sólo por eso. Lo controlamos de dos formas: Δ ajustado por la tasa geométrica del par (regresión con la tasa
#    como covariable, también testeado por permutación) y Δ dentro de cuartiles de tasa.

# %%
fig, axs = plt.subplots(2, 4, figsize=(10, 4.6), gridspec_kw=dict(hspace=0.75, wspace=0.35))
for j, (clave, o) in enumerate(RES4.items()):
    ax = axs[0, j]
    ax.hist(o["nulo"], bins=30, color="#C8C8C8", edgecolor="white")
    ax.axvline(o["delta"], color=VERDE_CR, lw=2)
    ax.set_title(f"{clave[0]} · {clave[1]}", fontsize=8.5)
    ax.set_xlabel("Δ r_sc (CR − CU)", fontsize=8)
    ax.text(0.97, 0.95, p_txt(o["p"]), transform=ax.transAxes, ha="right", va="top", fontsize=8)
    ax.set_yticks([])
    ax = axs[1, j]
    gm = np.sqrt(o["g_cr"] * o["g_cu"])[o["ok"]]
    d = (o["r_cr"] - o["r_cu"])[o["ok"]]
    q = pd.qcut(gm, 4, labels=False)
    m_ = [d[q == k].mean() for k in range(4)]
    e_ = [d[q == k].std(ddof=1) / np.sqrt((q == k).sum()) for k in range(4)]
    ax.bar(range(4), m_, yerr=e_, color=VERDE_CR, alpha=0.8, width=0.65, error_kw=dict(lw=1, capsize=2))
    ax.axhline(0, color=TINTA, lw=0.6)
    ax.set_xticks(range(4)); ax.set_xticklabels(["Q1", "Q2", "Q3", "Q4"], fontsize=8)
    ax.set_xlabel("cuartil de tasa del par", fontsize=8)
    ax.set_title(f"ajustado por tasa: {p_txt(o['p_aj'])}", fontsize=8.5)
axs[0, 0].set_ylabel("permutaciones")
axs[1, 0].set_ylabel("Δ r_sc (media ± EE)")
guardar(fig, "parte4/rsc_controles.png")
plt.show()

# %% [markdown]
# ### IV.2 · Ensambles: ¿se coordinan más las neuronas que responden parecido?
#
# - **Semejanza de respuesta (correlación de señal)**: correlación entre los PSTH promedio de dos neuronas, concatenando los
#   cuatro tipos de ensayo con olor (−0,5 a 1,5 s desde la inhalación). Alta = responden a lo mismo y con el mismo curso temporal.
# - **Acoplamiento**: r_sc de la Parte III (todos los ensayos con olor, 0–1 s) e interacción fina en el CCG (Parte III.b).
# - **Test de Mantel**: la correlación entre dos matrices de pares no se puede testear como si los pares fueran
#   independientes (cada neurona participa en 43 pares). Se permutan las etiquetas de las neuronas en una de las matrices
#   (1000 veces) y se recalcula la correlación de Spearman.
# - **Puente con IV.1**: ¿el Δ r_sc por contexto depende de la semejanza de respuesta del par? El corredor (antes de ver
#   el contexto) es el control negativo: ahí la relación no debería aparecer.

# %%
tc = TC["inhalacion"]
vent = (tc >= -0.5) & (tc <= 1.5)
SENAL = np.corrcoef(np.concatenate([POB["inhalacion"][k][:, vent] for k in TIPOS_OLOR], axis=1))
sig_par = SENAL[IA, IB]
rsc_par = RSC[IA, IB]


def mantel(M1, M2, n_perm=N_PERM):
    iu = (IA, IB)
    obs_ = stats.spearmanr(M1[iu], M2[iu], nan_policy="omit").statistic
    cnt = 0
    for _ in range(n_perm):
        p = RNG.permutation(M1.shape[0])
        cnt += abs(stats.spearmanr(M1[p][:, p][iu], M2[iu], nan_policy="omit").statistic) >= abs(obs_)
    return obs_, (cnt + 1) / (n_perm + 1)


rho_m, p_m = mantel(SENAL, RSC)
inter = pares_ok.significativo.values
q_sig = pd.qcut(sig_par, 4, labels=False)
frac_int = [inter[q_sig == k].mean() for k in range(4)]
tab = pd.crosstab(q_sig, inter)
p_chi = stats.chi2_contingency(tab)[1]
print(f"Mantel (Spearman) semejanza de respuesta vs r_sc: rho = {rho_m:.2f}, p = {p_m:.3f}")
print("Fracción de pares con interacción fina por cuartil de semejanza:", np.round(frac_int, 3), f"chi2 p = {p_chi:.3g}")
# ¿qué tipo de interacción domina en cada cuartil? (los pares más distintos podrían ser los inhibitorios)
tipo_int = np.select([pares_ok.inh_ab | pares_ok.inh_ba, pares_ok.sincronia, pares_ok.exc_ab | pares_ok.exc_ba],
                     ["inhibitoria", "sincronía", "dirigida"], "ninguna")
COMP_Q = pd.crosstab(q_sig, tipo_int).reindex(columns=["dirigida", "sincronía", "inhibitoria"], fill_value=0)
COMP_Q.index = ["Q1 distintas", "Q2", "Q3", "Q4 parecidas"]
print(COMP_Q.to_string())

DELTA_Q = {}
# el corredor va al final como control negativo (ahí el contexto todavía no se ve: no debería haber efecto);
# al final para no alterar la secuencia aleatoria de las otras dos comparaciones
for clave in [("Aproximación", "CR vs CU"), ("Olor", "OR: CR vs CU"), ("Corredor", "CR vs CU")]:
    o = RES4[clave]
    d = (o["r_cr"] - o["r_cu"])
    ok = o["ok"]
    rho_d = stats.spearmanr(sig_par[ok], d[ok]).statistic
    # test de Mantel: permuto las etiquetas de neurona de la matriz de semejanza
    cnt = 0
    for _ in range(N_PERM):
        p = RNG.permutation(SENAL.shape[0])
        cnt += abs(stats.spearmanr(SENAL[p][:, p][IA[ok], IB[ok]], d[ok]).statistic) >= abs(rho_d)
    DELTA_Q[clave] = dict(m=[d[ok][q_sig[ok] == k].mean() for k in range(4)],
                          e=[d[ok][q_sig[ok] == k].std(ddof=1) / np.sqrt((q_sig[ok] == k).sum()) for k in range(4)],
                          rho=rho_d, p=(cnt + 1) / (N_PERM + 1))
    print(f"Δ r_sc {clave[0]} {clave[1]} vs semejanza: rho = {rho_d:.2f}, p (Mantel) = {DELTA_Q[clave]['p']:.3f}")

# %%
fig, axs = plt.subplots(1, 3, figsize=(10, 3.0), gridspec_kw=dict(wspace=0.42))
ax = axs[0]
ax.scatter(sig_par, rsc_par, s=5, color="#BBBBBB", lw=0, rasterized=True)
bins_s = np.quantile(sig_par, np.linspace(0, 1, 9))
cen = [(bins_s[k] + bins_s[k + 1]) / 2 for k in range(8)]
med = [np.nanmean(rsc_par[(sig_par >= bins_s[k]) & (sig_par <= bins_s[k + 1])]) for k in range(8)]
ax.plot(cen, med, "o-", color=ACENTO, lw=1.5, ms=4)
ax.axhline(0, color=TINTA, lw=0.5)
ax.set_xlabel("Semejanza de respuesta (corr. de señal)")
ax.set_ylabel("r_sc (Parte III)")
ax.set_title(f"Like-to-like · Mantel ρ = {coma_py(rho_m, 2)}, {p_txt(p_m)}", fontsize=9)
ax = axs[1]
n_q = pd.Series(q_sig).value_counts().sort_index().values
abajo = np.zeros(4)
for tipo, col in [("dirigida", TINTA), ("sincronía", ACENTO), ("inhibitoria", "#D62728")]:
    v = 100 * COMP_Q[tipo].values / n_q
    ax.bar(range(4), v, bottom=abajo, color=col, width=0.65, label=tipo)
    abajo += v
ax.set_xticks(range(4)); ax.set_xticklabels(["Q1\ndistintas", "Q2", "Q3", "Q4\nparecidas"])
ax.set_ylabel("% de pares con interacción de ms")
ax.legend(fontsize=6.5, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0))
ax.set_ylim(0, max(abajo) * 1.3)
ax.set_title(f"Interacción fina por semejanza · {p_txt(p_chi)}", fontsize=9)
ax = axs[2]
for dx, (clave, col) in zip([-0.27, 0.0, 0.27], [(("Corredor", "CR vs CU"), "#BBBBBB"),
                                                  (("Aproximación", "CR vs CU"), VERDE_CR),
                                                  (("Olor", "OR: CR vs CU"), "#D62728")]):
    dq = DELTA_Q[clave]
    ax.bar(np.arange(4) + dx, dq["m"], yerr=dq["e"], width=0.26, color=col, alpha=0.85,
           error_kw=dict(lw=1, capsize=2), label=f"{clave[0]} (ρ = {coma_py(dq['rho'], 2)}, {p_txt(dq['p'])})")
ax.axhline(0, color=TINTA, lw=0.6)
ax.set_xticks(range(4)); ax.set_xticklabels(["Q1\ndistintas", "Q2", "Q3", "Q4\nparecidas"])
ax.set_ylabel("Δ r_sc (CR − CU)")
ax.set_title("¿Dónde actúa el contexto?", fontsize=9)
ax.set_ylim(top=ax.get_ylim()[1] * 1.45)           # espacio para la leyenda
ax.legend(fontsize=6.5, loc="upper right")
guardar(fig, "parte4/ensambles_semejanza.png")
plt.show()

# %% [markdown]
# ### IV.3 · ¿Cambian las interacciones de milisegundos con el contexto?
#
# r_sc mide co-variación **lenta** (conteos en cientos de ms, de ensayo a ensayo). Que no cambie con el contexto no
# descarta que cambie la **sincronía fina**: las interacciones de 1–5 ms que encontramos en la Parte III.b.
#
# **Método.**
# - **Ventana por ensayo**: de 1 s antes de entrar al contexto hasta 0,5 s después de la primera inhalación (en los
#   ensayos sin olor, hasta 0,9 s después de entrar, la latencia típica de inhalación). Es la parte del ensayo donde el
#   contexto ya se ve.
# - **CCG por ensayo**: como las ventanas están separadas por segundos, el CCG de un conjunto de ensayos es la **suma** de
#   los CCG de cada ensayo. Los calculamos una vez (±50 ms, bins de 1 ms) y después cualquier partición CR/CU, real o
#   permutada, es una suma.
# - **Pares**: los 140 con interacción significativa en la Parte III.b (el resto casi no tiene coincidencias).
# - **Medida** (*fuerza de la interacción*): en los bins que definen la interacción de cada par (|lag| ≤ 5 ms, p < 0,01 en
#   el CCG de toda la sesión), exceso relativo sobre la base de gaussiana hueca: (conteo − base) / base. Para los pares
#   inhibitorios se invierte el signo, así que en todos los casos **más alto = interacción más fuerte**. Al ser relativo a
#   la base, no depende de la tasa de disparo.
# - **Test**: mediana entre pares del Δ fuerza (CR − CU), contra 1000 permutaciones de la etiqueta de contexto entre
#   ensayos (dentro de cada clase: con olor recompensado, no recompensado, sin olor). Además Wilcoxon pareado.
# - **Control de muestra**: CR tiene más ensayos (100 vs 75) y ventanas más largas (el ratón va más lento), así que su CCG
#   es menos ruidoso. Repetimos con CR submuestreado a 75 ensayos.

# %%
TR3 = VALIDOS
CTX3 = TR3.tipo.map(CTX).values
CLASE3 = TR3.tipo.map(ODOR_CLASE).values
INI3 = TR3.t_entrada.values - 1.0
FIN3 = np.where(TR3.tipo.isin(TIPOS_OLOR), TR3.t_inhal.values + 0.5, TR3.t_entrada.values + 0.9)
SPK3 = {n: [spikes[n][np.searchsorted(spikes[n], a):np.searchsorted(spikes[n], b)] for a, b in zip(INI3, FIN3)]
        for n in ESTABLES}

P3 = pares_ok[pares_ok.significativo].reset_index(drop=True)
L_MS = np.round(LAG_CCG * 1e3).astype(int)
CC3 = np.zeros((len(P3), len(TR3), len(L_MS)))         # par × ensayo × bin
for i, r in enumerate(P3.itertuples()):
    for j in range(len(TR3)):
        sa, sb = SPK3[r.a][j], SPK3[r.b][j]
        if len(sa) and len(sb):
            CC3[i, j] = correlograma(sa, sb, 0.05, 0.001)[0]

# bins que definen la interacción de cada par (del CCG de toda la sesión) y signo
FIRMA, SIGNO, CLASE_INT = [], [], []
for r in P3.itertuples():
    c, base = CCG[(r.a, r.b)]
    inh = (r.inh_ab or r.inh_ba) and not (r.exc_ab or r.exc_ba or r.sincronia)
    w = np.abs(L_MS) <= 5
    p = p_defecto(c, base) if inh else p_exceso(c, base)
    b = w & (p < 0.01)
    if not b.any():
        ratio = c / np.maximum(base, 1e-9)
        b = np.zeros_like(w)
        b[np.where(w)[0][np.argmin(ratio[w]) if inh else np.argmax(ratio[w])]] = True
    FIRMA.append(b)
    SIGNO.append(-1 if inh else 1)
    CLASE_INT.append("inhibitoria" if inh else "excitatoria / sincronía")
FIRMA, SIGNO, CLASE_INT = np.array(FIRMA), np.array(SIGNO), np.array(CLASE_INT)


def fuerza(m):
    """Fuerza de la interacción de cada par usando los ensayos de la máscara m. Devuelve (fuerza, base en la firma)."""
    S = CC3[:, m].sum(1)
    f, nb = np.empty(len(P3)), np.empty(len(P3))
    for i in range(len(P3)):
        base = base_gauss_hueca(S[i])
        b = FIRMA[i]
        nb[i] = base[b].sum()
        f[i] = SIGNO[i] * (S[i][b].sum() - nb[i]) / max(nb[i], 1e-9)
    return f, nb


def permutar_ctx(ctx, clase):
    out = ctx.copy()
    for o in np.unique(clase):
        m = np.where(clase == o)[0]
        out[m] = RNG.permutation(ctx[m])
    return out


F_CR, NB_CR = fuerza(CTX3 == "CR")
F_CU, NB_CU = fuerza(CTX3 == "CU")
D3 = F_CR - F_CU
BIEN = (NB_CR >= 10) & (NB_CU >= 10)                   # pares con suficientes coincidencias esperadas en ambos contextos

nulo3 = np.empty(N_PERM)
for k in range(N_PERM):
    cp = permutar_ctx(CTX3, CLASE3)
    nulo3[k] = np.median(fuerza(cp == "CR")[0] - fuerza(cp == "CU")[0])
p3 = (np.sum(np.abs(nulo3) >= abs(np.median(D3))) + 1) / (N_PERM + 1)
p3_w = stats.wilcoxon(F_CR, F_CU).pvalue
p3_w_bien = stats.wilcoxon(F_CR[BIEN], F_CU[BIEN]).pvalue

# control de muestra: CR submuestreado al azar al número de ensayos CU (200 veces)
idx_cr = np.where(CTX3 == "CR")[0]
n_cu = int((CTX3 == "CU").sum())
med_sub = np.empty(200)
for k in range(200):
    m = np.zeros(len(TR3), bool)
    m[RNG.choice(idx_cr, n_cu, replace=False)] = True
    med_sub[k] = np.median(fuerza(m)[0] - F_CU)

RES43 = dict(n_pares=int(len(P3)), n_bien=int(BIEN.sum()),
             fuerza_cr_mediana=float(np.median(F_CR)), fuerza_cu_mediana=float(np.median(F_CU)),
             delta_mediana=float(np.median(D3)), p_perm=float(p3), p_wilcoxon=float(p3_w),
             delta_mediana_bien=float(np.median(D3[BIEN])), p_wilcoxon_bien=float(p3_w_bien),
             delta_mediana_submuestreo=float(np.median(med_sub)),
             delta_submuestreo_ic95=[float(x) for x in np.quantile(med_sub, [0.025, 0.975])],
             frac_cr_mayor=float(np.mean(D3 > 0)),
             mde=float(np.quantile(np.abs(nulo3), 0.95)))
for cl in ["excitatoria / sincronía", "inhibitoria"]:
    m = CLASE_INT == cl
    RES43[cl] = dict(n=int(m.sum()), delta_mediana=float(np.median(D3[m])),
                     p_wilcoxon=float(stats.wilcoxon(F_CR[m], F_CU[m]).pvalue) if m.sum() >= 6 else None)

print(f"Pares: {len(P3)} ({BIEN.sum()} con ≥ 10 coincidencias esperadas por contexto)")
print(f"Fuerza mediana: CR = {np.median(F_CR):.2f}  CU = {np.median(F_CU):.2f}  "
      f"Δ mediano = {np.median(D3):+.3f}  (permutación p = {p3:.3f}; Wilcoxon p = {p3_w:.3f}); "
      f"|Δ| detectable ≈ {RES43['mde']:.3f}")
print(f"Sólo pares bien medidos: Δ mediano = {np.median(D3[BIEN]):+.3f} (Wilcoxon p = {p3_w_bien:.3f})")
print(f"CR submuestreado a {n_cu} ensayos: Δ mediano = {np.median(med_sub):+.3f} "
      f"(IC 95 % entre submuestreos {np.quantile(med_sub, 0.025):+.3f} a {np.quantile(med_sub, 0.975):+.3f})")
for cl in ["excitatoria / sincronía", "inhibitoria"]:
    print(f"  {cl}: n = {RES43[cl]['n']}, Δ mediano = {RES43[cl]['delta_mediana']:+.3f}, "
          f"Wilcoxon p = {RES43[cl]['p_wilcoxon']:.3f}")

# %%
fig, axs = plt.subplots(1, 3, figsize=(10, 3.1), gridspec_kw=dict(wspace=0.4, width_ratios=[1.1, 1, 1.1]))
ax = axs[0]
for cl, col in [("excitatoria / sincronía", ACENTO), ("inhibitoria", "#D62728")]:
    m = CLASE_INT == cl
    ax.scatter(F_CU[m], F_CR[m], s=np.where(BIEN[m], 16, 6), color=col, alpha=0.75, lw=0, label=cl)
todo = np.r_[F_CR, F_CU]
lim = (todo.min() - 0.1, todo.max() + 0.1)
ax.plot(lim, lim, color=TINTA, lw=0.7, ls="--")
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("Fuerza en CU (exceso relativo)")
ax.set_ylabel("Fuerza en CR (exceso relativo)")
ax.set_title(f"Cada punto un par (n = {len(P3)})", fontsize=9)
ax.legend(fontsize=6.5, loc="upper left")
ax = axs[1]
ax.hist(nulo3, bins=30, color="#C8C8C8", edgecolor="white")
ax.axvline(np.median(D3), color=VERDE_CR, lw=2)
ax.set_xlabel("Δ fuerza mediana (CR − CU)")
ax.set_yticks([])
ax.set_title(f"Permutando el contexto · {p_txt(p3)}", fontsize=9)
ax = axs[2]
i_ej = int(np.argmax(np.where(CLASE_INT == "excitatoria / sincronía", NB_CR + NB_CU, -1)))
r_ej = P3.iloc[i_ej]
for m, col, lab in [(CTX3 == "CR", VERDE_CR, "CR"), (CTX3 == "CU", GRIS_CU, "CU")]:
    S = CC3[i_ej, m].sum(0)
    ax.step(L_MS, S / base_gauss_hueca(S), where="mid", color=col, lw=1.2, label=lab)
ax.axhline(1, color=TINTA, lw=0.5, ls=":")
ax.set_xlim(-20, 20)
ax.set_xlabel("Lag (ms)")
ax.set_ylabel("Conteo / base")
ax.set_title(f"Ejemplo N{int(r_ej.a)} → N{int(r_ej.b)}", fontsize=9)
ax.legend(fontsize=7)
guardar(fig, "parte4/ccg_por_contexto.png")
plt.show()

# %% [markdown]
# **Cómo leerlo.**
# - **Izquierda**: si el contexto recompensado reforzara (o debilitara) las interacciones finas, los puntos quedarían
#   sistemáticamente por encima (o por debajo) de la diagonal. Están repartidos a ambos lados: la dispersión es ruido de
#   estimación (cada par tiene pocas coincidencias por contexto; los puntos grandes son los pares bien medidos).
# - **Centro**: distribución del Δ mediano permutando la etiqueta de contexto. No está centrada exactamente en 0 porque
#   CR tiene más ensayos y eso sesga levemente el cociente conteo/base; por eso se compara contra la permutación (que
#   conserva los tamaños de grupo) y no contra 0. El Δ observado cae en el medio.
# - **Derecha**: un par de ejemplo (el de más coincidencias). El pico a +1–4 ms está en los dos contextos, con la misma altura.
#
# **Conclusión de IV.3.** Las interacciones de milisegundos son **estables entre contextos**: lo que encontramos en la
# Parte III.b es una propiedad del circuito que no se reconfigura con el contexto (al menos a esta resolución: cambios
# en la fuerza mediana mayores a ~0,05 los habríamos detectado). Junto con IV.1: el contexto cambia la tasa, pero ni la
# co-variación lenta (r_sc) ni la sincronía fina.

# %% [markdown]
# ### IV.4 · ¿La coordinación ayuda o perjudica a decodificar el olor?
#
# Que el r_sc **medio** no cambie con el contexto no dice si las correlaciones **importan para el código**. Lo que importa
# no es su tamaño sino su **estructura** respecto de las respuestas: si las neuronas que prefieren el mismo olor fluctúan
# juntas, el ruido compartido se confunde con la señal y las correlaciones **limitan** la información (Averbeck,
# Latham & Pouget 2006); con otra estructura pueden **ayudar**.
#
# **Método.**
# - **Features**: conteos de las 44 neuronas en 0–0,5 s tras la primera inhalación (la época de olor de IV.1). Como
#   variante, 0–1 s (incluye la salida del contexto en CU).
# - **Etiqueta**: olor recompensado (OR: tipos 1, 2) vs no recompensado (OU: 3, 4), **por separado en cada contexto**:
#   CR (63 OR vs 24 OU) y CU (30 vs 33).
# - **Decodificador**: regresión logística regularizada (C = 1) con estandarización, entrenada sólo con los datos de
#   entrenamiento de cada fold.
# - **Validación** (chequeo TIME de Uribarri): ensayos vecinos se parecen (deriva lenta de tasas, motivación), así que
#   partir al azar filtra información. Usamos `GroupKFold` (5 folds) con **bloques de 20 ensayos contiguos** como grupos:
#   nunca se entrena y testea con ensayos del mismo bloque.
# - **Métrica**: *balanced accuracy* (en CR hay 63 vs 24: un decodificador que siempre dice "OR" tendría 72 % de accuracy
#   pero 50 % balanceada). **Azar**: el mismo procedimiento con las etiquetas permutadas (200 veces).
# - **Mezcla que destruye las correlaciones** (*shuffle*): dentro de cada clase, se permutan los ensayos **de cada neurona
#   por separado**. Cada neurona conserva su distribución de respuestas a cada olor, pero se pierde la co-variación
#   entre neuronas. Se mezcla **dentro de cada fold** (entrenamiento y test por separado) para no mezclar ensayos de
#   bloques distintos. 100 repeticiones.
# - **Lectura**: real < mezclado → las correlaciones **perjudican**; real > mezclado → **ayudan**.
# - **Comparación entre contextos en igualdad**: CR y CU tienen distinto número de ensayos y desbalance. Para comparar el
#   efecto de las correlaciones (real − mezclado) entre contextos, submuestreamos ambos a 30 OR + 24 OU (100 veces).

# %%
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

BLOQUE = 20
CV4 = GroupKFold(n_splits=5)


def conteos_ventana(tr, a, b):
    ev = tr.t_inhal.values
    return np.array([np.searchsorted(spikes[n], ev + b) - np.searchsorted(spikes[n], ev + a) for n in ESTABLES], float).T


def mezclar(X, y):
    """Permuta los ensayos de cada neurona por separado dentro de cada clase: destruye la co-variación entre neuronas."""
    Xs = X.copy()
    for c in np.unique(y):
        f = np.where(y == c)[0]
        for j in range(X.shape[1]):
            Xs[f, j] = X[RNG.permutation(f), j]
    return Xs


def decodificar(X, y, grupos, mezcla=False):
    """Balanced accuracy por fold (lista)."""
    acc = []
    for itr, ite in CV4.split(X, y, grupos):
        Xtr, Xte = X[itr], X[ite]
        if mezcla:
            Xtr, Xte = mezclar(Xtr, y[itr]), mezclar(Xte, y[ite])
        mod = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
        mod.fit(Xtr, y[itr])
        acc.append(balanced_accuracy_score(y[ite], mod.predict(Xte)))
    return np.array(acc)


VENT4 = {"0–0,5 s": (0.0, 0.5), "0–1 s": (0.0, 1.0)}
CTX4 = {"CR": [1, 3], "CU": [2, 4]}
RES44 = {}
for vn, (a, b) in VENT4.items():
    for cn, tipos in CTX4.items():
        tr = VALIDOS[VALIDOS.tipo.isin(tipos)]
        X = conteos_ventana(tr, a, b)
        y = tr.tipo.isin([1, 2]).values.astype(int)            # 1 = olor recompensado
        g = tr.index.values // BLOQUE
        real = decodificar(X, y, g)
        mezc = np.array([decodificar(X, y, g, mezcla=True).mean() for _ in range(100)])
        azar = np.array([decodificar(X, RNG.permutation(y), g).mean() for _ in range(200)])
        RES44[(vn, cn)] = dict(n_or=int(y.sum()), n_ou=int((1 - y).sum()), real=float(real.mean()),
                               real_folds=real, mezcla=mezc, azar=azar,
                               p_vs_azar=float((np.sum(azar >= real.mean()) + 1) / (len(azar) + 1)),
                               p_vs_mezcla=float((np.sum(np.abs(mezc - mezc.mean()) >= abs(real.mean() - mezc.mean())) + 1)
                                                 / (len(mezc) + 1)))
        o = RES44[(vn, cn)]
        print(f"{vn:8s} {cn}: OR/OU = {o['n_or']}/{o['n_ou']}  real = {o['real']:.3f} (folds {np.round(real, 2)})  "
              f"mezclado = {mezc.mean():.3f} ± {mezc.std():.3f}  azar = {azar.mean():.3f} (95 % {np.quantile(azar, 0.95):.3f})  "
              f"p vs azar = {o['p_vs_azar']:.3f}  p vs mezclado = {o['p_vs_mezcla']:.3f}")

# comparación entre contextos con los mismos tamaños (30 OR + 24 OU), ventana principal
N_OR, N_OU = 30, 24
DIF_CTX = {cn: [] for cn in CTX4}
a, b = VENT4["0–0,5 s"]
for cn, tipos in CTX4.items():
    tr = VALIDOS[VALIDOS.tipo.isin(tipos)]
    X = conteos_ventana(tr, a, b)
    y = tr.tipo.isin([1, 2]).values.astype(int)
    g = tr.index.values // BLOQUE
    for _ in range(100):
        s = np.sort(np.r_[RNG.choice(np.where(y == 1)[0], N_OR, replace=False),
                          RNG.choice(np.where(y == 0)[0], N_OU, replace=False)])
        r_ = decodificar(X[s], y[s], g[s]).mean()
        m_ = np.mean([decodificar(X[s], y[s], g[s], mezcla=True).mean() for _ in range(5)])
        DIF_CTX[cn].append((r_, m_))
    DIF_CTX[cn] = np.array(DIF_CTX[cn])
d_cr, d_cu = DIF_CTX["CR"][:, 0] - DIF_CTX["CR"][:, 1], DIF_CTX["CU"][:, 0] - DIF_CTX["CU"][:, 1]
for cn, d in [("CR", d_cr), ("CU", d_cu)]:
    print(f"Igualados ({N_OR} OR + {N_OU} OU) {cn}: real = {DIF_CTX[cn][:, 0].mean():.3f}  "
          f"mezclado = {DIF_CTX[cn][:, 1].mean():.3f}  real − mezclado = {d.mean():+.3f} "
          f"(IC 95 % {np.quantile(d, 0.025):+.3f} a {np.quantile(d, 0.975):+.3f})")
dd = d_cr[:, None] - d_cu[None, :]
print(f"Diferencia CR − CU del efecto de las correlaciones: {dd.mean():+.3f} "
      f"(IC 95 % {np.quantile(dd, 0.025):+.3f} a {np.quantile(dd, 0.975):+.3f})")

# %%
fig, axs = plt.subplots(1, 3, figsize=(10, 3.1), gridspec_kw=dict(wspace=0.38, width_ratios=[1, 1, 0.9]))
for ax, vn in zip(axs[:2], VENT4):
    for k, cn in enumerate(CTX4):
        o = RES44[(vn, cn)]
        x0 = k * 1.2
        vp = ax.violinplot([o["azar"], o["mezcla"]], positions=[x0 - 0.3, x0 + 0.3], widths=0.35, showextrema=False)
        for body, col in zip(vp["bodies"], ["#DDDDDD", "#A9C4F5"]):
            body.set_facecolor(col); body.set_alpha(1); body.set_edgecolor("none")
        ax.errorbar(x0, o["real"], yerr=o["real_folds"].std(ddof=1) / np.sqrt(len(o["real_folds"])), fmt="o",
                    color=VERDE_CR if cn == "CR" else GRIS_CU, ms=8, capsize=3, zorder=3)
        ax.text(x0, 0.32, f"{cn}\n{o['n_or']} OR / {o['n_ou']} OU", ha="center", va="bottom", fontsize=7.5)
    ax.axhline(0.5, color=TINTA, lw=0.5, ls=":")
    ax.set_xticks([-0.3, 0, 0.3, 0.9, 1.2, 1.5])
    ax.set_xticklabels(["azar", "real", "mezcl.", "azar", "real", "mezcl."], fontsize=7.5)
    ax.set_ylim(0.3, 1.03)
    ax.set_title(f"Olor OR vs OU · {vn}", fontsize=9)
axs[0].set_ylabel("Balanced accuracy (CV por bloques)")
ax = axs[2]
vp = ax.violinplot([d_cr, d_cu], positions=[0, 1], widths=0.6, showextrema=False)
for body, col in zip(vp["bodies"], [VERDE_CR, GRIS_CU]):
    body.set_facecolor(col); body.set_alpha(0.6); body.set_edgecolor("none")
ax.scatter([0, 1], [d_cr.mean(), d_cu.mean()], color=TINTA, s=18, zorder=3)
ax.axhline(0, color=TINTA, lw=0.6)
ax.set_xticks([0, 1]); ax.set_xticklabels(["CR", "CU"])
ax.set_ylabel("real − mezclado")
ax.set_title(f"Efecto de las correlaciones\n(igualados: {N_OR} OR + {N_OU} OU)", fontsize=9)
guardar(fig, "parte4/decodificacion.png")
plt.show()

RES44_json = {f"{vn} | {cn}": dict(n_or=o["n_or"], n_ou=o["n_ou"], real=o["real"],
                                   real_sd_folds=float(o["real_folds"].std(ddof=1)),
                                   mezcla=float(o["mezcla"].mean()), mezcla_sd=float(o["mezcla"].std()),
                                   azar=float(o["azar"].mean()), azar_q95=float(np.quantile(o["azar"], 0.95)),
                                   p_vs_azar=o["p_vs_azar"], p_vs_mezcla=o["p_vs_mezcla"])
              for (vn, cn), o in RES44.items()}
RES44_json["igualados"] = dict(n_or=N_OR, n_ou=N_OU,
                               **{f"{cn}_{k}": float(DIF_CTX[cn][:, i].mean()) for cn in CTX4 for i, k in enumerate(["real", "mezcla"])},
                               dif_CR=float(d_cr.mean()), dif_CU=float(d_cu.mean()),
                               dif_CR_menos_CU=float(dd.mean()),
                               dif_CR_menos_CU_ic95=[float(x) for x in np.quantile(dd, [0.025, 0.975])])

# %% [markdown]
# **Cómo leerlo.** En cada panel: gris = azar (etiquetas permutadas), punto = decodificador con los datos reales
# (± error estándar entre folds), celeste = datos mezclados (sin correlaciones entre neuronas).
#
# - **El olor se decodifica bien en los dos contextos**: ~0,78–0,79 de balanced accuracy en 0–0,5 s, muy por encima del
#   azar (p < 0,01), aunque en el promedio poblacional de la Parte II casi no se veía. La información está distribuida
#   en el patrón de la población, no en la actividad media.
# - **Destruir las correlaciones no cambia nada**: real ≈ mezclado en todos los casos. Con estos tamaños, las
#   correlaciones entre neuronas **ni ayudan ni perjudican** de forma detectable a la lectura lineal del olor. Es
#   coherente con que los r_sc sean tan chicos (~0,01–0,02, IV.1): con 44 neuronas no alcanzan para limitar la información.
# - **Entre contextos** (panel derecho, igualando ensayos): el efecto de las correlaciones es ~0 en ambos y la diferencia
#   CR − CU tiene un intervalo muy ancho (de −0,12 a +0,16): no podemos afirmar ni descartar diferencias moderadas.
#
# **Cuidado con dos confusores de comportamiento** (no tenemos los lengüeteos ni la velocidad, sólo el tiempo en el contexto):
# - **En CR, el olor cambia la conducta**: con OU el ratón se queda ~10 s en el contexto, con OR ~2 s. Parte de lo que
#   distingue OR de OU en CR podría ser movimiento (frenar). Pero en CU, donde la velocidad es igual para los dos olores
#   (~0,5 s hasta salir en ambos), el olor se decodifica igual de bien: la información sobre el olor no se explica por
#   la velocidad.
# - **Ventana 0–1 s en CU (0,99)**: en CU el ratón sale ~0,5 s después de inhalar, así que esa ventana incluye la salida y
#   el comienzo de la ventana de respuesta, donde OR·CU (olor asociado a recompensa) y OU·CU pueden llevar a conductas
#   distintas (lamer o no). Por eso la ventana principal es 0–0,5 s; el 0,99 no debe leerse como "codificación de olor".
#
# **Conclusión de IV.4.** La corteza piriforme lleva información del olor (recompensado o no) en ambos contextos, y esa
# información no depende de la coordinación entre neuronas: tratarlas como independientes da la misma lectura.

# %% [markdown]
# ### IV.5 · Ensambles por clustering
#
# IV.2 mostró que la coordinación depende de la semejanza de respuesta de forma continua. Acá agrupamos las neuronas en
# **ensambles** (grupos de neuronas que responden parecido) para preguntar tres cosas:
# 1. ¿Qué tipos de neurona hay? (¿un ensamble "de olor recompensado", uno inhibido…?)
# 2. ¿Las interacciones de ms excitatorias y de sincronía son **dentro** de los ensambles y las inhibitorias **entre**
#    ensambles? (lo que sugería el panel del medio de IV.2: competencia entre ensambles).
# 3. ¿El Δ r_sc por contexto de la época de olor (concentrado en los pares "distintos" en IV.2) está **entre** ensambles?
#
# **Método.**
# - Distancia = 1 − correlación de señal (la matriz `SENAL` de IV.2: PSTH de los 4 tipos con olor, −0,5 a 1,5 s).
# - Clustering jerárquico con *average linkage*; el número de ensambles k (2 a 6) se elige con el **silhouette**
#   (qué tan cerca está cada neurona de su ensamble respecto del más cercano; 1 = perfecto, 0 = en el borde).
# - **¿Los ensambles son reales?** El clustering siempre devuelve grupos. Nulo: desplazar circularmente en el tiempo el
#   PSTH concatenado de cada neurona por separado (conserva la forma de cada respuesta, destruye la coincidencia
#   entre neuronas), recalcular la semejanza y el mejor silhouette; 200 veces.
# - **Dentro vs entre**: test de permutación sobre las etiquetas de ensamble de las neuronas (1000 veces), que conserva
#   el tamaño de los ensambles y la estructura de pares.

# %%
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.metrics import silhouette_score

KS = range(2, 7)


def mejor_cluster(S):
    D = np.clip(1 - S, 0, 2)
    np.fill_diagonal(D, 0)
    Z = linkage(squareform(D, checks=False), method="average")
    sil = {k: silhouette_score(D, fcluster(Z, k, "maxclust"), metric="precomputed") for k in KS}
    return Z, D, sil


Z5, D5, SIL5 = mejor_cluster(SENAL)
K5 = max(SIL5, key=SIL5.get)
ENS = fcluster(Z5, K5, "maxclust")                      # ensamble de cada neurona (orden de ESTABLES)

# nulo: desplazamientos circulares independientes del PSTH concatenado de cada neurona
PSTH_CAT = np.concatenate([POB["inhalacion"][k][:, vent] for k in TIPOS_OLOR], axis=1)
sil_nulo = np.empty(200)
for i in range(200):
    Xn = np.array([np.roll(f, RNG.integers(len(f))) for f in PSTH_CAT])
    sil_nulo[i] = max(mejor_cluster(np.corrcoef(Xn))[2].values())
p_sil = (np.sum(sil_nulo >= SIL5[K5]) + 1) / (len(sil_nulo) + 1)
print("Silhouette por k:", {k: round(v, 3) for k, v in SIL5.items()}, f"→ k = {K5}")
print(f"Silhouette nulo (máx. sobre k): media {sil_nulo.mean():.3f}, 95 % {np.quantile(sil_nulo, 0.95):.3f}; p = {p_sil:.3f}")

# descripción de cada ensamble
desc = clas.loc[ESTABLES].assign(ens=ENS)
TAB_ENS = pd.DataFrame({
    "n": desc.groupby("ens").size(),
    "excitadas": desc.groupby("ens").resp_olor.apply(lambda s: int((s == "excitada").sum())),
    "inhibidas": desc.groupby("ens").resp_olor.apply(lambda s: int((s == "inhibida").sum())),
    "sel_olor": desc.groupby("ens").sel_olor.sum(),
    "sel_contexto": desc.groupby("ens").sel_contexto.sum(),
    "sel_recompensa": desc.groupby("ens").sel_recompensa.sum(),
    "d_olor_hz (mediana)": desc.groupby("ens").d_olor_hz.median().round(1),
})
print(TAB_ENS.to_string())

# dentro / entre ensambles × tipo de interacción (pares sin artefactos; tipo_int viene de IV.2)
mismo = ENS[IA] == ENS[IB]
TAB_DE = pd.crosstab(np.where(mismo, "dentro", "entre"), tipo_int).reindex(
    columns=["ninguna", "dirigida", "sincronía", "inhibitoria"], fill_value=0)
TASA_DE = TAB_DE[["dirigida", "sincronía", "inhibitoria"]].div(TAB_DE.sum(1), axis=0) * 100   # % de pares
print(TAB_DE.to_string())
print("% de pares con cada interacción:\n" + TASA_DE.round(1).to_string())
q1_inh = (q_sig == 0) & (tipo_int == "inhibitoria")         # los inhibitorios "entre distintas" de IV.2
Q1_INH = pd.Series([f"{ENS[i]}-{ENS[j]}" if ENS[i] != ENS[j] else f"dentro {ENS[i]}"
                    for i, j in zip(IA[q1_inh], IB[q1_inh])]).value_counts()
print("Pares inhibitorios del Q1 de semejanza (IV.2) según ensamble:", Q1_INH.to_dict())


def stat_de(ens):
    """Razón de tasas dentro/entre (log) para excitatoria+sincronía menos la de inhibitoria."""
    m = ens[IA] == ens[IB]
    exc = np.isin(tipo_int, ["dirigida", "sincronía"])
    inh = tipo_int == "inhibitoria"
    lr = lambda x: np.log((x[m].mean() + 1e-3) / (x[~m].mean() + 1e-3))
    return lr(exc) - lr(inh), lr(exc), lr(inh)


obs_de = stat_de(ENS)
nulo_de = np.array([stat_de(RNG.permutation(ENS)) for _ in range(N_PERM)])
p_de = [(np.sum(np.abs(nulo_de[:, j] - nulo_de[:, j].mean()) >= abs(obs_de[j] - nulo_de[:, j].mean())) + 1) / (N_PERM + 1)
        for j in range(3)]
print(f"log(dentro/entre): exc+sinc = {obs_de[1]:+.2f} (p = {p_de[1]:.3f}), inhibitoria = {obs_de[2]:+.2f} "
      f"(p = {p_de[2]:.3f}); diferencia = {obs_de[0]:+.2f} (p = {p_de[0]:.3f})")

# Δ r_sc por contexto dentro vs entre ensambles (puente con IV.2), con y sin los pares inhibitorios
DR_DE = {}
for clave in [("Corredor", "CR vs CU"), ("Aproximación", "CR vs CU"), ("Olor", "OR: CR vs CU")]:
    o = RES4[clave]
    d, ok = o["r_cr"] - o["r_cu"], o["ok"]
    for etq, filtro in [("todos", ok), ("sin inhibitorios", ok & (tipo_int != "inhibitoria"))]:
        obs_ = d[filtro & ~mismo].mean() - d[filtro & mismo].mean()
        nul_ = []
        for _ in range(N_PERM):
            e = RNG.permutation(ENS)
            mm = e[IA] == e[IB]
            nul_.append(d[filtro & ~mm].mean() - d[filtro & mm].mean())
        nul_ = np.array(nul_)
        DR_DE[(clave[0], etq)] = dict(dentro=float(d[filtro & mismo].mean()), entre=float(d[filtro & ~mismo].mean()),
                                      e_dentro=float(d[filtro & mismo].std(ddof=1) / np.sqrt((filtro & mismo).sum())),
                                      e_entre=float(d[filtro & ~mismo].std(ddof=1) / np.sqrt((filtro & ~mismo).sum())),
                                      p=float((np.sum(np.abs(nul_) >= abs(obs_)) + 1) / (N_PERM + 1)))
        r_ = DR_DE[(clave[0], etq)]
        print(f"Δ r_sc {clave[0]:13s} ({etq:16s}): dentro = {r_['dentro']:+.3f}  entre = {r_['entre']:+.3f}  p = {r_['p']:.3f}")

# %%
COL_ENS = ["#4A86E8", "#D62728", "#2CA02C", "#FF8C1A", "#9467BD", "#8C564B"]
orden = dendrogram(Z5, no_plot=True)["leaves"]
fig = plt.figure(figsize=(11, 3.4))
gs = fig.add_gridspec(1, 4, width_ratios=[1.25, 0.75, 1, 1], wspace=0.75)
ax = fig.add_subplot(gs[0])
im = ax.imshow(SENAL[np.ix_(orden, orden)], cmap="RdBu_r", vmin=-1, vmax=1)
lim_e = np.r_[0, np.cumsum([np.sum(ENS[orden] == e) for e in pd.unique(ENS[orden])])] - 0.5
for e, (a_, b_) in zip(pd.unique(ENS[orden]), zip(lim_e[:-1], lim_e[1:])):
    ax.add_patch(plt.Rectangle((a_, a_), b_ - a_, b_ - a_, fill=False, color=COL_ENS[e - 1], lw=1.6))
ax.set_xticks([]); ax.set_yticks([])
ax.set_xlabel("neuronas (orden del dendrograma)")
ax.set_title("Semejanza de respuesta", fontsize=9)
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
ax = fig.add_subplot(gs[1])
ax.plot(list(SIL5), list(SIL5.values()), "o-", color=TINTA, ms=4)
ax.axhspan(np.quantile(sil_nulo, 0.025), np.quantile(sil_nulo, 0.975), color="#DDDDDD", zorder=0)
ax.axhline(sil_nulo.mean(), color=GRIS, lw=0.8, ls="--")
ax.set_xticks(list(KS))
ax.set_xlabel("k ensambles"); ax.set_ylabel("silhouette")
ax.set_title(f"k = {K5} · {p_txt(p_sil)}", fontsize=9)
ax = fig.add_subplot(gs[2])
x = np.arange(3)
for dx, fila, col in [(-0.18, "dentro", TINTA), (0.18, "entre", "#BBBBBB")]:
    ax.bar(x + dx, TASA_DE.loc[fila].values, width=0.36, color=col, label=f"{fila} ensambles")
ax.set_xticks(x); ax.set_xticklabels(["dirig.", "sincr.", "inhib."], fontsize=8)
ax.set_ylabel("% de pares con interacción")
ax.set_ylim(0, TASA_DE.values.max() * 1.45)
ax.legend(fontsize=7, loc="upper left")
ax.set_title(f"Interacciones de ms · {p_txt(p_de[0])}", fontsize=9)
ax = fig.add_subplot(gs[3])
x = np.arange(3)
for dx, lugar, col in [(-0.18, "dentro", TINTA), (0.18, "entre", "#BBBBBB")]:
    v = [DR_DE[(ep, "todos")][lugar] for ep in ["Corredor", "Aproximación", "Olor"]]
    e_ = [DR_DE[(ep, "todos")]["e_" + lugar] for ep in ["Corredor", "Aproximación", "Olor"]]
    ax.bar(x + dx, v, yerr=e_, width=0.36, color=col, error_kw=dict(lw=1, capsize=2))
ax.axhline(0, color=TINTA, lw=0.6)
ax.set_xticks(x)
ax.set_xticklabels([f"{n_}\n{p_txt(DR_DE[(ep, 'todos')]['p'])}" for n_, ep in
                    zip(["Corr.", "Aprox.", "Olor"], ["Corredor", "Aproximación", "Olor"])], fontsize=7)
ax.set_ylabel("Δ r_sc (CR − CU)")
ax.set_title("¿Dónde actúa el contexto?\n(negro dentro · gris entre)", fontsize=9)
guardar(fig, "parte4/ensambles_clusters.png")
plt.show()

# PSTH medio de cada ensamble por tipo de ensayo
fig, axs = plt.subplots(1, K5, figsize=(2.5 * K5, 2.4), sharey=True, squeeze=False)
tcv = TC["inhalacion"][vent]
for e, ax in zip(range(1, K5 + 1), axs[0]):
    m = ENS == e
    for k in TIPOS_OLOR:
        ax.plot(tcv, POB["inhalacion"][k][m][:, vent].mean(0), color=COLORES[k], lw=1.3, label=ETIQ[k])
    ax.axvline(0, color=TINTA, lw=0.5, ls="--")
    ax.axhline(0, color="#BBBBBB", lw=0.5)
    t_ = TAB_ENS.loc[e]
    ax.set_title(f"Ensamble {e} (n = {int(t_.n)})", fontsize=9, color=COL_ENS[e - 1])
    ax.text(0.98, 0.02, f"{int(t_.excitadas)} exc · {int(t_.inhibidas)} inh · {int(t_.sel_contexto)} sel. contexto",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7, color=GRIS)
    ax.set_xlabel("tiempo desde la inhalación (s)")
axs[0, 0].set_ylabel("z (media del ensamble)")
axs[0, -1].legend(fontsize=6.5, loc="upper right")
guardar(fig, "parte4/ensambles_psth.png")
plt.show()

RES45 = dict(k=int(K5), silhouette={int(k): float(v) for k, v in SIL5.items()},
             silhouette_nulo_media=float(sil_nulo.mean()), silhouette_nulo_q95=float(np.quantile(sil_nulo, 0.95)),
             p_silhouette=float(p_sil),
             ensambles={int(e): {c: (int(v) if c != "d_olor_hz (mediana)" else float(v)) for c, v in fila.items()}
                        for e, fila in TAB_ENS.iterrows()},
             pct_interaccion={f: {c: float(v) for c, v in TASA_DE.loc[f].items()} for f in TASA_DE.index},
             log_dentro_entre=dict(exc_sinc=float(obs_de[1]), p_exc_sinc=float(p_de[1]), inhibitoria=float(obs_de[2]),
                                   p_inhibitoria=float(p_de[2]), diferencia=float(obs_de[0]), p_diferencia=float(p_de[0])),
             delta_rsc_dentro_entre={f"{k[0]} | {k[1]}": v for k, v in DR_DE.items()})

# %% [markdown]
# **Cómo leerlo.**
# - **Matriz** (izquierda): la semejanza de respuesta ordenada por el dendrograma; los recuadros son los ensambles. Hay
#   bloques, pero difusos. **Silhouette**: el mejor k es 3, con silhouette 0,19 contra 0,14 del nulo (95 % = 0,17;
#   p ≈ 0,015). Hay estructura de ensambles **real pero blanda**: más un continuo con tres "polos" que grupos separados.
# - **Qué es cada ensamble** (PSTH medio):
#   - **Ensamble 3 (6 neuronas) · "de olor"**: excitado por la inhalación con los cuatro tipos, pero **antes** con el olor
#     recompensado (OR, rojo y naranja: pico a ~0,25 s) que con el no recompensado (~0,6 s).
#   - **Ensamble 2 (12) · "de contexto"**: separa los contextos **antes** del olor (CR, rojo y negro, por encima de CU) y
#     sube tarde en OU·CR, cuando el ratón se queda en el contexto recompensado con el olor no recompensado. Es la
#     anticipación de la Parte II, concentrada en un grupo de neuronas.
#   - **Ensamble 1 (26)**: respuesta media débil, con la mayoría de las inhibidas por el olor; es el grupo más
#     heterogéneo.
# - **Interacciones de ms dentro vs entre**: la hipótesis "excitación dentro, inhibición entre ensambles" **no se sostiene**.
#   Las dirigidas y de sincronía son igual de frecuentes dentro que entre, y las inhibitorias tienden a ser más
#   frecuentes **dentro** (6,0 % vs 2,8 % de los pares; p ≈ 0,16). De los 16 pares inhibitorios entre neuronas
#   "distintas" de IV.2, 7 quedan **dentro** del ensamble 1 (el heterogéneo): la observación de IV.2 era sobre semejanza
#   continua y no se traduce en "inhibición entre grupos".
# - **¿Dónde actúa el contexto?** En la época de olor el Δ r_sc es mayor entre ensambles (+0,019) que dentro (+0,001), en la
#   misma dirección que el Q1 de IV.2, pero no es significativo (p ≈ 0,3), tampoco sacando los pares inhibitorios.
#
# **Conclusión de IV.5.** La población se organiza en tres ensambles blandos con roles interpretables (olor, contexto, y
# un grupo mayormente inhibido), pero la coordinación fina no sigue esos límites, y el efecto del contexto sobre r_sc no
# se concentra en ellos de forma detectable.

# %% [markdown]
# ### Resumen de la Parte IV (IV.1–IV.4) y lo que sigue
#
# Los números se guardan en `figuras/resumen_parte4.json` (los usa la presentación). Lo que falta (IV.5–IV.6) está
# detallado en `HANDOFF_parte_IV.md`, con las variables de este notebook que conviene reutilizar.

# %%
res4 = {f"{e} | {c}": dict(n_cr=o["n_cr"], n_cu=o["n_cu"], rsc_cr=float(np.mean(o["r_cr"][o["ok"]])),
                           rsc_cu=float(np.mean(o["r_cu"][o["ok"]])), delta=float(o["delta"]), p=float(o["p"]),
                           delta_aj=float(o["delta_aj"]), p_aj=float(o["p_aj"]),
                           tasa_cr=float(o["tasa_cr"]), tasa_cu=float(o["tasa_cu"]), mde=float(o["mde"]))
        for (e, c), o in RES4.items()}
res4["mantel_rho"], res4["mantel_p"] = float(rho_m), float(p_m)
res4["frac_interaccion_por_cuartil"] = [float(x) for x in frac_int]
res4["p_chi_interaccion"] = float(p_chi)
res4["composicion_por_cuartil"] = {q: {k: int(v) for k, v in fila.items()} for q, fila in COMP_Q.iterrows()}
res4["delta_vs_semejanza"] = {f"{k[0]} | {k[1]}": dict(rho=float(v["rho"]), p=float(v["p"])) for k, v in DELTA_Q.items()}
res4["n_pares"] = int(len(pares_ok))
res4["ccg_contexto"] = RES43
res4["decodificacion"] = RES44_json
res4["ensambles_clusters"] = RES45
(FIG / "resumen_parte4.json").write_text(pd.Series(res4, dtype=object).to_json(force_ascii=False, indent=1), encoding="utf-8")
pd.Series(res4, dtype=object)
