from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
import digitalhub as dh

@tool
def new_dh_workflow(
    project: str,
    name: str,
    kind: str = "hera",
    uuid: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    embedded: bool = False,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Create a Workflow instance in DigitalHub with the given parameters.
    Kind-specific spec fields (e.g. 'code_src', 'handler', 'code', 'base64', 'lang' for
    kind='hera') must be provided inside 'extra_specs'.
    """
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    spec_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return dh.new_workflow(
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
def get_dh_workflow(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None,
):
    """
    Get a Workflow object from the backend.

    'identifier' can be an entity key (store://...) or the workflow name.
    """
    return dh.get_workflow(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
    )


@tool
def get_dh_workflow_versions(
    identifier: str,
    project: Optional[str] = None,
):
    """
    Get all workflow version instances from the backend.
    """
    return dh.get_workflow_versions(
        identifier=identifier,
        project=project,
    )


@tool
def import_dh_workflow(
    file: Optional[str] = None,
    key: Optional[str] = None,
    reset_id: bool = False,
    context: Optional[str] = None,
):
    """
    Import a workflow object from a YAML file or from a storage key.
    """
    return dh.import_workflow(
        file=file,
        key=key,
        reset_id=reset_id,
        context=context,
    )


@tool
def list_dh_workflows(
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
    List latest-version workflow objects from backend for a project with optional filters.
    """
    return dh.list_workflows(
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
def update_dh_workflow(
    project_name: str,
    name: str,
):
    """
    Update a workflow object in the backend. Note that object specs are immutable.
    """
    wf = dh.get_workflow(name, project=project_name)
    return dh.update_workflow(wf)


@tool
def delete_dh_workflow(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None,
    delete_all_versions: bool = False,
    cascade: bool = True,
):
    """
    Delete a workflow object from backend.
    """
    return dh.delete_workflow(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        cascade=cascade,
    )


@tool
def save_dh_workflow(
    project_name: str,
    name: str,
    update: bool = False,
):
    """
    Save or update the workflow entity into the backend.
    """
    wf = dh.get_workflow(name, project=project_name)
    return wf.save(update=update)


@tool
def refresh_dh_workflow(
    project_name: str,
    name: str,
):
    """
    Refresh workflow state from backend.
    """
    wf = dh.get_workflow(name, project=project_name)
    return wf.refresh()


@tool
def export_dh_workflow(
    project_name: str,
    name: str,
):
    """
    Export workflow object as a YAML file in the context folder.
    """
    wf = dh.get_workflow(name, project=project_name)
    return wf.export()


@tool
def run_dh_workflow(
    project_name: str,
    name: str,
    action: str,
    wait: bool = False,
    log_info: bool = True,
    extensions: Optional[List[dict]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
):
    """
    Run a workflow. Creates a new run and executes it with the specified action.

    For the 'hera' kind, valid actions are:
      - 'build'    : compile the pipeline into Argo Workflows YAML (must be run first).
      - 'pipeline' : execute the compiled pipeline on Kubernetes.

    Task/run parameters (e.g. 'parameters', 'volumes', 'resources', 'envs',
    'secrets', 'profile') go inside 'kwargs'.
    """
    wf = dh.get_workflow(name, project=project_name)
    run_kwargs = kwargs or {}
    return wf.run(
        action=action,
        wait=wait,
        log_info=log_info,
        extensions=extensions,
        **run_kwargs,
    )


@tool
def build_dh_hera_workflow(
    project_name: str,
    name: str,
    volumes: Optional[List[dict]] = None,
    resources: Optional[dict] = None,
    envs: Optional[List[dict]] = None,
    secrets: Optional[List[str]] = None,
    profile: Optional[str] = None,
    wait: bool = True,
    log_info: bool = True,
):
    """
    Compile a Hera workflow into Argo Workflows YAML (action='build').
    Must be executed at least once before invoking 'pipeline'.
    """
    wf = dh.get_workflow(name, project=project_name)
    return wf.run(
        action="build",
        wait=wait,
        log_info=log_info,
        volumes=volumes,
        resources=resources,
        envs=envs,
        secrets=secrets,
        profile=profile,
    )


@tool
def run_dh_hera_pipeline(
    project_name: str,
    name: str,
    parameters: Optional[dict] = None,
    volumes: Optional[List[dict]] = None,
    resources: Optional[dict] = None,
    envs: Optional[List[dict]] = None,
    secrets: Optional[List[str]] = None,
    profile: Optional[str] = None,
    wait: bool = True,
    log_info: bool = True,
):
    """
    Execute a previously-built Hera pipeline on Kubernetes (action='pipeline').
    'parameters' are the pipeline input values (matching the Hera Workflow Parameters).
    """
    wf = dh.get_workflow(name, project=project_name)
    return wf.run(
        action="pipeline",
        wait=wait,
        log_info=log_info,
        parameters=parameters,
        volumes=volumes,
        resources=resources,
        envs=envs,
        secrets=secrets,
        profile=profile,
    )


@tool
def list_dh_workflow_tasks(
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
    List tasks of the workflow from backend.
    """
    wf = dh.get_workflow(name, project=project_name)
    return wf.list_task(
        q=q,
        name=task_name,
        kind=kind,
        user=user,
        state=state,
        created=created,
        updated=updated,
    )


@tool
def get_dh_workflow_task(
    project_name: str,
    name: str,
    action: str,
):
    """
    Get workflow task by action name (e.g. 'build', 'pipeline').
    """
    wf = dh.get_workflow(name, project=project_name)
    return wf.get_task(action)


@tool
def new_dh_workflow_task(
    project_name: str,
    name: str,
    action: str,
    kwargs: Optional[Dict[str, Any]] = None,
):
    """
    Create a new workflow task. If the task already exists, it is updated.
    """
    wf = dh.get_workflow(name, project=project_name)
    task_kwargs = kwargs or {}
    return wf.new_task(action, **task_kwargs)


@tool
def update_dh_workflow_task(
    project_name: str,
    name: str,
    action: str,
    kwargs: Optional[Dict[str, Any]] = None,
):
    """
    Update a workflow task by action name.
    """
    wf = dh.get_workflow(name, project=project_name)
    task_kwargs = kwargs or {}
    return wf.update_task(action, **task_kwargs)


@tool
def trigger_dh_workflow(
    project_name: str,
    name: str,
    action: str,
    kind: str,
    trigger_name: str,
    template: Optional[Dict[str, Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
):
    """
    Trigger workflow execution on a schedule or event.
    """
    wf = dh.get_workflow(name, project=project_name)
    trig_kwargs = kwargs or {}
    return wf.trigger(
        action=action,
        kind=kind,
        name=trigger_name,
        template=template,
        **trig_kwargs,
    )


@tool
def list_dh_workflow_triggers(
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
    List triggers of the workflow from backend.
    """
    wf = dh.get_workflow(name, project=project_name)
    return wf.list_triggers(
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
def get_dh_workflow_trigger(
    project_name: str,
    name: str,
    identifier: str,
):
    """
    Get a workflow trigger by identifier (entity key or trigger ID).
    """
    wf = dh.get_workflow(name, project=project_name)
    return wf.get_trigger(identifier)


WORKFLOW_TOOLS = [
    new_dh_workflow,
    get_dh_workflow,
    get_dh_workflow_versions,
    import_dh_workflow,
    list_dh_workflows,
    update_dh_workflow,
    delete_dh_workflow,
    save_dh_workflow,
    refresh_dh_workflow,
    export_dh_workflow,
    run_dh_workflow,
    build_dh_hera_workflow,
    run_dh_hera_pipeline,
    list_dh_workflow_tasks,
    get_dh_workflow_task,
    new_dh_workflow_task,
    update_dh_workflow_task,
    trigger_dh_workflow,
    list_dh_workflow_triggers,
    get_dh_workflow_trigger,
]
