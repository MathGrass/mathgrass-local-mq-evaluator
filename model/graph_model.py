from typing import List, Dict


class Graph:
    """ This class represents a graph consisting of Edges, Vertices and Labels.
    """
    def __init__(self, id: int, label: str, vertices: List, edges: List):
        """ Initialize a Graph instance.

        :param id: ID of graph
        :param label: graph label
        :param vertices: vertices in graph
        :param edges: edges in graph
        """
        self.id = id
        self.edges = edges
        self.vertices = vertices
        self.label = label
    
    def to_json(self) -> Dict:
        """ Return a JSON representation of this class instance.

        :return: Instance representation as dictionary
        """
        return {
            "id": self.id,
            "edges": [edge.to_json() for edge in self.edges],
            "vertices": [vertex.to_json() for vertex in self.vertices],
            "label": self.label
        }
    

class Vertex:
    """ This class represents a vertex consisting of coordinates and a label.
    """
    def __init__(self, id: int, label: str, x: int, y: int):
        """ Initialize a Vertex instance.

        :param id: ID of vertex
        :param label: vertex label
        :param x: x coordinate
        :param y: y coordinate
        """
        self.id = id
        self.label = label
        self.x = x
        self.y = y

    def to_json(self) -> Dict:
        """ Return a JSON representation of this class instance.

        :return: Instance representation as dictionary
        """
        return {
            "id": self.id,
            "label": self.label,
            "x": self.x,
            "y": self.y
        }


class Edge:
    """ This class represents an edge consisting of a source and target vertex and a label.
    """
    def __init__(self, source_vertex: Vertex, target_vertex: Vertex, label: str):
        """ Initialize an Edge instance.

        :param source_vertex: source vertex
        :param target_vertex: target vertex
        :param label: edge label
        """
        self.first_vertex = source_vertex
        self.second_vertex = target_vertex
        self.label = label

    def to_json(self) -> Dict:
        """ Return a JSON representation of this class instance.

        :return: Instance representation as dictionary
        """
        return {
            "source_vertex": self.first_vertex.to_json(),
            "target_vertex": self.second_vertex.to_json(),
            "label": self.label
        }
