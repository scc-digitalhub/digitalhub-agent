---
type: entity_specification
entity: run
version: "0.16"
tags: [run, execution, lifecycle, metrics, outputs, results, invoke, logs, crud]
tools:
  - new_dh_run
  - get_dh_run
  - import_dh_run
  - list_dh_runs
  - update_dh_run
  - delete_dh_run
  - save_dh_run
  - refresh_dh_run
  - export_dh_run
  - start_dh_run
  - wait_dh_run
  - stop_dh_run
  - resume_dh_run
  - get_dh_run_logs
  - log_dh_run_metric
  - log_dh_run_metrics
  - get_dh_run_output
  - get_dh_run_outputs
  - get_dh_run_result
  - get_dh_run_results
  - invoke_dh_run_service
description: "Specification and reference for the DigitalHub Run entity: representation of a single execution of a Function or Workflow task, including lifecycle, metrics, outputs, results, and service invocation."
---

# DigitalHub Run Specification & SDK Guide

A **Run** is the representation of the execution of a task through a **Function**
or a **Workflow**. It is the entity you use to observe execution state, collect
outputs and results, log training metrics, and (for served endpoints) invoke the
resulting service. Runs are usually created _indirectly_ via `Function.run()`
or `Workflow.run()`; the entity-level CRUD is used for lookup, listing, and
lifecycle control.

---

## 1. Conceptual Model

A run entity holds:

- **Metadata** — auto-generated UUID, `labels`, `kind` (e.g. `python+job:run`).
- **Spec** — task reference, and kind-specific fields such as `inputs`,
  `parameters`, `init_parameters`, `local_execution`, `resources`, `volumes`, ...
- **Status** — backend-managed lifecycle state, log lines, service URL (for
  serve runs), outputs, results, and logged metrics.

A run belongs to a **Project**. Unlike other entities, **runs are not versioned
by name** — each run is addressed by its UUID (or its store key).

Relationship:

```text
Function or Workflow
   |
   |  .run(action=...)
   v
   Task (per-action config, auto-created)
   |
   v
   Run  <- the execution instance
```

### 1.1 Where a run comes from

| Origin                          | Typical call                                                             |
| :------------------------------ | :----------------------------------------------------------------------- |
| Function job/serve/build        | `run_dh_python_job` / `run_dh_python_serve` / `run_dh_python_build`      |
| Function with a non-python kind | `run_dh_function(action=..., kwargs={...})`                              |
| Workflow build/pipeline         | `build_dh_hera_workflow` / `run_dh_hera_pipeline` (or `run_dh_workflow`) |
| Fired by a trigger              | Automatic — inspect via `list_dh_runs(task=..., action=...)`             |
| Explicitly constructed          | `new_dh_run(kind=..., task=..., kwargs={...})` + `start_dh_run`          |

---

## 2. Supported Run Kinds

Run kinds follow a `<runtime>+<action>:run` pattern. Each kind is a subclass of
`Run` with its own `spec`, `status`, and (occasionally) helper methods.

| Kind                      | Runtime / Function kind | Origin action                                                          |
| :------------------------ | :---------------------- | :--------------------------------------------------------------------- |
| `python+job:run`          | `python`                | `job`                                                                  |
| `python+serve:run`        | `python`                | `serve`                                                                |
| `python+build:run`        | `python`                | `build`                                                                |
| `guardrail+serve:run`     | `guardrail`             | `serve`                                                                |
| `guardrail+build:run`     | `guardrail`             | `build`                                                                |
| `openinference+serve:run` | `openinference`         | `serve`                                                                |
| `openinference+build:run` | `openinference`         | `build`                                                                |
| `dbt`                     | `dbt`                   | `transform`                                                            |
| `container`               | `container`             | `job`/`serve`/`build`                                                  |
| `modelserve`              | `modelserve`            | serve (sklearnserve, mlflowserve, huggingfaceserve, vllmserve, kubeai) |
| `flower`                  | `flower`                | flower-app-train / flower-client-_ / flower-server-_                   |
| `hera`                    | `hera` (Workflow)       | `build`, `pipeline`                                                    |

See the runtime documentation of each kind for the precise `spec`/`status`
shape.

---

## 3. Run Lifecycle

