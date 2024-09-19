import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gurobipy as gp
from gurobipy import GRB
import networkx as nx

# Importar Datos xlsx (Primera fila nombres de columnas)
data = pd.read_excel('Tarea 2-202420.xlsx', header=1)

# Crear DataFrame
df = pd.DataFrame(data)

# Mostrar DataFrame
print(df.head())

# Conjuntos
Lugares = list(range(26))  # 25 cultivos más el hangar (L = {0,1,2,...,25}).
Drones = [1, 2, 3, 4, 5]  # Conjunto de drones.
A = [(i, j) for i in Lugares for j in Lugares if i != j] # Lista de arcos entre lugares (Con distancia máxima permitida).

# Parametros
# Distancias entre los lugares (distancia Manhattan)
q = {(i, j): np.abs(df["Calle"][i] - df["Calle"][j]) + np.abs(df["Carrera"][i] - df["Carrera"][j]) for i, j in A}

# Crear el modelo
m = gp.Model('Opti-Drones')



# Variables de decisión
# x[d, i, j] = 1 si el dron d viaja de lugar i a lugar j, 0 en caso contrario
x = m.addVars(Drones, A, vtype=GRB.BINARY, name='x')
# Variables auxiliares u para eliminación de subtours (Miller-Tucker-Zemlin)
u = m.addVars(Drones, Lugares, vtype=GRB.CONTINUOUS, name='u')



# Función objetivo: Minimizar la distancia total recorrida por todos los drones
m.setObjective(gp.quicksum(q[i, j] * x[d, i, j] for d in Drones for i, j in A), GRB.MINIMIZE)



# Restricciones
# Restricción 1: Todo cultivo debe ser visitado por exactamente un dron (llega a i)
for i in Lugares:
    if i != 0:  # El hangar no cuenta
        m.addConstr(gp.quicksum(x[d, j, i] for d in Drones for j in Lugares if (j, i) in A) == 1)

# Restricción 2: Todo cultivo debe ser visitado por exactamente un dron (sale de i)
for i in Lugares:
    if i != 0:  # El hangar no cuenta
        m.addConstr(gp.quicksum(x[d, i, j] for d in Drones for j in Lugares if (i, j) in A) == 1)


# Restricción 4: Balance en cada nodo (número de arcos que entran = número de arcos que salen para cada dron)
for d in Drones:
    for i in Lugares:
        if i != 0:
            m.addConstr(gp.quicksum(x[d, i, j] for j in Lugares if (i, j) in A) == 
                        gp.quicksum(x[d, j, i] for j in Lugares if (j, i) in A))
            

# Prohibir subtours de tamaño 2 para cada dron
for d in Drones:
    for i in Lugares:
        for j in Lugares:
            if i != j:
                m.addConstr(x[d, i, j] + x[d, j, i] <= 1)


# Optimizar el modelo
m.optimize()

# Imprimir resultados
if m.status == GRB.OPTIMAL:
    print(f"Solución óptima encontrada con un valor objetivo de: {m.objVal}")

    # Dibujar grafo de la solución
    G = nx.DiGraph()
    for d in Drones:
        for i, j in A:
            if x[d, i, j].x > 0.5:
                G.add_edge(i, j)

    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=700, node_color='skyblue')
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.show()

    # Imprimir la solución para cada dron
    
    for d in Drones:
        SumaFotos = 0
        SumaDistancia = 0
        print(f"Rutas del dron {d}:")
        for i, j in A:
            if x[d, i, j].x > 0.5:
                print(f"Dron {d} va de {i} a {j}")
                SumaFotos += df["Fotos a tomar"][j]
                SumaDistancia += q[i, j]
else:
    print("No se encontró una solución óptima.")
