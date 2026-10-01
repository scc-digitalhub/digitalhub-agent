"""Dynamic tool reflection, registry, and execution package for DigitalHub SDK.

Provides automated inspection and execution for DigitalHub entities and runtimes.
"""

from tools.dynamic.constants import SUPPORTED_ENTITIES, SUPPORTED_RUNTIMES
from tools.dynamic.schema_builder import (
    unwrap_callable,
    resolve_type_annotation,
    build_dynamic_pydantic_schema,
)
from tools.dynamic.normalizer import (
    normalize_kwargs_for_func,
    sync_entity_for_update,
)
from tools.dynamic.registry import DynamicToolRegistry, DYNAMIC_REGISTRY
from tools.dynamic.entity_scanner import introspect_sdk_for_entity
from tools.dynamic.runtime_scanner import introspect_sdk_for_runtime
from tools.dynamic.tools import (
    scan_and_create_dh_tools,
    call_dh_sdk,
    execute_dynamic_dh_tool,
    DYNAMIC_TOOLS,
)

__all__ = [
    "SUPPORTED_ENTITIES",
    "SUPPORTED_RUNTIMES",
    "unwrap_callable",
    "resolve_type_annotation",
    "build_dynamic_pydantic_schema",
    "normalize_kwargs_for_func",
    "sync_entity_for_update",
    "DynamicToolRegistry",
    "DYNAMIC_REGISTRY",
    "introspect_sdk_for_entity",
    "introspect_sdk_for_runtime",
    "scan_and_create_dh_tools",
    "call_dh_sdk",
    "execute_dynamic_dh_tool",
    "DYNAMIC_TOOLS",
]
