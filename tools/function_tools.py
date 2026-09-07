from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
import digitalhub as dh


@tool
def new_dh_function(
    project: str,
    name: str,
    kind: str = "python",
    uuid: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    embedded: bool = False,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Create a Function entity in DigitalHub with the given parameters.
    Kind-specific spec fields (e.g. 'code_src', 'handler', 'python_version',
    'requirements' for kind='python') go inside 'extra_specs'.
    """
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    spec_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return dh.new_function(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        **spec_kwargs,
    )


@tool
def get_dh_function(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None,
):
    """
    Get a Function object from the backend.
    'identifier' can be an entity key (store://...) or the function name.
    """
    return dh.get_function(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
    )


@tool
def get_dh_function_versions(
    identifier: str,
    project: Optional[str] = None,
):
    """
    Get all function version instances from the backend.
    """
    return dh.get_function_versions(
        identifier=identifier,
        project=project,
    )


@tool
def import_dh_function(
    file: Optional[str] = None,
    key: Optional[str] = None,
    reset_id: bool = False,
    context: Optional[str] = None,
):
    """
    Import a function object from a YAML file or from a storage key.
    """
    return dh.import_function(
        file=file,
        key=key,
        reset_id=reset_id,
        context=context,
    )


@tool
def list_dh_functions(
    project: str,
    q: Optional[str] = None,
    name: Optional[str] = None,
    kind: Optional[str] = None,
    user: Optional[str] = None,
    state: Optional[str] = None,
    created: Optional[str] = None,
    updated: Optional[str] = None,
    versions: Optional[str] = None,
):
    """
    List latest-version function objects from backend for a project with optional filters.
    """
    return dh.list_functions(
        project=project,
        q=q,
        name=name,
        kind=kind,
        user=user,
        state=state,
        created=created,
        updated=updated,
        versions=versions,
    )


@tool
def update_dh_function(
    project_name: str,
    name: str,
):
    """
    Update a function object in the backend. Note that object specs are immutable.
    """
    fn = dh.get_function(name, project=project_name)
    return dh.update_function(fn)


@tool
def delete_dh_function(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None,
    delete_all_versions: bool = False,
    cascade: bool = True,
):
    """
    Delete a function object from backend.
    """
    return dh.delete_function(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        cascade=cascade,
    )


@tool
def save_dh_function(
    project_name: str,
    name: str,
    update: bool = False,
):
    """
    Save or update the function entity into the backend.
    """
    fn = dh.get_function(name, project=project_name)
    return fn.save(update=update)


@tool
def refresh_dh_function(
    project_name: str,
    name: str,
):
    """
    Refresh function state from backend.
    """
    fn = dh.get_function(name, project=project_name)
    return fn.refresh()


@tool
def export_dh_function(
    project_name: str,
    name: str,
):
    """
    Export function object as a YAML file in the context folder.
    """
    fn = dh.get_function(name, project=project_name)
    return fn.export()

@tool
def run_dh_function(
    project_name: str,
    name: str,
    action: str,
    wait: bool = False,
    log_info: bool = True,
    extensions: Optional[List[dict]] = None,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Run function. Creates a new Run and executes the specified action.
    Valid actions depend on the function kind (e.g. 'job', 'serve', 'build' for
    kind='python'; 'transform' for kind='dbt'; etc.). Task/run parameters
    ('inputs', 'parameters', 'volumes', 'resources', 'envs', 'secrets',
    'profile', kind-specific fields) go inside 'extra_specs'.
    For the python runtime, prefer the specialized wrappers in python_runtime_tools:
    run_dh_python_job, run_dh_python_serve, run_dh_python_build.
    """
    fn = dh.get_function(name, project=project_name)
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    run_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return fn.run(
        action=action,
        wait=wait,
        log_info=log_info,
        extensions=extensions,
        **run_kwargs,
    )

@tool
def list_dh_function_tasks(
    project_name: str,
    name: str,
    q: Optional[str] = None,
    task_name: Optional[str] = None,
    kind: Optional[str] = None,
    user: Optional[str] = None,
    state: Optional[str] = None,
    created: Optional[str] = None,
    updated: Optional[str] = None,
):
    """
    List tasks of the function from backend.
    """
    fn = dh.get_function(name, project=project_name)
    return fn.list_task(
        q=q,
        name=task_name,
        kind=kind,
        user=user,
        state=state,
        created=created,
        updated=updated,
    )


@tool
def get_dh_function_task(
    project_name: str,
    name: str,
    action: str,
):
    """
    Get function task by action name (e.g. 'job', 'serve', 'build').
    """
    fn = dh.get_function(name, project=project_name)
    return fn.get_task(action)


@tool
def new_dh_function_task(
    project_name: str,
    name: str,
    action: str,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Create a new function task. If the task already exists, it is updated.
    """
    fn = dh.get_function(name, project=project_name)
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    task_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return fn.new_task(action, **task_kwargs)


@tool
def update_dh_function_task(
    project_name: str,
    name: str,
    action: str,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Update a function task by action name.
    """
    fn = dh.get_function(name, project=project_name)
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    task_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return fn.update_task(action, **task_kwargs)


@tool
def trigger_dh_function(
    project_name: str,
    name: str,
    action: str,
    kind: str,
    trigger_name: str,
    template: Optional[Dict[str, Any]] = None,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Trigger function execution on a schedule or event.
    """
    fn = dh.get_function(name, project=project_name)
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    trig_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return fn.trigger(
        action=action,
        kind=kind,
        name=trigger_name,
        template=template,
        **trig_kwargs,
    )


@tool
def list_dh_function_triggers(
    project_name: str,
    name: str,
    q: Optional[str] = None,
    trigger_name: Optional[str] = None,
    kind: Optional[str] = None,
    user: Optional[str] = None,
    created: Optional[str] = None,
    updated: Optional[str] = None,
    versions: Optional[str] = None,
    task: Optional[str] = None,
):
    """
    List triggers of the function from backend.
    """
    fn = dh.get_function(name, project=project_name)
    return fn.list_triggers(
        q=q,
        name=trigger_name,
        kind=kind,
        user=user,
        created=created,
        updated=updated,
        versions=versions,
        task=task,
    )


@tool
def get_dh_function_trigger(
    project_name: str,
    name: str,
    identifier: str,
):
    """
    Get a function trigger by identifier (entity key or trigger ID).
    """
    fn = dh.get_function(name, project=project_name)
    return fn.get_trigger(identifier)


FUNCTION_TOOLS = [
    new_dh_function,
    get_dh_function,
    get_dh_function_versions,
    import_dh_function,
    list_dh_functions,
    update_dh_function,
    delete_dh_function,
    save_dh_function,
    refresh_dh_function,
    export_dh_function,
    run_dh_function,
    list_dh_function_tasks,
    get_dh_function_task,
    new_dh_function_task,
    update_dh_function_task,
    trigger_dh_function,
    list_dh_function_triggers,
    get_dh_function_trigger,
]
