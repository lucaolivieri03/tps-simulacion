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

    listado_resultados = []

    print(f"Iniciando {c} corridas de {n} tiradas cada una. Analizando el número: {e}")
    
    ''' for corrida in range(c):
        listado_corrida={"frec_rel": [], "desvio": [], "promedio": [], "varianza": []} 
        salio_numero = 0
        acum = 0
        print(f"Corrida {corrida + 1}:")
        for i in range(n):
            resultado = random.randint(0, 36)  
            acum += resultado
            tirada = i + 1
            listado_corrida["promedio"].append(acum/tirada)
            print(f"  Tirada {tirada}: Resultado = {resultado}")
            if resultado == e:
                print("¡Número elegido salió!")
                salio_numero += 1
            listado_corrida["frec_rel"].append(salio_numero/tirada) 
    '''
    
    resultados = random.randint(0, 36, size=(c, n))
    print(resultados)
    
if __name__ == "__main__":
    main()