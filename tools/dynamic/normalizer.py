"""
Argument normalizer for bridging LLM invocations and DigitalHub SDK signatures.
"""
import inspect
from typing import Any, Callable, Dict, Optional
import digitalhub as dh
from .schema_builder import unwrap_callable


def sync_entity_for_update(
    entity_type: str,
    normalized: Dict[str, Any],
) -> Optional[Any]:
    """
    Polymorphic entity updater:
    Locates and retrieves the target entity object from the SDK, applies
    any metadata updates (e.g. description, labels), and returns the updated object.
    Replaces repetitive per-entity conditional logic with clean reflection.
    """
    ent = entity_type.lower().rstrip("s")
    getter = getattr(dh, f"get_{ent}", None)
    if not getter:
        return None

    if ent == "project":
        name = normalized.pop("name", normalized.pop("identifier", normalized.pop("project_name", None)))
        if not name:
            return None
        obj = getter(name)
    elif ent == "run":
        r_id = normalized.pop("run_id", normalized.pop("identifier", normalized.pop("name", None)))
        proj = normalized.pop("project", normalized.pop("project_name", None))
        if not r_id:
            return None
        obj = getter(r_id, project=proj) if proj else getter(r_id)
    else:
        name = normalized.pop("name", normalized.pop("identifier", None))
        proj = normalized.pop("project", normalized.pop("project_name", None))
        if not name:
            return None
        obj = getter(name, project=proj) if proj else getter(name)

    if "description" in normalized:
        obj.set_description(normalized.pop("description"))
    if "labels" in normalized:
        obj.add_labels(normalized.pop("labels"))

    return obj


def normalize_kwargs_for_func(
    func: Callable,
    kwargs: Dict[str, Any],
    entity_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Intelligently adapt primitive caller arguments to SDK function expectations.
    Automates project_name/project and identifier/name mappings without hardcoded schemas.
    """
    real_func = unwrap_callable(func)
    sig = inspect.signature(real_func)
    params = sig.parameters
    normalized = dict(kwargs)

    # 0. Alias un-aliasing
    if "v_model_config" in normalized and "model_config" not in normalized:
        normalized["model_config"] = normalized.pop("v_model_config")

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
        obj = sync_entity_for_update(ent, normalized)
        if obj is not None:
            normalized["entity"] = obj

    # 4. Filter accepted arguments if function does not accept variable keyword arguments
    has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    if not has_var_kw:
        normalized = {k: v for k, v in normalized.items() if k in params}

    return normalized
