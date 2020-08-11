import csv
import sys

from entities.Package import Package
from .Logger import Logger
sys.path.append("..")


class PackageLoader(object):
    """Loads packages from a CSV file"""
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.packages = None

    def load(self):
        """Loads the contents of the file passed to constructor."""
        self.packages = []  # Create a new array for the packages we're loading

        with open(self.filename, mode='r') as csv_file:
            reader = csv.DictReader(csv_file)
            line_count = 0

            # Time complexity is O(N)
            for row in reader:
                # Print the headers
                if line_count == 0:
                    Logger.log(Logger.LogLevel.INFORMATION,
                               f"Loading packages from {self.filename}")
                    Logger.log(Logger.LogLevel.DEBUG,
                               "Columns: " + ", ".join(row))

                line_count += 1

                Logger.log(
                    Logger.LogLevel.DEBUG,
                    f"Row {line_count}: Package {row['Package ID']} goes to {row['Address']} by {row['Delivery Deadline']}"
                )
                self.packages.append(
                    Package(row["Package ID"], row["Address"], row["City"],
                            row["State"], row["Zip"], row["Mass KILO"],
                            row["Special Notes"], row["Delivery Deadline"]))

            Logger.log(Logger.LogLevel.INFORMATION,
                       f"Loaded {line_count} packages")
