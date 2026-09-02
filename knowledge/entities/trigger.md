---
type: entity_specification
entity: trigger
version: "0.15"
tags:
  [trigger, scheduler, lifecycle, cron, automation, event, orchestration, crud]
tools:
  - new_dh_trigger
  - get_dh_trigger
  - import_dh_trigger
  - list_dh_triggers
  - update_dh_trigger
  - delete_dh_trigger
  - save_dh_trigger
  - refresh_dh_trigger
  - export_dh_trigger
  - stop_dh_trigger
  - new_dh_scheduler_trigger
  - new_dh_lifecycle_trigger
description: "Specification and reference for the DigitalHub Trigger entity: scheduler (cron) and lifecycle (event-driven) automation of function and workflow executions."
---

# DigitalHub Trigger Specification & SDK Guide

A **Trigger** is the logical description of _how_ and _when_ a job should be executed on the platform. Triggers control the scheduling and event-driven execution of a task, targeting either a **Function** or a **Workflow**. They cover time-based cron schedules and reactions to entity state changes (lifecycle events).

---

## 1. Conceptual Model

A trigger binds together:

- A **target entity** — either a `function` or a `workflow` (mutually exclusive).
- A **task** — the specific action-configuration on that entity (e.g. `job`, `pipeline`).
- A **kind-specific spec** — the "when" logic (cron schedule or entity-state condition).
- An optional **template** — the run parameters/inputs/resources used when the trigger fires.

Triggers belong to a **Project** and are versioned like any other DigitalHub entity.

---

## 2. Supported Trigger Kinds

| Kind        | Purpose                                       | Required kind-spec               |
| :---------- | :-------------------------------------------- | :------------------------------- |
| `scheduler` | Time-based execution via cron                 | `schedule` (Quartz cron)         |
| `lifecycle` | Event-based execution on entity state changes | `key`, `states` (list of states) |

Each kind is a `Trigger` subclass with its own `spec` and `status` attributes.

### 2.1 Base spec (all kinds)

| Field      | Type | Description                                                                      |
| :--------- | :--- | :------------------------------------------------------------------------------- |
| `task`     | str  | Task URI: `<task-kind>://<project>/<task-id>`                                    |
| `function` | str  | Target function URI: `<function-kind>://<project>/<function-name>:<function-id>` |
| `workflow` | str  | Target workflow URI: `<workflow-kind>://<project>/<workflow-name>:<workflow-id>` |
| `template` | dict | Run configuration template (parameters, inputs, resources, ...)                  |

`function` **and** `workflow` are mutually exclusive — provide exactly one.

### 2.2 Scheduler-specific spec

