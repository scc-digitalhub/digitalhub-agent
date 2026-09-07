from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
import digitalhub as dh


@tool
def new_dh_run(
    project: str,
    kind: str,
    task: Optional[str] = None,
    uuid: Optional[str] = None,
    labels: Optional[List[str]] = None,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Create a new Run entity in the backend.
    'kind' is the run kind (e.g. 'python+job:run', 'python+serve:run',
    'python+build:run', 'hera+pipeline:run', ...).
    'task' is the task string (URI). Kind-specific spec fields go inside 'extra_specs'.
    Typically runs are created indirectly via Function.run() / Workflow.run()
    (see run_dh_function, run_dh_workflow, and the runtime-specific helpers).
    Use new_dh_run only when you need to construct a Run explicitly.
    """
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    spec_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return dh.new_run(
        project=project,
        kind=kind,
        task=task,
        uuid=uuid,
        labels=labels,
        **spec_kwargs,
    )


@tool
def get_dh_run(
    identifier: str,
    project: Optional[str] = None,
):
    """
    Get a Run object from the backend.
    'identifier' can be an entity key (store://...) or the run ID.
    Note: runs are addressed by entity ID (not name); there is no 'entity_id'
    parameter and no 'get_run_versions' — runs are not versioned by name.
    """
    return dh.get_run(
        identifier=identifier,
        project=project,
    )


@tool
def import_dh_run(
    file: Optional[str] = None,
    key: Optional[str] = None,
    reset_id: bool = False,
    context: Optional[str] = None,
):
    """
    Import a run object from a YAML file or from a storage key.
    """
    return dh.import_run(
        file=file,
        key=key,
        reset_id=reset_id,
        context=context,
    )


@tool
def list_dh_runs(
    project: str,
    q: Optional[str] = None,
    name: Optional[str] = None,
    kind: Optional[str] = None,
    user: Optional[str] = None,
    state: Optional[str] = None,
    created: Optional[str] = None,
    updated: Optional[str] = None,
    function: Optional[str] = None,
    workflow: Optional[str] = None,
    task: Optional[str] = None,
    action: Optional[str] = None,
):
    """
    List latest runs of a project with optional filters.
    Runs support extra filters beyond the common ones: 'function' and 'workflow'
    filter by parent entity key, 'task' by task string, 'action' by action name.
    """
    return dh.list_runs(
        project=project,
        q=q,
        name=name,
        kind=kind,
        user=user,
        state=state,
        created=created,
        updated=updated,
        function=function,
        workflow=workflow,
        task=task,
        action=action,
    )


@tool
def update_dh_run(
    project: str,
    run_id: str,
):
    """
    Update a run object in the backend. Only metadata-level changes are applied.
    """
    run = dh.get_run(run_id, project=project)
    return dh.update_run(run)


@tool
def delete_dh_run(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None,
):
    """
    Delete a run from backend.
    Note: delete_run does NOT accept delete_all_versions or cascade.
    """
    return dh.delete_run(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
    )

@tool
def save_dh_run(
    project: str,
    run_id: str,
    update: bool = False,
):
    """
    Save or update the run entity into the backend.
    """
    run = dh.get_run(run_id, project=project)
    return run.save(update=update)


@tool
def refresh_dh_run(
    project: str,
    run_id: str,
):
    """
    Refresh run state from backend (poll for state/status changes).
    """
    run = dh.get_run(run_id, project=project)
    return run.refresh()


@tool
def export_dh_run(
    project: str,
    run_id: str,
):
    """
    Export the run object as a YAML file in the context folder.
    """
    run = dh.get_run(run_id, project=project)
    return run.export()


@tool
def start_dh_run(
    project: str,
    run_id: str,
):
    """
    Start the run (calls Run.run()). Use when a run was created but not yet
    executed (e.g. constructed via new_dh_run).
    """
    run = dh.get_run(run_id, project=project)
    return run.run()


@tool
def wait_dh_run(
    project: str,
    run_id: str,
    log_info: bool = True,
):
    """
    Wait synchronously for the run to finish. Returns the run object once terminal.
    """
    run = dh.get_run(run_id, project=project)
    return run.wait(log_info=log_info)


@tool
def stop_dh_run(
    project: str,
    run_id: str,
):
    """
    Stop the run.
    """
    run = dh.get_run(run_id, project=project)
    return run.stop()


@tool
def resume_dh_run(
    project: str,
    run_id: str,
):
    """
    Resume a previously stopped run.
    """
    run = dh.get_run(run_id, project=project)
    return run.resume()


@tool
def get_dh_run_logs(
    project: str,
    run_id: str,
):
    """
    Get run logs. Returns an empty list if none are present. For local
    executions, logs are also printed to the console.
    """
    run = dh.get_run(run_id, project=project)
    return run.logs()


@tool
def log_dh_run_metric(
    project: str,
    run_id: str,
    key: str,
    value: Any,
    overwrite: bool = False,
    single_value: bool = False,
):
    """
    Log a metric into the run's status.
    Default behaviour appends to any existing list for that key.
    Set single_value=True to store a scalar (not wrapped in a list).
    Set overwrite=True to replace any existing metric with that key.
    """
    run = dh.get_run(run_id, project=project)
    return run.log_metric(
        key=key,
        value=value,
        overwrite=overwrite,
        single_value=single_value,
    )


@tool
def log_dh_run_metrics(
    project: str,
    run_id: str,
    metrics: Dict[str, Any],
    overwrite: bool = False,
):
    """
    Log multiple metrics into the run's status in one call.
    List values are logged as lists; scalars as single values.
    """
    run = dh.get_run(run_id, project=project)
    return run.log_metrics(
        metrics=metrics,
        overwrite=overwrite,
    )

@tool
def get_dh_run_output(
    project: str,
    run_id: str,
    output_name: str,
    as_key: bool = False,
    as_dict: bool = False,
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
    as_dict: bool = False,
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
    result_name: str,
):
    """
    Get a run's result (primitive value) by name.
    """
    run = dh.get_run(run_id, project=project)
    return run.result(result_name)


@tool
def get_dh_run_results(
    project: str,
    run_id: str,
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
    request_kwargs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Invoke the HTTP endpoint of a served run (python+serve, modelserve, ...).
    Uses the service URL from the run status if 'url' is not specified.
    Method defaults to POST when 'json'/'data' are provided in request_kwargs, GET otherwise.
    Extra request options (json, data, headers, params, ...) go inside 'request_kwargs'.
    """
    run = dh.get_run(run_id, project=project)
    raw_req = request_kwargs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_req, dict):
        raw_req = {}
    req_kwargs = {k: v for k, v in raw_req.items() if k not in ("v__kwargs", "kwargs")}
    return run.invoke(method=method, url=url, **req_kwargs)


RUN_TOOLS = [
    new_dh_run,
    get_dh_run,
    import_dh_run,
    list_dh_runs,
    update_dh_run,
    delete_dh_run,
    save_dh_run,
    refresh_dh_run,
    export_dh_run,
    start_dh_run,
    wait_dh_run,
    stop_dh_run,
    resume_dh_run,
    get_dh_run_logs,
    log_dh_run_metric,
    log_dh_run_metrics,
    get_dh_run_output,
    get_dh_run_outputs,
    get_dh_run_result,
    get_dh_run_results,
    invoke_dh_run_service,
]
