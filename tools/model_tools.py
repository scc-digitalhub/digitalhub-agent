from typing import Optional, List, Dict, Any, Union
from langchain_core.tools import tool
import digitalhub as dh


@tool
def new_dh_model(
    project: str,
    name: str,
    kind: str = "model",
    uuid: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    embedded: bool = False,
    path: Optional[str] = None,
    extensions: Optional[List[dict]] = None,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Create a new Model entity in DigitalHub WITHOUT uploading file content.

    Registers a metadata-only reference pointing at an existing local or remote
    path. 'path' becomes both the model's spec.path (source of downloads) and
    the default destination of upload(). Kind-specific spec fields
    (framework, algorithm, base_model, parameters, metrics, and kind-specific
    extras like flavor/signature/model_id) go inside 'extra_specs'.
    """
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    spec_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return dh.new_model(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        path=path,
        extensions=extensions,
        **spec_kwargs,
    )


@tool
def log_dh_model(
    project: str,
    name: str,
    source: Union[str, List[str]],
    kind: str = "model",
    drop_existing: bool = False,
    path: Optional[str] = None,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Log a model: create the entity AND upload the local file(s) to the model store.

    'source' can be a single local filepath, a directory, or a list of paths.
    'path' is the destination path in the model store; auto-generated if omitted.
    """
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    spec_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return dh.log_model(
        project=project,
        name=name,
        kind=kind,
        source=source,
        drop_existing=drop_existing,
        path=path,
        **spec_kwargs,
    )


@tool
def log_dh_generic_model(
    project: str,
    name: str,
    source: Union[str, List[str]],
    drop_existing: bool = False,
    path: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Log a generic model (kind='model') from a local path to the model store.
    Convenience shortcut for a plain model with description and labels.
    """
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    spec_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return dh.log_generic_model(
        project=project,
        name=name,
        source=source,
        drop_existing=drop_existing,
        path=path,
        description=description,
        labels=labels,
        **spec_kwargs,
    )


@tool
def log_dh_mlflow_model(
    project: str,
    name: str,
    source: Union[str, List[str]],
    drop_existing: bool = False,
    path: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Log an MLflow model (kind='mlflow') from a local MLflow directory.

    MLflow-specific spec fields (flavor, model_config, input_datasets, signature)
    may be provided inside 'extra_specs'.
    """
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    spec_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return dh.log_mlflow(
        project=project,
        name=name,
        source=source,
        drop_existing=drop_existing,
        path=path,
        description=description,
        labels=labels,
        **spec_kwargs,
    )


@tool
def log_dh_sklearn_model(
    project: str,
    name: str,
    source: Union[str, List[str]],
    drop_existing: bool = False,
    path: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Log a scikit-learn model (kind='sklearn') from a local file or directory.
    """
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    spec_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return dh.log_sklearn(
        project=project,
        name=name,
        source=source,
        drop_existing=drop_existing,
        path=path,
        description=description,
        labels=labels,
        **spec_kwargs,
    )


@tool
def log_dh_huggingface_model(
    project: str,
    name: str,
    source: Union[str, List[str]],
    drop_existing: bool = False,
    path: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    extra_specs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    Log a HuggingFace model (kind='huggingface') from a local repository or directory.

    HuggingFace-specific spec fields (model_id, model_revision) may be provided
    inside 'extra_specs'.
    """
    raw_specs = extra_specs or kwargs.get("kwargs") or kwargs.get("v__kwargs") or {}
    if not isinstance(raw_specs, dict):
        raw_specs = {}
    spec_kwargs = {k: v for k, v in raw_specs.items() if k not in ("v__kwargs", "kwargs")}
    return dh.log_huggingface(
        project=project,
        name=name,
        source=source,
        drop_existing=drop_existing,
        path=path,
        description=description,
        labels=labels,
        **spec_kwargs,
    )


@tool
def get_dh_model(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None,
):
    """
    Get a Model object from the backend.

    'identifier' can be an entity key (store://...) or the model name.
    """
    return dh.get_model(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
    )


@tool
def get_dh_model_versions(
    identifier: str,
    project: Optional[str] = None,
):
    """
    Get all model version instances from the backend.
    """
    return dh.get_model_versions(
        identifier=identifier,
        project=project,
    )


@tool
def import_dh_model(
    file: Optional[str] = None,
    key: Optional[str] = None,
    reset_id: bool = False,
    context: Optional[str] = None,
):
    """
    Import a model object from a YAML file or from a storage key.
    """
    return dh.import_model(
        file=file,
        key=key,
        reset_id=reset_id,
        context=context,
    )


@tool
def list_dh_models(
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
    List latest-version model objects from backend for a project with optional filters.
    """
    return dh.list_models(
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
def update_dh_model(
    project_name: str,
    name: str,
):
    """
    Update a model object in the backend. Note that object specs are immutable.
    """
    mdl = dh.get_model(name, project=project_name)
    return dh.update_model(mdl)


@tool
def delete_dh_model(
    identifier: str,
    project: Optional[str] = None,
    entity_id: Optional[str] = None,
    delete_all_versions: bool = False,
    cascade: bool = True,
):
    """
    Delete a model object from backend.
    """
    return dh.delete_model(
        identifier=identifier,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        cascade=cascade,
    )


@tool
def save_dh_model(
    project_name: str,
    name: str,
    update: bool = False,
):
    """
    Save or update the model entity into the backend.
    """
    mdl = dh.get_model(name, project=project_name)
    return mdl.save(update=update)


@tool
def refresh_dh_model(
    project_name: str,
    name: str,
):
    """
    Refresh model state from backend.
    """
    mdl = dh.get_model(name, project=project_name)
    return mdl.refresh()


@tool
def export_dh_model(
    project_name: str,
    name: str,
):
    """
    Export model object as a YAML file in the context folder.
    """
    mdl = dh.get_model(name, project=project_name)
    return mdl.export()



@tool
def as_file_dh_model(
    project_name: str,
    name: str,
):
    """
    Download the model into a temporary folder and return the list of file paths.
    Useful for immediate consumption (e.g. load with framework loader) without choosing a destination.
    """
    mdl = dh.get_model(name, project=project_name)
    return mdl.as_file()


@tool
def download_dh_model(
    project_name: str,
    name: str,
    destination: Optional[str] = None,
    overwrite: bool = False,
):
    """
    Download the model's file(s) from storage to a local path.

    If 'destination' is not specified, files are placed under the context path.
    If files already exist and overwrite=False, an error is raised.
    """
    mdl = dh.get_model(name, project=project_name)
    return mdl.download(destination=destination, overwrite=overwrite)


@tool
def upload_dh_model(
    project_name: str,
    name: str,
    source: Union[str, List[str]],
    keep_dir_structure: bool = False,
):
    """
    Upload local file(s) to the model's spec.path in remote storage.

    'source' can be a filepath, a directory, or a list of paths.
    When 'source' is a directory or list, spec.path must be a folder/partition
    ending with '/' (for s3).
    """
    mdl = dh.get_model(name, project=project_name)
    return mdl.upload(source, keep_dir_structure=keep_dir_structure)


@tool
def log_dh_model_metric(
    project_name: str,
    name: str,
    key: str,
    value: Any,
    overwrite: bool = False,
    single_value: bool = False,
):
    """
    Log a metric into the model's status.

    A metric is named by 'key' and has a 'value' that can be a number or a list of numbers.
    By default new values are appended to any existing list for that key.
    Set single_value=True to store the value as a single number (not wrapped in a list).
    Set overwrite=True to replace any existing metric for that key.
    """
    mdl = dh.get_model(name, project=project_name)
    return mdl.log_metric(
        key=key,
        value=value,
        overwrite=overwrite,
        single_value=single_value,
    )


@tool
def log_dh_model_metrics(
    project_name: str,
    name: str,
    metrics: Dict[str, Any],
    overwrite: bool = False,
):
    """
    Log multiple metrics into the model's status in one call.

    'metrics' is a dict mapping metric name to value (number or list of numbers).
    List values are logged as lists; scalars are logged as single values.
    Set overwrite=True to replace all provided metrics; default appends to existing ones.
    """
    mdl = dh.get_model(name, project=project_name)
    return mdl.log_metrics(
        metrics=metrics,
        overwrite=overwrite,
    )


MODEL_TOOLS = [
    new_dh_model,
    log_dh_model,
    log_dh_generic_model,
    log_dh_mlflow_model,
    log_dh_sklearn_model,
    log_dh_huggingface_model,
    get_dh_model,
    get_dh_model_versions,
    import_dh_model,
    list_dh_models,
    update_dh_model,
    delete_dh_model,
    save_dh_model,
    refresh_dh_model,
    export_dh_model,
    as_file_dh_model,
    download_dh_model,
    upload_dh_model,
    log_dh_model_metric,
    log_dh_model_metrics,
]
