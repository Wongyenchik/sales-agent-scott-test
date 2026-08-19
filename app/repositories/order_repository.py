from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.schemas import DataRepositoryError, OrderRecord


class OrderRepository:
    """Read-only repository for synthetic order data."""

    def __init__(self, data_path: Path) -> None:
        self._data_path = data_path
        self._orders = self._load_orders(data_path)

    def find_by_customer_and_po(
        self,
        *,
        customer_number: str,
        purchase_order_number: str,
    ) -> list[OrderRecord]:
        """Return orders matching exact customer number and case-insensitive PO number."""
        normalized_po = purchase_order_number.casefold()
        return [
            order
            for order in self._orders
            if order.customer_number == customer_number
            and order.purchase_order_number.casefold() == normalized_po
        ]

    @staticmethod
    def _load_orders(data_path: Path) -> list[OrderRecord]:
        try:
            raw_records = json.loads(data_path.read_text(encoding="utf-8"))
            if not isinstance(raw_records, list):
                raise DataRepositoryError("Order data must contain a JSON array.")
            return [OrderRecord.model_validate(record) for record in raw_records]
        except json.JSONDecodeError as exc:
            raise DataRepositoryError("Order data is not valid JSON.") from exc
        except ValidationError as exc:
            raise DataRepositoryError("Order data failed schema validation.") from exc
        except OSError as exc:
            raise DataRepositoryError("Order data could not be read.") from exc
