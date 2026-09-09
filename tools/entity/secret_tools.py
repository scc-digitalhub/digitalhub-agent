from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
import digitalhub as dh

@tool
def new_dh_secret(
    project: str,
    name: str,
    secret_value: str,
    uuid: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    embedded: bool = False,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Create a new Secret entity in DigitalHub.

    Stores a sensitive key/value pair (e.g. external API credentials, storage
    credentials) in the project's underlying secret manager (Kubernetes Secret Manager).
    
    'secret_value' is required by the SDK; secrets cannot be created without a value.
    'name' must follow lowercase kebab-case (e.g. 'my-api-key').
    """
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    spec_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return dh.new_secret(
        project=project,
        name=name,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        secret_value=secret_value,
        **spec_kwargs,
    )


@tool
def get_dh_secret(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None,
):
    """
    Get a Secret object from the backend.

    'identifier' can be an entity key (store://...) or the secret name.
    Note: this returns the entity metadata; use read_dh_secret_value to fetch
    the actual sensitive value.
    """
    return dh.get_secret(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
    )

@tool
def import_dh_secret(
    file: Optional[str] = None,
    key: Optional[str] = None,
    reset_id: bool = False,
    context: Optional[str] = None,
):
    """
    Import a secret object from a YAML file or from a storage key.
    """
    return dh.import_secret(
        file=file,
        key=key,
        reset_id=reset_id,
        context=context,
    )


@tool
def list_dh_secrets(project: str):
    """
    List latest-version secret objects from backend for a project.
    """
    return dh.list_secrets(project=project)


@tool
def update_dh_secret(
    project_name: str,
    name: str,
):
    """
    Update a secret object in the backend. Note that object specs are immutable;
    use set_dh_secret_value to change the stored value.
    """
    sec = dh.get_secret(name, project=project_name)
    return dh.update_secret(sec)


@tool
def delete_dh_secret(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None,
    delete_all_versions: bool = False,
):
    """
    Delete a secret object from backend. The underlying key/value is also
    removed from the project's secret store.
    """
    return dh.delete_secret(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
    )


@tool
def save_dh_secret(
    project_name: str,
    name: str,
    update: bool = False,
):
    """
    Save or update the secret entity into the backend.
    """
    sec = dh.get_secret(name, project=project_name)
    return sec.save(update=update)


@tool
def refresh_dh_secret(
    project_name: str,
    name: str,
):
    """
    Refresh secret state from backend.
    """
    sec = dh.get_secret(name, project=project_name)
    return sec.refresh()


@tool
def export_dh_secret(
    project_name: str,
    name: str,
):
    """
    Export secret object as a YAML file in the context folder.
    The exported YAML contains metadata only, not the sensitive value.
    """
    sec = dh.get_secret(name, project=project_name)
    return sec.export()


@tool
def set_dh_secret_value(
    project_name: str,
    name: str,
    value: str,
):
    """
    Update the secret's stored value in the project's secret manager.
    Overwrites any previous value for the same key.
    """
    sec = dh.get_secret(name, project=project_name)
    return sec.set_secret_value(value=value)


@tool
def read_dh_secret_value(
    project_name: str,
    name: str,
):
    """
    Read the secret's value from the backend secret manager.
    Handle the returned string carefully: do not log, echo, or persist it.
    """
    sec = dh.get_secret(name, project=project_name)
    return sec.read_secret_value()


SECRET_TOOLS = [
    new_dh_secret,
    get_dh_secret,
    import_dh_secret,
    list_dh_secrets,
    update_dh_secret,
    delete_dh_secret,
    save_dh_secret,
    refresh_dh_secret,
    export_dh_secret,
    set_dh_secret_value,
    read_dh_secret_value,
]
