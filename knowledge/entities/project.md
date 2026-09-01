---
type: entity_specification
entity: project
version: "0.16"
tags: [project, core, workspace, permissions, search, crud]
tools:
  - new_dh_project
  - get_dh_project
  - list_dh_projects
  - delete_dh_project
  - export_dh_project
  - search_dh_project_entities
  - share_dh_project
  - unshare_dh_project
description: "Specification and reference for the DigitalHub Project entity, including CRUD, search, collaboration, and export operations."
---

# DigitalHub Project Specification & SDK Guide

The **Project** is the central organizational and execution container in DigitalHub. Every resource (DataItem, Function, Model, Artifact, Workflow, Run, Secret) belongs to a Project.

---

## 1. Project Lifecycle & Model

A Project encapsulates:
- **Metadata**: `name` (unique identifier), `description`, `labels`.
- **Entities**: All DataItems, Functions, Artifacts, Models, and Workflows associated with the project workspace.
- **Access Control & Permissions**: User sharing and role assignments.
- **Storage Context**: Underlying object store or bucket context allocated to the project.

---

## 2. SDK API Reference (DigitalHub 0.16)

### 2.1 Create Project (`dh.new_project`)
Creates a new Project entity in DigitalHub.

```python
import digitalhub as dh

project = dh.new_project(
    name="customer-analytics",
    description="Analytics pipeline for customer churn predictions",
    labels=["team:data-science", "env:production"]
)
```

**Parameters:**
- `name` (*str*, required): The unique name of the project.
- `description` (*str*, optional): Human-readable description.
- `labels` (*list[str]*, optional): Metadata labels (e.g. `["stage:dev"]`).
- `source` (*str*, optional): Local context directory path.

**Agent Tool Mapping:** `new_dh_project(name, description)`

---

### 2.2 Get Project (`dh.get_project`)
Retrieves an existing Project instance from the backend by name.

```python
project = dh.get_project(name="customer-analytics")
```

**Parameters:**
- `name` (*str*, required): The name of the project to retrieve.

**Agent Tool Mapping:** `get_dh_project(name)`

---

### 2.3 List Projects (`dh.list_projects`)
Lists all projects accessible to the current user context.

```python
projects = dh.list_projects()
for p in projects:
    print(p.name, p.description)
```

**Agent Tool Mapping:** `list_dh_projects()`

---

### 2.4 Delete Project (`dh.delete_project`)
Deletes a project and optionally cascades deletion to its child resources.

```python
dh.delete_project(name="old-project", cascade=True)
```

**Parameters:**
- `name` (*str*, required): Project name to delete.
- `cascade` (*bool*, default=`True`): Whether to cascade delete all child entities.
- `clean_context` (*bool*, default=`True`): Whether to clean up storage context.

**Agent Tool Mapping:** `delete_dh_project(name)`
> **Safety Rule:** Always ask user confirmation before deleting a project.

---

### 2.5 Entity Search (`project.search_entity`)
Searches across all entities registered inside a project.

```python
project = dh.get_project("customer-analytics")
results, pagination = project.search_entity(
    query="churn", 
    entity_types=["dataitem", "function"]
)
```

**Parameters:**
- `query` (*str*, optional): Search keyword.
- `entity_types` (*list[str]*, optional): Filter entity types (e.g. `["dataitem", "function", "model"]`).

**Agent Tool Mapping:** `search_dh_project_entities(project_name, query, entity_types)`

---

### 2.6 Collaboration & Sharing (`project.share` / `project.unshare`)
Manage user permissions for a project workspace.

```python
project = dh.get_project("customer-analytics")

# Grant access to a user
project.share(user="alice@company.com")

# Revoke access
project.unshare(user="alice@company.com")
```

**Agent Tool Mapping:**
- `share_dh_project(project_name, user)`
- `unshare_dh_project(project_name, user)`

---

### 2.7 Export Project (`project.export`)
Exports the full project configuration and entity definitions to a YAML specification.

```python
project = dh.get_project("customer-analytics")
yaml_path = project.export()
```

**Agent Tool Mapping:** `export_dh_project(project_name)`

---

## 3. Best Practices for Agents

1. **Context Verification**: Before creating or modifying entities, verify the project exists using `get_dh_project` or list with `list_dh_projects`.
2. **Never Fabricate Project Names**: Extract the project name directly from user requests. If absent or ambiguous, ask the user.
3. **Destructive Operations**: Always confirm before deleting projects.
