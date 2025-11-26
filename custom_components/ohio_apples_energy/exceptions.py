"""Exceptions for Ohio Apples Energy."""

class OhioApplesEnergyError(Exception):
    """Base class for other exceptions."""
    pass

class CannotConnect(OhioApplesEnergyError):
    """Raised when there is a connection error."""
    pass

class NoDataAvailable(OhioApplesEnergyError):
    """Raised when no data is returned from the source."""
    pass
