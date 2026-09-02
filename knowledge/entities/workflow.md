---
type: entity_specification
entity: workflow
version: "0.15"
tags:
  [
    workflow,
    pipeline,
    dag,
    hera,
    argo,
    orchestration,
    mlops,
    crud,
    tasks,
    triggers,
    runs,
  ]
tools:
  - new_dh_workflow
  - get_dh_workflow
  - get_dh_workflow_versions
  - import_dh_workflow
  - list_dh_workflows
  - update_dh_workflow
  - delete_dh_workflow
  - save_dh_workflow
  - refresh_dh_workflow
  - export_dh_workflow
  - run_dh_workflow
  - build_dh_hera_workflow
  - run_dh_hera_pipeline
  - list_dh_workflow_tasks
  - get_dh_workflow_task
  - new_dh_workflow_task
  - update_dh_workflow_task
  - trigger_dh_workflow
  - list_dh_workflow_triggers
  - get_dh_workflow_trigger
description: "Specification and reference for the DigitalHub Workflow entity: DAG-based pipeline orchestration, CRUD, build/pipeline lifecycle, tasks, triggers, and the Hera runtime."
---

# DigitalHub Workflow Specification & SDK Guide

A **Workflow** in DigitalHub represents a long-running orchestration procedure defined as a **Directed Acyclic Graph (DAG)**. Each node is a unit of work executed on the platform (typically as a Kubernetes Job) — for example, a Function `job`, a `serve`, a Container step, or a DBT transformation. Workflows are the primary way to organize multi-step data processing, ML training pipelines, and serving deployments.

---

## 1. Conceptual Model

- **Workflow entity**: metadata + spec (kind, source code, handler) + status (state, associated runs).
- **Task**: a per-action configuration attached to the workflow (`build`, `pipeline`, ...).
- **Run**: an actual execution of a task; produced by `workflow.run(action=...)`.
- **Trigger**: schedule- or event-based automation that starts a workflow run.

Every workflow belongs to a **Project**. Its resources (steps, container images, run artifacts) are namespaced under that project.

---

## 2. Supported Workflow Kinds

| Kind   | Runtime               | Package                   | Actions             |
| :----- | :-------------------- | :------------------------ | :------------------ |
| `hera` | Hera / Argo Workflows | `digitalhub-runtime-hera` | `build`, `pipeline` |

At the moment `hera` is the officially documented workflow kind in DigitalHub 0.15. For each kind, the `Workflow` object has kind-specific `spec` and `status` attributes; see the runtime documentation for spec details.

### 2.1 Hera Runtime Prerequisites

- Python `>= 3.10, < 3.15`
- `pip install digitalhub-runtime-hera`

### 2.2 Hera Workflow Spec Fields

Passed via `kwargs` to `new_dh_workflow` (or directly to `dh.new_workflow`):

| Field      | Type | Description                                              |
| :--------- | :--- | :------------------------------------------------------- |
| `code_src` | str  | URI pointing to the source code (local path, git, s3...) |
| `code`     | str  | Source code provided as plain text                       |
| `base64`   | str  | Source code encoded as base64                            |
| `handler`  | str  | Pipeline entrypoint function name                        |
| `lang`     | str  | Source code language (informational)                     |

---

## 3. Workflow Lifecycle

```text
[ 1. Define pipeline function (Hera Workflow) ]
        |  pipeline.py: def pipeline() -> Workflow
        v
[ 2. Register Workflow entity ]
        |  new_dh_workflow(kind="hera", code_src=..., handler=...)
        v
[ 3. Build (compile to Argo YAML) ]
        |  build_dh_hera_workflow(project, name)          # required at least once
        v
[ 4. Execute pipeline on Kubernetes ]
        |  run_dh_hera_pipeline(project, name, parameters={...})
        v
[ 5. Monitor & inspect runs ]
```

**Important:** `build` MUST be executed before `pipeline` for the Hera kind.

---

## 4. SDK API Reference (DigitalHub 0.15)

### 4.1 Create Workflow (`dh.new_workflow`)

Creates a Workflow entity and saves it into the backend.

```python
import digitalhub as dh

wf = dh.new_workflow(
    project="my-project",
    name="my-workflow",
    kind="hera",
    code_src="pipeline.py",
    handler="pipeline",
    description="ETL + training pipeline",
    labels=["team:mlops"],
)
```

**Parameters:**

