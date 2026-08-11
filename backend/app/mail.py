def normalize_email(input_payload: dict) -> dict:
    sender = input_payload.get("sender") or {}
    return {
        "messageId": str(input_payload.get("messageId") or "").strip(),
        "subject": str(input_payload.get("subject") or "").strip(),
        "sender": {
            "name": str(sender.get("name") or "").strip(),
            "email": str(sender.get("email") or "").strip().lower(),
        },
        "recipients": input_payload.get("recipients") if isinstance(input_payload.get("recipients"), list) else [],
        "bodyText": str(input_payload.get("bodyText") or "").replace("\r\n", "\n").strip(),
        "bodyHtml": str(input_payload.get("bodyHtml") or "").strip(),
        "conversationId": str(input_payload.get("conversationId") or "").strip(),
    }
