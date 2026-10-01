---
type: entity_specification
entity: model
version: "0.16"
tags:
  [
    model,
    ml,
    mlflow,
    sklearn,
    huggingface,
    metrics,
    storage,
    upload,
    download,
    crud,
    io,
  ]
tools:
  - new_dh_model
  - log_dh_model
  - log_dh_generic_model
  - log_dh_mlflow_model
  - log_dh_sklearn_model
  - log_dh_huggingface_model
  - get_dh_model
  - get_dh_model_versions
  - import_dh_model
  - list_dh_models
  - update_dh_model
  - delete_dh_model
  - save_dh_model
  - refresh_dh_model
  - export_dh_model
  - as_file_dh_model
  - download_dh_model
  - upload_dh_model
  - log_dh_model_metric
  - log_dh_model_metrics
description: "Specification and reference for the DigitalHub Model entity: ML model registration, framework-specific logging (mlflow, sklearn, huggingface), I/O, and metrics tracking."
---

# DigitalHub Model Specification & SDK Guide

A **Model** represents a machine-learning model stored as files in the DigitalHub artifact store. Models track framework metadata, training parameters, and metrics (loss, accuracy, ...) alongside the model artifacts themselves.

> Requires the `digitalhub[ml]` layer installed.

---

## 1. Conceptual Model

A model entity holds:

- **Metadata** — `name`, `description`, `labels`, `kind`, version (UUID).
- **Spec** — the model file location (`path`) and framework-level metadata (`framework`, `algorithm`, `base_model`, `parameters`, `metrics`, plus kind-specific fields).
- **Status** — backend-managed state, including metrics logged via `log_metric` / `log_metrics`.
- **Extensions** — optional list of extension dicts.

A model belongs to a **Project** and is versioned; specs are immutable — each write produces a new version.

### 1.1 Register vs. Log

| Operation                               | Creates entity | Uploads file(s) | Use when                                                     |
| :-------------------------------------- | :------------: | :-------------: | :----------------------------------------------------------- |
| `new_dh_model`                          |       ✅       |       ❌        | The model files already live at a known local/remote `path`. |
| `log_dh_model` / `log_dh_generic_model` |       ✅       |       ✅        | Generic upload from a local file or folder.                  |
| `log_dh_mlflow_model`                   |       ✅       |       ✅        | Local MLflow directory (`MLmodel` layout).                   |
| `log_dh_sklearn_model`                  |       ✅       |       ✅        | Pickled scikit-learn model file/dir.                         |
| `log_dh_huggingface_model`              |       ✅       |       ✅        | Local HuggingFace repo/directory.                            |

---

## 2. Supported Model Kinds

| Kind          | Purpose                                               |
| :------------ | :---------------------------------------------------- |
| `model`       | Generic ML model                                      |
| `mlflow`      | MLflow model (with flavor, signature, input_datasets) |
| `sklearn`     | Scikit-learn model                                    |
| `huggingface` | HuggingFace model (with model_id, model_revision)     |

Each kind is a subclass of `Model` with its own `spec` and `status` schemas. None of the kinds adds new methods — behaviour differs only through spec fields.

### 2.1 Base spec fields (all kinds)

| Field        | Type | Description                                                                             |
| :----------- | :--- | :-------------------------------------------------------------------------------------- |
| `path`       | str  | Local or remote path (single file or directory/partition). Required for a usable model. |
| `framework`  | str  | Model framework (e.g. `'pytorch'`).                                                     |
| `algorithm`  | str  | Model algorithm (e.g. `'resnet'`).                                                      |
| `base_model` | str  | Base model reference.                                                                   |
| `parameters` | dict | Model hyperparameters / training parameters.                                            |
| `metrics`    | dict | Model metrics (also writable at runtime via `log_metric` / `log_metrics`).              |

### 2.2 `mlflow`-specific spec fields

| Field            | Type          | Description             |
| :--------------- | :------------ | :---------------------- |
| `flavor`         | str           | MLflow model flavor.    |
| `model_config`   | dict          | MLflow model config.    |
| `input_datasets` | list[Dataset] | MLflow input datasets.  |
| `signature`      | Signature     | MLflow model signature. |

**Dataset** entries: `name`, `digest`, `profile`, `schema`, `source`, `source_type`.
**Signature**: `inputs`, `outputs`, `parameters`.

### 2.3 `huggingface`-specific spec fields

| Field            | Type | Description                                                                            |
| :--------------- | :--- | :------------------------------------------------------------------------------------- |
| `model_id`       | str  | HuggingFace model id. If not specified, the model is loaded from the local model path. |
| `model_revision` | str  | HuggingFace model revision.                                                            |

