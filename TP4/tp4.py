import random
import matplotlib.pyplot as plt

def generador_uniforme(a, b, cantidad):
    #Genera numeros pseudoaleatorios con distribucion uniforme continua.
    #a: limite inferior del intervalo.
    #b: limite superior del intervalo.
    #cantidad: numero de iteraciones/valores a generar.
    
    valores_generados = []
    
    for _ in range(cantidad):
        # Generacion de r en el intervalo [0, 1)
        r = random.random() 
        
        # Aplicacion de la Ecuacion de Transformada Inversa
        x = a + (b - a) * r
        
        valores_generados.append(x)
        
    return valores_generados

    import matplotlib.pyplot as plt

###TESTEO EMPIRICO: GENERADOR UNIFORME CONTINUO
# Parametros de prueba
limite_inferior = 10
limite_superior = 20
tamano_muestra = 10000

# Ejecucion del generador
muestras = generador_uniforme(limite_inferior, limite_superior, tamano_muestra)

# Ploteo del histograma de densidad
plt.hist(muestras, bins=50, density=True, alpha=0.7, color='skyblue', edgecolor='black')

# Superposicion de la PDF Teorica
pdf_teorica = 1 / (limite_superior - limite_inferior)
plt.axhline(y=pdf_teorica, color='red', linestyle='dashed',
linewidth=2, label='PDF Teorica')

plt.title('Testeo Empirico: Generador Uniforme')
plt.xlabel('Valor Generado (x)')
plt.ylabel('Frecuencia / Densidad')
plt.legend()
plt.savefig('histograma_uniforme.png')
plt.show()
