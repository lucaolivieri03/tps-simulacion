"""
╔══════════════════════════════════════════════════════════════════════════╗
║      SIMULACIÓN DE SISTEMA DE INVENTARIO (s, S)  –  Traducción del C        ║
║    (Averill M. Law, Simulation Modeling and Analysis, 5ª ed., 2014, §1.5)  ║
║    Generador: Mersenne Twister (random.Random) en lugar del LCG original   ║
╚══════════════════════════════════════════════════════════════════════════╝

Descripción del modelo
───────────────────────
  Una empresa vende un único producto y desea decidir cuánto inventario
  mantener durante los próximos n meses. Usa una política estacionaria (s, S):

        Z = | S − I   si  I < s     (se ordena hasta S)
            | 0        si  I ≥ s     (no se ordena)

  donde I es el nivel de inventario al inicio del mes.

Eventos del modelo (el menor índice gana ante empate de tiempos)
────────────────────────────────────────────────────────────────
  1 → Llegada de un pedido del proveedor   (order arrival)
  2 → Demanda de un cliente                (demand)
  3 → Fin de la simulación tras n meses    (end simulation)
  4 → Evaluación del inventario (inicio de mes, posible orden)

  Nota: el fin de simulación (3) tiene índice menor que la evaluación (4)
  para que, en t = n, se ejecute primero el fin y no se ordene de más.

Variables aleatorias
─────────────────────
  • Tiempo entre demandas:  exponencial, media 0.1 meses (transf. inversa).
  • Tamaño de la demanda D: discreto,  P(1)=1/6, P(2)=1/3, P(3)=1/3, P(4)=1/6
        (CDF acumulada = 0.167, 0.500, 0.833, 1.000).
  • Lag de entrega (lead time): uniforme en [0.5, 1.0] meses.

Costos
───────
  • Ordenar Z ítems:   K + i·Z   (K=$32 setup,  i=$3 por ítem;  Z=0 → costo 0).
  • Mantenimiento:     h = $1 por ítem y por mes en inventario positivo.
  • Faltante (backlog): p = $5 por ítem y por mes en backlog.

  Costo total promedio por mes = ordenar + mantenimiento + faltante,
  promediado sobre los n meses. Es el criterio para comparar políticas.

Medidas de rendimiento (estimadas por simulación, sin fórmula cerrada)
──────────────────────────────────────────────────────────────────────
  • Costo total promedio por mes
  • Costo de ordenar promedio por mes
  • Costo de mantenimiento promedio por mes  =  h · ∫I⁺(t)dt / n
  • Costo de faltante promedio por mes        =  p · ∫I⁻(t)dt / n

Experimentos
────────────
  • 9 políticas (s, S) del libro.
  • ≥ 30 réplicas independientes por política (IC 95 %).
"""

import random
import math
import statistics
import os
import json
import argparse
from typing import Optional
import numpy as np
import matplotlib
matplotlib.use('Agg')            # sin GUI
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 – Generadores de números aleatorios
#   Usamos random.Random (Mersenne Twister MT19937) en lugar del LCG del libro.
#   Cada instancia random.Random(seed) es independiente — sin estado global.
#     • expon  : X = -mean · ln(U)            (transformada inversa)
#     • uniform: a + U·(b − a)                (uniforme en [a, b])
#     • random_integer: variante discreta a partir de su CDF acumulada
# ─────────────────────────────────────────────────────────────────────────────
def expon(rng: random.Random, mean: float) -> float:
    """Variante exponencial con media `mean` usando transformada inversa."""
    return -mean * math.log(rng.random())


def uniform(rng: random.Random, a: float, b: float) -> float:
    """Variante uniforme U(a, b)."""
    return a + rng.random() * (b - a)


