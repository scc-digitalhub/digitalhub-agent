"""
Schema builder and reflection utilities for dynamically generating Pydantic validation models.
"""
import inspect
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field, create_model


def parse_numpy_docstring(doc: Optional[str]) -> Dict[str, str]:
    """
    Industry-standard NumPy-style docstring parser (numpydoc / PEP 257).
    Extracts parameter names and descriptions strictly from the 'Parameters' section.
    """
    if not doc:
        return {}
    cleaned = inspect.cleandoc(doc)
    params: Dict[str, str] = {}

    in_params_section = False
    current_param: Optional[str] = None
    desc_buffer: List[str] = []

    for line in cleaned.splitlines():
        trimmed = line.strip()
        if not trimmed:
            continue
        # Detect section header
        if trimmed in ("Parameters", "Args", "Arguments"):
            in_params_section = True
            continue
        if in_params_section and (trimmed.startswith("---") or trimmed.startswith("===")):
            continue
        # Exit section when reaching subsequent section headers
        if in_params_section and trimmed in (
            "Returns",
            "Raises",
            "Yields",
            "Examples",
            "Notes",
            "See Also",
            "References",
            "Attributes",
        ):
            if current_param and desc_buffer:
                params[current_param] = " ".join(desc_buffer)
            break

        if in_params_section:
            # In clean numpydoc, parameter definition lines start with zero indentation
            m = re.match(r"^(\*{0,2}[a-zA-Z0-9_]+)\s*:\s*(.*)$", line)
            if m:
                if current_param and desc_buffer:
                    params[current_param] = " ".join(desc_buffer)
                    desc_buffer = []
                current_param = m.group(1).lstrip("*")
            elif current_param and line.startswith((" ", "\t")):
                desc_buffer.append(trimmed)

    if current_param and desc_buffer:
        params[current_param] = " ".join(desc_buffer)

    return params


# Backward-compatible alias
parse_param_descriptions = parse_numpy_docstring


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
    docstring: Optional[str] = None,
) -> type[BaseModel]:
    """
    Dynamically construct a validated Pydantic schema directly from inspect.Signature.
    Parses NumPy docstrings to inject Field(description=...) metadata for LLM tool clarity.
    """
    doc_descriptions = parse_numpy_docstring(docstring)
    fields: Dict[str, Tuple[Any, Any]] = {}

    # Handle injected parameters
    if injected_params:
        for p_name, p_spec in injected_params.items():
            desc = doc_descriptions.get(p_name)
            p_type, p_default = p_spec
            if isinstance(p_default, Field.__class__):
                fields[p_name] = p_spec
            elif desc:
                if p_default is ...:
                    fields[p_name] = (p_type, Field(..., description=desc))
                else:
                    fields[p_name] = (p_type, Field(default=p_default, description=desc))
            else:
                fields[p_name] = p_spec

    skip = skip_params or set()
    for param_name, param in sig.parameters.items():
        if param_name in skip or param_name in fields or param_name.startswith("*"):
            continue
        if param_name in {"setup_kwargs", "extensions", "config", "self"}:
            continue

        resolved = resolve_type_annotation(param.annotation)
        default_val = ... if param.default == inspect.Parameter.empty else param.default
        desc = doc_descriptions.get(param_name)

        field_kwargs: Dict[str, Any] = {}
        if desc:
            field_kwargs["description"] = desc

        if param_name == "model_config":
            field_kwargs.update({"alias": "model_config", "validation_alias": "model_config"})
            fields["v_model_config"] = (
                resolved,
                Field(default=default_val, **field_kwargs),
            )
        else:
            if default_val is ...:
                fields[param_name] = (resolved, Field(..., **field_kwargs) if field_kwargs else ...)
            else:
                fields[param_name] = (
                    resolved,
                    Field(default=default_val, **field_kwargs) if field_kwargs else default_val,
                )

    return create_model(schema_name, **fields)
