---
type: runtime_specification
runtime: python
kind: python
version: "0.15"
tags:
  [
    runtime,
    python,
    handler,
    job,
    serve,
    build,
    inputs,
    parameters,
    requirements,
    python_version,
    nuclio,
  ]
tools:
  - new_dh_python_function
  - run_dh_python_job
  - run_dh_python_serve
  - run_dh_python_build
description: "Specification and reference for the DigitalHub Python runtime: writing @handler code, function spec fields (python_version, code_src, handler, requirements, ...), and the job/serve/build actions."
---

# DigitalHub Python Runtime Guide

The **Python runtime** executes user-defined Python handlers on the DigitalHub
platform. It backs `Function` entities of `kind='python'` and supports the
`job`, `serve`, and `build` actions. This document covers only the Python
runtime; for the generic function entity surface, see [function](../entities/function.md);
for the run entity surface, see [run](../entities/run.md).

Runtime package: **`digitalhub-runtime-python`**.

---

## 1. Supported kinds and actions

| Function kind | Actions                 | Runtime package             |
| :------------ | :---------------------- | :-------------------------- |
| `python`      | `job`, `serve`, `build` | `digitalhub-runtime-python` |

Action semantics:

- `job` — execute the handler as a one-off task on Kubernetes (or locally).
- `serve` — deploy the handler as a long-lived HTTP endpoint (Nuclio-backed).
- `build` — build a container image with the handler and its dependencies.

The corresponding **Run kinds** are `python+job:run`, `python+serve:run`,
`python+build:run` (see [run](../entities/run.md)).

---

## 2. Prerequisites

- Package requirement: **Python `>= 3.10, < 3.15`** for the SDK client.
- Execution Python version (in-container) must be one of:
  - `PYTHON3_10`
  - `PYTHON3_11`
  - `PYTHON3_12`
  - `PYTHON3_13`
- Install runtime package: `pip install digitalhub-runtime-python`

---

## 3. Defining a Python handler

A handler is a Python function declared with the standard `def` keyword. It
becomes the entrypoint when referenced by `handler` in the function spec.

### 3.1 Function anatomy

```python
from digitalhub_runtime_python import handler

@handler(outputs=["my-sdk-output", "my-primitive-output"])
def func(project, run, context, event, input_1, parameter_1):
    project.log_artifact("my-artifact", "artifact", source="some-file.ext")
    run.log_metric("my-metric", -14.6)
    context.logger.info("log-some-string")

    body = event.body

    df = input_1.as_df(sep=";")
    df.head(70)
    parameter_1.pop("some-key")

    return df, 19.45
```

Simple handler (no parameters, no return):

```python
def func():
    print("hello world")
```

### 3.2 Reserved arguments

The runtime injects these when it invokes your handler:

| Argument  | Meaning                                                                  |
| :-------- | :----------------------------------------------------------------------- |
| `project` | The current `Project` entity object.                                     |
| `run`     | The active `Run` entity object (usable for `log_metric`, `log_metrics`). |
| `context` | Nuclio runtime context — **remote execution only**.                      |
| `event`   | Nuclio event — **remote execution only**.                                |

> **Local execution:** `context` and `event` are not provided automatically.
> If your handler expects them, pass them explicitly through `function.run()`.

### 3.3 Inputs and parameters

- **Inputs** must reference platform entities (`Dataitem`, `Artifact`, `Model`)
  by their **keys**.
- **Parameters** are plain Python values (strings, numbers, dicts, lists, ...).

```python
def func(di, param1):
    ...

fn.run(
    inputs={"di": some_dataitem.key},
    parameters={"param1": "some value"},
)
```

> **Common pitfall:** passing a parameter where an input is expected will produce
> an error stating the SDK cannot parse an `entity_key`. Double-check which
> values you provided in `inputs` vs `parameters`.

### 3.4 `@handler` decorator and named outputs

