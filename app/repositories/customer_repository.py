from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.schemas import CustomerRecord, DataRepositoryError


class CustomerRepository:
    """Read-only repository for synthetic customer data."""

    def __init__(self, data_path: Path) -> None:
        self._data_path = data_path
        self._customers_by_email = self._load_customers(data_path)

    def find_by_email(self, email: str) -> CustomerRecord | None:
        """Return an exact case-insensitive email match, if present."""
        return self._customers_by_email.get(email.casefold())

    @staticmethod
    def _load_customers(data_path: Path) -> dict[str, CustomerRecord]:
        try:
            raw_records = json.loads(data_path.read_text(encoding="utf-8"))
            if not isinstance(raw_records, list):
                raise DataRepositoryError("Customer data must contain a JSON array.")
            customers = [CustomerRecord.model_validate(record) for record in raw_records]
        except json.JSONDecodeError as exc:
            raise DataRepositoryError("Customer data is not valid JSON.") from exc
        except ValidationError as exc:
            raise DataRepositoryError("Customer data failed schema validation.") from exc
        except OSError as exc:
            raise DataRepositoryError("Customer data could not be read.") from exc

        customers_by_email: dict[str, CustomerRecord] = {}
        for customer in customers:
            key = str(customer.email).casefold()
            if key in customers_by_email:
                raise DataRepositoryError("Customer data contains duplicate emails.")
            customers_by_email[key] = customer
        return customers_by_email
