from fastapi import HTTPException


class ServiceError(Exception, HTTPException):
    code = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(ServiceError):
    code = 404


class ValidationError(ServiceError):
    code = 422


class ForbiddenError(ServiceError):
    code = 403


class NotImplementedError(ServiceError):
    code = 501


class OrgStructureClientError(RuntimeError):
    code = 503


class PdfRenderError(RuntimeError):
    code = 503