```python
from digitalhub_runtime_python import handler

@handler(outputs=["data", "string"])
def func(di, param1):
    return pd.DataFrame(...), "some value"

run = fn.run(inputs={"di": di.key}, parameters={"param1": "x"}, wait=True)
run.output("data")     # -> a Dataitem
run.result("string")   # -> "some value"
```

Omitting the decorator makes the SDK assign placeholder names to returned values.
Use `@handler(outputs=[...])` to name them explicitly.

### 3.5 Init function (remote only)

When executing remotely, the Nuclio wrapper calls an `init` function (if
present) before invoking the handler. The Nuclio `context` is injected into
`init`; extra values come through `init_parameters`.

```python
def init(context, param1, param2):
    ...

fn.run(init_parameters={"param1": "a", "param2": "b"})
```

Reference the init function name via the `init_function` spec field.

---

## 4. Function spec fields (`kind='python'`)

These are set when creating the function. Prefer the `new_dh_python_function`
tool, which exposes them explicitly.

| Field            | Type      | Required | Description                                                                       |
| :--------------- | :-------- | :------: | :-------------------------------------------------------------------------------- |
| `kind`           | str       |    ✅    | Must be `python`.                                                                 |
| `handler`        | str       |    ✅    | Handler entrypoint (e.g. `main`).                                                 |
| `python_version` | str       |    ✅    | One of `PYTHON3_10`..`PYTHON3_13`.                                                |
| `code_src`       | str       |          | URI to source (local, http, git, s3). One of `code_src`/`code`/`base64` required. |
| `code`           | str       |          | Source as plain text.                                                             |
| `base64`         | str       |          | Source encoded as base64.                                                         |
| `init_function`  | str       |          | Init function name (Nuclio init wrapper — remote only).                           |
| `lang`           | str       |          | Source-code language (informational).                                             |
| `image`          | str       |          | Container image used to execute the function.                                     |
| `base_image`     | str       |          | Base image (`name:tag`) used to build the execution image.                        |
| `requirements`   | list[str] |          | Pip requirements installed into the execution image.                              |

Notes:

- **Base image**: deploying jobs built from certain base images may be restricted
  by cluster security policies — confirm allowed base images with your admin.
- **Requirements** example:
  ```python
  requirements = ["numpy", "pandas>1,<3", "scikit-learn==1.2.0"]
  ```

**Agent tool:** `new_dh_python_function(project, name, handler, python_version, code_src, code, base64, init_function, lang, image, base_image, requirements, uuid, description, labels, embedded)`

---

## 5. Actions

### 5.1 `job` — one-off task

```python
run = fn.run(
    action="job",
    inputs={"data": dataitem.key},
    parameters={"threshold": 0.5},
)
```

**Task parameters** (passed via `function.run()`):
| Field | Type | Description |
| :--------- | :--------- | :----------------------------------- |
| `action` | str | Required, must be `"job"`. |
| `volumes` | list[dict] | Attached volumes. |
| `resources`| dict | K8s resource limits/requests. |
| `envs` | list[dict] | Environment variables. |
| `secrets` | list[str] | Secret names to mount. |
| `profile` | str | Profile template. |

**Run parameters** (passed via `function.run()`):
| Field | Type | Description |
| :---------------- | :--- | :-------------------------------------------------------------- |
| `local_execution` | bool | Execute locally instead of on the cluster. |
| `inputs` | dict | Maps handler arg names → entity keys. |
| `parameters` | dict | Extra primitive parameters for the handler. |
| `init_parameters` | dict | Values supplied to the init function (remote execution only). |

**Agent tool:** `run_dh_python_job(project_name, name, local_execution, inputs, parameters, init_parameters, volumes, resources, envs, secrets, profile, wait, log_info)`

### 5.2 `serve` — HTTP endpoint

```python
run = fn.run(
    action="serve",
    inputs={"data": dataitem.key},
    parameters={"threshold": 0.5},
)
```

Serve is **remote-only**. Additional task parameters vs `job`:

