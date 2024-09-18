G = nx.DiGraph()
for i, j in A:
    for d in drones:
        if x[d, i, j].x > 0.5:
            G.add_edge(i, j)

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_size=700, node_color='skyblue')
labels = nx.get_edge_attributes(G, 'weight')
nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
plt.show()