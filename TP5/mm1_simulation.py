"""
╔══════════════════════════════════════════════════════════════════════════╗
║          SIMULACIÓN DE COLA M/M/1  –  Traducción del código C            ║
║    (Averill M. Law, Simulation Modeling and Analysis, 5ª ed., 2014)      ║
║    Generador: Mersenne Twister (random.Random) en lugar del LCG original ║
╚══════════════════════════════════════════════════════════════════════════╝

Medidas de rendimiento simuladas
─────────────────────────────────
  • Promedio de clientes en el sistema  (L  = Lq + ρ)
  • Promedio de clientes en cola        (Lq = λ·Wq)
  • Tiempo promedio en sistema          (W  = Wq + 1/μ)
  • Tiempo promedio en cola             (Wq)
  • Utilización del servidor            (ρ = λ/μ)
  • P(n clientes en cola)               para cola finita K = 0,2,5,10,50
  • Probabilidad de denegación          (P_block para cola finita)

Experimentos
────────────
  • λ/μ = 25%, 50%, 75%, 100%, 125%
  • ≥ 30 corridas por experimento

Marco teórico (M/M/1 cola infinita)
─────────────────────────────────────
  ρ  = λ/μ  (factor de utilización; ρ < 1 para sistema estable)
  L  = ρ / (1 − ρ)
  Lq = ρ² / (1 − ρ)
  W  = 1 / (μ − λ) = 1/μ · 1/(1−ρ)
  Wq = λ / (μ(μ − λ)) = ρ/μ · 1/(1−ρ)
  P(n=k) = (1 − ρ) · ρ^k

M/M/1/K (cola finita, tamaño K)
──────────────────────────────
  P(n=k) = ρ^k(1−ρ) / (1 − ρ^(K+2))   si ρ ≠ 1
  P_block = P(n=K+1)   (probabilidad de rechazo)
"""

import random
import math
import statistics
import sys
import os
import json
import argparse
from typing import Optional
import numpy as np
import matplotlib
matplotlib.use('Agg')            # sin GUI
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import pandas as pd
from scipy import stats

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 – Generador de números aleatorios
#   Usamos random.Random (Mersenne Twister MT19937) en lugar del LCG del libro.
#   Ventajas: período 2^19937-1 (vs ~2^31), equidistribuido en 623 dimensiones,
#   y cada instancia random.Random(seed) es independiente — sin estado global.
#   La variable exponencial sigue el mismo método de transformada inversa:
#     X = -mean · ln(U),  U ~ Uniforme(0,1)
# ─────────────────────────────────────────────────────────────────────────────
def expon(rng: random.Random, mean: float) -> float:
    """Variante exponencial con media `mean` usando transformada inversa."""
    return -mean * math.log(rng.random())


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2 – Simulación M/M/1 (traducción directa del C del libro)
# ─────────────────────────────────────────────────────────────────────────────
Q_LIMIT = 1_000_000   # límite de cola (práctico)
BUSY    = 1
IDLE    = 0

