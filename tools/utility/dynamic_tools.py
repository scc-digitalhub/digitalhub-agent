import inspect
import typing
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field, create_model
from langchain_core.tools import BaseTool, StructuredTool, tool
import digitalhub as dh


def _unwrap_callable(func: Callable) -> Callable:
    """Recursively unwrap decorators and closure cells to extract underlying signature and docstring."""
    if hasattr(func, "__wrapped__") and callable(func.__wrapped__):
        return _unwrap_callable(func.__wrapped__)
    if hasattr(func, "__closure__") and func.__closure__:
        for cell in func.__closure__:
            if callable(cell.cell_contents):
                inner = cell.cell_contents
                if hasattr(inner, "__code__") and inner.__name__ != "wrapper":
                    return _unwrap_callable(inner)
    return func


def _resolve_type_annotation(ann: Any) -> Any:
    """Resolve type annotations into valid Python/typing types."""
    if ann is inspect.Parameter.empty or ann is None:
        return Any
    if isinstance(ann, str):
        scope = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "dict": dict,
            "list": list,
            "Any": Any,
            "Optional": Optional,
            "List": List,
            "Dict": Dict,
            "Union": Union,
        }
        try:
            return eval(ann, scope)
        except Exception:
            return Any
    return ann


def _build_dynamic_pydantic_schema(
    schema_name: str,
    sig: inspect.Signature,
    skip_params: Optional[Set[str]] = None,
    injected_params: Optional[Dict[str, Tuple[Any, Any]]] = None,
) -> type[BaseModel]:
    """Dynamically construct a Pydantic schema directly from inspect.Signature."""
    fields: Dict[str, Tuple[Any, Any]] = {}
    if injected_params:
        fields.update(injected_params)

    skip = skip_params or set()
    for param_name, param in sig.parameters.items():
        if param_name in skip or param_name.startswith("*"):
            continue
        if param_name in {"setup_kwargs", "extensions", "config", "self"}:
            continue

        resolved = _resolve_type_annotation(param.annotation)
        default_val = ... if param.default == inspect.Parameter.empty else param.default
        fields[param_name] = (resolved, default_val)

    return create_model(schema_name, **fields)


