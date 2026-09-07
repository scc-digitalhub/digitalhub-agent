---
type: entity_specification
entity: function
version: "0.15"
tags:
  [
    function,
    executable,
    python,
    dbt,
    container,
    hera,
    modelserve,
    flower,
    crud,
    tasks,
    triggers,
  ]
tools:
  - new_dh_function
  - get_dh_function
  - get_dh_function_versions
  - import_dh_function
  - list_dh_functions
  - update_dh_function
  - delete_dh_function
  - save_dh_function
  - refresh_dh_function
  - export_dh_function
  - run_dh_function
  - list_dh_function_tasks
  - get_dh_function_task
  - new_dh_function_task
  - update_dh_function_task
  - trigger_dh_function
  - list_dh_function_triggers
  - get_dh_function_trigger
description: "Specification and reference for the DigitalHub Function entity: executable objects (code, ML inference, data validation, ...) with CRUD, run, tasks, triggers, and kind-selected runtimes."
---

# DigitalHub Function Specification & SDK Guide

A **Function** is the logical description of something the platform can execute
and track for you. It may represent code to run as a job, an ML inference
served as a batch procedure or as a service, a data validation, a DBT
transformation, etc. This document covers only the **entity-level** surface
(CRUD, generic methods, tasks, triggers, kinds enumeration). For runtime- and
action-specific parameters (e.g. `job`/`serve`/`build` for `kind='python'`),
see the corresponding runtime doc — for example the [python](../runtimes/python.md)
runtime guide.

---

## 1. Conceptual Model

A function entity holds:

- **Metadata** — `name`, `description`, `labels`, `kind`, version (UUID).
- **Spec** — kind-specific fields describing the function (source code, handler,
  image, requirements, ...). See the runtime doc for each kind.
- **Status** — backend-managed lifecycle state.

A function belongs to a **Project** and is versioned. Its executions are
represented by **Run** entities (see [run](run.md)); its per-action configuration
is represented by **Task** entities; and its schedule/event automations are
represented by **Trigger** entities (see [trigger](trigger.md)).

Object graph:

```text
                 +-------------+
                 |  Function   |
                 +------+------+
                        |
       +----------------+----------------+
       |                |                |
   +---v---+       +----v----+      +----v-----+
   | Task  |       | Trigger |      |   Run    |
   |(action|       |(schedule|      |(execution|
   | config|       | / event)|      | of a     |
   |       |       |         |      |  task)   |
   +-------+       +---------+      +----------+
```

---

## 2. Supported Function Kinds

Each kind is a subclass of `Function` with its own `spec` and `status`
schemas, executed by the corresponding runtime.

| Kind            | Runtime                        | Runtime package                             | Actions                                                                        |
| :-------------- | :----------------------------- | :------------------------------------------ | :----------------------------------------------------------------------------- |
| `python`        | Python (general purpose)       | `digitalhub-runtime-python`                 | `job`, `serve`, `build`                                                        |
| `guardrail`     | Python — LLM safety guardrail  | `digitalhub-runtime-python` (guardrail)     | `serve`, `build`                                                               |
| `openinference` | Python — OpenInference tracing | `digitalhub-runtime-python` (openinference) | `serve`, `build`                                                               |
| `dbt`           | DBT transformations            | `digitalhub-runtime-dbt`                    | `transform`                                                                    |
| `container`     | Arbitrary container workloads  | `digitalhub-runtime-container`              | `job`, `serve`, `build`                                                        |
| `modelserve`    | Model-serving runtimes         | `digitalhub-runtime-modelserve`             | `serve` (sklearnserve / mlflowserve / huggingfaceserve / vllmserve / kubeai)   |
| `flower`        | Federated learning (Flower)    | `digitalhub-runtime-flower`                 | `flower-app-train`, `flower-client-build/deploy`, `flower-server-build/deploy` |

**Not a Function kind**: `hera` is a _Workflow_ kind, not a Function kind — see [workflow](workflow.md).

Kind-specific spec details (`code_src`, `handler`, `python_version`, `requirements`,
`image`, `base_image`, `init_function`, ...) live in the runtime documentation
of each kind.

---

## 3. Function Lifecycle

