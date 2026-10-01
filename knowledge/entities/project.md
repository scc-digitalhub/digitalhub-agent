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
  - get_or_create_dh_project
  - import_dh_project
  - load_dh_project
  - update_dh_project
  - add_label_dh_project
  - add_labels_dh_project
  - set_description_dh_project
  - scan_and_create_dh_tools
  - execute_dynamic_dh_tool
description: "Specification and reference for the DigitalHub Project entity, including CRUD, search, collaboration, export, and dynamic SDK tool discovery."
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

- `name` (_str_, required): The unique name of the project.
- `description` (_str_, optional): Human-readable description.
- `labels` (_list[str]_, optional): Metadata labels (e.g. `["stage:dev"]`).
- `source` (_str_, optional): Local context directory path.

**Agent Tool Mapping:** `new_dh_project(name, description)`

---

### 2.2 Get Project (`dh.get_project`)

Retrieves an existing Project instance from the backend by name.

```python
project = dh.get_project(name="customer-analytics")
```

**Parameters:**

- `name` (_str_, required): The name of the project to retrieve.

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

- `name` (_str_, required): Project name to delete.
- `cascade` (_bool_, default=`True`): Whether to cascade delete all child entities.
- `clean_context` (_bool_, default=`True`): Whether to clean up storage context.

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

- `query` (_str_, optional): Search keyword.
- `entity_types` (_list[str]_, optional): Filter entity types (e.g. `["dataitem", "function", "model"]`).

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

### 2.8 Get or Create Project (`dh.get_or_create_project`)

Retrieves an existing Project instance from the backend by name or creates it if it does not already exist.

```python
project = dh.get_or_create_project(
    name="customer-analytics",
    description="Analytics workspace",
    labels=["team:data-science"]
)
```

**Parameters:**

- `name` (_str_, required): The name of the project.
- `description` (_str_, optional): Project description.
- `labels` (_list[str]_, optional): Metadata labels.
- `context` (_str_, optional): Local context folder path.

**Agent Tool Mapping:** `get_or_create_dh_project(name, description, labels, context)`

---

### 2.9 Import Project (`dh.import_project`)

Imports a project specification from a previously exported YAML file into the backend.

```python
project = dh.import_project(file="exported_project.yaml", reset_id=False)
```

**Parameters:**

- `file` (_str_, required): Path to the YAML file containing the project definition.
- `reset_id` (_bool_, default=`False`): Whether to generate a new entity identifier.

**Agent Tool Mapping:** `import_dh_project(file, reset_id)`

---

### 2.10 Load Project (`dh.load_project`)

Loads a project specification locally from a YAML file without immediately persisting.

```python
project = dh.load_project(file="project_spec.yaml")
```

**Parameters:**

- `file` (_str_, required): Path to the project YAML specification.

**Agent Tool Mapping:** `load_dh_project(file)`

---

### 2.11 Update Project (`dh.update_project`)

Updates an existing project's metadata (description, labels) in the backend.

```python
project = dh.get_project("customer-analytics")
project.set_description("Updated description")
project.add_labels(["env:staging"])
updated = dh.update_project(project)
```

**Agent Tool Mapping:**

- `update_dh_project(name, description, labels)`
- `add_label_dh_project(project_name, label)`
- `add_labels_dh_project(project_name, labels)`
- `set_description_dh_project(project_name, description)`

---

## 3. Dynamic SDK Scanning & Runtime Tool Creation

When an agent needs an SDK operation that is not pre-registered in the static toolset:

- The agent calls `scan_and_create_dh_tools(entity='project')`.
- The tool scans the underlying `digitalhub` SDK and entity classes for unmapped operations.
- It parses type annotations, signatures, and docstrings to dynamically instantiate LangChain `StructuredTool` instances.
- The new tools are immediately registered into the active agent runtime (`ToolNode` and LLM tool bindings) so they become callable by name in the current conversation.
- Fallback tool: `execute_dynamic_dh_tool(tool_name, parameters)` allows executing any dynamically generated tool directly.

---

## 4. Best Practices for Agents

1. **Context Verification**: Before creating or modifying entities, verify the project exists using `get_dh_project` or list with `list_dh_projects`. Use `get_or_create_dh_project` when idempotent creation is preferred.
2. **Never Fabricate Project Names**: Extract the project name directly from user requests. If absent or ambiguous, ask the user.
3. **Destructive Operations**: Always confirm before deleting projects.
4. **Dynamic Tool Discovery**: When a project operation is needed that lacks a dedicated static tool, execute `scan_and_create_dh_tools("project")` to generate and register it on the fly.
