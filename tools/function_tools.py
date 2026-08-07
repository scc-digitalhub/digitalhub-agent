from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
import digitalhub as dh


# ==============================================================================
# 1.  Function CRUD Tools 
# ==============================================================================

@tool
def new_dh_function(
    project: str,
    name: str,
    kind: str = "python",
    uuid: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    embedded: bool = False,
    kwargs: Optional[Dict[str, Any]] = None,
    **extra_kwargs
):
    """
    Create a Function instance in DigitalHub with the given parameters.
    """
    spec_kwargs = kwargs or {}
    return dh.new_function(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        **spec_kwargs
    )


@tool
def get_dh_function(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None
):
    """
    Get a Function object from the backend.
    """
    return dh.get_function(
        identifier=identifier,
        project=project,
        entity_id=entity_id
    )


@tool
def get_dh_function_versions(
    identifier: str,
    project: Optional[str] = None
):
    """
    Get all function version instances from the backend.
    """
    return dh.get_function_versions(
        identifier=identifier,
        project=project
    )


@tool
def import_dh_function(
    file: Optional[str] = None,
    key: Optional[str] = None,
    reset_id: bool = False,
    context: Optional[str] = None
):
    """
    Import a function object from a YAML file or from a storage key.
    """
    return dh.import_function(
        file=file,
        key=key,
        reset_id=reset_id,
        context=context
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
    versions: Optional[str] = None
):
    """
    List all latest version function objects from backend for a project with optional filters.
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
        versions=versions
    )


@tool
def update_dh_function(
    project_name: str,
    name: str
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
    cascade: bool = True
):
    """
    Delete a function object from backend.
    """
    return dh.delete_function(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        cascade=cascade
    )


# ==============================================================================
# 2. Function  Methods
# ==============================================================================

@tool
def save_dh_function(
    project_name: str,
    name: str,
    update: bool = False
):
    """
    Save or update the entity into the backend.
    """
    fn = dh.get_function(name, project=project_name)
    return fn.save(update=update)


@tool
def refresh_dh_function(
    project_name: str,
    name: str
):
    """
    Refresh object state from backend.
    """
    fn = dh.get_function(name, project=project_name)
    return fn.refresh()


@tool
def export_dh_function(
    project_name: str,
    name: str
):
    """
    Export object as a YAML file in the context folder.
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
    kwargs: Optional[Dict[str, Any]] = None
):
    """
    Run function. Creates a new run and executes it with specified action ('job', 'build' or 'serve').
    """
    fn = dh.get_function(name, project=project_name)
    run_kwargs = kwargs or {}
    return fn.run(
        action=action,
        wait=wait,
        log_info=log_info,
        extensions=extensions,
        **run_kwargs
    )


# Specialized Python Action Wrappers forConvenience

@tool
def run_dh_python_job(
    project_name: str,
    name: str,
    local_execution: bool = False,
    inputs: Optional[dict] = None,
    parameters: Optional[dict] = None,
    init_parameters: Optional[dict] = None,
    volumes: Optional[List[dict]] = None,
    resources: Optional[dict] = None,
    envs: Optional[List[dict]] = None,
    secrets: Optional[List[str]] = None,
    profile: Optional[str] = None,
    wait: bool = True,
    log_info: bool = True,
):
    """
    Run a Python function as a one-off batch job (action='job').
    """
    func = dh.get_function(name, project=project_name)
    return func.run(
        action="job",
        wait=wait,
        log_info=log_info,
        local_execution=local_execution,
        inputs=inputs,
        parameters=parameters,
        init_parameters=init_parameters,
        volumes=volumes,
        resources=resources,
        envs=envs,
        secrets=secrets,
        profile=profile,
    )


@tool
def run_dh_python_build(
    project_name: str,
    name: str,
    instructions: Optional[List[str]] = None,
    volumes: Optional[List[dict]] = None,
    resources: Optional[dict] = None,
    envs: Optional[List[dict]] = None,
    secrets: Optional[List[str]] = None,
    profile: Optional[str] = None,
    inputs: Optional[dict] = None,
    parameters: Optional[dict] = None,
    init_parameters: Optional[dict] = None,
    wait: bool = True,
    log_info: bool = True,
):
    """
    Build a container image for a Python function (action='build').
    'instructions' are executed as RUN lines in the generated Dockerfile.
    """
    func = dh.get_function(name, project=project_name)
    return func.run(
        action="build",
        wait=wait,
        log_info=log_info,
        instructions=instructions,
        volumes=volumes,
        resources=resources,
        envs=envs,
        secrets=secrets,
        profile=profile,
        inputs=inputs,
        parameters=parameters,
        init_parameters=init_parameters,
    )


@tool
def run_dh_python_serve(
    project_name: str,
    name: str,
    inputs: Optional[dict] = None,
    parameters: Optional[dict] = None,
    init_parameters: Optional[dict] = None,
    wait: bool = True,
    log_info: bool = True,
    replicas: Optional[int] = None,
    service_type: Optional[str] = None,
    service_name: Optional[str] = None,
    volumes: Optional[List[dict]] = None,
    resources: Optional[dict] = None,
    envs: Optional[List[dict]] = None,
    secrets: Optional[List[str]] = None,
    profile: Optional[str] = None,
):
    """
    Deploy a Python function as a HTTP service endpoint (action='serve').
    """
    func = dh.get_function(name, project=project_name)
    return func.run(
        action="serve",
        wait=wait,
        log_info=log_info,
        inputs=inputs,
        parameters=parameters,
        init_parameters=init_parameters,
        replicas=replicas,
        service_type=service_type,
        service_name=service_name,
        volumes=volumes,
        resources=resources,
        envs=envs,
        secrets=secrets,
        profile=profile,
    )


