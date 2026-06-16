import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import hypergeom
import random

def generador_hipergeometrica(N, n, p):
    """
    Genera una variable estocástica con distribución Hipergeométrica.
    :param N: población total
    :param n: tamaño de la muestra a extraer
    :param p: probabilidad inicial (Clase I / Población total)
    """
    tn = float(N)
    prob = float(p)
    x = 0
    
    for _ in range(n):
        r = random.random()
        
        if r <= prob:
            s = 1.0
            x += 1
        else:
            s = 0.0
            
        # Recálculo dinámico de probabilidad (sin reemplazo)
        prob = (tn * prob - s) / (tn - 1.0)
        tn -= 1.0
        
    return x

def validar_hipergeometrica(N_pob=50, K_clase=20, n_muestra=10, N_simulaciones=10000):
    p_inicial = K_clase / N_pob
    
    # 1. Generación de la muestra empírica
    muestras = [generador_hipergeometrica(N_pob, n_muestra, p_inicial) for _ in range(N_simulaciones)]
    
    # 2. Contraste de métricas
    media_teorica = n_muestra * p_inicial
    factor_correccion = (N_pob - n_muestra) / (N_pob - 1)
    var_teorica = n_muestra * p_inicial * (1 - p_inicial) * factor_correccion
    
    print(f"Media -> Teórica: {media_teorica:.4f} | Empírica: {np.mean(muestras):.4f}")
    print(f"Varianza -> Teórica: {var_teorica:.4f} | Empírica: {np.var(muestras):.4f}")
    
    # 3. Representación Gráfica
    x = np.arange(0, n_muestra + 1)
    prob_teorica = hypergeom.pmf(x, N_pob, K_clase, n_muestra)
    
    plt.figure(figsize=(8, 5))
    plt.hist(muestras, bins=np.arange(-0.5, n_muestra+1.5, 1), density=True, 
             alpha=0.6, color='#E05A47', label='Frecuencia Empírica (Simulación)')
    plt.plot(x, prob_teorica, 'bo-', lw=2, label='PMF Teórica')
    plt.title(f'Validación: Hipergeométrica (N={N_pob}, K={K_clase}, n={n_muestra})', fontweight='bold')
    plt.xlabel('Elementos de Clase I extraídos (x)')
    plt.ylabel('Probabilidad')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('validacion_hipergeometrica.png', dpi=300)

validar_hipergeometrica()