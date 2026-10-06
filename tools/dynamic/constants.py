"""
Constants and configurations for dynamic tool discovery and domain scoping.
"""
import importlib.metadata
from functools import lru_cache
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


@lru_cache(maxsize=1)
def discover_installed_runtimes() -> Set[str]:
    """
    Autonomous Package Discovery:
    Reflectively queries installed Python distribution metadata for all
    `digitalhub-runtime-*` packages present in the active environment.
    """
    runtimes = {"python", "container"}
    try:
        for dist in importlib.metadata.distributions():
            pkg_name = dist.metadata.get("Name", "")
            if pkg_name.startswith("digitalhub-runtime-"):
                rt = pkg_name.replace("digitalhub-runtime-", "").replace("-", "_").lower()
                runtimes.add(rt)
    except Exception:
        pass
    return runtimes


SUPPORTED_RUNTIMES: Set[str] = discover_installed_runtimes()

