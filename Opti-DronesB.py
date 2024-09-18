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
Lugares = list(range(26))  # 25 cultivos más el hangar (L = {0,1,2,...,25})

# Lista de arcos entre lugares (Con distancia máxima permitida)
distancia_maxima = 100  # Ajustar este umbral según sea necesario
A = [(i, j) for i in Lugares for j in Lugares if i != j]

# Distancias entre los lugares (distancia Manhattan)
q = {(i, j): np.abs(df.iloc[i, 1] - df.iloc[j, 1]) + np.abs(df.iloc[i, 2] - df.iloc[j, 2]) for i, j in A}

# Filtrar arcos con base en la distancia máxima
A = [(i, j) for i, j in A if q[(i, j)] <= distancia_maxima]

# Crear el modelo
m = gp.Model('Opti-Drones')

# Variables de decisión: x[i, j] = 1 si hay un viaje de lugar i a lugar j, 0 en caso contrario
x = m.addVars(A, vtype=GRB.BINARY, name='x')

# Variables auxiliares u para eliminación de subtours (Miller-Tucker-Zemlin)
u = m.addVars(Lugares, vtype=GRB.CONTINUOUS, name='u')

# Función objetivo: Minimizar la distancia total recorrida
m.setObjective(gp.quicksum(q[i, j] * x[i, j] for i, j in A), GRB.MINIMIZE)

# Restricción 1: Todo cultivo debe ser visitado por un dron (llega a i)
for i in Lugares:
    if i != 0:  # El hangar no cuenta
        m.addConstr(gp.quicksum(x[j, i] for j in Lugares if (j, i) in A) == 1)

# Restricción 2: Todo cultivo debe ser visitado por un dron (sale de i)
for i in Lugares:
    if i != 0:  # El hangar no cuenta
        m.addConstr(gp.quicksum(x[i, j] for j in Lugares if (i, j) in A) == 1)

# Restricción 3: Se deben realizar exactamente 5 rutas (entrada y salida del hangar)
m.addConstr(gp.quicksum(x[0, j] for j in Lugares if (0, j) in A) == 5)  # Salida del hangar
m.addConstr(gp.quicksum(x[i, 0] for i in Lugares if (i, 0) in A) == 5)  # Regreso al hangar

# Restricción 4: Balance en cada nodo (número de arcos que entran = número de arcos que salen)
for i in Lugares:
    if i != 0:
        m.addConstr(gp.quicksum(x[i, j] for j in Lugares if (i, j) in A) == 
                    gp.quicksum(x[j, i] for j in Lugares if (j, i) in A))

# Activar el uso de restricciones lazy
m.setParam('LazyConstraints', 1)

# Callback para agregar restricciones de eliminación de subtours
def subtour_elim(model, where):
    if where == GRB.Callback.MIPSOL:
        # Obtener la solución en el punto actual
        sol = model.cbGetSolution(x)
        
        # Construir el grafo a partir de la solución
        G_sol = nx.DiGraph()
        for i, j in A:
            if sol[i, j] > 0.5:
                G_sol.add_edge(i, j)
        
        # Buscar los ciclos en la solución actual
        subtours = list(nx.simple_cycles(G_sol))
        
        # Si se encuentran ciclos (subtours), agregamos las restricciones de eliminación
        for subtour in subtours:
            if len(subtour) < len(Lugares):
                model.cbLazy(gp.quicksum(x[i, j] for i in subtour for j in subtour if (i, j) in A) <= len(subtour) - 1)

# Optimizar el modelo con callback para eliminación de subtours
m.optimize(subtour_elim)

# Imprimir resultados
if m.status == GRB.OPTIMAL:
    print(f"Solución óptima encontrada con un valor objetivo de: {m.objVal}")

# Dibujar grafo de la solución
G = nx.DiGraph()
for i, j in A:
    if x[i, j].x > 0.5:
        G.add_edge(i, j)

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_size=700, node_color='skyblue')
labels = nx.get_edge_attributes(G, 'weight')
nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
plt.show()

# Imprimir la solución
for i in Lugares:
    for j in Lugares:
        if x[i, j].x > 0.5:
            print(f"El dron viaja de {i} a {j}")