| Field          | Type | Description                           |
| :------------- | :--- | :------------------------------------ |
| `action`       | str  | Required, must be `"serve"`.          |
| `replicas`     | int  | Number of replicas.                   |
| `service_type` | str  | Kubernetes service type.              |
| `service_name` | str  | Name assigned to the created service. |

Run parameters are the same as `job` except `local_execution` is not applicable.

To call the served endpoint, use `invoke_dh_run_service` (from the run
toolset).

**Agent tool:** `run_dh_python_serve(project_name, name, inputs, parameters, init_parameters, replicas, service_type, service_name, volumes, resources, envs, secrets, profile, wait, log_info)`

### 5.3 `build` — build a container image

```python
run = fn.run(
    action="build",
    instructions=["apt-get install -y git", "apt-get install -y curl"],
)
```

Task parameters are those shared with `job`, plus:
| Field | Type | Description |
| :------------- | :-------- | :-------------------------------------------------------------- |
| `action` | str | Required, must be `"build"`. |
| `instructions` | list[str] | Executed as `RUN` lines in the generated Dockerfile. |

Run parameters (`inputs`, `parameters`, `init_parameters`) may also be supplied.

**Agent tool:** `run_dh_python_build(project_name, name, instructions, inputs, parameters, init_parameters, volumes, resources, envs, secrets, profile, wait, log_info)`

---

## 6. Local vs remote execution

Applies to `job` (and, indirectly, to how you develop handlers):

- **Local (`local_execution=True`)** — runs on the calling machine. You must have
  the required dependencies installed locally. `context`/`event` are not
  injected.
- **Remote (default)** — the function runs on the cluster. Dependencies must be
  declared via `requirements` (or ship a `requirements.txt` alongside the
  source). `serve` requires remote execution.

---

## 7. Run object surface (Python runtime specifics)

Once a run is created, all common Run methods (see [run](../entities/run.md))
are available. The Python runtime is where the **output / result / invoke**
surface is most relevant:

| Method                                      | Applies to      | Agent tool                                |
| :------------------------------------------ | :-------------- | :---------------------------------------- |
| `output(name, as_key, as_dict)`             | job/serve/build | `get_dh_run_output`                       |
| `outputs(as_key, as_dict)`                  | job/serve/build | `get_dh_run_outputs`                      |
| `result(name)`                              | job/serve/build | `get_dh_run_result`                       |
| `results()`                                 | job/serve/build | `get_dh_run_results`                      |
| `invoke(method, url, **kw)`                 | **serve only**  | `invoke_dh_run_service`                   |
| `wait`, `stop`, `resume`, `logs`, `refresh` | all             | see [run](../entities/run.md)             |
| `log_metric`, `log_metrics`                 | all             | `log_dh_run_metric`, `log_dh_run_metrics` |

---

## 8. End-to-end Recipes

### 8.1 Build then run Job (Standard Workflow)

> **MANDATORY**: For Python runtimes on the platform, **always build before job execution**. The `build` step compiles the container image with the declared `requirements` and mounts the handler code. Attempting to execute `job` without a prior successful `build` will result in missing dependencies or `ExecutionError`.

```python
import digitalhub as dh

# 1. Define Function
fn = dh.new_function(
    project="my-project",
    name="classify",
    kind="python",
    code_src="handler.py",
    handler="main",
    python_version="PYTHON3_10",
    requirements=["scikit-learn==1.2.0", "pandas"],
)

# 2. Build Container Image (Mandatory)
build_run = fn.run(action="build", wait=True)

# 3. Execute Job
job_run = fn.run(
    action="job",
    inputs={"data": dataitem.key},
    parameters={"threshold": 0.5},
    wait=True,
)
print(job_run.results())
```

Agent-tool equivalent:

```
# Step 1: Create function definition
new_dh_python_function(project="my-project", name="classify", handler="main",
                       python_version="PYTHON3_10",
                       code_src="handler.py",
                       requirements=["scikit-learn==1.2.0", "pandas"])

# Step 2: Build container image (MANDATORY before job)
run_dh_python_build(project_name="my-project", name="classify", wait=True)

# Step 3: Execute Job
run_dh_python_job(project_name="my-project", name="classify",
                  inputs={"data": "<dataitem-key>"},
                  parameters={"threshold": 0.5},
                  wait=True)

# Step 4: Retrieve Results
get_dh_run_results(project="my-project", run_id="<job-run-id>")
```

