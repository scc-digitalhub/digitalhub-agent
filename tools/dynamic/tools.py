"""
Exposed LangChain tools for dynamic discovery, registration, and universal execution.
"""
from typing import Any, Dict, Optional
from langchain_core.tools import tool
import digitalhub as dh
from .constants import SUPPORTED_ENTITIES, SUPPORTED_RUNTIMES
from .entity_scanner import introspect_sdk_for_entity
from .normalizer import normalize_kwargs_for_func
from .registry import DYNAMIC_REGISTRY
from .runtime_scanner import introspect_sdk_for_runtime


@tool
def scan_and_create_dh_tools(
    entity: Optional[str] = None,
    runtime_name: Optional[str] = None,
    swap_domain: bool = True,
) -> str:
    """
    Pure Introspection SDK Scanner & Dynamic Tool Generator with Domain Scoping.
    Reflects directly on the DigitalHub SDK for the specified entity or runtime,
    dynamically constructs fully-typed LangChain tools with exact Pydantic parameter schemas,
    and activates them in the runtime.

    If swap_domain=True (default), any tools from a previous domain are unloaded from the
    agent's active context to prevent tool creep and keep context usage lean.

    Parameters:
    - entity: Entity to introspect and load ('project', 'dataitem', 'secret', 'trigger', 'artifact', 'model', 'workflow', 'function', or 'run').
    - runtime_name: Runtime to introspect and load ('python' or 'container').
    - swap_domain: Whether to unload previous domain tools and swap to this domain (default: True).
    """
    is_runtime = False
    target = ""

    if runtime_name:
        is_runtime = True
        target = runtime_name.lower().replace("_runtime", "").replace("-", "_").rstrip("s")
    elif entity:
        raw_ent = entity.lower().replace("_runtime", "").replace("-", "_").rstrip("s")
        if raw_ent in SUPPORTED_RUNTIMES or raw_ent.startswith("python") or raw_ent.startswith("container"):
            is_runtime = True
            target = raw_ent
        elif raw_ent in SUPPORTED_ENTITIES:
            target = raw_ent
        else:
            return (
                f"Target '{entity}' is neither a supported entity nor a supported runtime.\n"
                f"Supported entities: {sorted(SUPPORTED_ENTITIES)}\n"
                f"Supported runtimes: {sorted(SUPPORTED_RUNTIMES)}"
            )
    else:
        return "Please specify an 'entity' (e.g. 'project', 'function') or 'runtime_name' (e.g. 'python') to scan."

    if is_runtime:
        tools = introspect_sdk_for_runtime(target)
        if not tools:
            return f"Runtime '{target}' package 'digitalhub_runtime_{target}' could not be loaded or produced no tools."
        domain_name = f"runtime:{target}"
        title = f"Pure Introspection & Domain Activation for Runtime `{target}`"
    else:
        tools = introspect_sdk_for_entity(target)
        domain_name = target
        title = f"Pure Introspection & Domain Activation for Entity `{target}`"

    prev_domain = DYNAMIC_REGISTRY._active_domain
    DYNAMIC_REGISTRY.activate_domain(domain=domain_name, tools=tools, swap_domain=swap_domain)

    lines = [
        f"### {title}",
        f"Generated **{len(tools)}** tools directly via live SDK reflection (zero hardcoded schemas).",
    ]
    if swap_domain and prev_domain and prev_domain != domain_name:
        lines.append(f"*(Note: Swapped domain from `{prev_domain}` to `{domain_name}`; unloaded `{prev_domain}` tools to maintain lean context.)*")

    lines.append("\n**Active Dynamic Tools:**")
    for t in sorted(tools, key=lambda x: x.name):
        props = t.args
        params_str = ", ".join([f"{k}: {v.get('type', 'any')}" for k, v in props.items()])
        lines.append(f"- **`{t.name}`**: `{params_str}`\n  {t.description}")

    lines.append("\nAll tools are now available for direct invocation in subsequent steps.")
    return "\n".join(lines)


