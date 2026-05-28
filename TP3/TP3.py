#Generador 1 obligatorio: GCL (Generador Congruencial Lineal)

# Parámetros
a = 7**5          # 16807
c = 0
m = 2**31 - 1     # 2147483647
seed = 12345

def gcl(seed, n, a, c, m):
    seeds  = np.zeros(n, dtype=int)
    values = np.zeros(n, dtype=int)

    for i in range(n):
        x    = (a * seed + c) % m
        seed = x
        values[i] = x
        seeds[i]  = seed

    normalized = seeds / m              # normaliza a [0, 1)
    return np.column_stack((seeds, values, normalized))

result = gcl(seed, 10, a, c, m)
print(f"{'Seed':>12}  {'x':>12}  {'Normalizado':>12}")
print("-" * 42)
for row in result:
    print(f"{int(row[0]):>12}  {int(row[1]):>12}  {row[2]:>12.4f}")

# Generador 2 (comparación): Cuadrados Medios
def mid_square(seed, n):
      seeds  = np.zeros(n, dtype=int)
      values = np.zeros(n, dtype=int)

      for i in range(n):
          x = seed ** 2
          seed = (x // 100) % 10000 if len(str(x)) > 2 else 0
          values[i] = x
          seeds[i]  = seed

      normalized = seeds / 10000          # normaliza a [0, 1)
      return np.column_stack((seeds, values, normalized))

result = mid_square(seed, 10)
print(f"{'Seed':>8}  {'x (seed²)':>12}  {'Normalizado':>12}")
print("-" * 38)
for row in result:
    print(f"{int(row[0]):>8}  {int(row[1]):>12}  {row[2]:>12.4f}")

# Generador 3 (comparación): Python random
import random
import numpy as np
from scipy import stats

random.seed(12345)
valores = [random.random() for _ in range(10)]
print(f"{'Valor':>12}  {'Normalizado':>12}")
# PUSE 10 PARA MOSTRAR LOS NUMEROS CON UN PRINT EN LAS PRUEBAS USAR 10000 o por ahi