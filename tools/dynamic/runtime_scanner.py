"""
Pure Introspection Runtime Scanner:
Reflectively extracts runtime execution builders and action specifications from
installed runtime packages (e.g. digitalhub-runtime-python) to dynamically generate
LangChain StructuredTools for runtime actions.
"""
import importlib
import inspect
from functools import lru_cache
from typing import Any, Dict, List, Literal, Optional
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import create_model
import digitalhub as dh
from .constants import SUPPORTED_RUNTIMES
from .schema_builder import build_dynamic_pydantic_schema


@lru_cache(maxsize=16)
def introspect_sdk_for_runtime(runtime: str) -> List[BaseTool]:
    """
    Pure Introspection Runtime Scanner:
    Inspects digitalhub runtime packages (e.g. digitalhub_runtime_python)
    and dynamically constructs first-class StructuredTool instances for
    runtime function creation and execution actions (e.g. job, serve, build).
    Results are cached in memory for sub-millisecond retrieval.
    """
    rt_clean = runtime.lower().replace("_runtime", "").replace("-", "_").rstrip("s")
    if rt_clean not in SUPPORTED_RUNTIMES:
        return []

    pkg_name = f"digitalhub_runtime_{rt_clean}"
    try:
        mod = importlib.import_module(pkg_name)
    except ImportError:
        return []

    target_entity_type = "function"
    kind_name = rt_clean
    run_builders: Dict[str, Any] = {}

    target_builder = None
    modules_to_inspect = [mod]
    if hasattr(mod, "entities"):
        modules_to_inspect.append(mod.entities)

    for m in modules_to_inspect:
        for attr in dir(m):
            obj = getattr(m, attr)
            if isinstance(obj, type) and hasattr(obj, "ENTITY_TYPE") and hasattr(obj, "ENTITY_KIND"):
                ent_type = getattr(obj, "ENTITY_TYPE", "")
                ent_kind = getattr(obj, "ENTITY_KIND", "")
                if ent_type in ("function", "workflow") and ent_kind == rt_clean:
                    target_entity_type = ent_type
                    kind_name = ent_kind
                    target_builder = obj
                elif ent_type == "run" and ent_kind.startswith(f"{rt_clean}+") and ent_kind.endswith(":run"):
                    action = ent_kind.split(":run")[0].split("+")[1]
                    run_builders[action] = obj

    tools: List[BaseTool] = []

    # 1. new_dh_<runtime>_<entity> tool (Autonomous Introspection)
    create_tool_name = f"new_dh_{kind_name}_{target_entity_type}"
    base_func = dh.new_workflow if target_entity_type == "workflow" else dh.new_function
    base_doc = base_func.__doc__ or ""
    spec_cls = getattr(target_builder, "ENTITY_SPEC_CLASS", None) if target_builder else None
    spec_sig = inspect.signature(spec_cls.__init__) if spec_cls else None
    spec_doc = (spec_cls.__init__.__doc__ or spec_cls.__doc__) if spec_cls else ""
    create_doc = "\n\n".join([inspect.cleandoc(d) for d in [base_doc, spec_doc] if d and d.strip()])

    base_injected: Dict[str, Any] = {
        "project": (str, ...),
        "name": (str, ...),
        "code_src": (Optional[str], None),
        "handler": (Optional[str], None),
        "code": (Optional[str], None),
        "base64": (Optional[str], None),
        "description": (Optional[str], None),
        "labels": (Optional[List[str]], None),
        "embedded": (bool, False),
    }

    if spec_sig:
        create_schema = build_dynamic_pydantic_schema(
            f"{create_tool_name.title().replace('_', '')}Schema",
            spec_sig,
            skip_params={"self", "kwargs", "args", "source"},
            injected_params=base_injected,
            docstring=create_doc,
        )
    else:
        sig = inspect.signature(base_func)
        create_schema = build_dynamic_pydantic_schema(
            f"{create_tool_name.title().replace('_', '')}Schema",
            sig,
            skip_params={"self", "kwargs", "args", "kind"},
            injected_params={"project": (str, ...), "name": (str, ...)},
            docstring=base_doc,
        )

    def _create_entity(project: str, name: str, **kwargs):
        if target_entity_type == "workflow":
            return dh.new_workflow(project=project, name=name, kind=kind_name, **kwargs)
        return dh.new_function(project=project, name=name, kind=kind_name, **kwargs)

    t_create = StructuredTool.from_function(
        func=_create_entity,
        name=create_tool_name,
        description=f"Create a {target_entity_type.title()} of kind='{kind_name}' with the {kind_name.title()}-runtime spec.",
        args_schema=create_schema,
    )
    tools.append(t_create)

    # 2. run_dh_<runtime>_<action> tools
    ent_cls = getattr(target_builder, "ENTITY_CLASS", None) if target_builder else None
    base_run_doc = getattr(ent_cls.run, "__doc__", "") if ent_cls and hasattr(ent_cls, "run") else ""

    for action, builder_cls in sorted(run_builders.items()):
        tool_name = f"run_dh_{kind_name}_{action}"
        spec_cls = getattr(builder_cls, "ENTITY_SPEC_CLASS", None)
        sig = inspect.signature(spec_cls.__init__) if spec_cls else None
        spec_doc = (spec_cls.__init__.__doc__ or spec_cls.__doc__) if spec_cls else ""
        action_doc = "\n\n".join([inspect.cleandoc(d) for d in [base_run_doc, spec_doc] if d and d.strip()])

        skip = {"self", "kwargs", "task", "function", "workflow", "source"}
        injected = {
            "project_name": (str, ...),
            "name": (str, ...),
            "wait": (bool, True),
            "log_info": (bool, True),
        }
        if rt_clean == "python" and action == "job":
            injected["local_execution"] = (bool, False)
        elif rt_clean == "container":
            if action in ("job", "serve"):
                injected["auto_build"] = (bool, True)
            elif action == "build":
                injected["instructions"] = (Optional[List[str]], None)
                skip.add("instructions")

        action_schema = (
            build_dynamic_pydantic_schema(
                f"{tool_name.title().replace('_', '')}Schema",
                sig,
                skip_params=skip,
                injected_params=injected,
                docstring=action_doc,
            )
            if sig
            else None
        )

        def make_executor(act=action, ent_type=target_entity_type):
            def _exec(project_name: str, name: str, **kwargs):
                if ent_type == "workflow":
                    obj = dh.get_workflow(name, project=project_name)
                else:
                    obj = dh.get_function(name, project=project_name)
                return obj.run(action=act, **kwargs)
            return _exec

        t_run = StructuredTool.from_function(
            func=make_executor(action, target_entity_type),
            name=tool_name,
            description=f"Execute a {kind_name.title()} {target_entity_type} with action='{action}'.",
            args_schema=action_schema,
        )
        tools.append(t_run)

    return tools
