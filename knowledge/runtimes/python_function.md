---
type: runtime_specification
entity: function
runtime: python
version: "0.16"
tags:
  [
    function,
    python,
    handler,
    build,
    job,
    serve,
    ml,
    metrics,
    models,
    runs,
    tasks,
  ]
tools:
  - new_dh_function
  - get_dh_function
  - get_dh_function_versions
  - import_dh_function
  - list_dh_functions
  - delete_dh_function
  - delete_dh_function_versions
  - build_dh_function
  - run_dh_function
  - job_dh_function
  - serve_dh_function
  - export_dh_function
  - create_local_function_source_file
  - read_local_function_source_file
  - get_dh_function_run
  - list_dh_function_runs
  - get_dh_function_task
  - list_dh_function_tasks
  - log_dh_function_run_metric
  - get_dh_function_run_logs
description: "Comprehensive specification and developer guide for DigitalHub Python runtime functions, @handler conventions, execution lifecycles, and MLOps integrations."
---

# DigitalHub Python Function Runtime & Handler Guide

The **Python Runtime** in DigitalHub enables serverless, containerized execution of Python scripts, data processing workflows, and machine learning pipelines.

---

## 1. Execution Lifecycle

A Python Function follows a strict 3-step lifecycle:

```text
[ 1. Define / Register ]
       |  dh.new_function(..., code="...")
       v
[ 2. Build Container ]
       |  fn.build() -> compiles image & dependencies
       v
[ 3. Execute / Serve ]
       +---> fn.job()    (Batch Processing)
       +---> fn.serve()  (Real-time HTTP API)
```

> [!IMPORTANT]
> **Build Requirement**: A Python Function MUST be built with `build_dh_function` before running batch jobs (`job_dh_function`) or services (`serve_dh_function`). Never attempt to run without a successful build.

---

## 2. Writing Python Handlers (`digitalhub_runtime_python`)

Handler functions are the execution entrypoints. They use the `@handler` decorator from `digitalhub_runtime_python`.

### 2.1 Standard Handler Architecture

```python
from digitalhub_runtime_python import handler
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

@handler(outputs=["processed_data", "model_output"])
def train_model(project, run, raw_data, n_estimators=100, learning_rate=0.01):
    """
    Handler function for model training.
    """
    # 1. Access DataItem input (see DataItem Guide: ../entities/dataitem.md)
    df = raw_data.as_df()

    # 2. Data processing
    processed_df = df.dropna()
    X = processed_df.drop("target", axis=1)
    y = processed_df["target"]

    # 3. Model training
    clf = RandomForestClassifier(n_estimators=n_estimators)
    clf.fit(X, y)
    accuracy = clf.score(X, y)

    # 4. Log Metrics via 'run'
    run.log_metric("train_accuracy", accuracy)
    run.log_metric("sample_count", len(df))

    # 5. Log Model via 'project'
    os.makedirs("./models", exist_ok=True)
    model_path = "./models/rf_model.joblib"
    joblib.dump(clf, model_path)

    logged_model = project.log_model(
        name="customer-churn-model",
        kind="sklearn",
        source=model_path,
        algorithm="RandomForestClassifier",
        metrics={"accuracy": accuracy}
    )

    # 6. Return values (mapped to named outputs in @handler decorator)
    # DataFrames are automatically logged as DataItems
    return processed_df, logged_model
```

---

## 3. Handler Argument Semantics

| Argument Category    | Description                                                                                            | How It is Injected / Passed                                 | Example in Handler               |
| :------------------- | :----------------------------------------------------------------------------------------------------- | :---------------------------------------------------------- | :------------------------------- |
| **Reserved Objects** | Injected automatically by the runtime when declared in the signature.                                  | Auto-injected by parameter name: `project`, `run`.          | `def handler(project, run, ...)` |
| **Data Inputs**      | Platform entities ([DataItems](../entities/dataitem.md), Models, Artifacts) passed via `inputs={...}`. | `.as_df()`, `.download()`, or `.as_file()`                  | `df = raw_data.as_df()`          |
| **Parameters**       | Scalar hyper-parameters and primitive config passed via `parameters={...}`.                            | Plain Python types (`int`, `float`, `str`, `dict`, `list`). | `n_estimators = 100`             |

### 3.1 Reserved Parameters

