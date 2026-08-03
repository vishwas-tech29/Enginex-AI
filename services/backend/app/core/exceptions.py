class EngineXException(Exception):
    """Base for domain exceptions the global handler converts to structured JSON."""

    def __init__(self, message: str, code: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class NotFoundError(EngineXException):
    def __init__(self, resource: str, resource_id: object):
        super().__init__(f"{resource} with ID {resource_id} not found", "NOT_FOUND", 404)


class ForbiddenError(EngineXException):
    def __init__(self, message: str = "You are not authorized to perform this action"):
        super().__init__(message, "FORBIDDEN", 403)


class ConflictError(EngineXException):
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT", 409)


class ValidationError(EngineXException):
    def __init__(self, field: str, message: str):
        super().__init__(f"Validation failed for field '{field}': {message}", "VALIDATION_ERROR", 422)