```text
        (created by function.run() / workflow.run() / new_dh_run)
                              |
                              v
                   +----------+----------+
                   |     Run entity      |
                   +----------+----------+
                              |
    +-------------------------+-------------------------+
    |                         |                         |
[ wait_dh_run ]        [ stop_dh_run ]           [ resume_dh_run ]
 blocks until               interrupt              re-arm after stop
 terminal state
    |
    v
[ get_dh_run_logs / refresh_dh_run ]
    |
    v
[ get_dh_run_output(s) / get_dh_run_result(s) ]      # after success
    |
    v
[ invoke_dh_run_service ]                            # for serve runs only
```

---

## 4. SDK API Reference (DigitalHub 0.15)

### 4.1 Create — `dh.new_run`

Explicit construction — usually you don't need this; use `Function.run()` /
`Workflow.run()` instead.

```python
run = dh.new_run(
    project="my-project",
    kind="python+job:run",
    task="<task-uri>",
)
```

**Parameters:**

- `project` (_str_, required)
- `kind` (_str_, required — from the table above)
- `uuid` (_str_, optional)
- `labels` (_list[str]_, optional)
- `task` (_str_, optional — task URI)
- `**kwargs`: kind-specific spec fields.

**Agent tool:** `new_dh_run(project, kind, task, uuid, labels, kwargs)`

### 4.2 Read

#### `get_run`

Fetch a run by entity ID or store key.

```python
run = dh.get_run("store://my-project/run/python+job:run/<id>")
run = dh.get_run("<run-id>", project="my-project")
```

**Agent tool:** `get_dh_run(identifier, project)`

_Note:_ runs are addressed by ID (not name); there is no `get_run_versions`.

#### `list_runs`

Lists runs of a project with common filters (`q`, `name`, `kind`, `user`,
`state`, `created`, `updated`) plus **run-specific filters**:
| Filter | Meaning |
| :--------- | :----------------------------------- |
| `function` | Filter by parent function key. |
| `workflow` | Filter by parent workflow key. |
| `task` | Filter by task string. |
| `action` | Filter by action name (job/serve/…). |

**Agent tool:** `list_dh_runs(project, ...)`

#### `import_run`

Load a run from a local YAML file or a store key.
**Agent tool:** `import_dh_run(file, key, reset_id, context)`

### 4.3 Update / Delete

#### `update_run`

Metadata-only update; the run spec is immutable.
**Agent tool:** `update_dh_run(project, run_id)`

#### `delete_run`

Delete a run. Unlike other entities, `delete_run` does **not** accept
`delete_all_versions` or `cascade`.

```python
dh.delete_run("<run-id>", project="my-project")
```

**Agent tool:** `delete_dh_run(identifier, project, entity_id)`

---

## 5. Run Object Methods

### 5.1 CRUD-object methods

| Method      | Purpose                                    | Agent tool       |
| :---------- | :----------------------------------------- | :--------------- |
| `save()`    | Persist / update the entity in the backend | `save_dh_run`    |
| `refresh()` | Reload state from backend (poll)           | `refresh_dh_run` |
| `export()`  | Export as YAML file in the context folder  | `export_dh_run`  |

### 5.2 Lifecycle methods

| Method     | Purpose                                                                             | Agent tool        |
| :--------- | :---------------------------------------------------------------------------------- | :---------------- |
| `run()`    | Start the run (needed only if created explicitly)                                   | `start_dh_run`    |
| `wait()`   | Block until the run reaches a terminal state                                        | `wait_dh_run`     |
| `stop()`   | Interrupt the run                                                                   | `stop_dh_run`     |
| `resume()` | Resume a previously stopped run                                                     | `resume_dh_run`   |
| `logs()`   | Get run logs as `list[Log]`; each `Log.text` is the decoded human-readable content. | `get_dh_run_logs` |

`wait(log_info=True)` streams progress info while blocking.

`get_dh_run_logs` returns the concatenated human-readable log text (the `Log.text`
of every log entry) — this is the container execution output / traceback, ready
for analysis.

### 5.3 Metric methods

| Method                 | Purpose                                   | Agent tool           |
| :--------------------- | :---------------------------------------- | :------------------- |
| `log_metric(key, val)` | Log a single metric (append or overwrite) | `log_dh_run_metric`  |
| `log_metrics(dict)`    | Log multiple metrics at once              | `log_dh_run_metrics` |

