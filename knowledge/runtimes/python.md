---
type: runtime_specification
runtime: python
kind: python
version: "0.16"
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

### 3.1 Standard Function Anatomy (Recommended)

Standard Python functions do **NOT** require any decorator or runtime imports. They run directly in the container:

```python
def func(project, run, input_1, parameter_1):
    # Standard python libraries (e.g. pandas, scikit-learn)
    df = input_1.as_df(sep=";")

    # Log artifacts or metrics directly via project or run
    project.log_artifact(source="some-file.ext", name="my-artifact")
    run.log_metric("my-metric", -14.6)

    return {"status": "success"}
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

### 3.4 Optional: `@handler` decorator and named outputs

The `@handler` decorator is **strictly optional**. For standard workloads, write plain functions as shown in Section 3.1.
If you do use `@handler(outputs=[...])` to map returned tuples directly to platform outputs:

```python
from digitalhub_runtime_python import handler

@handler(outputs=["data", "string"])
def func(di, param1):
    return pd.DataFrame(...), "some value"

run = fn.run(inputs={"di": di.key}, parameters={"param1": "x"}, wait=True)
run.output("data")     # -> a Dataitem
run.result("string")   # -> "some value"
```

> ⚠️ **CRITICAL DEPENDENCY REQUIREMENT**:
> If your function source code imports `from digitalhub_runtime_python import handler`, you **MUST** include `"digitalhub-runtime-python"` in the function's `requirements` parameter:
> `new_dh_python_function(..., requirements=["digitalhub-runtime-python", ...])`.
> If omitted from `requirements`, execution in the deployed container will fail with:
> `ModuleNotFoundError: No module named 'digitalhub_runtime_python'`.
> **Best Practice**: Prefer plain functions without the `@handler` decorator for standard jobs and training scripts.

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

These are set when creating the function. In SDK 0.16, functions can be created either from a `Project` instance or directly from top-level `dh`.

### 4.1 Creation methods

```python
import digitalhub as dh

# Method A: Create from Project instance
project = dh.get_or_create_project("my-project")
function = project.new_function(
    name="my-python-function",
    kind="python",
    code_src="main.py",
    handler="function",
    python_version="PYTHON3_10",
)

