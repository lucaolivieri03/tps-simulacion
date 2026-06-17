import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import random
import math

def generador_normal(mu, sigma):
    """Genera una variable aleatoria Normal(mu, sigma)
    utilizando el método de Box-Muller."""

    u1 = random.random()
    u2 = random.random()
    z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)

    return mu + sigma * z

def validar_normal(mu=0, sigma=1, N_simulaciones=10000):

    muestras = [generador_normal(mu, sigma)
                for _ in range(N_simulaciones)]

    media_teorica = mu
    var_teorica = sigma**2

    print(f"Media -> Teórica: {media_teorica:.4f} | Empírica: {np.mean(muestras):.4f}")
    print(f"Varianza -> Teórica: {var_teorica:.4f} | Empírica: {np.var(muestras):.4f}")

    x = np.linspace(
        min(muestras),
        max(muestras),
        1000
    )

    pdf_teorica = norm.pdf(x, mu, sigma)
    plt.figure(figsize=(8,5))
    plt.hist(
        muestras,
        bins=50,
        density=True,
        alpha=0.6,
        color='#E05A47',
        label='Frecuencia Empírica'
    )

    plt.plot(
        x,
        pdf_teorica,
        'b-',
        lw=2,
        label='PDF Teórica'
    )

    plt.title(
        f'Validación: Normal (μ={mu}, σ={sigma})',
        fontweight='bold'
    )

    plt.xlabel('x')
    plt.ylabel('Densidad')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig('validacion_normal.png', dpi=300)

validar_normal()