

class OperationStatus:
    """Refers to the construction of an status of an operation once it is invoked
    """

    def __init__(self, success: bool, message: str, status_code: int, error_type: str = None):
        self.success = success
        self.message = message
        self.status_code = status_code

        self.error_type = error_type

    def __str__(self):
        return f"Success: {self.success}\tMessage: {self.message}\tStatusCode: {self.status_code}"
