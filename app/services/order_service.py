from __future__ import annotations

from app.repositories.order_repository import OrderRepository
from app.schemas import OrderRetrievalResult

NO_MATCHING_ORDER_MESSAGE = "No matching order was found for the authorised customer."


class OrderService:
    """Retrieve only orders owned by an authorised customer."""

    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    async def retrieve_orders(
        self,
        *,
        customer_number: str | None,
        purchase_order_numbers: list[str],
    ) -> OrderRetrievalResult:
        """Return matching orders for an authorised customer and supplied PO numbers."""
        if not customer_number:
            return OrderRetrievalResult(found=False, orders=[], error=NO_MATCHING_ORDER_MESSAGE)
        if not purchase_order_numbers:
            return OrderRetrievalResult(
                found=False,
                orders=[],
                error="A purchase order number is required for order status lookup.",
            )

        matched_orders = []
        seen_keys: set[tuple[str, str]] = set()
        for purchase_order_number in purchase_order_numbers:
            for order in self._repository.find_by_customer_and_po(
                customer_number=customer_number,
                purchase_order_number=purchase_order_number,
            ):
                key = (order.customer_number, order.purchase_order_number)
                if key not in seen_keys:
                    matched_orders.append(order)
                    seen_keys.add(key)

        if not matched_orders:
            return OrderRetrievalResult(found=False, orders=[], error=NO_MATCHING_ORDER_MESSAGE)
        return OrderRetrievalResult(found=True, orders=matched_orders, error=None)
