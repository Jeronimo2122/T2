# Importar Datos de Drones

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gurobipy as gp
import networkx as nx
import tabulate as tb
import math

# Funciones auxiliares
# Fotos tomadas en un ciclo
def get_fotos(cycle):
    return sum([Fotos[i] for i in cycle])

# Distancia recorrida en un ciclo
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

# Crear grafo
def createGraph(Lugares, A):
    G = nx.DiGraph()
    G.add_nodes_from(Lugares)
    G.add_edges_from(A)
    return G

# Desarmar ciclos
def cutOutCycles(cycles, Lugares):
    for cycle in cycles:
        m.addConstr(gp.quicksum(x[i,j] for i in cycle for j in Lugares if i != 0 and j not in cycle) >= 1)
        m.addConstr(gp.quicksum(x[i,j] for j in cycle for i in Lugares if j != 0 and i not in cycle) >= 1)

def get_active_arcs():
    return [(i,j) for i,j in A if x[i,j].x > 0.1]
    

# MAIN
# Importar Datos xlsx (Primera fila nombres de columnas)
data = pd.read_excel('Tarea 2-202420.xlsx', header=1)

# Crear DataFrame
df = pd.DataFrame(data)

# Conjunto 
Drones = [0,1,2,3,4]
Lugares = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]
Fotos = df['Fotos a tomar'].tolist()
maxFotos = 700
maxTime = 12

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


G = createGraph(Lugares, get_active_arcs())
c = list(nx.simple_cycles(G))
cycles = [cycle for cycle in c if 0 not in cycle]
hayCiclos = bool(cycles)

excedeFotos = next((i for i in range(len(c)) if get_fotos(c[i]) > maxFotos), -1)
print(excedeFotos)

excedeTiempo = next((i for i, cycle in enumerate(c) if get_time(cycle) > maxTime), -1)
print(excedeTiempo)

while hayCiclos or excedeFotos > -1 or excedeTiempo > -1:
    if hayCiclos:
        cutOutCycles(cycles, Lugares)
    else: 
        if excedeFotos == -1:
            proporcionFotos = 0
        else:
            proporcionFotos = get_fotos(c[excedeFotos])/maxFotos
        
        if excedeTiempo == -1:
            proporcionTiempo = 0
        else:
            proporcionTiempo = get_time(c[excedeTiempo])/maxTime

        if proporcionFotos < proporcionTiempo: 
            cutArcs = [(i, j) for i in c[excedeFotos] for j in Lugares if (i != j and j not in c[excedeFotos])]
            m.addConstr(gp.quicksum(x[i,j] * Fotos[i] for i,j in cutArcs) >= math.ceil(get_fotos(c[excedeFotos])/maxFotos))
            m.addConstr(gp.quicksum(x[j,i] * Fotos[i] for i,j in cutArcs) >= math.ceil(get_fotos(c[excedeFotos])/maxFotos))
        
        else:
            cutArcs = [(i, j) for i in c[excedeTiempo] for j in Lugares if (i != j and j not in c[excedeTiempo])]
            m.addConstr(gp.quicksum(x[i,j] * q[i,j] for i,j in cutArcs) >= math.ceil(get_time(c[excedeTiempo])/maxTime))
            m.addConstr(gp.quicksum(x[j,i] * q[i,j] for i,j in cutArcs) >= math.ceil(get_time(c[excedeTiempo])/maxTime))

    m.optimize()

    print('Función Objetivo: ', m.objVal)
    G = createGraph(Lugares, get_active_arcs())
    c = list(nx.simple_cycles(G))
    nx.draw(G, with_labels=True)
    plt.show()
    cycles = [cycle for cycle in c if 0 not in cycle]
    hayCiclos = True if len(cycles) > 0 else False
    hayCiclos = bool(cycles)
    excedeFotos = next((i for i, cycle in enumerate(c) if get_fotos(cycle) > maxFotos), -1)
    excedeTiempo = next((i for i, cycle in enumerate(c) if get_time(cycle) > maxTime), -1)

print('Estatus: ', m.Status)
print('Función Objetivo: ', m.objVal)


#Imprimir grafo de solución
nx.draw(G, with_labels=True)
plt.show()


cyclesS = list(nx.simple_cycles(G))

# Necestio sacar las fotos tomadas en cada cyclo y la distancia recorrida en cada ciclo y dame las fotos en una lista y la idstancias tambien
fotos = []
tiempo = []
for cycle in cyclesS:
    fotos.append(get_fotos(cycle))
    tiempo.append(get_time(cycle))

headers = ['Secuencia', 'Fotos', 'Tiempo']
data = list(zip(cyclesS, fotos, tiempo))
print(tb.tabulate(data, headers=headers, tablefmt='grid'))

