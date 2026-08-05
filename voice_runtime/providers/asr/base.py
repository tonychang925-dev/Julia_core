"""ASR Provider Interface — Core never processes audio bytes."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Optional


class ASRProvider(ABC):
    """Abstract ASR provider. Receives audio frames, emits transcripts."""

    def __init__(self):
        self._on_partial: Optional[Callable[[str], None]] = None
        self._on_final: Optional[Callable[[str], None]] = None

    def on_partial(self, callback: Callable[[str], None]):
        """Called when partial transcript is available (streaming)."""
        self._on_partial = callback

    def on_final(self, callback: Callable[[str], None]):
        """Called when final transcript is ready."""
        self._on_final = callback

    @abstractmethod
    async def start(self):
        """Start the ASR session."""

    @abstractmethod
    async def feed_frame(self, frame) -> None:
        """Feed one audio frame (aiortc AudioFrame) to ASR."""

    @abstractmethod
    async def stop(self) -> Optional[str]:
        """Stop ASR, return final transcript."""