| Field      | Type | Description                                                                                                      |
| :--------- | :--- | :--------------------------------------------------------------------------------------------------------------- |
| `schedule` | str  | [Quartz cron expression](https://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html) |

### 2.3 Lifecycle-specific spec

| Field    | Type      | Description                                                                                      |
| :------- | :-------- | :----------------------------------------------------------------------------------------------- |
| `key`    | str       | Entity key to monitor: `store://<project>/<entity-type>/<entity-kind>/<name>` (wildcards `*` OK) |
| `states` | list[str] | Monitored states that fire the trigger (e.g. `["READY"]`, `["completed"]`)                       |

Template values in lifecycle triggers may reference the source event, e.g. `{"inputs": {"my-param": "{{input.key}}"}}`.

---

## 3. Trigger Lifecycle

```text
[ 1. Define trigger ]
        |  new_dh_trigger(kind=..., task=..., function|workflow=..., ...)
        v
[ 2. Persisted in backend ]
        |  automatically by new_dh_trigger (or explicit save_dh_trigger)
        v
[ 3. Trigger active ]
        |  fires per schedule or on matching entity state change
        v
[ 4. Stop / delete ]
        |  stop_dh_trigger  or  delete_dh_trigger
```

---

## 4. SDK API Reference (DigitalHub 0.15)

### 4.1 Create Trigger (`dh.new_trigger`)

Creates and saves a Trigger entity in the backend.

```python
import digitalhub as dh

trg = dh.new_trigger(
    project="my-project",
    name="daily-run",
    kind="scheduler",
    task="<task-kind>://<project>/<task-id>",
    function="<function-kind>://<project>/<function-name>:<function-id>",
    schedule="0 0 * * * ?",
)
```

**Parameters:**

- `project` (_str_, required)
- `name` (_str_, required)
- `kind` (_str_, required — e.g. `"scheduler"`, `"lifecycle"`)
- `task` (_str_, required): task URI.
- `function` (_str_, optional) — provide either this or `workflow`.
- `workflow` (_str_, optional) — provide either this or `function`.
- `uuid` (_str_, optional)
- `description` (_str_, optional)
- `labels` (_list[str]_, optional)
- `embedded` (_bool_, default `False`)
- `**kwargs`: kind-specific spec (`schedule`, `key`, `states`, `template`).

**Agent tool:** `new_dh_trigger(project, name, kind, task, function, workflow, uuid, description, labels, embedded, kwargs)` — put `schedule` / `key` / `states` / `template` inside `kwargs`.

---

### 4.2 Read Triggers

#### `get_trigger`

Fetch a single trigger by name or store key.

```python
trg = dh.get_trigger("daily-run", project="my-project")
trg = dh.get_trigger("store://my-project/trigger/scheduler/daily-run:<id>")
```

**Agent tool:** `get_dh_trigger(identifier, project, entity_id)`

#### `list_triggers`

Lists latest trigger versions with optional filters:
`q`, `name`, `kind`, `user`, `state`, `created`, `updated`, `versions`, `task`.
**Agent tool:** `list_dh_triggers(project, ...)`

#### `import_trigger`

Load a trigger from a local YAML file or a store key.
**Agent tool:** `import_dh_trigger(file, key, reset_id, context)`

---

### 4.3 Update / Delete

#### `update_trigger`

Specs are immutable; only metadata-level updates are applied by the backend.
**Agent tool:** `update_dh_trigger(project_name, name)`

#### `delete_trigger`

Delete one version or all versions.

```python
dh.delete_trigger("daily-run", project="my-project", delete_all_versions=True)
```

**Agent tool:** `delete_dh_trigger(identifier, project, entity_id, delete_all_versions)`

_Note:_ `delete_trigger` does **not** accept a `cascade` argument, unlike function/workflow deletion.

---

## 5. Trigger Object Methods

| Method      | Purpose                                    | Agent tool           |
| :---------- | :----------------------------------------- | :------------------- |
| `save()`    | Persist / update the entity in the backend | `save_dh_trigger`    |
| `refresh()` | Reload state from backend                  | `refresh_dh_trigger` |
| `export()`  | Export as YAML file in the context folder  | `export_dh_trigger`  |
| `stop()`    | Deactivate the trigger (stop firing)       | `stop_dh_trigger`    |

`stop()` is trigger-specific — it halts an active scheduler/lifecycle subscription without deleting the entity.

---

## 6. Specialized Kind Wrappers

For convenience, the agent exposes two purpose-built wrappers that pre-set `kind` and enforce the required kind-spec fields:

### 6.1 `new_dh_scheduler_trigger`

```python
new_dh_scheduler_trigger(
    project="my-project",
    name="daily-run",
    task="job://my-project/<task-id>",
    schedule="0 0 * * * ?",
    function="python://my-project/my-function:<id>",
)
```

### 6.2 `new_dh_lifecycle_trigger`

```python
new_dh_lifecycle_trigger(
    project="my-project",
    name="validate-on-upload",
    task="job://my-project/<task-id>",
    key="store://my-project/artifact/*",
    states=["READY"],
    function="python://my-project/validate:<id>",
    template={"inputs": {"my-param": "{{input.key}}"}},
)
```

---

## 7. Creating Triggers from Function / Workflow Objects

The same trigger can be created via the parent entity's `trigger(...)` method — often more ergonomic because target and task are inferred:

```python
# Scheduler on a function job
function = project.get_function("my-function")
trigger = function.trigger(
    action="job",
    kind="scheduler",
    name="daily-function-run",
    schedule="0 0 * * * ?",
)

# Lifecycle on a workflow pipeline
workflow = project.get_workflow("my-workflow")
trigger = workflow.trigger(
    action="pipeline",
    kind="lifecycle",
    name="validation-pipeline-on-upload",
    key="store://project/artifact/*",
    states=["READY"],
    template={"parameters": {"param-name": "{{input.key}}"}},
)
```

Corresponding agent tools already exist in the function / workflow toolsets:
`trigger_dh_function`, `list_dh_function_triggers`, `get_dh_function_trigger`,
`trigger_dh_workflow`, `list_dh_workflow_triggers`, `get_dh_workflow_trigger`.

---

## 8. End-to-end Recipes

### 8.1 Nightly-run scheduler on a Python function job

```python
import digitalhub as dh

# 1. Look up the function and its 'job' task.
fn = dh.get_function("etl-daily", project="my-project")
job_task = fn.get_task("job")

trg = dh.new_trigger(
    project="my-project",
    name="etl-daily-nightly",
    kind="scheduler",
    task=job_task.key,
    function=fn.key,
    schedule="0 0 2 * * ?",       # every day at 02:00
    template={"parameters": {"date": "{{trigger.timestamp}}"}},
)
```

Agent-tool equivalent:

```
new_dh_scheduler_trigger(
    project="my-project",
    name="etl-daily-nightly",
    task="<task-key>",
    schedule="0 0 2 * * ?",
    function="<function-key>",
    template={"parameters": {"date": "{{trigger.timestamp}}"}},
)
```

### 8.2 Lifecycle validation on artifact upload

```python
trg = dh.new_trigger(
    project="my-project",
    name="validate-on-upload",
    kind="lifecycle",
    task="job://my-project/<task-id>",
    function="python://my-project/validate:<id>",
    key="store://my-project/artifact/*",
    states=["READY"],
    template={"inputs": {"artifact_key": "{{input.key}}"}},
)
```

### 8.3 Stop and remove a trigger

```python
trg = dh.get_trigger("etl-daily-nightly", project="my-project")
trg.stop()
dh.delete_trigger("etl-daily-nightly", project="my-project", delete_all_versions=True)
```

---

## 9. Operational Guidance for the Agent

- **One target only**: always set exactly one of `function` or `workflow`; setting both is invalid.
- **Task URI**: the `task` string must reference an _existing_ task on the target entity — obtain it via `get_dh_function_task` / `get_dh_workflow_task` (or `list_dh_function_tasks` / `list_dh_workflow_tasks`) before creating the trigger.
- **Cron format**: schedules use _Quartz_ cron (6 or 7 fields, including seconds), not standard Unix cron. Example: `"0 0 * * * ?"` = every hour on the hour.
- **Wildcards in `key`**: lifecycle `key` supports `*` to watch entire kinds/names.
- **Immutable spec**: to change a schedule/key/states, register a new trigger version via `new_dh_trigger`; do not attempt to edit spec fields via `update_dh_trigger`.
- **Stop vs delete**: prefer `stop_dh_trigger` to pause automation while keeping history; use `delete_dh_trigger` to permanently remove.
- **Prefer wrappers**: use `new_dh_scheduler_trigger` and `new_dh_lifecycle_trigger` when the kind is known — they enforce the required kind-spec fields at call time.
- **Discovery from parent entity**: to list all triggers attached to a specific function or workflow, use `list_dh_function_triggers` / `list_dh_workflow_triggers`. To scan the whole project, use `list_dh_triggers`.
