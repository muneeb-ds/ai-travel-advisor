"""
Custom exceptions for the application.
"""

class NotFoundError(Exception):
    """Exception raised for not found errors."""
    def __init__(self, message: str = "Not found"):
        self.message = message
        super().__init__(self.message)

class ForbiddenError(Exception):
    """Exception raised for forbidden errors."""
    def __init__(self, message: str = "Forbidden"):
        self.message = message
        super().__init__(self.message)

class BadRequestError(Exception):
    """Exception raised for bad request errors."""
    def __init__(self, message: str = "Bad request"):
        self.message = message
        super().__init__(self.message)