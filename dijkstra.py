import heapq

def dijkstra(graph, source):
    # distance[node] = shortest distance from source
    distance = {node: float('inf') for node in graph}
    distance[source] = 0

    # priority queue: (distance, node)
    pq = [(0, source)]
    visited = set()

    while pq:
        curr_dist, node = heapq.heappop(pq)   # extract_min → O(log V)

        if node in visited:
            continue
        visited.add(node)

        for neighbor, weight in graph[node]:   # for each edge → O(E) total
            new_dist = curr_dist + weight
            if new_dist < distance[neighbor]:
                distance[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))  # O(log V)

    return distance


# ── Test graph ──────────────────────────────────────────────
#        A
#      / | \
#    4/  |1  \2
#    /   |    \
#   B    C --- D
#    \  2|   3/
#    1\  |  /
#      \ | /
#        E
graph = {
    'A': [('B', 4), ('C', 1), ('D', 2)],
    'B': [('E', 1)],
    'C': [('E', 2), ('D', 3)],
    'D': [('E', 3)],
    'E': []
}

result = dijkstra(graph, 'A')
print("Shortest distances from A:")
for node, dist in sorted(result.items()):
    print(f"  A → {node} = {dist}")
