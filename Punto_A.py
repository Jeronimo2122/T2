# Importar Datos de Drones

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gurobipy as gp
import networkx as nx
import tabulate as tb

# Importar Datos xlsx (Primera fila nombres de columnas)
data = pd.read_excel('Tarea 2-202420.xlsx', header=1)

# Crear DataFrame
df = pd.DataFrame(data)

# Mostrar DataFrame
print(df.head())

# Conjunto 
Drones = [0,1,2,3,4]
Lugares = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]
Fotos = df['Fotos a tomar'].tolist()

# Lista de arcos entre lugares
A = [(i,j) for i in Lugares for j in Lugares if i != j]

# Diccionario de distancia entre lugares (Llave tupla de lugares)
q = {(i,j): float(abs(df['Calle'][i]-df['Calle'][j]) + abs(df['Carrera'][i]-df['Carrera'][j])) for i,j in A}

# Crear Modleo de Optimización
m = gp.Model('Drones')

#Variables de decisión
#x_dij:  {█(■(1&Si el drone d∈D debe ir del lugar i∈L hacia el lujar j∈L.),@0&En otro caso.).
x = m.addVars(Lugares, Lugares, vtype=gp.GRB.BINARY, name='x')

#Función Objetivo
#Minimizar: ∑_((i,j)∈A)▒∑_(d∈D)▒〖X_dij d_ij 〗  
m.setObjective(gp.quicksum(q[i,j]*x[i,j] for i,j in A if i != j), sense=gp.GRB.MINIMIZE)



#Restricciones
#	Todo cultivo debe ser visitado por un dron.
#∑_(d∈D)▒∑_({j:(j,i)∈A})▒x_dij =1 ; ∀ i∈L 
for i in Lugares:
    if i != 0:
        m.addConstr(gp.quicksum(x[i,j] for j in Lugares if i != j) == 1)

for j in Lugares:
    if j != 0:
        m.addConstr(gp.quicksum(x[i,j] for i in Lugares if i != j) == 1)

#	Se deben utilizar todos los Drones disponibles.
#∑_((i,j)∈A)▒x_dij ≥1 ; ∀ d∈D 
m.addConstr(gp.quicksum(x[0,j] for j in Lugares if j != 0) == 5)
m.addConstr(gp.quicksum(x[i,0] for i in Lugares if i != 0) == 5)

#	No deben existir ciclos entre un par de ubicaciones nisiquiera por drones diferentes.
#∑_({d:(d,i,j)∈D})▒x_dij ≤1 ; ∀ (i,j)∈A
for i in Lugares:
    for j in Lugares:
        if i != j:
            m.addConstr(x[i,j] + x[j,i] <= 1)


#Resolver
#Optimizar
m.optimize()
print('Estatus: ', m.Status)
print('Función Objetivo: ', m.objVal)

#Imprimir grafo de solución
G = nx.DiGraph()
G.add_nodes_from(Lugares)
for i,j in A:
    for d in Drones:
        if x[i,j].x > 0.1:
            G.add_edge(i,j)

nx.draw(G, with_labels=True)
plt.show()

G = nx.DiGraph()

for i,j in A:
    for d in Drones:
        if x[i,j].x > 0.1:
            G.add_edge(i,j)

cycles = list(nx.simple_cycles(G))

# Necestio sacar las fotos tomadas en cada cyclo y la distancia recorrida en cada ciclo y dame las fotos en una lista y la idstancias tambien
fotos = []
distancias = []
for cycle in cycles:
    fotos_cycle = 0
    distancias_cycle = 0
    for i in range(len(cycle)-1):
        distancias_cycle += q[cycle[i],cycle[i+1]]
        fotos_cycle += Fotos[cycle[i]]
        if i == len(cycle)-2:
            fotos_cycle += Fotos[cycle[i+1]]
    fotos.append(fotos_cycle)
    distancias.append(distancias_cycle)

headers = ['Secuencia', 'Fotos', 'Distancia']
data = list(zip(cycles, fotos, distancias))
print(tb.tabulate(data, headers=headers, tablefmt='grid'))

print(q[(24,20)])

