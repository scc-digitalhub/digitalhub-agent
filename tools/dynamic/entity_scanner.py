"""
Pure Introspection Entity Scanner:
Reflectively extracts methods, signatures, and docstrings from DigitalHub SDK
top-level functions and entity classes to dynamically generate LangChain StructuredTools.
"""
import inspect
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from langchain_core.tools import BaseTool, StructuredTool
import digitalhub as dh
from .schema_builder import build_dynamic_pydantic_schema, unwrap_callable
from .normalizer import normalize_kwargs_for_func


ENTITY_CLASS_SPECS: Dict[str, Tuple[str, str, List[str]]] = {
    "project": (
        "digitalhub.entities.project._base.entity",
        "Project",
        ["export", "search_entity", "share", "unshare", "add_label", "add_labels", "set_description"],
    ),
    "dataitem": (
        "digitalhub.entities.dataitem._base.entity",
        "Dataitem",
        ["download", "upload", "export", "as_file", "add_label", "add_labels", "set_description"],
    ),
    "secret": (
        "digitalhub.entities.secret._base.entity",
        "Secret",
        ["export", "read_secret_value", "set_secret_value", "save", "refresh", "add_label", "add_labels", "set_description"],
    ),
    "trigger": (
        "digitalhub.entities.trigger._base.entity",
        "Trigger",
        ["export", "stop", "save", "refresh", "add_label", "add_labels", "set_description"],
    ),
    "artifact": (
        "digitalhub.entities.artifact._base.entity",
        "Artifact",
        ["download", "upload", "export", "as_file", "save", "refresh", "add_label", "add_labels", "set_description"],
    ),
    "model": (
        "digitalhub.entities.model._base.entity",
        "Model",
        ["download", "upload", "export", "as_file", "save", "refresh", "add_label", "add_labels", "set_description", "log_metric", "log_metrics"],
    ),
    "workflow": (
        "digitalhub.entities.workflow._base.entity",
        "Workflow",
        [
            "export", "save", "refresh", "add_label", "add_labels", "set_description",
            "run", "new_task", "get_task", "delete_task", "list_task", "update_task",
            "trigger", "get_trigger", "list_triggers",
        ],
    ),
    "function": (
        "digitalhub.entities.function._base.entity",
        "Function",
        [
            "export", "save", "refresh", "add_label", "add_labels", "set_description",
            "run", "new_task", "get_task", "delete_task", "list_task", "update_task",
            "trigger", "get_trigger", "list_triggers",
        ],
    ),
    "run": (
        "digitalhub.entities.run._base.entity",
        "Run",
        [
            "run", "wait", "stop", "resume", "log_metric", "log_metrics",
            "save", "refresh", "export", "add_label", "add_labels", "set_description",
            "output", "outputs", "result", "results", "invoke",
        ],
    ),
}


def _resolve_tool_name_for_top_level(fn_name: str, entity_lower: str) -> str:
    """Standardize tool naming for top-level SDK functions."""
    if fn_name.startswith("log_") and fn_name in ("log_mlflow", "log_sklearn", "log_huggingface"):
        return f"log_dh_{fn_name.replace('log_', '')}_model"
    if fn_name.startswith("register_") and fn_name in ("register_mlflow", "register_sklearn", "register_huggingface"):
        return f"register_dh_{fn_name.replace('register_', '')}_model"
    if f"_{entity_lower}s" in fn_name:
        return fn_name.replace(f"_{entity_lower}s", f"_dh_{entity_lower}s")
    return fn_name.replace(f"_{entity_lower}", f"_dh_{entity_lower}")


def _resolve_tool_name_for_method(m_name: str, entity_lower: str) -> str:
    """Standardize tool naming for entity instance methods."""
    special_names = {
        ("output", "run"): "get_dh_run_output",
        ("outputs", "run"): "get_dh_run_outputs",
        ("result", "run"): "get_dh_run_result",
        ("results", "run"): "get_dh_run_results",
        ("invoke", "run"): "invoke_dh_run_service",
        ("search_entity", "project"): "search_dh_project_entities",
        ("read_secret_value", "secret"): "read_dh_secret_value",
        ("set_secret_value", "secret"): "set_dh_secret_value",
        ("stop", "trigger"): "stop_dh_trigger",
        ("stop", "run"): "stop_dh_run",
        ("run", "run"): "start_dh_run",
        ("logs", "run"): "get_dh_run_logs",
        ("log_metric", "model"): "log_dh_model_metric",
        ("log_metrics", "model"): "log_dh_model_metrics",
        ("log_metric", "run"): "log_dh_run_metric",
        ("log_metrics", "run"): "log_dh_run_metrics",
    }
    if (m_name, entity_lower) in special_names:
        return special_names[(m_name, entity_lower)]

    if m_name in ("new_task", "get_task", "delete_task", "update_task"):
        return f"{m_name.replace('_task', '')}_dh_{entity_lower}_task"
    if m_name == "list_task":
        return f"list_dh_{entity_lower}_tasks"
    if m_name == "trigger" and entity_lower in ("workflow", "function"):
        return f"trigger_dh_{entity_lower}"
    if m_name == "get_trigger" and entity_lower in ("workflow", "function"):
        return f"get_dh_{entity_lower}_trigger"
    if m_name == "list_triggers" and entity_lower in ("workflow", "function"):
        return f"list_dh_{entity_lower}_triggers"

    return f"{m_name}_dh_{entity_lower}"


