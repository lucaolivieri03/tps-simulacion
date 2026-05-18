import argparse
import random
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
        if numero == 0:
            return False
        if numero % 2 == 0 and self.valor == 'par':
            return True
        elif numero % 2 != 0 and self.valor == 'impar':
            return True
        return False

    def _validar_docena(self, numero):
        if numero == 0:
            return False
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
        if numero == 0:
            return False
        if numero <= 18 and self.valor == 'bajo':
            return True
        elif numero > 18 and self.valor == 'alto':
            return True
        return False

def estrategia_martingala(corridas, tiradas, capital_inicial, capital_infinito=False):
    resultados = []
    for _ in range(corridas):
        resultado_corrida = []
        capital = capital_inicial
        apuesta = 1
        for _ in range(tiradas):
            jugada = Apuesta('paridad', 'par')
            numero_ganador = random.randint(0, 36)
            if jugada.validar_ganancia(numero_ganador):
                capital += apuesta
                apuesta = 1
                resultado_corrida.append(capital)
            else:
                capital -= apuesta
                apuesta *= 2
                resultado_corrida.append(capital)
                if not capital_infinito and capital < apuesta:
                    break
        resultados.append(resultado_corrida)
    return resultados

def estrategia_dalembert(corridas, tiradas, capital_inicial, capital_infinito=False):
    resultados = []
    for _ in range(corridas):
        resultado_corrida = []
        capital = capital_inicial
        apuesta = 1
        for _ in range(tiradas):
            jugada = Apuesta('paridad', 'par')
            numero_ganador = random.randint(0, 36)
            if jugada.validar_ganancia(numero_ganador):
                capital += apuesta
                apuesta = max(1, apuesta - 1)
                resultado_corrida.append(capital)
            else:
                capital -= apuesta
                apuesta += 1
                resultado_corrida.append(capital)
                if not capital_infinito and capital < apuesta:
                    break
        resultados.append(resultado_corrida)
    return resultados

def estrategia_fibonacci(corridas, tiradas, capital_inicial, capital_infinito=False):
    resultados = []
    for _ in range(corridas):
        resultado_corrida = []
        capital = capital_inicial
        secuencia_fibonacci = [1, 1]
        apuesta_index = 0
        for _ in range(tiradas):
            jugada = Apuesta('paridad', 'par')
            numero_ganador = random.randint(0, 36)
            if jugada.validar_ganancia(numero_ganador):
                capital += secuencia_fibonacci[apuesta_index]
                apuesta_index = max(0, apuesta_index - 2)
                resultado_corrida.append(capital)
            else:
                capital -= secuencia_fibonacci[apuesta_index]
                apuesta_index += 1
                resultado_corrida.append(capital)
                if apuesta_index >= len(secuencia_fibonacci):
                    secuencia_fibonacci.append(secuencia_fibonacci[-1] + secuencia_fibonacci[-2])
                if not capital_infinito and capital < secuencia_fibonacci[apuesta_index]:
                    break
        resultados.append(resultado_corrida)
    return resultados

def estrategia_jacobo(corridas, tiradas, capital_inicial, capital_infinito=False):
    resultados = []
    numeros_jacobo = list(range(22, 37)) + [0, 3, 4, 7, 9, 12, 15, 18]
    apuestas = [Apuesta('numero', num) for num in numeros_jacobo]
    costo_apuesta = len(apuestas)
    for _ in range(corridas):
        resultado_corrida = []
        capital = capital_inicial
        for _ in range(tiradas):
            numero_ganador = random.randint(0, 36)
            gano = any(apuesta.validar_ganancia(numero_ganador) for apuesta in apuestas)
            if gano:
                capital += 13
                resultado_corrida.append(capital)
            else:
                capital -= costo_apuesta
                resultado_corrida.append(capital)
                if not capital_infinito and capital < costo_apuesta:
                    break
        resultados.append(resultado_corrida)
    return resultados

def calcular_frec_rel(corrida, capital_inicial):
    favorables = 0
    frec_rel = []
    for tirada in range(len(corrida)):
        capital_prev = corrida[tirada - 1] if tirada > 0 else capital_inicial
        if corrida[tirada] > capital_prev:
            favorables += 1
        frec_rel.append(favorables / (tirada + 1))
    return frec_rel

