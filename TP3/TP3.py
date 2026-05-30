import random
import math
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

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
print("\n=== Generador 1: GCL (Congruencial Lineal) ===")
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
print("\n=== Generador 2: Cuadrados Medios ===")
print(f"{'Seed':>8}  {'x (seed²)':>12}  {'Normalizado':>12}")
print("-" * 38)
for row in result:
    print(f"{int(row[0]):>8}  {int(row[1]):>12}  {row[2]:>12.4f}")

# Generador 3 (comparación): Python random
random.seed(12345)
valores = [random.random() for _ in range(10)]
print("\n=== Generador 3: Python random ===")
print(f"{'Normalizado':>12}")
print("-" * 12)
for v in valores:
    print(f"{v:>12.4f}")

# Generador 4: Numpy random
np.random.seed(12345)
valoresNP = [np.random.rand() for _ in range(10)]
print("\n=== Generador 4: NumPy random ===")
print(f"{'Normalizado':>12}")
print("-" * 12)
for v in valoresNP:
    print(f"{v:>12.4f}")

# =========================================================
# INTERFAZ UNIFICADA: devuelve un array de N valores en [0, 1)
# para cada generador, reseteando la semilla en cada llamada.
# =========================================================
def generar_valores(clave, n):
    if clave == "GCL (Congruencial Lineal)":
        return gcl(12345, n, a, c, m)[:, 2]
    if clave == "Cuadrados Medios":
        return mid_square(12345, n)[:, 2]
    if clave == "Python random":
        random.seed(12345)
        return np.array([random.random() for _ in range(n)])
    if clave == "NumPy random":
        np.random.seed(12345)
        return np.random.uniform(0, 1, n)
    raise ValueError(f"Generador desconocido: {clave}")


# =========================================================
# PRUEBAS DE ALEATORIEDAD (datos normalizados en [0, 1))
# =========================================================

# 1. Test de Chi-Cuadrado (Uniformidad)
def test_chi_cuadrado(data, num_bins=10):
    observed, _ = np.histogram(data, bins=num_bins, range=(0, 1))
    expected = len(data) / num_bins
    chi_square_stat = np.sum((observed - expected)**2 / expected)
    p_value = 1 - stats.chi2.cdf(chi_square_stat, num_bins - 1)  # gl = num_bins - 1
    return chi_square_stat, p_value

# 2. Test Monobit (Frecuencia)
def test_monobit(data):
    # 1 si el valor es > 0.5, -1 si es <= 0.5
    binary_data = [1 if x > 0.5 else -1 for x in data]
    sum_val = abs(sum(binary_data))
    # p-value con la función de error complementaria (erfc) del NIST
    p_value = math.erfc(sum_val / (math.sqrt(len(data)) * math.sqrt(2)))
    return sum_val, p_value

# 3. Test de Rachas (Runs Test, independencia respecto de la mediana)
def test_rachas(data):
    median = np.median(data)
    runs = 0
    n1 = 0  # cantidad por encima de la mediana
    n2 = 0  # cantidad por debajo o igual a la mediana

    if data[0] > median:
        n1 += 1
    else:
        n2 += 1

    for i in range(1, len(data)):
        if data[i] > median:
            n1 += 1
            if data[i-1] <= median:
                runs += 1
        else:
            n2 += 1
            if data[i-1] > median:
                runs += 1
    runs += 1  # cuenta la última racha

    # Si todos los valores caen del mismo lado de la mediana (p. ej. un
    # generador degenerado/constante), la varianza es 0 y el test no aplica.
    if n1 == 0 or n2 == 0:
        return float('nan'), 0.0

    expected_runs = ((2 * n1 * n2) / (n1 + n2)) + 1
    variance = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / (((n1 + n2)**2) * (n1 + n2 - 1))
    Z = (runs - expected_runs) / math.sqrt(variance)
    p_value = 2 * (1 - stats.norm.cdf(abs(Z)))
    return Z, p_value

# 4. Test de Bitmap (visual): cada valor -> 1 bit (>0.5 = blanco, <=0.5 = negro)
#    Se acomodan en una grilla cuadrada. Si es aleatorio se ve "ruido";
#    si hay patrones (rayas, bloques) el generador es malo.
def test_bitmap(data, lado):
    total = lado * lado
    bits = (np.asarray(data[:total]) > 0.5).astype(np.uint8)
    return bits.reshape(lado, lado)   # matriz 0/1 lista para imshow


def correr_pruebas(nombre, datos, alpha=0.01):
    # p-value > alpha => PASA el test.
    chi_stat, chi_p = test_chi_cuadrado(datos)
    mono_stat, mono_p = test_monobit(datos)
    runs_stat, runs_p = test_rachas(datos)

    print(f"\n=== {nombre} (n={len(datos)}, alpha={alpha}) ===")
    print(f"1. Chi-Cuadrado (Uniformidad):  Stat={chi_stat:.4f}, p-value={chi_p:.4f} -> {'PASA' if chi_p > alpha else 'FALLA'}")
    print(f"2. Monobit (Frecuencia):        Suma=|{mono_stat}|, p-value={mono_p:.4f} -> {'PASA' if mono_p > alpha else 'FALLA'}")
    print(f"3. Rachas (Independencia):      Z-score={runs_stat:.4f}, p-value={runs_p:.4f} -> {'PASA' if runs_p > alpha else 'FALLA'}")


# --- EJECUCIÓN: pruebas estadísticas + bitmap para cada generador ---
N = 10000        # muestra para los tests estadísticos
LADO = 200       # imagen LADO x LADO -> necesita LADO**2 valores
N_BITMAP = LADO * LADO

claves = ["GCL (Congruencial Lineal)", "Cuadrados Medios", "Python random", "NumPy random"]

fig, axes = plt.subplots(2, 2, figsize=(8, 8))
fig.suptitle("Test de Bitmap de los generadores", fontsize=14)

for ax, clave in zip(axes.ravel(), claves):
    correr_pruebas(clave, generar_valores(clave, N))

    imagen = test_bitmap(generar_valores(clave, N_BITMAP), LADO)
    ax.imshow(imagen, cmap="gray", interpolation="nearest")
    ax.set_title(clave, fontsize=9)
    ax.axis("off")

plt.tight_layout()
plt.savefig("bitmaps_comparacion.png", dpi=120)
print("\nImagen guardada: bitmaps_comparacion.png")
plt.show()