# Method B: Create from SDK top-level
function = dh.new_function(
    project="my-project",
    name="my-python-function",
    kind="python",
    code_src="main.py",
    handler="function",
    python_version="PYTHON3_10",
)
```

### 4.2 Spec parameters

| Field            | Type             | Required | Description                                                                                 |
| :--------------- | :--------------- | :------: | :------------------------------------------------------------------------------------------ |
| `project`        | str              |    *     | Project name. Required when creating via `dh.new_function()`; MUST NOT be passed when creating via `project.new_function()`. |
| `name`           | str              |    ✅    | Name that identifies the function object.                                                   |
| `kind`           | str              |    ✅    | Function kind. Must be `python`.                                                            |
| `handler`        | str              |    ✅    | Function entrypoint (e.g. `main` or `function`).                                            |
| `python_version` | str              |    ✅    | Python version to use: `PYTHON3_10`, `PYTHON3_11`, `PYTHON3_12`, or `PYTHON3_13`.           |
| `code_src`       | str              |          | URI pointing to the source code (local path, http, git, s3).                                |
| `code`           | str              |          | Source code provided directly as plain text.                                                |
| `base64`         | str              |          | Source code encoded as base64 string.                                                       |
| `init_function`  | str              |          | Init function entrypoint for remote (Nuclio) execution.                                     |
| `lang`           | str              |          | Source code language (informational).                                                       |
| `image`          | str              |          | Container image used to execute the function.                                               |
| `base_image`     | str              |          | Base image (`name:tag`) used to build the execution image.                                  |
| `requirements`   | list[str] \| str |          | List of pip requirements or a path to a supported requirements file.                        |
| `uuid`           | str              |          | Object ID in UUID4 format.                                                                  |
| `description`    | str              |          | Human-readable description of the function object.                                          |
| `labels`         | list[str]        |          | List of tags / labels.                                                                      |
| `embedded`       | bool             |          | Whether the function object should be embedded directly in the project (default `False`).  |

> ⚠️ **Base Image Security Warning**:
> Deploying jobs built from certain base images may be restricted by cluster security policies. Confirm allowed base images with your cluster administrator.

### 4.3 Requirements handling

Requirements can be supplied as a list of strings or as a path to an existing file:
- File formats supported: `requirements.txt`, `setup.py`, `pyproject.toml`, `conda.yml`, or `conda.yaml`.
- The SDK parses and normalizes them when the function is saved (`requirements.txt` and `setup.py` as pip requirements, `pyproject.toml` from `project.dependencies`, and Conda from `dependencies.pip`).
- **Automatic version inference**: If a package is specified without an explicit version (e.g. `"pandas"`), the SDK looks for it in the active local virtual environment, resolves the installed version, and logs an informational warning.

```python
requirements = ["numpy", "pandas>1,<3", "scikit-learn==1.2.0"]
```

### 4.4 Function methods

- **`function.build(wait=True, log_info=True, extensions=None, **kwargs) -> Run`**:
  Direct method to build the container image for the Python function using the `build` action.
- **`function.run(action, wait=False, log_info=True, extensions=None, **kwargs) -> Run`**:
  General entrypoint to execute a task (`job`, `serve`, or `build`).

**Agent tool:** `new_dh_python_function(project, name, handler, python_version, code_src, code, base64, init_function, lang, image, base_image, requirements, uuid, description, labels, embedded)`

---

## 5. Actions

### 5.1 `job` — one-off task

The `job` action executes a Python function as a one-off task on Kubernetes (or locally). It supports handlers that run to completion.

```python
run = function.run(
    action="job",
    inputs={"dataitem": dataitem.key},
    parameters={"param1": "value1"},
)
```

**Task parameters** (passed to `function.run()`):
| Field       | Type        | Description                             |
| :---------- | :---------- | :-------------------------------------- |
| `action`    | str         | Required, must be `"job"`.              |
| `volumes`   | list[dict]  | List of attached storage volumes.       |
| `resources` | dict        | Kubernetes resource limits and requests.|
| `envs`      | list[dict]  | Environment variables.                  |
| `secrets`   | list[str]   | Secret names to mount into the run.     |
| `profile`   | str         | Profile template.                       |

**Run parameters** (passed to `function.run()`):
| Field              | Type | Default | Description                                                                                 |
| :----------------- | :--- | :-----: | :------------------------------------------------------------------------------------------ |
| `local_execution`  | bool | `False` | Execute the run locally on the client instead of remotely on the cluster.                   |
| `auto_build`       | bool | `False` | Build the function automatically when `spec.image` is `None`. (If requirements are present, an existing image is not rebuilt). |
| `inputs`           | dict |         | Mapping of function argument names to entity keys (e.g. `Dataitem`, `Artifact`, `Model`).   |
| `parameters`       | dict |         | Extra primitive parameters passed to the function.                                          |
| `init_parameters`  | dict |         | Parameters supplied to the init function.                                                   |

**Agent tool:** `run_dh_python_job(project_name, name, local_execution, inputs, parameters, init_parameters, volumes, resources, envs, secrets, profile, wait, log_info)`

### 5.2 `serve` — HTTP endpoint

The `serve` action deploys a Python function as an HTTP endpoint on Kubernetes backed by Nuclio. It supports handlers that respond to incoming HTTP requests. Serving functions are **available only with remote execution**.

```python
run = function.run(
    action="serve",
    replicas=2,
    service_type="NodePort",
)
```

**Task parameters** (shared with `job`, plus service networking):
| Field          | Type | Description                                            |
| :------------- | :--- | :----------------------------------------------------- |
| `action`       | str  | Required, must be `"serve"`.                           |
| `replicas`     | int  | Number of service pod replicas.                        |
| `service_type` | str  | Kubernetes service type (e.g. `"NodePort"`, `"ClusterIP"`). |
| `service_name` | str  | Name assigned to the created Kubernetes service.       |
| `volumes`      | list[dict] | Storage volumes.                                 |
| `resources`    | dict | Kubernetes resource limits/requests.                   |
| `envs`         | list[dict] | Environment variables.                           |
| `secrets`      | list[str]  | Secrets to mount.                                |
| `profile`      | str  | Profile template.                                      |

**Run parameters**:
| Field             | Type | Default | Description                                                       |
| :---------------- | :--- | :-----: | :---------------------------------------------------------------- |
| `auto_build`      | bool | `False` | Build the function automatically when `spec.image` is `None`.     |
| `inputs`          | dict |         | Entity keys mapped to handler arguments.                          |
| `parameters`      | dict |         | Primitive arguments.                                              |
| `init_parameters` | dict |         | Parameters supplied to the init function.                         |

**Invoking the service**:
```python
# Invoke endpoint via requests.Response:
response = run.invoke(json={"some-func-param": "value"})

