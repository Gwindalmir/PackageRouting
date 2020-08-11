################################
# UPS Package Routing Program  #
# Daniel                       #
################################

from datetime import time
from os import path

from entities.Location import Location
from structures.RuntimeState import RuntimeState
from utilities.Logger import Logger


def main():
    drivers = ["Alice", "Fred"]
    trucks = 3
    truck_start_time = time(hour=8, minute=0)

    runtime_state = RuntimeState(simulation_speed_seconds=30)

    # Load the data (time complexity of O(N^2), space of O(N^2)
    runtime_state.load_destinations(get_file("locations.csv"))
    runtime_state.load_packages(get_file("packages.csv"))

    # Add two drivers
    runtime_state.add_drivers(drivers)

    # Add three trucks
    runtime_state.add_trucks(trucks, truck_start_time)

    # Initialize the terminal interface (disables Logger class)
    runtime_state.init_ui()

    # Add a correction for package 9 at 10:20am
    runtime_state.add_package_correction(9, time(hour=10, minute=20),
                                         Location('410 S State St', 84111))

    # Run simulation. This doesn't return until end of day.
    # Worst case time complexity is O(N^3)
    # Worst case space complexity is O(N^2)
    runtime_state.simulate()

    # Once finished, print results
    Logger.log(
        Logger.LogLevel.INFORMATION,
        f"\n{runtime_state.packages_delivered} packages were delivered in a combined time of {runtime_state.total_time} for a total distance of {runtime_state.total_distance}"
    )

def get_file(filename):
    if path.exists(filename):
        return filename
    
    newpath = path.join("..", filename)

    if path.exists(newpath):
        return newpath

    newpath = path.join("..", "data", filename)

    if path.exists(newpath):
        return newpath

    Logger.log(Logger.LogLevel.ERROR, f"Could not find filename: {filename}")
    return filename

# Start main program
main()