### 2.4 `sklearn` spec

Only the base spec fields — no additional keys.

---

## 3. Model Lifecycle

```text
[ 1. Have local model files? ]
        |                        \
        | yes                      \ no (already in storage)
        v                            v
[ log_dh_*_model / log_dh_model ]   [ new_dh_model(path=...) ]
   creates + uploads                    creates metadata only
        v                                     v
[ Persisted in backend ]              [ Persisted in backend ]
        \                                    /
         v----------------------------------v
                       |
                       v
[ Consume via I/O methods ]
   as_file / download / upload
                       |
                       v
[ Track training metrics ]
   log_dh_model_metric / log_dh_model_metrics
                       |
                       v
[ Optional: export YAML / update / delete ]
```

---

## 4. SDK API Reference (DigitalHub 0.15)

### 4.1 Create — `dh.new_model`

Registers a Model entity referencing an existing path, without uploading content.

```python
import digitalhub as dh

mdl = dh.new_model(
    project="my-project",
    name="my-model",
    kind="model",
    path="s3://my-bucket/models/my-model",
)
```

**Parameters:**

- `project` (_str_, required)
- `name` (_str_, required)
- `kind` (_str_, required — one of `"model"`, `"mlflow"`, `"sklearn"`, `"huggingface"`)
- `uuid` (_str_, optional)
- `description` (_str_, optional)
- `labels` (_list[str]_, optional)
- `embedded` (_bool_, default `False`)
- `path` (_str_, optional) — model path; also default destination of `upload()`.
- `extensions` (_list[dict]_, optional)
- `**kwargs`: kind-specific spec (framework/algorithm/parameters/... plus kind extras).

**Agent tool:** `new_dh_model(project, name, kind, uuid, description, labels, embedded, path, extensions, kwargs)`

### 4.2 Create + Upload — `dh.log_model`

Creates the entity AND uploads local file(s) to the model store.

```python
mdl = dh.log_model(
    project="my-project",
    name="my-model",
    kind="model",
    source="./local-path",
)
```

**Parameters:**

- `project` (_str_, required)
- `name` (_str_, required)
- `kind` (_str_, required)
- `source` (_str | list[str]_, required): local file, directory, or list of files.
- `drop_existing` (_bool_, default `False`): drop any existing entity with the same name before logging.
- `path` (_str_, optional): destination path in the model store; auto-generated if omitted.
- `**kwargs`: kind-specific spec (see kinds section).

**Agent tool:** `log_dh_model(project, name, source, kind, drop_existing, path, kwargs)`

> Note: unlike the framework-specific loggers below, `log_model` does not take `description` / `labels` as first-class arguments — pass them through the entity if needed, or use `log_dh_generic_model`.

### 4.3 Create + Upload (generic) — `dh.log_generic_model`

Same as `log_model` but pinned to `kind='model'` and exposes `description` / `labels` explicitly.

**Agent tool:** `log_dh_generic_model(project, name, source, drop_existing, path, description, labels, kwargs)`

### 4.4 Create + Upload (MLflow) — `dh.log_mlflow`

Logs an MLflow model from a local MLflow directory.

```python
mdl = dh.log_mlflow(
    project="my-project",
    name="my-mlflow-model",
    source="./mlruns/0/<run-id>/artifacts/model",
)
```

MLflow-specific spec fields (flavor, model_config, input_datasets, signature) are passed via `kwargs`.
**Agent tool:** `log_dh_mlflow_model(project, name, source, drop_existing, path, description, labels, kwargs)`

### 4.5 Create + Upload (scikit-learn) — `dh.log_sklearn`

Logs a scikit-learn model from a local file or directory.
**Agent tool:** `log_dh_sklearn_model(project, name, source, drop_existing, path, description, labels, kwargs)`

### 4.6 Create + Upload (HuggingFace) — `dh.log_huggingface`

Logs a HuggingFace model from a local repository or directory. Provide `model_id`/`model_revision` inside `kwargs` if needed.
**Agent tool:** `log_dh_huggingface_model(project, name, source, drop_existing, path, description, labels, kwargs)`

### 4.7 Read

#### `get_model`

Fetch a single model by name or key.

```python
mdl = dh.get_model("my-model", project="my-project")
mdl = dh.get_model("store://my-project/model/model/my-model:<id>")
```

**Agent tool:** `get_dh_model(identifier, project, entity_id)`

#### `get_model_versions`

Returns all versions.
**Agent tool:** `get_dh_model_versions(identifier, project)`

#### `list_models`

Lists latest model versions of a project with optional filters (`q`, `name`, `kind`, `user`, `state`, `created`, `updated`, `versions`).
**Agent tool:** `list_dh_models(project, ...)`