def dispatch_dh_sdk(
    entity: Optional[str] = None,
    runtime_name: Optional[str] = None,
    operation: str = "",
    parameters: Optional[Dict[str, Any]] = None,
) -> Any:
    """Internal helper to dispatch SDK operations across registered tools, introspected candidates, or top-level SDK functions."""
    args = parameters or {}

    # 1. Check if tool is already in registry
    t = DYNAMIC_REGISTRY.get_tool(operation)

    # 2. Check if runtime-targeted
    target_rt = runtime_name
    if not target_rt and entity:
        raw_ent = entity.lower().replace("_runtime", "").replace("-", "_").rstrip("s")
        if raw_ent in SUPPORTED_RUNTIMES or raw_ent.startswith("python") or raw_ent.startswith("container"):
            target_rt = raw_ent

    if not t and target_rt:
        rt_clean = target_rt.lower().replace("_runtime", "").replace("-", "_").rstrip("s")
        candidates = introspect_sdk_for_runtime(rt_clean)
        for cand in candidates:
            if cand.name in {operation, f"{operation}_dh_{rt_clean}", f"{operation}_{rt_clean}"}:
                t = cand
                break

    # 3. Check entity candidates if not found
    if not t and entity and not target_rt:
        entity_clean = entity.lower().rstrip("s")
        alt_name = f"{operation}_dh_{entity_clean}"
        t = DYNAMIC_REGISTRY.get_tool(alt_name)
        if not t:
            candidates = introspect_sdk_for_entity(entity_clean)
            for cand in candidates:
                if cand.name in {operation, f"{operation}_dh_{entity_clean}", f"{operation}_{entity_clean}"}:
                    t = cand
                    break

    if t:
        try:
            return t.invoke(args)
        except Exception as e:
            return f"Error executing SDK operation '{operation}': {e}"

    # 4. Direct top-level fallback
    if hasattr(dh, operation):
        fn = getattr(dh, operation)
        norm = normalize_kwargs_for_func(fn, args, entity_name=(entity or runtime_name or ""))
        try:
            return fn(**norm)
        except Exception as e:
            return f"Error calling dh.{operation}: {e}"

    return f"Operation '{operation}' not found in DigitalHub SDK or installed runtimes."


@tool
def call_dh_sdk(
    entity: Optional[str] = None,
    runtime_name: Optional[str] = None,
    operation: str = "",
    parameters: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Universal SDK Dispatcher:
    Execute any DigitalHub SDK operation on an entity or runtime without registering tools into the context.
    Ideal for one-off operations where you want to keep the tool count completely static.

    Parameters:
    - entity: Entity name ('project', 'dataitem', 'secret', 'trigger', 'artifact', 'model', 'workflow', 'function', 'run').
    - runtime_name: Runtime name ('python' or 'container').
    - operation: Operation name (e.g. 'new_project', 'run_dh_python_job', 'new_dh_python_function', etc.).
    - parameters: Dictionary of parameters to pass to the operation.
    """
    return dispatch_dh_sdk(
        entity=entity,
        runtime_name=runtime_name,
        operation=operation,
        parameters=parameters,
    )


@tool
def execute_dynamic_dh_tool(tool_name: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
    """
    Directly execute any dynamically created tool by name with provided parameters.
    Note: If you have already activated the domain using scan_and_create_dh_tools, the tool is already available in your toolset and can be invoked directly by name (e.g. new_dh_project(...)) without calling this wrapper.

    Parameters:
    - tool_name: Name of the dynamic tool.
    - parameters: Keyword arguments.
    """
    args = parameters or {}

    # 1. Check if tool is already in registry
    t = DYNAMIC_REGISTRY.get_tool(tool_name)
    if t:
        try:
            return t.invoke(args)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {e}"

    # 2. Check runtimes
    for rt in SUPPORTED_RUNTIMES:
        if f"_{rt}_" in tool_name or tool_name.startswith(f"run_dh_{rt}") or tool_name.startswith(f"new_dh_{rt}"):
            return dispatch_dh_sdk(runtime_name=rt, operation=tool_name, parameters=args)

    # 3. Check entity
    entity_cand = tool_name.split("_")[-1]
    return dispatch_dh_sdk(entity=entity_cand, operation=tool_name, parameters=args)


DYNAMIC_TOOLS = [
    scan_and_create_dh_tools,
    call_dh_sdk,
    execute_dynamic_dh_tool,
]
