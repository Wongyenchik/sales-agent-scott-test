from __future__ import annotations

import json
import logging
import time
from typing import TypeVar

from openai import APIError, APITimeoutError, AsyncAzureOpenAI
from pydantic import BaseModel, ValidationError

from app.config import Settings
from app.schemas import LLMProviderError, LLMResponseValidationError

logger = logging.getLogger(__name__)
TModel = TypeVar("TModel", bound=BaseModel)


class AzureOpenAIClient:
    """Lazy Azure OpenAI chat client that returns validated Pydantic models."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncAzureOpenAI | None = None

    @property
    def client(self) -> AsyncAzureOpenAI:
        """Initialise the Azure OpenAI client on first use."""
        if self._client is None:
            self._client = AsyncAzureOpenAI(
                azure_endpoint=self._settings.azure_openai_endpoint or "",
                api_key=self._settings.azure_openai_api_key or "",
                api_version=self._settings.azure_openai_api_version or "",
                timeout=self._settings.request_timeout_seconds,
                max_retries=1,
            )
        return self._client

    async def structured_chat_completion(
        self,
        *,
        operation_name: str,
        correlation_id: str,
        system_prompt: str,
        user_payload: dict[str, object],
        response_model: type[TModel],
    ) -> TModel:
        """Request JSON output from Azure OpenAI and validate it strictly."""
        start = time.perf_counter()
        success = False
        try:
            schema = response_model.model_json_schema()
            response = await self.client.chat.completions.create(
                model=self._settings.azure_openai_chat_deployment or "",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "response_schema": schema,
                                "input": user_payload,
                            },
                            default=str,
                        ),
                    },
                ],
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMResponseValidationError("Model response was empty.")
            parsed = json.loads(content)
            result = response_model.model_validate(parsed)
            success = True
            return result
        except (APIError, APITimeoutError) as exc:
            raise LLMProviderError(
                "The language model provider failed to process the request."
            ) from exc
        except (IndexError, json.JSONDecodeError, ValidationError) as exc:
            raise LLMResponseValidationError(
                "The language model returned malformed structured data."
            ) from exc
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "operation=%s correlation_id=%s success=%s duration_ms=%s",
                operation_name,
                correlation_id,
                success,
                duration_ms,
            )
