from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from app.core.logging import get_logger

logger = get_logger(__name__)
templates = Jinja2Templates(directory="app/templates")


async def http_exception_handler(request: Request, exc: HTTPException) -> HTMLResponse | JSONResponse:
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        template = "errors/404.html" if exc.status_code == HTTP_404_NOT_FOUND else "errors/500.html"
        return templates.TemplateResponse(request, template, status_code=exc.status_code)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def validation_exception_handler(request: Request, exc) -> JSONResponse:
    from fastapi.exceptions import RequestValidationError
    if isinstance(exc, RequestValidationError):
        errors = exc.errors()
        safe_errors = []
        for err in errors:
            ctx = err.get("ctx")
            if ctx and isinstance(ctx, dict):
                err["ctx"] = {k: str(v) for k, v in ctx.items()}
            safe_errors.append(err)
        return JSONResponse(status_code=422, content={"detail": safe_errors})
    return JSONResponse(status_code=422, content={"detail": str(exc)})


async def unhandled_exception_handler(request: Request, exc: Exception) -> HTMLResponse | JSONResponse:
    logger.exception("Unhandled exception", extra={"path": str(request.url.path)})
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return templates.TemplateResponse(request, "errors/500.html", status_code=500)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