### 8.2 Build then serve

```python
fn = dh.get_function("classify", project="my-project")
fn.run(action="build", instructions=["apt-get install -y git"], wait=True)
serve = fn.run(action="serve", wait=True)
resp = serve.invoke(json={"text": "hello"})
```

Agent-tool equivalent:

```
run_dh_python_build(project_name="my-project", name="classify",
                    instructions=["apt-get install -y git"])
run_dh_python_serve(project_name="my-project", name="classify")
invoke_dh_run_service(project="my-project", run_id="<serve-run-id>",
                      kwargs={"json": {"text": "hello"}})
```

### 8.3 Handler that logs a model and metrics

```python
from digitalhub_runtime_python import handler

@handler(outputs=["model"])
def train(project, run, di):
    from sklearn.ensemble import GradientBoostingClassifier
    df = di.as_df()
    model = GradientBoostingClassifier().fit(df.drop(columns=["y"]), df["y"])
    run.log_metric("accuracy", 0.94, single_value=True)
    m = project.log_model("churn", kind="sklearn", source="./model.pkl")
    return m
```

---

## 9. Operational Guidance for the Agent

- **Always Build Before Job / Serve Execution**: For Python runtimes, it is **necessary to execute a build action** (`run_dh_python_build` or `build_dh_function`) before executing a `job` or `serve` action. The build step validates syntax, installs pip `requirements`, and registers the container image. Never attempt to run a job without building first.
- **Troubleshooting & Automated Error Recovery Protocol**:
  Whenever a build run or job run fails or enters an `ERROR`/`FAILED` state:
  1. **Fetch Logs Immediately**: Call `get_dh_run_logs(project="<project>", run_id="<failed-run-id>")` to inspect stdout/stderr and tracebacks.
  2. **Diagnose from Logs**: Locate the failure source (e.g. missing package in `requirements`, syntax error in handler code, missing input parameter, incorrect handler signature).
  3. **Correct the Function**: Update the function definition using `new_dh_python_function` or `update_dh_function` with the corrected code, imports, or dependencies.
  4. **Re-Build & Re-Run**: Trigger `run_dh_python_build` (with `wait=True`), ensure the build completes successfully, and then re-execute `run_dh_python_job`.
- **Enforce required spec fields** — `kind='python'`, `handler`, and
  `python_version` are mandatory. Provide exactly one of `code_src` / `code` /
  `base64` for the source.
- **Prefer `new_dh_python_function`** — it exposes the runtime spec fields
  explicitly; use `new_dh_function(kind="python", kwargs={...})` only when you
  need generic construction.
- **Prefer the runtime action wrappers** — `run_dh_python_job`,
  `run_dh_python_serve`, `run_dh_python_build` enforce the correct action name
  and expose the parameter shape. Fall back to `run_dh_function(action=...)`
  only for uncommon extension cases.
- **Serve is remote-only** — `local_execution` is not applicable to `serve`.
- **Inputs vs parameters** — inputs are entity keys, parameters are primitives.
  Never pass entity keys through `parameters`.
- **Requirements** — declare pip specifiers via `requirements`; needed for
  remote execution unless already baked into `image`.
- **Invoke a served function** via `invoke_dh_run_service` — the service URL is
  taken from the run status if `url` is not supplied.
- **After firing a run** — either pass `wait=True` at invocation time or call
  `wait_dh_run` to block; use `get_dh_run_logs` / `refresh_dh_run` for
  non-blocking inspection.
- **Read outputs and results** through the run entity (`get_dh_run_output`,
  `get_dh_run_result`, ...), not through the function entity.
- **Sibling runtimes** — `guardrail` and `openinference` are Python-family
  runtimes with a similar shape but different actions (they lack `job`).