def _normalize_kwargs_for_func(func: Callable, kwargs: Dict[str, Any], entity_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Intelligently adapt primitive caller arguments to SDK function expectations.
    Automates project_name/project and identifier/name mappings without hardcoded schemas.
    """
    real_func = _unwrap_callable(func)
    sig = inspect.signature(real_func)
    params = sig.parameters
    normalized = dict(kwargs)

    # 1. Project mapping: if function expects 'project' and caller gave 'project_name'
    if "project" in params and "project" not in normalized and "project_name" in normalized:
        normalized["project"] = normalized.pop("project_name")
    elif "context" in params and "context" not in normalized and "project_name" in normalized:
        normalized["context"] = normalized.pop("project_name")
    elif "project_name" in params and "project_name" not in normalized and "project" in normalized:
        normalized["project_name"] = normalized.pop("project")

    # 2. Identifier / Name mapping
    if "identifier" in params and "identifier" not in normalized and "name" in normalized:
        normalized["identifier"] = normalized.pop("name")
    elif "name" in params and "name" not in normalized and "identifier" in normalized:
        normalized["name"] = normalized.pop("identifier")

    # 3. Dynamic Entity Update handling: e.g. update_project(entity: Project), update_dataitem(entity: Dataitem)
    if "entity" in params and "entity" not in normalized:
        ent = entity_name or ("project" if "project" in getattr(func, "__name__", "") else "dataitem")
        if ent == "project":
            p_name = normalized.pop("name", normalized.pop("identifier", normalized.pop("project_name", None)))
            if p_name:
                p_obj = dh.get_project(p_name)
                if "description" in normalized:
                    p_obj.set_description(normalized.pop("description"))
                if "labels" in normalized:
                    p_obj.add_labels(normalized.pop("labels"))
                normalized["entity"] = p_obj
        elif ent == "dataitem":
            di_name = normalized.pop("name", normalized.pop("identifier", None))
            proj = normalized.pop("project", normalized.pop("project_name", None))
            if di_name and proj:
                di_obj = dh.get_dataitem(di_name, project=proj)
                if "description" in normalized:
                    di_obj.set_description(normalized.pop("description"))
                if "labels" in normalized:
                    di_obj.add_labels(normalized.pop("labels"))
                normalized["entity"] = di_obj
        elif ent == "secret":
            s_name = normalized.pop("name", normalized.pop("identifier", None))
            proj = normalized.pop("project", normalized.pop("project_name", None))
            if s_name and proj:
                sec_obj = dh.get_secret(s_name, project=proj)
                if "description" in normalized:
                    sec_obj.set_description(normalized.pop("description"))
                if "labels" in normalized:
                    sec_obj.add_labels(normalized.pop("labels"))
                normalized["entity"] = sec_obj
        elif ent == "trigger":
            t_name = normalized.pop("name", normalized.pop("identifier", None))
            proj = normalized.pop("project", normalized.pop("project_name", None))
            if t_name and proj:
                trg_obj = dh.get_trigger(t_name, project=proj)
                if "description" in normalized:
                    trg_obj.set_description(normalized.pop("description"))
                if "labels" in normalized:
                    trg_obj.add_labels(normalized.pop("labels"))
                normalized["entity"] = trg_obj
        elif ent == "artifact":
            art_name = normalized.pop("name", normalized.pop("identifier", None))
            proj = normalized.pop("project", normalized.pop("project_name", None))
            if art_name and proj:
                art_obj = dh.get_artifact(art_name, project=proj)
                if "description" in normalized:
                    art_obj.set_description(normalized.pop("description"))
                if "labels" in normalized:
                    art_obj.add_labels(normalized.pop("labels"))
                normalized["entity"] = art_obj
        elif ent == "model":
            m_name = normalized.pop("name", normalized.pop("identifier", None))
            proj = normalized.pop("project", normalized.pop("project_name", None))
            if m_name and proj:
                m_obj = dh.get_model(m_name, project=proj)
                if "description" in normalized:
                    m_obj.set_description(normalized.pop("description"))
                if "labels" in normalized:
                    m_obj.add_labels(normalized.pop("labels"))
                normalized["entity"] = m_obj
        elif ent == "workflow":
            wf_name = normalized.pop("name", normalized.pop("identifier", None))
            proj = normalized.pop("project", normalized.pop("project_name", None))
            if wf_name and proj:
                wf_obj = dh.get_workflow(wf_name, project=proj)
                if "description" in normalized:
                    wf_obj.set_description(normalized.pop("description"))
                if "labels" in normalized:
                    wf_obj.add_labels(normalized.pop("labels"))
                normalized["entity"] = wf_obj

    # Filter accepted arguments if function does not accept variable keyword arguments
    has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    if not has_var_kw:
        normalized = {k: v for k, v in normalized.items() if k in params}

    return normalized


class DynamicToolRegistry:
    """
    Central registry with Domain Scoping support.
    Tracks active tools per entity domain (e.g. 'project', 'dataitem') and automatically
    unloads previous domain tools when activating a new domain, preventing tool context creep.
    """

    def __init__(self):
        self._domain_tools: Dict[str, Dict[str, BaseTool]] = {}
        self._active_domain: Optional[str] = None
        self._active_agents: List[Any] = []

    def activate_domain(self, domain: str, tools: List[BaseTool], swap_domain: bool = True) -> None:
        """Activate tools for a domain and swap out previous domain tools if swap_domain=True."""
        domain_key = domain.lower()

        # 1. If swapping domains, unload previous active domain tools from all agents
        if swap_domain and self._active_domain and self._active_domain != domain_key:
            prev_tools = self._domain_tools.get(self._active_domain, {})
            for agent in self._active_agents:
                self._unload_tools_from_agent(agent, list(prev_tools.keys()))

        # 2. Store tools in domain dictionary
        if domain_key not in self._domain_tools:
            self._domain_tools[domain_key] = {}
        for t in tools:
            self._domain_tools[domain_key][t.name] = t

        self._active_domain = domain_key

        # 3. Inject new domain tools into all active agents
        for agent in self._active_agents:
            for t in tools:
                self._inject_tool_into_agent(agent, t)

    def register_agent(self, agent: Any) -> None:
        """Register an active agent graph instance and populate it with currently active domain tools."""
        if agent not in self._active_agents:
            self._active_agents.append(agent)
            if self._active_domain:
                active_tools = self._domain_tools.get(self._active_domain, {})
                for t in active_tools.values():
                    self._inject_tool_into_agent(agent, t)

    def _inject_tool_into_agent(self, agent: Any, dynamic_tool: BaseTool) -> None:
        """Inject a dynamic tool into the agent's ToolNode and model node tool list closure."""
        try:
            tools_node = getattr(agent, "nodes", {}).get("tools")
            if tools_node and hasattr(tools_node, "bound") and hasattr(tools_node.bound, "tools_by_name"):
                tools_node.bound.tools_by_name[dynamic_tool.name] = dynamic_tool

            model_node = getattr(agent, "nodes", {}).get("model")
            if model_node and hasattr(model_node, "bound") and hasattr(model_node.bound, "func"):
                closure = getattr(model_node.bound.func, "__closure__", None)
                if closure:
                    for cell in closure:
                        val = cell.cell_contents
                        if isinstance(val, list) and (len(val) == 0 or hasattr(val[0], "name")):
                            if not any(getattr(t, "name", None) == dynamic_tool.name for t in val):
                                val.append(dynamic_tool)
        except Exception:
            pass

    def _unload_tools_from_agent(self, agent: Any, tool_names: List[str]) -> None:
        """Unload specific tool names from the agent's ToolNode and model node tool list closure."""
        try:
            names_set = set(tool_names)
            tools_node = getattr(agent, "nodes", {}).get("tools")
            if tools_node and hasattr(tools_node, "bound") and hasattr(tools_node.bound, "tools_by_name"):
                for name in tool_names:
                    tools_node.bound.tools_by_name.pop(name, None)

            model_node = getattr(agent, "nodes", {}).get("model")
            if model_node and hasattr(model_node, "bound") and hasattr(model_node.bound, "func"):
                closure = getattr(model_node.bound.func, "__closure__", None)
                if closure:
                    for cell in closure:
                        val = cell.cell_contents
                        if isinstance(val, list) and (len(val) == 0 or hasattr(val[0], "name")):
                            cell.cell_contents[:] = [t for t in val if getattr(t, "name", "") not in names_set]
        except Exception:
            pass

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Find a tool across any registered domain."""
        for domain_dict in self._domain_tools.values():
            if name in domain_dict:
                return domain_dict[name]
        return None

    def get_active_domain_tools(self) -> List[BaseTool]:
        """Return tools for the currently active domain."""
        if not self._active_domain:
            return []
        return list(self._domain_tools.get(self._active_domain, {}).values())

    def get_all_tools(self) -> List[BaseTool]:
        """Return all registered tools across all domains."""
        all_t = {}
        for d in self._domain_tools.values():
            all_t.update(d)
        return list(all_t.values())

    def clear(self) -> None:
        """Clear all registered domain tools and active domain."""
        for domain_dict in self._domain_tools.values():
            for agent in self._active_agents:
                self._unload_tools_from_agent(agent, list(domain_dict.keys()))
        self._domain_tools.clear()
        self._active_domain = None


# Global registry singleton
DYNAMIC_REGISTRY = DynamicToolRegistry()


def _introspect_sdk_for_entity(entity: str) -> List[BaseTool]:
    """
    Pure Introspection Scanner:
    Inspects digitalhub SDK functions and entity classes via runtime reflection (inspect.signature).
    Creates first-class StructuredTool instances with zero hardcoding.
    """
    entity_lower = entity.lower().rstrip("s")
    generated_tools: List[BaseTool] = []

    # 1. Introspect Top-Level SDK Functions
    top_candidates = [
        k for k in dir(dh)
        if not k.startswith("_") and (f"_{entity_lower}" in k.lower() or f"_{entity_lower}s" in k.lower())
    ]

    for fn_name in sorted(top_candidates):
        raw_fn = getattr(dh, fn_name, None)
        if not callable(raw_fn):
            continue

        real_fn = _unwrap_callable(raw_fn)
        sig = inspect.signature(real_fn)
        doc = inspect.getdoc(real_fn) or f"DigitalHub SDK operation: {fn_name}"
        short_doc = doc.split("\n\n")[0].replace("\n", " ").strip()

        # Format tool name: e.g. new_project -> new_dh_project, list_projects -> list_dh_projects
        if f"_{entity_lower}s" in fn_name:
            tool_name = fn_name.replace(f"_{entity_lower}s", f"_dh_{entity_lower}s")
        else:
            tool_name = fn_name.replace(f"_{entity_lower}", f"_dh_{entity_lower}")

        # Injected parameter helpers for update_* functions that take entity objects
        injected: Dict[str, Tuple[Any, Any]] = {}
        skip: Set[str] = {"self", "kwargs"}
        if "entity" in sig.parameters:
            skip.add("entity")
            if entity_lower == "project":
                injected["name"] = (str, ...)
            elif entity_lower in ("dataitem", "secret", "trigger", "artifact", "model", "workflow"):
                injected["project_name"] = (str, ...)
                injected["name"] = (str, ...)
            injected["description"] = (Optional[str], None)
            injected["labels"] = (Optional[List[str]], None)

        schema = _build_dynamic_pydantic_schema(
            f"{tool_name.title().replace('_', '')}Schema",
            sig,
            skip_params=skip,
            injected_params=injected,
        )

        def make_top_level_executor(target_fn):
            def _executor(**kwargs):
                norm = _normalize_kwargs_for_func(target_fn, kwargs, entity_name=entity_lower)
                return target_fn(**norm)
            return _executor

        t = StructuredTool.from_function(
            func=make_top_level_executor(real_fn),
            name=tool_name,
            description=short_doc,
            args_schema=schema,
        )
        generated_tools.append(t)


    # 2. Introspect Entity Class Instance Methods
    entity_class = None
    if entity_lower == "project":
        try:
            from digitalhub.entities.project._base.entity import Project as entity_class
        except Exception:
            pass
        target_methods = ["export", "search_entity", "share", "unshare", "add_label", "add_labels", "set_description"]
    elif entity_lower == "dataitem":
        try:
            from digitalhub.entities.dataitem._base.entity import Dataitem as entity_class
        except Exception:
            pass
        target_methods = ["download", "upload", "export", "as_file", "add_label", "add_labels", "set_description"]
    elif entity_lower == "secret":
        try:
            from digitalhub.entities.secret._base.entity import Secret as entity_class
        except Exception:
            pass
        target_methods = ["export", "read_secret_value", "set_secret_value", "save", "refresh", "add_label", "add_labels", "set_description"]
    elif entity_lower == "trigger":
        try:
            from digitalhub.entities.trigger._base.entity import Trigger as entity_class
        except Exception:
            pass
        target_methods = ["export", "stop", "save", "refresh", "add_label", "add_labels", "set_description"]
    elif entity_lower == "artifact":
        try:
            from digitalhub.entities.artifact._base.entity import Artifact as entity_class
        except Exception:
            pass
        target_methods = ["download", "upload", "export", "as_file", "save", "refresh", "add_label", "add_labels", "set_description"]
    elif entity_lower == "model":
        try:
            from digitalhub.entities.model._base.entity import Model as entity_class
        except Exception:
            pass
        target_methods = ["download", "upload", "export", "as_file", "save", "refresh", "add_label", "add_labels", "set_description", "log_metric", "log_metrics"]
    elif entity_lower == "workflow":
        try:
            from digitalhub.entities.workflow._base.entity import Workflow as entity_class
        except Exception:
            pass
        target_methods = [
            "export", "save", "refresh", "add_label", "add_labels", "set_description",
            "run", "new_task", "get_task", "delete_task", "list_task", "update_task",
            "trigger", "get_trigger", "list_triggers",
        ]
    else:
        target_methods = []

    if entity_class:
        for m_name in target_methods:
            raw_method = getattr(entity_class, m_name, None)
            if not callable(raw_method):
                continue

            real_method = _unwrap_callable(raw_method)
            sig = inspect.signature(real_method)
            doc = inspect.getdoc(real_method) or f"Method {m_name} on {entity_lower} entity."
            short_doc = doc.split("\n\n")[0].replace("\n", " ").strip()

            # Tool name: e.g. export_dh_project, download_dh_dataitem, read_dh_secret_value, stop_dh_trigger, log_dh_model_metric
            if m_name == "search_entity":
                tool_name = "search_dh_project_entities"
            elif m_name == "read_secret_value":
                tool_name = "read_dh_secret_value"
            elif m_name == "set_secret_value":
                tool_name = "set_dh_secret_value"
            elif m_name == "stop" and entity_lower == "trigger":
                tool_name = "stop_dh_trigger"
            elif m_name == "log_metric":
                tool_name = "log_dh_model_metric"
            elif m_name == "log_metrics":
                tool_name = "log_dh_model_metrics"
            elif m_name in ("new_task", "get_task", "delete_task", "update_task"):
                tool_name = f"{m_name.replace('_task', '')}_dh_{entity_lower}_task"
            elif m_name == "list_task":
                tool_name = f"list_dh_{entity_lower}_tasks"
            elif m_name == "trigger" and entity_lower == "workflow":
                tool_name = "trigger_dh_workflow"
            elif m_name == "get_trigger" and entity_lower == "workflow":
                tool_name = "get_dh_workflow_trigger"
            elif m_name == "list_triggers" and entity_lower == "workflow":
                tool_name = "list_dh_workflow_triggers"
            else:
                tool_name = f"{m_name}_dh_{entity_lower}"

            # Injected params for locating entity: project requires project_name; others require project_name + name
            injected_params: Dict[str, Tuple[Any, Any]] = {}
            if entity_lower == "project":
                injected_params["project_name"] = (str, ...)
            else:
                injected_params["project_name"] = (str, ...)
                injected_params["name"] = (str, ...)

            schema = _build_dynamic_pydantic_schema(
                f"{tool_name.title().replace('_', '')}Schema",
                sig,
                skip_params={"self", "kwargs"},
                injected_params=injected_params,
            )

            def make_method_executor(target_method_name):
                def _method_executor(project_name: str, **kwargs):
                    if entity_lower == "project":
                        obj = dh.get_project(project_name)
                    elif entity_lower == "dataitem":
                        d_name = kwargs.pop("name")
                        obj = dh.get_dataitem(d_name, project=project_name)
                    elif entity_lower == "secret":
                        s_name = kwargs.pop("name")
                        obj = dh.get_secret(s_name, project=project_name)
                    elif entity_lower == "trigger":
                        t_name = kwargs.pop("name")
                        obj = dh.get_trigger(t_name, project=project_name)
                    elif entity_lower == "artifact":
                        a_name = kwargs.pop("name")
                        obj = dh.get_artifact(a_name, project=project_name)
                    elif entity_lower == "model":
                        m_name = kwargs.pop("name")
                        obj = dh.get_model(m_name, project=project_name)
                    elif entity_lower == "workflow":
                        w_name = kwargs.pop("name")
                        obj = dh.get_workflow(w_name, project=project_name)
                    else:
                        raise ValueError(f"Unsupported entity: {entity_lower}")

                    method = getattr(obj, target_method_name)
                    norm = _normalize_kwargs_for_func(method, kwargs, entity_name=entity_lower)
                    res = method(**norm)

                    # For modifying methods (add_label, set_description), persist changes
                    if target_method_name in {"add_label", "add_labels", "set_description"}:
                        if entity_lower == "project":
                            return dh.update_project(obj)
                        elif entity_lower == "dataitem":
                            return dh.update_dataitem(obj)
                        elif entity_lower == "secret":
                            return dh.update_secret(obj)
                        elif entity_lower == "trigger":
                            return dh.update_trigger(obj)
                        elif entity_lower == "artifact":
                            return dh.update_artifact(obj)
                        elif entity_lower == "model":
                            return dh.update_model(obj)
                        elif entity_lower == "workflow":
                            return dh.update_workflow(obj)

                    # Return clean representations
                    if target_method_name == "search_entity" and isinstance(res, tuple):
                        return res[0]
                    if target_method_name == "as_file":
                        return str(res)
                    return res
                return _method_executor

            t = StructuredTool.from_function(
                func=make_method_executor(m_name),
                name=tool_name,
                description=short_doc,
                args_schema=schema,
            )
            generated_tools.append(t)

    # 3. Add convenience constructors for trigger, model, or workflow domain if available
    if entity_lower == "trigger":
        try:
            from tools.entity.trigger_tools import new_dh_scheduler_trigger, new_dh_lifecycle_trigger
            generated_tools.extend([new_dh_scheduler_trigger, new_dh_lifecycle_trigger])
        except Exception:
            pass
    elif entity_lower == "model":
        try:
            from tools.entity.model_tools import (
                log_dh_mlflow_model,
                log_dh_sklearn_model,
                log_dh_huggingface_model,
            )
            generated_tools.extend([log_dh_mlflow_model, log_dh_sklearn_model, log_dh_huggingface_model])
        except Exception:
            pass
    elif entity_lower == "workflow":
        try:
            from tools.entity.workflow_tools import build_dh_hera_workflow, run_dh_hera_pipeline
            generated_tools.extend([build_dh_hera_workflow, run_dh_hera_pipeline])
        except Exception:
            pass

    return generated_tools


@tool
def scan_and_create_dh_tools(entity: str, swap_domain: bool = True) -> str:
    """
    Pure Introspection SDK Scanner & Dynamic Tool Generator with Domain Scoping.
    Reflects directly on the DigitalHub SDK for the specified entity ('project', 'dataitem', 'secret', 'trigger', 'artifact', 'model', or 'workflow'),
    dynamically constructs fully-typed LangChain tools with exact Pydantic parameter schemas,
    and activates them in the runtime.

    If swap_domain=True (default), any tools from a previous entity domain are unloaded from the
    agent's active context to prevent tool creep and keep context usage lean.

    Parameters:
    - entity: Entity to introspect and load ('project', 'dataitem', 'secret', 'trigger', 'artifact', 'model', or 'workflow').
    - swap_domain: Whether to unload previous domain tools and swap to this domain (default: True).
    """
    entity_key = entity.lower().rstrip("s")
    if entity_key not in {"project", "dataitem", "secret", "trigger", "artifact", "model", "workflow"}:
        return f"Entity '{entity}' is not supported yet. Supported entities: 'project', 'dataitem', 'secret', 'trigger', 'artifact', 'model', 'workflow'."

    # Perform pure introspection directly on live SDK
    tools = _introspect_sdk_for_entity(entity_key)

    prev_domain = DYNAMIC_REGISTRY._active_domain
    DYNAMIC_REGISTRY.activate_domain(domain=entity_key, tools=tools, swap_domain=swap_domain)

    lines = [
        f"### Pure Introspection & Domain Activation for `{entity_key}`",
        f"Generated **{len(tools)}** tools directly via live SDK reflection (zero hardcoded schemas).",
    ]
    if swap_domain and prev_domain and prev_domain != entity_key:
        lines.append(f"*(Note: Swapped domain from `{prev_domain}` to `{entity_key}`; unloaded `{prev_domain}` tools to maintain lean context.)*")

    lines.append("\n**Active Dynamic Tools:**")
    for t in sorted(tools, key=lambda x: x.name):
        props = t.args
        params_str = ", ".join([f"{k}: {v.get('type', 'any')}" for k, v in props.items()])
        lines.append(f"- **`{t.name}`**: `{params_str}`\n  {t.description}")

    lines.append("\nAll tools are now available for direct invocation in subsequent steps.")
    return "\n".join(lines)


@tool
def call_dh_sdk(entity: str, operation: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
    """
    Universal SDK Dispatcher:
    Execute any DigitalHub SDK operation on an entity without registering tools into the context.
    Ideal for one-off operations where you want to keep the tool count completely static.

    Parameters:
    - entity: Entity name ('project', 'dataitem', 'secret', 'trigger', 'artifact', 'model', 'workflow').
    - operation: Operation name (e.g. 'new_project', 'get_secret', 'new_trigger', 'run_workflow', 'build_dh_hera_workflow').
    - parameters: Dictionary of parameters to pass to the operation.
    """
    args = parameters or {}
    entity_clean = entity.lower().rstrip("s")

    # 1. Try finding dynamically registered or generated tool
    t = DYNAMIC_REGISTRY.get_tool(operation)
    if not t:
        # Check standard tool naming (e.g. operation='export' -> 'export_dh_project')
        alt_name = f"{operation}_dh_{entity_clean}"
        t = DYNAMIC_REGISTRY.get_tool(alt_name)

    if not t:
        # Introspect on the fly to build tool
        candidates = _introspect_sdk_for_entity(entity_clean)
        for cand in candidates:
            if cand.name in {operation, f"{operation}_dh_{entity_clean}", f"{operation}_{entity_clean}"}:
                t = cand
                break

    if t:
        try:
            return t.invoke(args)
        except Exception as e:
            return f"Error executing SDK operation '{operation}' on '{entity}': {e}"

    # 2. Direct top-level fallback
    if hasattr(dh, operation):
        fn = getattr(dh, operation)
        norm = _normalize_kwargs_for_func(fn, args, entity_name=entity_clean)
        try:
            return fn(**norm)
        except Exception as e:
            return f"Error calling dh.{operation}: {e}"

    return f"Operation '{operation}' for entity '{entity}' not found in DigitalHub SDK."


@tool
def execute_dynamic_dh_tool(tool_name: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
    """
    Directly execute any dynamically created tool by name with provided parameters.

    Parameters:
    - tool_name: Name of the dynamic tool.
    - parameters: Keyword arguments.
    """
    return call_dh_sdk(entity=tool_name.split("_")[-1], operation=tool_name, parameters=parameters)


DYNAMIC_TOOLS = [
    scan_and_create_dh_tools,
    call_dh_sdk,
    execute_dynamic_dh_tool,
]
