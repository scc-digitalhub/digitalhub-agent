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

    for attr in dir(mod):
        obj = getattr(mod, attr)
        if isinstance(obj, type) and hasattr(obj, "ENTITY_TYPE") and hasattr(obj, "ENTITY_KIND"):
            ent_type = getattr(obj, "ENTITY_TYPE", "")
            ent_kind = getattr(obj, "ENTITY_KIND", "")
            if ent_type in ("function", "workflow") and ent_kind == rt_clean:
                target_entity_type = ent_type
                kind_name = ent_kind
            elif ent_type == "run" and ent_kind.startswith(f"{rt_clean}+") and ent_kind.endswith(":run"):
                action = ent_kind.split(":run")[0].split("+")[1]
                run_builders[action] = obj

    tools: List[BaseTool] = []

    # 1. new_dh_<runtime>_<entity> tool
    create_tool_name = f"new_dh_{kind_name}_{target_entity_type}"
    if rt_clean == "python":
        PythonVersion = Literal["PYTHON3_10", "PYTHON3_11", "PYTHON3_12", "PYTHON3_13", "PYTHON3_14"]
        create_fields = {
            "project": (str, ...),
            "name": (str, ...),
            "handler": (str, ...),
            "python_version": (Optional[PythonVersion], None),
            "code_src": (Optional[str], None),
            "code": (Optional[str], None),
            "base64": (Optional[str], None),
            "init_function": (Optional[str], None),
            "lang": (Optional[str], None),
            "image": (Optional[str], None),
            "base_image": (Optional[str], None),
            "requirements": (Optional[List[str]], None),
            "uuid": (Optional[str], None),
            "description": (Optional[str], None),
            "labels": (Optional[List[str]], None),
            "embedded": (bool, False),
        }
        create_schema = create_model(f"{create_tool_name.title().replace('_', '')}Schema", **create_fields)

        def _create_python_func(project: str, name: str, **kwargs):
            return dh.new_function(project=project, name=name, kind=kind_name, **kwargs)

        t_create = StructuredTool.from_function(
            func=_create_python_func,
            name=create_tool_name,
            description=f"Create a Function of kind='{kind_name}' with the {kind_name.title()}-runtime spec.",
            args_schema=create_schema,
        )
        tools.append(t_create)
    else:
        def _create_generic_entity(project: str, name: str, **kwargs):
            if target_entity_type == "workflow":
                return dh.new_workflow(project=project, name=name, kind=kind_name, **kwargs)
            return dh.new_function(project=project, name=name, kind=kind_name, **kwargs)

        sig = inspect.signature(dh.new_workflow if target_entity_type == "workflow" else dh.new_function)
        schema = build_dynamic_pydantic_schema(
            f"{create_tool_name.title().replace('_', '')}Schema",
            sig,
            skip_params={"self", "kwargs", "kind"},
            injected_params={"project": (str, ...), "name": (str, ...)},
        )
        t_create = StructuredTool.from_function(
            func=_create_generic_entity,
            name=create_tool_name,
            description=f"Create a {target_entity_type.title()} of kind='{kind_name}' with the {kind_name.title()}-runtime spec.",
            args_schema=schema,
        )
        tools.append(t_create)

    # 2. run_dh_<runtime>_<action> tools
    for action, builder_cls in sorted(run_builders.items()):
        tool_name = f"run_dh_{kind_name}_{action}"
        spec_cls = getattr(builder_cls, "ENTITY_SPEC_CLASS", None)
        sig = inspect.signature(spec_cls.__init__) if spec_cls else None

        skip = {"self", "kwargs", "task", "function", "workflow", "source"}
        injected = {
            "project_name": (str, ...),
            "name": (str, ...),
            "wait": (bool, True),
            "log_info": (bool, True),
        }
        if action == "job":
            injected["local_execution"] = (bool, False)

        action_schema = build_dynamic_pydantic_schema(
            f"{tool_name.title().replace('_', '')}Schema",
            sig,
            skip_params=skip,
            injected_params=injected,
        ) if sig else None

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