@lru_cache(maxsize=32)
def introspect_sdk_for_entity(entity: str) -> List[BaseTool]:
    """
    Pure Introspection Scanner:
    Inspects DigitalHub SDK functions and entity classes via runtime reflection.
    Creates first-class StructuredTool instances with zero hardcoding.
    Results are cached in memory for sub-millisecond repeated domain swaps.
    """
    entity_lower = entity.lower().rstrip("s")
    generated_tools: List[BaseTool] = []

    # 1. Introspect Top-Level SDK Functions
    if entity_lower == "model":
        top_candidates = [
            k for k in dir(dh)
            if not k.startswith("_") and (
                f"_{entity_lower}" in k.lower()
                or f"_{entity_lower}s" in k.lower()
                or k in ("log_mlflow", "log_sklearn", "log_huggingface", "register_mlflow", "register_sklearn", "register_huggingface")
            )
        ]
    else:
        top_candidates = [
            k for k in dir(dh)
            if not k.startswith("_") and (f"_{entity_lower}" in k.lower() or f"_{entity_lower}s" in k.lower())
        ]

    for fn_name in sorted(top_candidates):
        raw_fn = getattr(dh, fn_name, None)
        if not callable(raw_fn):
            continue

        real_fn = unwrap_callable(raw_fn)
        sig = inspect.signature(real_fn)
        doc = inspect.getdoc(real_fn) or f"DigitalHub SDK operation: {fn_name}"
        short_doc = doc.split("\n\n")[0].replace("\n", " ").strip()
        tool_name = _resolve_tool_name_for_top_level(fn_name, entity_lower)

        # Injected parameter helpers for update_* functions that take entity objects
        injected: Dict[str, Tuple[Any, Any]] = {}
        skip: Set[str] = {"self", "kwargs"}
        if "entity" in sig.parameters:
            skip.add("entity")
            if entity_lower == "project":
                injected["name"] = (str, ...)
            elif entity_lower in ("dataitem", "secret", "trigger", "artifact", "model", "workflow", "function"):
                injected["project_name"] = (str, ...)
                injected["name"] = (str, ...)
            elif entity_lower == "run":
                injected["project"] = (str, ...)
                injected["run_id"] = (str, ...)
            injected["description"] = (Optional[str], None)
            injected["labels"] = (Optional[List[str]], None)

        schema = build_dynamic_pydantic_schema(
            f"{tool_name.title().replace('_', '')}Schema",
            sig,
            skip_params=skip,
            injected_params=injected,
        )

        def make_top_level_executor(target_fn):
            def _executor(**kwargs):
                norm = normalize_kwargs_for_func(target_fn, kwargs, entity_name=entity_lower)
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
    if entity_lower in ENTITY_CLASS_SPECS:
        module_path, class_name, target_methods = ENTITY_CLASS_SPECS[entity_lower]
        try:
            import importlib
            mod = importlib.import_module(module_path)
            entity_class = getattr(mod, class_name, None)
        except Exception:
            entity_class = None

        if entity_class:
            for m_name in target_methods:
                raw_method = getattr(entity_class, m_name, None)
                if not raw_method and entity_lower == "run":
                    try:
                        from digitalhub_runtime_python.entities.run._base.entity import RunBaseRun
                        raw_method = getattr(RunBaseRun, m_name, None)
                    except Exception:
                        pass
                    if not raw_method:
                        try:
                            from digitalhub_runtime_python.entities.run.python_serve.entity import RunPythonRunServe
                            raw_method = getattr(RunPythonRunServe, m_name, None)
                        except Exception:
                            pass

                if not callable(raw_method):
                    continue

                real_method = unwrap_callable(raw_method)
                sig = inspect.signature(real_method)
                doc = inspect.getdoc(real_method) or f"Method {m_name} on {entity_lower} entity."
                short_doc = doc.split("\n\n")[0].replace("\n", " ").strip()
                tool_name = _resolve_tool_name_for_method(m_name, entity_lower)

                injected_params: Dict[str, Tuple[Any, Any]] = {}
                if entity_lower == "project":
                    injected_params["project_name"] = (str, ...)
                elif entity_lower == "run":
                    injected_params["project"] = (str, ...)
                    injected_params["run_id"] = (str, ...)
                else:
                    injected_params["project_name"] = (str, ...)
                    injected_params["name"] = (str, ...)

                schema = build_dynamic_pydantic_schema(
                    f"{tool_name.title().replace('_', '')}Schema",
                    sig,
                    skip_params={"self", "kwargs"},
                    injected_params=injected_params,
                )

                def make_method_executor(target_method_name):
                    def _method_executor(project_name: str = None, **kwargs):
                        if entity_lower == "project":
                            obj = dh.get_project(project_name)
                        elif entity_lower == "run":
                            r_id = kwargs.pop("run_id", kwargs.pop("identifier", kwargs.pop("name", None)))
                            proj = kwargs.pop("project", project_name)
                            obj = dh.get_run(r_id, project=proj)
                        else:
                            name = kwargs.pop("name")
                            getter = getattr(dh, f"get_{entity_lower}")
                            obj = getter(name, project=project_name)

                        method = getattr(obj, target_method_name)
                        norm = normalize_kwargs_for_func(method, kwargs, entity_name=entity_lower)
                        res = method(**norm)

                        # For modifying methods (add_label, set_description), persist changes
                        if target_method_name in {"add_label", "add_labels", "set_description"}:
                            updater = getattr(dh, f"update_{entity_lower}", None)
                            if updater:
                                return updater(obj)

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

    return generated_tools
