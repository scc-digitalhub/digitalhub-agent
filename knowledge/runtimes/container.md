---
type: runtime_specification
runtime: container
kind: container
version: "0.16"
tags:
  [
    runtime,
    container,
    job,
    serve,
    build,
    docker,
    kubernetes,
    images,
    replicas,
    service,
    instructions,
  ]
tools:
  - new_dh_container_function
  - run_dh_container_job
  - run_dh_container_serve
  - run_dh_container_build
description: "Specification and reference for the DigitalHub Container runtime: custom Docker images, commands, build action (Dockerfile generation), serve action (Kubernetes service/replicas/invoke), and job action."
---

# DigitalHub Container Runtime Guide

The **Container runtime** enables launching pods, jobs, and services on Kubernetes with custom container images, commands, and dependencies. It backs `Function` entities of `kind='container'` and supports the `job`, `serve`, and `build` actions. This document covers the Container runtime; for the generic function entity surface, see [function](../entities/function.md); for the run entity surface, see [run](../entities/run.md).

Runtime package: **`digitalhub-runtime-container`**.

---

## 1. Supported kinds and actions

| Function kind | Actions                 | Runtime package               |
| :------------ | :---------------------- | :---------------------------- |
| `container`   | `job`, `serve`, `build` | `digitalhub-runtime-container`|

Action semantics:

- `job` — execute a container workload as a one-off task on Kubernetes to completion and termination.
- `serve` — deploy a container workload as a long-lived HTTP service on Kubernetes.
- `build` — generate a Dockerfile with custom instructions and build a container image on Kubernetes.

The corresponding **Run kinds** are:
- `container+job:run`
- `container+serve:run`
- `container+build:run`

> ℹ️ **Execution Architecture**: Container functions are executed remotely on Kubernetes clusters managed by the platform.

---

## 2. Prerequisites

| Requirement | Details                       |
| :---------- | :---------------------------- |
| Python      | `>= 3.10, < 3.15`             |
| Package     | `digitalhub-runtime-container`|

Install runtime package: `pip install digitalhub-runtime-container`

---

## 3. Usage pattern & Architecture

To execute a container workload, follow this pattern:

1. **Create Function**: Use `dh.new_function()` or `project.new_function()` with `kind="container"`, passing function parameters (`image`, `base_image`, `command`, `image_pull_policy`).
2. **Execute Action**: Call `function.run()` with the desired action (`job`, `serve`, or `build`), passing task parameters and run parameters. Alternatively, use `function.build()`.

### 3.1 Create and run a container job

```python
import digitalhub as dh

project = dh.get_or_create_project("my-project")

# Create function with function parameters
function = project.new_function(
    name="my-function",
    kind="container",
    image="my-image:latest",
    command="my-command",
)

# Execute with task and run parameters
run = function.run(
    action="job",
    args=["arg1", "arg2"],
    wait=True,
)
```

### 3.2 Build and run with dependencies

When a job or service needs additional dependencies, build the execution image before launching it. Configure the `base_image` and the target `image` on the same `Function`, run `build()` (or `run(action="build")`) with the required `instructions`, and then use that function for the `job` or `serve` run.

```python
import digitalhub as dh

project = dh.get_or_create_project("my-project")

function = project.new_function(
    name="my-function",
    kind="container",
    image="registry.example.com/my-function:latest",
    base_image="python:3.11-slim",
    command="python app.py",
)

# Build image with custom instructions (RUN lines in generated Dockerfile)
function.build(
    instructions=["pip install numpy pandas"],
    wait=True,
)

# Execute job using the built image
run = function.run(
    action="job",
    args=["input.csv"],
    wait=True,
)
```

> 💡 **Auto-build**: If `spec.image` is `None` (or not yet built), you can pass `auto_build=True` to `function.run(action="job", auto_build=True)` or `function.run(action="serve", auto_build=True)`. The runtime will automatically build the image first.

---

## 4. Function spec fields (`kind='container'`)

Container functions can be created either from a `Project` instance or directly from top-level `dh`.

### 4.1 Creation methods

```python
import digitalhub as dh

# Method A: Create from Project instance
project = dh.get_or_create_project("my-project")
function = project.new_function(
    name="my-container-function",
    kind="container",
    image="python:3.11-slim",
    command="python -m http.server 8080",
)

# Method B: Create from SDK top-level
function = dh.new_function(
    project="my-project",
    name="my-container-function",
    kind="container",
    image="python:3.11-slim",
    command="python -m http.server 8080",
)
```

