from __future__ import annotations

import logging
from uuid import UUID, uuid4

from app.agents.email_drafter_agent import EmailDrafterAgentProtocol
from app.agents.email_understanding_agent import EmailUnderstandingAgentProtocol
from app.logging_config import timed_operation
from app.schemas import (
    ApplicationError,
    EmailRequest,
    OrderRetrievalResult,
    WorkflowResult,
    WorkflowStatus,
)
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)


class SalesAgentOrchestrator:
    """Deterministic APAC sales-order workflow orchestrator."""

    def __init__(
        self,
        *,
        understanding_agent: EmailUnderstandingAgentProtocol,
        customer_service: CustomerService,
        order_service: OrderService,
        drafter_agent: EmailDrafterAgentProtocol,
    ) -> None:
        self._understanding_agent = understanding_agent
        self._customer_service = customer_service
        self._order_service = order_service
        self._drafter_agent = drafter_agent

    async def run(self, request: EmailRequest) -> WorkflowResult:
        """Run the order-status workflow and return a safe structured result."""
        correlation_id = uuid4()
        try:
            with timed_operation(logger, correlation_id=str(correlation_id), step="understanding"):
                understanding = await self._understanding_agent.understand(
                    request,
                    correlation_id=str(correlation_id),
                )
            logger.info(
                "correlation_id=%s intent=%s po_count=%s",
                correlation_id,
                understanding.intent,
                len(understanding.purchase_order_numbers),
            )

            if understanding.intent != "order_status":
                return WorkflowResult(
                    status=WorkflowStatus.NEEDS_REVIEW,
                    understanding=understanding,
                    customer_validation=None,
                    order_result=None,
                    draft=None,
                    errors=["Only order_status requests are supported by this workflow."],
                    correlation_id=correlation_id,
                )

            if (
                "purchase_order_numbers" in understanding.missing_fields
                or not understanding.purchase_order_numbers
            ):
                return WorkflowResult(
                    status=WorkflowStatus.NEEDS_REVIEW,
                    understanding=understanding,
                    customer_validation=None,
                    order_result=None,
                    draft=None,
                    errors=["A purchase order number is required for order status lookup."],
                    correlation_id=correlation_id,
                )

            with timed_operation(
                logger, correlation_id=str(correlation_id), step="customer_validation"
            ):
                customer_validation = await self._customer_service.validate_sender(
                    str(request.sender_email)
                )
            logger.info(
                "correlation_id=%s known_customer=%s",
                correlation_id,
                customer_validation.is_known_customer,
            )

            if not customer_validation.is_known_customer:
                return WorkflowResult(
                    status=WorkflowStatus.NEEDS_REVIEW,
                    understanding=understanding,
                    customer_validation=customer_validation,
                    order_result=OrderRetrievalResult(found=False, orders=[], error=None),
                    draft=None,
                    errors=["The sender could not be validated for automatic order lookup."],
                    correlation_id=correlation_id,
                )

            with timed_operation(
                logger, correlation_id=str(correlation_id), step="order_retrieval"
            ):
                order_result = await self._order_service.retrieve_orders(
                    customer_number=customer_validation.customer_number,
                    purchase_order_numbers=understanding.purchase_order_numbers,
                )
            logger.info(
                "correlation_id=%s matching_order_count=%s",
                correlation_id,
                len(order_result.orders),
            )

            with timed_operation(logger, correlation_id=str(correlation_id), step="drafting"):
                draft = await self._drafter_agent.draft(
                    request=request,
                    understanding=understanding,
                    customer_validation=customer_validation,
                    order_result=order_result,
                    correlation_id=str(correlation_id),
                )
            draft = draft.model_copy(update={"requires_human_review": True})
            return WorkflowResult(
                status=WorkflowStatus.DRAFT_READY,
                understanding=understanding,
                customer_validation=customer_validation,
                order_result=order_result,
                draft=draft,
                errors=[],
                correlation_id=correlation_id,
            )
        except ApplicationError as exc:
            logger.exception("correlation_id=%s workflow_application_error", correlation_id)
            return _failed_result(correlation_id=correlation_id, message=str(exc))
        except Exception:
            logger.exception("correlation_id=%s workflow_unexpected_error", correlation_id)
            return _failed_result(
                correlation_id=correlation_id,
                message=(
                    "The workflow failed. Provide the correlation ID to support for investigation."
                ),
            )


def _failed_result(*, correlation_id: UUID, message: str) -> WorkflowResult:
    return WorkflowResult(
        status=WorkflowStatus.FAILED,
        understanding=None,
        customer_validation=None,
        order_result=None,
        draft=None,
        errors=[message],
        correlation_id=correlation_id,
    )


def build_orchestrator(
    *,
    understanding_agent: EmailUnderstandingAgentProtocol,
    customer_service: CustomerService,
    order_service: OrderService,
    drafter_agent: EmailDrafterAgentProtocol,
) -> SalesAgentOrchestrator:
    """Create an orchestrator from injected dependencies."""
    return SalesAgentOrchestrator(
        understanding_agent=understanding_agent,
        customer_service=customer_service,
        order_service=order_service,
        drafter_agent=drafter_agent,
    )
