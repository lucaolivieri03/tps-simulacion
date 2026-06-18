import matplotlib.pyplot as plt
import numpy as np
import random
import math
 
def generador_exponencial(lam, cantidad):
    #Genera numeros pseudoaleatorios con distribucion exponencial.
    #lam: tasa media de ocurrencia (lambda), debe ser > 0.
    #cantidad: numero de valores a generar.
 
    valores_generados = []
 
    for _ in range(cantidad):
        # Generacion de r en el intervalo [0, 1)
        r = random.random()
 
        # Aplicacion de la Ecuacion de Transformada Inversa
        x = -(1 / lam) * math.log(1 - r)
 
        valores_generados.append(x)
 
    return valores_generados

# Parametros de prueba
lam = 0.5
tamano_muestra = 10000
 
# Ejecucion del generador
muestras = generador_exponencial(lam, tamano_muestra)
 
# Ploteo del histograma de densidad
plt.hist(muestras, bins=50, density=True, alpha=0.7,
         color='skyblue', edgecolor='black')
 
# Superposicion de la PDF Teorica
x = np.linspace(0, max(muestras), 200)
pdf_teorica = lam * np.exp(-lam * x)
plt.plot(x, pdf_teorica, color='red', linestyle='dashed',
         linewidth=2, label='PDF Teorica')
 
plt.title('Testeo Empirico: Generador Exponencial')
plt.xlabel('Valor Generado (x)')
plt.ylabel('Frecuencia / Densidad')
plt.legend()
plt.savefig('validacion_exponencial.png', dpi=300)