### 4.2 Spec parameters

| Field               | Type             | Required | Description                                                                                 |
| :------------------ | :--------------- | :------: | :------------------------------------------------------------------------------------------ |
| `project`           | str              |    *     | Project name. Required when creating via `dh.new_function()`; MUST NOT be passed when creating via `project.new_function()`. |
| `name`              | str              |    ✅    | Name that identifies the function object.                                                   |
| `kind`              | str              |    ✅    | Function kind. Must be `container`.                                                         |
| `image`             | str              |          | Container image to use for execution (`name:tag`).                                          |
| `base_image`        | str              |          | Base image used when building the execution image.                                          |
| `command`           | str              |          | Command to run inside the container.                                                        |
| `image_pull_policy` | str              |          | Kubernetes image pull policy: `Always`, `IfNotPresent`, or `Never`.                         |
| `code_src`          | str              |          | URI pointing to the source code (local path, http, git, s3).                                |
| `code`              | str              |          | Source code provided directly as plain text.                                                |
| `base64`            | str              |          | Source code encoded as base64 string.                                                       |
| `handler`           | str              |          | Function entrypoint.                                                                        |
| `lang`              | str              |          | Source code language (informational).                                                       |
| `uuid`              | str              |          | Object ID in UUID4 format.                                                                  |
| `description`       | str              |          | Human-readable description of the function object.                                          |
| `labels`            | list[str]        |          | List of tags / labels.                                                                      |
| `embedded`          | bool             |          | Whether the function object should be embedded directly in the project (default `False`).  |

### 4.3 Function methods

- **`function.build(wait=True, log_info=True, extensions=None, **kwargs) -> Run`**:
  Create and execute a build run for the function using the `build` action.
- **`function.run(action, wait=False, log_info=True, extensions=None, auto_build=False, **kwargs) -> Run`**:
  General entrypoint to execute a task (`job`, `serve`, or `build`).

**Agent tool:** `new_dh_container_function(project, name, image, base_image, command, image_pull_policy, code_src, code, base64, handler, lang, uuid, description, labels, embedded)`

---

## 5. Actions

### 5.1 `job` — one-off container execution

The `job` action runs a container to completion on Kubernetes and then terminates.

```python
run = function.run(
    action="job",
    args=["arg1", "arg2"],
    run_as_user=8877,
    wait=True,
)
```

#### Shared Task parameters:
| Field       | Type        | Description                             |
| :---------- | :---------- | :-------------------------------------- |
| `action`    | str         | Task action. Required. Must be `"job"`. |
| `volumes`   | list[dict]  | List of attached storage volumes.       |
| `resources` | dict        | Resource values with optional `cpu`, `mem`, `gpu`, and `disk` keys. Example: `{"cpu": "1", "mem": "512Mi"}`. |
| `envs`      | list[dict]  | Environment variables. Example: `[{"name": "FOO", "value": "bar"}]`. |
| `secrets`   | list[str]   | List of secret names to mount into the run. |
| `profile`   | str         | Profile template.                       |

#### Job-Specific Task parameters:
| Field          | Type | Description                                        |
| :------------- | :--- | :------------------------------------------------- |
| `fs_group`     | int  | File system group ID. Must be positive.            |
| `run_as_user`  | int  | User ID to run the container. Must be non-negative.|
| `run_as_group` | int  | Group ID to run the container. Must be non-negative.|

#### Run parameters:
| Field        | Type      | Default | Description                                                                                 |
| :----------- | :-------- | :-----: | :------------------------------------------------------------------------------------------ |
| `auto_build` | bool      | `True`  | Whether to build the function automatically when no image is configured. Defaults to `True`.|
| `args`       | list[str] |         | Command-line arguments to pass to the container command.                                    |
| `wait`       | bool      | `True`  | Whether to wait for execution to complete.                                                  |
| `log_info`   | bool      | `True`  | Whether to log information while waiting.                                                   |

**Agent tool:** `run_dh_container_job(project_name, name, wait, log_info, auto_build, args, volumes, resources, envs, secrets, profile, image, base_image, image_pull_policy, command, run_as_user, run_as_group, fs_group)`