Semantics match the `Model.log_metric[s]` methods:

- Default behaviour **appends** to any existing list under the key.
- `overwrite=True` replaces the existing metric.
- `single_value=True` (on `log_metric`) stores a scalar, not a list.

### 5.4 Output / result / invoke methods (kind-specific, common shape)

Most run kinds expose the following on the returned `Run` object; these are
essential for reading results and calling served endpoints.

| Method                          | Purpose                                                             | Agent tool              |
| :------------------------------ | :------------------------------------------------------------------ | :---------------------- |
| `output(name, as_key, as_dict)` | Get a named output (entity, its key, or a dict)                     | `get_dh_run_output`     |
| `outputs(as_key, as_dict)`      | Get all outputs                                                     | `get_dh_run_outputs`    |
| `result(name)`                  | Get a primitive result by name                                      | `get_dh_run_result`     |
| `results()`                     | Get all primitive results                                           | `get_dh_run_results`    |
| `invoke(method, url, **kw)`     | Call the HTTP endpoint of a _serve_ run (default POST if json/data) | `invoke_dh_run_service` |

Rules of thumb:

- **Outputs** are platform entities produced by the handler (Dataitem, Artifact,
  Model). They are declared via the `@handler(outputs=[...])` decorator in
  Python handlers.
- **Results** are primitive values (numbers, strings, dicts).
- **`invoke`** is only valid on serve-kind runs (`python+serve:run`,
  `modelserve`, `container` serve, ...). It reads the service URL from the
  run status if `url` is not supplied.

---

## 6. End-to-end Recipes

### 6.1 Run a job, wait, and read results

```python
import digitalhub as dh

fn = dh.get_function("my-fn", project="my-project")
run = fn.run(
    action="job",
    inputs={"data": my_dataitem.key},
    parameters={"threshold": 0.5},
    wait=True,
)

df = run.output("dataset")           # returns a Dataitem
score = run.result("score")          # returns a primitive
metrics = run.results()              # all primitives
```

Agent-tool equivalent:

```
run_dh_python_job(project_name="my-project", name="my-fn",
                  inputs={"data": "<dataitem-key>"},
                  parameters={"threshold": 0.5})
# → returned run has an id; then:
get_dh_run_output(project="my-project", run_id="<id>", output_name="dataset")
get_dh_run_result(project="my-project", run_id="<id>", result_name="score")
get_dh_run_results(project="my-project", run_id="<id>")
```

### 6.2 Track training metrics from the handler

Inside a handler, use the injected `run` object:

```python
def train(project, run, context, event, data):
    ...
    run.log_metric("loss", 0.42)
    run.log_metric("loss", 0.31)          # appended
    run.log_metric("accuracy", 0.92, single_value=True)
```

Agent-tool equivalent (from outside the run):

```
log_dh_run_metric(project="my-project", run_id="<id>", key="loss", value=0.42)
log_dh_run_metric(project="my-project", run_id="<id>", key="loss", value=0.31)
log_dh_run_metric(project="my-project", run_id="<id>", key="accuracy",
                  value=0.92, single_value=True)
```

### 6.3 Invoke a served endpoint

```python
fn = dh.get_function("classify", project="my-project")
serve = fn.run(action="serve", wait=True)
resp = serve.invoke(json={"text": "hello"})
print(resp.status_code, resp.json())
```

Agent-tool equivalent:

```
run_dh_python_serve(project_name="my-project", name="classify")
# grab the id from the returned run, then:
invoke_dh_run_service(project="my-project", run_id="<id>",
                      kwargs={"json": {"text": "hello"}})
```

### 6.4 Stop, resume, and inspect logs

```python
run = dh.get_run("<id>", project="my-project")
run.stop()
run.refresh()
print(run.logs())
run.resume()
run.wait()
```

Agent-tool equivalent:

```
stop_dh_run(project="my-project", run_id="<id>")
refresh_dh_run(project="my-project", run_id="<id>")
get_dh_run_logs(project="my-project", run_id="<id>")
resume_dh_run(project="my-project", run_id="<id>")
wait_dh_run(project="my-project", run_id="<id>")
```

### 6.5 Filter runs of a function

