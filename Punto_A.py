# Importar Datos de Drones

import pandas as pd
import matplotlib.pyplot as plt
import gurobipy as gp
import networkx as nx
import tabulate as tb

# Importar Datos xlsx (Primera fila nombres de columnas)
data = pd.read_excel('Tarea 2-202420.xlsx', header=1)

# Crear DataFrame
df = pd.DataFrame(data)

fotos = list(df['Fotos a tomar'])

# Mostrar DataFrame
print(df.head())

# Conjunto 
Drones = [1,2,3,4,5]
Lugares = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,21,22,23,24,25]

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
m.setObjective(gp.quicksum(q[i,j]*x[i,j] for i,j in A), sense=gp.GRB.MINIMIZE)



#Restricciones
#	Todo cultivo debe ser visitado por un dron.
#∑_(d∈D)▒∑_({j:(j,i)∈A})▒x_dij =1 ; ∀ i∈L 
for i in Lugares:
    if i != 0:
        m.addConstr(gp.quicksum(x[i,j] for j in Lugares) == 1)
        m.addConstr(gp.quicksum(x[j,i] for j in Lugares) == 1)

#	Se deben utilizar todos los Drones disponibles.
#∑_((i,j)∈A)▒x_dij ≥1 ; ∀ d∈D 
m.addConstr(gp.quicksum(x[0,j] for j in Lugares) == 5)
m.addConstr(gp.quicksum(x[i,0] for i in Lugares) == 5)

#	No deben existir ciclos entre un par de ubicaciones nisiquiera por drones diferentes.
#∑_({d:(d,i,j)∈D})▒x_dij ≤1 ; ∀ (i,j)∈A
for i in Lugares:
    for j in Lugares:
        m.addConstr(x[i,j] + x[j,i] <= 1)


#Resolver
#Optimizar
m.optimize()
print('Estatus: ', m.Status)
print('Función Objetivo: ', m.objVal)

Gp = nx.DiGraph()
for i,j in A:
    if x[i,j].x > 0.1:
        Gp.add_edge(i,j)
cycles = list(nx.simple_cycles(Gp.to_directed()))

f = []
for i in list(range(len(cycles))):
    p = 0
    for j in list(range(len(cycles[i]))):
        p = p + fotos[cycles[i][j]]
    f.append(p)

# necesito sacar las distancias de cada ciclo con las distancias de q
distancias = []
for i in list(range(len(cycles))):
    l = 0
    for j in list(range(len(cycles[i])-1)):
        l = l + (q[cycles[i][j], cycles[i][j+1]] / 1000)
    distancias.append(l)

data = list(zip(cycles, distancias, f))

headers = ['Ciclos', 'Tiempo', 'Fotos']

table = tb.tabulate(data, headers= headers, tablefmt='fancy_grid')

print(table)

'''#Imprimir grafo de solución
G = nx.DiGraph()
G.add_nodes_from(Lugares)
for i,j in A:
    for d in Drones:
        if x[i,j].x > 0.1:
            G.add_edge(i,j)

nx.draw(G, with_labels=True)
plt.show()'''

