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


class ServiceUnavailableError(EngineXException):
    """Raised when a real integration exists but isn't configured in this
    environment (e.g. no Stripe key set) — distinct from
    EngineNotImplementedError, whose computation genuinely doesn't exist yet.
    """

    def __init__(self, message: str):
        super().__init__(message, "SERVICE_UNAVAILABLE", 503)


class EngineNotImplementedError(EngineXException):
    """Raised by endpoints whose geometry/routing/simulation engine doesn't exist yet.

    The API contract (route, auth, schema) is real; the computation behind it
    is future work per docs/architecture/roadmap.md.
    """

    def __init__(self, operation: str):
        super().__init__(
            f"'{operation}' is not implemented yet — the engine behind this "
            "endpoint lands in a later phase (see docs/architecture/roadmap.md)",
            "NOT_IMPLEMENTED",
            501,
        )
