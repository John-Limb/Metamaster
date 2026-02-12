"""Shared asyncio helpers for Celery workers.

Celery executes tasks inside synchronous worker processes. Previously we
used ``asyncio.run`` per task invocation which repeatedly created event
loops and caused contention once multiple workers were running.  This
module centralises the event loop lifecycle so tasks can schedule
coroutines via ``asyncio.run_coroutine_threadsafe`` without spawning
fresh loops on every call.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any, Awaitable, TypeVar


logger = logging.getLogger(__name__)

_loop: asyncio.AbstractEventLoop | None = None
_loop_thread: threading.Thread | None = None
_loop_started = threading.Event()

T = TypeVar("T")


def _event_loop_worker(loop: asyncio.AbstractEventLoop) -> None:
    """Run the asyncio event loop forever inside a background thread."""

    asyncio.set_event_loop(loop)
    _loop_started.set()
    try:
        loop.run_forever()
    except Exception as exc:  # pragma: no cover - catastrophic failure
        logger.exception("Background event loop terminated unexpectedly", exc_info=exc)


def _ensure_loop() -> asyncio.AbstractEventLoop:
    """Create (if needed) and return the background asyncio event loop."""

    global _loop, _loop_thread

    if _loop and _loop.is_running():
        return _loop

    loop = asyncio.new_event_loop()
    thread = threading.Thread(
        target=_event_loop_worker,
        name="celery-async-loop",
        args=(loop,),
        daemon=True,
    )
    thread.start()

    # Wait until the worker thread signals that the loop is ready so the
    # first scheduled coroutine does not race the loop.startup.
    _loop_started.wait()

    _loop = loop
    _loop_thread = thread
    logger.debug("Initialized shared asyncio event loop for Celery workers")
    return loop


def run_async(coro: Awaitable[T]) -> T:
    """Execute an async coroutine from sync Celery context.

    Args:
        coro: The coroutine object to execute.

    Returns:
        The result of the awaited coroutine.
    """

    loop = _ensure_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


def shutdown_loop() -> None:
    """Gracefully shut down the background loop (used by tests)."""

    global _loop, _loop_thread

    if not _loop:
        return

    logger.debug("Shutting down shared asyncio event loop")
    _loop.call_soon_threadsafe(_loop.stop)
    if _loop_thread:
        _loop_thread.join(timeout=1)

    _loop = None
    _loop_thread = None
    _loop_started.clear()
