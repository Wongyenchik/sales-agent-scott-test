import re

ORDER_NUMBER_RE = re.compile(r"\b(45\d{8})\b")
CUSTOMER_REFERENCE_RE = re.compile(r"\bPO-[A-Z0-9-]{3,}\b", re.IGNORECASE)


def extract_email_intent_and_parameters(email: dict) -> dict:
    full_text = f"{email.get('subject', '')}\n{email.get('bodyText', '')}"
    lower = full_text.lower()

    if any(keyword in lower for keyword in ["order", "delivery", "shipment", "status"]):
        intent = "order_status_lookup"
    else:
        intent = "order_status_lookup"

    order_match = ORDER_NUMBER_RE.search(full_text)
    customer_ref_match = CUSTOMER_REFERENCE_RE.search(full_text)

    parameters = {}
    if order_match:
        parameters["purchaseOrderNumber"] = order_match.group(1)
    if customer_ref_match:
        parameters["customerReference"] = customer_ref_match.group(0).upper()

    missing = []
    if "purchaseOrderNumber" not in parameters and "customerReference" not in parameters:
        missing.append("purchaseOrderNumber_or_customerReference")

    return {"intent": intent, "parameters": parameters, "missingParameters": missing}
