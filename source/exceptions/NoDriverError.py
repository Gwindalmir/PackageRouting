from .Error import Error


class NoDriverError(Error):
    """Truck tried to move without a driver."""