# The service URL can be inspected directly from the run status:
service_url = run.status.service["url"]
```

**Agent tool:** `run_dh_python_serve(project_name, name, inputs, parameters, init_parameters, replicas, service_type, service_name, volumes, resources, envs, secrets, profile, wait, log_info)`

### 5.3 `build` — build container image

The `build` action builds a container execution image for the Python function using Kaniko on Kubernetes.

```python
run = function.run(
    action="build",
    instructions=["apt-get install -y git", "apt-get install -y curl"],
)
# Or directly via build method:
run = function.build(instructions=["apt-get install -y git"])
```

**Task parameters**:
| Field          | Type      | Description                                                       |
| :------------- | :-------- | :---------------------------------------------------------------- |
| `action`       | str       | Required, must be `"build"`.                                      |
| `instructions` | list[str] | Build instructions executed as `RUN` lines in the generated Dockerfile. |
| `volumes`, `resources`, `envs`, `secrets`, `profile` | | Standard task parameters. |

**Run methods for build**:
- `run.image()`: Returns the container image tag generated by the build (`str | None`).

**Agent tool:** `run_dh_python_build(project_name, name, instructions, inputs, parameters, init_parameters, volumes, resources, envs, secrets, profile, wait, log_info)`

---

## 6. Local vs remote execution

Applies to `job` execution:

- **Local (`local_execution=True`)**: Runs on the calling machine. Dependencies must be installed in the current environment. `context` and `event` are not injected automatically.
- **Remote (default, `local_execution=False`)**: The function executes inside a container pod on the Kubernetes cluster. Dependencies must be declared via `requirements` or baked into `image`.
- **`serve` and `build`**: Strictly remote execution on the platform.

---

## 7. Run object surface (Python runtime specifics)

Once an action produces a `Run` entity, the following runtime-specific inspection methods are available:

| Method                                      | Applies to        | Description                                                                                 | Agent tool                                |
| :------------------------------------------ | :---------------- | :------------------------------------------------------------------------------------------ | :---------------------------------------- |
| `inputs(as_dict=False)`                     | all               | Returns inputs passed in spec as objects (or dicts if `as_dict=True`).                      | —                                         |
| `output(output_name, as_key=F, as_dict=F)`  | job / serve / build| Returns named platform entity output (or key / dict).                                       | `get_dh_run_output`                       |
| `outputs(as_key=False, as_dict=False)`      | job / serve / build| Returns dictionary of all run output objects.                                               | `get_dh_run_outputs`                      |
| `result(result_name)`                       | job / serve / build| Returns named primitive result value.                                                       | `get_dh_run_result`                       |
| `results()`                                 | job / serve / build| Returns dictionary of all primitive results.                                                | `get_dh_run_results`                      |
| `image()`                                   | **build only**    | Returns the container image string generated by the build run (`str \| None`).              | —                                         |
| `invoke(method='POST', url=None, **kwargs)` | **serve only**    | Dispatches HTTP request to the served service endpoint. Returns `requests.Response`.         | `invoke_dh_run_service`                   |
| `status.service['url']`                     | **serve only**    | URL of the deployed HTTP service endpoint.                                                 | —                                         |
| `logs()`                                    | all               | Retrieves stdout/stderr logs from the execution pod.                                        | `get_dh_run_logs`                         |

---

## 8. End-to-end Recipes & Examples

### 8.1 Build then run Job (Standard Platform Pattern)

> 💡 **Best Practice**: For Python runtimes on the platform, execute `build` (or use `auto_build=True`) prior to executing a remote job so dependencies and handler files are compiled into the image.

```python
import digitalhub as dh

