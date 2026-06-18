import random
import matplotlib.pyplot as plt
import numpy as np
import math


def generador_binomial(n, p, cantidad):
    # Genera numeros pseudoaleatorios con distribucion Binomial
    # n: numero de ensayos totales por experimento
    # p: probabilidad de exito
    # cantidad: numero de iteraciones/valores a generar
    
    valores_generados = []
    
    for _ in range(cantidad):
        exitos = 0
        for _ in range(n):
            r = random.random()
            if r < p:
                exitos += 1
        valores_generados.append(exitos)
        
    return valores_generados


# Parametros de prueba
n = 20
p = 0.3
tamano_muestra = 10000

# Ejecucion del generador
muestras = generador_binomial(n, p, tamano_muestra)

# Ploteo de barras empiricas
valores_unicos = np.arange(0, n + 1)
frecuencias = [muestras.count(v)/tamano_muestra for v in valores_unicos]

plt.bar(valores_unicos, frecuencias, color='skyblue', edgecolor='black', alpha=0.7, label='Empirica')

# Superposicion de la PMF Teorica
pdf_teorica = [(math.comb(n, k) * (p**k) * ((1-p)**(n-k))) for k in valores_unicos]
plt.plot(valores_unicos, pdf_teorica, color='red', marker='o', linestyle='dashed', linewidth=2, label='Teorica')

plt.title('Testeo Empirico: Generador Binomial')
plt.xlabel('Valor Generado (x)')
plt.ylabel('Frecuencia Relativa')
plt.xlim(-0.5, n + 0.5)
plt.legend()
plt.show()