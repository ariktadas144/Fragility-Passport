"""Domain exceptions, translated to HTTP responses in main.py's exception handlers."""


class DomainError(Exception):
    """Base class for expected, user-facing errors."""

    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    status_code = 404


class ValidationFailedError(DomainError):
    """Raised when inbound ML/VLM detection data fails a business-rule check
    that Pydantic's field-level validation can't express (e.g. a timestamp
    outside the source video's duration)."""

    status_code = 422


class ConflictError(DomainError):
    status_code = 409
