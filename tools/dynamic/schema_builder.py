"""
Schema builder and reflection utilities for dynamically generating Pydantic validation models.
"""
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field, create_model


def unwrap_callable(func: Callable) -> Callable:
    """
    Recursively unwrap decorators and closure cells to extract the underlying
    callable signature and docstring.
    """
    if hasattr(func, "__wrapped__") and callable(func.__wrapped__):
        return unwrap_callable(func.__wrapped__)
    if hasattr(func, "__closure__") and func.__closure__:
        for cell in func.__closure__:
            if callable(cell.cell_contents):
                inner = cell.cell_contents
                if hasattr(inner, "__code__") and inner.__name__ != "wrapper":
                    return unwrap_callable(inner)
    return func


def resolve_type_annotation(ann: Any) -> Any:
    """
    Resolve type annotations into valid Python/typing types.
    Gracefully handles string-encoded annotations and missing hints.
    """
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


def build_dynamic_pydantic_schema(
    schema_name: str,
    sig: inspect.Signature,
    skip_params: Optional[Set[str]] = None,
    injected_params: Optional[Dict[str, Tuple[Any, Any]]] = None,
) -> type[BaseModel]:
    """
    Dynamically construct a validated Pydantic schema directly from inspect.Signature.
    Handles reserved Pydantic keyword aliasing (e.g. model_config).
    """
    fields: Dict[str, Tuple[Any, Any]] = {}
    if injected_params:
        fields.update(injected_params)

    skip = skip_params or set()
    for param_name, param in sig.parameters.items():
        if param_name in skip or param_name in fields or param_name.startswith("*"):
            continue
        if param_name in {"setup_kwargs", "extensions", "config", "self"}:
            continue

        resolved = resolve_type_annotation(param.annotation)
        default_val = ... if param.default == inspect.Parameter.empty else param.default

        if param_name == "model_config":
            fields["v_model_config"] = (
                resolved,
                Field(default=default_val, alias="model_config", validation_alias="model_config"),
            )
        else:
            fields[param_name] = (resolved, default_val)

    return create_model(schema_name, **fields)