#### `import_model`

Load a model from a local YAML file or a store key.
**Agent tool:** `import_dh_model(file, key, reset_id, context)`

### 4.8 Update / Delete

#### `update_model`

Specs are immutable; only metadata-level updates are applied by the backend.
**Agent tool:** `update_dh_model(project_name, name)`

#### `delete_model`

Delete one version or all versions.

```python
dh.delete_model("my-model", project="my-project", delete_all_versions=True)
```

**Agent tool:** `delete_dh_model(identifier, project, entity_id, delete_all_versions, cascade)`

---

## 5. Model Object Methods

### 5.1 CRUD-object methods

| Method      | Purpose                                    | Agent tool         |
| :---------- | :----------------------------------------- | :----------------- |
| `save()`    | Persist / update the entity in the backend | `save_dh_model`    |
| `refresh()` | Reload state from backend                  | `refresh_dh_model` |
| `export()`  | Export as YAML file in the context folder  | `export_dh_model`  |

### 5.2 I/O methods

| Method       | Purpose                                                          | Agent tool          |
| :----------- | :--------------------------------------------------------------- | :------------------ |
| `as_file()`  | Download into a temporary folder and return list of file paths   | `as_file_dh_model`  |
| `download()` | Download to a chosen local `destination` (default: context path) | `download_dh_model` |
| `upload()`   | Upload local `source` file(s) to the model's `spec.path`         | `upload_dh_model`   |

Notes:

- `download` accepts `destination` and `overwrite`. If files already exist and `overwrite=False`, it raises.
- `upload` accepts `source` (path, dir, or list) and `keep_dir_structure`. For directory/list uploads, `spec.path` must be a folder/partition ending with `/` (s3).

### 5.3 Model-specific methods (metrics)

| Method                 | Purpose                                                        | Agent tool             |
| :--------------------- | :------------------------------------------------------------- | :--------------------- |
| `log_metric(key, val)` | Log a single metric (append to list, or store as single value) | `log_dh_model_metric`  |
| `log_metrics(dict)`    | Log multiple metrics at once                                   | `log_dh_model_metrics` |

`log_metric` parameters:

- `key` (str, required)
- `value` (number or list of numbers, required)
- `overwrite` (bool, default False): replace any existing metric with this key.
- `single_value` (bool, default False): store as a single number (default wraps into a list).

`log_metrics` parameters:

- `metrics` (dict[str, value], required): list values → logged as lists; scalars → logged as single values.
- `overwrite` (bool, default False): replace existing metrics.

Default behaviour is **append** to any existing metric list.

### 5.4 Kind-specific methods

None. The `model`, `mlflow`, `sklearn`, `huggingface` kinds have no additional methods beyond the base + I/O + metric ones.

---

## 6. End-to-end Recipes

### 6.1 Log a scikit-learn model and track metrics

```python
import digitalhub as dh

mdl = dh.log_sklearn(
    project="my-project",
    name="churn-classifier",
    source="./models/churn.pkl",
    description="Gradient boosted churn model",
    labels=["env:prod", "task:classification"],
    framework="scikit-learn",
    algorithm="gradient-boosting",
    parameters={"n_estimators": 200, "max_depth": 5},
)

mdl.log_metrics({"accuracy": 0.94, "loss": [0.42, 0.31, 0.22]})
mdl.log_metric("f1_score", 0.91, single_value=True)
```

Agent-tool equivalent:

```
log_dh_sklearn_model(project="my-project", name="churn-classifier",
                     source="./models/churn.pkl",
                     description="Gradient boosted churn model",
                     labels=["env:prod", "task:classification"],
                     kwargs={"framework": "scikit-learn", "algorithm": "gradient-boosting",
                             "parameters": {"n_estimators": 200, "max_depth": 5}})
log_dh_model_metrics(project_name="my-project", name="churn-classifier",
                     metrics={"accuracy": 0.94, "loss": [0.42, 0.31, 0.22]})
log_dh_model_metric(project_name="my-project", name="churn-classifier",
                    key="f1_score", value=0.91, single_value=True)
```

### 6.2 Log an MLflow model with signature and input datasets

```python
mdl = dh.log_mlflow(
    project="my-project",
    name="regressor-mlflow",
    source="./mlruns/0/<run-id>/artifacts/model",
    flavor="sklearn",
    signature={"inputs": "...", "outputs": "..."},
    input_datasets=[{"name": "train_set", "digest": "abc123", "source": "s3://..."}],
)
```

Agent-tool equivalent:

