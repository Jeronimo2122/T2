import pandas as pd
import numpy as np
import gurobipy as gp
from gurobipy import GRB
import networkx as nx

# Importar Datos xlsx (Primera fila nombres de columnas)
data = pd.read_excel('Tarea 2-202420.xlsx', header=1)

# Crear DataFrame
df = pd.DataFrame(data)

# Características de los drones
autonomia = 12  # Horas
velocidad = 1000  # metros/min
distancia_maxima = autonomia * 60 * velocidad
capacidad_fotos = 300  # fotos

# Conjuntos
Lugares = list(range(26))  # 25 cultivos más el hangar
Drones = [1, 2, 3, 4, 5]  # Conjunto de drones
A = [(i, j) for i in Lugares for j in Lugares if i != j]  # Lista de arcos entre lugares

# Parámetros
# Distancias entre los lugares (distancia Manhattan)
q = {(i, j): np.abs(df["Calle"][i] - df["Calle"][j]) + np.abs(df["Carrera"][i] - df["Carrera"][j]) for i, j in A}
# Filtro de lugares que no cumplen con la distancia máxima permitida
A = [(i, j) for i, j in A if q[i, j] <= distancia_maxima]

# Crear el modelo
m = gp.Model('Opti-Drones')

# Variables de decisión
x = m.addVars(Drones, A, vtype=GRB.BINARY, name='x')
u = m.addVars(Drones, Lugares, vtype=GRB.CONTINUOUS, name='u')

# Función objetivo: Minimizar la distancia total recorrida
m.setObjective(gp.quicksum(q[i, j] * x[d, i, j] for d in Drones for i, j in A), GRB.MINIMIZE)

# Restricciones
for i in Lugares:
    if i != 0:  # El hangar no cuenta
        m.addConstr(gp.quicksum(x[d, j, i] for d in Drones for j in Lugares if (j, i) in A) == 1)  # Llegada
        m.addConstr(gp.quicksum(x[d, i, j] for d in Drones for j in Lugares if (i, j) in A) == 1)  # Salida

for d in Drones:
    m.addConstr(gp.quicksum(x[d, 0, j] for j in Lugares if (0, j) in A) == 1)  # Salida del hangar
    m.addConstr(gp.quicksum(x[d, i, 0] for i in Lugares if (i, 0) in A) == 1)  # Regreso al hangar
    for i in Lugares:
        if i != 0:
            m.addConstr(gp.quicksum(x[d, i, j] for j in Lugares if (i, j) in A) == 
                        gp.quicksum(x[d, j, i] for j in Lugares if (j, i) in A))  # Balance

# Prohibir subtours de tamaño 2
for d in Drones:
    for i in Lugares:
        for j in Lugares:
            if i != j:
                m.addConstr(x[d, i, j] + x[d, j, i] <= 1)

# Restricciones MTZ
for d in Drones:
    for i in Lugares:
        for j in Lugares:
            if i != j and i != 0 and j != 0:
                m.addConstr(u[d, i] - u[d, j] + len(Lugares) * x[d, i, j] <= len(Lugares) - 1)

# Optimizar el modelo inicial
m.setParam('outputflag', 0)  # Deshabilitar la salida en pantalla
m.optimize()

def agregar_restricciones_conjunto_nodos(m, df, capacidad_fotos, ciclos_excedidos, tamanos_excedidos):
    """
    Esta función agrega restricciones de conjunto de nodos para eliminar todas las posibles rutas entre nodos
    que exceden la capacidad de fotos en un ciclo, y reduce la longitud de las rutas basándose en el tamaño 
    del ciclo excedido.
    """
    G = nx.DiGraph()
    for d in Drones:
        for i, j in A:
            if x[d, i, j].x > 0.5:
                G.add_edge(i, j)

    # Identificar los ciclos en el grafo
    cycles = list(nx.simple_cycles(G))

    # Revisar cada ciclo
    for cycle in cycles:
        fotos_totales = sum(df["Fotos a tomar"][nodo] for nodo in cycle)
        if fotos_totales > capacidad_fotos:
            print(f"Agregada restricción para el ciclo {cycle} con {fotos_totales} fotos.")
            ciclo_len = len(cycle)
            subconjunto_nodos = set(cycle)

            # Si es la primera vez que encontramos un ciclo de este tamaño, lo agregamos
            if ciclo_len not in ciclos_excedidos:
                ciclos_excedidos[ciclo_len] = 1  # Iniciar contador
                tamanos_excedidos.append(ciclo_len)
            else:
                ciclos_excedidos[ciclo_len] += 1  # Incrementar

            # Bloquear todas las rutas posibles entre esos nodos
            m.addConstr(gp.quicksum(x[d, i, j] for d in Drones for i in subconjunto_nodos for j in subconjunto_nodos if (i, j) in A) <= len(subconjunto_nodos) - 1)
            print(f"Restringiendo que los nodos {subconjunto_nodos} puedan conectarse entre ellos por cualquier ruta.")

    # Reducir el tamaño de las rutas en 1 unidad si encontramos un ciclo de ese tamaño en iteraciones anteriores
    if tamanos_excedidos:
        ciclo_mas_largo = max(tamanos_excedidos)
        print(f"Reduciendo el tamaño máximo permitido para las rutas a {ciclo_mas_largo - 1}.")
        for d in Drones:
            m.addConstr(gp.quicksum(x[d, i, j] for i in Lugares for j in Lugares if (i, j) in A) <= ciclo_mas_largo - 1)

    m.setParam('outputflag', 0)  # Deshabilitar la salida en pantalla
    print("FO antes de reoptimizar:", m.objVal)
    m.optimize()

# Inicializar el diccionario para guardar los tamaños de los ciclos excedidos
ciclos_excedidos = {}
tamanos_excedidos = []

# Proceso iterativo para agregar restricciones
while True:
    agregar_restricciones_conjunto_nodos(m, df, capacidad_fotos, ciclos_excedidos, tamanos_excedidos)
    
    # Verificar si aún quedan ciclos que exceden la capacidad de fotos
    G = nx.DiGraph()
    for d in Drones:
        for i, j in A:
            if x[d, i, j].x > 0.5:
                G.add_edge(i, j)

    cycles = list(nx.simple_cycles(G))
    
    # Terminar si no hay más ciclos que exceden la capacidad de fotos
    if not any(sum(df["Fotos a tomar"][nodo] for nodo in cycle) > capacidad_fotos for cycle in cycles):
        break

# Imprimir la función objetivo final
print(f"Función objetivo final: {m.objVal}")
