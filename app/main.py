from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import get_settings
from app.logging_config import configure_logging
from app.schemas import ApplicationError, WorkflowResult, WorkflowStatus

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title="APAC Sales Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.streamlit_origin, settings.outlook_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Correlation-ID"],
)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return safe validation failures with a correlation ID."""
    correlation_id = uuid4()
    result = WorkflowResult(
        status=WorkflowStatus.FAILED,
        understanding=None,
        customer_validation=None,
        order_result=None,
        draft=None,
        errors=["The request payload failed validation."],
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=422,
        content=result.model_dump(mode="json"),
        headers={"X-Correlation-ID": str(correlation_id)},
    )


@app.exception_handler(ApplicationError)
async def application_exception_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Return safe application failures with a correlation ID."""
    correlation_id = uuid4()
    result = WorkflowResult(
        status=WorkflowStatus.FAILED,
        understanding=None,
        customer_validation=None,
        order_result=None,
        draft=None,
        errors=["The application could not complete the request safely."],
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=500,
        content=result.model_dump(mode="json"),
        headers={"X-Correlation-ID": str(correlation_id)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return safe unexpected failures with a correlation ID."""
    correlation_id = uuid4()
    result = WorkflowResult(
        status=WorkflowStatus.FAILED,
        understanding=None,
        customer_validation=None,
        order_result=None,
        draft=None,
        errors=["The application encountered an unexpected error."],
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=500,
        content=result.model_dump(mode="json"),
        headers={"X-Correlation-ID": str(correlation_id)},
    )