---

### 5.2 `serve` — long-lived HTTP service

The `serve` action creates a Kubernetes service that runs continuously and can handle incoming HTTP requests.

```python
run = function.run(
    action="serve",
    replicas=2,
    service_ports=[{"port": 80, "target_port": 8080}],
    service_type="ClusterIP",
    service_name="my-service",
    wait=True,
)
```

#### Shared Task parameters:
Shared with `job` (`action="serve"`, `volumes`, `resources`, `envs`, `secrets`, `profile`, `run_as_user`, `run_as_group`, `fs_group`).

#### Serve-Specific Task parameters:
| Field           | Type       | Description                                                                              |
| :-------------- | :--------- | :--------------------------------------------------------------------------------------- |
| `replicas`      | int        | Number of replicas. Must be non-negative.                                                |
| `service_ports` | list[dict] | Ports to expose for the service. Each port and target port must be an integer. Example: `[{"port": 80, "target_port": 8080}]`. |
| `service_type`  | str        | Service type: `ClusterIP`, `LoadBalancer`, `NodePort`, or `ExternalName`.                |
| `service_name`  | str        | Custom service name.                                                                     |

#### Run parameters:
| Field        | Type      | Default | Description                                                                                 |
| :----------- | :-------- | :-----: | :------------------------------------------------------------------------------------------ |
| `auto_build` | bool      | `True`  | Whether to build the function automatically when no image is configured. Defaults to `True`.|
| `args`       | list[str] |         | Command-line arguments to pass to the container command.                                    |
| `wait`       | bool      | `True`  | Whether to wait for execution to complete.                                                  |
| `log_info`   | bool      | `True`  | Whether to log information while waiting.                                                   |

#### Invoking the service:
The `Run` object for a `serve` action provides the `invoke()` method:
- **`run.invoke(method='POST', url=None, **kwargs) -> requests.Response`**:
  Uses the service URL from the run status (`run.status.service["url"]`) if no URL is specified.
  Defaults to `"POST"` if `data` or `json` is provided in kwargs, otherwise defaults to `"GET"`. Returns a `requests.Response` object.
- The service URL can also be directly inspected:
  ```python
  service_url = run.status.service["url"]
  ```

```python
response = run.invoke()
print(response.text)
```

**Agent tool:** `run_dh_container_serve(project_name, name, wait, log_info, auto_build, args, replicas, service_ports, service_type, service_name, volumes, resources, envs, secrets, profile, image, base_image, image_pull_policy, command, run_as_user, run_as_group, fs_group)`

---

### 5.3 `build` — build container image

The `build` action generates a Dockerfile with your custom instructions and builds a container image using Kaniko on Kubernetes.

```python
run = function.run(
    action="build",
    instructions=["apt-get update && apt-get install -y git", "pip install pandas"],
    wait=True,
)
# Or directly via build() method:
run = function.build(
    instructions=["apt-get update && apt-get install -y git"],
    wait=True,
)
```

#### Task parameters:
| Field          | Type      | Description                                                                              |
| :------------- | :-------- | :--------------------------------------------------------------------------------------- |
| `action`       | str       | Task action. Required. Must be `"build"`.                                                |
| `instructions` | list[str] | Build instructions executed as `RUN` lines in the generated Dockerfile. Example: `["apt-get update", "pip install numpy"]`. |
| `base_image`   | str       | Optional override for the base image used by this build run.                             |
| `image`        | str       | Optional target image name:tag to build/push.                                            |
| `volumes`, `resources`, `envs`, `secrets`, `profile` | | Standard task parameters.                                 |

#### Run parameters:
| Field      | Type      | Default | Description                                                       |
| :--------- | :-------- | :-----: | :---------------------------------------------------------------- |
| `args`     | list[str] |         | Command-line arguments to pass to the container command.          |
| `wait`     | bool      | `True`  | Whether to wait for build to complete.                            |
| `log_info` | bool      | `True`  | Whether to log information while waiting.                         |

#### Run methods for build:
- `run.image()`: Returns the container image tag generated by the build (`str | None`).

**Agent tool:** `run_dh_container_build(project_name, name, wait, log_info, instructions, base_image, image, volumes, resources, envs, secrets, profile, args)`

---

