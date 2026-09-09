---
type: entity_specification
entity: artifact
version: "0.16"
tags: [artifact, files, binary, storage, upload, download, s3, crud, io]
tools:
  - new_dh_artifact
  - log_dh_artifact
  - log_dh_generic_artifact
  - get_dh_artifact
  - get_dh_artifact_versions
  - import_dh_artifact
  - list_dh_artifacts
  - update_dh_artifact
  - delete_dh_artifact
  - save_dh_artifact
  - refresh_dh_artifact
  - export_dh_artifact
  - as_file_dh_artifact
  - download_dh_artifact
  - upload_dh_artifact
description: "Specification and reference for the DigitalHub Artifact entity: (binary) files stored in an artifact store, with CRUD, log/upload, download and I/O operations."
---

# DigitalHub Artifact Specification & SDK Guide

An **Artifact** is a (binary) object stored in one of the DigitalHub artifact stores and made available to every process, module, and component as files or data streams. Artifacts cover generic files, model bundles, reports, images, archives, and any non-tabular payload that should be produced/consumed by functions and workflows.

---

## 1. Conceptual Model

An artifact entity holds:

- **Metadata** — `name`, `description`, `labels`, `kind`, version (UUID).
- **Spec** — most importantly `path`: the location of the data in the artifact store. `path` is both the **source** of downloads and the **destination** of uploads.
- **Status** — backend-managed lifecycle state.
- **Extensions** — optional list of extension dicts.

An artifact belongs to a **Project** and is versioned. Every DigitalHub write produces a new version rather than mutating spec fields (specs are immutable).

### 1.1 Register vs. Log

| Operation                                     | Creates entity | Uploads file(s) | Use when                                                  |
| :-------------------------------------------- | :------------: | :-------------: | :-------------------------------------------------------- |
| `new_dh_artifact`                             |       ✅       |       ❌        | The file already lives at a known local/remote `path`.    |
| `log_dh_artifact` / `log_dh_generic_artifact` |       ✅       |       ✅        | You have local file(s) to ingest into the artifact store. |

---

## 2. Supported Artifact Kinds

| Kind       | Purpose                                                        |
| :--------- | :------------------------------------------------------------- |
| `artifact` | Generic artifact — any file(s) manipulable via download/upload |

Each kind is a subclass of `Artifact` with its own `spec` and `status` schemas.

### 2.1 Generic `artifact` spec

| Field  | Type | Description                                                                                            |
| :----- | :--- | :----------------------------------------------------------------------------------------------------- |
| `path` | str  | Local or remote path (single file or directory/partition). Required at creation for a usable artifact. |

The generic `artifact` kind exposes **no additional methods** beyond the base CRUD + I/O described below.

---

## 3. Artifact Lifecycle

```text
[ 1. Have a file locally? ]
        |                   \
        | yes                 \ no (already in storage)
        v                       v
[ log_dh_artifact ]         [ new_dh_artifact(path=...) ]
   creates + uploads            creates metadata only
        v                             v
[ Persisted in backend ]     [ Persisted in backend ]
        \                       /
         v---------------------v
                  |
                  v
[ Consume via I/O methods ]
   as_file / download / upload
                  |
                  v
[ Optional: export YAML / update / delete ]
```

---

## 4. SDK API Reference (DigitalHub 0.15)

### 4.1 Create — `dh.new_artifact`

Registers an Artifact entity referencing an existing path, without uploading content.

```python
import digitalhub as dh

art = dh.new_artifact(
    project="my-project",
    name="my-artifact",
    kind="artifact",
    path="s3://my-bucket/my-key",
)
```

**Parameters:**

- `project` (_str_, required)
- `name` (_str_, required)
- `kind` (_str_, required — currently `"artifact"`)
- `uuid` (_str_, optional)
- `description` (_str_, optional)
- `labels` (_list[str]_, optional)
- `embedded` (_bool_, default `False`)
- `path` (_str_, optional) — object path; also the default destination of `upload()`.
- `extensions` (_list[dict]_, optional)
- `**kwargs`: kind-specific spec.

**Agent tool:** `new_dh_artifact(project, name, kind, uuid, description, labels, embedded, path, extensions, kwargs)`

### 4.2 Create + Upload — `dh.log_artifact`

Creates the entity AND uploads local file(s) to the artifact store.

```python
art = dh.log_artifact(
    project="my-project",
    name="my-artifact",
    kind="artifact",
    source="./local-path",
)
```

**Parameters:**

- `project` (_str_, required)
- `name` (_str_, required)
- `kind` (_str_, required)
- `source` (_str | list[str]_, required): local file, directory, or list of files.
- `drop_existing` (_bool_, default `False`): drop any existing entity with the same name before logging.
- `path` (_str_, optional): destination path in the artifact store; auto-generated if omitted.
- `description`, `labels`, `**kwargs`: same as `new_artifact`.

**Agent tool:** `log_dh_artifact(project, name, source, kind, drop_existing, path, description, labels, kwargs)`

### 4.3 Create + Upload (generic kind) — `dh.log_generic_artifact`

Same as `log_artifact` but pinned to the generic `artifact` kind — omit `kind`.

```python
art = dh.log_generic_artifact(
    project="my-project",
    name="my-generic-artifact",
    source="./local-path",
)
```

**Agent tool:** `log_dh_generic_artifact(project, name, source, drop_existing, path, description, labels, kwargs)`

### 4.4 Read

#### `get_artifact`

Fetch a single artifact by name or key.

```python
art = dh.get_artifact("my-artifact", project="my-project")
art = dh.get_artifact("store://my-project/artifact/artifact/my-artifact:<id>")
```