def analizar_frec_rel_tiradas_favorables(resultados, capital_inicial):
    num_corridas = len(resultados)
    width = 0.8 / num_corridas
    plt.figure()
    for i, corrida in enumerate(resultados):
        frec_rel = calcular_frec_rel(corrida, capital_inicial)
        x = range(1, len(frec_rel) + 1)
        if num_corridas <= 5:
            offset = [t + (i - num_corridas / 2) * width for t in x]
            plt.bar(offset, frec_rel, width=width, label=f'Corrida {i + 1}', alpha=0.8)
        else:
            plt.plot(x, frec_rel, label=f'Corrida {i + 1}', alpha=0.7)
    plt.axhline(y=18/37, color='r', linestyle='--', label='Prob. teórica (18/37)')
    plt.xlabel('n (número de tiradas)')
    plt.ylabel('fr (frecuencia relativa)')
    plt.title('Frecuencia relativa de tiradas favorables')
    plt.legend()
    plt.show()

def analizar_flujo_capital(resultados, capital_inicial, num_tiradas):
    plt.figure()
    resultados_completos = []
    for corrida in resultados:
        corrida_completa = [capital_inicial] + corrida
        if len(corrida_completa) < num_tiradas + 1:
            ultimo_valor = corrida_completa[-1]
            faltantes = (num_tiradas + 1) - len(corrida_completa)
            corrida_completa.extend([ultimo_valor] * faltantes)
        resultados_completos.append(corrida_completa)
    x = range(num_tiradas + 1)
    max_individuales = min(10, len(resultados_completos))
    for i in range(max_individuales):
        etiqueta = f'Corrida individual' if i == 0 else ""
        plt.plot(x, resultados_completos[i], alpha=0.3, color='gray', label=etiqueta)
    promedios = [sum(tirada) / len(tirada) for tirada in zip(*resultados_completos)]
    plt.plot(x, promedios, color='red', linewidth=2.5, label='Promedio General', zorder=5)
    plt.axhline(y=capital_inicial, color='blue', linestyle='--', label='Capital inicial', zorder=4)
    plt.xlabel('n (número de tiradas)')
    plt.ylabel('Cantidad de Capital (cc)')
    plt.title('Flujo de capital simulado vs Promedio')
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())
    plt.show()

def analizar_flujo_todas_corridas(resultados, capital_inicial, num_tiradas):
    plt.figure()
    resultados_completos = []
    for corrida in resultados:
        corrida_completa = [capital_inicial] + corrida
        if len(corrida_completa) < num_tiradas + 1:
            ultimo_valor = corrida_completa[-1]
            faltantes = (num_tiradas + 1) - len(corrida_completa)
            corrida_completa.extend([ultimo_valor] * faltantes)
        resultados_completos.append(corrida_completa)
    x = range(num_tiradas + 1)
    for i, corrida_completa in enumerate(resultados_completos):
        plt.plot(x, corrida_completa, alpha=0.7)
    plt.axhline(y=capital_inicial, color='black', linestyle='--', linewidth=2, label='Capital inicial')
    plt.xlabel('n (número de tiradas)')
    plt.ylabel('Cantidad de Capital (cc)')
    plt.title('Flujo de capital - Todas las corridas individuales')
    plt.legend()
    plt.show()

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
    capital = 100
    capital_infinito = a == 'i'
    print(f"Iniciando {c} corridas de {n} tiradas cada una. Analizando la estrategia: {s} con capital: {a}")
    if s == 'm':
        resultados = estrategia_martingala(c, n, capital, capital_infinito)
    elif s == 'd':
        resultados = estrategia_dalembert(c, n, capital, capital_infinito)
    elif s == 'f':
        resultados = estrategia_fibonacci(c, n, capital, capital_infinito)
    elif s == 'o':
        resultados = estrategia_jacobo(c, n, capital, capital_infinito)
    else:
        print("Estrategia no reconocida. Por favor, elija entre 'm', 'd', 'f' o 'o'.")
        return
    analizar_frec_rel_tiradas_favorables(resultados, capital)
    analizar_flujo_capital(resultados, capital, n)
    analizar_flujo_todas_corridas(resultados, capital, n)

if __name__ == '__main__':
    main()