class MM1Simulation:
    """
    Simulador de cola M/M/1 basado en la estructura de eventos del libro.
    Parámetros
    ----------
    mean_interarrival : float   1/λ  (minutos entre llegadas)
    mean_service      : float   1/μ  (minutos de servicio)
    num_delays_req    : int     número de clientes a simular (regla de parada)
    q_finite          : int     tamaño de cola finita (0 = sin límite práctico)
    seed              : int     semilla del Mersenne Twister (random.Random)
    """

    def __init__(self,
                 mean_interarrival: float,
                 mean_service: float,
                 num_delays_req: int = 10_000,
                 q_finite: Optional[int] = None,
                 seed: int = 12345):
        self.mean_interarrival = mean_interarrival
        self.mean_service      = mean_service
        self.num_delays_req    = num_delays_req
        self.q_finite          = q_finite     # None → cola infinita
        self.rng               = random.Random(seed)  # MT19937, instancia propia

        # Variables de estado
        self.sim_time        = 0.0
        self.server_status   = IDLE
        self.num_in_q        = 0
        self.time_last_event = 0.0

        # Contadores estadísticos
        self.num_custs_delayed = 0
        self.total_of_delays   = 0.0
        self.area_num_in_q     = 0.0
        self.area_server_status = 0.0
        self.num_blocked       = 0   # rechazados por cola llena

        # Lista de llegadas en cola
        self.time_arrival = []

        # Próximos eventos: [_, llegada, salida]
        self.time_next_event = [0.0, 0.0, 1e30]

        # Series temporales para gráficas
        self.ts_time      = []
        self.ts_num_in_q  = []
        self.ts_server    = []
        self.ts_delays    = []

        # Acumulador de colas a lo largo del tiempo (para distribución empírica)
        self.q_histogram  = {}   # {n_in_q: tiempo_acumulado}

    # ── Inicialización (Fig. 1.12) ──────────────────────────────────────────
    def initialize(self):
        self.sim_time         = 0.0
        self.server_status    = IDLE
        self.num_in_q         = 0
        self.time_last_event  = 0.0
        self.num_custs_delayed = 0
        self.total_of_delays  = 0.0
        self.area_num_in_q    = 0.0
        self.area_server_status = 0.0
        self.num_blocked      = 0
        self.time_arrival     = []
        self.time_next_event  = [0.0,
                                 self.sim_time + expon(self.rng, self.mean_interarrival),
                                 1e30]
        self.ts_time     = [0.0]
        self.ts_num_in_q = [0]
        self.ts_server   = [0]
        self.ts_delays   = []
        self.q_histogram = {}

    # ── Timing (Fig. 1.13) ──────────────────────────────────────────────────
    def timing(self):
        min_time = 1e29
        next_type = 0
        for i in [1, 2]:
            if self.time_next_event[i] < min_time:
                min_time  = self.time_next_event[i]
                next_type = i
        if next_type == 0:
            raise RuntimeError(f"Lista de eventos vacía en t={self.sim_time}")
        self.sim_time = min_time
        return next_type

    # ── Actualizar áreas (Fig. 1.17) ────────────────────────────────────────
    def update_time_avg_stats(self):
        dt = self.sim_time - self.time_last_event
        self.time_last_event = self.sim_time
        self.area_num_in_q     += self.num_in_q     * dt
        self.area_server_status += self.server_status * dt
        # histograma temporal de longitud de cola
        n = self.num_in_q
        self.q_histogram[n] = self.q_histogram.get(n, 0.0) + dt

    # ── Llegada (Fig. 1.14) ─────────────────────────────────────────────────
    def arrive(self):
        # Programar siguiente llegada
        self.time_next_event[1] = self.sim_time + expon(self.rng, self.mean_interarrival)

        if self.server_status == BUSY:
            # ¿Cola finita? Verificar capacidad
            K = self.q_finite
            if K is not None and self.num_in_q >= K:
                self.num_blocked += 1
                return   # Cliente rechazado
            self.num_in_q += 1
            self.time_arrival.append(self.sim_time)
        else:
            # Servidor libre: servicio inmediato con demora = 0
            delay = 0.0
            self.total_of_delays  += delay
            self.ts_delays.append(delay)
            self.num_custs_delayed += 1
            self.server_status     = BUSY
            self.time_next_event[2] = self.sim_time + expon(self.rng, self.mean_service)

        # Series temporales
        self.ts_time.append(self.sim_time)
        self.ts_num_in_q.append(self.num_in_q)
        self.ts_server.append(self.server_status)

    # ── Salida (Fig. 1.15) ──────────────────────────────────────────────────
    def depart(self):
        if self.num_in_q == 0:
            self.server_status      = IDLE
            self.time_next_event[2] = 1e30
        else:
            self.num_in_q -= 1
            delay = self.sim_time - self.time_arrival[0]
            self.time_arrival.pop(0)
            self.total_of_delays   += delay
            self.ts_delays.append(delay)
            self.num_custs_delayed += 1
            self.time_next_event[2] = self.sim_time + expon(self.rng, self.mean_service)

        # Series temporales
        self.ts_time.append(self.sim_time)
        self.ts_num_in_q.append(self.num_in_q)
        self.ts_server.append(self.server_status)

    # ── Ejecutar simulación ─────────────────────────────────────────────────
    def run(self) -> dict:
        self.initialize()
        while self.num_custs_delayed < self.num_delays_req:
            next_type = self.timing()
            self.update_time_avg_stats()
            if next_type == 1:
                self.arrive()
            elif next_type == 2:
                self.depart()

        # ── Métricas finales ────────────────────────────────────────────────
        avg_delay_q  = self.total_of_delays / self.num_custs_delayed   # Wq
        avg_num_q    = self.area_num_in_q / self.sim_time               # Lq
        utilization  = self.area_server_status / self.sim_time          # ρ
        mu_eff       = 1.0 / self.mean_service
        avg_num_sys  = avg_num_q + utilization                          # L = Lq + ρ
        avg_time_sys = avg_delay_q + self.mean_service                  # W = Wq + 1/μ
        total_arr    = self.num_custs_delayed + self.num_blocked
        p_block      = self.num_blocked / total_arr if total_arr > 0 else 0.0

        return {
            "Wq":         avg_delay_q,
            "W":          avg_time_sys,
            "Lq":         avg_num_q,
            "L":          avg_num_sys,
            "rho":        utilization,
            "p_block":    p_block,
            "num_delayed": self.num_custs_delayed,
            "num_blocked": self.num_blocked,
            "sim_time":   self.sim_time,
            "ts_time":    list(self.ts_time),
            "ts_num_in_q": list(self.ts_num_in_q),
            "ts_server":  list(self.ts_server),
            "ts_delays":  list(self.ts_delays),
            "q_histogram": dict(self.q_histogram),
        }


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 – Valores teóricos M/M/1 y M/M/1/K
# ─────────────────────────────────────────────────────────────────────────────
def mm1_theory(lam: float, mu: float) -> dict:
    """Fórmulas cerradas M/M/1 (cola infinita)."""
    rho = lam / mu
    if rho >= 1:
        return {"rho": rho, "L": math.inf, "Lq": math.inf,
                "W": math.inf, "Wq": math.inf}
    L  = rho / (1 - rho)
    Lq = rho**2 / (1 - rho)
    W  = 1 / (mu - lam)
    Wq = lam / (mu * (mu - lam))
    return {"rho": rho, "L": L, "Lq": Lq, "W": W, "Wq": Wq}


