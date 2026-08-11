import random
import time

from app.config import SAP_API_MODE
from app.drafts import generate_clarification_draft, generate_reply_from_sap_result, generate_sap_failure_draft
from app.extractor import extract_email_intent_and_parameters
from app.mail import normalize_email
from app.sap_tool import sap_retrieval_tool
from app.validators import assert_sap_was_called, validate_final_output


def _build_result(state: dict, status: str) -> dict:
    return {
        "status": status,
        "requestId": state["requestId"],
        "detectedIntent": state.get("detectedIntent"),
        "extractedParameters": state.get("extractedParameters"),
        "missingParameters": state.get("missingParameters"),
        "sapRetrieval": state.get("sapRetrieval"),
        "draftReply": state.get("draftReply"),
        "warnings": [],
    }


def _random_id() -> str:
    return f"{int(time.time() * 1000)}-{random.randrange(16**8):08x}"


def generate_reply_workflow(input_payload: dict) -> dict:
    state = {
        "requestId": input_payload.get("requestId") or _random_id(),
        "userId": input_payload.get("userId") or "web-user",
        "email": normalize_email(input_payload),
        "errors": [],
    }

    extraction = extract_email_intent_and_parameters(state["email"])
    state["detectedIntent"] = extraction["intent"]
    state["extractedParameters"] = extraction["parameters"]
    state["missingParameters"] = extraction["missingParameters"]

    if len(state["missingParameters"]) > 0:
        state["sapRetrieval"] = {
            "called": False,
            "status": "missing_parameters",
            "source": "mock-sap-api" if SAP_API_MODE == "mock" else "company-sap-api",
            "correlationId": state["requestId"],
        }
        state["draftReply"] = generate_clarification_draft(state["missingParameters"])
        return _build_result(state, "needs_more_information")

    state["sapRetrieval"] = sap_retrieval_tool.call(
        {
            "intent": state["detectedIntent"],
            "parameters": state["extractedParameters"],
            "requestId": state["requestId"],
            "userId": state["userId"],
        }
    )

    if state["sapRetrieval"].get("called") is not True:
        raise ValueError("SAP retrieval was not called. Reply generation blocked.")

    if state["sapRetrieval"].get("status") != "success":
        state["draftReply"] = generate_sap_failure_draft()
        return _build_result(state, state["sapRetrieval"].get("status", "api_error"))

    assert_sap_was_called(state)

    state["draftReply"] = generate_reply_from_sap_result(state["sapRetrieval"], state["email"])

    validation = validate_final_output(state)
    if validation.get("valid") is not True:
        raise ValueError(f"Final output validation failed: {validation.get('reason')}")

    return _build_result(state, "success")
