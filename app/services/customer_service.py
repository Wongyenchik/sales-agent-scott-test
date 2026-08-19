from __future__ import annotations

from app.repositories.customer_repository import CustomerRepository
from app.schemas import CustomerValidationResult

UNAUTHORISED_WARNING = "The sender is not linked to an active customer account."


class CustomerService:
    """Validate senders against active synthetic customers."""

    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    async def validate_sender(self, sender_email: str) -> CustomerValidationResult:
        """Return active customer metadata for an exact sender match."""
        customer = self._repository.find_by_email(sender_email)
        if customer is None or not customer.is_active:
            return CustomerValidationResult(
                is_known_customer=False,
                customer_number=None,
                customer_name=None,
                warning=UNAUTHORISED_WARNING,
            )
        return CustomerValidationResult(
            is_known_customer=True,
            customer_number=customer.customer_number,
            customer_name=customer.customer_name,
            warning=None,
        )
