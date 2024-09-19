# Importar Datos de Drones

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gurobipy as gp
import networkx as nx
import tabulate as tb

# Funciones auxiliares
# Fotos tomadas en un ciclo
def get_fotos(cycle):
    fotos_cycle = 0
    for i in range(len(cycle)):
        fotos_cycle += Fotos[cycle[i]]
    return fotos_cycle

# Distancia recorrida en un ciclo
def get_distancias(cycle):
    distancias_cycle = 0
    for i in range(len(cycle)-1):
        distancias_cycle += q[cycle[i],cycle[i+1]]
    return

# Crear grafo
def createGraph(Lugares, A):
    G = nx.DiGraph()
    G.add_nodes_from(Lugares)
    for i,j in A:
        G.add_edge(i,j)
    return G

# Desarmar ciclos
def cutOutCycles(cycles):
    for cycle in cycles:
        arcsInCycle = []
        for i in cycle:
            j = i + 1
            for j in cycle:
                if i != j:
                    arcsInCycle.append((i,j))
        m.addConstr(gp.quicksum(x[i,j] for i,j in arcsInCycle) <= len(cycle)-1)

def get_active_arcs(x):
    active_arcs = []
    for i,j in A:
        if x[i,j].x > 0.1:
            active_arcs.append((i,j))
    return active_arcs
    

# MAIN
# Importar Datos xlsx (Primera fila nombres de columnas)
data = pd.read_excel('Tarea 2-202420.xlsx', header=1)

# Crear DataFrame
df = pd.DataFrame(data)

# Conjunto 
Drones = [0,1,2,3,4]
Lugares = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]
Fotos = df['Fotos a tomar'].tolist()
maxFotos = 500

# Lista de arcos entre lugares
A = [(i,j) for i in Lugares for j in Lugares if i != j]

# Diccionario de distancia entre lugares (Llave tupla de lugares)
q = {(i,j): float(abs(df['Calle'][i]-df['Calle'][j]) + abs(df['Carrera'][i]-df['Carrera'][j])) for i,j in A}

# Crear Modleo de Optimización
m = gp.Model('Drones')
m.setParam('OutputFlag', 0)

#Variables de decisión
x = m.addVars(Lugares, Lugares, vtype=gp.GRB.BINARY, name='x')

#Función Objetivo
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

#	No deben existir ciclos entre un par de ubicaciones nisiquiera por drones diferentes
for i in Lugares:
    for j in Lugares:
        if i != j:
            m.addConstr(x[i,j] + x[j,i] <= 1)

#Optimizar
m.optimize()
G = createGraph(Lugares, get_active_arcs(x))

c = list(nx.simple_cycles(G))
cycles = [cycle for cycle in c if 0 not in cycle]
hayCiclos = True if len(cycles) > 0 else False

while hayCiclos:
    cutOutCycles(cycles)
    m.optimize()
    G = createGraph(Lugares, get_active_arcs(x))
    c = list(nx.simple_cycles(G))
    cycles = [cycle for cycle in c if 0 not in cycle]
    hayCiclos = True if len(cycles) > 0 else False

print('Estatus: ', m.Status)
print('Función Objetivo: ', m.objVal)


excedeFotos = -1
cycleFotos = 0
for i in range(len(c)):
    if get_fotos(c[i]) > maxFotos:
        excedeFotos = i
        cycleFotos = get_fotos(c[i])

while excedeFotos > -1:
    cutArcs = [(i, j) for i in c[excedeFotos] for j in Lugares if (i != j and j not in c[excedeFotos])]
    m.addConstr(gp.quicksum(x[i,j] * Fotos[i] for i,j in cutArcs) >= cycleFotos/maxFotos)
    m.optimize()
    print('Estatus: ', m.Status)
    print('Función Objetivo: ', m.objVal)
    G = createGraph(Lugares, get_active_arcs(x))
    c = list(nx.simple_cycles(G))
    excedeFotos = -1
    for i in range(len(c)):
        if get_fotos(c[i]) > maxFotos:
            excedeFotos = i
            cycleFotos = get_fotos(c[i])

    

print('Estatus: ', m.Status)
print('Función Objetivo: ', m.objVal)


#Imprimir grafo de solución
nx.draw(G, with_labels=True)
plt.show()


cyclesS = list(nx.simple_cycles(G))

# Necestio sacar las fotos tomadas en cada cyclo y la distancia recorrida en cada ciclo y dame las fotos en una lista y la idstancias tambien
fotos = []
distancias = []
for cycle in cyclesS:
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
data = list(zip(cyclesS, fotos, distancias))
print(tb.tabulate(data, headers=headers, tablefmt='grid'))

print(q[(24,20)])

