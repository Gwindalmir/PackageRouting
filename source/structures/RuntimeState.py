import sys
import os
import ctypes
from datetime import datetime, timedelta, time, date
from ctypes import c_long, c_ulong
from time import sleep

from exceptions.NoPackagesError import NoPackagesError
from exceptions.NoDriverError import NoDriverError
from exceptions.TooManyPackagesError import TooManyPackagesError
from exceptions.AlreadyInProgressException import AlreadyInProgressException
from exceptions.TooEarlyError import TooEarlyError
from utilities.Logger import Logger
from utilities.PackageLoader import PackageLoader
from utilities.RouteLoader import RouteLoader
from entities.Package import Package
from entities.Truck import Truck
from entities.Driver import Driver
from entities.Location import Location
from entities.PackageCorrection import PackageCorrection
from structures.HashSet import HashSet
sys.path.append("..")

# This is for manipulating the console window in Windows.
if sys.platform.startswith('win'):
    g_handle = ctypes.windll.kernel32.GetStdHandle(c_long(-11))


class RuntimeState:
    """State of the program."""

    _ALIGNMENT_CENTER = 0
    _ALIGNMENT_LEFT = 1
    _ALIGNMENT_RIGHT = 2

    def __init__(self, simulation_speed_seconds=60):
        # Initialize all data members
        self._rows = 25
        self._cols = 80

        self._destinations = None
        self._packages = None
        self._trucks = []
        self._drivers = []
        self._start_time = datetime.combine(date.today(), time(7, 50))
        self._end_time = datetime.combine(date.today(), time(23, 59, 59))
        self._current_time = self._start_time
        self._simulation_speed = timedelta(seconds=simulation_speed_seconds)
        self._total_delivered = 0
        self._total_time = timedelta()
        self._total_distance = 0
        self._ui_inited = False
        self._exceptions = HashSet(5)

    @property
    def destinations(self):
        """The Graph containing the destinations."""
        return self._destinations

    @property
    def packages(self):
        """The HashSet of all the packages to deliver."""
        return self._packages

    @property
    def trucks(self):
        """The list of trucks assigned to the HUB location."""
        return self._trucks

    @property
    def drivers(self):
        """The list of drivers assigned to the HUB location."""
        return self._drivers

    @property
    def start_time(self):
        """Time the trucks leave the facility for deliveries."""
        return self._start_time

    @property
    def end_time(self):
        """The time deliveries still stop. This is the end-of-day."""
        return self._end_time

    @property
    def current_time(self):
        """The current time."""
        return self._current_time

    @property
    def total_distance(self):
        """The total combined distanced traveled by the all trucks."""
        return self._total_distance

    @property
    def total_time(self):
        """The total combined time taken by the all trucks while on route."""
        return self._total_time

    @property
    def packages_delivered(self):
        """The total number of packages delivered."""
        return self._total_delivered

    def load_destinations(self, filename: str):
        """Loads all the packages from the specified CSV file."""

        # Build the graph of distance table
        route_loader = RouteLoader(filename)
        route_loader.load()
        self._destinations = route_loader.graph

    def load_packages(self, filename: str):
        """Loads all the packages from the specified CSV file."""

        # Build a list of all the packages
        package_loader = PackageLoader(filename)
        package_loader.load()

        # Create a HashSet large enough to contain all the packages without collisions
        # Doing so keeps the HashSet operating in O(1) time for lookups, insertions, and removals
        self._packages = HashSet(int(len(package_loader.packages) * (4 / 3)))

        # Load the HashSet with the list provided by PackageLoader
        for p in package_loader.packages:
            self._packages.add(p)

        return len(self._packages)

    def add_trucks(self, count: int, start_time: time):
        for _ in range(count):
            self.add_truck(start_time)

    def add_truck(self, start_time):
        """Creates a new truck and adds it to the trucks list, returns the created entity."""
        # Create a new track, with the current time, so truck operation time can be tracked
        if isinstance(start_time, time):
            start_time = datetime.combine(date.today(), start_time)

        truck = Truck(
            len(self.trucks) + 1, self.current_time, start_time,
            self.destinations)
        self._trucks.append(truck)
        return truck

    def add_drivers(self, names: list):
        for name in names:
            self.add_driver(name)

    def add_driver(self, name: str):
        """Creates a new driver with the specified name and adds it to the drivers list, \
        returns the created entity."""
        driver = Driver(name)
        self._drivers.append(driver)
        return driver

    def add_package_correction(self, package_id, update_time, updated_information):
        """Add a correction to a package that occurs at a specified time."""
        self._exceptions.add(PackageCorrection(package_id, update_time, updated_information))

    def assign_packages(self, truck: Truck):
        """Parses the packages list, and selects ones to go into specified truck."""
        # Package assignment follows a set of rules:
        # 1) If the truck is already on a route, don't add any
        # 2) If the package isn't at the facility ignore it
        # 3) If the package requires a specific truck,
        #    add it only if the current truck being loaded is that truck
        # 4) If the package requires other packages, check to see if any of
        #    the other packages have already been added.
        #  a) If so, check if they were loaded in this truck, and add that package too
        #  b) If not, then:
        #   1) If no packages have been loaded, then load this one, and each related package
        #   2) If another package was loaded on a different truck, don't load it on this truck
        # 5) If another package going to the same location was already loaded,
        #    add this one too for optmizing
        # 6) If the package has a delivery window in the next 3 hours, add it
        #    Then mark the truck as having priority packages
        # 7) If the truck is marked as having priority packages, and the current package
        #    being loaded does not have a deadline, don't load it yet.
        # 8) For all other cases, load the package on the truck, up to the maximum allowed (16)
        if truck.status != Truck.Status.AT_FACILITY:
            raise AlreadyInProgressException

        delivery_window = timedelta(hours=3)  # Trucks can deliver all their packages in 3 hours
        has_deadline = False
        pending_add = HashSet(len(self.packages))

        # Worst case time complexity for this is O(N^3)
        # Worst case space complexity is O(N^2)
        # Where P is the number of packages, and R is the number of required packages in P
        for p in self.packages:
            try:
                if p.time_arrival is not None and p.time_arrival > self.current_time.time():
                    continue  # Skip packages that haven't arrived in the facility yet

                if p.status == Package.Status.DELAYED:
                    # Package arrived, mark it available
                    p.status = Package.Status.AT_FACILITY

                if p.status != Package.Status.AT_FACILITY:
                    continue  # Skip packages that aren't at the facility

                if p.requires_truck is not None and p.requires_truck != truck.id:
                    continue  # Skip if it's required to go into a different truck

                if p.requires_packages is not None:
                    # If it requires delivery with another package
                    # check to see if one of the requirements was already
                    # placed on a different truck.
                    # This loop has a complexity of O(N^2)
                    for p1 in self.packages:
                        try:
                            # Complexity of the search is O(N)
                            # This additional storage adds to the space complexity
                            # The axiliary space complexity is O(N)
                            p.requires_packages.index(p1.id)

                            # If the package is on this truck, add this package too
                            if p1.truck == truck:
                                # Complexity for this should be O(1), assuming no collisions
                                truck.add_package(p)
                                break

                            if p1.truck is not None:
                                pending_add = None
                            else:
                                # If we have other related packages, flag those too
                                # as they might not have an indicator of requirements
                                if pending_add is not None:
                                    pending_add.add(p1.id)
                        except ValueError:
                            continue

                    if p.truck is not None:
                        continue  # If this package was assigned, go to the next one

                # Add any complimentary packages that weren't flagged before
                # Time complexity is O(N)
                if pending_add is not None:
                    try:
                        for pending in pending_add:
                            if pending == p.id:
                                truck.add_package(p)
                                pending_add.remove(pending)
                                break
                    except ValueError:
                        pass

                if p.truck is not None:
                    continue  # If this package was assigned, go to the next one

                # If we already have a package going nearby, add it
                # The time complexity of this is also O(N)
                for p1 in truck.packages:
                    if p1.location == p.location:
                        truck.add_package(p)
                        break

                if p.truck is not None:
                    continue  # If this package was assigned, go to the next one

                # Prioritize packages with an early delivery deadline
                if p.time_deadline < (self.current_time +
                                      delivery_window).time():
                    truck.add_package(p)
                    has_deadline = True
                    continue

                # If we get here, package doesn't already have a home. Add it.
                if has_deadline is False:
                    truck.add_package(p)

            except TooManyPackagesError:
                # No more room in this truck
                return

    def check_for_corrections(self):
        """Check for any package corrections that need to be performed."""
        for c in self._exceptions:
            if self.current_time.time() >= c.time:
                # We have a correction to make, do it
                for p in self.packages:
                    if p.id == c.id:
                        if isinstance(c.correction, Location):
                            p.location = c.correction
                        self._exceptions.remove(c)
                        break
        
        # Check if any packages have arrived
        for p in self.packages:
            if (p.status == Package.Status.DELAYED and p.time_arrival < self.current_time.time()):
                p.status = Package.Status.AT_FACILITY

    def simulate(self):
        """Simulates the world. Returns only when simulation ends."""

        while self.current_time < self.end_time:
            # Draw the user interface status screen
            self.draw()

            # If all the packages were delivered, we can stop
            if self._total_delivered >= len(self.packages):
                break

            # Handle package exceptions
            self.check_for_corrections()

            # Simulate each truck
            # Since the number of trucks doesn't change, this is a constant loop O(1)
            # If the number of trucks could change throughout runtime, it would be O(T)
            for truck in self.trucks:
                try:
                    # start_route is O(N^2)
                    truck.start_route()
                except NoDriverError:
                    for driver in self.drivers:  # Truck needs a driver assigned
                        if driver.truck is None:
                            driver.assign_truck(truck)
                            break
                except NoPackagesError:
                    # assign_packages complexity is O(N^3) time, O(N^2) space
                    self.assign_packages(truck)  # Truck is empty and needs packages
                except (AlreadyInProgressException, TooEarlyError):
                    pass  # do nothing

                # Simulate the truck operations
                # Worst case time complexity O(N^2)
                truck.simulate(self.current_time)

                # Get how far the truck traveled in the last simulation tick
                self._total_distance += truck.distance_last_update
                self._total_time += truck.elapsed_last_update

                # If the truck arrived at the facility, update the total delivery count
                if truck.status == Truck.Status.AT_FACILITY and \
                   truck.distance_traveled > 0 and \
                   truck.last_status_update == truck.last_update:
                    self._total_delivered += truck.delivered_packages
                    time_taken = truck.last_status_update - truck.route_start_time
                    Logger.log(
                        Logger.LogLevel.INFORMATION,
                        f"Truck {truck.id} delivered {truck.delivered_packages} packages in {time_taken} with a distance of {truck.distance_traveled}"
                    )

            # Increment clock
            self._current_time += self._simulation_speed

            # Sleep for a little bit so it doesn't steal CPU, and display is readable
            sleep(0.1)

    def init_ui(self):
        """Initialize the terminal interface. Call this before simulate()."""
        COLS = 90
        MIN_ROWS = 25
        MAX_ROWS = 60

        # Rows are dynamic, based on the number of trucks and packages
        rows = min(max(10 + len(self.trucks) + len(self.packages), MIN_ROWS), MAX_ROWS)
        self._rows = rows
        self._cols = COLS

        # Initialize the terminal screen
        os.system(f"mode con: cols={self._cols} lines={self._rows}")
        self._ui_inited = True
        Logger.instance().level = Logger.LogLevel.NONE  # Disable logging code

    def draw(self):
        """Draws a frame of the interface."""

        if not self._ui_inited:
            return

        lines_printed = 0

        # Clear the screen
        self.move_top_left()
        lines_printed += self.draw_header()

        ## Draw high-level summary, with time
        time_part = f" Time: {self.current_time}"
        summary_part = f"Trucks: {str(len(self.trucks)).ljust(5)} Drivers: {str(len(self.drivers)).ljust(5)} Packages: {str(len(self.packages)).ljust(7)}"
        lines_printed += self.draw_line(
            f"{time_part}{summary_part.rjust(self._cols - 2 - len(time_part))}"
        )
        driving_time_part = f"Cumulative time: {str(self.total_time).rjust(8)}".ljust(
            int((self._cols / 2) - 2))
        driving_distance_part = f"Total distance traveled: {self.total_distance:6.2f}".rjust(
            int((self._cols / 2) - 2))
        lines_printed += self.draw_line(
            f"{driving_time_part}{driving_distance_part}",
            alignment=self._ALIGNMENT_CENTER)
        lines_printed += self.draw_divider(True)

        ## Print truck status
        lines_printed += self.draw_line(
            "Truck Driver   Route Packages Distance Status      Destination")

        for t in self.trucks:
            lines_printed += self.draw_line(f"{t}")

        lines_printed += self.draw_divider(True)

        ## Print package information
        lines_printed += self.draw_line(
            "Package Truck Status    Weight Delivered Deadline Address")

        for p in self.packages:
            lines_printed += self.draw_line(f"{p}")

        # Fill in any remaining space to pad to the full terminal row height
        for _ in range(self._rows - 1 - lines_printed):
            self.draw_line()

        self.draw_bottom()

    def draw_header(self):
        # Draw header section
        title = "UPS Package Router - Daniel"
        self.draw_top()
        self.draw_line(title, alignment=self._ALIGNMENT_CENTER)
        self.draw_divider()
        return 3

    def draw_top(self, thin: bool = False):
        if thin:
            sys.stdout.write(f"┌{'═' * (self._cols - 2)}┐\n")
        else:
            sys.stdout.write(f"╔{'═' * (self._cols - 2)}╗\n")
        return 1

    def draw_bottom(self, thin: bool = False):
        if thin:
            sys.stdout.write(f"└{'═' * (self._cols - 2)}┘\r")
        else:
            sys.stdout.write(f"╚{'═' * (self._cols - 2)}╝\r")
        return 1

    def draw_line(self,
                  text=' ',
                  thin: bool = False,
                  alignment=_ALIGNMENT_LEFT):
        if thin:
            edge = "│"
        else:
            edge = "║"

        if alignment == self._ALIGNMENT_CENTER:
            sys.stdout.write(f"{edge}{text.center(self._cols - 2)}{edge}\n")
        elif alignment == self._ALIGNMENT_LEFT:
            sys.stdout.write(f"{edge}{text.ljust(self._cols - 2)}{edge}\n")
        elif alignment == self._ALIGNMENT_RIGHT:
            sys.stdout.write(f"{edge}{text.rjust(self._cols - 2)}{edge}\n")
        return 1

    def draw_divider(self, thin: bool = False):
        if thin:
            sys.stdout.write(f"╟{'─' * (self._cols - 2)}╢\n")
        else:
            sys.stdout.write(f"╠{'═' * (self._cols - 2)}╣\n")
        return 1

    @classmethod
    def move_top_left(cls):
        """Move cursor to the top-left position."""

        # This method is to allow redrawing without flickering
        if sys.platform.startswith('win'):
            value = 0 + (0 << 16)
            ctypes.windll.kernel32.SetConsoleCursorPosition(
                g_handle, c_ulong(value))
        else:
            os.system(f"clear")
