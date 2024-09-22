# Importar Datos de Drones

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gurobipy as gp
import networkx as nx
import tabulate as tb
import math
import time

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

def get_active_arcs():
    return [(i,j) for i,j in A if x[i,j].x > 0.1]
    

# MAIN
# Importar Datos xlsx (Primera fila nombres de columnas)
start_time = time.time()
data = pd.read_excel('Tarea 2-202420.xlsx', header=1)

# Crear DataFrame
df = pd.DataFrame(data)

# Conjunto 
Drones = [0,1,2,3,4]
Lugares = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]
Fotos = df['Fotos a tomar'].tolist()
maxFotos = 400
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

# Genera el grafo de la solucion inicial
G = createGraph(Lugares, get_active_arcs())

# Saca todos los ciclos del grafo
c = list(nx.simple_cycles(G))

# Saca los ciclos que no contienen el nodo 0
cycles = [cycle for cycle in c if 0 not in cycle]

# Verifica si hay ciclos que no contienen el nodo 0
hayCiclos = bool(cycles)

# Obtiene el primer ciclo que excede el maximo de fotos, si no hay ninguno retorna None
excedeFotos = next((i for i in c if get_fotos(i) > maxFotos), None)

# Obtiene el primer ciclo que excede el maximo de tiempo, si no hay ninguno retorna None
excedeTiempo = next((i for i in c if get_time(i) > maxTime), None)

# Ciclo principal iterativo que se ejecuta mientras haya ciclos que no contengan el 0 o algun ciclo exceda el maximo de fotos o tiempo
while hayCiclos or excedeFotos != None or excedeTiempo != None:
    # Condicional que verifica si hay ciclos que no contienen el 0
    if hayCiclos:
        for cycle in cycles:
            fotos = get_fotos(cycle)/maxFotos
            tiempo = get_time(cycle)/maxTime
            # Condicional que decide si romper el ciclo por fotos o tiempo
            if fotos > maxFotos:
                m.addConstr(gp.quicksum(x[i,j] for i in cycle for j in Lugares if i != 0 and j not in cycle) >= math.ceil(fotos))
                m.addConstr(gp.quicksum(x[j,i] for i in cycle for j in Lugares if i != 0 and j not in cycle) >= math.ceil(fotos))
            else:
                m.addConstr(gp.quicksum(x[i,j] for i in cycle for j in Lugares if i != 0 and j not in cycle) >= math.ceil(tiempo))
                m.addConstr(gp.quicksum(x[j,i] for i in cycle for j in Lugares if i != 0 and j not in cycle) >= math.ceil(tiempo))
    # Si no hay ciclos que no contienen el 0 entonces si se verifica los ciclos que excedan el maximo de fotos o tiempo
    else: 
        if excedeFotos == None:
            proporcionFotos = 0
        else:
            proporcionFotos = get_fotos(excedeFotos)/maxFotos
        
        if excedeTiempo == None:
            proporcionTiempo = 0
        else:
            proporcionTiempo = get_time(excedeTiempo)/maxTime

        # Condicional que decide si romper el ciclo por fotos o tiempo
        if proporcionFotos > proporcionTiempo: 
            m.addConstr(gp.quicksum(x[i,j] for i in excedeFotos for j in Lugares if i != 0 and j not in excedeFotos) >= math.ceil(proporcionFotos))
            m.addConstr(gp.quicksum(x[j,i] for i in excedeFotos for j in Lugares if i != 0 and j not in excedeFotos) >= math.ceil(proporcionFotos))
        
        else:
            m.addConstr(gp.quicksum(x[i,j] for i in excedeTiempo for j in Lugares if i != 0 and j not in excedeTiempo) >= math.ceil(proporcionTiempo))
            m.addConstr(gp.quicksum(x[j,i] for i in excedeTiempo for j in Lugares if i != 0 and j not in excedeTiempo) >= math.ceil(proporcionTiempo))

    #Se optimiza el nuevo modelo con las restricciones agregadas
    m.optimize()

    print('Función Objetivo: ', m.objVal)

    # Se recalculan los inputs del ciclo principal para ver si se cumplen todas las restricciones o se vuelve a iterar
    G = createGraph(Lugares, get_active_arcs())
    c = list(nx.simple_cycles(G))
    cycles = [cycle for cycle in c if 0 not in cycle]
    hayCiclos = bool(cycles)
    excedeFotos = next((i for i in c if get_fotos(i) > maxFotos), None)
    excedeTiempo = next((i for i in c if get_time(i) > maxTime), None)

print('Estatus: ', m.Status)
print('Función Objetivo: ', m.objVal)
end_time = time.time()
print('Tiempo de ejecución: ', end_time - start_time)

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

