from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.agents.azure_openai_client import AzureOpenAIClient
from app.agents.email_drafter_agent import (
    AzureEmailDrafterAgent,
    EmailDrafterAgentProtocol,
    FakeEmailDrafterAgent,
)
from app.agents.email_understanding_agent import (
    AzureEmailUnderstandingAgent,
    EmailUnderstandingAgentProtocol,
    FakeEmailUnderstandingAgent,
)
from app.config import Settings, get_settings
from app.orchestrator import SalesAgentOrchestrator, build_orchestrator
from app.repositories.customer_repository import CustomerRepository
from app.repositories.order_repository import OrderRepository
from app.schemas import EmailRequest, WorkflowResult
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Return a minimal health response without configuration details."""
    return {"status": "healthy"}


def get_orchestrator(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SalesAgentOrchestrator:
    """Build request-scoped orchestrator dependencies."""
    customer_repository = CustomerRepository(settings.data_dir / "customers.json")
    order_repository = OrderRepository(settings.data_dir / "orders.json")
    customer_service = CustomerService(customer_repository)
    order_service = OrderService(order_repository)
    understanding_agent: EmailUnderstandingAgentProtocol
    drafter_agent: EmailDrafterAgentProtocol

    if settings.llm_enabled:
        azure_client = AzureOpenAIClient(settings)
        understanding_agent = AzureEmailUnderstandingAgent(azure_client)
        drafter_agent = AzureEmailDrafterAgent(azure_client)
    else:
        understanding_agent = FakeEmailUnderstandingAgent()
        drafter_agent = FakeEmailDrafterAgent()

    return build_orchestrator(
        understanding_agent=understanding_agent,
        customer_service=customer_service,
        order_service=order_service,
        drafter_agent=drafter_agent,
    )


@router.post("/api/v1/run", response_model=WorkflowResult)
async def run(
    request: EmailRequest,
    response: Response,
    orchestrator: Annotated[SalesAgentOrchestrator, Depends(get_orchestrator)],
) -> WorkflowResult:
    """Run the APAC sales agent workflow."""
    result = await orchestrator.run(request)
    response.headers["X-Correlation-ID"] = str(result.correlation_id)
    return result
