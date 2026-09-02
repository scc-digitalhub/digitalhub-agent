from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
import digitalhub as dh


# ==============================================================================
# 1. Trigger CRUD Tools
# ==============================================================================

@tool
def new_dh_trigger(
    project: str,
    name: str,
    kind: str,
    task: str,
    function: Optional[str] = None,
    workflow: Optional[str] = None,
    uuid: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    embedded: bool = False,
    kwargs: Optional[Dict[str, Any]] = None,
):
    """
    Create a Trigger instance in DigitalHub with the given parameters.

    Kinds:
      - 'scheduler'  : time-based (cron) trigger; provide 'schedule' via kwargs.
      - 'lifecycle'  : event-based trigger reacting to entity state changes;
                       provide 'key' and 'states' via kwargs.

    Identifier formats:
      - task     : "<task-kind>://<project>/<task-id>"
      - function : "<function-kind>://<project>/<function-name>:<function-id>"
      - workflow : "<workflow-kind>://<project>/<workflow-name>:<workflow-id>"

    Provide exactly one of 'function' or 'workflow' as the execution target.
    Kind-specific spec fields (schedule / key / states / template) go inside 'kwargs'.
    """
    spec_kwargs = kwargs or {}
    return dh.new_trigger(
        project=project,
        name=name,
        kind=kind,
        task=task,
        function=function,
        workflow=workflow,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        **spec_kwargs,
    )


@tool
def get_dh_trigger(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None,
):
    """
    Get a Trigger object from the backend.

    'identifier' can be an entity key (store://...) or the trigger name.
    """
    return dh.get_trigger(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
    )


@tool
def import_dh_trigger(
    file: Optional[str] = None,
    key: Optional[str] = None,
    reset_id: bool = False,
    context: Optional[str] = None,
):
    """
    Import a trigger object from a YAML file or from a storage key.
    """
    return dh.import_trigger(
        file=file,
        key=key,
        reset_id=reset_id,
        context=context,
    )


@tool
def list_dh_triggers(
    project: str,
    q: Optional[str] = None,
    name: Optional[str] = None,
    kind: Optional[str] = None,
    user: Optional[str] = None,
    state: Optional[str] = None,
    created: Optional[str] = None,
    updated: Optional[str] = None,
    versions: Optional[str] = None,
    task: Optional[str] = None,
):
    """
    List latest-version trigger objects from backend for a project with optional filters.
    """
    return dh.list_triggers(
        project=project,
        q=q,
        name=name,
        kind=kind,
        user=user,
        state=state,
        created=created,
        updated=updated,
        versions=versions,
        task=task,
    )


@tool
def update_dh_trigger(
    project_name: str,
    name: str,
):
    """
    Update a trigger object in the backend. Note that object specs are immutable.
    """
    trg = dh.get_trigger(name, project=project_name)
    return dh.update_trigger(trg)


@tool
def delete_dh_trigger(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None,
    delete_all_versions: bool = False,
):
    """
    Delete a trigger object from backend.
    """
    return dh.delete_trigger(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
    )


# ==============================================================================
# 2. Trigger Object Methods (save / refresh / export / stop)
# ==============================================================================

@tool
def save_dh_trigger(
    project_name: str,
    name: str,
    update: bool = False,
):
    """
    Save or update the trigger entity into the backend.
    """
    trg = dh.get_trigger(name, project=project_name)
    return trg.save(update=update)


@tool
def refresh_dh_trigger(
    project_name: str,
    name: str,
):
    """
    Refresh trigger state from backend.
    """
    trg = dh.get_trigger(name, project=project_name)
    return trg.refresh()


@tool
def export_dh_trigger(
    project_name: str,
    name: str,
):
    """
    Export trigger object as a YAML file in the context folder.
    """
    trg = dh.get_trigger(name, project=project_name)
    return trg.export()


@tool
def stop_dh_trigger(
    project_name: str,
    name: str,
):
    """
    Stop an active trigger (deactivate its schedule/event subscription).
    """
    trg = dh.get_trigger(name, project=project_name)
    return trg.stop()


# ==============================================================================
# 3. Specialized Kind Wrappers for Convenience
# ==============================================================================

@tool
def new_dh_scheduler_trigger(
    project: str,
    name: str,
    task: str,
    schedule: str,
    function: Optional[str] = None,
    workflow: Optional[str] = None,
    template: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    embedded: bool = False,
):
    """
    Create a scheduler (cron) trigger that runs a task on a schedule.

    'schedule' is a Quartz cron expression (e.g. '0 0 * * * ?' for daily at midnight).
    Provide exactly one of 'function' or 'workflow' as the execution target.
    'template' optionally configures run parameters/inputs.
    """
    spec_kwargs: Dict[str, Any] = {"schedule": schedule}
    if template is not None:
        spec_kwargs["template"] = template
    return dh.new_trigger(
        project=project,
        name=name,
        kind="scheduler",
        task=task,
        function=function,
        workflow=workflow,
        description=description,
        labels=labels,
        embedded=embedded,
        **spec_kwargs,
    )


@tool
def new_dh_lifecycle_trigger(
    project: str,
    name: str,
    task: str,
    key: str,
    states: List[str],
    function: Optional[str] = None,
    workflow: Optional[str] = None,
    template: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    embedded: bool = False,
):
    """
    Create a lifecycle trigger that reacts to entity state changes.

    'key' is the store URI to monitor (e.g. 'store://project/artifact/*'; wildcards allowed).
    'states' is the list of states that trigger execution (e.g. ['READY']).
    Provide exactly one of 'function' or 'workflow' as the execution target.
    'template' optionally configures run parameters/inputs — values may reference
    the source event, e.g. {"inputs": {"my-param": "{{input.key}}"}}.
    """
    spec_kwargs: Dict[str, Any] = {"key": key, "states": states}
    if template is not None:
        spec_kwargs["template"] = template
    return dh.new_trigger(
        project=project,
        name=name,
        kind="lifecycle",
        task=task,
        function=function,
        workflow=workflow,
        description=description,
        labels=labels,
        embedded=embedded,
        **spec_kwargs,
    )


TRIGGER_TOOLS = [
    # 1. Trigger CRUD
    new_dh_trigger,
    get_dh_trigger,
    import_dh_trigger,
    list_dh_triggers,
    update_dh_trigger,
    delete_dh_trigger,
    # 2. Trigger Methods
    save_dh_trigger,
    refresh_dh_trigger,
    export_dh_trigger,
    stop_dh_trigger,
    # 3. Kind wrappers
    new_dh_scheduler_trigger,
    new_dh_lifecycle_trigger,
]
