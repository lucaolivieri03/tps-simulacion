import argparse
import random

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

    # Aquí inicia tu lógica de simulación
    print(f"Iniciando {c} corridas de {n} tiradas cada una. Analizando el número: {e}")

    
    for corrida in range(c):
        print(f"Corrida {corrida + 1}:")
        for tirada in range(n):
            resultado = random.randint(0, 36)  # Simulación de una tirada de ruleta
            print(f"  Tirada {tirada + 1}: Resultado = {resultado}")
            if resultado == e:
                print("    ¡Número elegido salió!")

if __name__ == "__main__":
    main()