from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, NonNegativeInt


class ApplicationError(Exception):
    """Base class for controlled application errors."""


class ConfigurationError(ApplicationError):
    """Raised when local configuration is incomplete or invalid."""


class LLMProviderError(ApplicationError):
    """Raised when Azure OpenAI cannot complete a model request."""


class LLMResponseValidationError(ApplicationError):
    """Raised when a model response fails structured validation."""


class DataRepositoryError(ApplicationError):
    """Raised when local data cannot be loaded or validated."""


class WorkflowValidationError(ApplicationError):
    """Raised when a workflow cannot continue due to controlled validation failure."""


class StrictBaseModel(BaseModel):
    """Base model that rejects unknown fields."""

    model_config = ConfigDict(extra="forbid")


class Intent(StrEnum):
    ORDER_STATUS = "order_status"
    ORDER_CONFIRMATION = "order_confirmation"
    UNKNOWN = "unknown"


class WorkflowStatus(StrEnum):
    DRAFT_READY = "draft_ready"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"
    FAILED = "failed"


class EmailRequest(StrictBaseModel):
    sender_email: EmailStr
    subject: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1, max_length=10_000)


class EmailUnderstandingResult(StrictBaseModel):
    intent: Intent
    sender_email: EmailStr
    purchase_order_numbers: list[str] = Field(default_factory=list)
    sales_order_numbers: list[str] = Field(default_factory=list)
    requested_language: str = Field(min_length=2, max_length=12)
    confidence: float = Field(ge=0.0, le=1.0)
    missing_fields: list[str] = Field(default_factory=list)


class CustomerRecord(StrictBaseModel):
    email: EmailStr
    customer_number: str
    customer_name: str
    is_active: bool


class CustomerValidationResult(StrictBaseModel):
    is_known_customer: bool
    customer_number: str | None
    customer_name: str | None
    warning: str | None


class OrderLine(StrictBaseModel):
    line_number: NonNegativeInt
    customer_part_number: str
    manufacturer_part_number: str
    order_quantity: NonNegativeInt
    confirmed_quantity: NonNegativeInt
    status: str
    estimated_ship_date: date | None


class OrderRecord(StrictBaseModel):
    customer_number: str
    purchase_order_number: str
    sales_order_number: str
    currency: str
    lines: list[OrderLine]


class OrderRetrievalResult(StrictBaseModel):
    found: bool
    orders: list[OrderRecord] = Field(default_factory=list)
    error: str | None


class EmailDraft(StrictBaseModel):
    subject: str
    body: str
    warnings: list[str] = Field(default_factory=list)
    requires_human_review: bool = True


class WorkflowResult(StrictBaseModel):
    status: WorkflowStatus
    understanding: EmailUnderstandingResult | None
    customer_validation: CustomerValidationResult | None
    order_result: OrderRetrievalResult | None
    draft: EmailDraft | None
    errors: list[str] = Field(default_factory=list)
    correlation_id: UUID