```text
[ 1. Write handler / source ]
        |  handler.py (kind-specific — see runtime docs)
        v
[ 2. Register the Function entity ]
        |  new_dh_function(kind="python", code_src="handler.py", handler="main", ...)
        v
[ 3. Build (optional / kind-dependent) ]
        |  run_dh_function(action="build")  or  run_dh_python_build(...)
        v
[ 4. Execute ]
        |  run_dh_function(action="job"|"serve"|"build"|...)
        |  or use runtime-specific wrappers (run_dh_python_job, ...)
        v
[ 5. Track produced Run entity ]
        |  get_dh_run / list_dh_runs / get_dh_run_output / ...
        v
[ 6. Automate ]
        |  trigger_dh_function(kind="scheduler"|"lifecycle", ...)
```

---

## 4. SDK API Reference (DigitalHub 0.15)

### 4.1 Create — `dh.new_function`

Creates a Function entity and saves it into the backend.

```python
import digitalhub as dh

fn = dh.new_function(
    project="my-project",
    name="my-function",
    kind="python",
    code_src="function.py",
    handler="function-handler",
    python_version="PYTHON3_10",
)
```

**Parameters:**

- `project` (_str_, required)
- `name` (_str_, required)
- `kind` (_str_, required — see kinds table above)
- `uuid` (_str_, optional)
- `description` (_str_, optional)
- `labels` (_list[str]_, optional)
- `embedded` (_bool_, default `False`)
- `**kwargs`: kind-specific spec fields (see runtime docs).

**Agent tool:** `new_dh_function(project, name, kind, uuid, description, labels, embedded, kwargs)`
Kind-specific spec fields go inside the `kwargs` dict. For `kind='python'`, prefer
`new_dh_python_function` (from the python-runtime toolset) which exposes those
fields explicitly.

### 4.2 Read

#### `get_function`

Fetch a single function by name or key.

```python
fn = dh.get_function("my-function", project="my-project")
fn = dh.get_function("store://my-project/function/python/my-function:<id>")
```

**Agent tool:** `get_dh_function(identifier, project, entity_id)`

#### `get_function_versions`

Returns all versions of a function.
**Agent tool:** `get_dh_function_versions(identifier, project)`

#### `list_functions`

Lists latest function versions of a project with optional filters (`q`, `name`,
`kind`, `user`, `state`, `created`, `updated`, `versions`).
**Agent tool:** `list_dh_functions(project, ...)`

#### `import_function`

Load a function from a local YAML file or a store key.
**Agent tool:** `import_dh_function(file, key, reset_id, context)`

### 4.3 Update / Delete

#### `update_function`

Specs are immutable; only metadata-level updates are applied.
**Agent tool:** `update_dh_function(project_name, name)`

#### `delete_function`

Delete one version or all versions.

```python
dh.delete_function("my-function", project="my-project", delete_all_versions=True)
```

**Agent tool:** `delete_dh_function(identifier, project, entity_id, delete_all_versions, cascade)`

---

## 5. Function Object Methods

### 5.1 CRUD-object methods

| Method      | Purpose                                    | Agent tool            |
| :---------- | :----------------------------------------- | :-------------------- |
| `save()`    | Persist / update the entity in the backend | `save_dh_function`    |
| `refresh()` | Reload state from backend                  | `refresh_dh_function` |
| `export()`  | Export as YAML file in the context folder  | `export_dh_function`  |
| `run()`     | Execute an action, producing a `Run`       | `run_dh_function`     |

### 5.2 Run method

```python
run = fn.run(
    action="job",         # kind-dependent — see runtime docs
    wait=True,
    log_info=True,
    inputs={"data": dataitem.key},
    parameters={"threshold": 0.5},
)
```

**Parameters (entity-level):**

- `action` (_str_, required): task action name (`'job'`, `'serve'`, `'build'`,
  `'transform'`, ... depending on kind).
- `wait` (_bool_, default `False`).
- `log_info` (_bool_, default `True`).
- `extensions` (_list[dict] | None_).
- `**kwargs`: task/run parameters — content depends on the target kind/action.

**Agent tool:** `run_dh_function(project_name, name, action, wait, log_info, extensions, kwargs)`

For `kind='python'`, prefer the runtime-specific wrappers that enforce correct
action naming and expose the runtime's `inputs`/`parameters`/`init_parameters`/
`resources`/... shape explicitly:

- `run_dh_python_job` — action `'job'`
- `run_dh_python_serve` — action `'serve'`
- `run_dh_python_build` — action `'build'`

---

## 6. Task Methods

Tasks are per-action configurations attached to the function.

