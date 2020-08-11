import sys
from enum import Enum
from datetime import datetime, time

from exceptions.DeliveryException import DeliveryException
from entities.Location import Location
from utilities.Logger import Logger
sys.path.append("..")


class Package:
    """Package to be delivered"""
    class Status(Enum):
        """State of the package"""
        DELAYED = 0
        AT_FACILITY = 1
        ON_TRUCK = 2
        IN_ROUTE = 3
        DELIVERED = 4
        REJECTED = 5

        def __str__(self):
            return self.name

        def __repr__(self):
            return self.name

    def __init__(self,
                 package_id: int,
                 address: str,
                 city: str,
                 state: str,
                 zip_code: int,
                 weight: int,
                 notes: str = None,
                 time_deadline: str = "EOD",
                 time_arrival: str = None,
                 status: Status = Status.AT_FACILITY):
        super().__init__()

        # Initialize data members, process arguments
        self.id = int(package_id)
        self._location = Location(address, int(zip_code))
        self.city = city
        self.state = state
        self.weight = int(weight)
        self._status = Package.Status(status)
        self.time_deadline = self.__process_time(time_deadline)
        self.time_arrival = self.__process_time(time_arrival)
        self.time_delivered = None
        self._truck = None

        self.notes = notes
        self.requires_truck = None  # If not None, then package must be on a specific truck ID
        self.requires_packages = None  # Indicates package must be on same truck as other packages

        # Parsing notes is last, it can change above values
        self.__process_notes(
            notes
        )  # Parse the notes, and make adjustments to the package information

    @property
    def truck(self):
        """The truck the package is assigned too."""
        return self._truck

    @truck.setter
    def truck(self, value):
        self._truck = value
        if value is not None:
            self.status = Package.Status.ON_TRUCK

    @property
    def location(self):
        """The delivery location for the package."""
        return self._location

    @location.setter
    def location(self, value):
        self._location = value
        if self.truck is not None:
            # If the location changes, change the package status and recalculate the route
            self.status = Package.Status.ON_TRUCK
            self.truck.calculate_route()
        self.notes = None

    @property
    def status(self):
        """The current status of the package."""
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        # If the package is marked as on the truck, clear any delivered time, if set
        # This can happen if the package was marked REJECTED
        if value == Package.Status.ON_TRUCK:
            self.time_delivered = None

    def deliver(self, delivery_time: time):
        """Delivers the package."""
        # Mark the delivery time
        self.time_delivered = delivery_time

        if self.notes is not None and self.notes.startswith("Wrong address"):
            # If the package was sent to the wrong address
            # Mark it as rejected and leave it on the truck. It will be corrected later.
            self.status = Package.Status.REJECTED
            raise DeliveryException(self.notes)

        # Package was successfully delivered!
        self.status = Package.Status.DELIVERED
        Logger.log(
            Logger.LogLevel.INFORMATION,
            f"Package {self.id} was delivered by truck {self.truck.id} at {delivery_time.time()}!"
        )

        # Log an error if the package was late
        if delivery_time.time() > self.time_deadline:
            Logger.log(Logger.LogLevel.ERROR,
                       f"Package {self.id} was delivered late!")

    @classmethod
    def __process_time(cls, time_):
        """Converts a string into a time object."""

        # Substitute EOD for the max time, 11:59 pm
        if time_ == "EOD":
            return time.max
        if time_ is not None:
            # The time string could be in two formats: '10:00 am' or '10:00:00 am'
            try:
                return datetime.strptime(time_, "%H:%M:%S %p").time()
            except ValueError:
                return datetime.strptime(time_, "%H:%M %p").time()
        return None

    def __process_notes(self, notes: str):
        # This reads the "Notes" column in the packages list,
        # and sets the correct information based on it
        if notes.startswith("Can only be on truck"):
            # Package must be placed on a specific truck
            self.requires_truck = int(notes.split(
                " ")[-1])  # The last "word" is the truck number, save that
            Logger.log(Logger.LogLevel.DEBUG,
                       f"Package requires truck {self.requires_truck}")
        elif notes.startswith("Delayed on flight"):
            # Package was delayed, grab the arrival time from the note and save it
            words = notes.split(" ")
            self.time_arrival = self.__process_time(f"{words[-2]} {words[-1]}")
            self.status = Package.Status.DELAYED
            Logger.log(
                Logger.LogLevel.DEBUG,
                f"Package will not arrive at hub until {self.time_arrival}")
        elif notes.startswith("Must be delivered with"):
            # Package must be placed on the same truck as at least one other package
            packages_string = notes[
                23:]  # Grab the last part, which are truck numbers
            packages = packages_string.split(",")
            self.requires_packages = []

            for t in packages:
                self.requires_packages.append(int(t))

            Logger.log(
                Logger.LogLevel.DEBUG,
                f"Package must be on the same truck as {self.requires_packages}"
            )

    def __hash__(self):
        # Use the package ID as the "hash" which will easily map to a bucket
        return self.id

    def __str__(self):
        """Returns a string representation of the package."""
        # This is used when printing package information in the display UI.
        # Truncate the address if it's too long
        address = self.location.address[:12] + '..' if len(
            self.location.address) > 14 else self.location.address
        city = self.city[:10] + '..' if len(self.city) > 12 else self.city
        address_formatted = f"{address}, {city} {self.state}, {self.location.zip}"
        # If the date isn't set, mark it with dashes to indicate not delivered
        delivered_time = self.time_delivered.time().strftime(
            '%H:%M:%S') if self.time_delivered is not None else '--:--:--'

        # If a package was late, mark it with a '*'
        if self.time_delivered is not None and self.time_delivered.time(
        ) > self.time_deadline:
            delivered_time += '*'
        else:
            delivered_time += ' '

        # Finally build the entire string to display
        truck = str(
            self.truck.id).rjust(5) if self.truck is not None else '-'.rjust(5)
        return f"{self.id:7d} {truck} {str(self.status):11} {self.weight:4d} {delivered_time} {self.time_deadline.strftime('%H:%M:%S')} {address_formatted}"

    def __repr__(self):
        return f"Package {self.id}: Status: {self.status}"
