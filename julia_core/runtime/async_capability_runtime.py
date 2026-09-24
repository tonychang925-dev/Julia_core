"""Persistent async lifecycle for Core's synchronous capability surface."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import concurrent.futures
from enum import Enum
import inspect
import math
import threading
from typing import TypeVar


T = TypeVar("T")

DEFAULT_CAPABILITY_EXECUTION_TIMEOUT_SECONDS = 30.0


class AsyncCapabilityRuntimeState(Enum):
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"


class AsyncCapabilityRuntime:
    """Run generic async capability work on one process-lifetime loop."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lifecycle_lock = threading.RLock()
        self._lifecycle_condition = threading.Condition(self._lifecycle_lock)
        self._shutdown_lock = threading.Lock()
        self._state = AsyncCapabilityRuntimeState.OPEN
        self._in_flight_executions = 0

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
            return self._state is AsyncCapabilityRuntimeState.CLOSED

    @property
    def state(self) -> str:
        with self._lifecycle_lock:
            return self._state.value

    def run(
        self,
        operation: Callable[[], Awaitable[T]],
        *,
        timeout_seconds: float = DEFAULT_CAPABILITY_EXECUTION_TIMEOUT_SECONDS,
    ) -> T:
        """Block the synchronous caller until the persistent loop finishes work."""
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("capability execution timeout must be finite and positive")

        with self._lifecycle_lock:
            if self._state is not AsyncCapabilityRuntimeState.OPEN:
                raise RuntimeError(f"async capability runtime is {self._state.value}")

            self._ensure_loop()
            loop = self._loop
            assert loop is not None
            future = asyncio.run_coroutine_threadsafe(operation(), loop)
            self._in_flight_executions += 1
            future.add_done_callback(self._finish_execution)

        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            try:
                future.result(timeout=5)
            except BaseException:
                pass
            raise TimeoutError(
                f"capability execution exceeded {timeout_seconds} seconds"
            ) from exc

    def close(self, providers: object) -> None:
        """Drain executions, close providers, then stop the persistent loop."""
        with self._shutdown_lock:
            with self._lifecycle_lock:
                if self._state is AsyncCapabilityRuntimeState.CLOSED:
                    return

                self._state = AsyncCapabilityRuntimeState.CLOSING
                self._lifecycle_condition.notify_all()
                self._ensure_loop()
                loop = self._loop
                thread = self._thread
                assert loop is not None and thread is not None

                drained = self._lifecycle_condition.wait_for(
                    lambda: self._in_flight_executions == 0,
                    timeout=30,
                )

            if not drained:
                raise TimeoutError(
                    "timed out waiting for in-flight capability executions"
                )

            close_error: BaseException | None = None
            try:
                close_future = asyncio.run_coroutine_threadsafe(
                    self._close_providers(providers), loop
                )
                try:
                    close_future.result(timeout=30)
                except concurrent.futures.TimeoutError as exc:
                    close_future.cancel()
                    try:
                        close_future.result(timeout=5)
                    except BaseException:
                        pass
                    raise TimeoutError(
                        "async capability provider close exceeded 30 seconds"
                    ) from exc
            except BaseException as exc:
                close_error = exc
            finally:
                loop.call_soon_threadsafe(loop.stop)
                thread.join(timeout=5)
                with self._lifecycle_lock:
                    self._loop = None
                    self._thread = None
                    self._state = AsyncCapabilityRuntimeState.CLOSED
                    self._lifecycle_condition.notify_all()

            if thread.is_alive():
                raise RuntimeError("async capability runtime thread did not stop")
            if close_error is not None:
                raise close_error

    def wait_for_state(self, state: str, timeout: float = 5) -> bool:
        target = AsyncCapabilityRuntimeState(state)
        with self._lifecycle_lock:
            return self._lifecycle_condition.wait_for(
                lambda: self._state is target,
                timeout=timeout,
            )

    def _finish_execution(self, future: concurrent.futures.Future) -> None:
        with self._lifecycle_lock:
            self._in_flight_executions -= 1
            self._lifecycle_condition.notify_all()

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
