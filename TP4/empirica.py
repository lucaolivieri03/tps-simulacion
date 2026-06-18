import random
 
def generador_empirica(valores, probabilidades, cantidad):
    #Genera numeros pseudoaleatorios con distribucion empirica discreta.
    #valores: lista de los valores posibles x_i.
    #probabilidades: lista de probabilidades p_i (deben sumar 1).
    #cantidad: numero de valores a generar.
 
    # Construccion del vector de probabilidades acumuladas F(x_i)
    acumuladas = []
    suma = 0.0
    for p in probabilidades:
        suma += p
        acumuladas.append(suma)
 
    valores_generados = []
 
    for _ in range(cantidad):
        # Generacion de r en el intervalo [0, 1)
        r = random.random()
 
        # Busqueda del primer valor cuya acumulada supere a r (inversa discreta)
        for i in range(len(acumuladas)):
            if r <= acumuladas[i]:
                valores_generados.append(valores[i])
                break
 
    return valores_generados

import matplotlib.pyplot as plt
from collections import Counter
 
# Parametros de prueba
valores = [1, 2, 3, 4, 5]
probabilidades = [0.10, 0.20, 0.40, 0.20, 0.10]
tamano_muestra = 10000
 
# Ejecucion del generador
muestras = generador_empirica(valores, probabilidades, tamano_muestra)
 
# Calculo de frecuencias relativas empiricas
conteo = Counter(muestras)
frec_relativas = [conteo[v] / tamano_muestra for v in valores]
 
# Ploteo comparativo: empirico vs teorico
ancho = 0.35
posiciones = range(len(valores))
 
plt.bar([p - ancho/2 for p in posiciones], frec_relativas, ancho,
        color='skyblue', edgecolor='black', label='Frecuencia Empirica')
plt.bar([p + ancho/2 for p in posiciones], probabilidades, ancho,
        color='salmon', edgecolor='black', label='Probabilidad Teorica')
 
plt.title('Testeo Empirico: Generador Empirico Discreto')
plt.xlabel('Valor (x_i)')
plt.ylabel('Probabilidad / Frecuencia Relativa')
plt.xticks(posiciones, valores)
plt.legend()
plt.savefig('validacion_empirica.png', dpi=300)