- `project`: An active `Project` instance (see [Project Guide](../entities/project.md)). Used to log child resources like `project.log_model(...)`, `project.log_dataitem(...)`, or `project.log_artifact(...)`.
- `run`: The active `Run` execution instance. Used to log scalar metrics and parameters: `run.log_metric("loss", 0.04)`.

### 3.2 Output Mapping (`@handler(outputs=[...])`)

- The `@handler(outputs=["out_name1", "out_name2"])` decorator matches return values in order.
- If a returned object is a `pandas.DataFrame` or `polars.DataFrame`, the runtime automatically logs it as a new [DataItem](../entities/dataitem.md) (`kind="table"`) in the project.
- If a returned object is an entity (e.g. `Model` or `Artifact`), it is linked directly to the run outputs.

---

## 4. Function Creation & Code Delivery

Functions can be defined with inline code or local source files:

### 4.1 Inline Code (`new_dh_function`)

Pass Python code directly via the `code` parameter:

```python
fn = dh.new_function(
    project="customer-analytics",
    name="data-prep",
    kind="python",
    source_code="""
from digitalhub_runtime_python import handler

@handler(outputs=["clean_table"])
def clean(input_data):
    df = input_data.as_df()
    return df.dropna()
""",
    requirements=["pandas", "pyarrow"]
)
```

### 4.2 Local Source File Delivery

Write the code to a local script using `create_local_function_source_file`, then reference the path:

```python
# 1. Agent writes script locally
# create_local_function_source_file(file_path="src/prep.py", content=...)

# 2. Agent registers function pointing to script
fn = dh.new_function(
    project="customer-analytics",
    name="data-prep",
    kind="python",
    source="src/prep.py",
    handler="prep.py:clean",
    requirements=["pandas>=2.0.0"]
)
```

---

## 5. Execution Workflow

### Step 1: Build Function

Compiles dependencies and generates the execution container.

```python
# Agent tool: build_dh_function(project_name="customer-analytics", function_name="data-prep")
fn = dh.get_function("data-prep", project="customer-analytics")
build_run = fn.build()
```

### Step 2: Run Batch Job (`fn.job` / `fn.run`)

Executes the function with inputs and parameters.

```python
# Agent tool: job_dh_function(project_name="customer-analytics", function_name="data-prep", inputs={"input_data": "store://..."}, parameters={"threshold": 0.5})
run = fn.job(
    action="job",
    inputs={"raw_data": "store://customer-analytics/dataitem/table/transactions"},
    parameters={"n_estimators": 200, "learning_rate": 0.05}
)
```

### Step 3: Deploy as Real-time Service (`fn.serve`)

Launches the function as a long-running HTTP endpoint service.

```python
# Agent tool: serve_dh_function(project_name="customer-analytics", function_name="data-prep")
service_run = fn.serve()
```

---

## 6. Runs, Tasks, and Logs Monitoring

| Operation               | SDK Method           | Agent Tool                                            |
| :---------------------- | :------------------- | :---------------------------------------------------- |
| **List Runs**           | `fn.list_runs()`     | `list_dh_function_runs(project_name, function_name)`  |
| **Get Run Status**      | `dh.get_run(run_id)` | `get_dh_function_run(project_name, run_id)`           |
| **View Execution Logs** | `run.logs()`         | `get_dh_function_run_logs(project_name, run_id)`      |
| **List Tasks**          | `fn.list_task()`     | `list_dh_function_tasks(project_name, function_name)` |

---

## 7. Best Practices & Troubleshooting

1. **Always Build First**: Never run `job_dh_function` on an unbuilt or modified function. Always execute `build_dh_function` first.
2. **Explicit Requirements**: Always specify third-party pip dependencies in `requirements` (e.g. `requirements=["scikit-learn", "pandas", "xgboost"]`).
3. **Clean Handler Code**: Ensure all imports are inside the code string/file and no interactive notebook constructs (`%matplotlib`, `!pip`) are present.
4. **Naming Standards**: Follow [Platform Governance Standards](../governance/standards.md).
5. **Errors & Recovery**: For build or parameter errors, consult [SDK Troubleshooting Guide](../troubleshooting/sdk_errors.md).

---

## 8. Cross-References

- [Project Guide](../entities/project.md)
- [DataItem Guide](../entities/dataitem.md)
- [Workflow Recipes](../workflows/recipes.md)
- [Troubleshooting Guide](../troubleshooting/sdk_errors.md)
- [Governance Standards](../governance/standards.md)
