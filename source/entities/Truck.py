import sys
from enum import Enum
from datetime import timedelta, datetime, time

from exceptions.NoDriverError import NoDriverError
from exceptions.NoPackagesError import NoPackagesError
from exceptions.TooManyPackagesError import TooManyPackagesError
from exceptions.AlreadyInProgressException import AlreadyInProgressException
from exceptions.DeliveryException import DeliveryException
from exceptions.TooEarlyError import TooEarlyError
from structures.HashSet import HashSet
from structures.Graph import Graph
from utilities.Logger import Logger
from entities.Package import Package
from entities.Location import Location
sys.path.append("..")


class Truck:
    """A truck which contains packages to be delivered."""
    class Status(Enum):
        """Truck status."""
        AT_FACILITY = 0
        ON_ROUTE = 1
        DELIVERING = 2
        EMPTY = 3

        def __str__(self):
            return self.name

        def __repr__(self):
            return self.name

    AVERAGE_SPEED = 18  # Trucks move 18 MPH
    AVERAGE_SPEED_PER_SEC = AVERAGE_SPEED / 3600
    MAXIMUM_NUMBER_OF_PACKAGES = 16
    HUB_LOCATION = Location('HUB')

    def __init__(self, truck_id, current_time: datetime, start_time: time,
                 destinations: Graph):
        """Creates a new truck."""
        super().__init__()

        # Initialize data members
        self.id = truck_id
        self.last_update = current_time
        self.last_status_update = current_time
        self.start_time = start_time
        self.route_start_time = None
        self.driver = None
        self.packages = HashSet(self.MAXIMUM_NUMBER_OF_PACKAGES)
        self._status = self.Status.AT_FACILITY
        self.speed = self.AVERAGE_SPEED
        self.destinations = destinations
        self.target = None
        self.source = None
        self.route = None
        self.route_start_time = None
        self.distance_to_target = float('Inf')
        self.distance_traveled = 0
        self.delivered_packages = 0
        self.distance_last_update = 0
        self.elapsed_last_update = timedelta()
        self.route_count = 0
        self.force_wait_for_packages = False

    @property
    def status(self):
        """The current status of the truck."""
        return self._status

    @status.setter
    def status(self, status: Status):
        self._status = status
        self.last_status_update = self.last_update

    def add_package(self, package: Package):
        """Adds a package to the truck."""
        if len(self.packages) < self.MAXIMUM_NUMBER_OF_PACKAGES:
            # Add the packageS
            package.truck = self
            self.packages.add(package)
            Logger.log(
                Logger.LogLevel.VERBOSE,
                f"Package {package.id} added to truck {self.id}, total: {len(self.packages)}"
            )
        else:
            # Too many packages
            raise TooManyPackagesError(
                f"Package limit for truck {self.id} exceeded.")

    def calculate_route(self):
        """Calculates the optimal path for delivering the packages on board."""
        # Get a list of all the "unique" addresses
        # HashSet is useful for that, since any duplicates are ignored
        # The runtime complexity of this method is O(N^2)

        # A HashSet is built containing all the locations for the packages
        # If there are multiple packages going to the same location,
        # They are counted as one total, for optimized path calculation
        # Worst case space complexity is O(N^2)
        locations = HashSet(len(self.packages))         # We have at most the number of packages
        priority_locations = HashSet(len(self.packages))

        # Build a list of all the locations,
        # if there are packages with a delivery deadline,
        # We build a path to those first, and come back to the rest after
        # If non-priority packages share a location with priority packages,
        # They will be included in the delivery.
        # Worst case time complexity for this is O(N)
        for p in self.packages:
            if p.status == Package.Status.ON_TRUCK or p.status == Package.Status.IN_ROUTE:
                locations.add(p.location)
                if p.time_deadline < time.max:
                    priority_locations.add(p.location)

        # if we have packages that have a deadline, prioritize those
        if len(priority_locations) > 0:
            locations = priority_locations

        if self.status != Truck.Status.EMPTY:
            # Worst case time complexity of find_shortest_path is O(N^2)
            if self.route is None or len(self.route) == 0:
                # Now that we know how many locations we have, pass that to the graph for the result
                (self.route, distance) = self.destinations.find_shortest_path(
                    self.HUB_LOCATION, locations)
            else:
                # If the route was already defined, some change happened, and we need to fix it
                # This will build a new route which will take affect after the next delivery
                Logger.log(Logger.LogLevel.WARNING,
                           f"Recalculating route due to package correction.")
                (self.route, distance) = self.destinations.find_shortest_path(
                    self.target, locations)

            if distance > 0:
                Logger.log(
                    Logger.LogLevel.VERBOSE,
                    f"Calculated path as {self.route} with a distance of {distance} miles"
                )

    def __calculate_next_target(self):
        # Worst case time complexity is O(N^2)
        try:
            # First run, source will be set, and target will not
            if self.target is not None:
                self.source = self.target
            # Set the first target destination
            self.target = self.destinations.vertices[self.route.pop(0)]
            # O(N) time complexity
            self.__update_target_packages(Package.Status.IN_ROUTE)
        except IndexError:
            # No more packages
            if self.target is not None and self.target == self.HUB_LOCATION:
                # We are home
                self.status = Truck.Status.AT_FACILITY
                self.source = None
                self.route = None
                return

            # No more packages in the current route, check if there are non-priority packages
            # O(N^2) time complexity, calculate_route is called at most once
            for p in self.packages:
                if p.status == Package.Status.ON_TRUCK:
                    # Time O(N^2)
                    self.calculate_route()
                    return

            # No more deliverable packages, return to HUB
            self.status = Truck.Status.EMPTY
            self.target = self.HUB_LOCATION
        # Because we look up weights based on Location class (string), not an index
        # This is an O(N) operation
        self.distance_to_target = self.destinations.get_weight(
            self.source, self.target)

    def start_route(self):
        """Tells the truck to start delivering packages."""
        # If the day hasn't started yet, it can't leave
        if self.start_time > self.last_update:
            raise TooEarlyError("Truck can't leave before {self.start_time}")
        # Truck can't begin a route if it's already on one
        if self.status == Truck.Status.ON_ROUTE or self.status == Truck.Status.EMPTY:
            raise AlreadyInProgressException(
                f"Truck {self.id} is already on route.")
        # If there is no driver assigned, the truck cannot leave
        if self.driver is None:
            raise NoDriverError(
                f"Truck {self.id} cannot leave without a driver!")
        # If the truck has no deliverable packages, it cannot leave
        if self.packages is None or len(
                self.packages) == 0 or self.force_wait_for_packages:
            self.force_wait_for_packages = False
            raise NoPackagesError(
                "Truck {self.id} cannot leave without packages!")

        for p in self.packages:
            if p.status == Package.Status.REJECTED:
                raise NoPackagesError(
                    "Truck {self.id} cannot leave without deliverable packages!"
                )

        # Build the route and set the starting conditions
        self.calculate_route()
        self.distance_traveled = 0
        self.delivered_packages = 0
        self.route_start_time = self.last_update
        self.status = Truck.Status.ON_ROUTE  # Signal the truck has started
        self.source = self.HUB_LOCATION
        self.__calculate_next_target()
        self.route_count += 1  # Counter for how many times the truck left the HUB

    def simulate(self, current_datetime: datetime):
        """Simulate truck movement since the last update."""
        # Worst case time complexity O(N^2)
        # This simulates the truck's activity
        # Calculate the changes that have happened since the last update
        previous_datetime = self.last_update
        timestep = current_datetime - previous_datetime
        self.last_update = current_datetime
        self.elapsed_last_update = timedelta()
        self.distance_last_update = 0

        if self.status == Truck.Status.AT_FACILITY:
            # If the truck is sitting at the facility, see if it can leave
            try:
                # start_route is O(N^2)
                self.start_route()
            except (NoDriverError, NoPackagesError, AlreadyInProgressException,
                    TooEarlyError):
                # If it can't leave yet, don't do anything else
                return
        elif self.status == Truck.Status.EMPTY and len(self.packages) > 0:
            self.force_wait_for_packages = True

        # Calculate the distance we traveled since the last update
        delta_distance = self.AVERAGE_SPEED_PER_SEC * timestep.total_seconds()
        self.distance_to_target -= delta_distance
        self.distance_traveled += delta_distance
        self.distance_last_update = delta_distance
        self.elapsed_last_update = timestep
        overflow = self.distance_to_target

        if self.distance_to_target <= 0:
            # Worst case time complexity O(N^2)
            if self.status == Truck.Status.ON_ROUTE:
                # We reached the destination, deliver the package!
                self.__deliver_packages(self.target)
                self.__calculate_next_target()

                # Any overflow we want to apply towards the next destination
                self.distance_to_target += overflow
            elif self.status == Truck.Status.EMPTY:
                self.__calculate_next_target()

                # We have returned to the HUB
                # Any overflow we cancel out, we didn't actually travel that distance
                self.distance_traveled -= overflow

    def __update_target_packages(self, status: Package.Status):
        # This is O(N) time complexity
        for p in self.packages:
            if p.location == self.target:
                p.status = status

    def __deliver_packages(self, location: Location):
        """Delivers all packages for the specified location."""

        # Check all the packages that are still on this truck
        # This is O(N)
        for p in self.packages:
            if p.location == location and p.status == Package.Status.IN_ROUTE:
                try:
                    # Delivery successful remove package
                    p.deliver(self.last_update)
                    self.packages.remove(p)
                    self.delivered_packages += 1
                except DeliveryException:
                    # There was an exception during deliver (wrong address?), log it and keep going
                    Logger.log(Logger.LogLevel.ERROR,
                               f"Error delivering package {p.id}.")

    def __str__(self):
        target = str(self.target)
        return f"{self.id:5d} {str(self.driver).ljust(8)} {self.route_count:5d} {len(self.packages):8d} {self.distance_traveled:8.2f} {str(self.status).ljust(11)} {target[:35] + '..' if len(target) > 37 else target}"
