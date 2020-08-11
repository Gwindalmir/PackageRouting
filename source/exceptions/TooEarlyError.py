from .Error import Error


class TooEarlyError(Error):
    """Truck cannot leave before its scheduled start time."""
