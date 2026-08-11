# Mock SAP API

Local mock API for order lookups while the real company SAP API is not available.

## Start

```bash
cd <repo-root>\mock-api
py server.py
```

Optional custom port:

```bash
set MOCK_SAP_PORT=8080
py server.py
```

If `py` is unavailable, use `python`.

## Endpoints

- `GET /health`
- `GET /api/mock-sap/orders/{orderNumber}`
- `GET /api/mock-sap/orders?customerReference={customerReference}`

## Example calls

```bash
curl http://localhost:7071/api/mock-sap/orders/4500012345
curl "http://localhost:7071/api/mock-sap/orders?customerReference=PO-77822"
```

## Failure simulation

Query string mode:

```bash
curl "http://localhost:7071/api/mock-sap/orders/4500012345?scenario=unauthorized"
curl "http://localhost:7071/api/mock-sap/orders/4500012345?scenario=api_error"
curl "http://localhost:7071/api/mock-sap/orders/4500012345?scenario=timeout"
```

Header mode:

```bash
curl -H "x-mock-sap-scenario: unauthorized" http://localhost:7071/api/mock-sap/orders/4500012345
```

Forced not-found and api-error test values:

- `4500099998` -> not found
- `4500099999` -> api_error
