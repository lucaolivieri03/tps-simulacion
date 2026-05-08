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
    # Configuración del manejador de argumentos
    parser = argparse.ArgumentParser(description='Simulación de Ruleta UTN')
    
    # -c para corridas, -n para tiradas, -e para número elegido
    parser.add_argument('-c', '--corridas', type=int, required=True, help='Cantidad de corridas (series de tiradas)')
    parser.add_argument('-n', '--tiradas', type=int, required=True, help='Cantidad de tiradas por cada corrida')
    parser.add_argument('-e', '--elegido', type=int, required=True, help='Número elegido para analizar (0-36)')

    args = parser.parse_args()

    # Acceso a los valores
    c = args.corridas
    n = args.tiradas
    e = args.elegido

    listado_resultados = []

    print(f"Iniciando {c} corridas de {n} tiradas cada una. Analizando el número: {e}")
    
    for corrida in range(c):
        listado_corrida={"frec_rel": [], "desvio": [], "promedio": [], "varianza": []} # Crear una lista para cada corrida
        salio_numero = 0
        print(f"Corrida {corrida + 1}:")
        for tirada in range(n):
            resultado = random.randint(0, 36)  # Simulación de una tirada de ruleta
            listado_corrida["promedio"].append(resultado/(n+1)) # Guardar el resultado de la tirada
            listado_corrida
            print(f"  Tirada {tirada + 1}: Resultado = {resultado}")
            if resultado == e:
                print("¡Número elegido salió!")
                salio_numero += 1
            listado_corrida["frec_rel"].append()
    


if __name__ == "__main__":
    main()