from __future__ import annotations
import asyncio
from typing import Any, Callable
import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter
from agent.utils.logger import get_logger

log = get_logger(__name__)
_RETRYABLE = (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError, ConnectionError)


async def with_retry(fn: Callable[[], Any], max_attempts: int = 3, min_wait: float = 0.5, max_wait: float = 10.0) -> Any:
    attempt = 0
    async for attempt_ctx in AsyncRetrying(stop=stop_after_attempt(max_attempts), wait=wait_exponential_jitter(initial=min_wait, max=max_wait), retry=retry_if_exception_type(_RETRYABLE), reraise=True):
        with attempt_ctx:
            attempt += 1
            try:
                result = fn()
                if asyncio.iscoroutine(result):
                    return await result
                return result
            except httpx.HTTPStatusError as e:
                if e.response.status_code in {429, 500, 502, 503, 504}:
                    log.warning("HTTP %d — retrying (%d/%d)", e.response.status_code, attempt, max_attempts)
                    raise
                raise
