from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(log_level: str) -> None:
    """Configure standard Python logging for the application."""
    logging.basicConfig(level=log_level.upper(), format=LOG_FORMAT, force=True)


def mask_email(email: str) -> str:
    """Mask an email address for safe logs."""
    local, separator, domain = email.partition("@")
    if not separator:
        return "***"
    first = local[:1] if local else "*"
    return f"{first}***@{domain}"


@contextmanager
def timed_operation(
    logger: logging.Logger,
    *,
    correlation_id: str,
    step: str,
    **fields: object,
) -> Iterator[None]:
    """Log operation duration without sensitive payloads."""
    start = time.perf_counter()
    logger.info("step=%s correlation_id=%s status=started %s", step, correlation_id, fields)
    try:
        yield
    except Exception:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.exception(
            "step=%s correlation_id=%s status=failed duration_ms=%s %s",
            step,
            correlation_id,
            duration_ms,
            fields,
        )
        raise
    duration_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "step=%s correlation_id=%s status=succeeded duration_ms=%s %s",
        step,
        correlation_id,
        duration_ms,
        fields,
    )
