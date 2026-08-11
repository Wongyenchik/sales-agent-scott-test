def assert_sap_was_called(state: dict) -> None:
    sap = state.get("sapRetrieval")
    if not sap or sap.get("called") is not True:
        raise ValueError("Blocked: SAP retrieval must be called before reply generation.")
    if sap.get("status") != "success":
        raise ValueError("Blocked: SAP retrieval did not complete successfully.")


def validate_final_output(state: dict) -> dict:
    sap = state.get("sapRetrieval")

    if not sap:
        return {"valid": False, "reason": "SAP retrieval result is missing."}
    if sap.get("called") is not True:
        return {"valid": False, "reason": "SAP retrieval was not called."}
    if sap.get("status") != "success":
        return {"valid": False, "reason": "SAP retrieval did not return success."}
    if not state.get("draftReply"):
        return {"valid": False, "reason": "Draft reply is missing."}

    return {"valid": True}
