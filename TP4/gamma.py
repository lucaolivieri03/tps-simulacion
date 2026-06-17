import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gamma
import random
import math

def generador_gamma(k, theta):
    """Genera una variable Gamma(k, theta)
    usando suma de exponenciales.
    Requiere k entero positivo."""

    suma = 0
    for _ in range(k):
        u = random.random()
        suma += -theta * math.log(u)

    return suma


def validar_gamma(k=4, theta=2, N_simulaciones=10000):

    muestras = [generador_gamma(k, theta)
                for _ in range(N_simulaciones)]

    media_teorica = k * theta
    var_teorica = k * theta**2

    print(f"Media -> Teórica: {media_teorica:.4f} | Empírica: {np.mean(muestras):.4f}")
    print(f"Varianza -> Teórica: {var_teorica:.4f} | Empírica: {np.var(muestras):.4f}")

    x = np.linspace(
        0,
        max(muestras),
        1000
    )

    pdf_teorica = gamma.pdf(x, a=k, scale=theta)

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
        f'Validación: Gamma(k={k}, θ={theta})',
        fontweight='bold'
    )

    plt.xlabel('x')
    plt.ylabel('Densidad')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig('validacion_gamma.png', dpi=300)

validar_gamma()