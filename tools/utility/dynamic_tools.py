"""Legacy dynamic_tools module proxying to the modular tools.dynamic package.

Preserves backward compatibility for existing module imports.
"""

from tools.dynamic import (
    SUPPORTED_ENTITIES,
    SUPPORTED_RUNTIMES,
    unwrap_callable,
    resolve_type_annotation,
    build_dynamic_pydantic_schema,
    normalize_kwargs_for_func,
    sync_entity_for_update,
    DynamicToolRegistry,
    DYNAMIC_REGISTRY,
    introspect_sdk_for_entity,
    introspect_sdk_for_runtime,
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
