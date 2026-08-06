"""R0.1 Local Capability Providers — legacy tools wrapped as CapabilityProviders.

Migrates ReadFile/SearchFiles/ListDirectory from runtime/capability.py
into the new CapabilityProvider protocol. These are registered in
CapabilityRegistry alongside ai_theme_app and future providers.

All local providers implement the CapabilityProvider protocol.
They return data dicts, not pre-assembled prompts.
"""

from __future__ import annotations

from julia_core.capability.models import CapabilityProvider, CapabilityRequest
from julia_core.capability.providers.local.file_read import FileReadProvider
from julia_core.capability.providers.local.file_search import FileSearchProvider
from julia_core.capability.providers.local.directory_list import DirectoryListProvider

__all__ = [
    "FileReadProvider",
    "FileSearchProvider",
    "DirectoryListProvider",
]