# ==============================================================================
# 3. Tasks Methods
# ==============================================================================

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
    updated: Optional[str] = None
):
    """
    List tasks of the executable entity from backend.
    """
    fn = dh.get_function(name, project=project_name)
    return fn.list_task(
        q=q,
        name=task_name,
        kind=kind,
        user=user,
        state=state,
        created=created,
        updated=updated
    )


@tool
def get_dh_function_task(
    project_name: str,
    name: str,
    action: str
):
    """
    Get task by action name.
    """
    fn = dh.get_function(name, project=project_name)
    return fn.get_task(action)


@tool
def new_dh_function_task(
    project_name: str,
    name: str,
    action: str,
    kwargs: Optional[Dict[str, Any]] = None
):
    """
    Create new task. If task already exists, update it.
    """
    fn = dh.get_function(name, project=project_name)
    task_kwargs = kwargs or {}
    return fn.new_task(action, **task_kwargs)


@tool
def update_dh_function_task(
    project_name: str,
    name: str,
    action: str,
    kwargs: Optional[Dict[str, Any]] = None
):
    """
    Update task.
    """
    fn = dh.get_function(name, project=project_name)
    task_kwargs = kwargs or {}
    return fn.update_task(action, **task_kwargs)


# ==============================================================================
# 4. Triggers Methods
# ==============================================================================

@tool
def trigger_dh_function(
    project_name: str,
    name: str,
    action: str,
    kind: str,
    trigger_name: str,
    template: Optional[Dict[str, Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None
):
    """
    Trigger function execution on a schedule or event.
    """
    fn = dh.get_function(name, project=project_name)
    trig_kwargs = kwargs or {}
    return fn.trigger(
        action=action,
        kind=kind,
        name=trigger_name,
        template=template,
        **trig_kwargs
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
    task: Optional[str] = None
):
    """
    List triggers of the executable entity from backend.
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
        task=task
    )


@tool
def get_dh_function_trigger(
    project_name: str,
    name: str,
    identifier: str
):
    """
    Get trigger object from backend.
    """
    fn = dh.get_function(name, project=project_name)
    return fn.get_trigger(identifier)


# ==============================================================================
# 5. Run Methods 
# ==============================================================================

@tool
def get_dh_run_output(
    project: str,
    run_id: str,
    output_name: str,
    as_key: bool = False,
    as_dict: bool = False
):
    """
    Get a run's output by name. Returns the entity, its key, or a dict representation.
    """
    run = dh.get_run(run_id, project=project)
    return run.output(output_name, as_key=as_key, as_dict=as_dict)


@tool
def get_dh_run_outputs(
    project: str,
    run_id: str,
    as_key: bool = False,
    as_dict: bool = False
):
    """
    Get all of a run's outputs. Returns a dict of output objects, keys, or dicts.
    """
    run = dh.get_run(run_id, project=project)
    return run.outputs(as_key=as_key, as_dict=as_dict)


@tool
def get_dh_run_result(
    project: str,
    run_id: str,
    result_name: str
):
    """
    Get a run's result (primitive value) by name.
    """
    run = dh.get_run(run_id, project=project)
    return run.result(result_name)


@tool
def get_dh_run_results(
    project: str,
    run_id: str
):
    """
    Get all of a run's results (primitive values).
    """
    run = dh.get_run(run_id, project=project)
    return run.results()


@tool
def invoke_dh_run_service(
    project: str,
    run_id: str,
    method: str = "POST",
    url: Optional[str] = None,
    **kwargs,
):
    """
    Invoke the HTTP endpoint of a served function run.
    Uses the service URL from the run status if no url is specified.
    Defaults to POST if json or data is provided, GET otherwise.
    Returns the response status code and body.
    """
    run = dh.get_run(run_id, project=project)
    return run.invoke(method=method, url=url, **kwargs)


FUNCTION_TOOLS = [
    # 1. Function CRUD
    new_dh_function,
    get_dh_function,
    get_dh_function_versions,
    import_dh_function,
    list_dh_functions,
    update_dh_function,
    delete_dh_function,
    # 2. Function Methods
    save_dh_function,
    refresh_dh_function,
    export_dh_function,
    run_dh_function,
    run_dh_python_job,
    run_dh_python_build,
    run_dh_python_serve,
    # 3. Tasks
    list_dh_function_tasks,
    get_dh_function_task,
    new_dh_function_task,
    update_dh_function_task,
    # 4. Triggers
    trigger_dh_function,
    list_dh_function_triggers,
    get_dh_function_trigger,
    # 5. Runs
    get_dh_run_output,
    get_dh_run_outputs,
    get_dh_run_result,
    get_dh_run_results,
    invoke_dh_run_service,
]
