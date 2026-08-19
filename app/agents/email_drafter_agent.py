from __future__ import annotations

from typing import Protocol

from app.agents.azure_openai_client import AzureOpenAIClient
from app.schemas import (
    CustomerValidationResult,
    EmailDraft,
    EmailRequest,
    EmailUnderstandingResult,
    OrderRetrievalResult,
)

EMAIL_DRAFTER_SYSTEM_PROMPT = """You are the Email Drafter Agent for an APAC sales-order workflow.

Create a professional customer-facing email draft using only the supplied
verified customer validation result and order retrieval JSON.

Rules:
1. The order retrieval JSON is the only source of order facts.
2. Never invent or estimate dates, quantities, prices, status values, customer
   names, part numbers, PO numbers, or sales order numbers.
3. Preserve every identifier and numeric value exactly.
4. Do not say that an order was shipped unless the supplied status explicitly
   says 'Shipped'.
5. Do not say that an order is confirmed unless the supplied status explicitly
   supports that statement.
6. If no matching order exists, clearly state that the order could not be
   located from the provided information.
7. Do not expose customer numbers, internal security messages, stack traces,
   API details, or implementation details to the customer.
8. Put validation warnings in the separate warnings array only.
9. Generate the email in the requested language.
10. Do not execute actions, send messages, update orders, or call tools.
11. The result is always a draft requiring human review.
12. Return data matching the supplied structured response schema as JSON."""


class EmailDrafterAgentProtocol(Protocol):
    """Interface for email drafting implementations."""

    async def draft(
        self,
        *,
        request: EmailRequest,
        understanding: EmailUnderstandingResult,
        customer_validation: CustomerValidationResult,
        order_result: OrderRetrievalResult,
        correlation_id: str,
    ) -> EmailDraft:
        """Return a customer-facing draft email."""


class AzureEmailDrafterAgent:
    """Azure OpenAI implementation of the Email Drafter Agent."""

    def __init__(self, client: AzureOpenAIClient) -> None:
        self._client = client

    async def draft(
        self,
        *,
        request: EmailRequest,
        understanding: EmailUnderstandingResult,
        customer_validation: CustomerValidationResult,
        order_result: OrderRetrievalResult,
        correlation_id: str,
    ) -> EmailDraft:
        """Generate a structured email draft with Azure OpenAI."""
        result = await self._client.structured_chat_completion(
            operation_name="email_drafting",
            correlation_id=correlation_id,
            system_prompt=EMAIL_DRAFTER_SYSTEM_PROMPT,
            user_payload={
                "original_request": request.model_dump(mode="json"),
                "understanding": understanding.model_dump(mode="json"),
                "customer_validation": customer_validation.model_dump(mode="json"),
                "order_result": order_result.model_dump(mode="json"),
            },
            response_model=EmailDraft,
        )
        return result.model_copy(update={"requires_human_review": True})


class FakeEmailDrafterAgent:
    """Deterministic drafter for offline local runs and tests."""

    def __init__(self) -> None:
        self.calls = 0

    async def draft(
        self,
        *,
        request: EmailRequest,
        understanding: EmailUnderstandingResult,
        customer_validation: CustomerValidationResult,
        order_result: OrderRetrievalResult,
        correlation_id: str,
    ) -> EmailDraft:
        """Build a draft only from validated customer and order result objects."""
        self.calls += 1
        warnings = [customer_validation.warning] if customer_validation.warning else []
        if understanding.requested_language.startswith("zh"):
            return self._draft_chinese(order_result=order_result, warnings=warnings)
        return self._draft_english(order_result=order_result, warnings=warnings)

    @staticmethod
    def _draft_english(*, order_result: OrderRetrievalResult, warnings: list[str]) -> EmailDraft:
        subject = "Draft: Order status update"
        if not order_result.found:
            body = (
                "Draft for human review.\n\n"
                "Hello,\n\n"
                "We could not locate a matching order from the information provided. "
                "Please review the request and confirm the identifiers before replying.\n\n"
                "Regards,\nSales Support"
            )
            return EmailDraft(
                subject=subject, body=body, warnings=warnings, requires_human_review=True
            )

        sections = [
            "Draft for human review.",
            "",
            "Hello,",
            "",
            "Here is the current order status:",
        ]
        for order in order_result.orders:
            sections.append(
                f"PO {order.purchase_order_number}, sales order {order.sales_order_number}, "
                f"currency {order.currency}:"
            )
            for line in order.lines:
                ship_date = (
                    line.estimated_ship_date.isoformat()
                    if line.estimated_ship_date
                    else "not provided"
                )
                sections.append(
                    "- Line "
                    f"{line.line_number}: customer part {line.customer_part_number}, "
                    f"manufacturer part {line.manufacturer_part_number}, "
                    f"ordered {line.order_quantity}, confirmed {line.confirmed_quantity}, "
                    f"status {line.status}, estimated ship date {ship_date}."
                )
        sections.extend(["", "Regards,", "Sales Support"])
        return EmailDraft(
            subject=subject,
            body="\n".join(sections),
            warnings=warnings,
            requires_human_review=True,
        )

    @staticmethod
    def _draft_chinese(*, order_result: OrderRetrievalResult, warnings: list[str]) -> EmailDraft:
        subject = "草稿：訂單狀態更新"
        if not order_result.found:
            body = (
                "人工審核用草稿。\n\n您好，\n\n"
                "根據您提供的資訊，我們無法找到相符的訂單。請先人工確認識別碼後再回覆。\n\n"
                "此致，\nSales Support"
            )
            return EmailDraft(
                subject=subject, body=body, warnings=warnings, requires_human_review=True
            )

        sections = ["人工審核用草稿。", "", "您好，", "", "以下是目前的訂單狀態："]
        for order in order_result.orders:
            sections.append(
                f"PO {order.purchase_order_number}，銷售訂單 {order.sales_order_number}，"
                f"幣別 {order.currency}："
            )
            for line in order.lines:
                ship_date = (
                    line.estimated_ship_date.isoformat() if line.estimated_ship_date else "未提供"
                )
                sections.append(
                    "- 行項目 "
                    f"{line.line_number}：客戶料號 {line.customer_part_number}，"
                    f"製造商料號 {line.manufacturer_part_number}，"
                    f"訂購數量 {line.order_quantity}，確認數量 {line.confirmed_quantity}，"
                    f"狀態 {line.status}，預計出貨日 {ship_date}。"
                )
        sections.extend(["", "此致，", "Sales Support"])
        return EmailDraft(
            subject=subject,
            body="\n".join(sections),
            warnings=warnings,
            requires_human_review=True,
        )
