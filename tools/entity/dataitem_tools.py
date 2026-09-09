import json
from typing import Optional, Literal
from langchain_core.tools import tool
import digitalhub as dh


@tool
def register_dh_dataitem(
    project_name: str, 
    name: str, 
    kind: Literal["dataitem", "table", "croissant"] = "dataitem", 
    path: Optional[str] = None
):
    """
    Register a new dataitem metadata record in a project WITHOUT uploading source files.
    Kinds: 'dataitem' (raw files), 'table' (tabular/SQL), 'croissant' (ML datasets).
    """
    return dh.new_dataitem(project=project_name, name=name, kind=kind, path=path)

@tool
def log_dh_dataitem(
    project_name: str, 
    name: str, 
    source: str, 
    kind: Literal["dataitem", "table", "croissant"] = "dataitem", 
    path: Optional[str] = None, 
    description: Optional[str] = None
):
    """
    Log and upload a dataset or file to DigitalHub storage.
    """
    return dh.log_dataitem(
        project=project_name, 
        name=name, 
        kind=kind, 
        source=source, 
        path=path, 
        description=description
    )

@tool
def get_dh_dataitem(
    project_name: str, 
    name: str, 
    version: Optional[str] = None, 
    overwrite_croissant: bool = False
):
    """
    Retrieve a dataitem by name.
    """
    return dh.get_dataitem(name, project=project_name, entity_id=version)


@tool
def download_dh_dataitem(
    project_name: str, 
    name: str, 
    destination: Optional[str] = None, 
    overwrite: bool = False
):
    """Download dataitem file(s) from storage (S3/remote/local) to a destination directory."""
    di = dh.get_dataitem(name, project=project_name)
    return di.download(destination=destination, overwrite=overwrite)

@tool
def upload_dh_dataitem(
    project_name: str, 
    name: str, 
    source: str, 
    keep_dir_structure: bool = False
):
    """Upload a local file or directory to a dataitem's target storage path."""
    di = dh.get_dataitem(name, project=project_name)
    return di.upload(source, keep_dir_structure=keep_dir_structure)

@tool
def list_dh_dataitems(
    project_name: str, 
    kind: Optional[Literal["dataitem", "table", "croissant"]] = None
):
    """List dataitems in a project, optionally filtered by kind ('dataitem', 'table', 'croissant')."""
    return dh.list_dataitems(project=project_name, kind=kind)

@tool
def export_dh_dataitem(project_name: str, name: str):
    """Export a dataitem definition as a local YAML file."""
    di = dh.get_dataitem(name, project=project_name)
    return di.export()

@tool
def import_dh_dataitem(project_name: str, file: Optional[str] = None, key: Optional[str] = None):
    """Import a dataitem entity from a YAML file or store key into a project."""
    return dh.import_dataitem(file=file, key=key, context=project_name)

@tool
def delete_dh_dataitem(
    project_name: str, 
    name: str, 
    version: Optional[str] = None, 
    delete_all_versions: bool = False
):
    """Delete a dataitem from a project."""
    should_delete_all = True if version is None else delete_all_versions
    return dh.delete_dataitem(
        identifier=name, 
        project=project_name, 
        entity_id=version, 
        delete_all_versions=should_delete_all
    )

DATAITEM_TOOLS = [
    register_dh_dataitem,
    log_dh_dataitem,
    get_dh_dataitem,
    download_dh_dataitem,
    upload_dh_dataitem,
    list_dh_dataitems,
    export_dh_dataitem,
    import_dh_dataitem,
    delete_dh_dataitem,
]
