"""Persistent async lifecycle for Core's synchronous capability surface."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import concurrent.futures
import inspect
import threading
from typing import TypeVar


T = TypeVar("T")


class AsyncCapabilityRuntime:
    """Run generic async capability work on one process-lifetime loop.

    The runtime owns no provider semantics. It only keeps async provider
    resources attached to one live loop and provides a deterministic lifecycle
    for closing providers before that loop stops.
    """

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lifecycle_lock = threading.RLock()
        self._closed = False

    @property
    def loop_identity(self) -> int | None:
        with self._lifecycle_lock:
            return id(self._loop) if self._loop is not None else None

    @property
    def thread_identity(self) -> int | None:
        with self._lifecycle_lock:
            return self._thread.ident if self._thread is not None else None

    @property
    def is_closed(self) -> bool:
        with self._lifecycle_lock:
            return self._closed

    def run(self, operation: Callable[[], Awaitable[T]]) -> T:
        """Block the synchronous caller until the persistent loop finishes work."""
        with self._lifecycle_lock:
            if self._closed:
                raise RuntimeError("async capability runtime is closed")
            self._ensure_loop()
            loop = self._loop
            assert loop is not None
            future = asyncio.run_coroutine_threadsafe(operation(), loop)

        try:
            return future.result(timeout=30)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            raise TimeoutError("capability execution exceeded 30 seconds") from exc

    def close(self, providers: object) -> None:
        """Close awaitable providers on their loop, then stop that loop."""
        with self._lifecycle_lock:
            if self._closed:
                return

            if self._thread is None:
                self._closed = True
                return

            loop = self._loop
            thread = self._thread
            assert loop is not None and thread is not None
            close_error: BaseException | None = None
            try:
                close_future = asyncio.run_coroutine_threadsafe(
                    self._close_providers(providers), loop
                )
                try:
                    close_future.result(timeout=30)
                except concurrent.futures.TimeoutError as exc:
                    close_future.cancel()
                    raise TimeoutError(
                        "async capability provider close exceeded 30 seconds"
                    ) from exc
            except BaseException as exc:
                close_error = exc
            finally:
                loop.call_soon_threadsafe(loop.stop)
                thread.join(timeout=5)
                self._loop = None
                self._thread = None
                self._closed = True

            if thread.is_alive():
                raise RuntimeError("async capability runtime thread did not stop")
            if close_error is not None:
                raise close_error

    def _ensure_loop(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="julia-core-async-capability-runtime",
            daemon=True,
        )
        self._thread.start()

    def _run_loop(self) -> None:
        loop = self._loop
        assert loop is not None
        asyncio.set_event_loop(loop)
        try:
            loop.run_forever()
        finally:
            asyncio.set_event_loop(None)
            loop.close()

    @staticmethod
    async def _close_providers(providers: object) -> None:
        if not isinstance(providers, dict):
            return

        close_errors: list[Exception] = []
        for provider in list(providers.values()):
            close = getattr(provider, "close", None)
            if not callable(close):
                continue
            try:
                result = close()
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:
                close_errors.append(exc)

        if close_errors:
            raise RuntimeError(
                "async capability provider close failed: "
                + "; ".join(str(error) for error in close_errors)
            ) from close_errors[0]