| Method        | Purpose                                 | Agent tool                |
| :------------ | :-------------------------------------- | :------------------------ |
| `new_task`    | Create (or update) a task for an action | `new_dh_function_task`    |
| `get_task`    | Get the task for a specific action      | `get_dh_function_task`    |
| `list_task`   | List all tasks of the function          | `list_dh_function_tasks`  |
| `update_task` | Update the task for an action           | `update_dh_function_task` |

Example:

```python
fn.new_task("job", resources={"limits": {"cpu": "2", "memory": "4Gi"}})
```

---

## 7. Trigger Methods

Triggers automate function execution based on schedule or event.

| Method          | Purpose                        | Agent tool                  |
| :-------------- | :----------------------------- | :-------------------------- |
| `trigger`       | Create a trigger for an action | `trigger_dh_function`       |
| `get_trigger`   | Get a trigger by identifier    | `get_dh_function_trigger`   |
| `list_triggers` | List triggers of the function  | `list_dh_function_triggers` |

For detailed trigger kinds (`scheduler`, `lifecycle`) and their spec fields,
see [trigger](trigger.md).

---

## 8. End-to-end Recipe (kind-agnostic pattern)

```python
import digitalhub as dh

# 1. Create the function
fn = dh.new_function(
    project="my-project",
    name="my-fn",
    kind="python",
    code_src="handler.py",
    handler="main",
    python_version="PYTHON3_10",
)

# 2. Build container image (MANDATORY for Python runtime before job execution)
fn.run(action="build", wait=True)

# 3. Execute the job with inputs and parameters
run = fn.run(
    action="job",
    wait=True,
    inputs={"data": my_dataitem.key},
    parameters={"threshold": 0.5},
)

# 4. Read outputs / results via the Run entity
out = run.output("result")
```

Agent-tool equivalent:

```
new_dh_function(project="my-project", name="my-fn", kind="python",
                kwargs={"code_src": "handler.py", "handler": "main",
                        "python_version": "PYTHON3_10"})
# MANDATORY: Build before job execution
run_dh_python_build(project_name="my-project", name="my-fn", wait=True)
run_dh_python_job(project_name="my-project", name="my-fn",
                  inputs={"data": "<dataitem-key>"},
                  parameters={"threshold": 0.5},
                  wait=True)
# then inspect the returned run via:
get_dh_run_output(project="my-project", run_id="<id>", output_name="result")
```

---

## 9. Operational Guidance for the Agent

- **Always Build Before Job / Serve Execution**: For Python runtimes on the platform, **always run the build action before executing job or serve**. The build step compiles dependencies and mounts the handler into the image.
- **Run Failure Self-Correction Protocol**: If a build or job run enters an `ERROR` or `FAILED` state:
  1. Fetch logs with `get_dh_run_logs(project, run_id)`.
  2. Diagnose the root cause from the error traceback.
  3. Correct the function definition or requirements.
  4. Re-build and re-run the job.
- **Pick the correct kind first** — `kind` locks the runtime, the allowed
  actions, and the spec shape. See the kinds table above.
- **For `kind='python'`, prefer the python-runtime tools** (`new_dh_python_function`,
  `run_dh_python_job`, `run_dh_python_serve`, `run_dh_python_build`). They expose
  the runtime-specific spec fields (`handler`, `python_version`, `requirements`,
  `code_src`, ...) and enforce the correct action name.
- **Immutable specs** — to change source, handler, or requirements, register a
  new version via `new_dh_function` (or a new `new_dh_python_function` call). Do
  not attempt to edit spec fields via `update_dh_function`.
- **Run vs Function** — `Function` is the _definition_; each execution creates a
  new `Run` (see [run](run.md)). Function-level lookups return the definition;
  run-level lookups return execution state, outputs, and metrics.
- **Task vs Run** — `Task` is the reusable per-action configuration attached to
  the function; `Run` is one concrete execution of a task. Tasks are usually
  auto-created on the first `run()`; call `new_dh_function_task` explicitly only
  when you need to preset resources/envs/secrets before running.
- **Automation** — attach `scheduler` or `lifecycle` triggers via
  `trigger_dh_function`. Details of trigger kinds and templates live in
  [trigger](trigger.md).
- **Discovery** — use `list_dh_functions` for project-wide scan; filter by
  `kind` to isolate a runtime.
- **Runtime docs** — for each kind, the source of truth for spec fields,
  task/run parameters, and entity-methods lives in the runtime page (e.g.
  [python](../runtimes/python.md)).