def random_integer(rng: random.Random, prob_distrib: list) -> int:
    """
    Genera un entero según la función de distribución acumulada `prob_distrib`.
    Equivale a la función random_integer del C (Fig. 1.42): recorre la CDF
    hasta que U sea menor que el corte acumulado y devuelve el índice (1-based).
    """
    u = rng.random()
    i = 0
    while u >= prob_distrib[i]:
        i += 1
    return i + 1


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2 – Simulación de inventario (s, S) (traducción directa del C)
# ─────────────────────────────────────────────────────────────────────────────
class InventorySimulation:
    """
    Simulador de un sistema de inventario (s, S) basado en la estructura de
    eventos del libro (§1.5).

    Parámetros
    ----------
    smalls            : int     s — umbral de reorden
    bigs              : int     S — nivel objetivo al ordenar
    initial_inv_level : int     I(0) — nivel de inventario inicial
    num_months        : int     n — horizonte (regla de parada)
    mean_interdemand  : float   media del tiempo entre demandas
    setup_cost        : float   K — costo fijo por orden
    incremental_cost  : float   i — costo por ítem ordenado
    holding_cost      : float   h — costo de mantenimiento por ítem-mes
    shortage_cost     : float   p — costo de faltante por ítem-mes
    minlag, maxlag    : float   rango del lead time (uniforme)
    prob_distrib_demand : list  CDF acumulada de los tamaños de demanda
    seed              : int     semilla del Mersenne Twister
    """

    def __init__(self,
                 smalls: int,
                 bigs: int,
                 initial_inv_level: int = 60,
                 num_months: int = 120,
                 mean_interdemand: float = 0.1,
                 setup_cost: float = 32.0,
                 incremental_cost: float = 3.0,
                 holding_cost: float = 1.0,
                 shortage_cost: float = 5.0,
                 minlag: float = 0.5,
                 maxlag: float = 1.0,
                 prob_distrib_demand: Optional[list] = None,
                 seed: int = 12345):
        self.smalls            = smalls
        self.bigs              = bigs
        self.initial_inv_level = initial_inv_level
        self.num_months        = num_months
        self.mean_interdemand  = mean_interdemand
        self.setup_cost        = setup_cost
        self.incremental_cost  = incremental_cost
        self.holding_cost      = holding_cost
        self.shortage_cost     = shortage_cost
        self.minlag            = minlag
        self.maxlag            = maxlag
        self.prob_distrib_demand = (prob_distrib_demand
                                     if prob_distrib_demand is not None
                                     else [0.167, 0.500, 0.833, 1.000])
        self.rng = random.Random(seed)   # MT19937, instancia propia

        # Número de eventos del modelo
        self.num_events = 4

        # Variables de estado
        self.sim_time        = 0.0
        self.inv_level       = 0
        self.time_last_event = 0.0
        self.amount          = 0   # cantidad del pedido pendiente

        # Contadores estadísticos
        self.total_ordering_cost = 0.0
        self.area_holding        = 0.0   # ∫ I⁺(t) dt
        self.area_shortage       = 0.0   # ∫ I⁻(t) dt

        # Lista de próximos eventos (índice 0 sin usar, eventos 1..4)
        self.time_next_event = [0.0] * (self.num_events + 1)

        # Series temporales para gráficas
        self.ts_time = []
        self.ts_inv  = []

    # ── Inicialización (Fig. 1.36) ──────────────────────────────────────────
    def initialize(self):
        self.sim_time            = 0.0
        self.inv_level           = self.initial_inv_level
        self.time_last_event     = 0.0
        self.total_ordering_cost = 0.0
        self.area_holding        = 0.0
        self.area_shortage       = 0.0
        self.amount              = 0

        # Sin orden pendiente → el evento de llegada se elimina (1e30).
        # La primera evaluación se programa en t = 0 (I(0) podría ser < s).
        self.time_next_event[1] = 1.0e30
        self.time_next_event[2] = self.sim_time + expon(self.rng, self.mean_interdemand)
        self.time_next_event[3] = float(self.num_months)
        self.time_next_event[4] = 0.0

        self.ts_time = [0.0]
        self.ts_inv  = [self.inv_level]

    # ── Timing (Fig. 1.13) ──────────────────────────────────────────────────
    #   El menor índice gana ante empate de tiempos (comparación estricta <),
    #   por eso el fin de simulación (3) se ejecuta antes que la evaluación (4).
    def timing(self):
        min_time  = 1.0e29
        next_type = 0
        for i in range(1, self.num_events + 1):
            if self.time_next_event[i] < min_time:
                min_time  = self.time_next_event[i]
                next_type = i
        if next_type == 0:
            raise RuntimeError(f"Lista de eventos vacía en t={self.sim_time}")
        self.sim_time = min_time
        return next_type

    # ── Actualizar áreas (Fig. 1.41) ────────────────────────────────────────
    #   Si I(t) fue negativo en el intervalo → actualiza área de faltante.
    #   Si fue positivo → actualiza área de mantenimiento.  Si fue 0, nada.
    def update_time_avg_stats(self):
        dt = self.sim_time - self.time_last_event
        self.time_last_event = self.sim_time
        if self.inv_level < 0:
            self.area_shortage -= self.inv_level * dt   # += |inv_level|·dt
        elif self.inv_level > 0:
            self.area_holding += self.inv_level * dt

    # ── Llegada de un pedido (Fig. 1.37) ────────────────────────────────────
    def order_arrival(self):
        # El pedido elimina primero el backlog y el resto suma al inventario.
        self.inv_level += self.amount
        # Ya no hay orden pendiente → eliminar el evento de llegada.
        self.time_next_event[1] = 1.0e30
        self._record()

    # ── Demanda (Fig. 1.38) ─────────────────────────────────────────────────
    def demand(self):
        # Decrementar el inventario según el tamaño de demanda generado.
        self.inv_level -= random_integer(self.rng, self.prob_distrib_demand)
        # Programar la próxima demanda.
        self.time_next_event[2] = self.sim_time + expon(self.rng, self.mean_interdemand)
        self._record()

    # ── Evaluación del inventario (Fig. 1.39) ───────────────────────────────
    def evaluate(self):
        # Si el nivel es menor que s, ordenar hasta S.
        if self.inv_level < self.smalls:
            self.amount = self.bigs - self.inv_level
            self.total_ordering_cost += (self.setup_cost
                                         + self.incremental_cost * self.amount)
            # Programar la llegada del pedido (lead time uniforme).
            self.time_next_event[1] = self.sim_time + uniform(self.rng,
                                                              self.minlag,
                                                              self.maxlag)
        # En cualquier caso, programar la próxima evaluación (un mes después).
        self.time_next_event[4] = self.sim_time + 1.0

    # ── Registro de la serie temporal del nivel de inventario ───────────────
    def _record(self):
        self.ts_time.append(self.sim_time)
        self.ts_inv.append(self.inv_level)

    # ── Ejecutar simulación ─────────────────────────────────────────────────
    def run(self) -> dict:
        self.initialize()
        while True:
            next_type = self.timing()
            self.update_time_avg_stats()
            if next_type == 1:
                self.order_arrival()
            elif next_type == 2:
                self.demand()
            elif next_type == 4:
                self.evaluate()
            elif next_type == 3:
                break   # fin de la simulación
        return self.report()

    # ── Métricas finales (Fig. 1.40) ────────────────────────────────────────
    def report(self) -> dict:
        avg_ordering_cost = self.total_ordering_cost / self.num_months
        avg_holding_cost  = self.holding_cost  * self.area_holding  / self.num_months
        avg_shortage_cost = self.shortage_cost * self.area_shortage / self.num_months
        avg_total_cost    = avg_ordering_cost + avg_holding_cost + avg_shortage_cost
        return {
            "total_cost":    avg_total_cost,
            "ordering_cost": avg_ordering_cost,
            "holding_cost":  avg_holding_cost,
            "shortage_cost": avg_shortage_cost,
            "sim_time":      self.sim_time,
            "ts_time":       list(self.ts_time),
            "ts_inv":        list(self.ts_inv),
        }


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 – Experimento principal: múltiples corridas (réplicas)
#   El modelo (s, S) no tiene fórmula cerrada para el costo, así que las
#   políticas se comparan por simulación con réplicas independientes e IC 95 %.
# ─────────────────────────────────────────────────────────────────────────────
def run_experiment(smalls: int, bigs: int,
                   num_runs: int = 30,
                   num_months: int = 120,
                   base_seed: int = 42,
                   **model_kwargs) -> dict:
    """
    Ejecuta `num_runs` réplicas independientes de la política (s, S) y retorna
    estadísticas con intervalo de confianza al 95 %.
    """
    results = []
    for i in range(num_runs):
        seed = base_seed + i * 1_000_003   # semillas bien separadas
        sim  = InventorySimulation(smalls, bigs,
                                   num_months=num_months,
                                   seed=seed,
                                   **model_kwargs)
        results.append(sim.run())

    def ci95(data):
        """Intervalo de confianza al 95 % (t-Student)."""
        n = len(data)
        m = statistics.mean(data)
        if n < 2:
            return m, 0.0, 0.0
        se = statistics.stdev(data) / math.sqrt(n)
        t  = stats.t.ppf(0.975, df=n - 1)
        return m, m - t * se, m + t * se

    def stats_of(key):
        vals = [r[key] for r in results]
        m, lo, hi = ci95(vals)
        std = statistics.stdev(vals) if len(vals) > 1 else 0.0
        return {"mean": m, "std": std, "ci_lo": lo, "ci_hi": hi, "all": vals}

    return {
        "total_cost":    stats_of("total_cost"),
        "ordering_cost": stats_of("ordering_cost"),
        "holding_cost":  stats_of("holding_cost"),
        "shortage_cost": stats_of("shortage_cost"),
        "last_run":      results[-1],   # última corrida para series temporales
        "num_runs":      num_runs,
        "policy":        (smalls, bigs),
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 – Gráficas
# ─────────────────────────────────────────────────────────────────────────────
PALETTE = {
    "sim":      "#2563EB",   # azul simulación
    "theory":   "#DC2626",   # rojo referencia
    "ci":       "#93C5FD",   # azul claro IC
    "holding":  "#059669",   # verde mantenimiento
    "shortage": "#DC2626",   # rojo faltante
    "ordering": "#F59E0B",   # ámbar ordenar
    "grid":     "#E5E7EB",
    "bg":       "#FFFFFF",
    "title":    "#111827",
    "text":     "#374151",
}

def _style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(PALETTE["bg"])
    ax.grid(True, color=PALETTE["grid"], linewidth=0.8, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    if title:  ax.set_title(title,  fontsize=11, fontweight="bold", color=PALETTE["title"], pad=8)
    if xlabel: ax.set_xlabel(xlabel, fontsize=9,  color=PALETTE["text"])
    if ylabel: ax.set_ylabel(ylabel, fontsize=9,  color=PALETTE["text"])


# ── 4.1  Serie temporal I(t), I⁺(t), I⁻(t) ──────────────────────────────────
def plot_time_series(last_run: dict, smalls: int, bigs: int, out_path: str):
    t   = np.array(last_run["ts_time"])
    inv = np.array(last_run["ts_inv"])
    pos = np.maximum(inv, 0)    # I⁺(t)
    neg = np.maximum(-inv, 0)   # I⁻(t)

    fig, axes = plt.subplots(2, 1, figsize=(14, 7), facecolor=PALETTE["bg"])
    fig.suptitle(f"Series temporales – Una corrida del inventario (s={smalls}, S={bigs})",
                 fontsize=13, fontweight="bold", color=PALETTE["title"], y=1.01)

    # I(t)
    ax = axes[0]
    ax.step(t, inv, where="post", color=PALETTE["sim"], linewidth=1.0, label="I(t) nivel de inventario")
    ax.axhline(smalls, color=PALETTE["ordering"], linestyle="--", linewidth=1.3, label=f"s = {smalls}")
    ax.axhline(bigs,   color=PALETTE["theory"],   linestyle="--", linewidth=1.3, label=f"S = {bigs}")
    ax.axhline(0, color=PALETTE["text"], linewidth=0.8)
    _style_ax(ax, "Nivel de inventario I(t)", "Tiempo (meses)", "Ítems")
    ax.legend(fontsize=8, ncol=3)

    # I⁺(t) y I⁻(t)
    ax = axes[1]
    ax.step(t, pos, where="post", color=PALETTE["holding"],  linewidth=1.0, label="I⁺(t) inventario físico")
    ax.step(t, neg, where="post", color=PALETTE["shortage"], linewidth=1.0, label="I⁻(t) backlog")
    _style_ax(ax, "Inventario físico I⁺(t) y backlog I⁻(t)", "Tiempo (meses)", "Ítems")
    ax.legend(fontsize=8)

    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── 4.2  Comparación de políticas (costos apilados + total con IC) ──────────
def plot_policy_comparison(policies: list, exp_data: list, out_path: str):
    labels   = [f"({s},{S})" for (s, S) in policies]
    ordering = [ed["ordering_cost"]["mean"] for ed in exp_data]
    holding  = [ed["holding_cost"]["mean"]  for ed in exp_data]
    shortage = [ed["shortage_cost"]["mean"] for ed in exp_data]
    total    = [ed["total_cost"]["mean"]    for ed in exp_data]
    tot_lo   = [ed["total_cost"]["ci_lo"]   for ed in exp_data]
    tot_hi   = [ed["total_cost"]["ci_hi"]   for ed in exp_data]

    x = np.arange(len(policies))

    fig, axes = plt.subplots(2, 1, figsize=(14, 9), facecolor=PALETTE["bg"])
    fig.suptitle("Comparación de políticas (s, S) – Costos promedio por mes",
                 fontsize=13, fontweight="bold", color=PALETTE["title"], y=1.01)

    # Barras apiladas de componentes de costo
    ax = axes[0]
    ax.bar(x, ordering, color=PALETTE["ordering"], label="Ordenar")
    ax.bar(x, holding,  bottom=ordering, color=PALETTE["holding"], label="Mantenimiento")
    bottom2 = [o + h for o, h in zip(ordering, holding)]
    ax.bar(x, shortage, bottom=bottom2, color=PALETTE["shortage"], label="Faltante")
    _style_ax(ax, "Composición del costo total por política", "Política (s, S)", "Costo por mes ($)")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.legend(fontsize=9)

    # Costo total con IC 95 % y mejor política resaltada
    ax = axes[1]
    err_lo = [t - lo for t, lo in zip(total, tot_lo)]
    err_hi = [hi - t for t, hi in zip(total, tot_hi)]
    ax.errorbar(x, total, yerr=[err_lo, err_hi], fmt="o-", color=PALETTE["sim"],
                linewidth=2, markersize=7, capsize=4, label="Costo total (media ± IC 95 %)")
    best = int(np.argmin(total))
    ax.scatter([x[best]], [total[best]], s=180, facecolors="none",
               edgecolors=PALETTE["theory"], linewidths=2.5, zorder=5,
               label=f"Mejor: {labels[best]} = ${total[best]:.2f}")
    _style_ax(ax, "Costo total promedio por mes", "Política (s, S)", "Costo total ($)")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.legend(fontsize=9)

    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── 4.3  Distribución de las réplicas (histograma + run chart) ──────────────
def plot_replicas(exp_result: dict, metric: str, label: str, out_path: str):
    vals = exp_result[metric]["all"]
    m    = exp_result[metric]["mean"]
    lo   = exp_result[metric]["ci_lo"]
    hi   = exp_result[metric]["ci_hi"]
    s, S = exp_result["policy"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor=PALETTE["bg"])

    # Histograma
    ax = axes[0]
    ax.hist(vals, bins=10, color=PALETTE["sim"], edgecolor="white", alpha=0.85, density=True)
    ax.axvline(m, color=PALETTE["sim"], linewidth=2, linestyle="-", label=f"Media = {m:.4f}")
    ax.axvspan(lo, hi, alpha=0.2, color=PALETTE["ci"], label="IC 95 %")
    _style_ax(ax, f"Distribución de réplicas – {label}  (s={s}, S={S})", label, "Densidad")
    ax.legend(fontsize=8)

    # Run chart
    ax2 = axes[1]
    ax2.plot(range(1, len(vals) + 1), vals, "o-", color=PALETTE["sim"],
             markersize=4, linewidth=1, alpha=0.8)
    ax2.axhline(m, color=PALETTE["sim"], linewidth=1.5, linestyle="-")
    ax2.fill_between(range(1, len(vals) + 1), lo, hi, alpha=0.2, color=PALETTE["ci"])
    _style_ax(ax2, f"Gráfica de corridas – {label}", "N.º corrida", label)

    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── 4.4  Convergencia de la media con el número de réplicas ─────────────────
def plot_convergence(exp_result: dict, metric: str, label: str, out_path: str):
    vals = exp_result[metric]["all"]
    n_range = range(1, len(vals) + 1)
    cumulative_mean = [statistics.mean(vals[:n]) for n in n_range]
    s, S = exp_result["policy"]

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=PALETTE["bg"])
    ax.plot(list(n_range), cumulative_mean, "-o", color=PALETTE["sim"],
            markersize=4, linewidth=1.5, label="Media acumulada")
    ax.axhline(exp_result[metric]["mean"], color=PALETTE["theory"], linewidth=2,
               linestyle="--", label=f"Media final = {exp_result[metric]['mean']:.4f}")
    _style_ax(ax, f"Convergencia de '{label}' con n.º de réplicas  (s={s}, S={S})",
              "N.º de réplicas", f"Media acumulada de {label}")
    ax.legend(fontsize=9)
    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── 4.5  Mapa de calor del costo total sobre la grilla (s, S) ───────────────
def plot_cost_heatmap(policies: list, exp_data: list, out_path: str):
    s_vals = sorted(set(s for (s, S) in policies))
    S_vals = sorted(set(S for (s, S) in policies))
    cost   = {(s, S): ed["total_cost"]["mean"] for (s, S), ed in zip(policies, exp_data)}

    grid = np.full((len(s_vals), len(S_vals)), np.nan)
    for i, s in enumerate(s_vals):
        for j, S in enumerate(S_vals):
            if (s, S) in cost:
                grid[i, j] = cost[(s, S)]

    fig, ax = plt.subplots(figsize=(9, 6), facecolor=PALETTE["bg"])
    im = ax.imshow(grid, cmap="RdYlGn_r", aspect="auto", origin="lower")
    ax.set_xticks(range(len(S_vals))); ax.set_xticklabels(S_vals)
    ax.set_yticks(range(len(s_vals))); ax.set_yticklabels(s_vals)
    ax.set_xlabel("S (nivel objetivo)", fontsize=9, color=PALETTE["text"])
    ax.set_ylabel("s (umbral de reorden)", fontsize=9, color=PALETTE["text"])
    ax.set_title("Costo total promedio por mes según la política (s, S)",
                 fontsize=12, fontweight="bold", color=PALETTE["title"], pad=10)

    for i in range(len(s_vals)):
        for j in range(len(S_vals)):
            if not np.isnan(grid[i, j]):
                ax.text(j, i, f"{grid[i, j]:.2f}", ha="center", va="center",
                        fontsize=9, fontweight="bold", color="#111827")
    fig.colorbar(im, ax=ax, label="Costo total ($/mes)")
    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── 4.6  Tabla resumen comparativa ──────────────────────────────────────────
def plot_summary_table(policies: list, exp_data: list, out_path: str):
    best = int(np.argmin([ed["total_cost"]["mean"] for ed in exp_data]))
    rows = []
    for (s, S), ed in zip(policies, exp_data):
        ic = f"[{ed['total_cost']['ci_lo']:.2f}, {ed['total_cost']['ci_hi']:.2f}]"
        rows.append({
            "(s, S)":        f"({s}, {S})",
            "Costo total":   f"{ed['total_cost']['mean']:.2f}",
            "IC 95 %":       ic,
            "Ordenar":       f"{ed['ordering_cost']['mean']:.2f}",
            "Mantenimiento": f"{ed['holding_cost']['mean']:.2f}",
            "Faltante":      f"{ed['shortage_cost']['mean']:.2f}",
        })
    df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(14, len(rows) * 0.6 + 1.5), facecolor=PALETTE["bg"])
    ax.axis("off")
    tbl = ax.table(cellText=df.values, colLabels=df.columns, cellLoc="center", loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.1, 1.6)

    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_facecolor("#1E3A5F")
            cell.set_text_props(color="white", fontweight="bold")
        elif row - 1 == best:
            cell.set_facecolor("#DCFCE7")   # resaltar mejor política
            cell.set_text_props(fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#EFF6FF")
        cell.set_edgecolor(PALETTE["grid"])

    ax.set_title("Tabla resumen comparativa – Políticas (s, S) del inventario",
                 fontsize=12, fontweight="bold", color=PALETTE["title"], pad=12)
    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5 – Interfaz de parámetros (CLI interactivo)
# ─────────────────────────────────────────────────────────────────────────────
def get_parameters():
    """Lee parámetros desde la línea de comandos o los solicita interactivamente."""
    parser = argparse.ArgumentParser(
        description="Simulación de inventario (s, S) – Laboratorio de Simulación",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--num_months", type=int, default=None,
                        help="Meses a simular por corrida [default: 120]")
    parser.add_argument("--num_runs",   type=int, default=None,
                        help="Número de réplicas por política [default: 30]")
    parser.add_argument("--initial",    type=int, default=None,
                        help="Nivel de inventario inicial I(0) [default: 60]")
    parser.add_argument("--seed",       type=int, default=42,
                        help="Semilla base del generador [default: 42]")
    parser.add_argument("--outdir",     type=str, default="inventory_results",
                        help="Carpeta de salida [default: inventory_results]")
    parser.add_argument("--no_prompt",  action="store_true",
                        help="No pedir parámetros interactivamente (usar defaults)")
    args = parser.parse_args()

    if args.no_prompt:
        num_months = args.num_months if args.num_months else 120
        num_runs   = args.num_runs   if args.num_runs   else 30
        initial    = args.initial    if args.initial    else 60
    else:
        print("\n" + "═"*60)
        print("   SIMULACIÓN DE INVENTARIO (s, S)  –  Ingreso de parámetros")
        print("═"*60)
        print("  (Presione ENTER para aceptar el valor por defecto)\n")

        nm_def = args.num_months if args.num_months else 120
        nr_def = args.num_runs   if args.num_runs   else 30
        i0_def = args.initial    if args.initial    else 60

        try:
            val = input(f"  Meses por corrida  [{nm_def}]: ").strip()
            num_months = int(val) if val else nm_def

            val = input(f"  Número de réplicas por política  [{nr_def}]: ").strip()
            num_runs = int(val) if val else nr_def

            val = input(f"  Nivel de inventario inicial I(0)  [{i0_def}]: ").strip()
            initial = int(val) if val else i0_def
        except (ValueError, EOFError):
            print("  ⚠  Entrada inválida, usando valores por defecto.")
            num_months, num_runs, initial = nm_def, nr_def, i0_def

    outdir = args.outdir
    seed   = args.seed

    print(f"\n  ✔  meses = {num_months}, réplicas = {num_runs}, I(0) = {initial}")
    print(f"  ✔  Semilla base = {seed}, carpeta = '{outdir}'\n")

    return num_months, num_runs, initial, seed, outdir


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 6 – Runner principal
# ─────────────────────────────────────────────────────────────────────────────
def main():
    num_months, num_runs, initial, seed, outdir = get_parameters()

    os.makedirs(outdir, exist_ok=True)
    print(f"Guardando resultados en '{outdir}/'")
    print("─"*60)

    # Las nueve políticas (s, S) del libro (Fig. 1.44)
    policies = [(20, 40), (20, 60), (20, 80), (20, 100),
                (40, 60), (40, 80), (40, 100),
                (60, 80), (60, 100)]

    # ── Experimento: simular cada política con réplicas ──────────────────────
    print(f"\n[1/3]  Simulando {len(policies)} políticas × {num_runs} réplicas ...")
    exp_data = []
    for (s, S) in policies:
        print(f"  (s={s:>3}, S={S:>3}) ...", end="  ", flush=True)
        ed = run_experiment(s, S, num_runs, num_months, seed,
                            initial_inv_level=initial)
        exp_data.append(ed)
        print(f"Costo total = {ed['total_cost']['mean']:8.2f}  "
              f"(ord={ed['ordering_cost']['mean']:.2f}  "
              f"hold={ed['holding_cost']['mean']:.2f}  "
              f"short={ed['shortage_cost']['mean']:.2f})")

    best = int(np.argmin([ed["total_cost"]["mean"] for ed in exp_data]))
    best_policy = policies[best]

    # ── Gráficas ─────────────────────────────────────────────────────────────
    print("\n[2/3]  Generando gráficas ...")

    # Serie temporal de la mejor política
    plot_time_series(exp_data[best]["last_run"], best_policy[0], best_policy[1],
                     f"{outdir}/ts_best_{best_policy[0]}_{best_policy[1]}.png")

    # Comparación de las 9 políticas
    plot_policy_comparison(policies, exp_data, f"{outdir}/policy_comparison.png")

    # Mapa de calor de costo total
    plot_cost_heatmap(policies, exp_data, f"{outdir}/cost_heatmap.png")

    # Distribución de réplicas y convergencia (costo total de la mejor política)
    plot_replicas(exp_data[best], "total_cost", "Costo total ($/mes)",
                  f"{outdir}/replicas_best.png")
    plot_convergence(exp_data[best], "total_cost", "Costo total",
                     f"{outdir}/conv_best.png")

    # Tabla resumen
    plot_summary_table(policies, exp_data, f"{outdir}/summary_table.png")

    # ── Informe de texto ──────────────────────────────────────────────────────
    print("\n[3/3]  Escribiendo informe de texto ...")
    report_lines = []
    report_lines.append("═"*72)
    report_lines.append("  INFORME DE SIMULACIÓN – SISTEMA DE INVENTARIO (s, S)")
    report_lines.append(f"  I(0) = {initial}  |  meses = {num_months}  |  réplicas = {num_runs}")
    report_lines.append("  K=$32  i=$3  h=$1  p=$5  |  interdemanda media=0.1  lag U(0.5,1.0)")
    report_lines.append("═"*72)
    report_lines.append("")
    header = (f"{'(s, S)':>10} | {'Total':>9} {'IC 95%':>20} | "
              f"{'Ordenar':>9} {'Manten.':>9} {'Faltante':>9}")
    report_lines.append(header)
    report_lines.append("-"*len(header))
    for (s, S), ed in zip(policies, exp_data):
        marca = "  <- MEJOR" if (s, S) == best_policy else ""
        ic = f"[{ed['total_cost']['ci_lo']:.2f}, {ed['total_cost']['ci_hi']:.2f}]"
        report_lines.append(
            f"{f'({s},{S})':>10} | "
            f"{ed['total_cost']['mean']:>9.2f} "
            f"{ic:>20} | "
            f"{ed['ordering_cost']['mean']:>9.2f} "
            f"{ed['holding_cost']['mean']:>9.2f} "
            f"{ed['shortage_cost']['mean']:>9.2f}{marca}"
        )

    report_lines.append("")
    report_lines.append("═"*72)
    report_lines.append(f"  POLÍTICA ÓPTIMA (menor costo): (s={best_policy[0]}, S={best_policy[1]})")
    report_lines.append(f"  Costo total promedio: ${exp_data[best]['total_cost']['mean']:.2f} por mes")
    report_lines.append("")
    report_lines.append("  Nota: cada estimación es el promedio de múltiples réplicas con IC 95 %.")
    report_lines.append("  Aumentar S sube el mantenimiento y baja el faltante; aumentar s")
    report_lines.append("  reduce el faltante a costa de más mantenimiento (ver §1.5.4).")
    report_lines.append("═"*72)

    report_text = "\n".join(report_lines)
    print(report_text)

    with open(f"{outdir}/informe.txt", "w", encoding="utf-8") as f:
        f.write(report_text)

    # ── Guardar datos en JSON ──────────────────────────────────────────────────
    summary_json = {
        "parametros": {
            "initial_inv_level": initial, "num_months": num_months,
            "num_runs": num_runs, "seed": seed,
            "setup_cost": 32.0, "incremental_cost": 3.0,
            "holding_cost": 1.0, "shortage_cost": 5.0,
            "mean_interdemand": 0.1, "minlag": 0.5, "maxlag": 1.0,
            "prob_distrib_demand": [0.167, 0.500, 0.833, 1.000],
        },
        "politicas": [
            {
                "s": s, "S": S,
                "simulacion": {k: v for k, v in ed.items() if k != "last_run"},
            }
            for (s, S), ed in zip(policies, exp_data)
        ],
        "mejor_politica": {"s": best_policy[0], "S": best_policy[1],
                           "costo_total": exp_data[best]["total_cost"]["mean"]},
    }
    with open(f"{outdir}/datos.json", "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2, default=str)

    print(f"\n✓  Listo. Archivos guardados en '{outdir}/'")
    img_files = [f for f in os.listdir(outdir) if f.endswith(".png")]
    print(f"  Imágenes: {len(img_files)} archivos .png")
    print(f"  Datos:    datos.json  |  informe.txt")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