## 6. Run object surface (Container runtime specifics)

Once an action produces a `Run` entity, the following runtime-specific inspection methods are available:

| Method                                      | Applies to     | Description                                                                                 | Agent tool                                |
| :------------------------------------------ | :------------- | :------------------------------------------------------------------------------------------ | :---------------------------------------- |
| `image()`                                   | **build only** | Returns the container image string generated by the build run (`str \| None`).              | —                                         |
| `invoke(method='POST', url=None, **kwargs)` | **serve only** | Dispatches HTTP request to the served service endpoint. Returns `requests.Response`.         | `invoke_dh_run_service`                   |
| `status.service['url']`                     | **serve only** | URL of the deployed HTTP service endpoint.                                                 | —                                         |
| `logs()`                                    | all            | Retrieves stdout/stderr logs from the execution pod.                                        | `get_dh_run_logs`                         |
| `wait()`                                    | all            | Blocks until run completion.                                                                | `wait_dh_run`                             |
| `stop()`                                    | all            | Stops a running execution.                                                                  | `stop_dh_run`                             |

---

## 7. End-to-end Recipes & Examples

### 7.1 Container Job (One-off execution)

```python
import digitalhub as dh

# 1. Obtain Project
project_name = "my-project"
project = dh.get_or_create_project(project_name)

# 2. Define Container Function
function = project.new_function(
    kind="container",
    name="my_job",
    image="hello-world:latest",
)

# 3. Execute Job
run = function.run(
    action="job",
    run_as_user=8877,
    wait=True,
)
print("Job finished with status:", run.status.state)
```

Agent-tool equivalent:

```
# Step 1: Scan and activate container runtime tools
scan_and_create_dh_tools(runtime_name="container")

# Step 2: Create function
new_dh_container_function(
    project="my-project",
    name="my_job",
    image="hello-world:latest",
)

# Step 3: Run job
run_dh_container_job(
    project_name="my-project",
    name="my_job",
    run_as_user=8877,
    wait=True,
)
```

---

### 7.2 Container Build with custom instructions

```python
import digitalhub as dh

# 1. Obtain Project
project = dh.get_or_create_project("my-project")

# 2. Define Function with base image
function = project.new_function(
    kind="container",
    name="my_custom_image",
    base_image="python:3.11-slim",
)

# 3. Build image with instructions
build_run = function.run(
    action="build",
    instructions=["apt-get update && apt-get install -y git"],
    wait=True,
)
print(f"Built image: {build_run.image()}")
```

Agent-tool equivalent:

```
# Step 1: Scan container tools
scan_and_create_dh_tools(runtime_name="container")

# Step 2: Create function with base image
new_dh_container_function(
    project="my-project",
    name="my_custom_image",
    base_image="python:3.11-slim",
)

# Step 3: Execute build
run_dh_container_build(
    project_name="my-project",
    name="my_custom_image",
    instructions=["apt-get update && apt-get install -y git"],
    wait=True,
)
```

---

### 7.3 Container Serve (Deploy and Invoke Service)

```python
import digitalhub as dh

# 1. Obtain Project
project = dh.get_or_create_project("my-project")

# 2. Define Serving Function
function = project.new_function(
    kind="container",
    name="echo_service",
    image="hashicorp/http-echo:latest",
)

# 3. Deploy Service
run = function.run(
    action="serve",
    replicas=2,
    service_ports=[{"port": 5678, "target_port": 5678}],
    service_name="http-echo",
    run_as_user=8877,
    wait=True,
)

# 4. Invoke Endpoint
response = run.invoke()
print("Service response:", response.text)
```

Agent-tool equivalent:

```
# Step 1: Scan container tools
scan_and_create_dh_tools(runtime_name="container")

# Step 2: Create function
new_dh_container_function(
    project="my-project",
    name="echo_service",
    image="hashicorp/http-echo:latest",
)

# Step 3: Deploy Service
run_dh_container_serve(
    project_name="my-project",
    name="echo_service",
    replicas=2,
    service_ports=[{"port": 5678, "target_port": 5678}],
    service_name="http-echo",
    run_as_user=8877,
    wait=True,
)

# Step 4: Invoke Service Endpoint
invoke_dh_run_service(
    project="my-project",
    run_id="<run-id>",
    method="GET",
)
```
