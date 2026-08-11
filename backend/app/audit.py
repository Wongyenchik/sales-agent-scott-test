import json
from datetime import datetime, timezone


def audit_log(event: dict) -> None:
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **event}
    print(json.dumps(payload))