- `project` (_str_, required)
- `name` (_str_, required)
- `kind` (_str_, required — e.g. `"hera"`)
- `uuid` (_str_, optional): custom UUID4 ID.
- `description` (_str_, optional)
- `labels` (_list[str]_, optional)
- `embedded` (_bool_, default `False`): embed spec in project spec.
- `**kwargs`: kind-specific spec (e.g. `code_src`, `handler`).

**Agent tool:** `new_dh_workflow(project, name, kind, uuid, description, labels, embedded, kwargs)`
Kind-specific spec fields go inside the `kwargs` dict.

---

### 4.2 Read Workflows

#### `get_workflow`

Fetch a workflow by name or key.

```python
wf = dh.get_workflow("my-workflow", project="my-project")
wf = dh.get_workflow("store://my-project/workflow/hera/my-workflow:<id>")
```

**Agent tool:** `get_dh_workflow(identifier, project, entity_id)`

#### `get_workflow_versions`

Returns all versions of a workflow.
**Agent tool:** `get_dh_workflow_versions(identifier, project)`

#### `list_workflows`

Lists latest workflow versions of a project with optional filters (`q`, `name`, `kind`, `user`, `state`, `created`, `updated`, `versions`).
**Agent tool:** `list_dh_workflows(project, ...)`

#### `import_workflow`

Load a workflow from a local YAML file (or store key).
**Agent tool:** `import_dh_workflow(file, key, reset_id, context)`

---

### 4.3 Update / Delete

#### `update_workflow`

Specs are immutable; only metadata-level changes are applied by the backend.
**Agent tool:** `update_dh_workflow(project_name, name)`

#### `delete_workflow`

Delete one version or all versions.

```python
dh.delete_workflow("my-workflow", project="my-project", delete_all_versions=True)
```

**Agent tool:** `delete_dh_workflow(identifier, project, entity_id, delete_all_versions, cascade)`

---

## 5. Workflow Object Methods

| Method      | Purpose                                    | Agent tool            |
| :---------- | :----------------------------------------- | :-------------------- |
| `save()`    | Persist / update the entity in the backend | `save_dh_workflow`    |
| `refresh()` | Reload state from backend                  | `refresh_dh_workflow` |
| `export()`  | Export as YAML file in the context folder  | `export_dh_workflow`  |
| `run()`     | Execute an action, producing a `Run`       | `run_dh_workflow`     |

### 5.1 Run method

```python
run = wf.run(
    action="pipeline",          # or "build"
    wait=True,
    log_info=True,
    parameters={"url": "https://example.com"},
)
```

**Parameters:**

- `action` (_str_, required): kind-specific action (`"build"`, `"pipeline"` for `hera`).
- `wait` (_bool_, default `False`)
- `log_info` (_bool_, default `True`)
- `extensions` (_list[dict] | None_)
- `**kwargs`: task/run parameters (see 5.2).

**Agent tool:** `run_dh_workflow(project_name, name, action, wait, log_info, extensions, kwargs)`

### 5.2 Hera task/run parameters (`kwargs`)

| Field        | Type       | Applies to         | Description                         |
| :----------- | :--------- | :----------------- | :---------------------------------- |
| `parameters` | dict       | `pipeline`         | Pipeline input values               |
| `volumes`    | list[dict] | `build`/`pipeline` | Attached volumes                    |
| `resources`  | dict       | `build`/`pipeline` | Kubernetes resource requests/limits |
| `envs`       | list[dict] | `build`/`pipeline` | Env variables                       |
| `secrets`    | list[str]  | `build`/`pipeline` | Secret names to mount               |
| `profile`    | str        | `build`/`pipeline` | Profile template                    |

### 5.3 Specialized Hera wrappers

- `build_dh_hera_workflow(project_name, name, ...)` → `action="build"`
- `run_dh_hera_pipeline(project_name, name, parameters, ...)` → `action="pipeline"`

---

## 6. Task Methods

Tasks are per-action configurations attached to the workflow.

| Method        | Purpose                               | Agent tool                |
| :------------ | :------------------------------------ | :------------------------ |
| `new_task`    | Create (or update) task for an action | `new_dh_workflow_task`    |
| `get_task`    | Get the task for a specific action    | `get_dh_workflow_task`    |
| `list_task`   | List all tasks of the workflow        | `list_dh_workflow_tasks`  |
| `update_task` | Update the task for an action         | `update_dh_workflow_task` |

Example:

```python
wf.new_task("pipeline", resources={"limits": {"cpu": "2", "memory": "4Gi"}})
```

---

## 7. Trigger Methods

Triggers automate workflow execution based on schedule or event.

