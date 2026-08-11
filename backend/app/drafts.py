def generate_clarification_draft(missing_parameters: list[str]) -> str:
    missing_text = ", ".join(missing_parameters).replace("_", " ")
    return "\n".join(
        [
            "Hi,",
            "",
            f"Could you please share the {missing_text} so I can check the latest SAP status?",
            "",
            "Best regards,",
        ]
    )


def generate_sap_failure_draft() -> str:
    return "\n".join(
        [
            "Hi,",
            "",
            "I tried checking the latest information, but I could not retrieve the SAP details at the moment.",
            "Could you please confirm the reference number, or I can follow up once the system information is available.",
            "",
            "Best regards,",
        ]
    )


def generate_reply_from_sap_result(sap_result: dict, email: dict) -> str:
    order = sap_result.get("data") or {}
    customer_name = (email.get("sender") or {}).get("name") or "there"
    order_label = order.get("orderNumber") or order.get("customerReference") or "your order"
    order_status = order.get("orderStatus") or "currently unavailable"
    estimated_delivery = order.get("estimatedDeliveryDate") or "not yet confirmed"

    lines = [
        f"Hi {customer_name},",
        "",
        f"I checked SAP for {order_label}.",
        f"Current status: {order_status}.",
        f"Estimated delivery date: {estimated_delivery}.",
    ]

    if order.get("lastUpdated"):
        lines.append(f"Last SAP update: {order['lastUpdated']}.")

    lines.extend(["", "Best regards,"])
    return "\n".join(lines)
