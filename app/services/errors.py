"""Domain errors raised by the service layer and rendered as JSON by the API.

Keeping these here (instead of in the routes) means services do not depend
on the HTTP layer; the API blueprint registers the handlers that map them
to the ``{"error": "..."}`` envelope (see app/routes/api/errors.py).
"""


class ApiError(Exception):
    """Base error: a request problem with a status code and message."""

    status_code = 400

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class BadRequest(ApiError):
    status_code = 400


class NotFound(ApiError):
    status_code = 404


class Conflict(ApiError):
    status_code = 409
