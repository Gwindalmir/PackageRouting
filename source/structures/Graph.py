import sys

from utilities.Logger import Logger
sys.path.append("..")


class Graph:
    """Represents an undirected graph of vertices connected by edges"""

    # This graph is represented internally by a square N x N adjacency matrix.
    # The adjacency matrix is the best choice for this situation,
    # as every vertex connects to every other vertex, so it's edge heavy.
    # The storage size is O(N^2) [actually O(N^2 + N), but simplifies to O(N^2)].

    def __init__(self, size):
        """Create a graph with the adjacency matrix of size N x N"""
        super().__init__()

        # Initialize matrix to the requested size, square matrix.
        # Default all weights to 0, meaning unreachable.
        self.size = size
        self.matrix = [[0 for i in range(size)] for j in range(size)]
        self.vertices = [None for i in range(size)]
        self.vertex_count = 0

    def add_vertex(self, vertex: str):
        """Adds a named vertex for indexing into the matrix"""
        Logger.log(Logger.LogLevel.VERBOSE,
                   f"Adding vertex {self.vertex_count}: {vertex}")
        self.vertices[self.vertex_count] = vertex
        self.vertex_count += 1

    def __lookup_vertex_index(self, vertex):
        """Gets the vertex index, given the name. Supports passing through the index."""
        try:
            # If vertex is an integer, just return it, this is O(1)
            return int(vertex)
        except (TypeError, ValueError):
            # If the vertex is a string instead, look up from the vertices array
            # This is O(N)
            for i in range(len(self.vertices)):
                if self.vertices[i] == vertex:
                    return i
            return -1

    def __lookup_vertex_name(self, vertex: int):
        """Gets the vertex name, given the index."""
        if vertex < 0:
            return None

        return self.vertices[vertex]

    def add_edge(self, u, v, weight=1.0, directed: bool = False):
        """Adds an edge connecting vertex u and v, with optional weight.

        If using strings for vertices, call add_vertex first.

        u = row
        v = column
        Default is undirected edge."""
        # if u and v are strings, look up their index
        u = self.__lookup_vertex_index(u)
        v = self.__lookup_vertex_index(v)

        # Add the edge to the ajacency matrix. Default is 1.0, meaning connected.
        # If weight is > 1, then it's a weighted edge.
        # This operation is O(1)
        self.matrix[u][v] = float(weight)

        Logger.log(Logger.LogLevel.DEBUG, f"Adding edge: {u}->{v} = {weight}")

        # If the edge being added is undirected, then add the mirror image (AB <-> BA).
        if not directed:
            self.add_edge(
                v, u, weight, True
            )  # pass True for directed to avoid more than one recursive call

    def is_connected(self, u, v):
        """Checks if the specified vertices are connected in the specified order (u -> v)."""
        return self.get_weight(u, v) > 0

    def get_weight(self, u, v):
        """Gets the weight of the specified edge.

        returns: weight if connected, 0 if not connected."""
        # if u and v are strings, look up their index
        u = self.__lookup_vertex_index(u)
        v = self.__lookup_vertex_index(v)

        # Get the actual weight from the adjacency matrix, this is an O(1) operation
        return float(self.matrix[u][v])

    def find_shortest_path(self, start, vertices):
        """Returns the shortest path that pass through all the supplied vertices, \
        and the weight of that path.
        Uses the nearest neighbor greedy algorithm."""
        # Time complexity is O(N^2)
        # Space complexity is O(N)
        u = self.__lookup_vertex_index(start)
        visited = []  # This will be our completed path
        to_visit = []  # This tracks where we still have to go

        # For simplicity at the user level, the vertices are referenced by string value
        # convert all vertices to indexes, and keep track of what we need to visit
        # This particular part is O(N)
        for vertex in vertices:
            to_visit.append(self.__lookup_vertex_index(vertex))

        # Call into the recursive method to initiate the algorithm
        total_weight = self.__find_shortest_path(u, to_visit, visited)

        # The return value is a tuple of the full path in traversal order, and its total weight
        return (visited, total_weight)

    def __find_shortest_path(self, start, to_visit: list, visited: list):
        # Time complexity is O(N^2)
        # It's difficult to measure, due to recursion,
        # but due to the loops, it's no worse than O(N^2)
        if to_visit is not None and len(to_visit) > 0:

            # We still have vertices to process, keep progressing through the algorithm
            # This "visits" the vertex
            # This is O(N)
            next_node = self.__find_nearest_of(start, to_visit)

            # a -1 return value means no vertex was found.
            # This will only be possible if the graph is directed, or is a single vertex
            if next_node < 0:
                raise IndexError("No path found")

            # We have visited the vertex
            to_visit.remove(next_node)              # remove it from the to_visit list
            visited.append(next_node)               # and add it to the visited list

            # Get the weight of the edge
            weight = self.get_weight(start, next_node)

            # Recurse, using the node we found as the starting node for the next iteration
            # The return value will be the weight, which we add to the weight we already found
            return weight + self.__find_shortest_path(next_node, to_visit, visited)

        # We visited all the vertices, the operation is complete.
        return 0

    def __find_nearest_of(self, start, vertices):
        """Finds the vertex in the list that's closest to the start point."""

        # Placeholder for the nearest.
        # Distance is Inf so any point will satisfy requirements first time.
        nearest_weight = float('Inf')
        nearest_vertex = int(-1)

        # Scan the entire matrix row (start), for the v with the smallest weight
        # This loop is O(N)
        for v in vertices:
            weight = self.get_weight(start, v)

            if 0 < weight < nearest_weight:
                # If this edge is the smallest that we've seen, save it
                # We found a candidate for the nearest
                nearest_weight = weight
                nearest_vertex = v

        # Once the iteration is complete, we have the closest vertex
        # If we didn't actually find one, it will return -1, which is an invalid index
        return nearest_vertex

    def __repr__(self):
        string = ""

        for row in self.matrix:
            string += f"{repr(row)}\n"

        return string
