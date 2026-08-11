from app.sap_adapter import retrieve_from_sap_adapter


class SapRetrievalTool:
    name = "sap_retrieve_information"

    @staticmethod
    def call(input_payload: dict) -> dict:
        return retrieve_from_sap_adapter(input_payload.get("parameters") or {}, input_payload.get("requestId") or "")


sap_retrieval_tool = SapRetrievalTool()
