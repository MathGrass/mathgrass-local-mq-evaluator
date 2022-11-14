import datetime
import logging
from typing import Tuple, List, Dict

import psycopg2

from model.graph_model import Edge, Graph, Vertex


class BasicEvalRequestData:
    """ This class represents a data structure for evaluation requests.
    """
    def __init__(self, graph: Graph, script: str):
        """ Initialize a BasicEvalRequestData instance.

        :param graph: graph
        :param script: script to run
        """
        self.graph = graph
        self.script = script


class Database:
    """ This class represents an interface to a database instance.
    """
    def __init__(self):
        """ Initialize a Database instance and connect to a database.
        """
        # TODO: make db configurable
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                database="mathgrass_db",
                user="postgres",
                password="postgres")
            logging.info("Connection to database established!")

        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(error)
            if self.conn is not None:
                self.conn.close()
                logging.error("Database connection closed!")
            
    def _get_task_template_and_graph_id(self, task_id: int) -> Tuple[int, int] | None:
        """ Get the task template ID and the graph ID for a given task ID.

        :param task_id: ID of task
        :return: (task template ID, graph ID)
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = " + str(task_id))
        tasks = self.get_cursor_elements_as_dicts(cursor)

        try:
            task = next(tasks)
        except IndexError:
            logging.error(f"Task with ID {task_id} not found!")
            return None

        return task["task_template_id"], task["graph_id"]
   
    def _get_task_solver_id(self, task_template_id: int) -> int | None:
        """ Get the task solver ID for a given task template ID.

        :param task_template_id: ID of task template
        :return: ID of task solver
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasktemplates WHERE id = " + str(task_template_id))
        task_templates = self.get_cursor_elements_as_dicts(cursor)

        try:
            task_template = next(task_templates)
        except IndexError:
            logging.error(f"Task template with ID {task_template_id} not found!")
            return None

        return task_template["task_solver_id"]

    def _get_execution_descriptor(self, task_solver_id: int) -> str | None:
        """ Get the execution descriptor for given task solver ID.

        :param task_solver_id: ID of task solver
        :return: execution descriptor (script)
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasksolvers WHERE id = " + str(task_solver_id))
        task_solvers = self.get_cursor_elements_as_dicts(cursor)

        try:
            task_solver = next(task_solvers)
        except IndexError:
            logging.error(f"Task solver with ID {task_solver_id} not found!")
            return None

        return task_solver["execution_descriptor"]

    def _get_graph(self, graph_id: int) -> Graph | None:
        """ Get the graph for specified graph ID.

        :param graph_id: ID of graph to load
        :return: Graph
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM graphs WHERE id = " + str(graph_id))
        graphs = self.get_cursor_elements_as_dicts(cursor)

        try:
            graph = next(graphs)
        except IndexError:
            logging.info(f"Graph with ID {graph_id} not found")
            return None

        # create graph string
        vertices = self._get_vertices(graph_id)
        edges = self._get_edges(graph_id)

        # build graph
        vertex_dict = {}
        for vertex in vertices:
            vertex_dict[vertex["id"]] = Vertex(vertex["id"], vertex["label"], vertex["x"], vertex["y"])
        
        edge_obj_list = []
        for edge in edges:
            edge_obj_list.append(Edge(vertex_dict[edge["v1_id"]], vertex_dict[edge["v2_id"]], edge["label"]))

        return Graph(graph["id"], graph["label"], list(vertex_dict.values()), edge_obj_list)

    def _get_edges(self, graph_id: int):
        """ Get the edges of the graph with specified graph ID.

        :param graph_id: ID of graph
        :return: edges
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM graphs_edges AS ge INNER JOIN edges AS e ON e.id = ge.edges_id "
                       "WHERE graph_entity_id = " + str(graph_id))
        edges = self.get_cursor_elements_as_dicts(cursor)

        return edges

    def _get_vertices(self, graph_id: int):
        """ Get the vertices of the graph with specified graph ID.

        :param graph_id: ID of graph
        :return: vertices
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM graphs_vertices AS gv INNER JOIN vertices AS v ON v.id = gv.vertices_id "
                       "WHERE graph_entity_id = " + str(graph_id))
        vertices = self.get_cursor_elements_as_dicts(cursor)

        return vertices

    def get_basic_eval_request_data(self, task_id: int) -> BasicEvalRequestData:
        """ Get data for evaluation request for specified task ID.

        :param task_id: ID of task
        :return: BasicEvalRequestData
        """
        task_template_id, graph_id = self._get_task_template_and_graph_id(task_id)

        task_solver_id = self._get_task_solver_id(task_template_id)
        script = self._get_execution_descriptor(task_solver_id)
        graph = self._get_graph(graph_id)

        return BasicEvalRequestData(graph, script)

    @staticmethod
    def get_cursor_elements_as_dicts(cursor) -> Dict:
        """ Load cursor elements as a dictionary.

        :param cursor: DB cursor
        :return: dictionary
        """
        colnames = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            d = {}
            for i in range(len(colnames)):
                d[colnames[i]] = row[i]
            yield d

    def add_evaluation_result(self, request_id: int, answer_is_true: bool):
        """ Add an evaluation result to the database.

        :param request_id: ID of request
        :param answer_is_true: whether answer is correct or not
        :return: None
        """
        # get current timestamp
        timestamp = datetime.datetime.now().isoformat()

        # update task result with id = request_id (table name is taskresults)
        cur = self.conn.cursor()
        answer_true = "true" if answer_is_true else "false"
        sql = "UPDATE taskresults SET answer_true = %s, evaluation_date = %s WHERE id = %s"
        cur.execute(sql, (str(answer_true), str(timestamp), str(request_id)))

        # commit
        self.conn.commit()
