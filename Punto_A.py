# Importar Datos de Drones

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gurobipy as gp
import networkx as nx
import tabulate as tb

def get_time(cycle):
    time = 0
    for i in range(len(cycle)):
        if i <= len(cycle)-2:
            if cycle[i] == 0:
                time += ((q[cycle[i],cycle[i+1]] / 1000)) / 60
            else:
                time += ((q[cycle[i],cycle[i+1]] / 1000) + 90) / 60
        else:
            time += ((q[cycle[i],cycle[0]] / 1000) + 90) / 60
    return time

def get_photos(cycle):
    photos = 0
    for i in range(len(cycle)):
        photos += Fotos[cycle[i]]
    return photos

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
q = {(i,j): float(abs(df['Calle'][i]-df['Calle'][j]) + abs(df['Carrera'][i]-df['Carrera'][j]))*100 for i,j in A}

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
for i in Lugares:
    if i != 0:
        m.addConstr(gp.quicksum(x[i,j] for j in Lugares if i != j) == 1)

for j in Lugares:
    if j != 0:
        m.addConstr(gp.quicksum(x[i,j] for i in Lugares if i != j) == 1)

#	Se deben utilizar todos los Drones disponibles.
m.addConstr(gp.quicksum(x[0,j] for j in Lugares if j != 0) == 5)
m.addConstr(gp.quicksum(x[i,0] for i in Lugares if i != 0) == 5)

#	No deben existir ciclos entre un par de ubicaciones nisiquiera por drones diferentes.
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
fotos = []
tiempo = []
for cycle in cycles:
    fotos.append(get_photos(cycle))
    tiempo.append(get_time(cycle))

headers = ['Secuencia', 'Fotos', 'Tiempo']
data = list(zip(cycles, fotos, tiempo))
print(tb.tabulate(data, headers=headers, tablefmt='grid'))


