# Importar Datos de Drones

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gurobipy as gp
import networkx as nx

# Importar Datos xlsx (Primera fila nombres de columnas)
data = pd.read_excel('Tarea 2-202420.xlsx', header=1)

# Crear DataFrame
df = pd.DataFrame(data)

# Mostrar DataFrame
print(df.head())

# Conjunto 
Drones = [0,1,2,3,4]
Lugares = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,21,22,23,24,25]

# Lista de arcos entre lugares
A = [(i,j) for i in Lugares for j in Lugares if i != j]

# Diccionario de distancia entre lugares (Llave tupla de lugares)
q = {(i,j): float(abs(df['Calle'][i]-df['Calle'][j]) + abs(df['Carrera'][i]-df['Carrera'][j])) for i,j in A}

print(A)

# Crear Modleo de Optimización

m = gp.Model('Drones')

#Variables de decisión
#x_dij:  {█(■(1&Si el drone d∈D debe ir del lugar i∈L hacia el lujar j∈L.),@0&En otro caso.).
x = m.addVars(Drones, Lugares, Lugares, vtype=gp.GRB.BINARY, name='x')

#Función Objetivo
#Minimizar: ∑_((i,j)∈A)▒∑_(d∈D)▒〖X_dij d_ij 〗  
m.setObjective(gp.quicksum(q[i,j]*x[d,i,j] for i,j in A for d in Drones), sense=gp.GRB.MINIMIZE)

#Restricciones
#	Todo cultivo debe ser visitado por un dron.
#∑_(d∈D)▒∑_({j:(j,i)∈A})▒x_dij =1 ; ∀ i∈L 
for i in Lugares:
    if i != 0:
        m.addConstr(gp.quicksum(x[d,j,i] for d in Drones for j in Lugares if (j,i) in A) == 1)
        m.addConstr(gp.quicksum(x[d,j,i] for d in Drones for j in Lugares if (i,j) in A) == 1)

'''
#∑_(d∈D)▒∑_({j:(i,j)∈A})▒x_dij =1 ; ∀ i∈L 
for i in Lugares:
    if i != 0:
        m.addConstr(gp.quicksum(x[d,i,j] for d in Drones for j in Lugares if (i,j) in A) == 1)
'''

#	Se deben utilizar todos los Drones disponibles.
#∑_((i,j)∈A)▒x_dij ≥1 ; ∀ d∈D 
for d in Drones:
    m.addConstr(gp.quicksum(x[d,i,j] for i,j in A) >= 1)

#	No deben existir ciclos entre un par de ubicaciones nisiquiera por drones diferentes.
#∑_({d:(d,i,j)∈D})▒x_dij ≤1 ; ∀ (i,j)∈A
for i,j in A:
    m.addConstr(gp.quicksum(x[d,i,j] for d in Drones) <= 1)

# Todos los drones deben salir del lugar 0
#∑_({j:(0,j)∈A})▒x_d0j =1 ; ∀ d∈D
for d in Drones:
    m.addConstr(gp.quicksum(x[d,0,j] for j in Lugares if (0,j) in A) == 1)

# Todos los drones deben regresar al lugar 0
#∑_({i:(i,0)∈A})▒x_di0 =1 ; ∀ d∈D
for d in Drones:
    m.addConstr(gp.quicksum(x[d,i,0] for i in Lugares if (i,0) in A) == 1)

#Optimizar
m.optimize()
print('Estatus: ', m.Status)
print('Función Objetivo: ', m.objVal)

#Imprimir grafo de solución
G = nx.DiGraph()
G.add_nodes_from(Lugares)
for i,j in A:
    for d in Drones:
        if x[d,i,j].x > 0.1:
            G.add_edge(i,j)

nx.draw(G, with_labels=True)
plt.show()

#Imprimir solución
for d in Drones:
    for i,j in A:
        if x[d,i,j].x > 0.1:
            print('Dron ', d, ' va de ', i, ' a ', j)