| Method          | Purpose                        | Agent tool                  |
| :-------------- | :----------------------------- | :-------------------------- |
| `trigger`       | Create a trigger for an action | `trigger_dh_workflow`       |
| `get_trigger`   | Get a trigger by identifier    | `get_dh_workflow_trigger`   |
| `list_triggers` | List triggers of the workflow  | `list_dh_workflow_triggers` |

Example:

```python
wf.trigger(
    action="pipeline",
    kind="scheduler",
    name="nightly-run",
    template={"schedule": "0 2 * * *"},
    parameters={"url": "https://example.com"},
)
```

---

## 8. Defining a Hera Pipeline (source code)

A pipeline is a Python function that returns a Hera `Workflow` object. It **must not take arguments**; declare inputs via `Parameter(...)` on the returned `Workflow`.

```python
from hera.workflows import Workflow, DAG, Parameter
from digitalhub_runtime_hera.dsl import step

def pipeline():
    with Workflow(entrypoint="dag", arguments=Parameter(name="url")) as w:
        with DAG(name="dag"):
            A = step(
                template={"action": "job",
                          "inputs": {"url": "{{workflow.parameters.url}}"}},
                function="download-data",
                outputs=["dataset"],
            )
            B = step(
                template={"action": "job",
                          "inputs": {"di": "{{inputs.parameters.di}}"}},
                function="process-spire",
                inputs={"di": A.get_parameter("dataset")},
            )
            C = step(
                template={"action": "job",
                          "inputs": {"di": "{{inputs.parameters.di}}"}},
                function="process-measures",
                inputs={"di": A.get_parameter("dataset")},
            )
            A >> [B, C]
    return w
```

### 8.1 DSL helpers (`digitalhub_runtime_hera.dsl`)

- **`step(**kwargs)`** — creates a workflow step (Hera Task) inside a `DAG`or`Steps` context.
  - `template` (dict, required): must include `"action"` (e.g. `"job"`); may include `"inputs"` referring to `{{inputs.parameters.<name>}}` or `{{workflow.parameters.<name>}}`.
  - `function` (str): DigitalHub function name to run.
  - `function_id` (str, optional).
  - `name` (str, optional).
  - `inputs` (dict): keys become Hera Parameters; values may reference other steps' outputs via `OTHER.get_parameter("...")`.
  - `outputs` (list[str]): declared step outputs (become Hera Outputs / Artifacts).
- **`container_template(...)`** — builds a Hera container template directly for advanced/custom scenarios.
- **Chaining**: use `A >> [B, C]` to declare dependencies inside a DAG.

---

## 9. End-to-end Recipe

```python
import digitalhub as dh

# 1. Create the workflow entity, pointing at the local pipeline source file.
wf = dh.new_workflow(
    project="my-project",
    name="etl-and-train",
    kind="hera",
    code_src="pipeline.py",
    handler="pipeline",
)

# 2. Build (required before pipeline).
wf.run(action="build", wait=True)

# 3. Execute the pipeline with runtime parameters.
run = wf.run(
    action="pipeline",
    wait=True,
    parameters={"url": "https://data.example.com/customers.csv"},
)
```

Equivalent agent tool sequence:

1. `new_dh_workflow(project="my-project", name="etl-and-train", kind="hera", kwargs={"code_src": "pipeline.py", "handler": "pipeline"})`
2. `build_dh_hera_workflow(project_name="my-project", name="etl-and-train")`
3. `run_dh_hera_pipeline(project_name="my-project", name="etl-and-train", parameters={"url": "..."})`

---

## 10. Operational Guidance for the Agent

- Use `list_dh_workflows` for discovery; use `get_dh_workflow` (with `entity_id`) to pin a specific version.
- Always call **`build_dh_hera_workflow` before `run_dh_hera_pipeline`** for Hera workflows (or the more general `run_dh_workflow(action="build")` then `action="pipeline"`).
- Pipeline inputs go under `parameters` (a dict); infrastructure knobs (`volumes`, `resources`, `envs`, `secrets`, `profile`) also flow via `kwargs` of `run_dh_workflow`.
- Prefer the specialized wrappers (`build_dh_hera_workflow`, `run_dh_hera_pipeline`) when the kind is `hera` — they enforce correct action naming.
- For non-hera kinds (future), use the generic `run_dh_workflow(action=...)`.
- Workflow specs are immutable: to modify a pipeline, register a new version via `new_dh_workflow` with updated `code_src`/`handler`.
- To retrieve pipeline results, treat the produced `Run` like any other DigitalHub run (`get_dh_run_output`, `get_dh_run_result`, etc.).