```
log_dh_mlflow_model(project="my-project", name="regressor-mlflow",
                    source="./mlruns/0/<run-id>/artifacts/model",
                    kwargs={"flavor": "sklearn",
                            "signature": {"inputs": "...", "outputs": "..."},
                            "input_datasets": [{"name": "train_set", "digest": "abc123",
                                                "source": "s3://..."}]})
```

### 6.3 Log a HuggingFace model

```python
mdl = dh.log_huggingface(
    project="my-project",
    name="sentence-encoder",
    source="./hf-models/sentence-encoder",
    model_id="sentence-transformers/all-MiniLM-L6-v2",
    model_revision="main",
)
```

Agent-tool equivalent:

```
log_dh_huggingface_model(project="my-project", name="sentence-encoder",
                         source="./hf-models/sentence-encoder",
                         kwargs={"model_id": "sentence-transformers/all-MiniLM-L6-v2",
                                 "model_revision": "main"})
```

### 6.4 Register a model already in S3, then download later

```python
mdl = dh.new_model(
    project="my-project",
    name="prod-checkpoint",
    kind="model",
    path="s3://my-bucket/models/prod-checkpoint/",
    framework="pytorch",
)

# Later, in a different process:
mdl = dh.get_model("prod-checkpoint", project="my-project")
mdl.download(destination="./local-checkpoints", overwrite=True)
```

### 6.5 Ephemeral read via `as_file`

```python
mdl = dh.get_model("churn-classifier", project="my-project")
tmp_files = mdl.as_file()
# load into memory with framework loader...
```

---

## 7. Operational Guidance for the Agent

- **Prefer the framework-specific logger** (`log_dh_mlflow_model`, `log_dh_sklearn_model`, `log_dh_huggingface_model`) when the source matches — it selects the right `kind` and enables framework-specific spec fields.
- **Use `new_dh_model`** when data already lives in storage — no I/O cost, cheap metadata write.
- **`log_dh_model` (base)** does _not_ accept `description` / `labels` directly — use `log_dh_generic_model` (kind=`model`) for that.
- **Kind ↔ log tool mapping**:
  - `model` → `log_dh_generic_model` (or `log_dh_model(kind="model")`)
  - `mlflow` → `log_dh_mlflow_model`
  - `sklearn` → `log_dh_sklearn_model`
  - `huggingface`→ `log_dh_huggingface_model`
- **`spec.path` is dual-purpose**: source of `download`/`as_file` and destination of `upload`. Directory uploads require `path` to end with `/` (s3).
- **Metrics**: default is _append_; use `overwrite=True` to reset. Use `single_value=True` for scalar metrics that should not be wrapped in a list.
- **Immutable specs**: to change `path` / `framework` / etc., register a new version via `new_dh_model` or a `log_*` call; do not attempt to edit spec fields via `update_dh_model`.
- **Versioning**: use `get_dh_model_versions` for history; use `get_dh_model` with `entity_id` to pin a specific version.
- **Difference vs. Artifact**: use `Model` for ML models — you get metric tracking (`log_metric`/`log_metrics`) and framework-typed specs. Use `Artifact` for generic binary payloads (reports, archives, images) with no framework semantics.
- **Serving**: to expose a model for inference, pair it with the appropriate `modelserve` runtime (sklearnserve / mlflowserve / huggingfaceserve / vllmserve / kubeai) — those runtimes read a `Model` entity via its store key.

---

## 8. Dynamic Tool Discovery & Domain Scoping

Model tools are omitted from the initial agent startup toolset to minimize initial context load.

When working with Model workflows:

1. **Dynamic Domain Loading**: Invoke `scan_and_create_dh_tools('model')` to reflectively introspect the live SDK and dynamically register all Model tools (`new_dh_model`, `register_dh_model`, `register_generic_dh_model`, `log_dh_model`, `log_generic_dh_model`, `log_dh_mlflow_model`, `log_dh_sklearn_model`, `log_dh_huggingface_model`, `get_dh_model`, `get_dh_model_versions`, `list_dh_models`, `delete_dh_model`, `import_dh_model`, `load_dh_model`, `download_dh_model`, `upload_dh_model`, `as_file_dh_model`, `export_dh_model`, `save_dh_model`, `refresh_dh_model`, `update_dh_model`, `add_label_dh_model`, `add_labels_dh_model`, `set_description_dh_model`, `log_dh_model_metric`, `log_dh_model_metrics`).
2. **Domain Swapping**: Loading `model` automatically unloads previous domain tools (e.g. `project`, `dataitem`, `artifact`, `secret`, or `trigger`) from the context window.
3. **Universal Execution (`call_dh_sdk`)**: For one-off operations, use `call_dh_sdk(entity='model', operation='list_models'|'get_model'|..., parameters={...})` without loading the model toolset into context.