```python
runs = dh.list_runs(
    project="my-project",
    function="python://my-project/my-fn:<uuid>",
    action="job",
    state="COMPLETED",
)
```

Agent-tool equivalent:

```
list_dh_runs(project="my-project",
             function="python://my-project/my-fn:<uuid>",
             action="job",
             state="COMPLETED")
```

### 6.6 Diagnose a failed run and self-correct

When a run may have failed, diagnose it and read the human-readable logs
(`Log.text`) to drive an automatic fix.

```python
run = dh.get_run("<id>", project="my-project")
run.refresh()
if run.status.state in ("ERROR", "FAILED", "ABORTED"):
    for log in run.logs():
        print(log.text)          # decoded human-readable traceback
    # → identify the cause, correct the function / requirements, re-build, rerun
```

Agent-tool equivalent:

```
get_dh_run_logs(project="my-project", run_id="<id>")
# → human-readable traceback and stdout/stderr
# inspect logs, then:
update_dh_function(...)                 # or new_dh_python_function(...)
run_dh_python_build(project_name="my-project", name="my-fn")   # wait until COMPLETED
run_dh_python_job(project_name="my-project", name="my-fn")
```

---

## 7. Operational Guidance for the Agent

- **Prefer indirect creation** — call `run_dh_function` (or a python-runtime
  wrapper) / `run_dh_workflow` to create runs implicitly. Use `new_dh_run`
  only when you must build a `Run` up-front (e.g. detached from
  `Function.run()`), and call `start_dh_run` to execute it.
- **Addressing** — runs are identified by UUID (or store key). There is no
  version tuple. Do not pass `entity_id` alongside a name to `get_dh_run`.
- **Filters** — `list_dh_runs` supports `function`, `workflow`, `task`, and
  `action` filters in addition to the common ones — use them to narrow to a
  specific parent.
- **Deletion** — `delete_dh_run` has no `cascade` and no
  `delete_all_versions`; deletion targets a single run.
- **Long executions** — after firing an action, either pass `wait=True` at
  invocation time or call `wait_dh_run` explicitly. Use `refresh_dh_run` to
  poll state without blocking.
- **Handling Failed Runs (Logs $\rightarrow$ Fix $\rightarrow$ Rerun)** — when a run ends in an
  `ERROR` / `FAILED` / `ABORTED` state, do not abandon or guess: call
  `get_dh_run_logs(project, run_id)` to fetch the execution traceback. Read the logs,
  identify the root cause (missing dependency, handler bug, wrong input parameter,
  build failure), correct the function code or requirements yourself, re-build
  with `wait=True` until `COMPLETED` if needed, and rerun the job.
- **Outputs vs results** — outputs are DigitalHub entities (Dataitem, Artifact,
  Model). Results are primitives. Pick the correct accessor.
- **Invoke** — only meaningful for serve runs. The default HTTP method is POST
  when `json`/`data` is provided in `kwargs`, otherwise GET.
- **Metrics** — `run.log_metric` / `run.log_metrics` share semantics with
  `Model.log_metric[s]`: append by default; `overwrite=True` to replace;
  `single_value=True` (on `log_metric`) to store a scalar.
- **Kind ↔ helper mapping** — for details of parameters accepted at run time,
  consult the runtime doc of the corresponding kind (for `python`, see
  [python](../runtimes/python.md)).

---

## 8. Dynamic Tool Discovery & Domain Scoping

Run entity tools are excluded from the initial startup toolset to prevent tool context creep and keep agent execution lean.

### Activation Mechanisms

1. **Dynamic Toolset Registration (`scan_and_create_dh_tools`)**:
   - Call `scan_and_create_dh_tools('run')` to dynamically reflect on `dh.*run*` and the `Run` class methods.
   - Instantiates 25 typed tools (`get_dh_run`, `list_dh_runs`, `wait_dh_run`, `stop_dh_run`, `get_dh_run_logs`, `log_dh_run_metric`, outputs/results helpers, etc.) into the active context.
   - Automatically unloads any previously active domain tools to keep context usage strictly bounded.

2. **Universal Dispatcher (`call_dh_sdk`)**:
   - For quick one-off operations without modifying your toolset:
     ```python
     call_dh_sdk(
         entity="run",
         operation="list_runs",
         parameters={"project": "my-project"}
     )
     ```
