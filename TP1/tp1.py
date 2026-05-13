import argparse
import random
import numpy as np
import matplotlib.pyplot as plt

# Se necesita:
# frecuencia relativa del numero X con respecto a n vs frecuencia relativa esperada
# valor del desvio del numero X con respecto a n VS valor del desvio esperado
# valor del promedio de las tiradas con respecto a n VS valor del promedio esperado
# valor de la varianza de las tiradas con respecto a n VS valor de la varianza esperada
# graficar con matplotlib el comportamiento de cada una de las métricas anteriores con respecto a n
# calcular datos estadisticos con numpy y comparar con los resultados obtenidos en la simulación
def main():
    parser = argparse.ArgumentParser(description='Simulación de Ruleta UTN')
    
    parser.add_argument('-c', '--corridas', type=int, required=True, help='Cantidad de corridas (series de tiradas)')
    parser.add_argument('-n', '--tiradas', type=int, required=True, help='Cantidad de tiradas por cada corrida')
    parser.add_argument('-e', '--elegido', type=int, required=True, help='Número elegido para analizar (0-36)')

    args = parser.parse_args()

    # Acceso a los valores
    c = args.corridas
    n = args.tiradas
    e = args.elegido

    print(f"Iniciando {c} corridas de {n} tiradas cada una. Analizando el número: {e}")

    # === VALORES ESPERADOS (CONSTANTES TEÓRICAS) ===
    frecuenciaEsperada = 1 / 37
    valorPromedioEsperado = 18.0 # (0 + 36) / 2
    valorVarianzaEsperada = 114.0 # (37**2 - 1) / 12
    desvioEsperado = np.sqrt(valorVarianzaEsperada)
        
    corridas = np.random.randint(0, 37, size=(c, n))  #Hasta 37 porque lo expcluye
    print(corridas)
    tiradas_acum = np.arange(1, n + 1) 

    # Frecuencia relativa

    listaFrecuenciasRelativaPorTirada = np.cumsum(corridas == e, axis=1) / tiradas_acum
    print(listaFrecuenciasRelativaPorTirada)

    # Promedio

    listaPromediosPorTirada = np.cumsum(corridas, axis=1) / tiradas_acum
    print(listaPromediosPorTirada)

    # Varianza

    # 1. Promedios acumulados por corrida (fila)
    promedios_acum = np.cumsum(corridas, axis=1) / tiradas_acum

    # 2. Promedios de los cuadrados acumulados por corrida (fila)
    promedios_cuad_acum = np.cumsum(corridas**2, axis=1) / tiradas_acum

    # 3. Varianza acumulada (Fórmula: E[X²] - (E[X])²)
    listaVarianzasPorTirada = promedios_cuad_acum - (promedios_acum**2)

    print(listaVarianzasPorTirada)

    listaDesvioEstandarPorTirada = np.sqrt(listaVarianzasPorTirada)
    print(listaDesvioEstandarPorTirada)

    ## Graficar resultados

    plt.figure(figsize=(14, 10))

    plt.subplot(2, 2, 1)
    plt.plot(tiradas_acum, listaFrecuenciasRelativaPorTirada[0], alpha=1)
    plt.axhline(y=frecuenciaEsperada, color='r', linestyle='--', label='Frecuencia Esperada', alpha=0.7)
    plt.title('Frecuencia Relativa del Número Elegido')
    plt.xlabel('Número de Tiradas')
    plt.ylabel('Frecuencia Relativa')
    plt.legend()

    plt.subplot(2, 2, 2)
    plt.plot(tiradas_acum, listaPromediosPorTirada[0], alpha=1)
    plt.axhline(y=valorPromedioEsperado, color='r', linestyle='--', label='Promedio Esperado',alpha=0.7)
    plt.title('Valor Promedio de las Tiradas')
    plt.xlabel('Número de Tiradas')
    plt.ylabel('Valor Promedio')
    plt.ylabel('Promedio')
    plt.legend()

    plt.subplot(2, 2, 3)
    plt.plot(tiradas_acum, listaVarianzasPorTirada[0], alpha=1)
    plt.axhline(y=valorVarianzaEsperada, color='r', linestyle='--', label='Varianza Esperada', alpha=0.7)
    plt.title('Valor de la Varianza de las Tiradas')
    plt.xlabel('Número de Tiradas')
    plt.ylabel('Valor de la Varianza')
    plt.legend()

    plt.subplot(2, 2, 4)
    plt.plot(tiradas_acum, listaDesvioEstandarPorTirada[0], alpha=1)
    plt.axhline(y=desvioEsperado, color='r', linestyle='--', label='Desvío Esperado', alpha=0.7)
    plt.title('Valor del Desvío Estándar de las Tiradas')
    plt.xlabel('Número de Tiradas')
    plt.ylabel('Valor del Desvío Estándar')
    plt.legend()

    plt.tight_layout()
    plt.savefig('graficas.png')

    # ------------------MULTIPLES CORRIDAS----------------------------------

    plt.figure(figsize=(14, 10))

    plt.subplot(2, 2, 1)
    for i in range(c):
        plt.plot(tiradas_acum, listaFrecuenciasRelativaPorTirada[i], alpha=0.8)
    plt.axhline(y=frecuenciaEsperada, color='r', linestyle='--', label='Frecuencia Esperada', alpha=0.7)
    plt.title('Frecuencia Relativa del Número Elegido')
    plt.xlabel('Número de Tiradas')
    plt.ylabel('Frecuencia Relativa')
    plt.legend()

    plt.subplot(2, 2, 2)
    for i in range(c):
        plt.plot(tiradas_acum, listaPromediosPorTirada[i], alpha=0.8)
    plt.axhline(y=valorPromedioEsperado, color='r', linestyle='--', label='Promedio Esperado',alpha=0.7)
    plt.title('Valor Promedio de las Tiradas')
    plt.xlabel('Número de Tiradas')
    plt.ylabel('Valor Promedio')
    plt.ylabel('Frecuencia Relativa')
    plt.legend()

    plt.subplot(2, 2, 3)
    for i in range(c):
        plt.plot(tiradas_acum, listaVarianzasPorTirada[i], alpha=0.8)
    plt.axhline(y=valorVarianzaEsperada, color='r', linestyle='--', label='Varianza Esperada', alpha=0.7)
    plt.title('Valor de la Varianza de las Tiradas')
    plt.xlabel('Número de Tiradas')
    plt.ylabel('Valor de la Varianza')
    plt.legend()

    plt.subplot(2, 2, 4)
    for i in range(c):
        plt.plot(tiradas_acum, listaDesvioEstandarPorTirada[i], alpha=0.8)
    plt.axhline(y=desvioEsperado, color='r', linestyle='--', label='Desvío Esperado', alpha=0.7)
    plt.title('Valor del Desvío Estándar de las Tiradas')
    plt.xlabel('Número de Tiradas')
    plt.ylabel('Valor del Desvío Estándar')
    plt.legend()

    plt.tight_layout()
    plt.savefig('graficasCorridas.png')

    # ------------------ GRÁFICAS ADICIONALES (SOLO 1RA CORRIDA) ------------------
    
    plt.figure(figsize=(14, 6))

    # 1. Gráfico de barras con la frecuencia absoluta de cada número (Primera corrida)
    plt.subplot(1, 2, 1)
    frecuencias_absolutas = np.bincount(corridas[0], minlength=37)
    numeros = np.arange(37)
    plt.bar(numeros, frecuencias_absolutas, color='skyblue', edgecolor='black', alpha=0.8)
    plt.title('Frecuencia Absoluta de cada número\n(Primera Corrida)')
    plt.xlabel('Número (0-36)')
    plt.ylabel('Frecuencia Absoluta (Ocurrencias)')
    plt.xticks(np.arange(0, 37, 2))

    # 2. Promedio en función de su ocurrencia / Teorema Central del Límite (Gráfica continua)
    plt.subplot(1, 2, 2)
    promedios_finales = promedios_acum[:, -1]
    plt.hist(promedios_finales, bins='auto', density=True, color='lightgreen', edgecolor='black', alpha=0.6, label='Frecuencia Empírica')
    sigma_promedio = desvioEsperado / np.sqrt(n)
    x_val = np.linspace(valorPromedioEsperado - 4*sigma_promedio, valorPromedioEsperado + 4*sigma_promedio, 100)
    y_val = (1 / (np.sqrt(2 * np.pi) * sigma_promedio)) * np.exp(-0.5 * ((x_val - valorPromedioEsperado) / sigma_promedio)**2)
    plt.plot(x_val, y_val, color='blue', linewidth=2, label='Distribución Normal (Teórica)')
    plt.title('Teorema del Límite Central\n(Densidad de los promedios finales)')
    plt.xlabel('Valor del Promedio')
    plt.ylabel('Frecuencia (Densidad)')
    plt.legend()

    plt.tight_layout()
    plt.savefig('graficasAdicionales.png')

    # Mostrar gráficos
    plt.show()

if __name__ == "__main__":
    main()