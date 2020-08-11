import sys
from entities.Truck import Truck
sys.path.append("..")


class Driver:
    """Truck driver"""
    def __init__(self, name):
        """Creates a new driver with the specified name"""
        self.name = name
        self.truck = None
        self.__hash = None

    def assign_truck(self, truck: Truck):
        """Assigns the driver to a truck."""
        # Clear the old truck of the driver, if one is assigned
        if truck is not None:
            truck.driver = None

        # Assign the driver to the truck, and the truck to the driver
        self.truck = truck
        truck.driver = self

    def __hash__(self):
        """Returns a hash of the driver's name."""
        # The hash is based on the name, and will be identical
        # if two drivers have the same name

        _INITIAL_VALUE = 5432
        _MULTIPLIER = 11

        # Cache the hash, so we only need to do this once per object
        # Simple character hash
        if self.__hash is None:
            hash_ = _INITIAL_VALUE

            for c in self.name:
                hash_ = (hash_ * _MULTIPLIER) + ord(c)

            self.__hash = hash_

        return self.__hash

    def __eq__(self, other):
        return self.name == other

    def __str__(self):
        return self.name
