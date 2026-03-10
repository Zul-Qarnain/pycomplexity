"""
Graph traversal examples — DFS, BFS, Dijkstra
Run: bigopy analyze examples/graph_examples.py --verbose
"""
import heapq
from collections import deque


def dfs(graph, node, visited=None):
    """Depth First Search — O(V+E)"""
    if visited is None:
        visited = set()
    visited.add(node)
    print(node, end=" ")
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)


def bfs(graph, start):
    """Breadth First Search — O(V+E)"""
    visited = set()
    queue = deque([start])
    visited.add(start)
    while queue:
        node = queue.popleft()
        print(node, end=" ")
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)


def dijkstra(graph, source):
    """Dijkstra shortest path — O((V+E) log V)"""
    distance = {node: float('inf') for node in graph}
    distance[source] = 0
    pq = [(0, source)]
    visited = set()
    while pq:
        curr_dist, node = heapq.heappop(pq)
        if node in visited:
            continue
        visited.add(node)
        for neighbor, weight in graph[node]:
            new_dist = curr_dist + weight
            if new_dist < distance[neighbor]:
                distance[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))
    return distance
