
import argparse
import random
import numpy as np
import matplotlib.pyplot as plt

class Apuesta:
    def __init__(self, tipo, valor):
        self.tipo = tipo
        self.valor = valor

    def validar_ganancia(self, numero):
        if self.tipo == 'color':
            return self._validar_color(numero)
        elif self.tipo == 'paridad':
            return self._validar_paridad(numero)
        elif self.tipo == 'docena':
            return self._validar_docena(numero)
        elif self.tipo == 'columna':
            return self._validar_columna(numero)
        elif self.tipo == 'alto_bajo':
            return self._validar_alto_bajo(numero)
        elif self.tipo == 'numero':
            return numero == self.valor
        return False

    def _validar_color(self, numero):
        ROJOS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        NEGROS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        if numero in ROJOS and self.valor == 'rojo':
            return True
        elif numero in NEGROS and self.valor == 'negro':
            return True
        return False

    def _validar_paridad(self, numero):
        if numero % 2 == 0 and self.valor == 'par':
            return True
        elif numero % 2 != 0 and self.valor == 'impar':
            return True
        return False

    def _validar_docena(self, numero):
        if numero <= 12 and self.valor == 'primera':
            return True
        elif 12 < numero <= 24 and self.valor == 'segunda':
            return True
        elif numero > 24 and self.valor == 'tercera':
            return True
        return False

    def _validar_columna(self, numero):
        PRIMERA_COLUMNA = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
        SEGUNDA_COLUMNA = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]
        TERCERA_COLUMNA = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]
        if numero in PRIMERA_COLUMNA and self.valor == 'primera':
            return True
        elif numero in SEGUNDA_COLUMNA and self.valor == 'segunda':
            return True
        elif numero in TERCERA_COLUMNA and self.valor == 'tercera':
            return True
        return False

    def _validar_alto_bajo(self, numero):
        if numero <= 18 and self.valor == 'bajo':
            return True
        elif numero > 18 and self.valor == 'alto':
            return True
        return False

def estrategia_martingala(corridas, tiradas, capital_inicial):
    resultados = []
    for _ in range(corridas):
        resultado_corrida = []
        capital = capital_inicial
        apuesta = 1
        for _ in range(tiradas):
            jugada = Apuesta('paridad', 'par')  # Suponemos que siempre apostamos al par
            numero_ganador = random.randint(0, 36)
            if jugada.validar_ganancia(numero_ganador):
                capital += apuesta
            else:
                capital -= apuesta
                apuesta *= 2  # Duplicamos la apuesta después de perder
                if capital_inicial != -1 and capital < apuesta:
                    break
            resultado_corrida.append(capital)
        resultados.append(resultado_corrida)
    return resultados

def estrategia_dalembert(corridas, tiradas, capital_inicial):
    resultados = []
    for _ in range(corridas):
        capital = capital_inicial
        apuesta = 1
        for _ in range(tiradas):
            resultado_corrida = []
            jugada = Apuesta('paridad', 'par')  # Suponemos que siempre apostamos al par
            numero_ganador = random.randint(0, 36)
            if jugada.validar_ganancia(numero_ganador):
                capital += apuesta
                apuesta = max(1, apuesta - 1)  # Reducimos la apuesta después de ganar, pero no menos de 1
            else:
                capital -= apuesta
                apuesta += 1  # Aumentamos la apuesta después de perder
                if capital_inicial != -1 and capital < apuesta:
                    break
            resultado_corrida.append(capital)
        resultados.append(resultado_corrida)
    return resultados

def estrategia_fibonacci(corridas, tiradas, capital_inicial):
    resultados = []
    for _ in range(corridas):
        capital = capital_inicial
        secuencia_fibonacci = [1, 1]  # Comenzamos con los dos primeros números de Fibonacci
        apuesta_index = 0
        for _ in range(tiradas):
            resultado_corrida = []
            jugada = Apuesta('paridad', 'par')  # Suponemos que siempre apostamos al par
            numero_ganador = random.randint(0, 36)
            if jugada.validar_ganancia(numero_ganador):
                capital += secuencia_fibonacci[apuesta_index]
                apuesta_index = max(0, apuesta_index - 2)  # Retrocedemos dos posiciones en la secuencia después de ganar
            else:
                capital -= secuencia_fibonacci[apuesta_index]
                apuesta_index += 1  # Avanzamos una posición en la secuencia después de perder
                if apuesta_index >= len(secuencia_fibonacci):  # Si llegamos al final de la secuencia, agregamos el siguiente número
                    secuencia_fibonacci.append(secuencia_fibonacci[-1] + secuencia_fibonacci[-2])
                if capital_inicial != -1 and capital < secuencia_fibonacci[apuesta_index]:
                    break
            resultado_corrida.append(capital)
        resultados.append(resultado_corrida)
    return resultados

def main():
    parser = argparse.ArgumentParser(description='Simulación de Ruleta UTN')

    parser.add_argument('-c', '--corridas', type=int, required=True, help='Cantidad de corridas (series de tiradas)')
    parser.add_argument('-n', '--tiradas', type=int, required=True, help='Cantidad de tiradas por cada corrida')
    parser.add_argument('-s', '--estrategia', type=str, required=True, help='Estrategia de apuesta (m - Martingala, d - DAlembert, f - Fibonacci, o - Otra)')
    parser.add_argument('-a', '--capital', type=str, required=True, help='Capital finito o infinito (i - infinito, f - finito)')

    args = parser.parse_args()

    c = args.corridas
    n = args.tiradas
    s = args.estrategia
    a = args.capital

    if a == 'i':
        capital = -1  # Capital infinito
    else:
        capital = 100  # Capital inicial para estrategias con capital finito

    print(f"Iniciando {c} corridas de {n} tiradas cada una. Analizando la estrategia: {s} con capital: {a}")

    if s == 'm':
        resultados = estrategia_martingala(c, n, capital)
    elif s == 'd':
        resultados = estrategia_dalembert(c, n, capital)
    elif s == 'f':
        resultados = estrategia_fibonacci(c, n, capital)
    else:
        print("Estrategia no reconocida. Por favor, elija entre 'm', 'd', 'f' o 'o'.")
        return

if __name__ == '__main__':
    main()