def mm1k_theory(lam: float, mu: float, K: int) -> dict:
    """
    M/M/1/K – cola finita con capacidad K (incluyendo el que está siendo servido).
    K aquí es el tamaño de la sala de espera (excluyendo al que está en servicio),
    así la capacidad total es K+1.
    Notación del libro: K = tamaño de la cola.
    """
    rho = lam / mu
    cap = K + 1   # total en el sistema
    if abs(rho - 1) < 1e-10:
        p0 = 1.0 / (cap + 1)
        pn = [p0] * (cap + 1)
    else:
        p0 = (1 - rho) / (1 - rho**(cap + 1))
        pn = [p0 * rho**n for n in range(cap + 1)]

    p_block = pn[-1]                     # P(sistema lleno) = P(n = K+1)
    lam_eff = lam * (1 - p_block)        # tasa efectiva de entrada

    Lq = sum(max(n - 1, 0) * pn[n] for n in range(cap + 1))
    L  = sum(n * pn[n] for n in range(cap + 1))
    if lam_eff > 0:
        W  = L  / lam_eff
        Wq = Lq / lam_eff
    else:
        W = Wq = 0.0

    return {
        "rho":     rho,
        "p_block": p_block,
        "pn":      pn,
        "Lq":      Lq,
        "L":       L,
        "W":       W,
        "Wq":      Wq,
        "lam_eff": lam_eff,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 – Experimento principal: múltiples corridas
# ─────────────────────────────────────────────────────────────────────────────
def run_experiment(lam: float, mu: float,
                   num_runs: int = 30,
                   num_delays: int = 10_000,
                   q_finite: Optional[int] = None,
                   base_seed: int = 42) -> dict:
    """
    Ejecuta `num_runs` réplicas independientes y retorna estadísticas.
    Cada réplica usa una semilla diferente para garantizar independencia.
    """
    mean_ia  = 1.0 / lam
    mean_svc = 1.0 / mu

    results = []
    for i in range(num_runs):
        seed = base_seed + i * 1_000_003   # semillas bien separadas
        sim  = MM1Simulation(mean_ia, mean_svc, num_delays, q_finite, seed)
        res  = sim.run()
        results.append(res)

    def ci95(data):
        """Intervalo de confianza al 95 % (t-Student)."""
        n   = len(data)
        m   = statistics.mean(data)
        if n < 2:
            return m, 0.0, 0.0
        se  = statistics.stdev(data) / math.sqrt(n)
        t   = stats.t.ppf(0.975, df=n - 1)
        return m, m - t * se, m + t * se

    def stats_of(key):
        vals = [r[key] for r in results]
        m, lo, hi = ci95(vals)
        return {"mean": m, "std": statistics.stdev(vals), "ci_lo": lo, "ci_hi": hi,
                "all": vals}

    return {
        "Wq":      stats_of("Wq"),
        "W":       stats_of("W"),
        "Lq":      stats_of("Lq"),
        "L":       stats_of("L"),
        "rho":     stats_of("rho"),
        "p_block": stats_of("p_block"),
        "last_run": results[-1],   # última corrida para gráficas de serie temporal
        "num_runs": num_runs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5 – Gráficas
# ─────────────────────────────────────────────────────────────────────────────
PALETTE = {
    "sim":    "#2563EB",   # azul simulación
    "theory": "#DC2626",   # rojo valor teórico
    "ci":     "#93C5FD",   # azul claro IC
    "grid":   "#E5E7EB",
    "bg":     "#FFFFFF",
    "title":  "#111827",
    "text":   "#374151",
}

def _style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(PALETTE["bg"])
    ax.grid(True, color=PALETTE["grid"], linewidth=0.8, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    if title:  ax.set_title(title,  fontsize=11, fontweight="bold", color=PALETTE["title"], pad=8)
    if xlabel: ax.set_xlabel(xlabel, fontsize=9,  color=PALETTE["text"])
    if ylabel: ax.set_ylabel(ylabel, fontsize=9,  color=PALETTE["text"])


# ── 5.1  Serie temporal Q(t) y B(t) ─────────────────────────────────────────
def plot_time_series(last_run: dict, mu: float, lam: float,
                     rho: float, out_path: str):
    fig, axes = plt.subplots(2, 1, figsize=(14, 7), facecolor=PALETTE["bg"])
    fig.suptitle("Series temporales – Una corrida de la simulación M/M/1",
                 fontsize=13, fontweight="bold", color=PALETTE["title"], y=1.01)

    t  = last_run["ts_time"]
    nq = last_run["ts_num_in_q"]
    bs = last_run["ts_server"]

    # Limitar a los primeros 2000 eventos para claridad
    N  = min(2000, len(t))
    t_p, nq_p, bs_p = t[:N], nq[:N], bs[:N]

    # Q(t)
    ax = axes[0]
    ax.step(t_p, nq_p, where="post", color=PALETTE["sim"], linewidth=1.0, label="Q(t) simulado")
    theory_lq = rho**2 / (1 - rho) if rho < 1 else None
    if theory_lq is not None:
        ax.axhline(theory_lq, color=PALETTE["theory"], linestyle="--",
                   linewidth=1.5, label=f"Lq teórico = {theory_lq:.3f}")
    _style_ax(ax, "Longitud de cola Q(t)", "Tiempo simulado (min)", "Clientes en cola")
    ax.legend(fontsize=8)

    # B(t) – estado del servidor
    ax = axes[1]
    ax.step(t_p, bs_p, where="post", color="#059669", linewidth=1.0, label="B(t) = 1 si ocupado")
    ax.axhline(rho, color=PALETTE["theory"], linestyle="--",
               linewidth=1.5, label=f"ρ teórico = {rho:.3f}")
    ax.set_ylim(-0.05, 1.2)
    _style_ax(ax, "Estado del servidor B(t)", "Tiempo simulado (min)", "Ocupado (1) / Libre (0)")
    ax.legend(fontsize=8)

    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── 5.2  Comparación Simulación vs. Teoría para distintos ρ ─────────────────
def plot_rho_sweep(rho_vals: list, exp_data: list, theory_data: list,
                   out_path: str):
    metrics = [("rho",  "Utilización ρ"),
               ("Lq",   "Clientes promedio en cola  Lq"),
               ("L",    "Clientes promedio en sistema  L"),
               ("Wq",   "Tiempo promedio en cola  Wq (min)"),
               ("W",    "Tiempo promedio en sistema  W (min)")]

    fig, axes = plt.subplots(2, 3, figsize=(16, 9), facecolor=PALETTE["bg"])
    fig.suptitle("M/M/1 – Comparación Simulación vs. Teoría  (λ/μ variable)",
                 fontsize=13, fontweight="bold", color=PALETTE["title"], y=1.01)
    axes_flat = axes.flatten()

    for idx, (key, label) in enumerate(metrics):
        ax = axes_flat[idx]
        sim_means  = [ed[key]["mean"]  for ed in exp_data]
        sim_lo     = [ed[key]["ci_lo"] for ed in exp_data]
        sim_hi     = [ed[key]["ci_hi"] for ed in exp_data]
        th_vals    = [td.get(key, float("nan")) for td in theory_data]

        ax.plot(rho_vals, sim_means, "o-", color=PALETTE["sim"],
                linewidth=2, markersize=6, label="Simulación (media)")
        ax.fill_between(rho_vals, sim_lo, sim_hi,
                        color=PALETTE["ci"], alpha=0.5, label="IC 95 %")
        ax.plot(rho_vals, th_vals, "s--", color=PALETTE["theory"],
                linewidth=1.5, markersize=5, label="Valor teórico")
        _style_ax(ax, label, "ρ = λ/μ", label.split("  ")[0])
        ax.legend(fontsize=7)
        ax.set_xticks(rho_vals)
        ax.set_xticklabels([f"{r:.2f}" for r in rho_vals], fontsize=8)

    # Ocultar el 6.º subplot vacío
    axes_flat[5].set_visible(False)
    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── 5.3  Distribución empírica de Q(t) vs. teórica P(n) ─────────────────────
def plot_queue_dist(last_run: dict, lam: float, mu: float,
                    rho: float, out_path: str):
    hist = last_run["q_histogram"]
    total_t = sum(hist.values())
    if total_t == 0:
        return

    max_n  = min(max(hist.keys()), 25)
    n_vals = list(range(max_n + 1))
    sim_p  = [hist.get(n, 0) / total_t for n in n_vals]
    # P(Nq = 0) = P(N=0) + P(N=1) = (1-ρ) + (1-ρ)ρ = (1-ρ)(1+ρ)
    # P(Nq = n) = P(N = n+1) = (1-ρ)·ρ^(n+1)  para n ≥ 1
    if rho < 1:
        th_p = [(1 - rho) * (1 + rho)] + [(1 - rho) * rho**(n + 1) for n in range(1, max_n + 1)]
    else:
        th_p = [0] * len(n_vals)

    x      = np.array(n_vals)
    width  = 0.35

    fig, ax = plt.subplots(figsize=(12, 5), facecolor=PALETTE["bg"])
    ax.bar(x - width/2, sim_p, width, color=PALETTE["sim"],   alpha=0.85, label="Simulado P(Q=n)")
    ax.bar(x + width/2, th_p,  width, color=PALETTE["theory"],alpha=0.70, label="Teórico P(Nq=n): (1−ρ)(1+ρ) / (1−ρ)ρⁿ⁺¹")
    _style_ax(ax,
              f"Distribución del número de clientes en cola  (ρ={rho:.2f})",
              "n = clientes en cola", "Probabilidad")
    ax.legend(fontsize=9)
    ax.set_xticks(x)
    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── 5.4  P(bloqueo) vs. tamaño de cola K ────────────────────────────────────
def plot_blocking(lam: float, mu: float, rho: float,
                  K_vals: list, exp_data_finite: dict, out_path: str):
    th_block  = [mm1k_theory(lam, mu, K)["p_block"]  for K in K_vals]
    sim_block = [exp_data_finite[K]["p_block"]["mean"] for K in K_vals]
    sim_lo    = [exp_data_finite[K]["p_block"]["ci_lo"] for K in K_vals]
    sim_hi    = [exp_data_finite[K]["p_block"]["ci_hi"] for K in K_vals]

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=PALETTE["bg"])
    ax.plot(K_vals, th_block,  "s--", color=PALETTE["theory"],
            linewidth=2, markersize=7, label="P_block teórico (M/M/1/K)")
    ax.plot(K_vals, sim_block, "o-",  color=PALETTE["sim"],
            linewidth=2, markersize=7, label="P_block simulado (media)")
    ax.fill_between(K_vals, sim_lo, sim_hi, color=PALETTE["ci"],
                    alpha=0.5, label="IC 95 %")
    _style_ax(ax,
              f"Probabilidad de denegación de servicio  (ρ={rho:.2f})",
              "Capacidad de cola K",
              "P(bloqueo)")
    ax.set_xticks(K_vals)
    ax.set_xticklabels([str(k) for k in K_vals])
    ax.legend(fontsize=9)
    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── 5.5  Distribución de las 30 réplicas (histograma + IC) ──────────────────
def plot_replicas(exp_result: dict, metric: str, label: str,
                  theory_val: float, rho: float, out_path: str):
    vals = exp_result[metric]["all"]
    m    = exp_result[metric]["mean"]
    lo   = exp_result[metric]["ci_lo"]
    hi   = exp_result[metric]["ci_hi"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor=PALETTE["bg"])

    # Histograma
    ax = axes[0]
    ax.hist(vals, bins=10, color=PALETTE["sim"], edgecolor="white",
            alpha=0.85, density=True)
    ax.axvline(m,           color=PALETTE["sim"],    linewidth=2, linestyle="-",
               label=f"Media sim. = {m:.4f}")
    ax.axvline(theory_val,  color=PALETTE["theory"], linewidth=2, linestyle="--",
               label=f"Valor teórico = {theory_val:.4f}")
    ax.axvspan(lo, hi, alpha=0.2, color=PALETTE["ci"], label="IC 95 %")
    _style_ax(ax, f"Distribución de réplicas – {label}  (ρ={rho:.2f})", label, "Densidad")
    ax.legend(fontsize=8)

    # Gráfica de corrida (run chart)
    ax2 = axes[1]
    ax2.plot(range(1, len(vals)+1), vals, "o-", color=PALETTE["sim"],
             markersize=4, linewidth=1, alpha=0.8)
    ax2.axhline(m,          color=PALETTE["sim"],    linewidth=1.5, linestyle="-")
    ax2.axhline(theory_val, color=PALETTE["theory"], linewidth=1.5, linestyle="--",
                label=f"Teórico = {theory_val:.4f}")
    ax2.fill_between(range(1, len(vals)+1), lo, hi, alpha=0.2, color=PALETTE["ci"])
    _style_ax(ax2, f"Gráfica de corridas – {label}", "N.º corrida", label)
    ax2.legend(fontsize=8)

    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── 5.6  Tabla resumen comparativa ──────────────────────────────────────────
def plot_summary_table(rho_vals, exp_data, theory_data, out_path):
    rows = []
    for rho_t, ed, td in zip(rho_vals, exp_data, theory_data):
        rows.append({
            "ρ = λ/μ":   f"{rho_t:.2f}",
            "Lq sim.":   f"{ed['Lq']['mean']:.4f}",
            "Lq teo.":   f"{td['Lq']:.4f}" if math.isfinite(td['Lq']) else "∞",
            "L sim.":    f"{ed['L']['mean']:.4f}",
            "L teo.":    f"{td['L']:.4f}"  if math.isfinite(td['L'])  else "∞",
            "Wq sim.":   f"{ed['Wq']['mean']:.4f}",
            "Wq teo.":   f"{td['Wq']:.4f}" if math.isfinite(td['Wq']) else "∞",
            "W sim.":    f"{ed['W']['mean']:.4f}",
            "W teo.":    f"{td['W']:.4f}"  if math.isfinite(td['W'])  else "∞",
            "ρ sim.":    f"{ed['rho']['mean']:.4f}",
            "ρ teo.":    f"{td['rho']:.4f}",
        })

    df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(16, len(rows) * 0.7 + 1.5),
                           facecolor=PALETTE["bg"])
    ax.axis("off")
    tbl = ax.table(
        cellText  = df.values,
        colLabels = df.columns,
        cellLoc   = "center",
        loc       = "center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.1, 1.6)

    # Estilo encabezado
    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_facecolor("#1E3A5F")
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#EFF6FF")
        cell.set_edgecolor(PALETTE["grid"])

    ax.set_title("Tabla resumen comparativa – Simulación vs. Teoría M/M/1",
                 fontsize=12, fontweight="bold", color=PALETTE["title"], pad=12)
    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── 5.7  Convergencia de la media con el número de réplicas ─────────────────
def plot_convergence(exp_result: dict, metric: str, label: str,
                     theory_val: float, rho: float, out_path: str):
    vals = exp_result[metric]["all"]
    n_range = range(1, len(vals) + 1)
    cumulative_mean = [statistics.mean(vals[:n]) for n in n_range]

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=PALETTE["bg"])
    ax.plot(list(n_range), cumulative_mean, "-o", color=PALETTE["sim"],
            markersize=4, linewidth=1.5, label="Media acumulada")
    ax.axhline(theory_val, color=PALETTE["theory"], linewidth=2,
               linestyle="--", label=f"Valor teórico = {theory_val:.4f}")
    _style_ax(ax,
              f"Convergencia de '{label}' con n.º de réplicas  (ρ={rho:.2f})",
              "N.º de réplicas",
              f"Media acumulada de {label}")
    ax.legend(fontsize=9)
    plt.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 6 – Interfaz de parámetros (CLI interactivo)
# ─────────────────────────────────────────────────────────────────────────────
def get_parameters():
    """
    Lee parámetros desde la línea de comandos o los solicita interactivamente.
    """
    parser = argparse.ArgumentParser(
        description="Simulación M/M/1 – Laboratorio de Simulación",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--mu",         type=float, default=None,
                        help="Tasa de servicio μ (clientes/min) [default: 2.0]")
    parser.add_argument("--num_runs",   type=int,   default=None,
                        help="Número de réplicas por experimento [default: 30]")
    parser.add_argument("--num_delays", type=int,   default=None,
                        help="Clientes a simular por corrida [default: 10000]")
    parser.add_argument("--seed",       type=int,   default=42,
                        help="Semilla base del generador [default: 42]")
    parser.add_argument("--outdir",     type=str,   default="mm1_results",
                        help="Carpeta de salida [default: mm1_results]")
    parser.add_argument("--no_prompt",  action="store_true",
                        help="No pedir parámetros interactivamente (usar defaults)")
    args = parser.parse_args()

    if args.no_prompt:
        mu         = args.mu         if args.mu         else 2.0
        num_runs   = args.num_runs   if args.num_runs   else 30
        num_delays = args.num_delays if args.num_delays else 10_000
    else:
        print("\n" + "═"*60)
        print("   SIMULACIÓN M/M/1  –  Ingreso de parámetros")
        print("═"*60)
        print("  (Presione ENTER para aceptar el valor por defecto)\n")

        mu_def  = args.mu         if args.mu         else 2.0
        nr_def  = args.num_runs   if args.num_runs   else 30
        nd_def  = args.num_delays if args.num_delays else 10_000

        try:
            val = input(f"  Tasa de servicio  μ  (clientes/min) [{mu_def}]: ").strip()
            mu  = float(val) if val else mu_def

            val = input(f"  Número de réplicas por experimento  [{nr_def}]: ").strip()
            num_runs = int(val) if val else nr_def

            val = input(f"  Clientes por corrida  [{nd_def}]: ").strip()
            num_delays = int(val) if val else nd_def
        except (ValueError, EOFError):
            print("  ⚠  Entrada inválida, usando valores por defecto.")
            mu, num_runs, num_delays = mu_def, nr_def, nd_def

    outdir = args.outdir
    seed   = args.seed

    print(f"\n  ✔  μ = {mu}, réplicas = {num_runs}, clientes/corrida = {num_delays}")
    print(f"  ✔  Semilla base = {seed}, carpeta = '{outdir}'\n")

    return mu, num_runs, num_delays, seed, outdir


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 7 – Runner principal
# ─────────────────────────────────────────────────────────────────────────────
def main():
    mu, num_runs, num_delays, seed, outdir = get_parameters()

    os.makedirs(outdir, exist_ok=True)
    print(f"Guardando resultados en '{outdir}/'")
    print("─"*60)

    # Tasas de arribo: 25%, 50%, 75%, 100%, 125% respecto a μ
    rho_targets  = [0.25, 0.50, 0.75, 1.00, 1.25]
    lam_values   = [r * mu for r in rho_targets]
    K_vals       = [0, 2, 5, 10, 50]   # tamaños de cola finita

    # ── Experimento 1: cola infinita, variando λ ─────────────────────────────
    print("\n[1/4]  Experimento cola infinita – variando λ ...")
    exp_data_inf    = []
    theory_data_inf = []

    for i, (rho_t, lam) in enumerate(zip(rho_targets, lam_values)):
        print(f"  ρ = {rho_t:.2f}  λ = {lam:.4f} ...", end="  ", flush=True)

        if rho_t < 1.0:
            ed = run_experiment(lam, mu, num_runs, num_delays, None, seed)
            td = mm1_theory(lam, mu)
        else:
            # Sistema inestable: corremos igual pero advertimos
            ed = run_experiment(lam, mu, num_runs, min(num_delays, 5_000), None, seed)
            td = mm1_theory(lam, mu)   # devuelve inf
            print("(inestable)", end="  ")

        exp_data_inf.append(ed)
        theory_data_inf.append(td)
        print(f"Lq_sim={ed['Lq']['mean']:.4f}  Lq_teo={td['Lq'] if math.isfinite(td['Lq']) else 'inf'}")

    # ── Experimento 2: cola finita – variando K (con ρ = 0.75) ──────────────
    print("\n[2/4]  Experimento cola finita – variando K (ρ=0.75) ...")
    rho_block = 0.75
    lam_block = rho_block * mu
    exp_data_finite = {}

    for K in K_vals:
        print(f"  K = {K} ...", end="  ", flush=True)
        ed = run_experiment(lam_block, mu, num_runs, num_delays, K, seed)
        exp_data_finite[K] = ed
        print(f"P_block_sim={ed['p_block']['mean']:.5f}  "
              f"P_block_teo={mm1k_theory(lam_block, mu, K)['p_block']:.5f}")

    # ── Gráficas ─────────────────────────────────────────────────────────────
    print("\n[3/4]  Generando gráficas ...")

    # Filtrar rho < 1 para gráficas de convergencia
    idx_stable = [i for i, r in enumerate(rho_targets) if r < 1.0]

    for idx in idx_stable:
        rho_t = rho_targets[idx]
        ed    = exp_data_inf[idx]
        td    = theory_data_inf[idx]

        # Serie temporal
        plot_time_series(
            ed["last_run"], mu, lam_values[idx], rho_t,
            f"{outdir}/ts_rho{int(rho_t*100):03d}.png"
        )

        # Distribución Q(t)
        plot_queue_dist(
            ed["last_run"], lam_values[idx], mu, rho_t,
            f"{outdir}/qdist_rho{int(rho_t*100):03d}.png"
        )

        # Distribución de réplicas y convergencia para Wq
        if math.isfinite(td["Wq"]):
            plot_replicas(
                ed, "Wq", "Wq (min)", td["Wq"], rho_t,
                f"{outdir}/replicas_Wq_rho{int(rho_t*100):03d}.png"
            )
            plot_convergence(
                ed, "Wq", "Wq", td["Wq"], rho_t,
                f"{outdir}/conv_Wq_rho{int(rho_t*100):03d}.png"
            )

    # Comparación global
    plot_rho_sweep(rho_targets, exp_data_inf, theory_data_inf,
                   f"{outdir}/sweep_rho.png")

    # P(bloqueo) vs K
    plot_blocking(lam_block, mu, rho_block, K_vals, exp_data_finite,
                  f"{outdir}/blocking_K.png")

    # Tabla resumen
    plot_summary_table(rho_targets, exp_data_inf, theory_data_inf,
                       f"{outdir}/summary_table.png")

    # ── Informe de texto ──────────────────────────────────────────────────────
    print("\n[4/4]  Escribiendo informe de texto ...")
    report_lines = []
    report_lines.append("═"*70)
    report_lines.append("  INFORME DE SIMULACIÓN M/M/1")
    report_lines.append(f"  μ = {mu}  |  réplicas = {num_runs}  |  "
                        f"clientes/corrida = {num_delays}")
    report_lines.append("═"*70)
    report_lines.append("")
    report_lines.append("─"*70)
    report_lines.append("  EXPERIMENTO 1 – Cola infinita, variando λ")
    report_lines.append("─"*70)
    header = (f"{'ρ':>6} | {'Lq sim':>9} {'Lq teo':>9} | "
              f"{'L sim':>8} {'L teo':>8} | "
              f"{'Wq sim':>8} {'Wq teo':>8} | "
              f"{'W sim':>8} {'W teo':>8} | "
              f"{'ρ sim':>7}")
    report_lines.append(header)
    report_lines.append("-"*len(header))

    for rho_t, ed, td in zip(rho_targets, exp_data_inf, theory_data_inf):
        def fmt(v): return f"{v:.4f}" if math.isfinite(v) else "   inf"
        report_lines.append(
            f"{rho_t:>6.2f} | "
            f"{ed['Lq']['mean']:>9.4f} {fmt(td['Lq']):>9} | "
            f"{ed['L']['mean']:>8.4f} {fmt(td['L']):>8} | "
            f"{ed['Wq']['mean']:>8.4f} {fmt(td['Wq']):>8} | "
            f"{ed['W']['mean']:>8.4f} {fmt(td['W']):>8} | "
            f"{ed['rho']['mean']:>7.4f}"
        )

    report_lines.append("")
    report_lines.append("─"*70)
    report_lines.append("  EXPERIMENTO 2 – Cola finita M/M/1/K  (ρ = 0.75)")
    report_lines.append("─"*70)
    report_lines.append(f"  {'K':>4} | {'P_block sim':>12} {'IC±':>10} | "
                        f"{'P_block teo':>12}")
    report_lines.append("-"*55)
    for K in K_vals:
        ed  = exp_data_finite[K]
        td  = mm1k_theory(lam_block, mu, K)
        m   = ed["p_block"]["mean"]
        lo  = ed["p_block"]["ci_lo"]
        hi  = ed["p_block"]["ci_hi"]
        report_lines.append(
            f"  {K:>4} | {m:>12.6f} [{lo:.4f},{hi:.4f}] | "
            f"{td['p_block']:>12.6f}"
        )

    report_lines.append("")
    report_lines.append("═"*70)
    report_lines.append("  Marco teórico")
    report_lines.append("  ρ = λ/μ  |  L = ρ/(1-ρ)  |  Lq = ρ²/(1-ρ)")
    report_lines.append("  W = 1/(μ-λ)  |  Wq = λ/(μ(μ-λ))")
    report_lines.append("  P(n) = (1-ρ)·ρⁿ  (cola infinita)")
    report_lines.append("  P_block(K) = P(n = K+1)  (cola finita M/M/1/K)")
    report_lines.append("═"*70)

    report_text = "\n".join(report_lines)
    print(report_text)

    with open(f"{outdir}/informe.txt", "w", encoding="utf-8") as f:
        f.write(report_text)

    # Guardar datos en JSON para AnyLogic o comparación externa
    summary_json = {
        "parametros": {"mu": mu, "num_runs": num_runs,
                       "num_delays": num_delays, "seed": seed},
        "experimento_infinita": [
            {
                "rho_objetivo": rho_t,
                "lam": lam,
                "simulacion": {k: v for k, v in ed.items() if k != "last_run"},
                "teoria": {k: (v if math.isfinite(v) else "inf")
                           for k, v in td.items()},
            }
            for rho_t, lam, ed, td
            in zip(rho_targets, lam_values, exp_data_inf, theory_data_inf)
        ],
        "experimento_finito": {
            str(K): {
                "simulacion": {k: v for k, v in exp_data_finite[K].items()
                               if k != "last_run"},
                "teoria": mm1k_theory(lam_block, mu, K),
            }
            for K in K_vals
        },
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