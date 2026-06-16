import numpy as np
import matplotlib.pyplot as plt
import math
import random
from scipy.stats import nbinom

def generador_pascal(k, q):
    """
    Genera una variable estocástica con distribución de Pascal.
    :param k: número de éxitos deseados (entero)
    :param q: probabilidad de fracaso (1 - p)
    :return: cantidad simulada de fracasos antes de los k éxitos
    """
    tr = 1.0
    qr = math.log(q)
    
    for _ in range(k):
        r = random.random()
        tr *= r
        
    nx = math.log(tr) / qr
    return int(nx)

def validar_pascal(k=3, p=0.5, N=10000):
    q = 1 - p
    # 1. Generación de la muestra empírica
    muestras = [generador_pascal(k, q) for _ in range(N)]
    
    # 2. Contraste de métricas teóricas vs empíricas
    media_teorica = (k * q) / p
    var_teorica = (k * q) / (p**2)
    print(f"Media -> Teórica: {media_teorica:.4f} | Empírica: {np.mean(muestras):.4f}")
    print(f"Varianza -> Teórica: {var_teorica:.4f} | Empírica: {np.var(muestras):.4f}")
    
    # 3. Representación Gráfica
    x = np.arange(0, max(muestras) + 1)
    prob_teorica = nbinom.pmf(x, k, p)
    
    plt.figure(figsize=(8, 5))
    plt.hist(muestras, bins=np.arange(-0.5, max(muestras)+1.5, 1), density=True, 
             alpha=0.6, color='#4A90E2', label='Frecuencia Empírica (Simulación)')
    plt.plot(x, prob_teorica, 'ro-', lw=2, label='PMF Teórica')
    plt.title(f'Validación: Pascal (k={k}, p={p}, N={N})', fontweight='bold')
    plt.xlabel('Número de fracasos (x)')
    plt.ylabel('Probabilidad')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('validacion_pascal.png', dpi=300)

validar_pascal()