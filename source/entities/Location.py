import sys
from utilities.Logger import Logger
sys.path.append("..")


class Location:
    """Delivery location"""

    _INITIAL_VALUE = 5432
    _MULTIPLIER = 11

    def __init__(self, address: str, zip_code: int = None):
        """Creates a new location

        Params:
        address - street address with optional zip code in format "Address (zip)"
        zip - optional, separate zip code"""

        if zip_code is not None:
            self.address = address
            self.zip = zip_code
        else:
            split = address.rpartition('(')
            if split[0] is '':
                # No zip code, could be HUB
                # Just set the address to the entire string, and set ZIP to 0
                self.address = split[2]
                self.zip = int(0)
            else:
                self.address = split[0].strip()
                self.zip = split[2][0:-1]
        self.__hash = None

    def __str__(self):
        return f"{self.address} ({self.zip})"

    def __repr__(self):
        return f"{self.address} ({self.zip})"

    def __hash__(self):
        """Generate a hash that's unique for a given address and zip combination."""
        # This hash is based on the address and zip, and will return the same hash
        # if two locations have the same address and zip

        # Consider this immutable
        # Cache the hash, so we only need to do this once per object
        # Simple character hash
        if self.__hash is None:
            hash_ = self._INITIAL_VALUE

            for c in self.address:
                hash_ = (hash_ * self._MULTIPLIER) + ord(c)

            for c in str(self.zip):
                hash_ = (hash_ * self._MULTIPLIER) + ord(c)
            self.__hash = hash_
        return self.__hash

    def __eq__(self, other):
        """Two location objects are the same if they have the same address and zip code."""
        # This will compare against a Location class, or a string of the same value
        if isinstance(other, str):
            # Convert string to Location, for comparison
            return self == Location(other)
        if isinstance(other, Location):
            Logger.log(Logger.LogLevel.DEBUG,
                       f"Hash comparing: {hash(other)} to {hash(self)}")
            return hash(other) == hash(self)

        raise TypeError
