import csv
import sys

from entities.Location import Location
from structures.Graph import Graph
from .Logger import Logger
sys.path.append("..")


class RouteLoader:
    """Loads the distance table from a file."""
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.packages = None
        self.graph = None

    def load(self):
        """Loads the contents of the file passed to constructor."""

        with open(self.filename, mode='r') as csv_file:
            reader = csv.DictReader(csv_file)
            line_count = 0

            # Once we know the number of columns, we can create the graph
            self.graph = Graph(len(reader.fieldnames) -
                               2)  # First two columns aren't relevant

            # Time complexity is O(N^2)
            for row in reader:
                # Print the headers
                if line_count == 0:
                    Logger.log(Logger.LogLevel.INFORMATION,
                               f"Loading destinations from {self.filename}")
                    Logger.log(Logger.LogLevel.DEBUG,
                               "Columns: " + ", ".join(row))

                line_count += 1

                # This assumes the CSV file is in matrix format,
                # and the rows are in the same order as the columns
                Logger.log(
                    Logger.LogLevel.DEBUG,
                    f"Row {line_count}: Location {row[reader.fieldnames[0]]}")

                # Each row will be processed one column at a time, per edge
                # First, get the row name, which will remain constant for each outer iteration
                row_name = Location(row[reader.fieldnames[1]].strip())

                # Use second column for the vertex name, so it will match up to the packages
                self.graph.add_vertex(row_name)

                # While we are loading, we don't have all the vertex names yet,
                # So load the row by name, but the column by index
                # Time complexity is O(N)
                for v in range(2, len(reader.fieldnames)):
                    col_name = reader.fieldnames[v]
                    weight = row[col_name]

                    try:
                        # If the weight wasn't a number (empty), then ignore it
                        # It will be filled in later if the graph is undirected
                        weight = float(weight)
                        self.graph.add_edge(row_name, v - 2, weight)
                    except ValueError:
                        pass

            Logger.log(Logger.LogLevel.INFORMATION,
                       f"Loaded {line_count} destinations")
