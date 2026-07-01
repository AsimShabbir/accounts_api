class ApplicationError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(ApplicationError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class ValidationError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422)


class ConflictError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


class UnauthorizedError(ApplicationError):
    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message, status_code=401)


class ForbiddenError(ApplicationError):
    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message, status_code=403)
