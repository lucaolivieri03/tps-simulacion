import random
import math
import matplotlib.pyplot as plt
import numpy as np



def generador_poisson(lam, cantidad):
    # Genera numeros pseudoaleatorios con distribucion de Poisson
    # lam: tasa media de ocurrencia (lambda), debe ser > 0
    # cantidad: numero de iteraciones/valores a generar
    
    valores_generados = []
    limite = math.exp(-lam)
    
    for _ in range(cantidad):
        p = 1.0
        x = 0
        while True:
            r = random.random()
            p *= r
            if p < limite:
                break
            x += 1
        valores_generados.append(x)
        
    return valores_generados

# Parametros de prueba
lam = 5
tamano_muestra = 10000

# Ejecucion del generador
muestras = generador_poisson(lam, tamano_muestra)

# Ploteo de barras empiricas
valores_unicos = np.arange(0, max(muestras) + 1)
frecuencias = [muestras.count(v)/tamano_muestra for v in valores_unicos]

plt.bar(valores_unicos, frecuencias, color='skyblue', edgecolor='black', alpha=0.7, label='Empirica')

# Superposicion de la PMF Teorica
pdf_teorica = [((lam**k) * math.exp(-lam)) / math.factorial(k) for k in valores_unicos]
plt.plot(valores_unicos, pdf_teorica, color='red', marker='o', linestyle='dashed', linewidth=2, label='Teorica')

plt.title('Testeo Empirico: Generador Poisson')
plt.xlabel('Valor Generado (x)')
plt.ylabel('Frecuencia Relativa')
plt.legend()
plt.show()