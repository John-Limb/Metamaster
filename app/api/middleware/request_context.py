"""Request context middleware with trace and request identifiers."""

from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request, Response


async def request_context_middleware(request: Request, call_next: Callable):
    """Attach tracing metadata to the request lifecycle."""

    request_id = str(uuid.uuid4())
    trace_id = request.headers.get("x-trace-id", request_id)
    request.state.request_id = request_id
    request.state.trace_id = trace_id

    start_time = time.time()
    response: Response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Trace-ID"] = trace_id
    response.headers["X-Process-Time"] = f"{duration_ms:.2f}"
    return response
