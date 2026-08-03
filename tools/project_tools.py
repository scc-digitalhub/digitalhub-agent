import json
from typing import Optional, List
from langchain_core.tools import tool
import digitalhub as dh


@tool
def get_dh_project(name: str):
    """Retrieve an existing DigitalHub project by name."""
    return dh.get_project(name)


@tool
def new_dh_project(name: str, description: Optional[str] = None):
    """Create a new DigitalHub project."""
    return dh.new_project(name=name, description=description)


@tool
def list_dh_projects():
    """List all DigitalHub projects available in the context/backend."""
    return dh.list_projects()


@tool
def delete_dh_project(name: str):
    """Delete a DigitalHub project by name."""
    return dh.delete_project(name)


@tool
def export_dh_project(project_name: str):
    """Export project definition to a YAML file."""
    project = dh.get_project(project_name)
    return project.export()


@tool
def search_dh_project_entities(project_name: str, query: Optional[str] = None, entity_types: Optional[List[str]] = None):
    """Search for entities inside a DigitalHub project."""
    project = dh.get_project(project_name)
    results, _ = project.search_entity(query=query, entity_types=entity_types)
    return results


@tool
def share_dh_project(project_name: str, user: str):
    """Share a project with a specific user."""
    project = dh.get_project(project_name)
    return project.share(user=user)


@tool
def unshare_dh_project(project_name: str, user: str):
    """Unshare a project from a user."""
    project = dh.get_project(project_name)
    return project.unshare(user=user)


PROJECT_TOOLS = [
    get_dh_project,
    new_dh_project,
    list_dh_projects,
    delete_dh_project,
    export_dh_project,
    search_dh_project_entities,
    share_dh_project,
    unshare_dh_project,
]