# 1. Obtain Project
project = dh.get_or_create_project("my-project")

# 2. Define Function
fn = project.new_function(
    name="classify",
    kind="python",
    code_src="handler.py",
    handler="train",
    python_version="PYTHON3_10",
    requirements=["scikit-learn==1.2.0", "pandas"],
)

# 3. Build Container Image
build_run = fn.run(action="build", wait=True)
print(f"Built image: {build_run.image()}")

# 4. Execute Job
di = project.get_dataitem("iris-dataset")
job_run = fn.run(
    action="job",
    inputs={"dataitem": di.key},
    parameters={"threshold": 0.5},
    wait=True,
)
print("Results:", job_run.results())
print("Output artifact:", job_run.output("model"))
```

Agent-tool equivalent:

```
# Step 1: Create function
new_dh_python_function(project="my-project", name="classify", handler="train",
                       python_version="PYTHON3_10",
                       code_src="handler.py",
                       requirements=["scikit-learn==1.2.0", "pandas"])

# Step 2: Build container image
run_dh_python_build(project_name="my-project", name="classify", wait=True)

# Step 3: Execute Job
run_dh_python_job(project_name="my-project", name="classify",
                  inputs={"dataitem": "dataitem://my-project/iris-dataset"},
                  parameters={"threshold": 0.5},
                  wait=True)

# Step 4: Retrieve Results
get_dh_run_results(project="my-project", run_id="<job-run-id>")
```

### 8.2 Build then Deploy Service (`serve`) and Invoke

```python
import digitalhub as dh

project = dh.get_or_create_project("my-project")

# 1. Define Serving Function
fn = project.new_function(
    name="inference-service",
    kind="python",
    code_src="serve_handler.py",
    handler="predict",
    python_version="PYTHON3_11",
    requirements=["fastapi", "uvicorn", "pydantic"],
)

# 2. Build image with system instructions
fn.run(action="build", instructions=["apt-get update && apt-get install -y curl"], wait=True)

# 3. Deploy as Service
serve_run = fn.run(
    action="serve",
    replicas=2,
    service_type="NodePort",
    wait=True,
)

# 4. Invoke service endpoint
response = serve_run.invoke(json={"features": [5.1, 3.5, 1.4, 0.2]})
print("Service Response:", response.json())
```

Agent-tool equivalent:

```
run_dh_python_build(project_name="my-project", name="inference-service",
                    instructions=["apt-get update && apt-get install -y curl"],
                    wait=True)

run_dh_python_serve(project_name="my-project", name="inference-service",
                    replicas=2, service_type="NodePort",
                    wait=True)

invoke_dh_run_service(project="my-project", run_id="<serve-run-id>",
                      kwargs={"json": {"features": [5.1, 3.5, 1.4, 0.2]}})
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
    m = project.log_model(source="./model.pkl", name="churn", framework="sklearn")
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
