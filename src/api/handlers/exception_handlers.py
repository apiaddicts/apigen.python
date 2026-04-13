import logging
from fastapi.responses import JSONResponse


def custom_exception_handler(_, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "errors": [
                {
                    "code": exc.custom_code,
                    "msg": exc.msg
                }
            ]
        }
    )


def validation_exception_handler(request, exc):
    logging.warning(exc, request)
    errors = exc.errors()
    modified_errors = []
    for error in errors:
        error.pop('url', None)
        error.pop('input', None)
        error.pop('type', None)
        modified_errors.append(error)
    return JSONResponse(
        status_code=400,
        content={
            "errors": modified_errors
        },
    )
