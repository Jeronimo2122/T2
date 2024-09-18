# Restricción: La distancia total recorrida no debe superar la distancia máxima permitida por la autonomía
m.addConstr(gp.quicksum(q[i, j] * x[i, j] for i, j in A) <= distancia_maxima)