**Agent tool:** `get_dh_artifact(identifier, project, entity_id)`

#### `get_artifact_versions`

Returns all versions.
**Agent tool:** `get_dh_artifact_versions(identifier, project)`

#### `list_artifacts`

Lists latest artifact versions of a project with optional filters (`q`, `name`, `kind`, `user`, `state`, `created`, `updated`, `versions`).
**Agent tool:** `list_dh_artifacts(project, ...)`

#### `import_artifact`

Load an artifact from a local YAML file or a store key.
**Agent tool:** `import_dh_artifact(file, key, reset_id, context)`

### 4.5 Update / Delete

#### `update_artifact`

Specs are immutable; only metadata-level updates are applied by the backend.
**Agent tool:** `update_dh_artifact(project_name, name)`

#### `delete_artifact`

Delete one version or all versions.

```python
dh.delete_artifact("my-artifact", project="my-project", delete_all_versions=True)
```

**Agent tool:** `delete_dh_artifact(identifier, project, entity_id, delete_all_versions, cascade)`

---

## 5. Artifact Object Methods

### 5.1 CRUD-object methods

| Method      | Purpose                                    | Agent tool            |
| :---------- | :----------------------------------------- | :-------------------- |
| `save()`    | Persist / update the entity in the backend | `save_dh_artifact`    |
| `refresh()` | Reload state from backend                  | `refresh_dh_artifact` |
| `export()`  | Export as YAML file in the context folder  | `export_dh_artifact`  |

### 5.2 I/O methods

| Method       | Purpose                                                          | Agent tool             |
| :----------- | :--------------------------------------------------------------- | :--------------------- |
| `as_file()`  | Download into a temporary folder and return list of file paths   | `as_file_dh_artifact`  |
| `download()` | Download to a chosen local `destination` (default: context path) | `download_dh_artifact` |
| `upload()`   | Upload local `source` file(s) to the artifact's `spec.path`      | `upload_dh_artifact`   |

Notes:

- `download` accepts `destination` (path/dir) and `overwrite` (bool). If files already exist and `overwrite=False`, it raises.
- `upload` accepts `source` (path, dir, or list) and `keep_dir_structure` (bool). When uploading a folder or list, `spec.path` must be a folder/partition (must end with `/` for s3).

### 5.3 Kind-specific methods

The generic `artifact` kind has no additional methods.

---

## 6. End-to-end Recipes

### 6.1 Log a local file and download it later

```python
import digitalhub as dh

art = dh.log_generic_artifact(
    project="my-project",
    name="training-report",
    source="./reports/train.pdf",
    description="Nightly training report",
    labels=["team:mlops", "env:prod"],
)

# Later, in a different process:
art = dh.get_artifact("training-report", project="my-project")
path = art.download(destination="./tmp")
```

Agent-tool equivalent:

```
log_dh_generic_artifact(project="my-project", name="training-report", source="./reports/train.pdf",
                        description="...", labels=["team:mlops", "env:prod"])
download_dh_artifact(project_name="my-project", name="training-report", destination="./tmp")
```

### 6.2 Register an artifact already in S3, then upload a new version's file

```python
art = dh.new_artifact(
    project="my-project",
    name="model-bundle",
    kind="artifact",
    path="s3://my-bucket/models/model-bundle.tar.gz",
)

# Refresh spec, then push a local file that will land at spec.path
art.upload("./dist/model-bundle.tar.gz")
```

Agent-tool equivalent:

```
new_dh_artifact(project="my-project", name="model-bundle", kind="artifact",
                path="s3://my-bucket/models/model-bundle.tar.gz")
upload_dh_artifact(project_name="my-project", name="model-bundle",
                   source="./dist/model-bundle.tar.gz")
```

### 6.3 Upload a whole directory

```python
art = dh.new_artifact(project="my-project", name="images", kind="artifact",
                     path="s3://my-bucket/images/")
art.upload("./local/images", keep_dir_structure=True)
```

### 6.4 Ephemeral read via `as_file`

```python
art = dh.get_artifact("training-report", project="my-project")
tmp_files = art.as_file()
with open(tmp_files[0], "rb") as f:
    payload = f.read()
```

---

## 7. Operational Guidance for the Agent

- **Choose the right creator**:
  - Use `new_dh_artifact` when the data is already at a known path — cheap, no I/O.
  - Use `log_dh_artifact` / `log_dh_generic_artifact` when ingesting local file(s) into the store.
- **`spec.path` is dual-purpose**: it is both the source of `download`/`as_file` and the destination of `upload`. For directory uploads, the `path` must end with `/` (s3).
- **Uploading directories or file lists** requires `spec.path` to be a folder/partition; use `keep_dir_structure=True` to preserve the local hierarchy.
- **Overwrite protection**: `download_dh_artifact(overwrite=False)` is the default — pass `overwrite=True` to replace existing local files.
- **Immutable specs**: to change `path`, register a new version via `new_dh_artifact`; do not attempt to edit spec fields via `update_dh_artifact`.
- **Versioning**: use `get_dh_artifact_versions` for history; use `get_dh_artifact` with `entity_id` to pin a specific version.
- **Discovery**: use `list_dh_artifacts` for project-wide scan; filter by `kind`, `name`, `state`, etc.
- **Only kind is `artifact`** in 0.15 — passing another value will fail.
- **Difference vs. DataItem**: use `Artifact` for arbitrary binary / file payloads (models, reports, images, archives). Use `DataItem` for datasets (tabular, croissant) that participate in data-plane operations.
