"""
Constants and configurations for dynamic tool discovery and domain scoping.
"""
from typing import Set

SUPPORTED_ENTITIES: Set[str] = {
    "project",
    "dataitem",
    "secret",
    "trigger",
    "artifact",
    "model",
    "workflow",
    "function",
    "run",
}

SUPPORTED_RUNTIMES: Set[str] = {
    "python",
}
