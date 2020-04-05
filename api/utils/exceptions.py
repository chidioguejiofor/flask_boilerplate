class ResponseException(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code


class DataConflictException(Exception):
    """This exception is raised when a unique constraint is not met"""
    def __init__(self, message):
        self.message = message
