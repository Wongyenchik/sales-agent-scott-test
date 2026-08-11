from app.audit import audit_log
from app.workflow import generate_reply_workflow


def _hash_lite(value: str) -> str:
    text = str(value or "")
    hash_value = 0
    for ch in text:
        hash_value = ((hash_value * 31) + ord(ch)) & 0xFFFFFFFF
    return format(hash_value, "x")


def _validate_payload(payload: dict) -> str | None:
    if not isinstance(payload, dict):
        return "Request body must be a JSON object"
    if not payload.get("subject") and not payload.get("bodyText"):
        return "At least one of subject or bodyText is required"
    return None


def handle_generate_reply(payload: dict) -> tuple[int, dict]:
    validation_error = _validate_payload(payload)
    if validation_error:
        return 400, {"status": "bad_request", "error": validation_error}

    result = generate_reply_workflow(payload)

    audit_log(
        {
            "requestId": result.get("requestId"),
            "userIdHash": _hash_lite(payload.get("userId") or "web-user"),
            "messageIdHash": _hash_lite(payload.get("messageId") or ""),
            "intent": result.get("detectedIntent"),
            "sapToolCalled": (result.get("sapRetrieval") or {}).get("called") is True,
            "sapStatus": (result.get("sapRetrieval") or {}).get("status"),
            "sapCorrelationId": (result.get("sapRetrieval") or {}).get("correlationId"),
            "replyGenerated": bool(result.get("draftReply")),
        }
    )

    return 200, result
